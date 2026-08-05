import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { attachParsedApiError } from '../../../api/error';
import { fullDataBackupApi } from '../../../api/fullDataBackup';
import { UiLanguageProvider } from '../../../contexts/UiLanguageContext';
import { UI_LANGUAGE_STORAGE_KEY } from '../../../utils/uiLanguage';
import FullDataBackupCard from '../FullDataBackupCard';

const get = vi.hoisted(() => vi.fn());
const post = vi.hoisted(() => vi.fn());

vi.mock('../../../api/index', () => ({
  default: { get, post },
}));

const backup = {
  format: 'pp02.full-data.backup' as const,
  format_version: 1 as const,
  metadata: { created_at: '2026-08-04T09:00:00Z' },
  manifest: {
    categories: {
      agent_conversations: {
        status: 'supported',
        row_count: 4,
        tables: ['agent_conversations'],
      },
      analysis: { status: 'supported', row_count: 7, tables: ['analysis_history'] },
      configuration: { status: 'supported', row_count: 1, tables: ['configuration'] },
      fund: { status: 'not_applicable', row_count: 0, tables: [] },
      period_reports: { status: 'supported', row_count: 3, tables: ['period_reports'] },
      portfolio_events: {
        status: 'supported',
        row_count: 9,
        tables: [
          'portfolio_accounts',
          'portfolio_trades',
          'portfolio_cash_ledger',
          'portfolio_corporate_actions',
        ],
      },
      structured_user_records: {
        status: 'supported',
        row_count: 5,
        tables: ['alert_rules', 'decision_signals'],
      },
    },
    excluded: [
      'derived_portfolio_caches',
      'rebuildable_price_news_caches',
      'scheduler_runtime_state',
      'provider_traces',
      'logs',
      'drafts',
      'schema_bookkeeping',
      'credentials_tokens_cookies_vault_ciphertext',
    ],
    excluded_tables: {
      stock_daily: {
        classification: 'rebuildable_market_data_cache',
        contains_user_data: false,
        restore_behavior: 'cleared_then_rebuilt_on_demand',
        rebuild_entrypoint: 'get_daily_history',
      },
    },
    table_row_counts: {
      analysis_history: 7,
      period_reports: 3,
      portfolio_accounts: 2,
    },
  },
  data: {
    configuration: { values: { STOCK_LIST: '600519,000001' } },
    tables: { analysis_history: [], portfolio_accounts: [] },
  },
  integrity: { algorithm: 'sha256' as const, value: 'incoming-digest' },
};
const canonicalJson = `${JSON.stringify(backup)}\n`;

const preview = {
  manifest: backup.manifest,
  warnings: ['Current formal user data will be replaced.'],
  previewToken: 'preview-token-1',
  incomingDigest: 'incoming-digest',
  destinationDigest: 'destination-digest',
  issuedAt: '2026-08-04T09:01:00Z',
  expiresAt: '2026-08-04T09:06:00Z',
  incomingTableRowCounts: { analysis_history: 7, portfolio_accounts: 2 },
  destinationTableRowCounts: { analysis_history: 3, portfolio_accounts: 1 },
  restartRequired: true,
};

function renderCard(language: 'zh' | 'en' = 'zh') {
  window.localStorage.setItem(UI_LANGUAGE_STORAGE_KEY, language);
  return render(
    <UiLanguageProvider>
      <FullDataBackupCard />
    </UiLanguageProvider>,
  );
}

function makeBackupFile(content = canonicalJson) {
  const file = new File([content], 'complete-backup.json', {
    type: 'application/json',
  });
  Object.defineProperty(file, 'text', {
    value: vi.fn().mockResolvedValue(content),
  });
  return file;
}

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
}

type ExportRequestConfig = {
  transformResponse: Array<(
    content: string,
    headers: Record<string, never>,
    status?: number,
  ) => unknown>;
};

