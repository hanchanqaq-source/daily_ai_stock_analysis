import apiClient from './index';
import { createParsedApiError, getParsedApiError, type ParsedApiError } from './error';
import { toCamelCase } from './utils';
import type {
  AgentBackendStatusPreviewRequest,
  AgentBackendStatusResponse,
  DiscoverLLMChannelModelsRequest,
  DiscoverLLMChannelModelsResponse,
  ExportSystemConfigResponse,
  GenerationBackendStatusPreviewRequest,
  GenerationBackendStatusResponse,
  ImportSystemConfigRequest,
  SchedulerRunNowResponse,
  SchedulerStatusResponse,
  SetupStatusResponse,
  SystemConfigConflictResponse,
  SystemConfigResponse,
  SystemConfigSchemaResponse,
  SystemConfigValidationErrorResponse,
  TestLLMChannelRequest,
  TestLLMChannelResponse,
  TestGenerationBackendRequest,
  TestGenerationBackendResponse,
  TestNotificationChannelRequest,
  TestNotificationChannelResponse,
  UpdateSystemConfigRequest,
  UpdateSystemConfigResponse,
  ValidateSystemConfigRequest,
  ValidateSystemConfigResponse,
} from '../types/systemConfig';

export class SystemConfigValidationError extends Error {
  issues: SystemConfigValidationErrorResponse['issues'];
  parsedError: ParsedApiError;

  constructor(message: string, issues: SystemConfigValidationErrorResponse['issues'], parsedError?: ParsedApiError) {
    super(message);
    this.name = 'SystemConfigValidationError';
    this.issues = issues;
    this.parsedError = parsedError ?? createParsedApiError({
      title: '配置校验失败',
      message,
      rawMessage: message,
      status: 400,
      category: 'http_error',
    });
  }
}

export class SystemConfigConflictError extends Error {
  currentConfigVersion?: string;
  parsedError: ParsedApiError;

  constructor(message: string, currentConfigVersion?: string, parsedError?: ParsedApiError) {
    super(message);
    this.name = 'SystemConfigConflictError';
    this.currentConfigVersion = currentConfigVersion;
    this.parsedError = parsedError ?? createParsedApiError({
      title: '配置版本冲突',
      message,
      rawMessage: message,
      status: 409,
      category: 'http_error',
    });
  }
}

interface DesktopSecureCredentialPrepareResult {
  supported: boolean;
  transactionId?: string | null;
  handledKeys: string[];
  changedKeys: string[];
  skippedMaskedKeys: string[];
}

interface DesktopSecureCredentialBridge {
  prepareSecureCredentialUpdate(payload: {
    items: UpdateSystemConfigRequest['items'];
    maskToken: string;
  }): Promise<DesktopSecureCredentialPrepareResult>;
  commitSecureCredentialUpdate(payload: {
    transactionId: string;
    configVersion: string;
  }): Promise<unknown>;
  rollbackSecureCredentialUpdate(transactionId: string): Promise<unknown>;
  finalizeSecureCredentialUpdate(transactionId: string): Promise<unknown>;
}

type SystemConfigValidationErrorEnvelope = Partial<SystemConfigValidationErrorResponse> & {
  detail?: Partial<SystemConfigValidationErrorResponse>;
};

const PENDING_LLM_CREDENTIAL_KEYS = new Set([
  'AIHUBMIX_KEY',
  'ANSPIRE_API_KEYS',
  'ANTHROPIC_API_KEY',
  'ANTHROPIC_API_KEYS',
  'DEEPSEEK_API_KEY',
  'DEEPSEEK_API_KEYS',
  'GEMINI_API_KEY',
  'GEMINI_API_KEYS',
  'OPENAI_API_KEY',
  'OPENAI_API_KEYS',
]);
const PENDING_LLM_CHANNEL_CREDENTIAL_RE = /^LLM_[A-Z0-9_]+_API_KEYS?$/;
const DISPLAYED_VALIDATION_ISSUE_LIMIT = 3;
const DISPLAYED_VALIDATION_MESSAGE_MAX_LENGTH = 600;

