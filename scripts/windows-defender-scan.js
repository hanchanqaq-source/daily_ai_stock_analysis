const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const MAX_SIGNATURE_AGE_DAYS = 1;
const SIGNATURE_UPDATE_MAX_ATTEMPTS = 3;
const SIGNATURE_UPDATE_RETRY_DELAY_MS = 5000;
const HEAD_PATTERN = /^[0-9a-f]{40}$/i;

class MalwareScanError extends Error {
  constructor(reasonCode, message, processFailure = null) {
    super(message);
    this.name = 'MalwareScanError';
    this.reasonCode = reasonCode;
    if (processFailure) this.processFailure = processFailure;
  }
}

function fail(reasonCode, message) {
  throw new MalwareScanError(reasonCode, message);
}

function sha256File(filePath) {
  const hash = crypto.createHash('sha256');
  const descriptor = fs.openSync(filePath, 'r');
  const buffer = Buffer.allocUnsafe(1024 * 1024);
  try {
    while (true) {
      const bytesRead = fs.readSync(descriptor, buffer, 0, buffer.length, null);
      if (bytesRead === 0) break;
      hash.update(buffer.subarray(0, bytesRead));
    }
  } finally {
    fs.closeSync(descriptor);
  }
  return hash.digest('hex');
}

function describeTarget(targetPath) {
  const resolved = path.resolve(targetPath);
  if (!fs.existsSync(resolved)) {
    fail('scan_target_missing', 'A required Defender scan target is missing.');
  }
  const metadata = fs.lstatSync(resolved);
  if (metadata.isSymbolicLink()) {
    fail('scan_target_symlink', 'Defender scan targets must not be symbolic links.');
  }
  if (metadata.isFile()) {
    return {
      resolved,
      report: {
        name: path.basename(resolved),
        kind: 'file',
        bytes: metadata.size,
        sha256: sha256File(resolved),
      },
    };
  }
  if (!metadata.isDirectory()) {
    fail('scan_target_type_invalid', 'Defender scan targets must be files or directories.');
  }
  let fileCount = 0;
  let bytes = 0;
  const pending = [resolved];
  while (pending.length > 0) {
    const directory = pending.pop();
    for (const name of fs.readdirSync(directory)) {
      const child = path.join(directory, name);
      const childMetadata = fs.lstatSync(child);
      if (childMetadata.isSymbolicLink()) {
        fail('scan_target_symlink', 'Defender scan directories must not contain symbolic links.');
      }
      if (childMetadata.isDirectory()) pending.push(child);
      else if (childMetadata.isFile()) {
        fileCount += 1;
        bytes += childMetadata.size;
      } else {
        fail('scan_target_type_invalid', 'Defender scan directories contain an unsupported item.');
      }
    }
  }
  return {
    resolved,
    report: {
      name: path.basename(resolved),
      kind: 'directory',
      fileCount,
      bytes,
    },
  };
}

function defenderEnvironmentPreparationScript() {
  return [
    "$ErrorActionPreference = 'Stop'",
    'Import-Module Defender -ErrorAction Stop',
    '$preferences = Get-MpPreference -ErrorAction Stop',
    '$removedWholeDriveExclusions = 0',
    "foreach ($root in @('C:\\', 'D:\\')) {",
    '  if (@($preferences.ExclusionPath) -contains $root) {',
    '    Remove-MpPreference -ExclusionPath $root -Force -ErrorAction Stop',
    '    $removedWholeDriveExclusions += 1',
    '  }',
    '}',
    'Set-MpPreference -DisableArchiveScanning $false -Force -ErrorAction Stop',
    '$preferences = Get-MpPreference -ErrorAction Stop',
    "$platformRoot = Join-Path $env:ProgramData 'Microsoft\\Windows Defender\\Platform'",
    '$scanner = $null',
    'if (Test-Path -LiteralPath $platformRoot -PathType Container) {',
    "  $scanner = Get-ChildItem -LiteralPath $platformRoot -Directory -ErrorAction Stop | Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'MpCmdRun.exe' } | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1",
    '}',
    'if (-not $scanner) {',
    "  $legacyScanner = Join-Path $env:ProgramFiles 'Windows Defender\\MpCmdRun.exe'",
    '  if (Test-Path -LiteralPath $legacyScanner -PathType Leaf) { $scanner = $legacyScanner }',
    '}',
    '[ordered]@{',
    '  archiveScanningDisabled = [bool]$preferences.DisableArchiveScanning',
    '  removedWholeDriveExclusions = [int]$removedWholeDriveExclusions',
    '  scannerPath = [string]$scanner',
    '} | ConvertTo-Json -Compress',
  ].join('\n');
}

