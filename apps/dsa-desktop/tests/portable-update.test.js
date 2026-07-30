const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { EventEmitter } = require('events');
const { Readable } = require('stream');
const archiver = require('archiver');
const { detectWindowsRuntime, PRODUCT_ID, PRODUCT_NAME, PACKAGE_KIND, ARTIFACT_PREFIX } = require('../portable-update/portableIdentity');
const { selectPortableAssets, parseBoundSha256 } = require('../portable-update/portableRelease');
const { extractAndVerify, normalizeEntryName, validateManifest } = require('../portable-update/portableArchive');
const { downloadHttps } = require('../portable-update/portableDownload');
const { buildUpdatePlan } = require('../portable-update/portablePlan');
const { backupRuntimeState, copyHelperToTemp, restoreRuntimeState } = require('../portable-update/portableTransaction');

function validManifest(version = '3.22.0') {
  const files = { 'PP02 AI Daily Stock Analysis.exe': 'exe', 'resources/app.asar': 'asar' };
  return { manifest: { schemaVersion: 1, productId: PRODUCT_ID, productName: PRODUCT_NAME, packageKind: PACKAGE_KIND, version, releaseTag: `v${version}`, artifactPrefix: ARTIFACT_PREFIX, entryExecutable: 'PP02 AI Daily Stock Analysis.exe', managedFiles: Object.entries(files).map(([relativePath, value]) => ({ relativePath, size: Buffer.byteLength(value), sha256: crypto.createHash('sha256').update(value).digest('hex') })) }, files };
}

function writeRuntime(root, manifest = validManifest().manifest) {
  fs.mkdirSync(path.join(root, 'resources', 'backend', 'stock_analysis'), { recursive: true });
  fs.writeFileSync(path.join(root, 'PP02 AI Daily Stock Analysis.exe'), 'exe');
  fs.writeFileSync(path.join(root, 'resources', 'app.asar'), 'asar');
  if (manifest) fs.writeFileSync(path.join(root, 'pp02-portable-release.json'), JSON.stringify(manifest));
}

test('portable and NSIS runtime recognition are mutually exclusive and ambiguity is rejected', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-runtime-'));
  writeRuntime(root);
  assert.deepEqual(detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root }).runtimeKind, 'windows-portable');
  fs.writeFileSync(path.join(root, 'Uninstall PP02 AI Daily Stock Analysis.exe'), '');
  assert.equal(detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root }).runtimeKind, 'ambiguous');
  fs.rmSync(path.join(root, 'pp02-portable-release.json'));
  assert.equal(detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root }).runtimeKind, 'windows-nsis');
});

test('current manifest identity and strict legacy portable structure are required', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-identity-'));
  writeRuntime(root);
  const detected = detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root, exePath: path.join(root, 'PP02 AI Daily Stock Analysis.exe') });
  assert.equal(detected.runtimeKind, 'windows-portable'); assert.equal(detected.manifest.productId, PRODUCT_ID);
  assert.equal(detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root, exePath: path.join(root, 'PP02 AI Daily Stock Analysis.exe'), version: '9.9.9' }).runtimeKind, 'ambiguous');
  fs.rmSync(path.join(root, 'pp02-portable-release.json'));
  assert.equal(detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root, exePath: path.join(root, 'PP02 AI Daily Stock Analysis.exe') }).runtimeKind, 'windows-portable-legacy');
  fs.rmSync(path.join(root, 'resources', 'backend'), { recursive: true });
  assert.equal(detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root, exePath: path.join(root, 'PP02 AI Daily Stock Analysis.exe') }).runtimeKind, 'ambiguous');
});

test('download follows one allowed GitHub 302 and writes the final response', async () => {
  const target = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-download-')), 'asset.zip'); let calls = 0;
  const request = (_url, _options, callback) => { const req = new EventEmitter(); req.destroyed = false; req.destroy = () => { req.destroyed = true; }; req.setTimeout = () => {}; process.nextTick(() => { calls += 1; const response = calls === 1 ? Readable.from([]) : Readable.from([Buffer.from('payload')]); response.statusCode = calls === 1 ? 302 : 200; response.headers = calls === 1 ? { location: 'https://release-assets.githubusercontent.com/asset' } : { 'content-length': '7' }; response.setTimeout = () => {}; callback(response); }); return req; };
  assert.deepEqual(await downloadHttps('https://github.com/release', target, { request }), { bytes: 7, redirects: 1 }); assert.equal(fs.readFileSync(target, 'utf8'), 'payload');
});

test('download timeout and interruption remove partial files', async () => {
  for (const event of ['timeout', 'aborted']) { const target = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-download-fail-')), 'asset.zip'); let timeout;
    const request = (_url, _options, callback) => { const req = new EventEmitter(); req.destroyed = false; req.destroy = () => { req.destroyed = true; }; req.setTimeout = (_ms, fn) => { timeout = fn; }; process.nextTick(() => { if (event === 'timeout') timeout(); else { const response = new Readable({ read() {} }); response.statusCode = 200; response.headers = {}; response.setTimeout = () => {}; callback(response); response.push('partial'); response.emit('aborted'); } }); return req; };
    await assert.rejects(downloadHttps('https://github.com/release', target, { request }), /timeout|interrupted/); assert.equal(fs.existsSync(target), false);
  }
});

