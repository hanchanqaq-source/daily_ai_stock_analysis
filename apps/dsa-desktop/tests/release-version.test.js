const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  compareStableVersions,
  parseStableVersion,
  verifyRepositoryVersion,
} = require('../../../scripts/verify-release-version');

function writeJson(root, relativePath, value) {
  const target = path.join(root, relativePath);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function createVersionFixture(version = '3.29.5') {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-release-version-'));
  fs.writeFileSync(path.join(root, 'VERSION'), `${version}\n`, 'utf8');
  for (const app of ['dsa-desktop', 'dsa-web']) {
    writeJson(root, `apps/${app}/package.json`, { version });
    writeJson(root, `apps/${app}/package-lock.json`, {
      version,
      packages: { '': { version } },
    });
  }
  const service = path.join(root, 'src/services/full_data_backup_service.py');
  fs.mkdirSync(path.dirname(service), { recursive: true });
  fs.writeFileSync(
    service,
    `DEFAULT_APPLICATION_VERSION = "${version}"\n`,
    'utf8',
  );
  return root;
}

test('stable version parsing rejects tags that are not canonical release SemVer', () => {
  assert.deepEqual(parseStableVersion('v3.29.5'), [3, 29, 5]);
  for (const invalid of ['3.29.5', 'v03.29.5', 'v3.29', 'v3.29.5-rc.1', 'latest']) {
    assert.throws(() => parseStableVersion(invalid), /stable vX\.Y\.Z/);
  }
  assert.equal(compareStableVersions('v3.29.5', 'v3.29.4'), 1);
  assert.equal(compareStableVersions('v3.29.5', 'v3.29.5'), 0);
  assert.equal(compareStableVersions('v3.28.99', 'v3.29.0'), -1);
});

test('candidate verification binds every checked-in version surface and exceeds the latest tag', (t) => {
  const root = createVersionFixture();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));

  const result = verifyRepositoryVersion({
    root,
    mode: 'candidate',
    stableTags: ['v3.29.3', 'v3.29.4'],
  });

  assert.equal(result.version, '3.29.5');
  assert.equal(result.latestStableTag, 'v3.29.4');
  assert.equal(result.mode, 'candidate');
});

test('candidate verification fails when source equals or trails the latest release', (t) => {
  const equalRoot = createVersionFixture('3.29.4');
  const staleRoot = createVersionFixture('3.29.3');
  t.after(() => fs.rmSync(equalRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(staleRoot, { recursive: true, force: true }));

  assert.throws(
    () => verifyRepositoryVersion({ root: equalRoot, mode: 'candidate', stableTags: ['v3.29.4'] }),
    /must be newer than latest stable tag v3\.29\.4/,
  );
  assert.throws(
    () => verifyRepositoryVersion({ root: staleRoot, mode: 'candidate', stableTags: ['v3.29.4'] }),
    /must be newer than latest stable tag v3\.29\.4/,
  );
});

test('candidate verification ignores only its exact source tag when that tag points at HEAD', (t) => {
  const root = createVersionFixture();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));

  const result = verifyRepositoryVersion({
    root,
    mode: 'candidate',
    stableTags: ['v3.29.4', 'v3.29.5'],
    headTags: ['v3.29.5'],
  });
  assert.equal(result.latestStableTag, 'v3.29.4');
  assert.throws(
    () => verifyRepositoryVersion({
      root,
      mode: 'candidate',
      stableTags: ['v3.29.4', 'v3.30.0'],
      headTags: ['v3.30.0'],
    }),
    /does not match source tag v3\.29\.5/,
  );
});

test('release verification requires the requested tag to equal checked-in VERSION', (t) => {
  const root = createVersionFixture();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));

  assert.equal(
    verifyRepositoryVersion({ root, mode: 'release', releaseTag: 'v3.29.5' }).releaseTag,
    'v3.29.5',
  );
  assert.throws(
    () => verifyRepositoryVersion({ root, mode: 'release', releaseTag: 'v3.29.6' }),
    /does not match source version v3\.29\.5/,
  );
});

test('auto-tag verification requires VERSION to be the requested successor', (t) => {
  const root = createVersionFixture();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));

  assert.equal(
    verifyRepositoryVersion({
      root,
      mode: 'auto-tag',
      bump: 'patch',
      stableTags: ['v3.29.4'],
    }).releaseTag,
    'v3.29.5',
  );
  assert.throws(
    () => verifyRepositoryVersion({
      root,
      mode: 'auto-tag',
      bump: 'minor',
      stableTags: ['v3.29.4'],
    }),
    /expected minor successor v3\.30\.0/,
  );
});

test('version verification fails when any package or backup surface drifts', (t) => {
  const root = createVersionFixture();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const desktop = path.join(root, 'apps/dsa-desktop/package.json');
  writeJson(root, 'apps/dsa-desktop/package.json', { version: '3.29.4' });

  assert.throws(
    () => verifyRepositoryVersion({ root, mode: 'release', releaseTag: 'v3.29.5' }),
    new RegExp(`${desktop.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}.*3\\.29\\.4.*3\\.29\\.5`),
  );
});