function defenderStatusScript() {
  return [
    "$ErrorActionPreference = 'Stop'",
    'Import-Module Defender -ErrorAction Stop',
    '$status = Get-MpComputerStatus -ErrorAction Stop',
    '$preferences = Get-MpPreference -ErrorAction Stop',
    "$platformRoot = Join-Path $env:ProgramData 'Microsoft\\Windows Defender\\Platform'",
    '$scanner = $null',
    'if (Test-Path -LiteralPath $platformRoot -PathType Container) {',
    "  $scanner = Get-ChildItem -LiteralPath $platformRoot -Directory -ErrorAction Stop | Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'MpCmdRun.exe' } | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1",
    '}',
    'if (-not $scanner) {',
    "  $legacyScanner = Join-Path $env:ProgramFiles 'Windows Defender\\MpCmdRun.exe'",
    '  if (Test-Path -LiteralPath $legacyScanner -PathType Leaf) { $scanner = $legacyScanner }',
    '}',
    '[ordered]@{',
    '  amServiceEnabled = [bool]$status.AMServiceEnabled',
    '  antivirusEnabled = [bool]$status.AntivirusEnabled',
    '  amRunningMode = [string]$status.AMRunningMode',
    '  antivirusSignatureAge = [int]$status.AntivirusSignatureAge',
    "  antivirusSignatureLastUpdatedUtc = if ($status.AntivirusSignatureLastUpdated) { $status.AntivirusSignatureLastUpdated.ToUniversalTime().ToString('o') } else { '' }",
    '  antivirusSignatureVersion = [string]$status.AntivirusSignatureVersion',
    '  amEngineVersion = [string]$status.AMEngineVersion',
    '  amProductVersion = [string]$status.AMProductVersion',
    '  disableArchiveScanning = [bool]$preferences.DisableArchiveScanning',
    '  scannerPath = [string]$scanner',
    '} | ConvertTo-Json -Compress',
  ].join('\n');
}

function defaultRunPowerShell(script) {
  return spawnSync(
    'powershell.exe',
    ['-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command', script],
    {
      encoding: 'utf8',
      maxBuffer: 2 * 1024 * 1024,
      timeout: 15 * 60 * 1000,
      windowsHide: true,
    },
  );
}

function boundedProcessToken(value) {
  if (typeof value !== 'string') return null;
  const token = value.trim();
  if (!token) return null;
  return /^[a-z0-9._-]{1,64}$/i.test(token) ? token : 'UNRECOGNIZED';
}

function describeProcessFailure(stage, result, attempts = null) {
  const failure = {
    stage,
    exitCode: Number.isInteger(result?.status) ? result.status : null,
    signal: boundedProcessToken(result?.signal),
    errorCode: boundedProcessToken(result?.error?.code),
  };
  if (Number.isInteger(attempts) && attempts > 0) failure.attempts = attempts;
  return failure;
}

function runProcessSafely(run) {
  try {
    return run();
  } catch (error) {
    return { status: null, error };
  }
}

function failProcess(reasonCode, message, stage, result, attempts = null) {
  throw new MalwareScanError(
    reasonCode,
    message,
    describeProcessFailure(stage, result, attempts),
  );
}

function defaultRunScanner(scannerPath, args) {
  return spawnSync(scannerPath, args, {
    encoding: 'utf8',
    maxBuffer: 4 * 1024 * 1024,
    timeout: 60 * 60 * 1000,
    windowsHide: true,
  });
}

function defaultSleep(milliseconds) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, milliseconds);
}

