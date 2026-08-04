import type React from 'react';
import { useRef, useState } from 'react';
import { createParsedApiError, getParsedApiError, type ParsedApiError } from '../../api/error';
import { fullDataBackupApi } from '../../api/fullDataBackup';
import { useUiLanguage } from '../../contexts/UiLanguageContext';
import type { UiTextKey } from '../../i18n/uiText';
import type {
  FullDataBackupDocument,
  FullDataBackupPreviewResponse,
  FullDataBackupRestoreResponse,
} from '../../types/fullDataBackup';
import { ApiErrorAlert, Button, InlineAlert } from '../common';
import { SettingsSectionCard } from './SettingsSectionCard';

function RowCounts({ counts }: { counts: Record<string, number> }) {
  return (
    <div className="grid gap-1 text-xs text-secondary-text sm:grid-cols-2">
      {Object.entries(counts).map(([table, count]) => (
        <p key={table}>{table}：{count}</p>
      ))}
    </div>
  );
}

type ManifestCategory = {
  name: string;
  status: 'supported' | 'not_applicable';
  rowCount: number;
};

type ManifestExcludedTable = {
  name: string;
  classification: string;
  restoreBehavior: string;
  rebuildEntrypoint: string;
};

const MANIFEST_CATEGORY_LABEL_KEYS: Record<string, UiTextKey> = {
  agent_conversations: 'settings.fullBackupManifestCategoryAgentConversations',
  analysis: 'settings.fullBackupManifestCategoryAnalysis',
  configuration: 'settings.fullBackupManifestCategoryConfiguration',
  fund: 'settings.fullBackupManifestCategoryFund',
  period_reports: 'settings.fullBackupManifestCategoryPeriodReports',
  portfolio_events: 'settings.fullBackupManifestCategoryPortfolioEvents',
  structured_user_records: 'settings.fullBackupManifestCategoryStructuredRecords',
};

