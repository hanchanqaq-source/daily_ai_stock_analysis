const fs = require('fs');
const crypto = require('crypto');
const https = require('https');

function downloadHttps(url, destination, { request = https.get, maxBytes = 2 * 1024 ** 3 } = {}) {
  const parsed = new URL(url);
  if (parsed.protocol !== 'https:') return Promise.reject(new Error('Only HTTPS downloads are allowed.'));
  return new Promise((resolve, reject) => {
    const output = fs.createWriteStream(destination, { flags: 'wx' });
    let received = 0;
    let settled = false;
    const fail = (error) => { if (settled) return; settled = true; output.destroy(); fs.rm(destination, { force: true }, () => reject(error)); };
    const req = request(parsed, { headers: { 'User-Agent': 'pp02-portable-updater' } }, (response) => {
      if (response.statusCode !== 200) return fail(new Error(`Download failed with HTTP ${response.statusCode}.`));
      const expected = Number(response.headers['content-length']);
      response.on('data', (chunk) => { received += chunk.length; if (received > maxBytes) fail(new Error('Download exceeds size limit.')); });
      response.on('aborted', () => fail(new Error('Download was interrupted.')));
      response.on('error', fail);
      output.on('finish', () => {
        if (settled) return;
        if (Number.isFinite(expected) && expected !== received) return fail(new Error('Downloaded length does not match Content-Length.'));
        settled = true; output.close(() => resolve({ bytes: received }));
      });
      response.pipe(output);
    });
    req.on('error', fail);
  });
}

function sha256File(file) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(file);
    stream.on('error', reject); stream.on('data', (chunk) => hash.update(chunk)); stream.on('end', () => resolve(hash.digest('hex')));
  });
}

module.exports = { downloadHttps, sha256File };
