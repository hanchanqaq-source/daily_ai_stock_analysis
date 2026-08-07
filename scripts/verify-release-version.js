const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const STABLE_TAG_PATTERN = /^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const MODES = new Set(['candidate', 'release', 'auto-tag']);

function parseStableVersion(value) {
  const match = STABLE_TAG_PATTERN.exec(String(value || '').trim());
  if (!match) {
    throw new Error(`Version must be a stable vX.Y.Z value: ${value || '<empty>'}`);
  }
  return match.slice(1).map((part) => Number(part));
}

function compareStableVersions(left, right) {
  const leftParts = parseStableVersion(left);
  const rightParts = parseStableVersion(right);
  for (let index = 0; index < leftParts.length; index += 1) {
    if (leftParts[index] !== rightParts[index]) {
      return leftParts[index] > rightParts[index] ? 1 : -1;
    }
  }
  return 0;
}

function readJsonVersion(root, relativePath, selector = (document) => document.version) {
  const absolutePath = path.join(root, relativePath);
  const document = JSON.parse(fs.readFileSync(absolutePath, 'utf8'));
  return { path: absolutePath, version: String(selector(document) || '').trim() };
}

function readVersionSources(root) {
  const versionPath = path.join(root, 'VERSION');
  const version = fs.readFileSync(versionPath, 'utf8').trim();
  parseStableVersion(`v${version}`);
  const sources = [
    { path: versionPath, version },
    readJsonVersion(root, 'apps/dsa-desktop/package.json'),
    readJsonVersion(root, 'apps/dsa-desktop/package-lock.json'),
    readJsonVersion(root, 'apps/dsa-desktop/package-lock.json', (value) => value.packages?.['']?.version),
    readJsonVersion(root, 'apps/dsa-web/package.json'),
    readJsonVersion(root, 'apps/dsa-web/package-lock.json'),
    readJsonVersion(root, 'apps/dsa-web/package-lock.json', (value) => value.packages?.['']?.version),
  ];
  const backupPath = path.join(root, 'src/services/full_data_backup_service.py');
  const backupSource = fs.readFileSync(backupPath, 'utf8');
  const backupMatches = [...backupSource.matchAll(/^DEFAULT_APPLICATION_VERSION\s*=\s*"([^"]+)"\s*$/gm)];
  if (backupMatches.length !== 1) {
    throw new Error(`${backupPath} must declare exactly one DEFAULT_APPLICATION_VERSION.`);
  }
  sources.push({ path: backupPath, version: backupMatches[0][1] });
  for (const source of sources) {
    if (source.version !== version) {
      throw new Error(`${source.path} version ${source.version || '<empty>'} does not match VERSION ${version}.`);
    }
  }
  return { version, sources };
}