function isPendingLLMCredentialKey(key: string): boolean {
  const normalizedKey = key.toUpperCase();
  return PENDING_LLM_CREDENTIAL_KEYS.has(normalizedKey)
    || PENDING_LLM_CHANNEL_CREDENTIAL_RE.test(normalizedKey);
}

function truncateValidationMessage(message: string, maxLength: number): string {
  return message.length <= maxLength ? message : `${message.slice(0, Math.max(0, maxLength - 1))}…`;
}

function parseSystemConfigValidationError(data: unknown): SystemConfigValidationErrorResponse {
  const envelope = toCamelCase<SystemConfigValidationErrorEnvelope>(data ?? {});
  const payload = envelope.detail ?? envelope;
  return {
    error: payload.error || 'validation_failed',
    message: payload.message || 'System configuration validation failed',
    issues: Array.isArray(payload.issues) ? payload.issues : [],
  };
}

function createSystemConfigValidationError(
  validation: Pick<SystemConfigValidationErrorResponse, 'message' | 'issues'>,
  parsedError?: ParsedApiError,
): SystemConfigValidationError {
  const displayedIssues = validation.issues
    .slice(0, DISPLAYED_VALIDATION_ISSUE_LIMIT)
    .map((issue) => `${issue.key}：${issue.message}`)
    .join('；');
  const remainingIssueCount = validation.issues.length - DISPLAYED_VALIDATION_ISSUE_LIMIT;
  const issueSuffix = remainingIssueCount > 0 ? `另有 ${remainingIssueCount} 项校验错误` : '';
  const separator = displayedIssues && issueSuffix ? '；' : '';
  const availableIssueLength = DISPLAYED_VALIDATION_MESSAGE_MAX_LENGTH - separator.length - issueSuffix.length;
  const issueMessage = [
    truncateValidationMessage(displayedIssues, availableIssueLength),
    issueSuffix,
  ].filter(Boolean).join(separator);
  const message = issueMessage || parsedError?.message || validation.message || '配置校验失败';
  const detailedError = createParsedApiError({
    title: '配置校验失败',
    message,
    rawMessage: parsedError?.rawMessage || validation.message || message,
    status: parsedError?.status ?? 400,
    category: parsedError?.category ?? 'http_error',
  });
  return new SystemConfigValidationError(message, validation.issues, detailedError);
}

function getDesktopSecureCredentialBridge(): DesktopSecureCredentialBridge | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const candidate = (window as typeof window & { dsaDesktop?: Partial<DesktopSecureCredentialBridge> })
    .dsaDesktop;
  if (
    !candidate
    || typeof candidate.prepareSecureCredentialUpdate !== 'function'
    || typeof candidate.commitSecureCredentialUpdate !== 'function'
    || typeof candidate.rollbackSecureCredentialUpdate !== 'function'
    || typeof candidate.finalizeSecureCredentialUpdate !== 'function'
  ) {
    return null;
  }
  return candidate as DesktopSecureCredentialBridge;
}

function toSnakeUpdatePayload(payload: UpdateSystemConfigRequest): Record<string, unknown> {
  return {
    config_version: payload.configVersion,
    mask_token: payload.maskToken ?? '******',
    reload_now: payload.reloadNow ?? true,
    items: payload.items.map((item) => ({
      key: item.key,
      value: item.value,
    })),
  };
}

function toSnakeValidatePayload(payload: ValidateSystemConfigRequest): Record<string, unknown> {
  return {
    items: payload.items.map((item) => ({
      key: item.key,
      value: item.value,
    })),
  };
}

function toSnakeImportPayload(payload: ImportSystemConfigRequest): Record<string, unknown> {
  return {
    config_version: payload.configVersion,
    content: payload.content,
    reload_now: payload.reloadNow ?? true,
  };
}

function toSnakeTestChannelPayload(payload: TestLLMChannelRequest): Record<string, unknown> {
  const request: Record<string, unknown> = {
    name: payload.name,
    protocol: payload.protocol,
    base_url: payload.baseUrl ?? '',
    api_key: payload.apiKey ?? '',
    models: payload.models,
    enabled: payload.enabled ?? true,
    timeout_seconds: payload.timeoutSeconds ?? 20,
    use_saved_secret: payload.useSavedSecret ?? false,
  };
  if (payload.capabilityChecks && payload.capabilityChecks.length > 0) {
    request.capability_checks = payload.capabilityChecks;
  }
  return request;
}

