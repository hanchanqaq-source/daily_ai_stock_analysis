const fs = require('fs');
const path = require('path');

const PRODUCT_ID = 'com.hanchanqaq.pp02.aidailystockanalysis';
const PRODUCT_NAME = 'PP02 AI Daily Stock Analysis';
const PACKAGE_KIND = 'windows-portable';
const MANIFEST_NAME = 'pp02-portable-release.json';
const ARTIFACT_PREFIX = 'pp02-ai-daily-stock-analysis-windows-noinstall';

function detectWindowsRuntime({ platform = process.platform, packaged = false, exePath = '', appDir = '' } = {}) {
  if (platform !== 'win32' || !packaged) return { runtimeKind: 'unsupported', portableEligible: false };
  const root = path.resolve(appDir || path.dirname(exePath));
  const hasManifest = fs.existsSync(path.join(root, MANIFEST_NAME));
  const uninstallers = fs.existsSync(path.join(root, 'Uninstall PP02 AI Daily Stock Analysis.exe'))
    || fs.existsSync(path.join(root, 'Uninstall Daily Stock Analysis.exe'));
  if (hasManifest && !uninstallers) return { runtimeKind: 'windows-portable', portableEligible: true, root };
  if (!hasManifest && uninstallers) return { runtimeKind: 'windows-nsis', portableEligible: false, root };
  return { runtimeKind: 'ambiguous', portableEligible: false, root };
}

module.exports = { ARTIFACT_PREFIX, MANIFEST_NAME, PACKAGE_KIND, PRODUCT_ID, PRODUCT_NAME, detectWindowsRuntime };
