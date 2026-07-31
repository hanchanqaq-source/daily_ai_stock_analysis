const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const SKIPPED_DIRECTORIES = new Set(['.git', '__pycache__', 'node_modules']);
const CHUNK_BYTES = 1024 * 1024;

function parseArguments(argv) {
  let head = '';
  const paths = [];
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === '--head') {
      head = argv[index + 1] || '';
      index += 1;
    } else if (argv[index] === '--path') {
      paths.push(argv[index + 1] || '');
      index += 1;
    } else {
      throw new Error('Invalid fake credential scan arguments.');
    }
  }
  if (!/^[0-9a-f]{40}$/i.test(head) || paths.length === 0 || paths.some((item) => !item)) {
    throw new Error('Fake credential scan requires an exact Head and at least one path.');
  }
  return { head: head.toLowerCase(), paths };
}

function deriveFakeCredential(head) {
  const digest = crypto.createHash('sha256').update(`pp02-r37-fake:${head}`, 'utf8').digest('hex');
  return `pp02-r37-${digest}`;
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

function scanPath(targetPath, patterns) {
  const resolved = path.resolve(targetPath);
  if (!fs.existsSync(resolved)) {
    throw new Error('A required fake credential scan path is missing.');
  }
  const metadata = fs.lstatSync(resolved);
  if (metadata.isSymbolicLink()) {
    return;
  }
  if (metadata.isDirectory()) {
    for (const name of fs.readdirSync(resolved)) {
      if (!SKIPPED_DIRECTORIES.has(name)) {
        scanPath(path.join(resolved, name), patterns);
      }
    }
    return;
  }
  if (metadata.isFile() && fileContainsAny(resolved, patterns)) {
    throw new Error('Fake credential plaintext was found in scanned output.');
  }
}

function main() {
  const { head, paths } = parseArguments(process.argv.slice(2));
  const fake = deriveFakeCredential(head);
  const patterns = [Buffer.from(fake, 'utf8'), Buffer.from(fake, 'utf16le')];
  for (const targetPath of paths) {
    scanPath(targetPath, patterns);
  }
  process.stdout.write('R3_7_WINDOWS_FAKE_CREDENTIAL_SCAN=PASS\n');
  process.stdout.write(`R3_7_WINDOWS_FAKE_CREDENTIAL_SCAN_HEAD=${head}\n`);
}

try {
  main();
} catch (_error) {
  process.stderr.write('R3_7_WINDOWS_FAKE_CREDENTIAL_SCAN=FAIL\n');
  process.exitCode = 1;
}
