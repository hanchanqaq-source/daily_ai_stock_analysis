import {
  AxiosError,
  AxiosHeaders,
  type AxiosAdapter,
  type AxiosResponse,
} from 'axios';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import apiClient from '../index';
import { getParsedApiError, isApiRequestError } from '../error';
import { fullDataBackupApi } from '../fullDataBackup';

const originalAdapter = apiClient.defaults.adapter;
let trailingObserverId: number | null = null;
let trailingObservations: Array<{
  error: unknown;
  isApiRequestError: boolean;
  name?: string;
  parsedError?: ReturnType<typeof getParsedApiError>;
}> = [];

function installResponseAdapter({
  data,
  status,
  statusText,
  headers = {},
}: {
  data: string;
  status: number;
  statusText: string;
  headers?: Record<string, string>;
}) {
  const adapter: AxiosAdapter = async (config) => {
    const response: AxiosResponse<string> = {
      data,
      status,
      statusText,
      headers: new AxiosHeaders(headers),
      config,
      request: { testAdapter: true },
    };
    if (status >= 200 && status < 300) {
      return response;
    }
    throw new AxiosError(
      `Request failed with status code ${status}`,
      status >= 500 ? AxiosError.ERR_BAD_RESPONSE : AxiosError.ERR_BAD_REQUEST,
      config,
      response.request,
      response,
    );
  };
  apiClient.defaults.adapter = adapter;
}

describe('fullDataBackupApi with the project Axios pipeline', () => {
  beforeEach(() => {
    expect(trailingObserverId).toBeNull();
    expect(apiClient.defaults.adapter).toBe(originalAdapter);
    apiClient.defaults.adapter = originalAdapter;
    trailingObservations = [];
    trailingObserverId = apiClient.interceptors.response.use(
      (response) => response,
      (error: unknown) => {
        const parsedBySharedInterceptor = isApiRequestError(error);
        trailingObservations.push({
          error,
          isApiRequestError: parsedBySharedInterceptor,
          name: error instanceof Error ? error.name : undefined,
          parsedError: parsedBySharedInterceptor ? error.parsedError : undefined,
        });
        return Promise.reject(error);
      },
    );
  });

  afterEach(async () => {
    const observerId = trailingObserverId;
    trailingObserverId = null;
    if (observerId !== null) {
      apiClient.interceptors.response.eject(observerId);
    }
    const observedBeforeCleanupProbe = trailingObservations.length;
    try {
      installResponseAdapter({
        data: '{"detail":"cleanup probe"}',
        status: 418,
        statusText: "I'm a teapot",
      });
      await apiClient.get('/test-only/interceptor-cleanup-probe').catch(() => undefined);
      expect(trailingObservations).toHaveLength(observedBeforeCleanupProbe);
    } finally {
      apiClient.defaults.adapter = originalAdapter;
    }
    expect(apiClient.defaults.adapter).toBe(originalAdapter);
  });

  it('preserves successful canonical export text including its trailing newline', async () => {
    const canonicalText = '{"format":"pp02.full-data.backup","format_version":1}\n';
    installResponseAdapter({
      data: canonicalText,
      status: 200,
      statusText: 'OK',
      headers: {
        'content-disposition': 'attachment; filename="canonical-backup.json"',
      },
    });

    const result = await fullDataBackupApi.exportBackup();

    expect(result).toEqual({
      fileName: 'canonical-backup.json',
      content: canonicalText,
    });
    expect(result.content.endsWith('\n')).toBe(true);
  });

  it('decodes rejected JSON through Axios before shared error classification', async () => {
    const serializedEnvelope = JSON.stringify({
      detail: {
        error: 'full_data_backup_unavailable',
        message: 'Complete backup export is temporarily unavailable.',
      },
    });
    installResponseAdapter({
      data: serializedEnvelope,
      status: 409,
      statusText: 'Conflict',
    });

    const rejected = await fullDataBackupApi.exportBackup().catch((error: unknown) => error);
    const parsed = getParsedApiError(rejected);

    expect(trailingObservations).toHaveLength(1);
    expect(trailingObservations[0]).toMatchObject({
      error: rejected,
      isApiRequestError: true,
      name: 'ApiRequestError',
      parsedError: {
        message: 'Complete backup export is temporarily unavailable.',
        status: 409,
        category: 'http_error',
      },
    });
    expect(isApiRequestError(rejected)).toBe(true);
    expect((rejected as AxiosError).response?.data).toEqual({
      detail: {
        error: 'full_data_backup_unavailable',
        message: 'Complete backup export is temporarily unavailable.',
      },
    });
    expect(parsed).toMatchObject({
      title: '请求失败',
      message: 'Complete backup export is temporarily unavailable.',
      rawMessage: 'Complete backup export is temporarily unavailable.',
      status: 409,
      category: 'http_error',
    });
    expect(parsed.message).not.toContain(serializedEnvelope);
    expect(parsed.message).not.toContain('"detail"');
  });

  it.each([
    ['malformed text', 'failure at /srv/private/runtime/backup.json marker=private-payload'],
    ['non-object JSON', '"failure at /srv/private/runtime/backup.json marker=private-payload"'],
  ])('discards rejected %s before shared error classification', async (_label, responseText) => {
    installResponseAdapter({
      data: responseText,
      status: 500,
      statusText: 'Internal Server Error',
    });

    const rejected = await fullDataBackupApi.exportBackup().catch((error: unknown) => error);
    const parsed = getParsedApiError(rejected);

    expect(trailingObservations).toHaveLength(1);
    expect(trailingObservations[0]).toMatchObject({
      error: rejected,
      isApiRequestError: true,
      name: 'ApiRequestError',
      parsedError: {
        message: '请求未成功完成（HTTP 500）。',
        status: 500,
        category: 'http_error',
      },
    });
    expect(isApiRequestError(rejected)).toBe(true);
    expect((rejected as AxiosError).response?.data).toBeUndefined();
    expect(parsed.message).toBe('请求未成功完成（HTTP 500）。');
    expect(parsed.rawMessage).not.toContain('/srv/private');
    expect(parsed.rawMessage).not.toContain('private-payload');
  });
});
