const fs = require('fs');
const path = require('path');

const PRODUCT_ID = 'com.hanchanqaq.pp02.aidailystockanalysis';
const PRODUCT_NAME = 'PP02 AI Daily Stock Analysis';
const PACKAGE_KIND = 'windows-portable';
const MANIFEST_NAME = 'pp02-portable-release.json';
const ARTIFACT_PREFIX = 'pp02-ai-daily-stock-analysis-windows-noinstall';
const ENTRY_EXECUTABLE = `${PRODUCT_NAME}.exe`;

function readCurrentManifest(root, exePath, version = '') {
  const manifestPath = path.join(root, MANIFEST_NAME);
  let manifest;
  try { manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8')); } catch (_) { return null; }
  const entry = typeof manifest.entryExecutable === 'string' ? manifest.entryExecutable : '';
  const managed = Array.isArray(manifest.managedFiles) ? manifest.managedFiles : [];
  const valid = manifest.schemaVersion === 1
    && manifest.productId === PRODUCT_ID
    && manifest.productName === PRODUCT_NAME
    && manifest.packageKind === PACKAGE_KIND
    && /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(manifest.version || '')
    && (!version || manifest.version === String(version).replace(/^v/i, ''))
    && manifest.releaseTag === `v${manifest.version}`
    && manifest.artifactPrefix === ARTIFACT_PREFIX
    && entry === ENTRY_EXECUTABLE
    && path.basename(exePath).toLowerCase() === ENTRY_EXECUTABLE.toLowerCase()
    && fs.existsSync(path.join(root, entry))
    && fs.existsSync(path.join(root, 'resources', 'app.asar'))
    && managed.some((file) => file && file.relativePath === entry)
    && managed.some((file) => file && file.relativePath === 'resources/app.asar');
  return valid ? manifest : null;
}

function isStrictLegacyPortable(root, exePath) {
  return path.basename(exePath).toLowerCase() === ENTRY_EXECUTABLE.toLowerCase()
    && fs.existsSync(path.join(root, ENTRY_EXECUTABLE))
    && fs.existsSync(path.join(root, 'resources', 'app.asar'))
    && fs.existsSync(path.join(root, 'resources', 'backend', 'stock_analysis'))
    && !fs.existsSync(path.join(root, MANIFEST_NAME));
}

function detectWindowsRuntime({ platform = process.platform, packaged = false, exePath = '', appDir = '', version = '' } = {}) {
  if (platform !== 'win32' || !packaged) return { runtimeKind: 'unsupported', portableEligible: false };
  const root = path.resolve(appDir || path.dirname(exePath));
  const resolvedExe = path.resolve(exePath || path.join(root, ENTRY_EXECUTABLE));
  const uninstallers = fs.existsSync(path.join(root, 'Uninstall PP02 AI Daily Stock Analysis.exe'))
    || fs.existsSync(path.join(root, 'Uninstall Daily Stock Analysis.exe'));
  const manifest = readCurrentManifest(root, resolvedExe, version);
  if (manifest && !uninstallers) return { runtimeKind: 'windows-portable', portableEligible: true, root, manifest, legacy: false };
  if (!fs.existsSync(path.join(root, MANIFEST_NAME)) && !uninstallers && isStrictLegacyPortable(root, resolvedExe)) return { runtimeKind: 'windows-portable-legacy', portableEligible: true, root, manifest: null, legacy: true };
  if (!fs.existsSync(path.join(root, MANIFEST_NAME)) && uninstallers) return { runtimeKind: 'windows-nsis', portableEligible: false, root };
  return { runtimeKind: 'ambiguous', portableEligible: false, root };
}

module.exports = { ARTIFACT_PREFIX, ENTRY_EXECUTABLE, MANIFEST_NAME, PACKAGE_KIND, PRODUCT_ID, PRODUCT_NAME, detectWindowsRuntime, readCurrentManifest };
