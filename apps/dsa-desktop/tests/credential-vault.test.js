const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  CredentialVault,
  SecureCredentialError,
} = require('../secure-credentials/credentialVault');
const {
  isSensitiveConfigKey,
} = require('../secure-credentials/sensitiveKeys');

const PRODUCT_ID = 'com.hanchanqaq.pp02.aidailystockanalysis';
const MASK_TOKEN = '******';
const CONFIG_VERSION = `1000:${'a'.repeat(64)}`;
const NEXT_CONFIG_VERSION = `2000:${'b'.repeat(64)}`;

function fakeCredential() {
  return ['pp02', 'windows', 'credential', 'test'].join('-');
}

function createFakeSafeStorage({ available = true, decryptError = null } = {}) {
  return {
    isEncryptionAvailable: () => available,
    encryptString: (value) => Buffer.from(value, 'utf8').map((byte) => byte ^ 0xa5),
    decryptString: (buffer) => {
      if (decryptError) {
        throw decryptError;
      }
      return Buffer.from(buffer).map((byte) => byte ^ 0xa5).toString('utf8');
    },
  };
}

function createVault(t, options = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-credential-vault-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const vaultPath = path.join(root, 'secure-credentials.v1.json');
  return {
    root,
    vaultPath,
    vault: new CredentialVault({
      platform: 'win32',
      safeStorage: createFakeSafeStorage(),
      vaultPath,
      productId: PRODUCT_ID,
      ...options,
    }),
  };
}

test('sensitive key policy covers registered secrets and capability URLs', () => {
  assert.equal(isSensitiveConfigKey('OPENAI_API_KEY'), true);
  assert.equal(isSensitiveConfigKey('LLM_CUSTOM_EXTRA_HEADERS'), true);
  assert.equal(isSensitiveConfigKey('CUSTOM_WEBHOOK_URLS'), true);
  assert.equal(isSensitiveConfigKey('SLACK_WEBHOOK_URL'), true);
  assert.equal(isSensitiveConfigKey('ALPHASIFT_INSTALL_SPEC'), true);
  assert.equal(isSensitiveConfigKey('STOCK_LIST'), false);
  assert.equal(isSensitiveConfigKey('LLM_USAGE_HMAC_KEY_VERSION'), false);
  assert.equal(isSensitiveConfigKey('ANTHROPIC_MAX_TOKENS'), false);
  assert.equal(isSensitiveConfigKey('FEISHU_WEBHOOK_KEYWORD'), false);
  assert.equal(isSensitiveConfigKey('DISCORD_INTERACTIONS_PUBLIC_KEY'), false);
  assert.equal(isSensitiveConfigKey('../OPENAI_API_KEY'), false);
});

test('vault fails closed outside Windows or when safeStorage is unavailable', (t) => {
  const nonWindows = createVault(t, { platform: 'linux' }).vault;
  const unavailable = createVault(t, {
    safeStorage: createFakeSafeStorage({ available: false }),
  }).vault;

  assert.equal(nonWindows.status().supported, false);
  assert.equal(unavailable.status().supported, false);
  assert.throws(
    () => unavailable.prepare([{ key: 'OPENAI_API_KEY', value: fakeCredential() }], MASK_TOKEN),
    (error) => error instanceof SecureCredentialError && error.code === 'encryption_unavailable',
  );
});

test('vault commit stores ciphertext only and buildEnvironment decrypts in memory', (t) => {
  const { vault, vaultPath } = createVault(t);
  const value = fakeCredential();

  const transaction = vault.prepare(
    [
      { key: 'OPENAI_API_KEY', value },
      { key: 'STOCK_LIST', value: '600519' },
    ],
    MASK_TOKEN,
  );
  assert.deepEqual(transaction.handledKeys, ['OPENAI_API_KEY']);
  vault.commit(transaction, CONFIG_VERSION);

  const rawVault = fs.readFileSync(vaultPath, 'utf8');
  assert.equal(rawVault.includes(value), false);
  assert.deepEqual(JSON.parse(rawVault).version, 1);
  assert.deepEqual(vault.status(), {
    supported: true,
    storage: 'windows_dpapi',
    configuredKeys: ['OPENAI_API_KEY'],
  });

  const environment = vault.buildEnvironment(CONFIG_VERSION);
  assert.deepEqual(environment.keys, ['OPENAI_API_KEY']);
  assert.equal(environment.values.OPENAI_API_KEY === value, true, 'decrypted value mismatch');
});

