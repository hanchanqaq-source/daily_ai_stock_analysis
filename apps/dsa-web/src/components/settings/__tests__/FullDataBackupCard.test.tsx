import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fullDataBackupApi } from '../../../api/fullDataBackup';
import { UiLanguageProvider } from '../../../contexts/UiLanguageContext';
import { UI_LANGUAGE_STORAGE_KEY } from '../../../utils/uiLanguage';
import FullDataBackupCard from '../FullDataBackupCard';

vi.mock('../../../api/fullDataBackup', () => ({
  fullDataBackupApi: {
    exportBackup: vi.fn(),
    previewRestore: vi.fn(),
    restore: vi.fn(),
  },
}));

const backup = {
  format: 'pp02.full-data.backup' as const,
  format_version: 1 as const,
  metadata: { created_at: '2026-08-04T09:00:00Z' },
  manifest: { table_names: ['analysis_history', 'portfolio_accounts'] },
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

describe('FullDataBackupCard', () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.clearAllMocks();
    window.localStorage.clear();
    vi.mocked(fullDataBackupApi.exportBackup).mockResolvedValue({
      fileName: 'pp02-full-data-backup-20260804T090000Z.json',
      content: canonicalJson,
    });
    vi.mocked(fullDataBackupApi.previewRestore).mockResolvedValue(preview);
    vi.mocked(fullDataBackupApi.restore).mockResolvedValue({
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
    expect(screen.queryByText('/srv/private/runtime/recovery.json')).not.toBeInTheDocument();
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
