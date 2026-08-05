const assert = require('node:assert/strict');
const test = require('node:test');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const hookPath = path.resolve(
  __dirname,
  '..',
  'scripts',
  'afterSignRuntimeIntegrity.js'
);
const runtimeIntegrity = require('../runtime-integrity/runtimeIntegrity');

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function createWindowsStage(t, { includeBackend = true } = {}) {
  const appOutDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-runtime-integrity-'));
  const desktopPath = path.join(appOutDir, 'PP02 AI Daily Stock Analysis.exe');
  const backendPath = path.join(
    appOutDir,
    'resources',
    'backend',
    'stock_analysis',
    'stock_analysis.exe'
  );
  fs.mkdirSync(path.dirname(backendPath), { recursive: true });
  fs.writeFileSync(desktopPath, 'signed-desktop-binary');
  if (includeBackend) {
    fs.writeFileSync(backendPath, 'frozen-backend-binary');
  }
  t.after(() => fs.rmSync(appOutDir, { recursive: true, force: true }));
  return { appOutDir, desktopPath, backendPath };
}

async function createVerifiedStage(t) {
  const stage = createWindowsStage(t);
  const { afterSign } = require(hookPath);
  const generated = await afterSign({
    appOutDir: stage.appOutDir,
    electronPlatformName: 'win32',
    packager: { appInfo: { version: '3.29.3' } },
  });
  return {
    ...stage,
    manifestPath: generated.manifestPath,
    manifest: generated.manifest,
    verifyOptions: {
      platform: 'win32',
      packaged: true,
      appRoot: stage.appOutDir,
      resourcesPath: path.join(stage.appOutDir, 'resources'),
      exePath: stage.desktopPath,
      backendPath: stage.backendPath,
      version: '3.29.3',
    },
  };
}

function rewriteManifest(stage, mutate) {
  const manifest = JSON.parse(JSON.stringify(stage.manifest));
  mutate(manifest);
  fs.writeFileSync(stage.manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
}

test('afterSign records exactly the signed desktop and backend executables', async (t) => {
  assert.equal(
    fs.existsSync(hookPath),
    true,
    'Windows runtime-integrity afterSign hook must exist'
  );
  const { afterSign } = require(hookPath);
  const stage = createWindowsStage(t);

  const result = await afterSign({
    appOutDir: stage.appOutDir,
    electronPlatformName: 'win32',
    packager: { appInfo: { version: '3.29.3' } },
  });

  assert.equal(
    result.manifestPath,
    path.join(stage.appOutDir, 'resources', 'pp02-runtime-integrity.json')
  );
  assert.deepEqual(result.manifest, {
    schemaVersion: 1,
    productId: 'com.hanchanqaq.pp02.aidailystockanalysis',
    version: '3.29.3',
    entries: [
      {
        role: 'desktop',
        relativePath: 'PP02 AI Daily Stock Analysis.exe',
        size: Buffer.byteLength('signed-desktop-binary'),
        sha256: sha256('signed-desktop-binary'),
      },
      {
        role: 'backend',
        relativePath: 'resources/backend/stock_analysis/stock_analysis.exe',
        size: Buffer.byteLength('frozen-backend-binary'),
        sha256: sha256('frozen-backend-binary'),
      },
    ],
  });
  assert.deepEqual(
    JSON.parse(fs.readFileSync(result.manifestPath, 'utf8')),
    result.manifest
  );
});

test('afterSign fails closed when a required executable is missing', async (t) => {
  assert.equal(fs.existsSync(hookPath), true);
  const { afterSign } = require(hookPath);
  const stage = createWindowsStage(t, { includeBackend: false });

  await assert.rejects(
    afterSign({
      appOutDir: stage.appOutDir,
      electronPlatformName: 'win32',
      packager: { appInfo: { version: '3.29.3' } },
    }),
    /required runtime file is missing: backend/
  );
});

test('afterSign rejects a required executable symlink that resolves outside the package', async (t) => {
  assert.equal(fs.existsSync(hookPath), true);
  const { afterSign } = require(hookPath);
  const stage = createWindowsStage(t, { includeBackend: false });
  const outsideRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-runtime-outside-'));
  const outsideBackend = path.join(outsideRoot, 'stock_analysis.exe');
  fs.writeFileSync(outsideBackend, 'outside-backend-binary');
  t.after(() => fs.rmSync(outsideRoot, { recursive: true, force: true }));
  try {
    fs.symlinkSync(outsideBackend, stage.backendPath, 'file');
  } catch (error) {
    if (error && ['EPERM', 'EACCES', 'ENOSYS'].includes(error.code)) {
      t.skip(`symbolic links unavailable: ${error.code}`);
      return;
    }
    throw error;
  }

  await assert.rejects(
    afterSign({
      appOutDir: stage.appOutDir,
      electronPlatformName: 'win32',
      packager: { appInfo: { version: '3.29.3' } },
    }),
    /required runtime path is not a regular in-package file: backend/
  );
});

test('afterSign skips non-Windows packages without writing a manifest', async (t) => {
  assert.equal(fs.existsSync(hookPath), true);
  const { afterSign } = require(hookPath);
  const stage = createWindowsStage(t);

  const result = await afterSign({
    appOutDir: stage.appOutDir,
    electronPlatformName: 'darwin',
    packager: { appInfo: { version: '3.29.3' } },
  });

  assert.deepEqual(result, { skipped: true });
  assert.equal(
    fs.existsSync(path.join(stage.appOutDir, 'resources', 'pp02-runtime-integrity.json')),
    false
  );
});

test('verifier accepts the exact two-entry packaged Windows manifest', async (t) => {
  assert.equal(
    typeof runtimeIntegrity.verifyPackagedWindowsRuntime,
    'function',
    'packaged Windows verifier must exist'
  );
  const stage = await createVerifiedStage(t);

  const result = runtimeIntegrity.verifyPackagedWindowsRuntime(stage.verifyOptions);

  assert.equal(result.verified, true);
  assert.deepEqual(result.roles, ['desktop', 'backend']);
});

test('verifier skips development and packaged non-Windows runs', () => {
  assert.equal(typeof runtimeIntegrity.verifyPackagedWindowsRuntime, 'function');
  assert.deepEqual(
    runtimeIntegrity.verifyPackagedWindowsRuntime({ platform: 'win32', packaged: false }),
    { skipped: true }
  );
  assert.deepEqual(
    runtimeIntegrity.verifyPackagedWindowsRuntime({ platform: 'darwin', packaged: true }),
    { skipped: true }
  );
});

test('verifier rejects a missing or malformed manifest', async (t) => {
  assert.equal(typeof runtimeIntegrity.verifyPackagedWindowsRuntime, 'function');
  const stage = await createVerifiedStage(t);
  fs.rmSync(stage.manifestPath);
  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime(stage.verifyOptions),
    (error) => error instanceof runtimeIntegrity.RuntimeIntegrityError && error.reasonCode === 'manifest_missing'
  );
  fs.writeFileSync(stage.manifestPath, '{not-json', 'utf8');
  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime(stage.verifyOptions),
    (error) => error instanceof runtimeIntegrity.RuntimeIntegrityError && error.reasonCode === 'manifest_malformed'
  );
});

