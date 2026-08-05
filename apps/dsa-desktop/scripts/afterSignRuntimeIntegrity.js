const {
  writeWindowsRuntimeIntegrityManifest,
} = require('../runtime-integrity/runtimeIntegrity');

async function afterSign(context) {
  return writeWindowsRuntimeIntegrityManifest({
    appOutDir: context.appOutDir,
    platform: context.electronPlatformName,
    version: context.packager.appInfo.version,
  });
}

module.exports = afterSign;
module.exports.afterSign = afterSign;
