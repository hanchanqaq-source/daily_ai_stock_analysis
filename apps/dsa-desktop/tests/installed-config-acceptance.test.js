const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  createAcceptanceServer,
  deriveFakeCredential,
} = require('./installed-config-smoke-server');

function request({ port, authorization, body }) {
  return new Promise((resolve, reject) => {
    const payload = typeof body === 'string' ? body : JSON.stringify(body);
    const req = http.request({
      host: '127.0.0.1',
      port,
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        authorization,
        'content-type': 'application/json',
        'content-length': Buffer.byteLength(payload),
      },
      timeout: 2000,
    }, (response) => {
      const chunks = [];
      response.on('data', (chunk) => chunks.push(chunk));
      response.on('end', () => resolve({
        statusCode: response.statusCode,
        body: Buffer.concat(chunks).toString('utf8'),
      }));
    });
    req.on('timeout', () => req.destroy(new Error('request timeout')));
    req.on('error', reject);
    req.end(payload);
  });
}

test('exact-Head fake credential is deterministic and never embedded in harness source', () => {
  const head = 'a'.repeat(40);
  const expected = `pp02-r37-${crypto.createHash('sha256')
    .update(`pp02-r37-fake:${head}`, 'utf8')
    .digest('hex')}`;
  assert.equal(deriveFakeCredential(head), expected);

  const serverSource = fs.readFileSync(
    path.join(__dirname, 'installed-config-smoke-server.js'),
    'utf8',
  );
  const vaultSource = fs.readFileSync(
    path.join(__dirname, 'windows-installed-config-vault-harness.js'),
    'utf8',
  );
  assert.match(serverSource, /127\.0\.0\.1/);
  assert.doesNotMatch(serverSource, /0\.0\.0\.0/);
  assert.doesNotMatch(serverSource, /console\.(?:log|error)\([^\n]*fake/i);
  assert.match(vaultSource, /safeStorage/);
  assert.match(vaultSource, /app\.setPath\('userData'/);
  assert.match(vaultSource, /LLM_AIHUBMIX_API_KEY/);
  assert.match(vaultSource, /getBackendConfigVersion/);
  assert.doesNotMatch(vaultSource, /DSA_CONFIG_ACCEPTANCE_FAKE_CREDENTIAL/);
  assert.doesNotMatch(vaultSource, /console\.(?:log|error)\([^\n]*(?:fake|secret)/i);
});

test('installed lifecycle pins Electron userData to a verifier-owned path', () => {
  const verifierSource = fs.readFileSync(
    path.join(__dirname, '../../../scripts/verify-windows-installer.ps1'),
    'utf8',
  );

  assert.match(
    verifierSource,
    /\$acceptanceUserData = Join-Path \$acceptanceRoot 'user-data'/,
  );
  assert.equal(
    (verifierSource.match(/--user-data-dir=/g) || []).length,
    2,
  );
  assert.doesNotMatch(
    verifierSource,
    /Get-ChildItem -LiteralPath \$acceptanceAppData -Directory/,
  );
  assert.match(verifierSource, /WINDOWS_INSTALLED_USER_DATA_ISOLATION=PASS/);
});

test('installed smoke failure preserves only sanitized diagnostic evidence', () => {
  const verifierSource = fs.readFileSync(
    path.join(__dirname, '../../../scripts/verify-windows-installer.ps1'),
    'utf8',
  );

  assert.match(verifierSource, /smoke-response-sanitized\.json/);
  assert.match(verifierSource, /mock-stdout-sanitized\.log/);
  assert.match(verifierSource, /mock-stderr-sanitized\.log/);
  assert.match(verifierSource, /receipt_exists/);
  assert.equal(
    (verifierSource.match(/mock-stderr-sanitized\.log/g) || []).length,
    2,
  );
  assert.doesNotMatch(verifierSource, /smoke-request-body/);
  assert.doesNotMatch(verifierSource, /smoke-authorization/);
  assert.match(
    verifierSource,
    /\$mockProcess\.WaitForExit\(\)\s+\$mockProcess\.Refresh\(\)\s+\$mockExitCode = \$mockProcess\.ExitCode/,
  );
  assert.match(verifierSource, /WINDOWS_INSTALLED_CONFIG_MOCK=PASS/);
  assert.match(verifierSource, /IsNullOrWhiteSpace\(\$mockStderrText\)/);

  const serverSource = fs.readFileSync(
    path.join(__dirname, 'installed-config-smoke-server.js'),
    'utf8',
  );
  assert.match(serverSource, /safeErrorName/);
  assert.match(serverSource, /safeErrorCode/);
  assert.match(serverSource, /await writeCompletionMarker\(\)/);
  assert.match(serverSource, /process\.exit\(0\)/);
  assert.doesNotMatch(serverSource, /error\.(?:message|stack)/);
});

test('loopback server rejects a wrong key and records only a safe successful receipt', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-config-smoke-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const receiptPath = path.join(root, 'receipt.json');
  const readyPath = path.join(root, 'ready.json');
  const head = 'b'.repeat(40);
  const server = await createAcceptanceServer({
    head,
    receiptPath,
    readyPath,
    lifetimeMs: 5000,
  });
  t.after(() => server.close());

  assert.equal(server.address.address, '127.0.0.1');
  const wrong = await request({
    port: server.address.port,
    authorization: 'Bearer pp02-r37-wrong',
    body: { model: 'pp02-acceptance', messages: [] },
  });
  assert.equal(wrong.statusCode, 401);
  assert.equal(fs.existsSync(receiptPath), false);

  const accepted = await request({
    port: server.address.port,
    authorization: `Bearer ${deriveFakeCredential(head)}`,
    body: { model: 'pp02-acceptance', messages: [{ role: 'user', content: 'fixed smoke' }] },
  });
  assert.equal(accepted.statusCode, 200);
  const completion = JSON.parse(accepted.body);
  assert.equal(
    completion.choices[0].message.content,
    '{"ok":true,"backend_smoke":"passed"}',
  );
  const receiptRaw = fs.readFileSync(receiptPath, 'utf8');
  const receipt = JSON.parse(receiptRaw);
  assert.deepEqual(receipt, {
    schemaVersion: 1,
    head,
    authorizationMatched: true,
    routeMatched: true,
    modelMatched: true,
    requestCount: 2,
  });
  assert.equal(receiptRaw.includes(deriveFakeCredential(head)), false);
});

test('loopback server rejects oversized bodies without preserving request content', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-config-smoke-large-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const receiptPath = path.join(root, 'receipt.json');
  const server = await createAcceptanceServer({
    head: 'c'.repeat(40),
    receiptPath,
    readyPath: path.join(root, 'ready.json'),
    maxBodyBytes: 64,
    lifetimeMs: 5000,
  });
  t.after(() => server.close());
  const response = await request({
    port: server.address.port,
    authorization: 'Bearer wrong',
    body: 'x'.repeat(65),
  });
  assert.equal(response.statusCode, 413);
  assert.equal(fs.existsSync(receiptPath), false);
});
