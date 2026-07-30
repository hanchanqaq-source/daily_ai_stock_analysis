const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { detectWindowsRuntime, PRODUCT_ID, PRODUCT_NAME, PACKAGE_KIND, ARTIFACT_PREFIX } = require('../portable-update/portableIdentity');
const { selectPortableAssets, parseBoundSha256 } = require('../portable-update/portableRelease');
const { normalizeEntryName, validateManifest } = require('../portable-update/portableArchive');
const { buildUpdatePlan } = require('../portable-update/portablePlan');

test('portable and NSIS runtime recognition are mutually exclusive and ambiguity is rejected', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-runtime-'));
  fs.writeFileSync(path.join(root, 'pp02-portable-release.json'), '{}');
  assert.deepEqual(detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root }).runtimeKind, 'windows-portable');
  fs.writeFileSync(path.join(root, 'Uninstall PP02 AI Daily Stock Analysis.exe'), '');
  assert.equal(detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root }).runtimeKind, 'ambiguous');
  fs.rmSync(path.join(root, 'pp02-portable-release.json'));
  assert.equal(detectWindowsRuntime({ platform: 'win32', packaged: true, appDir: root }).runtimeKind, 'windows-nsis');
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

test('PowerShell helper uses fixed hidden process contract without dynamic evaluation', () => {
  const text = fs.readFileSync(path.join(__dirname, '..', 'portable-update', 'portable-update-helper.ps1'), 'utf8');
  assert.doesNotMatch(text, /Invoke-Expression|cmd\s+\/c/i);
  assert.match(text, /Start-Process[\s\S]*-WindowStyle Hidden/);
});
