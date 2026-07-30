const fs = require('fs');
const path = require('path');

const RUNTIME_FILES = ['.env', 'data/stock_analysis.db', 'data/stock_analysis.db-wal', 'data/stock_analysis.db-shm'];

function copyHelperToTemp(source, tempRoot) {
  const target = path.join(tempRoot, 'portable-update-helper.ps1');
  fs.copyFileSync(source, target, fs.constants.COPYFILE_EXCL);
  return target;
}

function backupRuntimeState(root, backupRoot, manifestName) {
  const paths = [...RUNTIME_FILES, manifestName];
  const state = {};
  for (const relative of paths) {
    const source = path.join(root, relative);
    const existed = fs.existsSync(source);
    state[relative] = { existed };
    if (!existed) continue;
    const target = path.join(backupRoot, 'runtime', relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(source, target, fs.constants.COPYFILE_EXCL);
  }
  const metadataPath = path.join(backupRoot, 'runtime-state.json');
  fs.writeFileSync(metadataPath, JSON.stringify({ schemaVersion: 1, paths: state }, null, 2), { encoding: 'utf8', flag: 'wx', mode: 0o600 });
  return { metadataPath, paths: state };
}

function restoreRuntimeState(root, backupRoot, metadataPath) {
  const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
  const restored = []; const removed = [];
  for (const [relative, record] of Object.entries(metadata.paths)) {
    const target = path.join(root, relative); const saved = path.join(backupRoot, 'runtime', relative);
    if (record.existed) { fs.mkdirSync(path.dirname(target), { recursive: true }); fs.copyFileSync(saved, target); restored.push(relative); }
    else { fs.rmSync(target, { recursive: true, force: true }); removed.push(relative); }
  }
  return { restored, removed };
}

module.exports = { RUNTIME_FILES, backupRuntimeState, copyHelperToTemp, restoreRuntimeState };