test('verifier rejects another product or version', async (t) => {
  assert.equal(typeof runtimeIntegrity.verifyPackagedWindowsRuntime, 'function');
  const stage = await createVerifiedStage(t);
  rewriteManifest(stage, (manifest) => { manifest.productId = 'another.product'; });
  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime(stage.verifyOptions),
    (error) => error.reasonCode === 'product_mismatch'
  );
  rewriteManifest(stage, (manifest) => { manifest.version = '9.9.9'; });
  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime(stage.verifyOptions),
    (error) => error.reasonCode === 'version_mismatch'
  );
});

test('verifier rejects duplicate, extra, or unexpected runtime entries', async (t) => {
  assert.equal(typeof runtimeIntegrity.verifyPackagedWindowsRuntime, 'function');
  const stage = await createVerifiedStage(t);
  rewriteManifest(stage, (manifest) => { manifest.entries.push({ ...manifest.entries[0] }); });
  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime(stage.verifyOptions),
    (error) => error.reasonCode === 'entry_set_invalid'
  );
  rewriteManifest(stage, (manifest) => {
    manifest.entries[1].relativePath = 'resources/backend/other.exe';
  });
  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime(stage.verifyOptions),
    (error) => error.reasonCode === 'entry_path_mismatch'
  );
});

test('verifier rejects a renamed Desktop path even when its bytes match', async (t) => {
  assert.equal(typeof runtimeIntegrity.verifyPackagedWindowsRuntime, 'function');
  const stage = await createVerifiedStage(t);
  const renamedPath = path.join(stage.appOutDir, 'renamed-desktop.exe');
  fs.copyFileSync(stage.desktopPath, renamedPath);

  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime({
      ...stage.verifyOptions,
      exePath: renamedPath,
    }),
    (error) => error.reasonCode === 'desktop_path_mismatch'
  );
});

test('verifier rejects an unexpected backend path before hashing it', async (t) => {
  assert.equal(typeof runtimeIntegrity.verifyPackagedWindowsRuntime, 'function');
  const stage = await createVerifiedStage(t);
  const otherBackend = path.join(stage.appOutDir, 'other-backend.exe');
  fs.copyFileSync(stage.backendPath, otherBackend);

  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime({
      ...stage.verifyOptions,
      backendPath: otherBackend,
    }),
    (error) => error.reasonCode === 'backend_path_mismatch'
  );
});

test('verifier rejects changed file size and changed digest', async (t) => {
  assert.equal(typeof runtimeIntegrity.verifyPackagedWindowsRuntime, 'function');
  const stage = await createVerifiedStage(t);
  fs.appendFileSync(stage.backendPath, '-changed');
  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime(stage.verifyOptions),
    (error) => error.reasonCode === 'file_size_mismatch'
  );

  fs.writeFileSync(stage.backendPath, 'same-length-binary!!');
  rewriteManifest(stage, (manifest) => {
    const backend = manifest.entries.find((entry) => entry.role === 'backend');
    backend.size = Buffer.byteLength('same-length-binary!!');
    backend.sha256 = '0'.repeat(64);
  });
  assert.throws(
    () => runtimeIntegrity.verifyPackagedWindowsRuntime(stage.verifyOptions),
    (error) => error.reasonCode === 'file_digest_mismatch'
  );
});
