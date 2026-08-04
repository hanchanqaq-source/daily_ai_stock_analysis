import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { periodReportApi } from '../../api/periodReport';
import { UiLanguageProvider } from '../../contexts/UiLanguageContext';
import type { PeriodReportResponse } from '../../types/periodReport';
import PeriodReportPage from '../PeriodReportPage';

vi.mock('../../api/periodReport', () => ({
  periodReportApi: {
    generate: vi.fn(),
    getLatest: vi.fn(),
    getById: vi.fn(),
  },
}));

const historicalReport: PeriodReportResponse = {
  reportId: 401,
  status: 'ready',
  period: 'week_to_date',
  reportKind: 'historical',
  startDate: '2026-07-27',
  endDate: '2026-07-30',
  generatedAt: '2026-07-30T12:00:00+02:00',
  sourceRecordCount: 3,
  stockSummaries: [
    {
      stockCode: '600519',
      stockName: '贵州茅台',
      assetType: 'stock',
      recordCount: 1,
      latestRecordId: 11,
      latestCreatedAt: '2026-07-30T09:00:00+02:00',
      latestTrend: '看多',
      latestSummary: '股票历史摘要',
      directionCounts: { bullish: 1, neutral: 0, bearish: 0, unknown: 0 },
      sourceRecordIds: [11],
    },
  ],
  etfSummaries: [
    {
      stockCode: '512880',
      stockName: '证券ETF',
      assetType: 'etf',
      recordCount: 1,
      latestRecordId: 12,
      latestCreatedAt: '2026-07-30T08:00:00+02:00',
      latestTrend: '中性',
      latestSummary: 'ETF 历史摘要',
      directionCounts: { bullish: 0, neutral: 1, bearish: 0, unknown: 0 },
      sourceRecordIds: [12],
    },
  ],
  marketReviews: [
    {
      recordId: 13,
      region: 'cn',
      createdAt: '2026-07-30T07:00:00+02:00',
      summary: '市场复盘摘要',
      trendPrediction: '指数震荡',
    },
  ],
  outlook: null,
  matchedOutlook: null,
  disclaimer: null,
};

const readyOutlook = {
  snapshotVersion: 1,
  snapshotId: 77,
  snapshotCreatedAt: '2026-07-30T12:00:00+02:00',
  status: 'ready' as const,
  message: null,
  targetPeriod: {
    startDate: '2026-08-03',
    endDate: '2026-08-09',
  },
  generatedAt: '2026-07-30T12:00:00+02:00',
  overallTendency: '看多' as const,
  stocks: [
    {
      stockCode: '600519',
      stockName: '贵州茅台',
      assetType: 'stock' as const,
      tendency: '看多' as const,
      confidence: '高' as const,
      historicalSignals: ['趋势：看多', '策略信号：持有'],
      risks: ['市场波动风险'],
      invalidationConditions: ['价格有效跌破历史支撑参考 1500。'],
      dataAsOf: '2026-07-30T09:00:00+02:00',
      sourceRecordCount: 2,
      sourceRecordIds: [11, 14],
    },
  ],
  etfs: [
    {
      stockCode: '512880',
      stockName: '证券ETF',
      assetType: 'etf' as const,
      tendency: '中性' as const,
      confidence: '中' as const,
      historicalSignals: ['趋势：震荡'],
      risks: ['流动性风险'],
      invalidationConditions: ['趋势脱离中性区间。'],
      dataAsOf: '2026-07-30T08:00:00+02:00',
      sourceRecordCount: 1,
      sourceRecordIds: [12],
    },
  ],
  marketSignals: [
    {
      recordId: 13,
      region: 'cn',
      createdAt: '2026-07-30T07:00:00+02:00',
      summary: '市场复盘摘要',
    },
  ],
  dataAsOf: '2026-07-30T09:00:00+02:00',
  sourceRecordCount: 4,
  sourceRecordIds: [11, 12, 13, 14],
  disclaimer: '下周展望基于已有历史分析形成，仅供参考，不代表确定结果。',
};

