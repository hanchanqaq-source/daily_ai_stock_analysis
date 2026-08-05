import { beforeEach, describe, expect, it, vi } from 'vitest';
import { attachParsedApiError, getParsedApiError } from '../error';
import { fullDataBackupApi } from '../fullDataBackup';

const get = vi.hoisted(() => vi.fn());
const post = vi.hoisted(() => vi.fn());

vi.mock('../index', () => ({
  default: { get, post },
}));

const canonicalDocument = {
  format: 'pp02.full-data.backup' as const,
  format_version: 1 as const,
  metadata: {
    created_at: '2026-08-04T09:00:00Z',
    project_id: 'PP02',
  },
  manifest: {
    table_names: ['analysis_history', 'portfolio_accounts'],
  },
  data: {
    configuration: {
      values: {
        STOCK_LIST: '600519,000001',
        LLM_CHANNELS: 'primary,backup',
      },
    },
    tables: {
      analysis_history: [{ stock_code: '600519', analysis_summary: 'stored' }],
    },
  },
  integrity: { algorithm: 'sha256' as const, value: 'canonical-checksum' },
};

const canonicalJson = `${JSON.stringify(canonicalDocument)}\n`;

type ExportRequestConfig = {
  transformResponse: Array<(
    content: string,
    headers: Record<string, never>,
    status?: number,
  ) => unknown>;
};

function rejectExportWithBody(body: string, status: number) {
  get.mockImplementationOnce((_: string, config: ExportRequestConfig) => {
    const error = Object.assign(new Error(`Request failed with status code ${status}`), {
      response: {
        status,
        data: config.transformResponse[0](body, {}, status),
      },
    });
    attachParsedApiError(error);
    return Promise.reject(error);
  });
}

describe('fullDataBackupApi canonical document boundary', () => {
  beforeEach(() => {
    get.mockReset();
    post.mockReset();
  });

  it('keeps the exported canonical JSON bytes and trailing newline opaque', async () => {
    get.mockImplementationOnce((_: string, config: ExportRequestConfig) => {
      return Promise.resolve({
        data: config.transformResponse[0](canonicalJson, {}, 200),
        headers: {
          'content-disposition': 'attachment; filename="pp02-full-data-backup-20260804T090000Z.json"',
        },
      });
    });

    const result = await fullDataBackupApi.exportBackup();

    expect(get).toHaveBeenCalledWith('/api/v1/system/full-data-backup/export', {
      responseType: 'text',
      transformResponse: [expect.any(Function)],
    });
    expect(result.content).toBe(canonicalJson);
    expect(result.content).toContain('"STOCK_LIST"');
    expect(result.content).not.toContain('"stockList"');
    expect(result.content).not.toContain('"stock_list"');
  });

  it('decodes a rejected JSON error envelope for shared safe error handling', async () => {
    rejectExportWithBody(JSON.stringify({
      detail: {
        error: 'full_data_backup_unavailable',
        message: 'Complete backup export is temporarily unavailable.',
      },
    }), 409);

    const rejected = await fullDataBackupApi.exportBackup().catch((error: unknown) => error);
    const parsed = getParsedApiError(rejected);

    expect(parsed.status).toBe(409);
    expect(parsed.message).toBe('Complete backup export is temporarily unavailable.');
    expect(parsed.rawMessage).toBe('Complete backup export is temporarily unavailable.');
    expect(parsed.message).not.toContain('"detail"');
  });

  it('discards malformed rejected export text before shared error handling', async () => {
    const privateServerText = 'failure at /srv/private/runtime/backup.json payload=credential-secret';
    rejectExportWithBody(privateServerText, 500);

    const rejected = await fullDataBackupApi.exportBackup().catch((error: unknown) => error);
    const parsed = getParsedApiError(rejected);

    expect(parsed.status).toBe(500);
    expect(parsed.message).toBe('请求未成功完成（HTTP 500）。');
    expect(parsed.message).not.toContain(privateServerText);
    expect(parsed.rawMessage).not.toContain('/srv/private');
    expect(parsed.rawMessage).not.toContain('credential-secret');
  });

  it('passes the exact imported document through preview and restore while mapping only envelopes', async () => {
    post
      .mockResolvedValueOnce({
        data: {
          manifest: canonicalDocument.manifest,
          warnings: [],
          preview_token: 'preview-token-1',
          incoming_digest: 'incoming-digest',
          destination_digest: 'destination-digest',
          issued_at: '2026-08-04T09:01:00Z',
          expires_at: '2026-08-04T09:06:00Z',
          incoming_table_row_counts: { analysis_history: 1 },
          destination_table_row_counts: { analysis_history: 3 },
          restart_required: true,
        },
      })
      .mockResolvedValueOnce({
        data: {
          success: true,
          incoming_digest: 'incoming-digest',
          destination_digest_before: 'destination-digest',
          destination_digest_after: 'incoming-digest',
          restored_table_row_counts: { analysis_history: 1 },
          recovery_filename: 'safe-recovery.json',
          recovery: {
            filename: 'safe-recovery.json',
            digest: 'recovery-digest',
            destination_digest: 'destination-digest',
          },
          warnings: [
            'Recovery receipt cleanup must be completed after restart.',
            'Keep the recovery file until cleanup is confirmed.',
          ],
          restart_required: true,
        },
      });

    const preview = await fullDataBackupApi.previewRestore(canonicalDocument);
    const restore = await fullDataBackupApi.restore({
      backup: canonicalDocument,
      previewToken: preview.previewToken,
    });

    expect(post.mock.calls[0][1]).toBe(canonicalDocument);
    expect(post.mock.calls[1][1].backup).toBe(canonicalDocument);
    expect(post.mock.calls[1][1]).toEqual({
      backup: canonicalDocument,
      preview_token: 'preview-token-1',
    });
    expect(canonicalDocument.data.configuration.values.STOCK_LIST).toBe('600519,000001');
    expect(preview.incomingTableRowCounts).toEqual({ analysis_history: 1 });
    expect(restore.recovery.destinationDigest).toBe('destination-digest');
    expect(restore.warnings).toEqual([
      'Recovery receipt cleanup must be completed after restart.',
      'Keep the recovery file until cleanup is confirmed.',
    ]);
  });
});
