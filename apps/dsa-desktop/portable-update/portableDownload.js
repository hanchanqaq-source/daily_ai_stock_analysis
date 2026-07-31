const fs = require('fs');
const crypto = require('crypto');
const https = require('https');

const ALLOWED_DOWNLOAD_HOSTS = new Set(['github.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com']);

function downloadHttps(url, destination, {
  request = https.get,
  maxBytes = 2 * 1024 ** 3,
  maxRedirects = 5,
  connectTimeoutMs = 10_000,
  responseTimeoutMs = 30_000,
  totalTimeoutMs = 10 * 60_000,
} = {}) {
  let redirects = 0;
  let settled = false;
  let requestHandle = null;
  let responseHandle = null;
  let output = null;
  let totalTimer = null;

  return new Promise((resolve, reject) => {
    const cleanup = (error, result) => {
      if (settled) return;
      settled = true;
      clearTimeout(totalTimer);
      if (requestHandle && !requestHandle.destroyed) requestHandle.destroy();
      if (responseHandle && !responseHandle.destroyed) responseHandle.destroy();
      if (output) output.destroy();
      if (error) fs.rm(destination, { force: true }, () => reject(error));
      else resolve(result);
    };

    const fetch = (candidate) => {
      let parsed;
      try { parsed = new URL(candidate); } catch (_) { cleanup(new Error('Invalid download URL.')); return; }
      if (parsed.protocol !== 'https:' || !ALLOWED_DOWNLOAD_HOSTS.has(parsed.hostname.toLowerCase())) {
        cleanup(new Error('Download URL is not an allowed GitHub Release asset host.')); return;
      }
      requestHandle = request(parsed, { headers: { 'User-Agent': 'pp02-portable-updater' } }, (response) => {
        responseHandle = response;
        response.setTimeout?.(responseTimeoutMs, () => cleanup(new Error('Download response timeout.')));
        const status = Number(response.statusCode || 0);
        if (status >= 300 && status < 400) {
          response.resume?.();
          if (!response.headers.location) { cleanup(new Error('Download redirect is missing Location.')); return; }
          if (redirects >= maxRedirects) { cleanup(new Error('Download redirect limit exceeded.')); return; }
          redirects += 1;
          fetch(new URL(response.headers.location, parsed).toString());
          return;
        }
        if (status !== 200) { cleanup(new Error(`Download failed with HTTP ${status}.`)); return; }
        const rawLength = response.headers['content-length'];
        const expected = rawLength === undefined ? null : Number(rawLength);
        if (expected !== null && (!Number.isSafeInteger(expected) || expected < 0 || expected > maxBytes)) { cleanup(new Error('Invalid or excessive Content-Length.')); return; }
        let received = 0;
        output = fs.createWriteStream(destination, { flags: 'wx' });
        response.on('data', (chunk) => { received += chunk.length; if (received > maxBytes) cleanup(new Error('Download exceeds size limit.')); });
        response.on('aborted', () => cleanup(new Error('Download was interrupted.')));
        response.on('error', (error) => cleanup(error));
        output.on('error', (error) => cleanup(error));
        output.on('finish', () => {
          if (expected !== null && expected !== received) { cleanup(new Error('Downloaded length does not match Content-Length.')); return; }
          output.close(() => cleanup(null, { bytes: received, redirects }));
        });
        response.pipe(output);
      });
      requestHandle.setTimeout?.(connectTimeoutMs, () => cleanup(new Error('Download connection timeout.')));
      requestHandle.on('error', (error) => cleanup(error));
    };

    totalTimer = setTimeout(() => cleanup(new Error('Download total timeout.')), totalTimeoutMs);
    fetch(url);
  });
}

function sha256File(file) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(file);
    stream.on('error', reject); stream.on('data', (chunk) => hash.update(chunk)); stream.on('end', () => resolve(hash.digest('hex')));
  });
}

module.exports = { ALLOWED_DOWNLOAD_HOSTS, downloadHttps, sha256File };