function updateDefenderSignatures(runScanner, scannerPath, sleep) {
  let result = null;
  for (let attempt = 1; attempt <= SIGNATURE_UPDATE_MAX_ATTEMPTS; attempt += 1) {
    result = runProcessSafely(
      () => runScanner(scannerPath, ['-SignatureUpdate', '-MMPC']),
    );
    if (result?.status === 0) return { attempts: attempt, result };
    if (attempt < SIGNATURE_UPDATE_MAX_ATTEMPTS) {
      sleep(SIGNATURE_UPDATE_RETRY_DELAY_MS);
    }
  }
  return { attempts: SIGNATURE_UPDATE_MAX_ATTEMPTS, result };
}

function validateDefenderStatus(status) {
  if (!status || typeof status !== 'object') {
    fail('defender_status_invalid', 'Microsoft Defender returned invalid status data.');
  }
  if (status.amServiceEnabled !== true) {
    fail('defender_service_disabled', 'Microsoft Defender antimalware service is disabled.');
  }
  if (status.antivirusEnabled !== true) {
    fail('defender_antivirus_disabled', 'Microsoft Defender Antivirus is disabled.');
  }
  if (status.amRunningMode !== 'Normal') {
    fail('defender_not_normal', 'Microsoft Defender is not running in Normal mode.');
  }
  if (status.disableArchiveScanning !== false) {
    fail('defender_archive_scanning_disabled', 'Microsoft Defender archive scanning is disabled.');
  }
  if (!Number.isInteger(status.antivirusSignatureAge) ||
      status.antivirusSignatureAge < 0 ||
      status.antivirusSignatureAge > MAX_SIGNATURE_AGE_DAYS) {
    fail('defender_signatures_stale', 'Microsoft Defender security intelligence is stale.');
  }
  for (const field of [
    'antivirusSignatureLastUpdatedUtc',
    'antivirusSignatureVersion',
    'amEngineVersion',
    'amProductVersion',
  ]) {
    if (typeof status[field] !== 'string' || !status[field].trim()) {
      fail('defender_identity_missing', 'Microsoft Defender identity metadata is incomplete.');
    }
  }
  if (typeof status.scannerPath !== 'string' ||
      !status.scannerPath.trim() ||
      !fs.existsSync(status.scannerPath) ||
      !fs.lstatSync(status.scannerPath).isFile()) {
    fail('defender_scanner_missing', 'Microsoft Defender MpCmdRun.exe is unavailable.');
  }
  return {
    amRunningMode: status.amRunningMode,
    amEngineVersion: status.amEngineVersion,
    amProductVersion: status.amProductVersion,
    antivirusSignatureVersion: status.antivirusSignatureVersion,
    antivirusSignatureAge: status.antivirusSignatureAge,
    antivirusSignatureLastUpdatedUtc: status.antivirusSignatureLastUpdatedUtc,
    archiveScanningEnabled: true,
  };
}

function parseProcessJson(result, reasonCode, message) {
  if (!result || result.status !== 0 || typeof result.stdout !== 'string') {
    return null;
  }
  try {
    return JSON.parse(result.stdout.trim());
  } catch (_error) {
    fail(reasonCode, message);
  }
}

function validateEnvironmentPreparation(preparation) {
  if (!preparation || typeof preparation !== 'object') {
    fail('defender_environment_invalid', 'Microsoft Defender environment preparation returned invalid data.');
  }
  if (preparation.archiveScanningDisabled !== false) {
    fail('defender_archive_scanning_disabled', 'Microsoft Defender archive scanning is disabled.');
  }
  if (!Number.isInteger(preparation.removedWholeDriveExclusions) ||
      preparation.removedWholeDriveExclusions < 0 ||
      preparation.removedWholeDriveExclusions > 2) {
    fail('defender_environment_invalid', 'Microsoft Defender environment preparation returned invalid data.');
  }
  if (typeof preparation.scannerPath !== 'string' ||
      !preparation.scannerPath.trim() ||
      !fs.existsSync(preparation.scannerPath) ||
      !fs.lstatSync(preparation.scannerPath).isFile()) {
    fail('defender_scanner_missing', 'Microsoft Defender MpCmdRun.exe is unavailable.');
  }
  return {
    archiveScanningEnabled: true,
    removedWholeDriveExclusions: preparation.removedWholeDriveExclusions,
    scannerPath: preparation.scannerPath,
  };
}