test('mask is a no-op, empty value deletes, and rollback restores committed state', (t) => {
  const { vault } = createVault(t);
  const original = fakeCredential();
  const replacement = `${original}-rotated`;

  const initial = vault.prepare([{ key: 'OPENAI_API_KEY', value: original }], MASK_TOKEN);
  vault.commit(initial, CONFIG_VERSION);
  vault.finalize(initial);
  const masked = vault.prepare([{ key: 'OPENAI_API_KEY', value: MASK_TOKEN }], MASK_TOKEN);
  assert.deepEqual(masked.changedKeys, []);
  vault.commit(masked, CONFIG_VERSION);
  vault.finalize(masked);

  const rotated = vault.prepare([{ key: 'OPENAI_API_KEY', value: replacement }], MASK_TOKEN);
  vault.commit(rotated, CONFIG_VERSION);
  vault.rollback(rotated);
  assert.equal(vault.buildEnvironment(CONFIG_VERSION).values.OPENAI_API_KEY === original, true);

  const deleted = vault.prepare([{ key: 'OPENAI_API_KEY', value: '' }], MASK_TOKEN);
  vault.commit(deleted, CONFIG_VERSION);
  assert.deepEqual(vault.status().configuredKeys, []);
});

test('invalid keys, excessive values, corrupt vaults, and wrong identity are rejected', (t) => {
  const { vault, vaultPath } = createVault(t);

  assert.throws(
    () => vault.prepare([{ key: '../OPENAI_API_KEY', value: fakeCredential() }], MASK_TOKEN),
    (error) => error instanceof SecureCredentialError && error.code === 'invalid_key',
  );
  assert.throws(
    () => vault.prepare([{ key: 'OPENAI_API_KEY', value: 'x'.repeat(65537) }], MASK_TOKEN),
    (error) => error instanceof SecureCredentialError && error.code === 'value_too_large',
  );

  fs.writeFileSync(vaultPath, '{not-json', 'utf8');
  assert.throws(
    () => vault.status(),
    (error) => error instanceof SecureCredentialError && error.code === 'vault_corrupt',
  );

  fs.writeFileSync(
    vaultPath,
    JSON.stringify({ version: 1, productId: 'wrong-product', entries: {} }),
    'utf8',
  );
  assert.throws(
    () => vault.status(),
    (error) => error instanceof SecureCredentialError && error.code === 'vault_identity_mismatch',
  );
});

test('decrypt failures do not echo plaintext, ciphertext, or platform exception text', (t) => {
  const { vaultPath } = createVault(t);
  const writer = new CredentialVault({
    platform: 'win32',
    safeStorage: createFakeSafeStorage(),
    vaultPath,
    productId: PRODUCT_ID,
  });
  writer.commit(
    writer.prepare([{ key: 'OPENAI_API_KEY', value: fakeCredential() }], MASK_TOKEN),
    CONFIG_VERSION,
  );

  const reader = new CredentialVault({
    platform: 'win32',
    safeStorage: createFakeSafeStorage({ decryptError: new Error('sensitive platform detail') }),
    vaultPath,
    productId: PRODUCT_ID,
  });
  assert.throws(
    () => reader.buildEnvironment(CONFIG_VERSION),
    (error) => (
      error instanceof SecureCredentialError
      && error.code === 'decrypt_failed'
      && !error.message.includes('sensitive platform detail')
      && !error.message.includes(fakeCredential())
    ),
  );
});

test('failed atomic replace preserves the prior encrypted vault', (t) => {
  const { vault, vaultPath } = createVault(t);
  vault.commit(
    vault.prepare([{ key: 'OPENAI_API_KEY', value: fakeCredential() }], MASK_TOKEN),
    CONFIG_VERSION,
  );
  const originalBytes = fs.readFileSync(vaultPath);
  const fsWithFailingRename = {
    ...fs,
    renameSync: () => {
      throw new Error('simulated replace failure');
    },
  };
  const failingVault = new CredentialVault({
    platform: 'win32',
    safeStorage: createFakeSafeStorage(),
    vaultPath,
    productId: PRODUCT_ID,
    fsImpl: fsWithFailingRename,
  });

  assert.throws(
    () => failingVault.commit(
      failingVault.prepare([{ key: 'OPENAI_API_KEY', value: `${fakeCredential()}-new` }], MASK_TOKEN),
      NEXT_CONFIG_VERSION,
    ),
    (error) => error instanceof SecureCredentialError && error.code === 'vault_write_failed',
  );
  assert.deepEqual(fs.readFileSync(vaultPath), originalBytes);
  assert.equal(fs.existsSync(`${vaultPath}.tmp`), false);
});

