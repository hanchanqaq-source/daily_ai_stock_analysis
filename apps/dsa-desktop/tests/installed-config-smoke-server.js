'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

const LOOPBACK_HOST = '127.0.0.1';
const DEFAULT_MAX_BODY_BYTES = 64 * 1024;
const DEFAULT_LIFETIME_MS = 420 * 1000;

function deriveFakeCredential(head) {
  if (!/^[0-9a-f]{40}$/i.test(String(head || ''))) {
    throw new Error('Acceptance server requires an exact Head.');
  }
  const normalized = String(head).toLowerCase();
  const digest = crypto.createHash('sha256')
    .update(`pp02-r37-fake:${normalized}`, 'utf8')
    .digest('hex');
  return `pp02-r37-${digest}`;
}

function sameValue(left, right) {
  const leftDigest = crypto.createHash('sha256').update(String(left), 'utf8').digest();
  const rightDigest = crypto.createHash('sha256').update(String(right), 'utf8').digest();
  return crypto.timingSafeEqual(leftDigest, rightDigest);
}

function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, {
    encoding: 'utf8',
    mode: 0o600,
  });
}

function safeErrorToken(value, fallback) {
  const text = String(value || '').trim();
  return /^[A-Za-z0-9_.:-]{1,96}$/.test(text) ? text : fallback;
}

async function createAcceptanceServer({
  head,
  receiptPath,
  readyPath,
  maxBodyBytes = DEFAULT_MAX_BODY_BYTES,
  lifetimeMs = DEFAULT_LIFETIME_MS,
  closeAfterSuccess = false,
} = {}) {
  const normalizedHead = String(head || '').toLowerCase();
  const fakeCredential = deriveFakeCredential(normalizedHead);
  if (!path.isAbsolute(receiptPath || '') || !path.isAbsolute(readyPath || '')) {
    throw new Error('Acceptance server output paths must be absolute.');
  }
  if (!Number.isSafeInteger(maxBodyBytes) || maxBodyBytes < 64 || maxBodyBytes > 1024 * 1024) {
    throw new Error('Acceptance server body bound is invalid.');
  }
  if (!Number.isSafeInteger(lifetimeMs) || lifetimeMs < 100 || lifetimeMs > 10 * 60 * 1000) {
    throw new Error('Acceptance server lifetime is invalid.');
  }

  let requestCount = 0;
  let closeReason = '';
  let complete;
  const completion = new Promise((resolve) => {
    complete = resolve;
  });

  const server = http.createServer((req, res) => {
    requestCount += 1;
    const routeMatched = req.method === 'POST' && req.url === '/v1/chat/completions';
    if (!routeMatched) {
      res.writeHead(404, { 'content-type': 'application/json' });
      res.end('{"error":"not_found"}');
      return;
    }

    let bodyBytes = 0;
    let rejected = false;
    const chunks = [];
    req.on('data', (chunk) => {
      if (rejected) return;
      bodyBytes += chunk.length;
      if (bodyBytes > maxBodyBytes) {
        rejected = true;
        res.writeHead(413, { 'content-type': 'application/json' });
        res.end('{"error":"request_too_large"}');
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      if (rejected) return;
      const authorizationMatched = sameValue(
        req.headers.authorization || '',
        `Bearer ${fakeCredential}`,
      );
      if (!authorizationMatched) {
        res.writeHead(401, { 'content-type': 'application/json' });
        res.end('{"error":"unauthorized"}');
        return;
      }

      let payload;
      try {
        payload = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      } catch (_error) {
        res.writeHead(400, { 'content-type': 'application/json' });
        res.end('{"error":"invalid_json"}');
        return;
      }
      const model = typeof payload.model === 'string' ? payload.model : '';
      const modelMatched = model === 'pp02-acceptance' || model.endsWith('/pp02-acceptance');
      if (!modelMatched || !Array.isArray(payload.messages)) {
        res.writeHead(422, { 'content-type': 'application/json' });
        res.end('{"error":"invalid_smoke_request"}');
        return;
      }

      writeJson(receiptPath, {
        schemaVersion: 1,
        head: normalizedHead,
        authorizationMatched: true,
        routeMatched: true,
        modelMatched: true,
        requestCount,
      });
      const response = {
        id: 'chatcmpl-pp02-acceptance',
        object: 'chat.completion',
        created: 0,
        model: 'pp02-acceptance',
        choices: [{
          index: 0,
          message: {
            role: 'assistant',
            content: '{"ok":true,"backend_smoke":"passed"}',
          },
          finish_reason: 'stop',
        }],
        usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
      };
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify(response), () => {
        if (closeAfterSuccess) void close('success');
      });
    });
  });
  server.requestTimeout = 15 * 1000;
  server.headersTimeout = 10 * 1000;

  let lifetimeTimer;
  async function close(reason = 'manual') {
    if (!closeReason) closeReason = reason;
    if (lifetimeTimer) clearTimeout(lifetimeTimer);
    if (server.listening) {
      await new Promise((resolve) => server.close(resolve));
    }
    complete(closeReason);
  }

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, LOOPBACK_HOST, resolve);
  });
  server.removeAllListeners('error');
  const address = server.address();
  writeJson(readyPath, {
    schemaVersion: 1,
    head: normalizedHead,
    host: LOOPBACK_HOST,
    port: address.port,
  });
  lifetimeTimer = setTimeout(() => void close('timeout'), lifetimeMs);

  return {
    address,
    close,
    completion,
  };
}

async function main() {
  const head = process.env.DSA_CONFIG_ACCEPTANCE_HEAD || '';
  const receiptPath = path.resolve(process.env.DSA_CONFIG_ACCEPTANCE_RECEIPT_PATH || '');
  const readyPath = path.resolve(process.env.DSA_CONFIG_ACCEPTANCE_READY_PATH || '');
  const acceptance = await createAcceptanceServer({
    head,
    receiptPath,
    readyPath,
    closeAfterSuccess: true,
  });
  const reason = await acceptance.completion;
  if (reason !== 'success') {
    throw new Error('Acceptance server did not receive the expected request.');
  }
  process.stdout.write('WINDOWS_INSTALLED_CONFIG_MOCK=PASS\n');
}

if (require.main === module) {
  main().catch((error) => {
    const safeErrorName = safeErrorToken(error && error.name, 'Error');
    const safeErrorCode = safeErrorToken(error && error.code, 'unknown');
    process.stderr.write(
      `WINDOWS_INSTALLED_CONFIG_MOCK=FAIL name=${safeErrorName} code=${safeErrorCode}\n`,
    );
    process.exitCode = 1;
  });
}

module.exports = {
  createAcceptanceServer,
  deriveFakeCredential,
};
