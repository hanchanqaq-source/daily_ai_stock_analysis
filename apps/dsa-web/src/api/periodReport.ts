import type { PeriodReportKey, PeriodReportResponse } from '../types/periodReport';
import apiClient from './index';
import { toCamelCase } from './utils';

export const periodReportApi = {
  generate: async (period: PeriodReportKey): Promise<PeriodReportResponse> => {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/period-report/generate',
      { period },
    );
    return toCamelCase<PeriodReportResponse>(response.data);
  },
};
