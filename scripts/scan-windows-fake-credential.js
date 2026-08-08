const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const SKIPPED_DIRECTORIES = new Set(['.git', '__pycache__', 'node_modules']);
const CHUNK_BYTES = 1024 * 1024;

function parseArguments(argv) {
  let head = '';
  let report = '';
  const paths = [];
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === '--head') {
      head = argv[index + 1] || '';
      index += 1;
    } else if (argv[index] === '--path') {
      paths.push(argv[index + 1] || '');
      index += 1;
    } else if (argv[index] === '--report') {
      report = argv[index + 1] || '';
      index += 1;
    } else {
      throw new Error('Invalid fake credential scan arguments.');
    }
  }
  if (!/^[0-9a-f]{40}$/i.test(head) || paths.length === 0 || paths.some((item) => !item)) {
    throw new Error('Fake credential scan requires an exact Head and at least one path.');
  }
  return { head: head.toLowerCase(), paths, report };
}

function deriveFakeCredential(head) {
  const digest = crypto.createHash('sha256').update(`pp02-r37-fake:${head}`, 'utf8').digest('hex');
  return `pp02-r37-${digest}`;
}

function safeErrorToken(value, fallback) {
  const text = String(value || '');
  return /^[A-Za-z0-9_.:-]{1,96}$/.test(text) ? text : fallback;
}

function fileContainsAny(filePath, patterns) {
  const descriptor = fs.openSync(filePath, 'r');
  const buffer = Buffer.allocUnsafe(CHUNK_BYTES);
  const overlapBytes = Math.max(...patterns.map((pattern) => pattern.length)) - 1;
  let carry = Buffer.alloc(0);
  try {
    while (true) {
      const bytesRead = fs.readSync(descriptor, buffer, 0, buffer.length, null);
      if (bytesRead === 0) {
        return false;
      }
      const window = Buffer.concat([carry, buffer.subarray(0, bytesRead)]);
      if (patterns.some((pattern) => window.indexOf(pattern) !== -1)) {
        return true;
      }
      carry = window.subarray(Math.max(0, window.length - overlapBytes));
    }
  } finally {
    fs.closeSync(descriptor);
  }
}

function scanPath(targetPath, patterns, rootPath, rootIndex) {
  const resolved = path.resolve(targetPath);
  const scanContext = {
    rootIndex,
    relativePath: path.relative(rootPath, resolved).split(path.sep).join('/') || '.',
  };
  try {
    const metadata = fs.lstatSync(resolved);
    if (metadata.isSymbolicLink()) {
      return;
    }
    if (metadata.isDirectory()) {
      for (const name of fs.readdirSync(resolved)) {
        if (!SKIPPED_DIRECTORIES.has(name)) {
          scanPath(path.join(resolved, name), patterns, rootPath, rootIndex);
        }
      }
      return;
    }
    if (metadata.isFile() && fileContainsAny(resolved, patterns)) {
      const error = new Error('Fake credential plaintext was found in scanned output.');
      error.scanMatch = scanContext;
      throw error;
    }
  } catch (error) {
    if (!error.scanMatch && !error.scanContext) {
      error.scanContext = scanContext;
    }
    throw error;
  }
}

function main({ head, paths }) {
  const fake = deriveFakeCredential(head);
  const patterns = [Buffer.from(fake, 'utf8'), Buffer.from(fake, 'utf16le')];
  for (const [rootIndex, targetPath] of paths.entries()) {
    const rootPath = path.resolve(targetPath);
    scanPath(rootPath, patterns, rootPath, rootIndex);
  }
  process.stdout.write('R3_7_WINDOWS_FAKE_CREDENTIAL_SCAN=PASS\n');
  process.stdout.write(`R3_7_WINDOWS_FAKE_CREDENTIAL_SCAN_HEAD=${head}\n`);
}

let reportPath = '';
try {
  const parsed = parseArguments(process.argv.slice(2));
  reportPath = parsed.report;
  main(parsed);
} catch (error) {
  if (reportPath && error) {
    const context = error.scanMatch || error.scanContext || {};
    const result = error.scanMatch ? 'MATCH' : 'ERROR';
    const errorCode = error.scanMatch
      ? 'plaintext_match'
      : safeErrorToken(error.safeCode || error.code || error.name, 'unknown');
    try {
      fs.writeFileSync(reportPath, `${JSON.stringify({
        schemaVersion: 1,
        result,
        rootIndex: Number.isInteger(context.rootIndex) ? context.rootIndex : null,
        relativePath: context.relativePath || '<unavailable>',
        errorCode,
      }, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' });
    } catch (_reportError) {
      // The scanner still fails closed when its optional diagnostic cannot be written.
    }
  }
  process.stderr.write('R3_7_WINDOWS_FAKE_CREDENTIAL_SCAN=FAIL\n');
  process.exitCode = 1;
}
