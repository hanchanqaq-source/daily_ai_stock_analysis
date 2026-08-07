const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  runWindowsDefenderScan,
} = require('../../../scripts/windows-defender-scan');

const HEAD = 'a'.repeat(40);

function createFixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pp02-defender-scan-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const target = path.join(root, 'candidate.exe');
  const scannerPath = path.join(root, 'MpCmdRun.exe');
  const reportPath = path.join(root, 'reports', 'scan.json');
  fs.writeFileSync(target, 'synthetic candidate bytes', 'utf8');
  fs.writeFileSync(scannerPath, 'synthetic scanner fixture', 'utf8');
  fs.mkdirSync(path.dirname(reportPath));
  return { root, target, scannerPath, reportPath };
}

function healthyStatus(scannerPath, overrides = {}) {
  return {
    amServiceEnabled: true,
    antivirusEnabled: true,
    amRunningMode: 'Normal',
    antivirusSignatureAge: 0,
    antivirusSignatureLastUpdatedUtc: '2026-08-06T10:00:00.0000000Z',
    antivirusSignatureVersion: '1.2.3.4',
    amEngineVersion: '1.1.2.3',
    amProductVersion: '4.18.26070.1000',
    disableArchiveScanning: false,
    scannerPath,
    ...overrides,
  };
}

function dependencies(status, options = {}) {
  const calls = [];
  const powerShellCalls = [];
  const preparation = {
    archiveScanningDisabled: false,
    removedWholeDriveExclusions: 2,
    scannerPath: status.scannerPath,
    ...(options.preparation || {}),
  };
  return {
    calls,
    powerShellCalls,
    value: {
      now: () => new Date('2026-08-06T12:00:00.000Z'),
      runEnvironmentPreparation: (script) => {
        powerShellCalls.push({ stage: 'environment_prepare', script });
        return options.preparationResult || {
          status: 0,
          stdout: JSON.stringify(preparation),
        };
      },
      runStatusQuery: (script) => {
        powerShellCalls.push({ stage: 'status_query', script });
        return { status: 0, stdout: JSON.stringify(status) };
      },
      runScanner: (scannerPath, args) => {
        calls.push({ scannerPath, args });
        if (args[0] === '-SignatureUpdate') {
          return options.signatureUpdateResult || { status: 0 };
        }
        if (args[0] === '-CheckExclusion') {
          return options.exclusionCheckResult || { status: 1 };
        }
        return { status: options.scannerExitCode || 0 };
      },
    },
  };
}

function readReport(reportPath) {
  return JSON.parse(fs.readFileSync(reportPath, 'utf8'));
}

test('clean scan repairs hosted-runner exclusions, updates from MMPC, proves targets are included, and scans', (t) => {
  const fixture = createFixture(t);
  const deps = dependencies(healthyStatus(fixture.scannerPath));

  const result = runWindowsDefenderScan({
    platform: 'win32',
    head: HEAD,
    targets: [fixture.target],
    reportPath: fixture.reportPath,
  }, deps.value);

  assert.equal(result.status, 'PASS');
  assert.equal(result.head, HEAD);
  assert.equal(result.defender.antivirusSignatureVersion, '1.2.3.4');
  assert.deepEqual(deps.powerShellCalls.map((call) => call.stage), [
    'environment_prepare',
    'status_query',
  ]);
  const preparationScript = deps.powerShellCalls[0].script;
  assert.match(preparationScript, /Remove-MpPreference -ExclusionPath \$root/);
  assert.equal(preparationScript.includes("foreach ($root in @('C:\\', 'D:\\')) {"), true);
  assert.match(preparationScript, /Set-MpPreference -DisableArchiveScanning \$false/);
  assert.deepEqual(deps.calls, [
    {
      scannerPath: fixture.scannerPath,
      args: ['-SignatureUpdate', '-MMPC'],
    },
    {
      scannerPath: fixture.scannerPath,
      args: ['-CheckExclusion', '-Path', path.resolve(fixture.target)],
    },
    {
      scannerPath: fixture.scannerPath,
      args: ['-Scan', '-ScanType', '3', '-File', path.resolve(fixture.target), '-DisableRemediation'],
    },
  ]);
  const report = readReport(fixture.reportPath);
  assert.equal(report.status, 'PASS');
  assert.deepEqual(report.environment, {
    archiveScanningEnabled: true,
    removedWholeDriveExclusions: 2,
  });
  assert.equal(report.targets[0].name, 'candidate.exe');
  assert.equal(report.targets[0].kind, 'file');
  assert.equal(report.targets[0].bytes, Buffer.byteLength('synthetic candidate bytes'));
  assert.equal(
    report.targets[0].sha256,
    crypto.createHash('sha256').update('synthetic candidate bytes').digest('hex'),
  );
  assert.equal(report.targets[0].exclusionStatus, 'NOT_EXCLUDED');
  assert.equal(report.targets[0].exclusionExitCode, 1);
  assert.equal(JSON.stringify(report).includes('synthetic candidate bytes'), false);
});

