export type PeriodReportKey =
  | 'week_to_date'
  | 'previous_week'
  | 'next_week'
  | 'weeks_5'
  | 'weeks_10'
  | 'month_1'
  | 'months_2';

export type OutlookTendency = '看多' | '中性' | '看空';
export type OutlookConfidence = '低' | '中' | '高';

export type PeriodDirectionCounts = {
  bullish: number;
  neutral: number;
  bearish: number;
  unknown: number;
};

export type PeriodAssetSummary = {
  stockCode: string;
  stockName?: string | null;
  assetType: 'stock' | 'etf';
  recordCount: number;
  latestRecordId: number;
  latestCreatedAt?: string | null;
  latestTrend?: string | null;
  latestSummary?: string | null;
  directionCounts: PeriodDirectionCounts;
  sourceRecordIds: number[];
};

export type PeriodMarketReview = {
  recordId: number;
  region?: string | null;
  createdAt?: string | null;
  summary?: string | null;
  trendPrediction?: string | null;
};

export type PeriodOutlookItem = {
  stockCode: string;
  stockName?: string | null;
  assetType: 'stock' | 'etf';
  tendency: OutlookTendency;
  confidence: OutlookConfidence;
  historicalSignals: string[];
  risks: string[];
  invalidationConditions: string[];
  dataAsOf?: string | null;
  sourceRecordCount: number;
  sourceRecordIds: number[];
};

export type PeriodOutlookMarketSignal = {
  recordId: number;
  region?: string | null;
  createdAt?: string | null;
  summary?: string | null;
};

export type PeriodOutlookSnapshot = {
  snapshotVersion: number;
  snapshotId?: number | null;
  snapshotCreatedAt?: string | null;
  status: 'ready' | 'insufficient_data';
  message?: string | null;
  targetPeriod: {
    startDate: string;
    endDate: string;
  };
  generatedAt: string;
  overallTendency?: OutlookTendency | null;
  stocks: PeriodOutlookItem[];
  etfs: PeriodOutlookItem[];
  marketSignals: PeriodOutlookMarketSignal[];
  dataAsOf?: string | null;
  sourceRecordCount: number;
  sourceRecordIds: number[];
  disclaimer: string;
};

export type PeriodReportResponse = {
  reportId: number;
  status: 'ready' | 'insufficient_data';
  period: PeriodReportKey;
  reportKind: 'historical' | 'outlook';
  startDate: string;
  endDate: string;
  generatedAt: string;
  sourceRecordCount: number;
  stockSummaries: PeriodAssetSummary[];
  etfSummaries: PeriodAssetSummary[];
  marketReviews: PeriodMarketReview[];
  outlook?: PeriodOutlookSnapshot | null;
  matchedOutlook?: PeriodOutlookSnapshot | null;
  disclaimer?: string | null;
};
