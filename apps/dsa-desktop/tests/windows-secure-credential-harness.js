const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { app, safeStorage } = require('electron');
const { CredentialVault } = require('../secure-credentials/credentialVault');
const { sanitizeEnvFile } = require('../secure-credentials/envSanitizer');

const PASS_MARKER = 'R3_7_WINDOWS_FAKE_CREDENTIAL_VALIDATION=PASS';

function requireGate(condition) {
  if (!condition) {
    throw new Error('Windows secure credential validation gate failed.');
  }
}

function sameSecret(left, right) {
  const leftDigest = crypto.createHash('sha256').update(left, 'utf8').digest();
  const rightDigest = crypto.createHash('sha256').update(right, 'utf8').digest();
  return crypto.timingSafeEqual(leftDigest, rightDigest);
}

function fileVersion(filePath) {
  if (!fs.existsSync(filePath)) {
    return 'missing:0';
  }
  const content = fs.readFileSync(filePath);
  const stat = fs.statSync(filePath, { bigint: true });
  const digest = crypto.createHash('sha256').update(content).digest('hex');
  return `${stat.mtimeNs}:${digest}`;
}

async function run() {
  requireGate(process.platform === 'win32');
  requireGate(safeStorage.isEncryptionAvailable() === true);

  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-r37-safe-storage-'));
  const vaultPath = path.join(root, 'secure-credentials.v1.json');
  const envPath = path.join(root, '.env');
  const exportEnvPath = path.join(root, 'export.env');
  const fake = process.env.DSA_WINDOWS_TEST_FAKE_CREDENTIAL || '';
  requireGate(/^pp02-r37-[0-9a-f]{64}$/.test(fake));

  try {
    fs.writeFileSync(envPath, 'STOCK_LIST=600519\n', { encoding: 'utf8', mode: 0o600 });
    const configVersion = fileVersion(envPath);
    const vault = new CredentialVault({
      safeStorage,
      platform: process.platform,
      vaultPath,
    });
    const transaction = vault.prepare(
      [{ key: 'OPENAI_API_KEY', value: fake }],
      '******',
    );
    vault.commit(transaction, configVersion);

    const vaultBytes = fs.readFileSync(vaultPath);
    requireGate(!vaultBytes.includes(Buffer.from(fake, 'utf8')));
    const environment = vault.buildEnvironment(configVersion);
    requireGate(environment.keys.length === 1);
    requireGate(environment.keys[0] === 'OPENAI_API_KEY');
    requireGate(sameSecret(environment.values.OPENAI_API_KEY, fake));

    fs.writeFileSync(
      exportEnvPath,
      `# Export candidate\nSTOCK_LIST=600519\nOPENAI_API_KEY=${fake}\n`,
      { encoding: 'utf8', mode: 0o600 },
    );
    const removed = sanitizeEnvFile(exportEnvPath);
    const sanitized = fs.readFileSync(exportEnvPath, 'utf8');
    requireGate(removed.length === 1 && removed[0] === 'OPENAI_API_KEY');
    requireGate(!sanitized.includes(fake));
    requireGate(!sanitized.includes('OPENAI_API_KEY'));
    requireGate(sanitized.includes('STOCK_LIST=600519'));

    vault.finalize(transaction);
    process.stdout.write(`${PASS_MARKER}\n`);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
}

app.disableHardwareAcceleration();
app.whenReady()
  .then(run)
  .then(() => app.quit())
  .catch(() => {
    process.stderr.write('R3_7_WINDOWS_FAKE_CREDENTIAL_VALIDATION=FAIL\n');
    process.exitCode = 1;
    app.quit();
  });
