const VALID_CONFIG_KEY_PATTERN = /^[A-Z][A-Z0-9_]{0,127}$/;

const SENSITIVE_CAPABILITY_KEYS = new Set([
  'ALPHASIFT_INSTALL_SPEC',
  'ASTRBOT_URL',
  'CUSTOM_WEBHOOK_URLS',
  'DINGTALK_WEBHOOK_URL',
  'DISCORD_WEBHOOK_URL',
  'FEISHU_WEBHOOK_URL',
  'GOTIFY_URL',
  'NTFY_URL',
  'SLACK_WEBHOOK_URL',
  'WECHAT_WEBHOOK_URL',
]);

const SENSITIVE_MARKERS = ['KEY', 'TOKEN', 'SECRET', 'PASSWORD'];
const NON_SENSITIVE_MARKER_KEYS = new Set([
  'AGENT_CONTEXT_COMPRESSION_TRIGGER_TOKENS',
  'ANTHROPIC_MAX_TOKENS',
  'DISCORD_INTERACTIONS_PUBLIC_KEY',
  'FEISHU_WEBHOOK_KEYWORD',
  'LLM_USAGE_HMAC_KEY_VERSION',
]);
const LLM_EXTRA_HEADERS_PATTERN = /^LLM_[A-Z0-9_]+_EXTRA_HEADERS$/;

function normalizeConfigKey(key) {
  return typeof key === 'string' ? key.trim().toUpperCase() : '';
}

function isValidConfigKey(key) {
  return VALID_CONFIG_KEY_PATTERN.test(normalizeConfigKey(key));
}

function isSensitiveConfigKey(key) {
  const normalized = normalizeConfigKey(key);
  if (!VALID_CONFIG_KEY_PATTERN.test(normalized)) {
    return false;
  }
  if (NON_SENSITIVE_MARKER_KEYS.has(normalized)) {
    return false;
  }
  return (
    SENSITIVE_CAPABILITY_KEYS.has(normalized)
    || LLM_EXTRA_HEADERS_PATTERN.test(normalized)
    || SENSITIVE_MARKERS.some((marker) => normalized.includes(marker))
  );
}

module.exports = {
  LLM_EXTRA_HEADERS_PATTERN,
  NON_SENSITIVE_MARKER_KEYS,
  SENSITIVE_CAPABILITY_KEYS,
  VALID_CONFIG_KEY_PATTERN,
  isSensitiveConfigKey,
  isValidConfigKey,
  normalizeConfigKey,
};