test('scan fails closed outside Windows before invoking Defender', (t) => {
  const fixture = createFixture(t);
  const deps = dependencies(healthyStatus(fixture.scannerPath));

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'linux', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'unsupported_platform',
  );
  assert.equal(deps.calls.length, 0);
  assert.equal(readReport(fixture.reportPath).status, 'FAIL');
});

test('hosted-runner Defender preparation failure blocks update and scan without child output', (t) => {
  const fixture = createFixture(t);
  const deps = dependencies(healthyStatus(fixture.scannerPath), {
    preparationResult: {
      status: 1,
      stdout: 'synthetic-sensitive-preparation-output',
      stderr: 'synthetic-sensitive-preparation-error',
    },
  });

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'defender_environment_prepare_failed',
  );
  assert.equal(deps.calls.length, 0);
  const reportText = fs.readFileSync(fixture.reportPath, 'utf8');
  const report = JSON.parse(reportText);
  assert.equal(report.reasonCode, 'defender_environment_prepare_failed');
  assert.deepEqual(report.processFailure, {
    stage: 'environment_prepare',
    exitCode: 1,
    signal: null,
    errorCode: null,
  });
  assert.equal(reportText.includes('synthetic-sensitive-preparation-output'), false);
  assert.equal(reportText.includes('synthetic-sensitive-preparation-error'), false);
  assert.equal(Object.hasOwn(report, 'stdout'), false);
  assert.equal(Object.hasOwn(report, 'stderr'), false);
});

test('MMPC signature update failure is reported separately without child output', (t) => {
  const fixture = createFixture(t);
  const deps = dependencies(healthyStatus(fixture.scannerPath), {
    signatureUpdateResult: {
      status: 1,
      stdout: 'synthetic-sensitive-update-output',
      stderr: 'synthetic-sensitive-update-error',
    },
  });

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'defender_signature_update_failed',
  );
  assert.equal(deps.calls.length, 1);
  assert.deepEqual(deps.calls[0].args, ['-SignatureUpdate', '-MMPC']);
  const reportText = fs.readFileSync(fixture.reportPath, 'utf8');
  const report = JSON.parse(reportText);
  assert.equal(report.reasonCode, 'defender_signature_update_failed');
  assert.deepEqual(report.processFailure, {
    stage: 'mmpc_signature_update',
    exitCode: 1,
    signal: null,
    errorCode: null,
  });
  assert.equal(reportText.includes('synthetic-sensitive-update-output'), false);
  assert.equal(reportText.includes('synthetic-sensitive-update-error'), false);
});

test('Defender status failure is reported separately with bounded process metadata', (t) => {
  const fixture = createFixture(t);
  const deps = dependencies(healthyStatus(fixture.scannerPath));
  deps.value.runStatusQuery = () => ({
    status: null,
    signal: 'SIGTERM',
    stdout: 'synthetic-sensitive-status-output',
    stderr: 'synthetic-sensitive-status-error',
    error: { code: 'ETIMEDOUT' },
  });

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'defender_status_query_failed',
  );
  assert.deepEqual(deps.calls.map((call) => call.args[0]), ['-SignatureUpdate']);
  const reportText = fs.readFileSync(fixture.reportPath, 'utf8');
  const report = JSON.parse(reportText);
  assert.equal(report.reasonCode, 'defender_status_query_failed');
  assert.deepEqual(report.processFailure, {
    stage: 'status_query',
    exitCode: null,
    signal: 'SIGTERM',
    errorCode: 'ETIMEDOUT',
  });
  assert.equal(reportText.includes('synthetic-sensitive-status-output'), false);
  assert.equal(reportText.includes('synthetic-sensitive-status-error'), false);
  assert.equal(Object.hasOwn(report, 'stdout'), false);
  assert.equal(Object.hasOwn(report, 'stderr'), false);
});

test('scan fails closed when archive scanning remains disabled after preparation', (t) => {
  const fixture = createFixture(t);
  const deps = dependencies(healthyStatus(fixture.scannerPath, {
    disableArchiveScanning: true,
  }));

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'defender_archive_scanning_disabled',
  );
  assert.equal(deps.calls.some((call) => call.args[0] === '-Scan'), false);
});

test('scan fails closed when MpCmdRun reports a target is excluded', (t) => {
  const fixture = createFixture(t);
  const deps = dependencies(healthyStatus(fixture.scannerPath), {
    exclusionCheckResult: { status: 0 },
  });

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'scan_target_excluded',
  );
  assert.equal(deps.calls.some((call) => call.args[0] === '-Scan'), false);
  const report = readReport(fixture.reportPath);
  assert.equal(report.targets[0].exclusionStatus, 'EXCLUDED');
  assert.equal(report.targets[0].exclusionExitCode, 0);
});