function writeReport(reportPath, report) {
  const temporaryPath = `${reportPath}.tmp-${process.pid}`;
  fs.writeFileSync(temporaryPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  fs.renameSync(temporaryPath, reportPath);
}

function runWindowsDefenderScan(options, dependencies = {}) {
  const reportPath = path.resolve(String(options.reportPath || ''));
  const reportDirectory = path.dirname(reportPath);
  if (!options.reportPath || !fs.existsSync(reportDirectory) || !fs.lstatSync(reportDirectory).isDirectory()) {
    fail('report_directory_missing', 'Defender report directory must already exist.');
  }
  const now = dependencies.now || (() => new Date());
  const runEnvironmentPreparation = dependencies.runEnvironmentPreparation ||
    ((script) => defaultRunPowerShell(script));
  const runStatusQuery = dependencies.runStatusQuery ||
    ((script) => defaultRunPowerShell(script));
  const runScanner = dependencies.runScanner || defaultRunScanner;
  const sleep = dependencies.sleep || defaultSleep;
  const head = String(options.head || '').toLowerCase();
  const startedAtUtc = now().toISOString();
  const baseReport = {
    schemaVersion: 1,
    productId: 'com.hanchanqaq.pp02.aidailystockanalysis',
    head,
    startedAtUtc,
  };
  let defender = null;
  let environment = null;
  let targetReports = [];

  try {
    if (options.platform !== 'win32') {
      fail('unsupported_platform', 'Microsoft Defender scanning requires Windows.');
    }
    if (!HEAD_PATTERN.test(head)) {
      fail('invalid_head', 'Defender scanning requires an exact 40-character Git Head.');
    }
    if (!Array.isArray(options.targets) || options.targets.length === 0) {
      fail('scan_targets_missing', 'At least one Defender scan target is required.');
    }
    const targets = options.targets.map(describeTarget);
    targetReports = targets.map((target) => ({
      ...target.report,
      exclusionStatus: 'NOT_CHECKED',
      exclusionExitCode: null,
      scanStatus: 'NOT_RUN',
      scanExitCode: null,
    }));
    const preparationResult = runProcessSafely(
      () => runEnvironmentPreparation(defenderEnvironmentPreparationScript()),
    );
    if (!preparationResult || preparationResult.status !== 0) {
      failProcess(
        'defender_environment_prepare_failed',
        'Microsoft Defender environment preparation failed.',
        'environment_prepare',
        preparationResult,
      );
    }
    const rawPreparation = parseProcessJson(
      preparationResult,
      'defender_environment_invalid',
      'Microsoft Defender environment preparation returned invalid data.',
    );
    const prepared = validateEnvironmentPreparation(rawPreparation);
    environment = {
      archiveScanningEnabled: prepared.archiveScanningEnabled,
      removedWholeDriveExclusions: prepared.removedWholeDriveExclusions,
    };
    const signatureUpdate = updateDefenderSignatures(
      runScanner,
      prepared.scannerPath,
      sleep,
    );
    environment.signatureUpdateAttempts = signatureUpdate.attempts;
    if (!signatureUpdate.result || signatureUpdate.result.status !== 0) {
      failProcess(
        'defender_signature_update_failed',
        'Microsoft Defender security intelligence update failed.',
        'mmpc_signature_update',
        signatureUpdate.result,
        signatureUpdate.attempts,
      );
    }
    const statusResult = runProcessSafely(() => runStatusQuery(defenderStatusScript()));
    if (!statusResult || statusResult.status !== 0 || typeof statusResult.stdout !== 'string') {
      failProcess(
        'defender_status_query_failed',
        'Microsoft Defender status query failed.',
        'status_query',
        statusResult,
      );
    }
    const rawStatus = parseProcessJson(
      statusResult,
      'defender_status_invalid',
      'Microsoft Defender returned invalid status data.',
    );
    defender = validateDefenderStatus(rawStatus);
    for (let index = 0; index < targets.length; index += 1) {
      const target = targets[index];
      const exclusionResult = runProcessSafely(
        () => runScanner(rawStatus.scannerPath, [
          '-CheckExclusion',
          '-Path',
          target.resolved,
        ]),
      );
      const exclusionExitCode = Number.isInteger(exclusionResult?.status)
        ? exclusionResult.status
        : null;
      targetReports[index].exclusionExitCode = exclusionExitCode;
      if (exclusionExitCode === 0) {
        targetReports[index].exclusionStatus = 'EXCLUDED';
        fail('scan_target_excluded', 'A required Defender scan target is excluded from scanning.');
      }
      if (exclusionExitCode !== 1) {
        targetReports[index].exclusionStatus = 'CHECK_FAILED';
        fail('scan_target_exclusion_check_failed', 'Defender could not prove that a scan target is included.');
      }
      targetReports[index].exclusionStatus = 'NOT_EXCLUDED';
      let scanResult;
      try {
        scanResult = runScanner(rawStatus.scannerPath, [
          '-Scan',
          '-ScanType',
          '3',
          '-File',
          target.resolved,
          '-DisableRemediation',
        ]);
      } catch (_error) {
        targetReports[index].scanStatus = 'FAIL';
        throw _error;
      }
      const scanExitCode = Number.isInteger(scanResult?.status)
        ? scanResult.status
        : null;
      targetReports[index].scanExitCode = scanExitCode;
      if (scanExitCode !== 0) {
        targetReports[index].scanStatus = 'FAIL';
        fail('threat_detected_or_scan_failed', 'Microsoft Defender reported a threat or scan failure.');
      }
      targetReports[index].scanStatus = 'PASS';
    }
    const report = {
      ...baseReport,
      completedAtUtc: now().toISOString(),
      status: 'PASS',
      environment,
      defender,
      targets: targetReports,
    };
    writeReport(reportPath, report);
    return report;
  } catch (error) {
    const failure = error instanceof MalwareScanError
      ? error
      : new MalwareScanError('unexpected_scan_failure', 'Unexpected Defender scan failure.');
    writeReport(reportPath, {
      ...baseReport,
      completedAtUtc: now().toISOString(),
      status: 'FAIL',
      reasonCode: failure.reasonCode,
      ...(failure.processFailure ? { processFailure: failure.processFailure } : {}),
      ...(environment ? { environment } : {}),
      ...(defender ? { defender } : {}),
      targets: targetReports,
    });
    throw failure;
  }
}

function parseArguments(argv) {
  let head = '';
  let reportPath = '';
  const targets = [];
  for (let index = 0; index < argv.length; index += 1) {
    const name = argv[index];
    const value = argv[index + 1] || '';
    if (name === '--head') head = value;
    else if (name === '--report') reportPath = value;
    else if (name === '--path') targets.push(value);
    else fail('invalid_arguments', 'Unknown Defender scan argument.');
    index += 1;
  }
  return { head, reportPath, targets };
}

function main() {
  const options = parseArguments(process.argv.slice(2));
  const report = runWindowsDefenderScan({ ...options, platform: process.platform });
  process.stdout.write('PP02_WINDOWS_DEFENDER_SCAN=PASS\n');
  process.stdout.write(`PP02_WINDOWS_DEFENDER_SCAN_HEAD=${report.head}\n`);
  process.stdout.write(`PP02_WINDOWS_DEFENDER_SIGNATURE=${report.defender.antivirusSignatureVersion}\n`);
  process.stdout.write(`PP02_WINDOWS_DEFENDER_TARGETS=${report.targets.length}\n`);
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    process.stderr.write('PP02_WINDOWS_DEFENDER_SCAN=FAIL\n');
    process.stderr.write(`PP02_WINDOWS_DEFENDER_REASON=${error.reasonCode || 'unexpected_scan_failure'}\n`);
    process.exitCode = 1;
  }
}

module.exports = {
  MalwareScanError,
  defenderEnvironmentPreparationScript,
  describeTarget,
  runWindowsDefenderScan,
  validateEnvironmentPreparation,
  validateDefenderStatus,
};