const outlookReport: PeriodReportResponse = {
  reportId: 407,
  status: 'ready',
  period: 'next_week',
  reportKind: 'outlook',
  startDate: '2026-08-03',
  endDate: '2026-08-09',
  generatedAt: '2026-07-30T12:00:00+02:00',
  sourceRecordCount: 4,
  stockSummaries: [],
  etfSummaries: [],
  marketReviews: [],
  outlook: readyOutlook,
  matchedOutlook: null,
  disclaimer: readyOutlook.disclaimer,
};

function renderPage() {
  return render(
    <UiLanguageProvider>
      <PeriodReportPage />
    </UiLanguageProvider>,
  );
}

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((promiseResolve) => {
    resolve = promiseResolve;
  });
  return { promise, resolve };
}

beforeEach(() => {
  window.localStorage.clear();
  window.localStorage.setItem('dsa.uiLanguage', 'zh');
  vi.clearAllMocks();
  vi.mocked(periodReportApi.generate).mockResolvedValue(historicalReport);
  vi.mocked(periodReportApi.getLatest).mockResolvedValue(historicalReport);
});

describe('PeriodReportPage', () => {
  it('loads the latest stored report on mount without generating anything', async () => {
    renderPage();

    for (const label of [
      '本周至今',
      '上一周',
      '下周展望',
      '5周',
      '10周',
      '1个月',
      '2个月',
    ]) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    }
    await waitFor(() => {
      expect(periodReportApi.getLatest).toHaveBeenCalledWith('week_to_date');
    });
    expect(periodReportApi.generate).not.toHaveBeenCalled();
    expect(await screen.findByText('报告 #401')).toBeInTheDocument();
    expect(screen.getByText('股票历史摘要')).toBeInTheDocument();
  });

  it('loads that period latest stored report when the selection changes', async () => {
    vi.mocked(periodReportApi.getLatest).mockImplementation(async (period) => ({
      ...historicalReport,
      reportId: period === 'weeks_5' ? 405 : 401,
      period,
    }));
    renderPage();

    await screen.findByText('报告 #401');
    fireEvent.click(screen.getByRole('button', { name: '5周' }));

    await waitFor(() => {
      expect(periodReportApi.getLatest).toHaveBeenLastCalledWith('weeks_5');
    });
    expect(await screen.findByText('报告 #405')).toBeInTheDocument();
    expect(periodReportApi.generate).not.toHaveBeenCalled();
  });

  it('does not let a slow stored-report read overwrite an explicit generation result', async () => {
    const latest = createDeferred<PeriodReportResponse>();
    vi.mocked(periodReportApi.getLatest).mockReturnValue(latest.promise);
    vi.mocked(periodReportApi.generate).mockResolvedValue({
      ...historicalReport,
      reportId: 499,
      stockSummaries: [{
        ...historicalReport.stockSummaries[0],
        latestSummary: '用户刚刚生成的报告',
      }],
    });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: '生成报告' }));
    expect(await screen.findByText('报告 #499')).toBeInTheDocument();
    await act(async () => {
      latest.resolve(historicalReport);
      await latest.promise;
    });

    expect(screen.getByText('报告 #499')).toBeInTheDocument();
    expect(screen.getByText('用户刚刚生成的报告')).toBeInTheDocument();
  });

  it('calls the single manual endpoint only after the user chooses a period and generates', async () => {
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: '5周' }));
    expect(periodReportApi.generate).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: '生成报告' }));

    await waitFor(() => {
      expect(periodReportApi.generate).toHaveBeenCalledTimes(1);
      expect(periodReportApi.generate).toHaveBeenCalledWith('weeks_5');
    });
  });

  it('renders stock, ETF, and market-review history as separate sections', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '生成报告' }));

    const stockSection = await screen.findByRole('region', { name: '股票分析汇总' });
    const etfSection = screen.getByRole('region', { name: 'ETF 分析汇总' });
    const marketSection = screen.getByRole('region', { name: '市场复盘' });

    expect(within(stockSection).getByText('600519')).toBeInTheDocument();
    expect(within(stockSection).getByText('股票历史摘要')).toBeInTheDocument();
    expect(within(stockSection).queryByText('512880')).not.toBeInTheDocument();
    expect(within(etfSection).getByText('512880')).toBeInTheDocument();
    expect(within(etfSection).queryByText('市场复盘摘要')).not.toBeInTheDocument();
    expect(within(marketSection).getByText('市场复盘摘要')).toBeInTheDocument();
    expect(screen.getByText('2026-07-27 至 2026-07-30')).toBeInTheDocument();
  });

  it('renders every required outlook field and keeps stock and ETF items separate', async () => {
    vi.mocked(periodReportApi.generate).mockResolvedValue(outlookReport);
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: '下周展望' }));
    fireEvent.click(screen.getByRole('button', { name: '生成报告' }));

    const outlook = await screen.findByRole('region', { name: '下周展望结果' });
    expect(within(outlook).getByText('2026-08-03 至 2026-08-09')).toBeInTheDocument();
    expect(within(outlook).getByText(/总体倾向/)).toHaveTextContent('看多');
    expect(within(outlook).getAllByText('主要历史信号')).toHaveLength(2);
    expect(within(outlook).getByText('趋势：看多')).toBeInTheDocument();
    expect(within(outlook).getAllByText('主要风险')).toHaveLength(2);
    expect(within(outlook).getByText('市场波动风险')).toBeInTheDocument();
    expect(within(outlook).getAllByText('判断失效条件')).toHaveLength(2);
    expect(within(outlook).getByText('价格有效跌破历史支撑参考 1500。')).toBeInTheDocument();
    const snapshotMetadata = within(outlook).getByText(/来源记录：4$/);
    expect(snapshotMetadata).toHaveTextContent('数据截至：2026-07-30');
    expect(within(outlook).getByText('置信度：高')).toBeInTheDocument();
    expect(within(outlook).getByText('置信度：中')).toBeInTheDocument();
    expect(within(outlook).getByText(readyOutlook.disclaimer)).toBeInTheDocument();
    expect(within(outlook).queryByText(/目标价/)).not.toBeInTheDocument();

    const stockSection = within(outlook).getByRole('region', { name: '股票展望' });
    const etfSection = within(outlook).getByRole('region', { name: 'ETF 展望' });
    expect(within(stockSection).getByText('600519')).toBeInTheDocument();
    expect(within(stockSection).queryByText('512880')).not.toBeInTheDocument();
    expect(within(etfSection).getByText('512880')).toBeInTheDocument();
  });

  it('shows the fixed insufficient-data message instead of inventing a direction', async () => {
    vi.mocked(periodReportApi.generate).mockResolvedValue({
      ...outlookReport,
      sourceRecordCount: 0,
      outlook: {
        ...readyOutlook,
        status: 'insufficient_data',
        message: '近期有效数据不足，暂不能形成下周展望。',
        overallTendency: null,
        stocks: [],
        etfs: [],
        marketSignals: [],
        dataAsOf: null,
        sourceRecordCount: 0,
        sourceRecordIds: [],
      },
    });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: '下周展望' }));
    fireEvent.click(screen.getByRole('button', { name: '生成报告' }));

    expect(
      await screen.findByText('近期有效数据不足，暂不能形成下周展望。'),
    ).toBeInTheDocument();
    expect(screen.queryByText(/总体倾向/)).not.toBeInTheDocument();
    expect(screen.queryByText(/看多/)).not.toBeInTheDocument();
  });

  it('places the prior snapshot beside the actual previous-week summary for review', async () => {
    vi.mocked(periodReportApi.generate).mockResolvedValue({
      ...historicalReport,
      period: 'previous_week',
      startDate: '2026-07-20',
      endDate: '2026-07-26',
      matchedOutlook: {
        ...readyOutlook,
        snapshotId: 55,
        targetPeriod: {
          startDate: '2026-07-20',
          endDate: '2026-07-26',
        },
      },
    });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: '上一周' }));
    fireEvent.click(screen.getByRole('button', { name: '生成报告' }));

    const review = await screen.findByRole('region', { name: '上周展望与实际复盘' });
    expect(within(review).getByRole('heading', { name: '上周展望' })).toBeInTheDocument();
    expect(within(review).getByRole('heading', { name: '实际周期汇总' })).toBeInTheDocument();
    expect(within(review).getByText('股票历史摘要')).toBeInTheDocument();
    expect(within(review).getByText('趋势：看多')).toBeInTheDocument();
    expect(within(review).queryByText(/胜率/)).not.toBeInTheDocument();
  });
});
