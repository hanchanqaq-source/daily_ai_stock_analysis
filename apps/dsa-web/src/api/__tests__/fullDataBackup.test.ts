import { beforeEach, describe, expect, it, vi } from 'vitest';
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

describe('fullDataBackupApi canonical document boundary', () => {
  beforeEach(() => {
    get.mockReset();
    post.mockReset();
  });

  it('keeps the exported canonical JSON byte content opaque', async () => {
    get.mockResolvedValue({
      data: canonicalJson,
      headers: {
        'content-disposition': 'attachment; filename="pp02-full-data-backup-20260804T090000Z.json"',
      },
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
  });
});
