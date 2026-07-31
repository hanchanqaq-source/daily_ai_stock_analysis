const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { PRODUCT_ID, PRODUCT_NAME, PACKAGE_KIND, ARTIFACT_PREFIX, MANIFEST_NAME } = require('../apps/dsa-desktop/portable-update/portableIdentity');

function walk(root, current = '') { return fs.readdirSync(path.join(root, current), { withFileTypes: true }).flatMap((entry) => { const relative = path.posix.join(current.replace(/\\/g, '/'), entry.name); if (entry.isSymbolicLink()) throw new Error(`Links are forbidden: ${relative}`); return entry.isDirectory() ? walk(root, relative) : [relative]; }); }
function sha(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function includePortableSourcePath(source, candidate) {
  const relative = path.relative(source, candidate).replace(/\\/g, '/');
  if (!relative) return true;
  const rootEntry = relative.split('/')[0].toLowerCase();
  return !['.env', 'data', 'logs'].includes(rootEntry);
}
async function main() {
  const [mode, tag, source, target] = process.argv.slice(2); if (!/^v\d+\.\d+\.\d+$/.test(tag || '')) throw new Error('Release tag must be vX.Y.Z.'); const version = tag.slice(1);
  const pkg = require('../apps/dsa-desktop/package.json'); if (pkg.version !== version) throw new Error(`package.json version ${pkg.version} does not match ${tag}.`);
  if (mode === 'stage') { fs.rmSync(target, { recursive: true, force: true }); fs.cpSync(source, target, { recursive: true, filter: (file) => includePortableSourcePath(source, file) });
    const managedFiles = walk(target).filter((name) => name !== MANIFEST_NAME).sort().map((relativePath) => { const file = path.join(target, relativePath); return { relativePath, size: fs.statSync(file).size, sha256: sha(file) }; });
    const entryExecutable = 'PP02 AI Daily Stock Analysis.exe'; if (!managedFiles.some((f) => f.relativePath === entryExecutable)) throw new Error(`Missing ${entryExecutable}.`);
    fs.writeFileSync(path.join(target, MANIFEST_NAME), JSON.stringify({ schemaVersion: 1, productId: PRODUCT_ID, productName: PRODUCT_NAME, packageKind: PACKAGE_KIND, version, releaseTag: tag, artifactPrefix: ARTIFACT_PREFIX, entryExecutable, managedFiles }, null, 2)); return;
  }
  if (mode === 'verify') { const { extractAndVerify } = require('../apps/dsa-desktop/portable-update/portableArchive'); const expectedName = `${ARTIFACT_PREFIX}-${tag}.zip`; if (path.basename(source) !== expectedName) throw new Error('ZIP filename does not match release tag.'); const temp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'pp02-verify-')); try { await extractAndVerify(source, path.join(temp, 'payload'), { version, releaseTag: tag }); } finally { fs.rmSync(temp, { recursive: true, force: true }); } const digest = sha(source); fs.writeFileSync(target, `${digest}  ${expectedName}\n`); return; }
  throw new Error('Usage: stage|verify tag source target');
}
main().catch((error) => { console.error(error.message); process.exitCode = 1; });
