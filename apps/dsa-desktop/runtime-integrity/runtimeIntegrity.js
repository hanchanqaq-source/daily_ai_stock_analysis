const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const PP02_PRODUCT_ID = 'com.hanchanqaq.pp02.aidailystockanalysis';
const PP02_RUNTIME_INTEGRITY_MANIFEST = 'pp02-runtime-integrity.json';
const RUNTIME_INTEGRITY_SCHEMA_VERSION = 1;
const RUNTIME_INTEGRITY_PUBLIC_MESSAGE =
  '程序文件或启动参数校验失败，后端未启动，也没有启动任何分析任务。请从官方 Release 重新安装后再试。';
const EXPECTED_RUNTIME_ENTRIES = Object.freeze([
  Object.freeze({
    role: 'desktop',
    relativePath: 'PP02 AI Daily Stock Analysis.exe',
  }),
  Object.freeze({
    role: 'backend',
    relativePath: 'resources/backend/stock_analysis/stock_analysis.exe',
  }),
]);

class RuntimeIntegrityError extends Error {
  constructor(reasonCode) {
    super(RUNTIME_INTEGRITY_PUBLIC_MESSAGE);
    this.name = 'RuntimeIntegrityError';
    this.reasonCode = String(reasonCode || 'unknown').slice(0, 80);
  }
}

function normalizeRelativePath(relativePath) {
  return String(relativePath || '').replace(/\\/g, '/');
}

function isPathInside(rootPath, candidatePath) {
  const relative = path.relative(rootPath, candidatePath);
  return Boolean(relative) && !relative.startsWith('..') && !path.isAbsolute(relative);
}

function samePath(leftPath, rightPath, platform) {
  const left = path.resolve(String(leftPath || ''));
  const right = path.resolve(String(rightPath || ''));
  return platform === 'win32'
    ? left.toLowerCase() === right.toLowerCase()
    : left === right;
}