function toSnakeNotificationTestPayload(payload: TestNotificationChannelRequest): Record<string, unknown> {
  return {
    channel: payload.channel,
    items: (payload.items || []).map((item) => ({
      key: item.key,
      value: item.value,
    })),
    mask_token: payload.maskToken ?? '******',
    title: payload.title ?? 'DSA 通知测试',
    content: payload.content ?? '这是一条来自 DSA Web 设置页的通知测试消息。',
    timeout_seconds: payload.timeoutSeconds ?? 20,
  };
}

function toSnakeDiscoverModelsPayload(payload: DiscoverLLMChannelModelsRequest): Record<string, unknown> {
  return {
    name: payload.name,
    protocol: payload.protocol,
    base_url: payload.baseUrl ?? '',
    api_key: payload.apiKey ?? '',
    models: payload.models,
    timeout_seconds: payload.timeoutSeconds ?? 20,
    use_saved_secret: payload.useSavedSecret ?? false,
  };
}

function toSnakeGenerationBackendStatusPreviewPayload(
  payload: GenerationBackendStatusPreviewRequest = {},
): Record<string, unknown> {
  return {
    items: (payload.items || []).map((item) => ({
      key: item.key,
      value: item.value,
    })),
    mask_token: payload.maskToken ?? '******',
  };
}

function toSnakeGenerationBackendSmokePayload(payload: TestGenerationBackendRequest = {}): Record<string, unknown> {
  const request: Record<string, unknown> = {
    mode: payload.mode ?? 'json',
    items: (payload.items || []).map((item) => ({
      key: item.key,
      value: item.value,
    })),
    mask_token: payload.maskToken ?? '******',
  };
  if (payload.backendId) {
    request.backend_id = payload.backendId;
  }
  if (payload.timeoutSeconds !== undefined && payload.timeoutSeconds !== null) {
    request.timeout_seconds = payload.timeoutSeconds;
  }
  return request;
}

function toSnakeAgentBackendPayload(
  payload: AgentBackendStatusPreviewRequest = {},
): Record<string, unknown> {
  return {
    items: (payload.items || []).map((item) => ({ key: item.key, value: item.value })),
    mask_token: payload.maskToken ?? '******',
  };
}

