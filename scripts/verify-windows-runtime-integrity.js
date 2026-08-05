const path = require('node:path');

const {
  RuntimeIntegrityError,
  verifyPackagedWindowsRuntime,
} = require('../apps/dsa-desktop/runtime-integrity/runtimeIntegrity');

function main(argv = process.argv.slice(2)) {
  const [appRootValue, versionValue] = argv;
  if (!appRootValue || !versionValue) {
    throw new Error(
      'Usage: node scripts/verify-windows-runtime-integrity.js <app-root> <version>'
    );
  }
  const appRoot = path.resolve(appRootValue);
  const result = verifyPackagedWindowsRuntime({
    platform: 'win32',
    packaged: true,
    appRoot,
    resourcesPath: path.join(appRoot, 'resources'),
    exePath: path.join(appRoot, 'PP02 AI Daily Stock Analysis.exe'),
    backendPath: path.join(
      appRoot,
      'resources',
      'backend',
      'stock_analysis',
      'stock_analysis.exe'
    ),
    version: String(versionValue).trim(),
  });
  console.log(
    `OK: Windows runtime integrity verified roles=${result.roles.join(',')}`
  );
  return result;
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    const reason = error instanceof RuntimeIntegrityError
      ? error.reasonCode
      : 'verification_error';
    console.error(`ERROR: Windows runtime integrity failed reason=${reason}`);
    process.exitCode = 1;
  }
}

module.exports = { main };