test('real ZIP extraction verifies manifest and file digests', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-real-zip-')); const zip = path.join(root, 'release.zip'); const stage = path.join(root, 'stage'); const { manifest, files } = validManifest();
  await new Promise((resolve, reject) => { const output = fs.createWriteStream(zip); const archive = archiver('zip'); output.on('close', resolve); archive.on('error', reject); archive.pipe(output); for (const [name, value] of Object.entries(files)) archive.append(value, { name }); archive.append(JSON.stringify(manifest), { name: 'pp02-portable-release.json' }); archive.finalize(); });
  const result = await extractAndVerify(zip, stage, { version: '3.22.0', releaseTag: 'v3.22.0' }); assert.equal(result.productId, PRODUCT_ID); assert.equal(fs.readFileSync(path.join(stage, 'resources', 'app.asar'), 'utf8'), 'asar');
});

test('helper is copied outside app resources and runtime existence is restored transactionally', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-transaction-')); const backup = path.join(root, '.backup'); const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-helper-')); fs.mkdirSync(path.join(root, 'data'), { recursive: true }); fs.writeFileSync(path.join(root, '.env'), 'old'); fs.writeFileSync(path.join(root, 'data', 'stock_analysis.db'), 'db');
  const helper = copyHelperToTemp(path.join(__dirname, '..', 'portable-update', 'portable-update-helper.ps1'), temp); assert.equal(path.dirname(helper), temp);
  const state = backupRuntimeState(root, backup, 'pp02-portable-release.json'); fs.writeFileSync(path.join(root, '.env'), 'new'); fs.writeFileSync(path.join(root, 'data', 'stock_analysis.db-wal'), 'new-wal'); fs.writeFileSync(path.join(root, 'data', 'stock_analysis.db-shm'), 'new-shm');
  const restored = restoreRuntimeState(root, backup, state.metadataPath); assert.equal(fs.readFileSync(path.join(root, '.env'), 'utf8'), 'old'); assert.ok(restored.removed.includes('data/stock_analysis.db-wal')); assert.equal(fs.existsSync(path.join(root, 'data', 'stock_analysis.db-wal')), false); assert.equal(fs.existsSync(path.join(root, 'data', 'stock_analysis.db-shm')), false);
});

test('release assets require one exact ZIP and bound SHA file', () => {
  const version = '3.22.0'; const zipName = `${ARTIFACT_PREFIX}-v${version}.zip`;
  const asset = (name) => ({ name, browser_download_url: `https://github.com/hanchanqaq-source/daily_ai_stock_analysis/releases/download/v${version}/${name}` });
  const pair = selectPortableAssets({ tag_name: `v${version}`, assets: [asset(zipName), asset(`${zipName}.sha256`)] }, version);
  assert.equal(pair.zipName, zipName);
  assert.equal(parseBoundSha256(`${'a'.repeat(64)}  ${zipName}\n`, zipName), 'a'.repeat(64));
  assert.throws(() => parseBoundSha256(`${'a'.repeat(64)}  wrong.zip`, zipName), /not bound/);
  assert.throws(() => selectPortableAssets({ tag_name: `v${version}`, assets: [asset(zipName)] }, version), /exact/);
});

test('ZIP path policy rejects traversal, absolute, ADS, devices, trailing dot and duplicates after normalization', () => {
  for (const unsafe of ['../evil', '/evil', 'C:/evil', '\\\\server\\evil', 'safe/../evil', 'safe/file:stream', 'NUL.txt', 'safe/name.']) assert.throws(() => normalizeEntryName(unsafe));
  assert.equal(normalizeEntryName('resources/app.asar'), 'resources/app.asar');
});

test('manifest enforces PP02 identity, managed file digests, and protected paths', () => {
  const valid = { schemaVersion: 1, productId: PRODUCT_ID, productName: PRODUCT_NAME, packageKind: PACKAGE_KIND, version: '3.22.0', releaseTag: 'v3.22.0', artifactPrefix: ARTIFACT_PREFIX, entryExecutable: 'PP02 AI Daily Stock Analysis.exe', managedFiles: [{ relativePath: 'app.exe', size: 1, sha256: crypto.createHash('sha256').update('x').digest('hex') }] };
  assert.equal(validateManifest(valid, { version: '3.22.0', releaseTag: 'v3.22.0' }), valid);
  assert.throws(() => validateManifest({ ...valid, productId: 'other' }, { version: '3.22.0', releaseTag: 'v3.22.0' }), /identity/);
  assert.throws(() => validateManifest({ ...valid, managedFiles: [{ ...valid.managedFiles[0], relativePath: '.env' }] }, { version: '3.22.0', releaseTag: 'v3.22.0' }), /Invalid managed/);
});

test('first update without old manifest never guesses deletions; later updates remove only old managed files', () => {
  const nextManifest = { managedFiles: [{ relativePath: 'new.exe' }] };
  const base = { currentRoot: 'C:/PP02', stagedRoot: 'C:/stage', backupRoot: 'C:/backup', nextManifest, version: '3.22.0', backendUrl: 'http://127.0.0.1/api/health', homeUrl: 'http://127.0.0.1/' };
  assert.deepEqual(buildUpdatePlan({ ...base, currentManifest: null }).remove, []);
  assert.deepEqual(buildUpdatePlan({ ...base, currentManifest: { managedFiles: [{ relativePath: 'old.exe' }] } }).remove, ['old.exe']);
});
