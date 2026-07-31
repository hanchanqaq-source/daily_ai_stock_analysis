const fs = require('node:fs');

const { isSensitiveConfigKey } = require('./sensitiveKeys');

function sanitizeEnvFile(envPath, { fsImpl = fs } = {}) {
  if (!fsImpl.existsSync(envPath)) {
    return [];
  }
  const original = fsImpl.readFileSync(envPath, 'utf8');
  const hadTrailingNewline = original.endsWith('\n');
  const removed = new Set();
  const retained = original.split(/\r?\n/).filter((line, index, lines) => {
    if (index === lines.length - 1 && line === '' && hadTrailingNewline) {
      return false;
    }
    const match = line.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=/);
    if (!match || !isSensitiveConfigKey(match[1])) {
      return true;
    }
    removed.add(match[1].toUpperCase());
    return false;
  });
  if (removed.size === 0) {
    return [];
  }

  const content = retained.length ? `${retained.join('\n')}\n` : '';
  const tempPath = `${envPath}.secure.tmp`;
  let descriptor = null;
  try {
    descriptor = fsImpl.openSync(tempPath, 'w', 0o600);
    fsImpl.writeFileSync(descriptor, content, 'utf8');
    fsImpl.fsyncSync(descriptor);
    fsImpl.closeSync(descriptor);
    descriptor = null;
    fsImpl.renameSync(tempPath, envPath);
  } catch (_error) {
    if (descriptor !== null) {
      try {
        fsImpl.closeSync(descriptor);
      } catch (_closeError) {
      }
    }
    try {
      if (fsImpl.existsSync(tempPath)) {
        fsImpl.unlinkSync(tempPath);
      }
    } catch (_cleanupError) {
    }
    const error = new Error('Environment credential cleanup failed.');
    error.code = 'env_sanitize_failed';
    throw error;
  }
  return [...removed].sort();
}

module.exports = { sanitizeEnvFile };
