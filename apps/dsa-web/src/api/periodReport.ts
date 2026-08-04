import type { PeriodReportKey, PeriodReportResponse } from '../types/periodReport';
import apiClient from './index';
import { toCamelCase } from './utils';

export const periodReportApi = {
  getLatest: async (period: PeriodReportKey): Promise<PeriodReportResponse> => {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/period-report/latest',
      { params: { period } },
    );
    return toCamelCase<PeriodReportResponse>(response.data);
  },

  getById: async (reportId: number): Promise<PeriodReportResponse> => {
    const response = await apiClient.get<Record<string, unknown>>(
      `/api/v1/period-report/${reportId}`,
    );
    return toCamelCase<PeriodReportResponse>(response.data);
  },

  generate: async (period: PeriodReportKey): Promise<PeriodReportResponse> => {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/period-report/generate',
      { period },
    );
    return toCamelCase<PeriodReportResponse>(response.data);
  },
};
