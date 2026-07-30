const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const yauzl = require('yauzl');
const { MANIFEST_NAME, PACKAGE_KIND, PRODUCT_ID, ARTIFACT_PREFIX } = require('./portableIdentity');

const PROTECTED = /^(?:\.env|data(?:\/|$)|logs(?:\/|$)|\.pp02-update-backup(?:\/|$))/i;
const DEVICE = /^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i;
function normalizeEntryName(raw) {
  if (typeof raw !== 'string' || !raw || raw.includes('\0')) throw new Error('Invalid ZIP entry name.');
  const value = raw.replace(/\\/g, '/');
  if (/^(?:\/|[a-zA-Z]:|\/\/)/.test(value)) throw new Error('Absolute ZIP paths are forbidden.');
  const parts = value.split('/').filter(Boolean);
  if (!parts.length || parts.some((part) => part === '..' || part.includes(':') || /[ .]$/.test(part) || DEVICE.test(part))) throw new Error(`Unsafe ZIP path: ${raw}`);
  return parts.join('/');
}
function validateManifest(manifest, { version, releaseTag } = {}) {
  if (!manifest || manifest.schemaVersion !== 1 || manifest.productId !== PRODUCT_ID || manifest.packageKind !== PACKAGE_KIND
    || manifest.version !== version || manifest.releaseTag !== releaseTag || manifest.artifactPrefix !== ARTIFACT_PREFIX) throw new Error('Portable release manifest identity does not match the update.');
  if (!Array.isArray(manifest.managedFiles) || !manifest.entryExecutable) throw new Error('Portable release manifest is incomplete.');
  const seen = new Set();
  for (const file of manifest.managedFiles) {
    const name = normalizeEntryName(file.relativePath);
    const key = name.toLowerCase();
    if (PROTECTED.test(name) || seen.has(key) || !Number.isSafeInteger(file.size) || file.size < 0 || !/^[a-f0-9]{64}$/i.test(file.sha256)) throw new Error(`Invalid managed file: ${name}`);
    seen.add(key);
  }
  return manifest;
}
function openZip(file) { return new Promise((resolve, reject) => yauzl.open(file, { lazyEntries: true, decodeStrings: true, validateEntrySizes: true }, (e, zip) => e ? reject(e) : resolve(zip))); }
async function extractAndVerify(zipFile, destination, identity, limits = {}) {
  const maxEntries = limits.maxEntries || 20000; const maxBytes = limits.maxBytes || 4 * 1024 ** 3; const maxRatio = limits.maxRatio || 200;
  const zip = await openZip(zipFile); const entries = []; const names = new Map(); let expanded = 0;
  await new Promise((resolve, reject) => { zip.on('error', reject); zip.on('end', resolve); zip.on('entry', (entry) => {
    try { const name = normalizeEntryName(entry.fileName); const key = name.toLowerCase(); const isDirectory = /[\\/]$/.test(entry.fileName); const parents = key.split('/').slice(0, -1).map((_part, index, all) => all.slice(0, index + 1).join('/')); if (names.has(key) || parents.some((parent) => names.get(parent) === 'file') || (!isDirectory && [...names].some(([existing]) => existing.startsWith(`${key}/`)))) throw new Error('Duplicate or file/directory-conflicting ZIP path.'); names.set(key, isDirectory ? 'directory' : 'file');
      if ((entry.externalFileAttributes >>> 16) && (((entry.externalFileAttributes >>> 16) & 0o170000) === 0o120000)) throw new Error('Links are forbidden in portable ZIPs.');
      expanded += entry.uncompressedSize; if (entries.length >= maxEntries || expanded > maxBytes || (entry.compressedSize > 0 && entry.uncompressedSize / entry.compressedSize > maxRatio)) throw new Error('ZIP safety limits exceeded.'); entries.push({ entry, name }); zip.readEntry();
    } catch (e) { zip.close(); reject(e); } }); zip.readEntry(); });
  const manifestRecord = entries.find(({ name }) => name === MANIFEST_NAME); if (!manifestRecord) throw new Error('Portable release manifest is missing.');
  fs.mkdirSync(destination, { recursive: false });
  async function write(record) { if (/\/$/.test(record.entry.fileName)) return; const target = path.resolve(destination, record.name); if (!target.startsWith(`${path.resolve(destination)}${path.sep}`)) throw new Error('Zip Slip path rejected.'); fs.mkdirSync(path.dirname(target), { recursive: true });
    const readZip = await openZip(zipFile); await new Promise((resolve, reject) => { readZip.on('error', reject); readZip.on('entry', (entry) => { if (normalizeEntryName(entry.fileName) !== record.name) return readZip.readEntry(); readZip.openReadStream(entry, (e, input) => { if (e) return reject(e); const output = fs.createWriteStream(target, { flags: 'wx' }); input.on('error', reject); output.on('error', reject); output.on('finish', () => { readZip.close(); resolve(); }); input.pipe(output); }); }); readZip.readEntry(); }); }
  try { for (const record of entries) await write(record); const manifest = validateManifest(JSON.parse(fs.readFileSync(path.join(destination, MANIFEST_NAME), 'utf8')), identity); const actual = entries.filter(({ name, entry }) => name !== MANIFEST_NAME && !/\/$/.test(entry.fileName)); const wanted = new Map(manifest.managedFiles.map((f) => [normalizeEntryName(f.relativePath).toLowerCase(), f])); if (actual.length !== wanted.size || actual.some(({ name }) => !wanted.has(name.toLowerCase()))) throw new Error('ZIP payload does not exactly match managedFiles.');
    for (const { name } of actual) { const expected = wanted.get(name.toLowerCase()); const data = fs.readFileSync(path.join(destination, name)); if (data.length !== expected.size || crypto.createHash('sha256').update(data).digest('hex') !== expected.sha256.toLowerCase()) throw new Error(`Managed file verification failed: ${name}`); } return manifest;
  } catch (e) { fs.rmSync(destination, { recursive: true, force: true }); throw e; }
}
module.exports = { PROTECTED, extractAndVerify, normalizeEntryName, validateManifest };
