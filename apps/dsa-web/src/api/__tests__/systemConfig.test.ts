import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { systemConfigApi } from '../systemConfig';

const get = vi.hoisted(() => vi.fn());
const post = vi.hoisted(() => vi.fn());
const put = vi.hoisted(() => vi.fn());

vi.mock('../index', () => ({
  default: {
    get,
    post,
    put,
  },
}));

describe('systemConfigApi', () => {
  beforeEach(() => {
    get.mockReset();
    post.mockReset();
    put.mockReset();
    post.mockResolvedValue({
      data: {
        success: true,
        message: 'ok',
        error: null,
        error_code: null,
        stage: 'chat_completion',
        retryable: false,
        details: {},
        resolved_protocol: 'openai',
        resolved_model: 'openai/gpt-4o-mini',
        latency_ms: 10,
        capability_results: {},
      },
    });
  });

  afterEach(() => {
    delete (window as typeof window & { dsaDesktop?: unknown }).dsaDesktop;
  });

  it('routes Desktop secrets through a write-only transaction and refreshes the final version', async () => {
    const prepare = vi.fn().mockResolvedValue({
      supported: true,
      transactionId: 'transaction-1',
      handledKeys: ['OPENAI_API_KEY'],
      changedKeys: ['OPENAI_API_KEY'],
      skippedMaskedKeys: [],
    });
    const commit = vi.fn().mockResolvedValue({ committed: true });
    const rollback = vi.fn().mockResolvedValue({ rolledBack: true });
    const finalize = vi.fn().mockResolvedValue({ finalized: true });
    (window as typeof window & { dsaDesktop?: Record<string, unknown> }).dsaDesktop = {
      version: '3.28.0',
      getSecureCredentialStatus: vi.fn(),
      prepareSecureCredentialUpdate: prepare,
      commitSecureCredentialUpdate: commit,
      rollbackSecureCredentialUpdate: rollback,
      finalizeSecureCredentialUpdate: finalize,
    };
    post.mockResolvedValueOnce({ data: { valid: true, issues: [] } });
    put.mockResolvedValueOnce({
      data: {
        success: true,
        config_version: 'intermediate-version',
        applied_count: 1,
        skipped_masked_count: 0,
        reload_triggered: false,
        updated_keys: ['LOG_LEVEL'],
        warnings: [],
      },
    });
    get.mockResolvedValueOnce({
      data: {
        config_version: 'final-version',
        mask_token: '******',
        items: [],
        updated_at: null,
      },
    });

    const result = await systemConfigApi.update({
      configVersion: 'base-version',
      items: [
        { key: 'OPENAI_API_KEY', value: ['pp02', 'fake', 'value'].join('-') },
        { key: 'LOG_LEVEL', value: 'DEBUG' },
      ],
    });

    expect(post).toHaveBeenCalledWith('/api/v1/system/config/validate', {
      items: [
        { key: 'OPENAI_API_KEY', value: 'pp02-fake-value' },
        { key: 'LOG_LEVEL', value: 'DEBUG' },
      ],
    });
    expect(prepare).toHaveBeenCalledWith({
      items: [
        { key: 'OPENAI_API_KEY', value: 'pp02-fake-value' },
        { key: 'LOG_LEVEL', value: 'DEBUG' },
      ],
      maskToken: '******',
    });
    expect(put).toHaveBeenCalledWith('/api/v1/system/config', {
      config_version: 'base-version',
      mask_token: '******',
      reload_now: false,
      items: [{ key: 'LOG_LEVEL', value: 'DEBUG' }],
    });
    expect(commit).toHaveBeenCalledWith({
      transactionId: 'transaction-1',
      configVersion: 'intermediate-version',
    });
    expect(put.mock.invocationCallOrder[0]).toBeLessThan(commit.mock.invocationCallOrder[0]);
    expect(finalize).toHaveBeenCalledWith('transaction-1');
    expect(rollback).not.toHaveBeenCalled();
    expect(result.configVersion).toBe('final-version');
    expect(result.updatedKeys).toEqual(['LOG_LEVEL', 'OPENAI_API_KEY']);
    expect(result.reloadTriggered).toBe(true);
  });

  it('abandons the Desktop vault transaction when backend persistence fails before commit', async () => {
    const rollback = vi.fn().mockResolvedValue({ rolledBack: true });
    const commit = vi.fn().mockResolvedValue({ committed: true });
    (window as typeof window & { dsaDesktop?: Record<string, unknown> }).dsaDesktop = {
      version: '3.28.0',
      prepareSecureCredentialUpdate: vi.fn().mockResolvedValue({
        supported: true,
        transactionId: 'transaction-2',
        handledKeys: ['OPENAI_API_KEY'],
        changedKeys: ['OPENAI_API_KEY'],
        skippedMaskedKeys: [],
      }),
      commitSecureCredentialUpdate: commit,
      rollbackSecureCredentialUpdate: rollback,
      finalizeSecureCredentialUpdate: vi.fn(),
    };
    post.mockResolvedValueOnce({ data: { valid: true, issues: [] } });
    put.mockRejectedValueOnce(new Error('backend unavailable'));

    await expect(systemConfigApi.update({
      configVersion: 'base-version',
      items: [
        { key: 'OPENAI_API_KEY', value: 'fake-value' },
        { key: 'LOG_LEVEL', value: 'DEBUG' },
      ],
    })).rejects.toThrow('backend unavailable');

    expect(rollback).toHaveBeenCalledWith('transaction-2');
    expect(commit).not.toHaveBeenCalled();
  });

  it('rolls back the uncommitted vault transaction when the env-version binding fails', async () => {
    const rollback = vi.fn().mockResolvedValue({ rolledBack: true });
    const commit = vi.fn().mockRejectedValue(new Error('config version mismatch'));
    const finalize = vi.fn();
    (window as typeof window & { dsaDesktop?: Record<string, unknown> }).dsaDesktop = {
      version: '3.28.0',
      prepareSecureCredentialUpdate: vi.fn().mockResolvedValue({
        supported: true,
        transactionId: 'transaction-3',
        handledKeys: ['OPENAI_API_KEY'],
        changedKeys: ['OPENAI_API_KEY'],
        skippedMaskedKeys: [],
      }),
      commitSecureCredentialUpdate: commit,
      rollbackSecureCredentialUpdate: rollback,
      finalizeSecureCredentialUpdate: finalize,
    };
    post.mockResolvedValueOnce({ data: { valid: true, issues: [] } });
    put.mockResolvedValueOnce({
      data: {
        success: true,
        config_version: 'new-env-version',
        applied_count: 1,
        skipped_masked_count: 0,
        reload_triggered: false,
        updated_keys: ['OPENAI_BASE_URL'],
        warnings: [],
      },
    });

    await expect(systemConfigApi.update({
      configVersion: 'base-version',
      items: [
        { key: 'OPENAI_API_KEY', value: 'fake-value' },
        { key: 'OPENAI_BASE_URL', value: 'https://example.invalid/v1' },
      ],
    })).rejects.toThrow('config version mismatch');

    expect(commit).toHaveBeenCalledWith({
      transactionId: 'transaction-3',
      configVersion: 'new-env-version',
    });
    expect(rollback).toHaveBeenCalledWith('transaction-3');
    expect(finalize).not.toHaveBeenCalled();
  });

  it('rebinds the vault version for Desktop updates that contain only public settings', async () => {
    const commit = vi.fn().mockResolvedValue({ committed: true });
    const finalize = vi.fn().mockResolvedValue({ finalized: true });
    (window as typeof window & { dsaDesktop?: Record<string, unknown> }).dsaDesktop = {
      version: '3.28.0',
      prepareSecureCredentialUpdate: vi.fn().mockResolvedValue({
        supported: true,
        transactionId: 'transaction-public',
        handledKeys: [],
        changedKeys: [],
        skippedMaskedKeys: [],
      }),
      commitSecureCredentialUpdate: commit,
      rollbackSecureCredentialUpdate: vi.fn(),
      finalizeSecureCredentialUpdate: finalize,
    };
    post.mockResolvedValueOnce({ data: { valid: true, issues: [] } });
    put.mockResolvedValueOnce({
      data: {
        success: true,
        config_version: 'public-env-version',
        applied_count: 1,
        skipped_masked_count: 0,
        reload_triggered: false,
        updated_keys: ['LOG_LEVEL'],
        warnings: [],
      },
    });
    get.mockResolvedValueOnce({
      data: {
        config_version: 'public-env-version',
        mask_token: '******',
        items: [],
        updated_at: null,
      },
    });

    await systemConfigApi.update({
      configVersion: 'base-version',
      items: [{ key: 'LOG_LEVEL', value: 'DEBUG' }],
    });

    expect(commit).toHaveBeenCalledWith({
      transactionId: 'transaction-public',
      configVersion: 'public-env-version',
    });
    expect(finalize).toHaveBeenCalledWith('transaction-public');
  });

  it('rebinds the vault version after a credential-free Desktop env import', async () => {
    const commit = vi.fn().mockResolvedValue({ committed: true });
    const finalize = vi.fn().mockResolvedValue({ finalized: true });
    (window as typeof window & { dsaDesktop?: Record<string, unknown> }).dsaDesktop = {
      version: '3.28.0',
      prepareSecureCredentialUpdate: vi.fn().mockResolvedValue({
        supported: true,
        transactionId: 'transaction-import',
        handledKeys: [],
        changedKeys: [],
        skippedMaskedKeys: [],
      }),
      commitSecureCredentialUpdate: commit,
      rollbackSecureCredentialUpdate: vi.fn(),
      finalizeSecureCredentialUpdate: finalize,
    };
    post.mockResolvedValueOnce({
      data: {
        success: true,
        config_version: 'import-env-version',
        applied_count: 1,
        skipped_masked_count: 0,
        reload_triggered: false,
        updated_keys: ['LOG_LEVEL'],
        warnings: [],
      },
    });

    const result = await systemConfigApi.importEnv({
      configVersion: 'base-version',
      content: 'LOG_LEVEL=DEBUG\n',
      reloadNow: true,
    });

    expect(post).toHaveBeenCalledWith('/api/v1/system/config/import', {
      config_version: 'base-version',
      content: 'LOG_LEVEL=DEBUG\n',
      reload_now: false,
    });
    expect(commit).toHaveBeenCalledWith({
      transactionId: 'transaction-import',
      configVersion: 'import-env-version',
    });
    expect(finalize).toHaveBeenCalledWith('transaction-import');
    expect(result.reloadTriggered).toBe(true);
  });

  it('omits capability_checks from basic LLM channel test payloads', async () => {
    await systemConfigApi.testLLMChannel({
      name: 'openai',
      protocol: 'openai',
      baseUrl: 'https://api.openai.com/v1',
      apiKey: 'sk-test',
      models: ['gpt-4o-mini'],
    });

    expect(post).toHaveBeenCalledWith(
      '/api/v1/system/config/llm/test-channel',
      expect.not.objectContaining({ capability_checks: expect.anything() }),
    );
  });

  it('sends capability_checks only for explicit runtime capability checks', async () => {
    await systemConfigApi.testLLMChannel({
      name: 'openai',
      protocol: 'openai',
      baseUrl: 'https://api.openai.com/v1',
      apiKey: 'sk-test',
      models: ['gpt-4o-mini'],
      capabilityChecks: ['json', 'stream'],
    });

    expect(post).toHaveBeenCalledWith(
      '/api/v1/system/config/llm/test-channel',
      expect.objectContaining({ capability_checks: ['json', 'stream'] }),
    );
  });

  it('sends notification channel test payloads with snake_case fields', async () => {
    post.mockResolvedValueOnce({
      data: {
        success: true,
        message: 'ok',
        error_code: null,
        stage: 'notification_send',
        retryable: false,
        latency_ms: 15,
        attempts: [
          {
            channel: 'custom',
            success: true,
            message: 'sent',
            target: 'https://example.com/hook?token=***',
            error_code: null,
            stage: 'notification_send',
            retryable: false,
            latency_ms: 15,
            http_status: 200,
          },
        ],
      },
    });

    const result = await systemConfigApi.testNotificationChannel({
      channel: 'custom',
      items: [{ key: 'CUSTOM_WEBHOOK_URLS', value: 'https://example.com/hook?token=secret' }],
      maskToken: '******',
      title: 'hello',
      content: 'world',
      timeoutSeconds: 7,
    });

    expect(post).toHaveBeenCalledWith(
      '/api/v1/system/config/notification/test-channel',
      {
        channel: 'custom',
        items: [{ key: 'CUSTOM_WEBHOOK_URLS', value: 'https://example.com/hook?token=secret' }],
        mask_token: '******',
        title: 'hello',
        content: 'world',
        timeout_seconds: 7,
      },
    );
    expect(result.latencyMs).toBe(15);
    expect(result.attempts[0].errorCode).toBeNull();
    expect(result.attempts[0].httpStatus).toBe(200);
  });

  it('loads first-run setup status with camelCase fields', async () => {
    get.mockResolvedValueOnce({
      data: {
        is_complete: false,
        ready_for_smoke: false,
        required_missing_keys: ['llm_primary'],
        next_step_key: 'llm_primary',
        checks: [
          {
            key: 'llm_primary',
            title: 'LLM 主渠道',
            category: 'ai_model',
            required: true,
            status: 'needs_action',
            message: '缺少主模型配置',
            next_step: '打开系统设置',
          },
        ],
      },
    });

    const result = await systemConfigApi.getSetupStatus();

    expect(get).toHaveBeenCalledWith('/api/v1/system/config/setup/status');
    expect(result.isComplete).toBe(false);
    expect(result.nextStepKey).toBe('llm_primary');
    expect(result.checks[0].nextStep).toBe('打开系统设置');
  });

  it('loads generation backend status with camelCase fields', async () => {
    get.mockResolvedValueOnce({
      data: {
        primary_backend_id: 'codex_cli',
        fallback_backend_id: null,
        primary: {
          backend_id: 'codex_cli',
          backend_type: 'local_cli',
          provider_id: 'codex_cli',
          available: true,
          health_status: 'passed',
          supports_json: true,
          supports_tools: false,
          supports_stream: true,
          supports_vision: false,
          is_primary: true,
          fallback_target: null,
          max_concurrency: 1,
          usage_available: false,
          last_error_code: null,
          last_error_message: null,
        },
        fallback: null,
        backends: [],
      },
    });

    const result = await systemConfigApi.getGenerationBackendStatus();

    expect(get).toHaveBeenCalledWith('/api/v1/system/config/generation-backends/status');
    expect(result.primaryBackendId).toBe('codex_cli');
    expect(result.primary.supportsTools).toBe(false);
    expect(result.primary.healthStatus).toBe('passed');
  });

  it('previews generation backend status with draft items and mask token', async () => {
    post.mockResolvedValueOnce({
      data: {
        primary_backend_id: 'opencode_cli',
        fallback_backend_id: null,
        primary: {
          backend_id: 'opencode_cli',
          backend_type: 'local_cli',
          provider_id: 'opencode_cli',
          available: false,
          health_status: 'failed',
          supports_json: true,
          supports_tools: false,
          supports_stream: false,
          supports_vision: false,
          is_primary: true,
          fallback_target: null,
          max_concurrency: 1,
          usage_available: false,
          last_error_code: 'command_not_found',
          last_error_message: 'Executable not found',
        },
        fallback: null,
        backends: [],
      },
    });

    const result = await systemConfigApi.previewGenerationBackendStatus({
      items: [
        { key: 'GENERATION_BACKEND', value: 'opencode_cli' },
        { key: 'OPENAI_API_KEY', value: '******' },
      ],
      maskToken: '******',
    });

    expect(post).toHaveBeenCalledWith(
      '/api/v1/system/config/generation-backends/status/preview',
      {
        items: [
          { key: 'GENERATION_BACKEND', value: 'opencode_cli' },
          { key: 'OPENAI_API_KEY', value: '******' },
        ],
        mask_token: '******',
      },
    );
    expect(result.primary.lastErrorCode).toBe('command_not_found');
  });

  it('runs generation backend smoke tests with snake_case fields', async () => {
    post.mockResolvedValueOnce({
      data: {
        success: true,
        mode: 'json',
        message: 'JSON smoke test passed',
        status: {
          backend_id: 'litellm',
          backend_type: 'litellm',
          provider_id: 'litellm',
          available: true,
          health_status: 'passed',
          supports_json: true,
          supports_tools: false,
          supports_stream: true,
          supports_vision: false,
          is_primary: true,
          fallback_target: null,
          max_concurrency: 2,
          usage_available: true,
          last_error_code: null,
          last_error_message: null,
        },
      },
    });

    const result = await systemConfigApi.testGenerationBackend({
      backendId: 'litellm',
      mode: 'json',
      items: [{ key: 'LITELLM_MODEL', value: 'openai/gpt-4o-mini' }],
      maskToken: '******',
      timeoutSeconds: 9,
    });

    expect(post).toHaveBeenCalledWith(
      '/api/v1/system/config/generation-backends/smoke-test',
      {
        backend_id: 'litellm',
        mode: 'json',
        items: [{ key: 'LITELLM_MODEL', value: 'openai/gpt-4o-mini' }],
        mask_token: '******',
        timeout_seconds: 9,
      },
    );
    expect(result.success).toBe(true);
    expect(result.status.healthStatus).toBe('passed');
  });

  it('loads the flat Agent backend compatibility status', async () => {
    get.mockResolvedValueOnce({
      data: {
        backend: 'codex_app_server',
        available: true,
        experimental: true,
        version: 'codex-cli test',
        error_code: null,
        message: null,
      },
    });

    const result = await systemConfigApi.getAgentBackendStatus();

    expect(get).toHaveBeenCalledWith('/api/v1/system/config/agent-backends/status');
    expect(result).toEqual({
      backend: 'codex_app_server',
      available: true,
      experimental: true,
      version: 'codex-cli test',
      errorCode: null,
      message: null,
    });
  });

  it('previews Agent backend status with unsaved draft items', async () => {
    post.mockResolvedValueOnce({
      data: {
        backend: 'codex_app_server',
        available: false,
        experimental: true,
        version: null,
        error_code: 'unsupported_agent_arch',
        message: 'single only',
      },
    });

    const result = await systemConfigApi.previewAgentBackendStatus({
      items: [
        { key: 'AGENT_BACKEND', value: 'codex_app_server' },
        { key: 'AGENT_ARCH', value: 'multi' },
      ],
      maskToken: '***',
    });

    expect(post).toHaveBeenCalledWith('/api/v1/system/config/agent-backends/status/preview', {
      items: [
        { key: 'AGENT_BACKEND', value: 'codex_app_server' },
        { key: 'AGENT_ARCH', value: 'multi' },
      ],
      mask_token: '***',
    });
    expect(result.errorCode).toBe('unsupported_agent_arch');
    expect(result.message).toBe('single only');
  });
});
