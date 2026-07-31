const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const {
  isSensitiveConfigKey,
  isValidConfigKey,
  normalizeConfigKey,
} = require('./sensitiveKeys');

const DEFAULT_PRODUCT_ID = 'com.hanchanqaq.pp02.aidailystockanalysis';
const VAULT_VERSION = 1;
const MAX_CREDENTIAL_COUNT = 256;
const MAX_CREDENTIAL_VALUE_BYTES = 65536;
const MAX_CIPHERTEXT_BYTES = 262144;
const DEFAULT_TRANSACTION_TTL_MS = 5 * 60 * 1000;
const BASE64_PATTERN = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;

const ERROR_MESSAGES = Object.freeze({
  decrypt_failed: 'Secure credential decryption failed.',
  encryption_unavailable: 'Windows secure credential encryption is unavailable.',
  invalid_items: 'Secure credential update payload is invalid.',
  invalid_key: 'Secure credential key is invalid.',
  too_many_credentials: 'Secure credential count exceeds the supported limit.',
  transaction_invalid: 'Secure credential transaction is invalid or expired.',
  value_too_large: 'Secure credential value exceeds the supported limit.',
  vault_corrupt: 'Secure credential vault is invalid.',
  vault_identity_mismatch: 'Secure credential vault belongs to a different product.',
  vault_version_unsupported: 'Secure credential vault version is unsupported.',
  vault_write_failed: 'Secure credential vault could not be updated.',
});

class SecureCredentialError extends Error {
  constructor(code) {
    super(ERROR_MESSAGES[code] || 'Secure credential operation failed.');
    this.name = 'SecureCredentialError';
    this.code = code;
  }
}

class CredentialVault {
  constructor({
    safeStorage,
    vaultPath,
    platform = process.platform,
    productId = DEFAULT_PRODUCT_ID,
    fsImpl = fs,
    now = Date.now,
    transactionTtlMs = DEFAULT_TRANSACTION_TTL_MS,
  }) {
    if (
      !safeStorage
      || typeof vaultPath !== 'string'
      || !vaultPath.trim()
      || typeof now !== 'function'
      || !Number.isSafeInteger(transactionTtlMs)
      || transactionTtlMs <= 0
    ) {
      throw new SecureCredentialError('invalid_items');
    }
    this.safeStorage = safeStorage;
    this.vaultPath = path.resolve(vaultPath);
    this.platform = platform;
    this.productId = productId;
    this.fs = fsImpl;
    this.now = now;
    this.transactionTtlMs = transactionTtlMs;
    this.transactions = new Map();
  }

  isSupported() {
    return (
      this.platform === 'win32'
      && typeof this.safeStorage.isEncryptionAvailable === 'function'
      && this.safeStorage.isEncryptionAvailable() === true
    );
  }

  status() {
    if (!this.isSupported()) {
      return {
        supported: false,
        storage: 'windows_dpapi',
        configuredKeys: [],
      };
    }
    const document = this._readDocument().document;
    return {
      supported: true,
      storage: 'windows_dpapi',
      configuredKeys: Object.keys(document.entries).sort(),
    };
  }

  prepare(items, maskToken = '******') {
    this._assertSupported();
    if (!Array.isArray(items)) {
      throw new SecureCredentialError('invalid_items');
    }
    if (items.length > MAX_CREDENTIAL_COUNT) {
      throw new SecureCredentialError('too_many_credentials');
    }

    const before = this._readDocument();
    const nextEntries = { ...before.document.entries };
    const handledKeys = [];
    const changedKeys = [];
    const skippedMaskedKeys = [];

    for (const item of items) {
      const key = normalizeConfigKey(item && item.key);
      if (!isValidConfigKey(key)) {
        throw new SecureCredentialError('invalid_key');
      }
      if (!isSensitiveConfigKey(key)) {
        continue;
      }
      if (!handledKeys.includes(key)) {
        handledKeys.push(key);
      }

      const value = item && item.value == null ? '' : String(item.value);
      if (Buffer.byteLength(value, 'utf8') > MAX_CREDENTIAL_VALUE_BYTES) {
        throw new SecureCredentialError('value_too_large');
      }
      if (value === maskToken) {
        skippedMaskedKeys.push(key);
        continue;
      }
      if (value === '') {
        if (Object.hasOwn(nextEntries, key)) {
          delete nextEntries[key];
          changedKeys.push(key);
        }
        continue;
      }

      let encrypted;
      try {
        encrypted = this.safeStorage.encryptString(value);
      } catch (_error) {
        throw new SecureCredentialError('vault_write_failed');
      }
      if (!Buffer.isBuffer(encrypted) || encrypted.length === 0 || encrypted.length > MAX_CIPHERTEXT_BYTES) {
        throw new SecureCredentialError('vault_write_failed');
      }
      nextEntries[key] = encrypted.toString('base64');
      changedKeys.push(key);
    }

    const transaction = {
      id: crypto.randomUUID(),
      handledKeys: [...new Set(handledKeys)].sort(),
      changedKeys: [...new Set(changedKeys)].sort(),
      skippedMaskedKeys: [...new Set(skippedMaskedKeys)].sort(),
    };
    this.transactions.set(transaction.id, {
      public: transaction,
      beforeExists: before.exists,
      beforeRaw: before.raw,
      nextDocument: {
        version: VAULT_VERSION,
        productId: this.productId,
        entries: Object.fromEntries(Object.entries(nextEntries).sort(([a], [b]) => a.localeCompare(b))),
      },
      committed: false,
      createdAt: this.now(),
    });
    return transaction;
  }

