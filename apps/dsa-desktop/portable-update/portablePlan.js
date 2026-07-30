const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { MANIFEST_NAME, PRODUCT_ID } = require('./portableIdentity');

function buildUpdatePlan({ currentRoot, stagedRoot, backupRoot, currentManifest, nextManifest, version, backendUrl, homeUrl }) {
  const next = new Set(nextManifest.managedFiles.map((file) => file.relativePath.toLowerCase()));
  const remove = currentManifest ? currentManifest.managedFiles.map((f) => f.relativePath).filter((name) => !next.has(name.toLowerCase())) : [];
  return { schemaVersion: 1, productId: PRODUCT_ID, token: crypto.randomBytes(32).toString('hex'), currentRoot: path.resolve(currentRoot), stagedRoot: path.resolve(stagedRoot), backupRoot: path.resolve(backupRoot), readySignal: path.resolve(backupRoot, 'new-version-ready.json'), targetVersion: version, manifestName: MANIFEST_NAME, replace: nextManifest.managedFiles.map((f) => f.relativePath), remove, protected: ['.env', 'data', 'logs'], health: { backendUrl, homeUrl } };
}
function writeUpdatePlan(file, plan) { fs.writeFileSync(file, JSON.stringify(plan, null, 2), { encoding: 'utf8', flag: 'wx', mode: 0o600 }); }
module.exports = { buildUpdatePlan, writeUpdatePlan };