const MANIFEST_EXCLUSION_LABEL_KEYS: Record<string, UiTextKey> = {
  derived_portfolio_caches: 'settings.fullBackupManifestExclusionDerivedPortfolio',
  rebuildable_price_news_caches: 'settings.fullBackupManifestExclusionMarketCaches',
  scheduler_runtime_state: 'settings.fullBackupManifestExclusionSchedulerState',
  provider_traces: 'settings.fullBackupManifestExclusionProviderTraces',
  logs: 'settings.fullBackupManifestExclusionLogs',
  drafts: 'settings.fullBackupManifestExclusionDrafts',
  schema_bookkeeping: 'settings.fullBackupManifestExclusionSchemaBookkeeping',
  credentials_tokens_cookies_vault_ciphertext: 'settings.fullBackupManifestExclusionCredentials',
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function readManifestCategories(manifest: Record<string, unknown>): ManifestCategory[] {
  const categories = manifest.categories;
  if (!isRecord(categories)) {
    return [];
  }
  return Object.entries(categories).flatMap(([name, candidate]) => {
    if (!isRecord(candidate)) {
      return [];
    }
    const status = candidate.status;
    const rowCount = candidate.row_count;
    if (
      (status !== 'supported' && status !== 'not_applicable')
      || typeof rowCount !== 'number'
      || !Number.isSafeInteger(rowCount)
      || rowCount < 0
    ) {
      return [];
    }
    return [{ name, status, rowCount }];
  });
}

function readManifestExclusions(manifest: Record<string, unknown>): string[] {
  if (!Array.isArray(manifest.excluded)) {
    return [];
  }
  return manifest.excluded.filter(
    (value): value is string => typeof value === 'string' && value.trim().length > 0,
  );
}

function readManifestExcludedTables(
  manifest: Record<string, unknown>,
): ManifestExcludedTable[] {
  if (!isRecord(manifest.excluded_tables)) {
    return [];
  }
  return Object.entries(manifest.excluded_tables).flatMap(([name, candidate]) => {
    if (!isRecord(candidate)) {
      return [];
    }
    const classification = candidate.classification;
    const containsUserData = candidate.contains_user_data;
    const restoreBehavior = candidate.restore_behavior;
    const rebuildEntrypoint = candidate.rebuild_entrypoint;
    if (
      typeof classification !== 'string'
      || classification.trim().length === 0
      || containsUserData !== false
      || typeof restoreBehavior !== 'string'
      || restoreBehavior.trim().length === 0
      || typeof rebuildEntrypoint !== 'string'
      || rebuildEntrypoint.trim().length === 0
    ) {
      return [];
    }
    return [{ name, classification, restoreBehavior, rebuildEntrypoint }];
  });
}

function getOwnLabelKey(
  labels: Record<string, UiTextKey>,
  name: string,
): UiTextKey | undefined {
  return Object.hasOwn(labels, name) ? labels[name] : undefined;
}

function ManifestSummary({ manifest }: { manifest: Record<string, unknown> }) {
  const { t } = useUiLanguage();
  const categories = readManifestCategories(manifest);
  const exclusions = readManifestExclusions(manifest);
  const excludedTables = readManifestExcludedTables(manifest);

  return (
    <div className="space-y-3">
      <div>
        <p className="mb-1 text-xs font-medium text-foreground">
          {t('settings.fullBackupManifestCategories')}
        </p>
        <ul className="space-y-1 text-xs text-secondary-text">
          {categories.map(({ name, status, rowCount }) => {
            const labelKey = getOwnLabelKey(MANIFEST_CATEGORY_LABEL_KEYS, name);
            const label = labelKey ? t(labelKey) : name;
            const statusLabel = t(
              status === 'supported'
                ? 'settings.fullBackupManifestStatusSupported'
                : 'settings.fullBackupManifestStatusNotApplicable',
            );
            return (
              <li key={name}>
                {t(
                  rowCount === 1
                    ? 'settings.fullBackupManifestCategoryRowOne'
                    : 'settings.fullBackupManifestCategoryRowMany',
                  { label, name, status: statusLabel, count: rowCount },
                )}
              </li>
            );
          })}
        </ul>
      </div>
      <div>
        <p className="mb-1 text-xs font-medium text-foreground">
          {t('settings.fullBackupManifestExclusions')}
        </p>
        <ul className="space-y-1 text-xs text-secondary-text">
          {exclusions.map((name, index) => {
            const labelKey = getOwnLabelKey(MANIFEST_EXCLUSION_LABEL_KEYS, name);
            const label = labelKey ? t(labelKey) : name;
            return (
              <li key={`${name}-${index}`}>
                {t('settings.fullBackupManifestExclusionRow', { label, name })}
              </li>
            );
          })}
        </ul>
      </div>
      {excludedTables.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-medium text-foreground">
            {t('settings.fullBackupManifestExcludedTables')}
          </p>
          <ul className="space-y-1 text-xs text-secondary-text">
            {excludedTables.map((table) => (
              <li key={table.name}>
                {t('settings.fullBackupManifestExcludedTableRow', {
                  name: table.name,
                  classification: table.classification,
                  restoreBehavior: table.restoreBehavior,
                  rebuildEntrypoint: table.rebuildEntrypoint,
                })}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

const FullDataBackupCard = () => {
  const { t } = useUiLanguage();
  const [backup, setBackup] = useState<FullDataBackupDocument | null>(null);
  const [preview, setPreview] = useState<FullDataBackupPreviewResponse | null>(null);
  const [result, setResult] = useState<FullDataBackupRestoreResponse | null>(null);
  const [error, setError] = useState<ParsedApiError | null>(null);
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState<'export' | 'preview' | 'restore' | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const restoreInFlightRef = useRef(false);

  const exportBackup = async () => {
    setBusy('export');
    setError(null);
    setSuccess('');
    try {
      const exported = await fullDataBackupApi.exportBackup();
      const blob = new Blob([exported.content], {
        type: 'application/json;charset=utf-8',
      });
      let url: string | null = null;
      let anchor: HTMLAnchorElement | null = null;
      try {
        url = URL.createObjectURL(blob);
        anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = exported.fileName;
        document.body.appendChild(anchor);
        anchor.click();
        setSuccess(t('settings.fullBackupExported'));
      } finally {
        anchor?.remove();
        if (url) {
          URL.revokeObjectURL(url);
        }
      }
    } catch (requestError: unknown) {
      setError(getParsedApiError(requestError));
    } finally {
      setBusy(null);
    }
  };

  const previewFile = async (file: File | null) => {
    setBackup(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setSuccess('');
    if (!file) {
      return;
    }
    setBusy('preview');
    try {
      const parsed = JSON.parse(await file.text()) as FullDataBackupDocument;
      const nextPreview = await fullDataBackupApi.previewRestore(parsed);
      setBackup(parsed);
      setPreview(nextPreview);
    } catch (requestError: unknown) {
      if (requestError instanceof SyntaxError) {
        setError(createParsedApiError({
          title: t('settings.fullBackupPreview'),
          message: t('settings.fullBackupInvalidFile'),
          category: 'http_error',
        }));
      } else {
        setError(getParsedApiError(requestError));
      }
    } finally {
      setBusy(null);
    }
  };

  const restore = async () => {
    if (!backup || !preview || busy || restoreInFlightRef.current) {
      return;
    }
    const restoreBackup = backup;
    const previewToken = preview.previewToken;
    restoreInFlightRef.current = true;
    setBackup(null);
    setPreview(null);
    setBusy('restore');
    setError(null);
    setSuccess('');
    try {
      const restored = await fullDataBackupApi.restore({
        backup: restoreBackup,
        previewToken,
      });
      setResult(restored);
      setSuccess(t('settings.fullBackupRestored'));
    } catch (requestError: unknown) {
      setError(getParsedApiError(requestError));
    } finally {
      restoreInFlightRef.current = false;
      setBusy(null);
    }
  };

  return (
    <SettingsSectionCard
      title={t('settings.fullBackup')}
      description={t('settings.fullBackupDescription')}
    >
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="button"
            variant="settings-secondary"
            onClick={() => void exportBackup()}
            disabled={busy !== null}
            isLoading={busy === 'export'}
            loadingText={t('settings.fullBackupProcessing')}
          >
            {t('settings.fullBackupExport')}
          </Button>
          <Button
            type="button"
            variant="settings-primary"
            disabled={busy !== null}
            onClick={() => fileInputRef.current?.click()}
            onKeyDown={(event: React.KeyboardEvent<HTMLButtonElement>) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                fileInputRef.current?.click();
              }
            }}
          >
            {busy === 'preview' ? t('settings.fullBackupProcessing') : t('settings.fullBackupChoose')}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,application/json"
            aria-label={t('settings.fullBackupChoose')}
            className="hidden"
            disabled={busy !== null}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              const file = event.target.files?.[0] || null;
              event.target.value = '';
              void previewFile(file);
            }}
          />
        </div>

        {preview ? (
          <section aria-label={t('settings.fullBackupPreview')} className="space-y-3 rounded-xl border border-amber-400/30 bg-amber-500/5 p-4">
            <h3 className="text-sm font-semibold text-foreground">{t('settings.fullBackupPreview')}</h3>
            <ManifestSummary manifest={preview.manifest} />
            <div>
              <p className="mb-1 text-xs font-medium text-foreground">{t('settings.fullBackupIncomingCounts')}</p>
              <RowCounts counts={preview.incomingTableRowCounts} />
            </div>
            <div>
              <p className="mb-1 text-xs font-medium text-foreground">{t('settings.fullBackupCurrentCounts')}</p>
              <RowCounts counts={preview.destinationTableRowCounts} />
            </div>
            <div>
              <p className="mb-1 text-xs font-medium text-foreground">{t('settings.fullBackupWarnings')}</p>
              {preview.warnings.length > 0 ? preview.warnings.map((warning) => (
                <p key={warning} className="text-xs text-amber-700 dark:text-amber-300">{warning}</p>
              )) : (
                <p className="text-xs text-secondary-text">{t('settings.fullBackupNoWarnings')}</p>
              )}
            </div>
            {preview.restartRequired ? (
              <InlineAlert variant="warning" message={t('settings.fullBackupRestartRequired')} />
            ) : null}
            <Button
              type="button"
              variant="danger"
              onClick={() => void restore()}
              disabled={busy !== null}
              isLoading={busy === 'restore'}
              loadingText={t('settings.fullBackupProcessing')}
            >
              {t('settings.fullBackupConfirm')}
            </Button>
          </section>
        ) : null}

        {result ? (
          <div className="space-y-2 rounded-xl border border-emerald-400/30 bg-emerald-500/5 p-4 text-xs text-secondary-text">
            <p>{t('settings.fullBackupRecoveryFile')}：{result.recovery.filename}</p>
            <p className="font-medium text-foreground">{t('settings.fullBackupRestoredCounts')}</p>
            <RowCounts counts={result.restoredTableRowCounts} />
            {result.warnings?.length > 0 ? (
              <div>
                <p className="font-medium text-amber-700 dark:text-amber-300">
                  {t('settings.fullBackupRestoreWarnings')}
                </p>
                {result.warnings.map((warning, index) => (
                  <p key={`${warning}-${index}`} className="text-amber-700 dark:text-amber-300">
                    {warning}
                  </p>
                ))}
              </div>
            ) : null}
            {result.restartRequired ? <p>{t('settings.fullBackupRestartResult')}</p> : null}
          </div>
        ) : null}

        {error ? <ApiErrorAlert error={error} /> : null}
        {!error && success ? <InlineAlert variant="success" message={success} /> : null}
      </div>
    </SettingsSectionCard>
  );
};

export default FullDataBackupCard;