function hasExactKeys(value, expectedKeys) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return false;
  }
  const actual = Object.keys(value).sort();
  const expected = [...expectedKeys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function failIntegrity(reasonCode) {
  throw new RuntimeIntegrityError(reasonCode);
}

function resolveRequiredRuntimeFile(appOutDir, entry) {
  const normalizedRoot = path.resolve(appOutDir);
  const resolvedPath = path.resolve(
    normalizedRoot,
    ...entry.relativePath.split('/')
  );
  if (!isPathInside(normalizedRoot, resolvedPath)) {
    throw new Error(`required runtime file resolves outside package root: ${entry.role}`);
  }
  if (!fs.existsSync(resolvedPath)) {
    throw new Error(`required runtime file is missing: ${entry.role}`);
  }
  const stats = fs.lstatSync(resolvedPath);
  const realRoot = fs.realpathSync(normalizedRoot);
  const realFile = fs.realpathSync(resolvedPath);
  if (
    !stats.isFile()
    || stats.isSymbolicLink()
    || !isPathInside(realRoot, realFile)
  ) {
    throw new Error(`required runtime path is not a regular in-package file: ${entry.role}`);
  }
  return { resolvedPath, stats };
}

function sha256FileSync(filePath) {
  const digest = crypto.createHash('sha256');
  const buffer = Buffer.allocUnsafe(1024 * 1024);
  const fd = fs.openSync(filePath, 'r');
  try {
    let bytesRead = 0;
    do {
      bytesRead = fs.readSync(fd, buffer, 0, buffer.length, null);
      if (bytesRead > 0) {
        digest.update(buffer.subarray(0, bytesRead));
      }
    } while (bytesRead > 0);
  } finally {
    fs.closeSync(fd);
  }
  return digest.digest('hex');
}

function writeWindowsRuntimeIntegrityManifest({ appOutDir, platform, version }) {
  if (platform !== 'win32') {
    return { skipped: true };
  }
  const normalizedVersion = String(version || '').trim();
  if (!normalizedVersion) {
    throw new Error('package version is required for runtime integrity manifest');
  }

  const entries = EXPECTED_RUNTIME_ENTRIES.map((entry) => {
    const { resolvedPath, stats } = resolveRequiredRuntimeFile(appOutDir, entry);
    return {
      role: entry.role,
      relativePath: normalizeRelativePath(entry.relativePath),
      size: stats.size,
      sha256: sha256FileSync(resolvedPath),
    };
  });
  const manifest = {
    schemaVersion: RUNTIME_INTEGRITY_SCHEMA_VERSION,
    productId: PP02_PRODUCT_ID,
    version: normalizedVersion,
    entries,
  };
  const manifestPath = path.join(
    path.resolve(appOutDir),
    'resources',
    PP02_RUNTIME_INTEGRITY_MANIFEST
  );
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  return { manifestPath, manifest };
}

function verifyPackagedWindowsRuntime({
  platform,
  packaged,
  appRoot,
  resourcesPath,
  exePath,
  backendPath,
  version,
} = {}) {
  if (platform !== 'win32' || packaged !== true) {
    return { skipped: true };
  }

  const normalizedRoot = path.resolve(String(appRoot || ''));
  const expectedResourcesPath = path.join(normalizedRoot, 'resources');
  if (!samePath(resourcesPath, expectedResourcesPath, platform)) {
    failIntegrity('resources_path_mismatch');
  }
  const manifestPath = path.join(
    expectedResourcesPath,
    PP02_RUNTIME_INTEGRITY_MANIFEST
  );
  if (!fs.existsSync(manifestPath)) {
    failIntegrity('manifest_missing');
  }

  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  } catch (_error) {
    failIntegrity('manifest_malformed');
  }
  if (!hasExactKeys(manifest, ['schemaVersion', 'productId', 'version', 'entries'])) {
    failIntegrity('manifest_malformed');
  }
  if (manifest.schemaVersion !== RUNTIME_INTEGRITY_SCHEMA_VERSION) {
    failIntegrity('schema_mismatch');
  }
  if (manifest.productId !== PP02_PRODUCT_ID) {
    failIntegrity('product_mismatch');
  }
  if (manifest.version !== String(version || '').trim()) {
    failIntegrity('version_mismatch');
  }
  if (!Array.isArray(manifest.entries) || manifest.entries.length !== EXPECTED_RUNTIME_ENTRIES.length) {
    failIntegrity('entry_set_invalid');
  }

  const expectedByRole = new Map(EXPECTED_RUNTIME_ENTRIES.map((entry) => [entry.role, entry]));
  const entriesByRole = new Map();
  for (const entry of manifest.entries) {
    if (!hasExactKeys(entry, ['role', 'relativePath', 'size', 'sha256'])) {
      failIntegrity('entry_malformed');
    }
    if (!expectedByRole.has(entry.role) || entriesByRole.has(entry.role)) {
      failIntegrity('entry_set_invalid');
    }
    if (!Number.isSafeInteger(entry.size) || entry.size < 0 || !/^[a-f0-9]{64}$/.test(entry.sha256)) {
      failIntegrity('entry_malformed');
    }
    const expected = expectedByRole.get(entry.role);
    if (normalizeRelativePath(entry.relativePath) !== expected.relativePath) {
      failIntegrity('entry_path_mismatch');
    }
    entriesByRole.set(entry.role, entry);
  }

  const expectedDesktopPath = path.resolve(
    normalizedRoot,
    ...EXPECTED_RUNTIME_ENTRIES[0].relativePath.split('/')
  );
  const expectedBackendPath = path.resolve(
    normalizedRoot,
    ...EXPECTED_RUNTIME_ENTRIES[1].relativePath.split('/')
  );
  if (!samePath(exePath, expectedDesktopPath, platform)) {
    failIntegrity('desktop_path_mismatch');
  }
  if (!samePath(backendPath, expectedBackendPath, platform)) {
    failIntegrity('backend_path_mismatch');
  }

  const realRoot = fs.realpathSync(normalizedRoot);
  for (const expected of EXPECTED_RUNTIME_ENTRIES) {
    const entry = entriesByRole.get(expected.role);
    const absolutePath = path.resolve(normalizedRoot, ...expected.relativePath.split('/'));
    if (!isPathInside(normalizedRoot, absolutePath) || !fs.existsSync(absolutePath)) {
      failIntegrity('file_missing');
    }
    const linkStats = fs.lstatSync(absolutePath);
    if (!linkStats.isFile() || linkStats.isSymbolicLink()) {
      failIntegrity('file_type_invalid');
    }
    const realFile = fs.realpathSync(absolutePath);
    if (!isPathInside(realRoot, realFile)) {
      failIntegrity('file_outside_root');
    }
    if (linkStats.size !== entry.size) {
      failIntegrity('file_size_mismatch');
    }
    if (sha256FileSync(absolutePath) !== entry.sha256) {
      failIntegrity('file_digest_mismatch');
    }
  }

  return {
    verified: true,
    manifestPath,
    roles: EXPECTED_RUNTIME_ENTRIES.map((entry) => entry.role),
  };
}

module.exports = {
  EXPECTED_RUNTIME_ENTRIES,
  PP02_PRODUCT_ID,
  PP02_RUNTIME_INTEGRITY_MANIFEST,
  RUNTIME_INTEGRITY_SCHEMA_VERSION,
  RUNTIME_INTEGRITY_PUBLIC_MESSAGE,
  RuntimeIntegrityError,
  sha256FileSync,
  verifyPackagedWindowsRuntime,
  writeWindowsRuntimeIntegrityManifest,
};
