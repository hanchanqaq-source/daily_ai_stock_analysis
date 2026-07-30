const { ARTIFACT_PREFIX } = require('./portableIdentity');

function selectPortableAssets(release, version) {
  const tag = `v${version}`;
  if (!release || release.tag_name !== tag || !Array.isArray(release.assets)) throw new Error('Release tag does not match target version.');
  const zipName = `${ARTIFACT_PREFIX}-${tag}.zip`;
  const shaName = `${zipName}.sha256`;
  const exact = (name) => release.assets.filter((asset) => asset && asset.name === name);
  const zips = exact(zipName);
  const shas = exact(shaName);
  if (zips.length !== 1 || shas.length !== 1) throw new Error('Release must contain one exact portable ZIP/SHA-256 pair.');
  for (const asset of [...zips, ...shas]) {
    const url = new URL(asset.browser_download_url);
    if (url.protocol !== 'https:' || url.hostname !== 'github.com') throw new Error('Portable assets must use GitHub HTTPS downloads.');
  }
  return { zip: zips[0], sha256: shas[0], zipName, shaName, tag };
}

function parseBoundSha256(text, zipName) {
  const lines = String(text || '').trim().split(/\r?\n/).filter(Boolean);
  if (lines.length !== 1) throw new Error('SHA-256 file must contain exactly one record.');
  const match = lines[0].match(/^([a-fA-F0-9]{64})\s+\*?(.+)$/);
  if (!match || match[2] !== zipName) throw new Error('SHA-256 record is not bound to the selected ZIP.');
  return match[1].toLowerCase();
}

module.exports = { parseBoundSha256, selectPortableAssets };
