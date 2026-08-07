'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const { app, safeStorage } = require('electron');
const { CredentialVault } = require('../secure-credentials/credentialVault');

const PASS_MARKER = 'WINDOWS_INSTALLED_CONFIG_VAULT=PASS';

function requireGate(condition) {
  if (!condition) throw new Error('Installed configuration vault gate failed.');
}

function pathInside(child, parent) {
  const relative = path.relative(path.resolve(parent), path.resolve(child));
  return relative !== '' && !relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative);
}

function deriveFakeCredential(head) {
  const digest = crypto.createHash('sha256')
    .update(`pp02-r37-fake:${head}`, 'utf8')
    .digest('hex');
  return `pp02-r37-${digest}`;
}

function getBackendConfigVersion(envPath) {
  const exists = fs.existsSync(envPath);
  const marker = Buffer.from(exists ? 'present\0' : 'missing\0', 'utf8');
  const content = exists ? fs.readFileSync(envPath) : Buffer.alloc(0);
  const digest = crypto.createHash('sha256')
    .update(Buffer.concat([marker, content]))
    .digest('hex');
  return `sha256:${digest}`;
}

function getVaultConfigVersion(envPath) {
  const content = fs.readFileSync(envPath);
  const stat = fs.statSync(envPath, { bigint: true });
  const digest = crypto.createHash('sha256').update(content).digest('hex');
  return `${stat.mtimeNs}:${digest}`;
}

function sameSecret(left, right) {
  const leftDigest = crypto.createHash('sha256').update(left, 'utf8').digest();
  const rightDigest = crypto.createHash('sha256').update(right, 'utf8').digest();
  return crypto.timingSafeEqual(leftDigest, rightDigest);
}

const head = String(process.env.DSA_CONFIG_ACCEPTANCE_HEAD || '').toLowerCase();
const userData = path.resolve(process.env.DSA_CONFIG_ACCEPTANCE_USER_DATA || '');
const envPath = path.resolve(process.env.DSA_CONFIG_ACCEPTANCE_ENV_PATH || '');
const backendConfigVersion = process.env.DSA_CONFIG_ACCEPTANCE_BACKEND_VERSION || '';
const runnerTemp = path.resolve(process.env.RUNNER_TEMP || '');

requireGate(/^[0-9a-f]{40}$/.test(head));
requireGate(/^sha256:[0-9a-f]{64}$/.test(backendConfigVersion));
requireGate(runnerTemp && pathInside(userData, runnerTemp));
requireGate(runnerTemp && pathInside(envPath, runnerTemp));
fs.mkdirSync(userData, { recursive: true });
app.setName('PP02 AI Daily Stock Analysis');
app.setPath('userData', userData);
app.disableHardwareAcceleration();

async function run() {
  requireGate(process.platform === 'win32');
  requireGate(safeStorage.isEncryptionAvailable() === true);
  requireGate(getBackendConfigVersion(envPath) === backendConfigVersion);

  const fakeCredential = deriveFakeCredential(head);
  const vaultPath = path.join(userData, 'secure-credentials.v1.json');
  const vault = new CredentialVault({
    safeStorage,
    platform: process.platform,
    vaultPath,
  });
  const transaction = vault.prepare(
    [{ key: 'LLM_AIHUBMIX_API_KEY', value: fakeCredential }],
    '******',
  );
  const vaultConfigVersion = getVaultConfigVersion(envPath);
  vault.commit(transaction, vaultConfigVersion);
  vault.finalize(transaction);

  const rawVault = fs.readFileSync(vaultPath);
  requireGate(!rawVault.includes(Buffer.from(fakeCredential, 'utf8')));
  const environment = vault.buildEnvironment(vaultConfigVersion);
  requireGate(environment.keys.length === 1);
  requireGate(environment.keys[0] === 'LLM_AIHUBMIX_API_KEY');
  requireGate(sameSecret(environment.values.LLM_AIHUBMIX_API_KEY, fakeCredential));
  process.stdout.write(`${PASS_MARKER}\n`);
}

app.whenReady()
  .then(run)
  .then(() => app.quit())
  .catch(() => {
    process.stderr.write('WINDOWS_INSTALLED_CONFIG_VAULT=FAIL\n');
    process.exitCode = 1;
    app.quit();
  });