test('uncommitted credential transactions expire before they can modify the vault', (t) => {
  let now = 1_000;
  const { vault } = createVault(t, {
    now: () => now,
    transactionTtlMs: 100,
  });
  const transaction = vault.prepare(
    [{ key: 'OPENAI_API_KEY', value: fakeCredential() }],
    MASK_TOKEN,
  );

  now += 101;

  assert.throws(
    () => vault.commit(transaction, CONFIG_VERSION),
    (error) => error instanceof SecureCredentialError && error.code === 'transaction_invalid',
  );
  assert.deepEqual(vault.status().configuredKeys, []);
});

test('vault fails closed when encrypted credentials are bound to another env version', (t) => {
  const { vault } = createVault(t);
  const transaction = vault.prepare(
    [{ key: 'OPENAI_API_KEY', value: fakeCredential() }],
    MASK_TOKEN,
  );
  vault.commit(transaction, CONFIG_VERSION);

  assert.throws(
    () => vault.buildEnvironment(NEXT_CONFIG_VERSION),
    (error) => error instanceof SecureCredentialError && error.code === 'vault_config_mismatch',
  );
  assert.equal(vault.buildEnvironment(CONFIG_VERSION).values.OPENAI_API_KEY, fakeCredential());
});

test('vault permits only one live transaction so rollback cannot erase another commit', (t) => {
  const { vault } = createVault(t);
  const first = vault.prepare(
    [{ key: 'OPENAI_API_KEY', value: fakeCredential() }],
    MASK_TOKEN,
  );

  assert.throws(
    () => vault.prepare([{ key: 'ANTHROPIC_API_KEY', value: 'second-fake' }], MASK_TOKEN),
    (error) => error instanceof SecureCredentialError && error.code === 'transaction_invalid',
  );

  vault.commit(first, CONFIG_VERSION);
  assert.throws(
    () => vault.prepare([{ key: 'ANTHROPIC_API_KEY', value: 'second-fake' }], MASK_TOKEN),
    (error) => error instanceof SecureCredentialError && error.code === 'transaction_invalid',
  );
  vault.finalize(first);

  const second = vault.prepare(
    [{ key: 'ANTHROPIC_API_KEY', value: 'second-fake' }],
    MASK_TOKEN,
  );
  vault.commit(second, NEXT_CONFIG_VERSION);
  assert.deepEqual(
    vault.buildEnvironment(NEXT_CONFIG_VERSION).keys,
    ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY'],
  );
});

test('finalizable assertion rejects invalid or uncommitted transactions before side effects', (t) => {
  const { vault } = createVault(t);
  const transaction = vault.prepare(
    [{ key: 'OPENAI_API_KEY', value: fakeCredential() }],
    MASK_TOKEN,
  );

  assert.throws(
    () => vault.assertFinalizable(transaction.id),
    (error) => error instanceof SecureCredentialError && error.code === 'transaction_invalid',
  );
  vault.commit(transaction, CONFIG_VERSION);
  assert.deepEqual(vault.assertFinalizable(transaction.id), transaction);
});

test('permission hardening failure happens before replace and preserves the prior vault', (t) => {
  const { vault, vaultPath } = createVault(t);
  const initial = vault.prepare(
    [{ key: 'OPENAI_API_KEY', value: fakeCredential() }],
    MASK_TOKEN,
  );
  vault.commit(initial, CONFIG_VERSION);
  vault.finalize(initial);
  const originalBytes = fs.readFileSync(vaultPath);
  const fsWithFailingChmod = {
    ...fs,
    chmodSync: () => {
      throw new Error('simulated permission failure');
    },
  };
  const failingVault = new CredentialVault({
    platform: 'win32',
    safeStorage: createFakeSafeStorage(),
    vaultPath,
    productId: PRODUCT_ID,
    fsImpl: fsWithFailingChmod,
  });

  assert.throws(
    () => failingVault.commit(
      failingVault.prepare([{ key: 'OPENAI_API_KEY', value: 'replacement-fake' }], MASK_TOKEN),
      NEXT_CONFIG_VERSION,
    ),
    (error) => error instanceof SecureCredentialError && error.code === 'vault_write_failed',
  );
  assert.deepEqual(fs.readFileSync(vaultPath), originalBytes);
});
