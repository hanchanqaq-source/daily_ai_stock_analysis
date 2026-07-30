import { CalendarRange, Database, FileClock, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { getParsedApiError, type ParsedApiError } from '../api/error';
import { periodReportApi } from '../api/periodReport';
import {
  ApiErrorAlert,
  AppPage,
  Badge,
  Button,
  Card,
  EmptyState,
  InlineAlert,
  PageHeader,
} from '../components/common';
import { useUiLanguage } from '../contexts/UiLanguageContext';
import type { UiLanguage } from '../i18n/uiText';
import type {
  OutlookTendency,
  PeriodAssetSummary,
  PeriodMarketReview,
  PeriodOutlookItem,
  PeriodOutlookSnapshot,
  PeriodReportKey,
  PeriodReportResponse,
} from '../types/periodReport';
import { cn } from '../utils/cn';

const PERIODS: PeriodReportKey[] = [
  'week_to_date',
  'previous_week',
  'next_week',
  'weeks_5',
  'weeks_10',
  'month_1',
  'months_2',
];

const COPY = {
  zh: {
    eyebrow: 'Period reports',
    title: '周期报告',
    description: '手动汇总已保存的正式分析与市场复盘历史，并基于近期有效记录形成下周参考展望。',
    generate: '生成报告',
    generating: '正在生成',
    initialTitle: '尚未生成周期报告',
    initialDescription: '选择一个周期后手动生成；打开页面不会自动运行，也不会发送通知。',
    periods: {
      week_to_date: '本周至今',
      previous_week: '上一周',
      next_week: '下周展望',
      weeks_5: '5周',
      weeks_10: '10周',
      month_1: '1个月',
      months_2: '2个月',
    },
    reportRange: '报告区间',
    generatedAt: '生成时间',
    sourceRecords: '来源记录',
    sourceIds: '来源标识',
    snapshot: '快照',
    stockSummary: '股票分析汇总',
    etfSummary: 'ETF 分析汇总',
    marketReviews: '市场复盘',
    noStockSummary: '本周期没有股票正式分析记录。',
    noEtfSummary: '本周期没有 ETF 正式分析记录。',
    noMarketReviews: '本周期没有市场复盘记录。',
    records: '条记录',
    latest: '最近记录',
    directionCounts: '方向统计',
    bullish: '看多',
    neutral: '中性',
    bearish: '看空',
    unknown: '未判断',
    outlookResult: '下周展望结果',
    overallTendency: '总体倾向',
    confidence: '置信度',
    historicalSignals: '主要历史信号',
    risks: '主要风险',
    invalidation: '判断失效条件',
    dataAsOf: '数据截至',
    stockOutlook: '股票展望',
    etfOutlook: 'ETF 展望',
    marketSignals: '市场复盘信号',
    noStockOutlook: '没有可形成展望的股票记录。',
    noEtfOutlook: '没有可形成展望的 ETF 记录。',
    priorReview: '上周展望与实际复盘',
    priorOutlook: '上周展望',
    actualSummary: '实际周期汇总',
    errorTitle: '周期报告生成失败',
    retry: '重新生成',
  },
  en: {
    eyebrow: 'Period reports',
    title: 'Period reports',
    description: 'Manually aggregate saved formal analyses and market reviews, with a conditional next-week outlook from recent qualifying records.',
    generate: 'Generate report',
    generating: 'Generating',
    initialTitle: 'No period report generated',
    initialDescription: 'Choose a period and generate it manually. Opening this page does not run a report or send a notification.',
    periods: {
      week_to_date: 'Week to date',
      previous_week: 'Previous week',
      next_week: 'Next-week outlook',
      weeks_5: '5 weeks',
      weeks_10: '10 weeks',
      month_1: '1 month',
      months_2: '2 months',
    },
    reportRange: 'Report range',
    generatedAt: 'Generated at',
    sourceRecords: 'Source records',
    sourceIds: 'Source IDs',
    snapshot: 'Snapshot',
    stockSummary: 'Stock analysis summary',
    etfSummary: 'ETF analysis summary',
    marketReviews: 'Market reviews',
    noStockSummary: 'No formal stock analysis records in this period.',
    noEtfSummary: 'No formal ETF analysis records in this period.',
    noMarketReviews: 'No market-review records in this period.',
    records: 'records',
    latest: 'Latest record',
    directionCounts: 'Direction counts',
    bullish: 'Bullish',
    neutral: 'Neutral',
    bearish: 'Bearish',
    unknown: 'Unknown',
    outlookResult: 'Next-week outlook result',
    overallTendency: 'Overall tendency',
    confidence: 'Confidence',
    historicalSignals: 'Main historical signals',
    risks: 'Main risks',
    invalidation: 'Invalidation conditions',
    dataAsOf: 'Data as of',
    stockOutlook: 'Stock outlook',
    etfOutlook: 'ETF outlook',
    marketSignals: 'Market-review signals',
    noStockOutlook: 'No qualifying stock records for an outlook.',
    noEtfOutlook: 'No qualifying ETF records for an outlook.',
    priorReview: 'Prior outlook and actual review',
    priorOutlook: 'Prior outlook',
    actualSummary: 'Actual period summary',
    errorTitle: 'Failed to generate period report',
    retry: 'Generate again',
  },
} as const;

type Copy = (typeof COPY)[UiLanguage];

function formatTimestamp(value?: string | null): string {
  if (!value) {
    return '-';
  }
  return value.replace('T', ' ');
}

function directionVariant(
  direction?: OutlookTendency | string | null,
): 'success' | 'warning' | 'danger' | 'default' {
  if (direction === '看多') {
    return 'success';
  }
  if (direction === '看空') {
    return 'danger';
  }
  if (direction === '中性') {
    return 'warning';
  }
  return 'default';
}

function RecordIds({
  ids,
  copy,
}: {
  ids: number[];
  copy: Copy;
}) {
  return (
    <p className="mt-2 break-words text-xs text-muted-text">
      {copy.sourceIds}：{ids.length > 0 ? ids.map((id) => `#${id}`).join(', ') : '-'}
    </p>
  );
}

function AssetSummaryCard({
  item,
  copy,
}: {
  item: PeriodAssetSummary;
  copy: Copy;
}) {
  const counts = item.directionCounts;
  return (
    <Card padding="sm" className="rounded-xl">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-foreground">{item.stockCode}</p>
          {item.stockName ? <p className="mt-1 text-sm text-secondary-text">{item.stockName}</p> : null}
        </div>
        <Badge variant="history">{item.recordCount} {copy.records}</Badge>
      </div>
      {item.latestSummary ? <p className="mt-3 text-sm text-foreground">{item.latestSummary}</p> : null}
      <div className="mt-3 flex flex-wrap gap-2">
        {item.latestTrend ? (
          <Badge variant={directionVariant(item.latestTrend)}>{item.latestTrend}</Badge>
        ) : null}
        <span className="text-xs text-muted-text">
          {copy.latest}：{formatTimestamp(item.latestCreatedAt)}
        </span>
      </div>
      <p className="mt-3 text-xs text-secondary-text">
        {copy.directionCounts}：{copy.bullish} {counts.bullish} · {copy.neutral} {counts.neutral} · {copy.bearish} {counts.bearish} · {copy.unknown} {counts.unknown}
      </p>
      <RecordIds ids={item.sourceRecordIds} copy={copy} />
    </Card>
  );
}

function AssetSummarySection({
  label,
  items,
  emptyText,
  copy,
}: {
  label: string;
  items: PeriodAssetSummary[];
  emptyText: string;
  copy: Copy;
}) {
  return (
    <section aria-label={label} className="space-y-3">
      <h3 className="text-base font-semibold text-foreground">{label}</h3>
      {items.length > 0 ? (
        <div className="grid gap-3 md:grid-cols-2">
          {items.map((item) => (
            <AssetSummaryCard key={`${item.assetType}-${item.stockCode}`} item={item} copy={copy} />
          ))}
        </div>
      ) : (
        <p className="rounded-xl border border-dashed border-border/60 px-4 py-5 text-sm text-secondary-text">
          {emptyText}
        </p>
      )}
    </section>
  );
}

function MarketReviewSection({
  items,
  copy,
}: {
  items: PeriodMarketReview[];
  copy: Copy;
}) {
  return (
    <section aria-label={copy.marketReviews} className="space-y-3">
      <h3 className="text-base font-semibold text-foreground">{copy.marketReviews}</h3>
      {items.length > 0 ? (
        <div className="grid gap-3 md:grid-cols-2">
          {items.map((item) => (
            <Card key={item.recordId} padding="sm" className="rounded-xl">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Badge variant="info">{item.region || '-'}</Badge>
                <span className="text-xs text-muted-text">{formatTimestamp(item.createdAt)}</span>
              </div>
              {item.summary ? <p className="mt-3 text-sm text-foreground">{item.summary}</p> : null}
              {item.trendPrediction ? <p className="mt-2 text-xs text-secondary-text">{item.trendPrediction}</p> : null}
              <RecordIds ids={[item.recordId]} copy={copy} />
            </Card>
          ))}
        </div>
      ) : (
        <p className="rounded-xl border border-dashed border-border/60 px-4 py-5 text-sm text-secondary-text">
          {copy.noMarketReviews}
        </p>
      )}
    </section>
  );
}

function HistoricalContent({
  report,
  copy,
}: {
  report: PeriodReportResponse;
  copy: Copy;
}) {
  return (
    <div className="space-y-5">
      <AssetSummarySection
        label={copy.stockSummary}
        items={report.stockSummaries}
        emptyText={copy.noStockSummary}
        copy={copy}
      />
      <AssetSummarySection
        label={copy.etfSummary}
        items={report.etfSummaries}
        emptyText={copy.noEtfSummary}
        copy={copy}
      />
      <MarketReviewSection items={report.marketReviews} copy={copy} />
    </div>
  );
}

function OutlookItemCard({
  item,
  copy,
}: {
  item: PeriodOutlookItem;
  copy: Copy;
}) {
  return (
    <Card padding="sm" className="rounded-xl">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-foreground">{item.stockCode}</p>
          {item.stockName ? <p className="mt-1 text-sm text-secondary-text">{item.stockName}</p> : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant={directionVariant(item.tendency)}>{item.tendency}</Badge>
          <Badge variant="info">{copy.confidence}：{item.confidence}</Badge>
        </div>
      </div>
      <dl className="mt-4 space-y-4 text-sm">
        <div>
          <dt className="font-medium text-foreground">{copy.historicalSignals}</dt>
          <dd className="mt-1 space-y-1 text-secondary-text">
            {item.historicalSignals.map((signal) => <p key={signal}>{signal}</p>)}
          </dd>
        </div>
        <div>
          <dt className="font-medium text-foreground">{copy.risks}</dt>
          <dd className="mt-1 space-y-1 text-secondary-text">
            {item.risks.map((risk) => <p key={risk}>{risk}</p>)}
          </dd>
        </div>
        <div>
          <dt className="font-medium text-foreground">{copy.invalidation}</dt>
          <dd className="mt-1 space-y-1 text-secondary-text">
            {item.invalidationConditions.map((condition) => <p key={condition}>{condition}</p>)}
          </dd>
        </div>
      </dl>
      <p className="mt-4 text-xs text-muted-text">
        {copy.dataAsOf}：{formatTimestamp(item.dataAsOf)} · {copy.sourceRecords}：{item.sourceRecordCount}
      </p>
      <RecordIds ids={item.sourceRecordIds} copy={copy} />
    </Card>
  );
}

function OutlookAssetSection({
  label,
  items,
  emptyText,
  copy,
}: {
  label: string;
  items: PeriodOutlookItem[];
  emptyText: string;
  copy: Copy;
}) {
  return (
    <section aria-label={label} className="space-y-3">
      <h4 className="text-base font-semibold text-foreground">{label}</h4>
      {items.length > 0 ? (
        <div className="grid gap-3 lg:grid-cols-2">
          {items.map((item) => (
            <OutlookItemCard key={`${item.assetType}-${item.stockCode}`} item={item} copy={copy} />
          ))}
        </div>
      ) : (
        <p className="rounded-xl border border-dashed border-border/60 px-4 py-5 text-sm text-secondary-text">
          {emptyText}
        </p>
      )}
    </section>
  );
}

function OutlookSnapshotContent({
  snapshot,
  copy,
}: {
  snapshot: PeriodOutlookSnapshot;
  copy: Copy;
}) {
  if (snapshot.status === 'insufficient_data') {
    return (
      <div className="space-y-4">
        <InlineAlert variant="warning" message={snapshot.message || '-'} />
        <InlineAlert variant="info" message={snapshot.disclaimer} />
        {snapshot.snapshotId ? (
          <p className="text-xs text-muted-text">{copy.snapshot}：#{snapshot.snapshotId}</p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="font-medium text-foreground">
          {copy.overallTendency}：{snapshot.overallTendency || '-'}
        </span>
        {snapshot.snapshotId ? <Badge variant="history">{copy.snapshot} #{snapshot.snapshotId}</Badge> : null}
      </div>
      <p className="text-sm text-secondary-text">
        {copy.dataAsOf}：{formatTimestamp(snapshot.dataAsOf)} · {copy.sourceRecords}：{snapshot.sourceRecordCount}
      </p>
      <RecordIds ids={snapshot.sourceRecordIds} copy={copy} />
      <OutlookAssetSection
        label={copy.stockOutlook}
        items={snapshot.stocks}
        emptyText={copy.noStockOutlook}
        copy={copy}
      />
      <OutlookAssetSection
        label={copy.etfOutlook}
        items={snapshot.etfs}
        emptyText={copy.noEtfOutlook}
        copy={copy}
      />
      {snapshot.marketSignals.length > 0 ? (
        <section aria-label={copy.marketSignals} className="space-y-3">
          <h4 className="text-base font-semibold text-foreground">{copy.marketSignals}</h4>
          <div className="grid gap-3 md:grid-cols-2">
            {snapshot.marketSignals.map((item) => (
              <Card key={item.recordId} padding="sm" className="rounded-xl">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Badge variant="info">{item.region || '-'}</Badge>
                  <span className="text-xs text-muted-text">{formatTimestamp(item.createdAt)}</span>
                </div>
                {item.summary ? <p className="mt-3 text-sm text-foreground">{item.summary}</p> : null}
                <RecordIds ids={[item.recordId]} copy={copy} />
              </Card>
            ))}
          </div>
        </section>
      ) : null}
      <InlineAlert variant="info" message={snapshot.disclaimer} />
    </div>
  );
}

const PeriodReportPage = () => {
  const { language } = useUiLanguage();
  const copy = COPY[language];
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodReportKey>('week_to_date');
  const [report, setReport] = useState<PeriodReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ParsedApiError | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      setReport(await periodReportApi.generate(selectedPeriod));
    } catch (requestError) {
      const parsed = getParsedApiError(requestError);
      setError({
        ...parsed,
        title: copy.errorTitle,
      });
    } finally {
      setLoading(false);
    }
  };

  const metadata = report ? (
    <Card padding="sm" className="rounded-xl">
      <div className="grid gap-2 text-sm text-secondary-text md:grid-cols-3">
        <p>{copy.reportRange}：<span className="text-foreground">{report.startDate} 至 {report.endDate}</span></p>
        <p>{copy.generatedAt}：<span className="text-foreground">{formatTimestamp(report.generatedAt)}</span></p>
        <p>{copy.sourceRecords}：<span className="text-foreground">{report.sourceRecordCount}</span></p>
      </div>
    </Card>
  ) : null;

  return (
    <AppPage>
      <div className="space-y-5">
        <PageHeader
          eyebrow={copy.eyebrow}
          title={copy.title}
          description={copy.description}
          actions={(
            <Button
              onClick={() => void generate()}
              isLoading={loading}
              loadingText={copy.generating}
            >
              <Sparkles className="h-4 w-4" />
              {copy.generate}
            </Button>
          )}
        />

        <Card padding="sm" className="rounded-xl">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-7">
            {PERIODS.map((period) => (
              <button
                key={period}
                type="button"
                disabled={loading}
                aria-pressed={selectedPeriod === period}
                onClick={() => setSelectedPeriod(period)}
                className={cn(
                  'rounded-xl border px-3 py-2 text-sm transition-colors',
                  selectedPeriod === period
                    ? 'border-cyan/35 bg-cyan/12 font-medium text-cyan'
                    : 'border-border/65 bg-card/50 text-secondary-text hover:bg-hover hover:text-foreground',
                )}
              >
                {copy.periods[period]}
              </button>
            ))}
          </div>
        </Card>

        {error ? (
          <ApiErrorAlert
            error={error}
            actionLabel={copy.retry}
            onAction={() => void generate()}
          />
        ) : null}

        {metadata}

        {!report ? (
          <EmptyState
            icon={<FileClock className="h-6 w-6" />}
            title={copy.initialTitle}
            description={copy.initialDescription}
          />
        ) : null}

        {report?.reportKind === 'historical' && report.period === 'previous_week' && report.matchedOutlook ? (
          <section aria-label={copy.priorReview} className="space-y-4">
            <div className="flex items-center gap-2">
              <CalendarRange className="h-5 w-5 text-cyan" />
              <h2 className="text-lg font-semibold text-foreground">{copy.priorReview}</h2>
            </div>
            <div className="grid gap-5 xl:grid-cols-2">
              <Card padding="md" className="rounded-xl">
                <h3 className="mb-4 text-base font-semibold text-foreground">{copy.priorOutlook}</h3>
                <OutlookSnapshotContent snapshot={report.matchedOutlook} copy={copy} />
              </Card>
              <Card padding="md" className="rounded-xl">
                <h3 className="mb-4 text-base font-semibold text-foreground">{copy.actualSummary}</h3>
                <HistoricalContent report={report} copy={copy} />
              </Card>
            </div>
          </section>
        ) : null}

        {report?.reportKind === 'historical' && !(report.period === 'previous_week' && report.matchedOutlook) ? (
          <Card padding="md" className="rounded-xl">
            <HistoricalContent report={report} copy={copy} />
          </Card>
        ) : null}

        {report?.reportKind === 'outlook' && report.outlook ? (
          <section aria-label={copy.outlookResult} className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-cyan" />
                <h2 className="text-lg font-semibold text-foreground">{copy.outlookResult}</h2>
              </div>
              <span className="text-sm text-secondary-text">
                {report.outlook.targetPeriod.startDate} 至 {report.outlook.targetPeriod.endDate}
              </span>
            </div>
            <Card padding="md" className="rounded-xl">
              <OutlookSnapshotContent snapshot={report.outlook} copy={copy} />
            </Card>
          </section>
        ) : null}
      </div>
    </AppPage>
  );
};

export default PeriodReportPage;