export const systemConfigApi = {
  async getConfig(includeSchema = true): Promise<SystemConfigResponse> {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/system/config', {
      params: { include_schema: includeSchema },
    });
    return toCamelCase<SystemConfigResponse>(response.data);
  },

  async exportEnv(): Promise<ExportSystemConfigResponse> {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/system/config/export');
    return toCamelCase<ExportSystemConfigResponse>(response.data);
  },

  async exportDesktopEnv(): Promise<ExportSystemConfigResponse> {
    return this.exportEnv();
  },

  async getSchema(): Promise<SystemConfigSchemaResponse> {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/system/config/schema');
    return toCamelCase<SystemConfigSchemaResponse>(response.data);
  },

  async getSetupStatus(): Promise<SetupStatusResponse> {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/system/config/setup/status');
    return toCamelCase<SetupStatusResponse>(response.data);
  },

  async getGenerationBackendStatus(): Promise<GenerationBackendStatusResponse> {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/system/config/generation-backends/status',
    );
    return toCamelCase<GenerationBackendStatusResponse>(response.data);
  },

  async previewGenerationBackendStatus(
    payload: GenerationBackendStatusPreviewRequest = {},
  ): Promise<GenerationBackendStatusResponse> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/system/config/generation-backends/status/preview',
      toSnakeGenerationBackendStatusPreviewPayload(payload),
    );
    return toCamelCase<GenerationBackendStatusResponse>(response.data);
  },

  async testGenerationBackend(payload: TestGenerationBackendRequest = {}): Promise<TestGenerationBackendResponse> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/system/config/generation-backends/smoke-test',
      toSnakeGenerationBackendSmokePayload(payload),
    );
    return toCamelCase<TestGenerationBackendResponse>(response.data);
  },

  async getAgentBackendStatus(): Promise<AgentBackendStatusResponse> {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/system/config/agent-backends/status',
    );
    return toCamelCase<AgentBackendStatusResponse>(response.data);
  },

  async previewAgentBackendStatus(
    payload: AgentBackendStatusPreviewRequest = {},
  ): Promise<AgentBackendStatusResponse> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/system/config/agent-backends/status/preview',
      toSnakeAgentBackendPayload(payload),
    );
    return toCamelCase<AgentBackendStatusResponse>(response.data);
  },

  async getSchedulerStatus(): Promise<SchedulerStatusResponse> {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/system/scheduler/status');
    return toCamelCase<SchedulerStatusResponse>(response.data);
  },

  async runSchedulerNow(): Promise<SchedulerRunNowResponse> {
    const response = await apiClient.post<Record<string, unknown>>('/api/v1/system/scheduler/run-now');
    return toCamelCase<SchedulerRunNowResponse>(response.data);
  },

  async validate(payload: ValidateSystemConfigRequest): Promise<ValidateSystemConfigResponse> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/system/config/validate',
      toSnakeValidatePayload(payload),
    );
    return toCamelCase<ValidateSystemConfigResponse>(response.data);
  },

  async importEnv(payload: ImportSystemConfigRequest): Promise<UpdateSystemConfigResponse> {
    const desktopBridge = getDesktopSecureCredentialBridge();
    if (desktopBridge) {
      const prepared = await desktopBridge.prepareSecureCredentialUpdate({
        items: [],
        maskToken: '******',
      });
      if (prepared.supported && prepared.transactionId) {
        const transactionId = prepared.transactionId;
        let vaultCommitted = false;
        try {
          const response = await apiClient.post<Record<string, unknown>>(
            '/api/v1/system/config/import',
            toSnakeImportPayload({ ...payload, reloadNow: false }),
          );
          const result = toCamelCase<UpdateSystemConfigResponse>(response.data);
          await desktopBridge.commitSecureCredentialUpdate({
            transactionId,
            configVersion: result.configVersion,
          });
          vaultCommitted = true;
          await desktopBridge.finalizeSecureCredentialUpdate(transactionId);
          return { ...result, reloadTriggered: true };
        } catch (error) {
          if (!vaultCommitted) {
            try {
              await desktopBridge.rollbackSecureCredentialUpdate(transactionId);
            } catch {
              // Preserve the original failure; secure-storage errors are already generic.
            }
          }
          throw error;
        }
      }
    }
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/system/config/import',
      toSnakeImportPayload(payload),
    );
    return toCamelCase<UpdateSystemConfigResponse>(response.data);
  },

  async importDesktopEnv(payload: ImportSystemConfigRequest): Promise<UpdateSystemConfigResponse> {
    return this.importEnv(payload);
  },

  async testLLMChannel(payload: TestLLMChannelRequest): Promise<TestLLMChannelResponse> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/system/config/llm/test-channel',
      toSnakeTestChannelPayload(payload),
    );
    return toCamelCase<TestLLMChannelResponse>(response.data);
  },

  async testNotificationChannel(payload: TestNotificationChannelRequest): Promise<TestNotificationChannelResponse> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/system/config/notification/test-channel',
      toSnakeNotificationTestPayload(payload),
    );
    return toCamelCase<TestNotificationChannelResponse>(response.data);
  },

  async discoverLLMChannelModels(
    payload: DiscoverLLMChannelModelsRequest,
  ): Promise<DiscoverLLMChannelModelsResponse> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/system/config/llm/discover-models',
      toSnakeDiscoverModelsPayload(payload),
    );
    return toCamelCase<DiscoverLLMChannelModelsResponse>(response.data);
  },

  async update(payload: UpdateSystemConfigRequest): Promise<UpdateSystemConfigResponse> {
    try {
      const desktopBridge = getDesktopSecureCredentialBridge();
      if (desktopBridge) {
        const maskToken = payload.maskToken ?? '******';
        const validation = await this.validate({ items: payload.items });
        if (!validation.valid) {
          throw createSystemConfigValidationError({
            message: '配置校验失败',
            issues: validation.issues,
          });
        }

        const prepared = await desktopBridge.prepareSecureCredentialUpdate({
          items: payload.items,
          maskToken,
        });
        if (prepared.supported && prepared.transactionId) {
          const transactionId = prepared.transactionId;
          const handledKeys = new Set(prepared.handledKeys.map((key) => key.toUpperCase()));
          const backendItems = payload.items.flatMap((item) => {
            if (!handledKeys.has(item.key.toUpperCase())) {
              return [item];
            }
            return isPendingLLMCredentialKey(item.key)
              ? [{ key: item.key, value: maskToken }]
              : [];
          });
          let backendResult: UpdateSystemConfigResponse = {
            success: true,
            configVersion: payload.configVersion,
            appliedCount: 0,
            skippedMaskedCount: 0,
            reloadTriggered: false,
            updatedKeys: [],
            warnings: [],
          };
          let vaultCommitted = false;

          try {
            if (backendItems.length > 0) {
              const response = await apiClient.put<Record<string, unknown>>(
                '/api/v1/system/config',
                toSnakeUpdatePayload({
                  ...payload,
                  items: backendItems,
                  reloadNow: false,
                }),
              );
              backendResult = toCamelCase<UpdateSystemConfigResponse>(response.data);
            }
            await desktopBridge.commitSecureCredentialUpdate({
              transactionId,
              configVersion: backendResult.configVersion,
            });
            vaultCommitted = true;
            await desktopBridge.finalizeSecureCredentialUpdate(transactionId);
          } catch (error) {
            if (!vaultCommitted) {
              try {
                await desktopBridge.rollbackSecureCredentialUpdate(transactionId);
              } catch {
                // Keep the original failure. Main returns only generic secure-storage errors.
              }
            }
            throw error;
          }

          const refreshed = await this.getConfig(false);
          return {
            ...backendResult,
            success: true,
            configVersion: refreshed.configVersion,
            appliedCount: backendResult.appliedCount + prepared.changedKeys.length,
            skippedMaskedCount:
              backendResult.skippedMaskedCount + prepared.skippedMaskedKeys.length,
            reloadTriggered: true,
            updatedKeys: [...new Set([
              ...backendResult.updatedKeys,
              ...prepared.changedKeys,
            ])],
          };
        }
      }

      const response = await apiClient.put<Record<string, unknown>>(
        '/api/v1/system/config',
        toSnakeUpdatePayload(payload),
      );
      return toCamelCase<UpdateSystemConfigResponse>(response.data);
    } catch (error: unknown) {
      const parsed = getParsedApiError(error);
      if (error && typeof error === 'object' && 'response' in error) {
        const status = (error as { response?: { status?: number } }).response?.status;
        const payloadData = (error as { response?: { data?: unknown } }).response?.data;

        if (status === 400) {
          const validationError = parseSystemConfigValidationError(payloadData);
          throw createSystemConfigValidationError(validationError, parsed);
        }

        if (status === 409) {
          const conflict = toCamelCase<SystemConfigConflictResponse>(payloadData ?? {});
          throw new SystemConfigConflictError(
            parsed.message || conflict.message || '配置版本冲突',
            conflict.currentConfigVersion,
            parsed,
          );
        }
      }

      throw error;
    }
  },

  /**
   * 获取自选队列股票代码列表
   */
  getWatchlist: async (): Promise<string[]> => {
    const response = await apiClient.get<Record<string, unknown>>('/api/v1/stocks/watchlist');
    const data = toCamelCase<{ stockCodes: string[] }>(response.data);
    return data.stockCodes || [];
  },

  /**
   * 添加股票到自选队列
   */
  addToWatchlist: async (stockCode: string): Promise<string[]> => {
    const response = await apiClient.post<Record<string, unknown>>('/api/v1/stocks/watchlist/add', {
      stock_code: stockCode,
    });
    const data = toCamelCase<{ stockCodes: string[] }>(response.data);
    return data.stockCodes || [];
  },

  /**
   * 从自选队列移除股票
   */
  removeFromWatchlist: async (stockCode: string): Promise<string[]> => {
    const response = await apiClient.post<Record<string, unknown>>('/api/v1/stocks/watchlist/remove', {
      stock_code: stockCode,
    });
    const data = toCamelCase<{ stockCodes: string[] }>(response.data);
    return data.stockCodes || [];
  },
};