function rejectActualExportWithBody(body: string, status: number) {
  vi.mocked(fullDataBackupApi.exportBackup).mockRestore();
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

describe('FullDataBackupCard', () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.clearAllMocks();
    get.mockReset();
    post.mockReset();
    window.localStorage.clear();
    vi.spyOn(fullDataBackupApi, 'exportBackup').mockResolvedValue({
      fileName: 'pp02-full-data-backup-20260804T090000Z.json',
      content: canonicalJson,
    });
    vi.spyOn(fullDataBackupApi, 'previewRestore').mockResolvedValue(preview);
    vi.spyOn(fullDataBackupApi, 'restore').mockResolvedValue({
      success: true,
      incomingDigest: 'incoming-digest',
      destinationDigestBefore: 'destination-digest',
      destinationDigestAfter: 'incoming-digest',
      restoredTableRowCounts: { analysis_history: 7, portfolio_accounts: 2 },
      recoveryFilename: 'pp02-full-data-recovery-20260804T090200Z.json',
      recovery: {
        filename: 'pp02-full-data-recovery-20260804T090200Z.json',
        digest: 'recovery-digest',
        destinationDigest: 'destination-digest',
        path: '/srv/private/runtime/recovery.json',
      },
      restartRequired: true,
      warnings: [
        'Recovery receipt cleanup must be completed after restart.',
        'Keep the recovery file until cleanup is confirmed.',
      ],
    } as never);
  });

  it('downloads the exact canonical JSON without changing configuration keys', async () => {
    let blobParts: BlobPart[] = [];
    vi.stubGlobal('Blob', class {
      constructor(parts: BlobPart[]) {
        blobParts = parts;
      }
    });
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    const createObjectUrl = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:full-backup');
    const revokeObjectUrl = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    renderCard();

    expect(fullDataBackupApi.exportBackup).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: '导出完整数据备份' }));

    await waitFor(() => expect(fullDataBackupApi.exportBackup).toHaveBeenCalledTimes(1));
    expect(createObjectUrl).toHaveBeenCalledWith(expect.any(Blob));
    expect(anchorClick).toHaveBeenCalledTimes(1);
    expect(revokeObjectUrl).toHaveBeenCalledWith('blob:full-backup');
    expect(blobParts).toEqual([canonicalJson]);
    expect(String(blobParts[0])).toContain('"STOCK_LIST"');
  });

  it('shows the decoded safe message from a rejected JSON export envelope', async () => {
    const serializedEnvelope = JSON.stringify({
      detail: {
        error: 'full_data_backup_unavailable',
        message: 'Complete backup export is temporarily unavailable.',
      },
    });
    rejectActualExportWithBody(serializedEnvelope, 409);
    renderCard();

    fireEvent.click(screen.getByRole('button', { name: '导出完整数据备份' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Complete backup export is temporarily unavailable.');
    expect(alert).not.toHaveTextContent(serializedEnvelope);
    expect(alert).not.toHaveTextContent('"detail"');
  });

  it('shows a generic safe message without leaking malformed export error text', async () => {
    const privateServerText = 'failure at /srv/private/runtime/backup.json payload=credential-secret';
    rejectActualExportWithBody(privateServerText, 500);
    renderCard();

    fireEvent.click(screen.getByRole('button', { name: '导出完整数据备份' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('请求未成功完成（HTTP 500）。');
    expect(alert).not.toHaveTextContent(privateServerText);
    expect(alert).not.toHaveTextContent('/srv/private');
    expect(alert).not.toHaveTextContent('credential-secret');
  });

  it('cleans up the temporary anchor and object URL when download click throws', async () => {
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {
      throw new Error('download blocked');
    });
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:full-backup-error');
    const revokeObjectUrl = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    renderCard();

    fireEvent.click(screen.getByRole('button', { name: '导出完整数据备份' }));

    expect(await screen.findByText(/download blocked/i)).toBeInTheDocument();
    expect(document.body.querySelector('a[download]')).toBeNull();
    expect(revokeObjectUrl).toHaveBeenCalledWith('blob:full-backup-error');
  });

  it('uses a focusable named button to activate the hidden file input', () => {
    const { container } = renderCard();
    const chooseButton = screen.getByRole('button', { name: '选择完整数据备份 JSON' });
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const inputClick = vi.spyOn(fileInput, 'click').mockImplementation(() => undefined);

    chooseButton.focus();
    expect(chooseButton).toHaveFocus();
    expect(chooseButton.tagName).toBe('BUTTON');
    fireEvent.keyDown(chooseButton, { key: 'Enter', code: 'Enter' });
    expect(inputClick).toHaveBeenCalledTimes(1);
    fireEvent.click(chooseButton);
    expect(inputClick).toHaveBeenCalledTimes(2);
  });

  it('previews counts and warnings, then restores only after explicit confirmation', async () => {
    const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => undefined);
    const storageWrite = vi.spyOn(Storage.prototype, 'setItem');
    const { container } = renderCard();
    consoleLog.mockClear();
    storageWrite.mockClear();
    const file = makeBackupFile();

    fireEvent.change(container.querySelector('input[type="file"]') as HTMLInputElement, {
      target: { files: [file] },
    });

    await waitFor(() => expect(fullDataBackupApi.previewRestore).toHaveBeenCalledWith(backup));
    const previewedBackup = vi.mocked(fullDataBackupApi.previewRestore).mock.calls[0][0];
    expect(previewedBackup.data.configuration).toEqual({ values: { STOCK_LIST: '600519,000001' } });
    expect(screen.getByText(/analysis_history：7/)).toBeInTheDocument();
    expect(screen.getByText(/portfolio_accounts：2/)).toBeInTheDocument();
    expect(screen.getByText('Current formal user data will be replaced.')).toBeInTheDocument();
    expect(screen.getByText(/恢复后需要重启/)).toBeInTheDocument();
    expect(fullDataBackupApi.restore).not.toHaveBeenCalled();
    expect(consoleLog).not.toHaveBeenCalled();
    expect(storageWrite).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: '确认恢复并替换当前完整数据' }));

    await waitFor(() => {
      expect(fullDataBackupApi.restore).toHaveBeenCalledWith({
        backup: previewedBackup,
        previewToken: 'preview-token-1',
      });
    });
    expect(vi.mocked(fullDataBackupApi.restore).mock.calls[0][0].backup).toBe(previewedBackup);
    expect(await screen.findByText(/完整数据恢复完成/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '确认恢复并替换当前完整数据' })).not.toBeInTheDocument();
    expect(screen.getByText(/pp02-full-data-recovery-20260804T090200Z.json/)).toBeInTheDocument();
    expect(screen.getByText('Recovery receipt cleanup must be completed after restart.')).toBeInTheDocument();
    expect(screen.getByText('Keep the recovery file until cleanup is confirmed.')).toBeInTheDocument();
    expect(screen.queryByText('/srv/private/runtime/recovery.json')).not.toBeInTheDocument();
  });

  it('shows every manifest category, configuration coverage, and exclusion before destructive confirmation', async () => {
    const { container } = renderCard('en');

    fireEvent.change(container.querySelector('input[type="file"]') as HTMLInputElement, {
      target: { files: [makeBackupFile()] },
    });

    const confirmation = await screen.findByRole('button', {
      name: 'Confirm restore and replace current complete data',
    });
    const previewSection = screen.getByRole('region', { name: 'Restore preview' });

    expect(previewSection).toContainElement(confirmation);
    expect(previewSection).toHaveTextContent('Backup manifest categories');
    expect(previewSection).toHaveTextContent('AI agent conversations (agent_conversations)');
    expect(previewSection).toHaveTextContent('Analysis histories (analysis)');
    expect(previewSection).toHaveTextContent('Configuration (configuration)');
    expect(previewSection).toHaveTextContent('Supported · 1 row');
    expect(previewSection).toHaveTextContent('Fund records (fund)');
    expect(previewSection).toHaveTextContent('Not applicable · 0 rows');
    expect(previewSection).toHaveTextContent('Period reports (period_reports)');
    expect(previewSection).toHaveTextContent('Portfolio ledger events (portfolio_events)');
    expect(previewSection).toHaveTextContent('Other formal user records (structured_user_records)');

    expect(previewSection).toHaveTextContent('Explicitly excluded from this backup');
    for (const exclusion of [
      'Derived portfolio caches (derived_portfolio_caches)',
      'Rebuildable price and news caches (rebuildable_price_news_caches)',
      'Scheduler runtime state (scheduler_runtime_state)',
      'Provider traces (provider_traces)',
      'Logs (logs)',
      'Unsaved drafts (drafts)',
      'Database schema bookkeeping (schema_bookkeeping)',
      'Credentials, tokens, cookies, and vault ciphertext (credentials_tokens_cookies_vault_ciphertext)',
    ]) {
      expect(previewSection).toHaveTextContent(exclusion);
    }
    expect(previewSection).toHaveTextContent('Excluded database tables and rebuild contract');
    expect(previewSection).toHaveTextContent(
      'stock_daily: rebuildable_market_data_cache · no user data · cleared_then_rebuilt_on_demand · get_daily_history',
    );
    expect(fullDataBackupApi.restore).not.toHaveBeenCalled();
  });

  it('uses Chinese manifest copy and safely degrades malformed nested manifest values', async () => {
    vi.mocked(fullDataBackupApi.previewRestore).mockResolvedValueOnce({
      ...preview,
      manifest: {
        categories: {
          configuration: { status: 'supported', row_count: 1, tables: ['configuration'] },
          malformed_null: null,
          malformed_array: ['supported', 99],
          malformed_fields: { status: { unsafe: true }, row_count: '99' },
        },
        excluded: ['drafts', { unsafe: 'do-not-render' }, null, 'logs'],
        excluded_tables: {
          safe_cache: {
            classification: 'rebuildable_cache',
            contains_user_data: false,
            restore_behavior: 'cleared',
            rebuild_entrypoint: 'safe_rebuild',
          },
          malformed_null: null,
          malformed_user_data: {
            classification: 'cache',
            contains_user_data: true,
            restore_behavior: 'kept',
            rebuild_entrypoint: 'none',
          },
        },
      },
    } as never);
    const { container } = renderCard('zh');

    fireEvent.change(container.querySelector('input[type="file"]') as HTMLInputElement, {
      target: { files: [makeBackupFile()] },
    });

    const previewSection = await screen.findByRole('region', { name: '恢复预览' });
    expect(previewSection).toHaveTextContent('备份清单类别');
    expect(previewSection).toHaveTextContent('配置（configuration）');
    expect(previewSection).toHaveTextContent('支持 · 1 条');
    expect(previewSection).toHaveTextContent('此备份明确排除');
    expect(previewSection).toHaveTextContent('未保存草稿（drafts）');
    expect(previewSection).toHaveTextContent('日志（logs）');
    expect(previewSection).toHaveTextContent('排除的数据库表与重建约定');
    expect(previewSection).toHaveTextContent(
      'safe_cache：rebuildable_cache · 不含用户数据 · cleared · safe_rebuild',
    );
    expect(previewSection).not.toHaveTextContent('do-not-render');
    expect(previewSection).not.toHaveTextContent('malformed_null');
    expect(previewSection).not.toHaveTextContent('malformed_array');
    expect(previewSection).not.toHaveTextContent('malformed_fields');
    expect(previewSection).not.toHaveTextContent('malformed_user_data');
    expect(screen.getByRole('button', { name: '确认恢复并替换当前完整数据' })).toBeInTheDocument();
  });

  it('renders inherited object names as safe raw manifest text without crashing', async () => {
    vi.mocked(fullDataBackupApi.previewRestore).mockResolvedValueOnce({
      ...preview,
      manifest: {
        categories: JSON.parse(`{
          "__proto__": {"status": "supported", "row_count": 1},
          "constructor": {"status": "supported", "row_count": 2},
          "toString": {"status": "not_applicable", "row_count": 0}
        }`),
        excluded: ['__proto__', 'constructor', 'toString'],
      },
    } as never);
    const { container } = renderCard('en');

    fireEvent.change(container.querySelector('input[type="file"]') as HTMLInputElement, {
      target: { files: [makeBackupFile()] },
    });

    const previewSection = await screen.findByRole('region', { name: 'Restore preview' });
    expect(previewSection).toHaveTextContent('__proto__ (__proto__): Supported · 1 row');
    expect(previewSection).toHaveTextContent('constructor (constructor): Supported · 2 rows');
    expect(previewSection).toHaveTextContent('toString (toString): Not applicable · 0 rows');
    expect(previewSection).toHaveTextContent('__proto__ (__proto__)');
    expect(previewSection).toHaveTextContent('constructor (constructor)');
    expect(previewSection).toHaveTextContent('toString (toString)');
    expect(previewSection).not.toHaveTextContent('{label}');
    expect(screen.getByRole('button', {
      name: 'Confirm restore and replace current complete data',
    })).toBeInTheDocument();
  });

  it('consumes a preview before restore and requires a fresh preview after an ambiguous failure', async () => {
    const deferredRestore = createDeferred<never>();
    vi.mocked(fullDataBackupApi.restore).mockReturnValue(deferredRestore.promise);
    const { container } = renderCard();
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(fileInput, { target: { files: [makeBackupFile()] } });
    const confirm = await screen.findByRole('button', { name: '确认恢复并替换当前完整数据' });
    fireEvent.click(confirm);
    fireEvent.click(confirm);

    expect(fullDataBackupApi.restore).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('button', { name: '确认恢复并替换当前完整数据' })).not.toBeInTheDocument();
    await act(async () => {
      deferredRestore.reject(new Error('network outcome unknown'));
      await deferredRestore.promise.catch(() => undefined);
    });
    expect(await screen.findByText(/network outcome unknown/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '确认恢复并替换当前完整数据' })).not.toBeInTheDocument();

    fireEvent.change(fileInput, { target: { files: [makeBackupFile()] } });
    await waitFor(() => expect(fullDataBackupApi.previewRestore).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole('button', { name: '确认恢复并替换当前完整数据' })).toBeInTheDocument();
  });

  it('shows a safe error and does not preview malformed JSON', async () => {
    const { container } = renderCard();
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(fileInput, { target: { files: [makeBackupFile('{not-json')] } });

    expect(await screen.findByText('所选文件不是有效的 JSON 备份。')).toBeInTheDocument();
    expect(fullDataBackupApi.previewRestore).not.toHaveBeenCalled();
  });

  it('distinguishes complete formal user data from credentials, drafts, and runtime paths in English', () => {
    renderCard('en');

    expect(screen.getByRole('heading', { name: 'Complete data backup and restore' })).toBeInTheDocument();
    expect(screen.getByText(/complete formal user data/i)).toBeInTheDocument();
    expect(screen.getByText(/excludes credentials, unsaved drafts, and service runtime paths/i)).toBeInTheDocument();
  });
});
