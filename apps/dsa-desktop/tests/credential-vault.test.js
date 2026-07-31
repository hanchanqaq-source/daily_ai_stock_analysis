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
  vault.commit(transaction);

  const rawVault = fs.readFileSync(vaultPath, 'utf8');
  assert.equal(rawVault.includes(value), false);
  assert.deepEqual(JSON.parse(rawVault).version, 1);
  assert.deepEqual(vault.status(), {
    supported: true,
    storage: 'windows_dpapi',
    configuredKeys: ['OPENAI_API_KEY'],
  });

  const environment = vault.buildEnvironment();
  assert.deepEqual(environment.keys, ['OPENAI_API_KEY']);
  assert.equal(environment.values.OPENAI_API_KEY === value, true, 'decrypted value mismatch');
});

test('mask is a no-op, empty value deletes, and rollback restores committed state', (t) => {
  const { vault } = createVault(t);
  const original = fakeCredential();
  const replacement = `${original}-rotated`;

  vault.commit(vault.prepare([{ key: 'OPENAI_API_KEY', value: original }], MASK_TOKEN));
  const masked = vault.prepare([{ key: 'OPENAI_API_KEY', value: MASK_TOKEN }], MASK_TOKEN);
  assert.deepEqual(masked.changedKeys, []);
  vault.commit(masked);

  const rotated = vault.prepare([{ key: 'OPENAI_API_KEY', value: replacement }], MASK_TOKEN);
  vault.commit(rotated);
  vault.rollback(rotated);
  assert.equal(vault.buildEnvironment().values.OPENAI_API_KEY === original, true);

  vault.commit(vault.prepare([{ key: 'OPENAI_API_KEY', value: '' }], MASK_TOKEN));
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
  writer.commit(writer.prepare([{ key: 'OPENAI_API_KEY', value: fakeCredential() }], MASK_TOKEN));

  const reader = new CredentialVault({
    platform: 'win32',
    safeStorage: createFakeSafeStorage({ decryptError: new Error('sensitive platform detail') }),
    vaultPath,
    productId: PRODUCT_ID,
  });
  assert.throws(
    () => reader.buildEnvironment(),
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
  vault.commit(vault.prepare([{ key: 'OPENAI_API_KEY', value: fakeCredential() }], MASK_TOKEN));
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
    ),
    (error) => error instanceof SecureCredentialError && error.code === 'vault_write_failed',
  );
  assert.deepEqual(fs.readFileSync(vaultPath), originalBytes);
  assert.equal(fs.existsSync(`${vaultPath}.tmp`), false);
});