test('scan fails closed when target exclusion state cannot be proven', (t) => {
  const fixture = createFixture(t);
  const deps = dependencies(healthyStatus(fixture.scannerPath), {
    exclusionCheckResult: { status: 2 },
  });

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'scan_target_exclusion_check_failed',
  );
  assert.equal(deps.calls.some((call) => call.args[0] === '-Scan'), false);
});

for (const [name, overrides, reasonCode] of [
  ['disabled antivirus service', { amServiceEnabled: false }, 'defender_service_disabled'],
  ['disabled antivirus engine', { antivirusEnabled: false }, 'defender_antivirus_disabled'],
  ['passive mode', { amRunningMode: 'Passive Mode' }, 'defender_not_normal'],
  ['stale intelligence', { antivirusSignatureAge: 2 }, 'defender_signatures_stale'],
  ['missing signature identity', { antivirusSignatureVersion: '' }, 'defender_identity_missing'],
]) {
  test(`scan fails closed for ${name}`, (t) => {
    const fixture = createFixture(t);
    const deps = dependencies(healthyStatus(fixture.scannerPath, overrides));

    assert.throws(
      () => runWindowsDefenderScan({
        platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
      }, deps.value),
      (error) => error.reasonCode === reasonCode,
    );
    assert.equal(deps.calls.some((call) => call.args[0] === '-Scan'), false);
  });
}

test('scan rejects a missing scanner executable or target', (t) => {
  const fixture = createFixture(t);
  const missingScanner = path.join(fixture.root, 'missing-MpCmdRun.exe');
  let deps = dependencies(healthyStatus(missingScanner));
  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'defender_scanner_missing',
  );

  deps = dependencies(healthyStatus(fixture.scannerPath));
  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32',
      head: HEAD,
      targets: [path.join(fixture.root, 'missing-candidate.exe')],
      reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'scan_target_missing',
  );
});

test('MpCmdRun exit 2 blocks the candidate as detection or scan error', (t) => {
  const fixture = createFixture(t);
  const deps = dependencies(healthyStatus(fixture.scannerPath), { scannerExitCode: 2 });

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'threat_detected_or_scan_failed',
  );
  const report = readReport(fixture.reportPath);
  assert.equal(report.status, 'FAIL');
  assert.equal(report.reasonCode, 'threat_detected_or_scan_failed');
});

test('detection report binds Defender identity, prior success, failing target digest, and exit code', (t) => {
  const fixture = createFixture(t);
  const secondTarget = path.join(fixture.root, 'portable.zip');
  fs.writeFileSync(secondTarget, 'synthetic portable bytes', 'utf8');
  const calls = [];
  const status = healthyStatus(fixture.scannerPath);

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32',
      head: HEAD,
      targets: [fixture.target, secondTarget],
      reportPath: fixture.reportPath,
    }, {
      now: () => new Date('2026-08-06T12:00:00.000Z'),
      runEnvironmentPreparation: () => ({
        status: 0,
        stdout: JSON.stringify({
          archiveScanningDisabled: false,
          removedWholeDriveExclusions: 2,
          scannerPath: fixture.scannerPath,
        }),
      }),
      runStatusQuery: () => ({ status: 0, stdout: JSON.stringify(status) }),
      runScanner: (_scannerPath, args) => {
        calls.push(args);
        if (args[0] === '-SignatureUpdate') return { status: 0 };
        if (args[0] === '-CheckExclusion') return { status: 1 };
        return { status: args.includes(fixture.target) ? 0 : 2 };
      },
    }),
    (error) => error.reasonCode === 'threat_detected_or_scan_failed',
  );

  const report = readReport(fixture.reportPath);
  assert.equal(report.status, 'FAIL');
  assert.equal(report.defender.antivirusSignatureVersion, '1.2.3.4');
  assert.equal(report.targets.length, 2);
  assert.deepEqual(
    report.targets.map((target) => [target.name, target.scanStatus, target.scanExitCode]),
    [
      ['candidate.exe', 'PASS', 0],
      ['portable.zip', 'FAIL', 2],
    ],
  );
  assert.equal(
    report.targets[1].sha256,
    crypto.createHash('sha256').update('synthetic portable bytes').digest('hex'),
  );
  assert.equal(Object.hasOwn(report, 'stdout'), false);
  assert.equal(Object.hasOwn(report, 'stderr'), false);
});

test('missing report directory is a blocking configuration failure', (t) => {
  const fixture = createFixture(t);
  fs.rmSync(path.dirname(fixture.reportPath), { recursive: true, force: true });
  const deps = dependencies(healthyStatus(fixture.scannerPath));

  assert.throws(
    () => runWindowsDefenderScan({
      platform: 'win32', head: HEAD, targets: [fixture.target], reportPath: fixture.reportPath,
    }, deps.value),
    (error) => error.reasonCode === 'report_directory_missing',
  );
  assert.equal(deps.calls.length, 0);
});