function getAllStableTags(root, run = execFileSync) {
  const output = run(
    'git',
    ['tag', '--list', 'v*'],
    { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
  );
  return output
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter((item) => STABLE_TAG_PATTERN.test(item));
}

function getStableTagsPointingAtHead(root) {
  const output = execFileSync(
    'git',
    ['tag', '--points-at', 'HEAD', '--list', 'v*'],
    { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
  );
  return output
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter((item) => STABLE_TAG_PATTERN.test(item));
}

function refreshStableTags(root, run = execFileSync) {
  const shallow = run(
    'git',
    ['rev-parse', '--is-shallow-repository'],
    { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
  ).trim() === 'true';
  const fetchArguments = ['fetch', '--force', '--tags', '--quiet'];
  if (shallow) fetchArguments.push('--unshallow');
  fetchArguments.push('origin');
  run(
    'git',
    fetchArguments,
    { cwd: root, encoding: 'utf8', stdio: ['ignore', 'ignore', 'pipe'] },
  );
}

function latestStableTag(stableTags) {
  const unique = [...new Set(stableTags.filter((tag) => STABLE_TAG_PATTERN.test(tag)))];
  unique.sort(compareStableVersions);
  return unique.at(-1) || null;
}

function successorTag(tag, bump) {
  const [major, minor, patch] = parseStableVersion(tag);
  if (bump === 'patch') return `v${major}.${minor}.${patch + 1}`;
  if (bump === 'minor') return `v${major}.${minor + 1}.0`;
  if (bump === 'major') return `v${major + 1}.0.0`;
  throw new Error(`Auto-tag bump must be patch, minor, or major: ${bump || '<empty>'}`);
}

function verifyRepositoryVersion({
  root,
  mode,
  releaseTag = '',
  bump = '',
  stableTags,
  headTags,
}) {
  if (!MODES.has(mode)) {
    throw new Error(`Version verification mode is invalid: ${mode || '<empty>'}`);
  }
  const resolvedRoot = path.resolve(root);
  const { version, sources } = readVersionSources(resolvedRoot);
  const sourceTag = `v${version}`;
  let latest = null;
  let resolvedReleaseTag = releaseTag;

  if (mode === 'candidate' || mode === 'auto-tag') {
    const tags = stableTags === undefined ? getAllStableTags(resolvedRoot) : stableTags;
    let comparisonTags = tags;
    if (mode === 'candidate') {
      const tagsAtHead = headTags === undefined
        ? (stableTags === undefined ? getStableTagsPointingAtHead(resolvedRoot) : [])
        : headTags.filter((tag) => STABLE_TAG_PATTERN.test(tag));
      for (const tagAtHead of tagsAtHead) {
        if (tagAtHead !== sourceTag) {
          throw new Error(`Stable tag ${tagAtHead} at HEAD does not match source tag ${sourceTag}.`);
        }
      }
      const tagsAtHeadSet = new Set(tagsAtHead);
      comparisonTags = tags.filter((tag) => !tagsAtHeadSet.has(tag));
    }
    latest = latestStableTag(comparisonTags);
    if (!latest) {
      throw new Error('No fetched stable release tag was found.');
    }
    if (compareStableVersions(sourceTag, latest) <= 0) {
      throw new Error(`Candidate source ${sourceTag} must be newer than latest stable tag ${latest}.`);
    }
  }

  if (mode === 'release') {
    parseStableVersion(releaseTag);
    if (releaseTag !== sourceTag) {
      throw new Error(`Requested release tag ${releaseTag} does not match source version ${sourceTag}.`);
    }
  }

  if (mode === 'auto-tag') {
    const expected = successorTag(latest, bump);
    if (sourceTag !== expected) {
      throw new Error(`Source version ${sourceTag} is not the expected ${bump} successor ${expected}.`);
    }
    resolvedReleaseTag = sourceTag;
  }

  return {
    mode,
    version,
    releaseTag: resolvedReleaseTag || null,
    latestStableTag: latest,
    sourceCount: sources.length,
  };
}

function parseArguments(argv) {
  const mode = argv[0] || '';
  let releaseTag = '';
  let bump = '';
  for (let index = 1; index < argv.length; index += 1) {
    const name = argv[index];
    const value = argv[index + 1] || '';
    if (name === '--tag') releaseTag = value;
    else if (name === '--bump') bump = value;
    else throw new Error(`Unknown version gate argument: ${name}`);
    index += 1;
  }
  return { mode, releaseTag, bump };
}

function main() {
  const options = parseArguments(process.argv.slice(2));
  const root = path.resolve(__dirname, '..');
  if (options.mode === 'candidate' && process.env.GITHUB_ACTIONS === 'true') {
    refreshStableTags(root);
  }
  const result = verifyRepositoryVersion({
    root,
    ...options,
  });
  process.stdout.write('PP02_RELEASE_VERSION_GATE=PASS\n');
  process.stdout.write(`PP02_RELEASE_VERSION_MODE=${result.mode}\n`);
  process.stdout.write(`PP02_RELEASE_VERSION=${result.version}\n`);
  if (result.latestStableTag) {
    process.stdout.write(`PP02_LATEST_STABLE_TAG=${result.latestStableTag}\n`);
  }
  if (result.releaseTag) {
    process.stdout.write(`PP02_RELEASE_TAG=${result.releaseTag}\n`);
  }
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    process.stderr.write('PP02_RELEASE_VERSION_GATE=FAIL\n');
    process.stderr.write(`${error instanceof Error ? error.message : 'Version verification failed.'}\n`);
    process.exitCode = 1;
  }
}

module.exports = {
  compareStableVersions,
  getAllStableTags,
  getStableTagsPointingAtHead,
  latestStableTag,
  parseStableVersion,
  readVersionSources,
  refreshStableTags,
  successorTag,
  verifyRepositoryVersion,
};