  commit(transaction) {
    const internal = this._resolveTransaction(transaction);
    if (internal.committed) {
      return internal.public;
    }
    if (internal.public.changedKeys.length > 0) {
      this._writeDocument(internal.nextDocument);
    }
    internal.committed = true;
    return internal.public;
  }

  rollback(transaction) {
    const internal = this._resolveTransaction(transaction);
    if (internal.committed && internal.public.changedKeys.length > 0) {
      if (internal.beforeExists) {
        this._atomicWrite(internal.beforeRaw);
      } else {
        try {
          if (this.fs.existsSync(this.vaultPath)) {
            this.fs.unlinkSync(this.vaultPath);
          }
        } catch (_error) {
          throw new SecureCredentialError('vault_write_failed');
        }
      }
    }
    this.transactions.delete(internal.public.id);
    return internal.public;
  }

  finalize(transaction) {
    const internal = this._resolveTransaction(transaction);
    if (!internal.committed) {
      throw new SecureCredentialError('transaction_invalid');
    }
    this.transactions.delete(internal.public.id);
    return internal.public;
  }

  buildEnvironment() {
    this._assertSupported();
    const document = this._readDocument().document;
    const values = {};
    const keys = Object.keys(document.entries).sort();
    for (const key of keys) {
      try {
        const decrypted = this.safeStorage.decryptString(
          Buffer.from(document.entries[key], 'base64'),
        );
        if (typeof decrypted !== 'string' || Buffer.byteLength(decrypted, 'utf8') > MAX_CREDENTIAL_VALUE_BYTES) {
          throw new Error('invalid decrypted value');
        }
        values[key] = decrypted;
      } catch (_error) {
        throw new SecureCredentialError('decrypt_failed');
      }
    }
    return { keys, values };
  }

  _assertSupported() {
    if (!this.isSupported()) {
      throw new SecureCredentialError('encryption_unavailable');
    }
  }

  _resolveTransaction(transaction) {
    const id = typeof transaction === 'string' ? transaction : transaction && transaction.id;
    const internal = typeof id === 'string' ? this.transactions.get(id) : null;
    if (!internal || internal.public !== transaction && typeof transaction !== 'string') {
      throw new SecureCredentialError('transaction_invalid');
    }
    if (!internal.committed && this.now() - internal.createdAt > this.transactionTtlMs) {
      this.transactions.delete(internal.public.id);
      throw new SecureCredentialError('transaction_invalid');
    }
    return internal;
  }

  _readDocument() {
    if (!this.fs.existsSync(this.vaultPath)) {
      return {
        exists: false,
        raw: null,
        document: { version: VAULT_VERSION, productId: this.productId, entries: {} },
      };
    }

    let raw;
    let document;
    try {
      raw = this.fs.readFileSync(this.vaultPath);
      document = JSON.parse(raw.toString('utf8'));
    } catch (_error) {
      throw new SecureCredentialError('vault_corrupt');
    }
    if (!document || typeof document !== 'object' || Array.isArray(document)) {
      throw new SecureCredentialError('vault_corrupt');
    }
    if (document.version !== VAULT_VERSION) {
      throw new SecureCredentialError('vault_version_unsupported');
    }
    if (document.productId !== this.productId) {
      throw new SecureCredentialError('vault_identity_mismatch');
    }
    if (!document.entries || typeof document.entries !== 'object' || Array.isArray(document.entries)) {
      throw new SecureCredentialError('vault_corrupt');
    }
    const entries = Object.entries(document.entries);
    if (entries.length > MAX_CREDENTIAL_COUNT) {
      throw new SecureCredentialError('vault_corrupt');
    }
    for (const [key, ciphertext] of entries) {
      if (
        !isValidConfigKey(key)
        || !isSensitiveConfigKey(key)
        || typeof ciphertext !== 'string'
        || ciphertext.length === 0
        || ciphertext.length > MAX_CIPHERTEXT_BYTES * 2
        || !BASE64_PATTERN.test(ciphertext)
        || Buffer.from(ciphertext, 'base64').length > MAX_CIPHERTEXT_BYTES
      ) {
        throw new SecureCredentialError('vault_corrupt');
      }
    }
    return { exists: true, raw, document };
  }

  _writeDocument(document) {
    const content = Buffer.from(`${JSON.stringify(document, null, 2)}\n`, 'utf8');
    this._atomicWrite(content);
  }

  _atomicWrite(content) {
    const tempPath = `${this.vaultPath}.tmp`;
    let descriptor = null;
    try {
      this.fs.mkdirSync(path.dirname(this.vaultPath), { recursive: true });
      descriptor = this.fs.openSync(tempPath, 'w', 0o600);
      this.fs.writeFileSync(descriptor, content);
      this.fs.fsyncSync(descriptor);
      this.fs.closeSync(descriptor);
      descriptor = null;
      this.fs.renameSync(tempPath, this.vaultPath);
      if (typeof this.fs.chmodSync === 'function') {
        this.fs.chmodSync(this.vaultPath, 0o600);
      }
    } catch (_error) {
      if (descriptor !== null) {
        try {
          this.fs.closeSync(descriptor);
        } catch (_closeError) {
          // Best-effort cleanup only.
        }
      }
      try {
        if (this.fs.existsSync(tempPath)) {
          this.fs.unlinkSync(tempPath);
        }
      } catch (_cleanupError) {
        // Preserve the original generic error and never include file contents.
      }
      throw new SecureCredentialError('vault_write_failed');
    }
  }
}

module.exports = {
  CredentialVault,
  DEFAULT_PRODUCT_ID,
  MAX_CREDENTIAL_COUNT,
  MAX_CREDENTIAL_VALUE_BYTES,
  SecureCredentialError,
  VAULT_VERSION,
};
