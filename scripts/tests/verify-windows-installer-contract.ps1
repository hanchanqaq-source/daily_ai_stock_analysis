param(
  [string]$ArtifactDiagnosticRoot = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw 'Windows installer verifier contract requires a Windows host.'
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$verifier = Join-Path $repoRoot 'scripts/verify-windows-installer.ps1'
$boundedProcessHelper = Join-Path $repoRoot 'scripts/windows-bounded-process.ps1'
$installedConfigMock = Join-Path `
  $repoRoot 'apps/dsa-desktop/tests/installed-config-smoke-server.js'
$installedConfigVaultHarness = Join-Path `
  $repoRoot 'apps/dsa-desktop/tests/windows-installed-config-vault-harness.js'
foreach ($requiredVerifierFile in @(
  $verifier,
  $boundedProcessHelper,
  $installedConfigMock,
  $installedConfigVaultHarness
)) {
  if (-not (Test-Path -LiteralPath $requiredVerifierFile -PathType Leaf)) {
    throw 'Windows installer verifier contract source is missing.'
  }
}

$fixtureRoot = Join-Path ([IO.Path]::GetTempPath()) (
  'pp02-installer-contract-' + [guid]::NewGuid().ToString('N')
)
$fakeInstaller = Join-Path $fixtureRoot 'fake-installer.exe'
$fakeMalwareScanner = Join-Path $fixtureRoot 'fake-malware-scanner.js'
$neverMalwareScanner = Join-Path $fixtureRoot 'never-malware-scanner.js'
$installRoot = Join-Path $fixtureRoot (
  'pp02-installer-verify-contract-' + [guid]::NewGuid().ToString('N')
)
$diagnosticRoot = Join-Path $fixtureRoot (
  'pp02-installer-diagnostics-contract-' + [guid]::NewGuid().ToString('N')
)
$malwareReportRoot = Join-Path $fixtureRoot (
  'pp02-defender-reports-contract-' + [guid]::NewGuid().ToString('N')
)
$malwareReportPath = Join-Path $malwareReportRoot 'installed.json'
$preinstallReportPath = Join-Path $malwareReportRoot 'defender-preinstall.json'
$fakeBlockmap = "$fakeInstaller.blockmap"
$fakeLatest = Join-Path $fixtureRoot 'latest.yml'
$fakePortableZip = Join-Path $fixtureRoot 'fake-portable.zip'
$fakePortableChecksum = "$fakePortableZip.sha256"
$fakeWinUnpacked = Join-Path $fixtureRoot 'win-unpacked'
$fakePortablePayload = Join-Path $fixtureRoot 'portable-payload'
$parentSentinel = Join-Path $fixtureRoot 'parent-sentinel.txt'
$previousRunnerTemp = [Environment]::GetEnvironmentVariable('RUNNER_TEMP', 'Process')
$previousInstallerDiagnosticRoot = [Environment]::GetEnvironmentVariable(
  'DSA_INSTALLER_DIAGNOSTIC_ROOT',
  'Process'
)
$contractStage = 'contract_setup'
$contractOutput = @()
$helperProcesses = @()

function Protect-ContractText {
  param([AllowEmptyString()][string]$Text)

  if ([string]::IsNullOrEmpty($Text)) {
    return ''
  }
  $sensitiveKey = '(?:api[_-]?key|token|secret|password|passwd|webhook|authorization|cookie|credential)'
  $protected = [regex]::Replace(
    $Text,
    "(?im)($sensitiveKey\s*[:=]\s*)([^\s,;]+)",
    '$1<redacted>'
  )
  $protected = [regex]::Replace(
    $protected,
    "(?i)([?&]$sensitiveKey=)[^&\s]+",
    '$1<redacted>'
  )
  $protected = [regex]::Replace(
    $protected,
    '(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+',
    '$1<redacted>'
  )
  $protected = [regex]::Replace(
    $protected,
    '\b(?:sk-[A-Za-z0-9_-]{8,}|gh[opsu]_[A-Za-z0-9_]{12,})\b',
    '<redacted>',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
  )
  return $protected
}

$fakeInstallerSource = @'
using System;
using System.IO;

public static class FakeInstaller {
  public static int Main(string[] args) {
    string installRoot = null;
    foreach (string arg in args) {
      if (arg.StartsWith("/D=", StringComparison.OrdinalIgnoreCase)) {
        installRoot = arg.Substring(3);
      }
    }
    if (String.IsNullOrWhiteSpace(installRoot)) return 91;
    Directory.CreateDirectory(installRoot);
    File.WriteAllText(Path.Combine(installRoot, "created-by-fake-installer.txt"), "owned");
    return 17;
  }
}
'@

try {
  New-Item -ItemType Directory -Path $fixtureRoot -Force | Out-Null
  Set-Content -LiteralPath $parentSentinel -Value 'preserve' -Encoding ASCII
  Add-Type -TypeDefinition $fakeInstallerSource -Language CSharp `
    -OutputAssembly $fakeInstaller -OutputType ConsoleApplication
  New-Item -ItemType Directory -Path $malwareReportRoot -Force | Out-Null
  foreach ($fixtureDirectory in @($fakeWinUnpacked, $fakePortablePayload)) {
    New-Item -ItemType Directory -Path $fixtureDirectory -Force | Out-Null
  }
  Set-Content -LiteralPath $fakeBlockmap -Value 'contract-blockmap' -Encoding ASCII
  Set-Content -LiteralPath $fakeLatest -Value 'version: 9.9.9' -Encoding ASCII
  Set-Content `
    -LiteralPath (Join-Path $fakeWinUnpacked 'contract.txt') `
    -Value 'unpacked' `
    -Encoding ASCII
  Set-Content `
    -LiteralPath (Join-Path $fakePortablePayload 'contract.txt') `
    -Value 'portable' `
    -Encoding ASCII
  Compress-Archive `
    -Path (Join-Path $fakePortablePayload '*') `
    -DestinationPath $fakePortableZip
  $portableHash = (Get-FileHash -LiteralPath $fakePortableZip -Algorithm SHA256).Hash.ToLowerInvariant()
  Set-Content `
    -LiteralPath $fakePortableChecksum `
    -Value "$portableHash  $(Split-Path -Leaf $fakePortableZip)" `
    -Encoding ASCII

  $verifierText = Get-Content -LiteralPath $verifier -Raw
  foreach ($installedAcceptanceContract in @(
    '/api/v1/system/config/validate',
    '/api/v1/system/config/generation-backends/smoke-test',
    '/api/v1/system/full-data-backup/export',
    'WINDOWS_INSTALLED_USER_DATA_ISOLATION=PASS',
    'WINDOWS_INSTALLED_CONFIG_MASKED_RESTART=PASS',
    'WINDOWS_INSTALLED_CONFIG_LEAKAGE_SCAN=PASS'
  )) {
    if (-not $verifierText.Contains($installedAcceptanceContract)) {
      throw 'Installed configuration acceptance verifier contract is incomplete.'
    }
  }
  if (-not $verifierText.Contains('pp02-r37-[0-9a-f]{64}')) {
    throw 'Installed configuration synthetic credential diagnostics are not redacted.'
  }
  if (([regex]::Matches($verifierText, '--user-data-dir=')).Count -ne 2 -or
      $verifierText.Contains(
        'Get-ChildItem -LiteralPath $acceptanceAppData -Directory'
      )) {
    throw 'Installed configuration userData isolation contract is incomplete.'
  }
  Write-Output 'WINDOWS_INSTALLED_CONFIG_ACCEPTANCE_CONTRACT=PASS'

  $contractStage = 'bounded_process_helper'
  . $boundedProcessHelper
  $powerShell = (Get-Process -Id $PID).Path
  $boundedStageReport = Join-Path $fixtureRoot 'bounded-process-stage-report.txt'
  Set-Content `
    -LiteralPath $boundedStageReport `
    -Value 'WINDOWS_BOUNDED_PROCESS_STAGE_REPORT=AVAILABLE' `
    -Encoding UTF8
  $boundedSuccess = Invoke-PP02BoundedProcess `
    -FilePath $powerShell `
    -ArgumentList @('-NoLogo', '-NoProfile', '-NonInteractive', '-Command', 'exit 0') `
    -TimeoutSeconds 10 `
    -Stage 'bounded_process_success' `
    -StageReportPath $boundedStageReport
  if ($boundedSuccess.ExitCode -ne 0) {
    throw 'Bounded process rejected a successful child.'
  }
  Write-Output 'WINDOWS_BOUNDED_PROCESS_SUCCESS_CONTRACT=PASS'

  $timeoutPidPath = Join-Path $fixtureRoot 'bounded-process-timeout.pid'
  $escapedTimeoutPidPath = $timeoutPidPath.Replace("'", "''")
  $timeoutScript = "`$PID | Set-Content -LiteralPath '$escapedTimeoutPidPath'; Start-Sleep -Seconds 30"
  $timeoutEncoded = [Convert]::ToBase64String(
    [Text.Encoding]::Unicode.GetBytes($timeoutScript)
  )
  $boundedTimedOut = $false
  try {
    Invoke-PP02BoundedProcess `
      -FilePath $powerShell `
      -ArgumentList @('-NoLogo', '-NoProfile', '-NonInteractive', '-EncodedCommand', $timeoutEncoded) `
      -TimeoutSeconds 1 `
      -Stage 'bounded_process' `
      -StageReportPath $boundedStageReport | Out-Null
  }
  catch {
    $boundedTimedOut = $_.Exception.Message.Contains('exceeded its bounded timeout')
  }
  if (-not $boundedTimedOut) {
    throw 'Bounded process did not reject a timed-out child.'
  }
  if (-not (Test-Path -LiteralPath $timeoutPidPath -PathType Leaf)) {
    throw 'Bounded process timeout fixture did not record its child PID.'
  }
  $timeoutProcessId = [int](Get-Content -LiteralPath $timeoutPidPath -Raw).Trim()
  if (Get-Process -Id $timeoutProcessId -ErrorAction SilentlyContinue) {
    throw 'Bounded process leaked its timed-out child.'
  }
  $boundedStageText = Get-Content -LiteralPath $boundedStageReport -Raw
  if (-not $boundedStageText.Contains('bounded_process status=TIMEOUT')) {
    throw 'Bounded process did not preserve its timeout stage evidence.'
  }
  Write-Output 'WINDOWS_BOUNDED_PROCESS_TIMEOUT_CONTRACT=PASS'

  $invalidTimeoutRejected = $false
  try {
    Invoke-PP02BoundedProcess `
      -FilePath $powerShell `
      -TimeoutSeconds 0 `
      -Stage 'bounded_process_invalid' `
      -StageReportPath $boundedStageReport | Out-Null
  }
  catch {
    $invalidTimeoutRejected = $_.Exception.Message.Contains(
      'TimeoutSeconds must be between 1 and 1800'
    )
  }
  if (-not $invalidTimeoutRejected) {
    throw 'Bounded process accepted an invalid timeout.'
  }
  Write-Output 'WINDOWS_BOUNDED_PROCESS_INVALID_TIMEOUT_CONTRACT=PASS'

  $fakeMalwareScannerSource = @'
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const args = process.argv.slice(2);
function value(name) {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : '';
}
const head = value('--head');
const report = value('--report');
const targets = [];
for (let index = 0; index < args.length; index += 1) {
  if (args[index] === '--path') targets.push(args[index + 1]);
}
if (!head || !report || targets.length === 0) process.exit(93);
fs.mkdirSync(path.dirname(report), { recursive: true });
fs.writeFileSync(report, JSON.stringify({ status: 'PASS', head, targets }, null, 2));
'@
  Set-Content `
    -LiteralPath $fakeMalwareScanner `
    -Value $fakeMalwareScannerSource `
    -Encoding UTF8
  Set-Content `
    -LiteralPath $neverMalwareScanner `
    -Value "'use strict'; process.exit(94);" `
    -Encoding UTF8
  $expectedCommitSha = (& git -C $repoRoot rev-parse HEAD).Trim().ToLowerInvariant()
  if ($LASTEXITCODE -ne 0 -or $expectedCommitSha -notmatch '^[0-9a-f]{40}$') {
    throw 'Unable to resolve contract fixture commit.'
  }

  $contractStage = 'owned_process_helper'
  $helperSource = Join-Path $repoRoot 'apps/dsa-desktop/windows/close-owned-processes.ps1'
  $manifestSource = Join-Path $repoRoot 'apps/dsa-desktop/windows/owned-processes.json'
  foreach ($requiredSource in @($helperSource, $manifestSource)) {
    if (-not (Test-Path -LiteralPath $requiredSource -PathType Leaf)) {
      throw 'Owned-process helper contract source is missing.'
    }
  }

  $helperInstallRoot = Join-Path $fixtureRoot 'owned-helper-install'
  $helperResources = Join-Path $helperInstallRoot 'resources'
  $helperBackendRoot = Join-Path $helperResources 'backend/stock_analysis'
  $helperExternalRoot = Join-Path $fixtureRoot 'external-control'
  $helperDiagnosticRoot = Join-Path $fixtureRoot (
    'pp02-installer-diagnostics-helper-' + [guid]::NewGuid().ToString('N')
  )
  foreach ($directory in @(
    $helperResources,
    $helperBackendRoot,
    $helperExternalRoot,
    $helperDiagnosticRoot
  )) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
  }

  $installedHelper = Join-Path $helperResources 'close-owned-processes.ps1'
  $installedManifest = Join-Path $helperResources 'owned-processes.json'
  $ownedDesktop = Join-Path $helperInstallRoot 'PP02 AI Daily Stock Analysis.exe'
  $ownedBackend = Join-Path $helperBackendRoot 'stock_analysis.exe'
  $externalDesktop = Join-Path $helperExternalRoot 'PP02 AI Daily Stock Analysis.exe'
  Copy-Item -LiteralPath $helperSource -Destination $installedHelper
  Copy-Item -LiteralPath $manifestSource -Destination $installedManifest
  foreach ($executablePath in @($ownedDesktop, $ownedBackend, $externalDesktop)) {
    Copy-Item -LiteralPath $powerShell -Destination $executablePath
  }

  $sleepArguments = @(
    '-NoLogo',
    '-NoProfile',
    '-NonInteractive',
    '-Command',
    'Start-Sleep -Seconds 120'
  )
  $ownedDesktopProcess = Start-Process `
    -FilePath $ownedDesktop -ArgumentList $sleepArguments -PassThru
  $ownedBackendProcess = Start-Process `
    -FilePath $ownedBackend -ArgumentList $sleepArguments -PassThru
  $externalDesktopProcess = Start-Process `
    -FilePath $externalDesktop -ArgumentList $sleepArguments -PassThru
  $helperProcesses = @(
    $ownedDesktopProcess,
    $ownedBackendProcess,
    $externalDesktopProcess
  )
  Start-Sleep -Milliseconds 750
  foreach ($helperProcess in $helperProcesses) {
    $helperProcess.Refresh()
    if ($helperProcess.HasExited) {
      throw 'Owned-process helper contract fixture exited before validation.'
    }
  }

  [Environment]::SetEnvironmentVariable(
    'DSA_INSTALLER_DIAGNOSTIC_ROOT',
    $helperDiagnosticRoot,
    'Process'
  )
  $helperStdoutPath = Join-Path $fixtureRoot 'owned-helper.stdout.log'
  $helperStderrPath = Join-Path $fixtureRoot 'owned-helper.stderr.log'
  $helperArguments = @(
    '-NoLogo'
    '-NoProfile'
    '-NonInteractive'
    '-ExecutionPolicy'
    'Bypass'
    '-File'
    ('"{0}"' -f $installedHelper)
  )
  $helperContractProcess = Start-Process `
    -FilePath $powerShell `
    -ArgumentList $helperArguments `
    -Wait `
    -PassThru `
    -RedirectStandardOutput $helperStdoutPath `
    -RedirectStandardError $helperStderrPath
  $helperOutput = @()
  foreach ($streamPath in @($helperStdoutPath, $helperStderrPath)) {
    if (Test-Path -LiteralPath $streamPath -PathType Leaf) {
      $helperOutput += @(
        Get-Content -LiteralPath $streamPath |
          ForEach-Object { $_.ToString() }
      )
    }
  }
  $helperExitCode = $helperContractProcess.ExitCode
  if ($helperExitCode -ne 0) {
    throw "Owned-process helper returned code $helperExitCode."
  }
  foreach ($ownedProcess in @($ownedDesktopProcess, $ownedBackendProcess)) {
    $ownedProcess.Refresh()
    if (-not $ownedProcess.HasExited) {
      throw 'Owned-process helper left an exact owned process running.'
    }
  }
  $externalDesktopProcess.Refresh()
  if ($externalDesktopProcess.HasExited) {
    throw 'Owned-process helper stopped the external same-name control process.'
  }
  if (-not ($helperOutput -contains 'PP02_OWNED_PROCESS_EXIT_VALIDATION=PASS')) {
    throw 'Owned-process helper did not emit its stable validation marker.'
  }
  $helperEvidencePath = Join-Path `
    $helperDiagnosticRoot 'owned-process-cleanup-evidence.json'
  if (-not (Test-Path -LiteralPath $helperEvidencePath -PathType Leaf)) {
    throw 'Owned-process helper did not preserve execution evidence.'
  }
  $helperEvidence = Get-Content -LiteralPath $helperEvidencePath -Raw |
    ConvertFrom-Json
  if ([string]$helperEvidence.status -ne 'PASS' -or
      [int]$helperEvidence.initialOwnedProcessCount -ne 2 -or
      [int]$helperEvidence.remainingOwnedProcessCount -ne 0) {
    throw 'Owned-process helper evidence did not prove exact cleanup.'
  }
  Write-Output 'WINDOWS_OWNED_PROCESS_HELPER_CONTRACT=PASS'

  [Environment]::SetEnvironmentVariable(
    'DSA_INSTALLER_DIAGNOSTIC_ROOT',
    $previousInstallerDiagnosticRoot,
    'Process'
  )

  [Environment]::SetEnvironmentVariable('RUNNER_TEMP', $fixtureRoot, 'Process')
  $contractStage = 'child_verifier'
  $stdoutPath = Join-Path $fixtureRoot 'verifier.stdout.log'
  $stderrPath = Join-Path $fixtureRoot 'verifier.stderr.log'
  $arguments = @(
    '-NoLogo'
    '-NoProfile'
    '-NonInteractive'
    '-ExecutionPolicy'
    'Bypass'
    '-File'
    ('"{0}"' -f $verifier)
    '-InstallerPath'
    ('"{0}"' -f $fakeInstaller)
    '-ExpectedVersion'
    '9.9.9'
    '-InstallRoot'
    ('"{0}"' -f $installRoot)
    '-DiagnosticRoot'
    ('"{0}"' -f $diagnosticRoot)
    '-ExpectedCommitSha'
    $expectedCommitSha
    '-MalwareScannerPath'
    ('"{0}"' -f $fakeMalwareScanner)
    '-MalwareReportPath'
    ('"{0}"' -f $malwareReportPath)
    '-PortableArchivePath'
    ('"{0}"' -f $fakePortableZip)
  )
  $contractProcess = Start-Process `
    -FilePath $powerShell `
    -ArgumentList $arguments `
    -Wait `
    -PassThru `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath
  $contractOutput = @()
  foreach ($streamPath in @($stdoutPath, $stderrPath)) {
    if (Test-Path -LiteralPath $streamPath -PathType Leaf) {
      $contractOutput += @(Get-Content -LiteralPath $streamPath | ForEach-Object {
        $_.ToString()
      })
    }
  }
  $verifierExitCode = $contractProcess.ExitCode

  if ($verifierExitCode -eq 0) {
    throw 'Verifier accepted a failing installer.'
  }
  $contractStage = 'contract_assertions'
  if (-not ($contractOutput -contains 'WINDOWS_INSTALLER_VALIDATION=FAIL')) {
    throw 'Verifier did not emit its stable failure marker.'
  }
  if (-not ($contractOutput -contains 'WINDOWS_CANDIDATE_DEFENDER_SCAN=PASS')) {
    throw 'Verifier did not pass its preinstall Defender orchestration contract.'
  }
  if (-not (Test-Path -LiteralPath $preinstallReportPath -PathType Leaf)) {
    throw 'Verifier did not preserve its preinstall Defender report.'
  }
  $preinstallReport = Get-Content -LiteralPath $preinstallReportPath -Raw |
    ConvertFrom-Json
  if ([string]$preinstallReport.status -ne 'PASS' -or
      [string]$preinstallReport.head -ne $expectedCommitSha) {
    throw 'Verifier did not bind the preinstall Defender report to the checked-out Head.'
  }
  if (Test-Path -LiteralPath $installRoot) {
    throw 'Verifier did not clean its owned install root.'
  }
  if (-not (Test-Path -LiteralPath $parentSentinel -PathType Leaf)) {
    throw 'Verifier removed a parent sentinel.'
  }
  $diagnosticSummary = Join-Path $diagnosticRoot 'diagnostic-summary.txt'
  if (-not (Test-Path -LiteralPath $diagnosticSummary -PathType Leaf)) {
    throw 'Verifier did not preserve diagnostic evidence before cleanup.'
  }
  $diagnosticText = Get-Content -LiteralPath $diagnosticSummary -Raw
  if (-not $diagnosticText.Contains('WINDOWS_INSTALLER_DIAGNOSTIC=AVAILABLE')) {
    throw 'Verifier did not preserve its stable diagnostic marker.'
  }
  if (-not $diagnosticText.Contains('failure_stage=installer_process')) {
    throw 'Verifier did not preserve the failing lifecycle stage.'
  }
  if (-not $diagnosticText.Contains('stage_process_exit_code=17')) {
    throw 'Verifier did not preserve the installer exit code.'
  }
  $installedFiles = Join-Path $diagnosticRoot 'installed-files.txt'
  if (-not (Test-Path -LiteralPath $installedFiles -PathType Leaf)) {
    throw 'Verifier did not complete its Windows PowerShell file inventory.'
  }
  $collectorStatus = Join-Path $diagnosticRoot 'diagnostic-collector-status.txt'
  if (-not (Test-Path -LiteralPath $collectorStatus -PathType Leaf)) {
    throw 'Verifier did not preserve collector-level status.'
  }
  $collectorText = Get-Content -LiteralPath $collectorStatus -Raw
  if (-not $collectorText.Contains('installed_files=PASS')) {
    throw 'Verifier did not record the installed-file collector result.'
  }
  if ($diagnosticText.Contains('parent-sentinel') -or $diagnosticText.Contains('owned')) {
    throw 'Verifier copied unrelated fixture content into diagnostic evidence.'
  }

  function Invoke-ExternalPreinstallVerifier {
    param(
      [Parameter(Mandatory=$true)][string]$EvidenceStatus,
      [Parameter(Mandatory=$true)][string]$EvidenceHead,
      [switch]$MissingEvidence,
      [switch]$WrongEvidenceRoot
    )

    $caseId = [guid]::NewGuid().ToString('N')
    $caseReportRoot = Join-Path $fixtureRoot "pp02-defender-reports-external-$caseId"
    $caseEvidenceRoot = $caseReportRoot
    if ($WrongEvidenceRoot) {
      $caseEvidenceRoot = Join-Path $fixtureRoot "pp02-defender-reports-wrong-$caseId"
    }
    foreach ($caseDirectory in @($caseReportRoot, $caseEvidenceRoot)) {
      New-Item -ItemType Directory -Path $caseDirectory -Force | Out-Null
    }
    $casePreinstallReport = Join-Path $caseEvidenceRoot 'preinstall.json'
    if (-not $MissingEvidence) {
      [ordered]@{
        status = $EvidenceStatus
        head = $EvidenceHead
      } | ConvertTo-Json | Set-Content `
        -LiteralPath $casePreinstallReport `
        -Encoding UTF8
    }
    $caseInstalledReport = Join-Path $caseReportRoot 'installed.json'
    $caseInstallRoot = Join-Path $fixtureRoot "pp02-installer-verify-external-$caseId"
    $caseDiagnosticRoot = Join-Path $fixtureRoot "pp02-installer-diagnostics-external-$caseId"
    $caseStdoutPath = Join-Path $fixtureRoot "external-$caseId.stdout.log"
    $caseStderrPath = Join-Path $fixtureRoot "external-$caseId.stderr.log"
    $caseArguments = @(
      '-NoLogo'
      '-NoProfile'
      '-NonInteractive'
      '-ExecutionPolicy'
      'Bypass'
      '-File'
      ('"{0}"' -f $verifier)
      '-InstallerPath'
      ('"{0}"' -f $fakeInstaller)
      '-ExpectedVersion'
      '9.9.9'
      '-InstallRoot'
      ('"{0}"' -f $caseInstallRoot)
      '-DiagnosticRoot'
      ('"{0}"' -f $caseDiagnosticRoot)
      '-ExpectedCommitSha'
      $expectedCommitSha
      '-MalwareScannerPath'
      ('"{0}"' -f $neverMalwareScanner)
      '-MalwareReportPath'
      ('"{0}"' -f $caseInstalledReport)
      '-PreinstallMalwareReportPath'
      ('"{0}"' -f $casePreinstallReport)
    )
    $caseProcess = Start-Process `
      -FilePath $powerShell `
      -ArgumentList $caseArguments `
      -Wait `
      -PassThru `
      -RedirectStandardOutput $caseStdoutPath `
      -RedirectStandardError $caseStderrPath
    $caseOutput = @()
    foreach ($caseStreamPath in @($caseStdoutPath, $caseStderrPath)) {
      if (Test-Path -LiteralPath $caseStreamPath -PathType Leaf) {
        $caseOutput += @(Get-Content -LiteralPath $caseStreamPath | ForEach-Object {
          $_.ToString()
        })
      }
    }
    return [pscustomobject]@{
      ExitCode = $caseProcess.ExitCode
      Output = $caseOutput
      InstallRoot = $caseInstallRoot
      DiagnosticRoot = $caseDiagnosticRoot
    }
  }

  $validExternalEvidence = Invoke-ExternalPreinstallVerifier `
    -EvidenceStatus 'PASS' `
    -EvidenceHead $expectedCommitSha
  if ($validExternalEvidence.ExitCode -eq 0 -or
      -not ($validExternalEvidence.Output -contains 'WINDOWS_CANDIDATE_DEFENDER_SCAN=PASS')) {
    throw 'Valid external preinstall evidence did not reach the controlled installer failure.'
  }
  $validExternalDiagnostic = Join-Path `
    $validExternalEvidence.DiagnosticRoot 'diagnostic-summary.txt'
  if (-not (Test-Path -LiteralPath $validExternalDiagnostic -PathType Leaf) -or
      -not (Get-Content -LiteralPath $validExternalDiagnostic -Raw).Contains(
        'failure_stage=installer_process'
      ) -or
      (Test-Path -LiteralPath $validExternalEvidence.InstallRoot)) {
    throw 'Valid external preinstall evidence did not preserve lifecycle and cleanup contracts.'
  }
  Write-Output 'EXTERNAL_PREINSTALL_EVIDENCE_VALIDATION=PASS'

  $rejectionCases = @(
    @{
      Marker = 'EXTERNAL_PREINSTALL_EVIDENCE_FAIL_REJECTION=PASS'
      Arguments = @{ EvidenceStatus = 'FAIL'; EvidenceHead = $expectedCommitSha }
    },
    @{
      Marker = 'EXTERNAL_PREINSTALL_EVIDENCE_HEAD_REJECTION=PASS'
      Arguments = @{
        EvidenceStatus = 'PASS'
        EvidenceHead = '0000000000000000000000000000000000000000'
      }
    },
    @{
      Marker = 'EXTERNAL_PREINSTALL_EVIDENCE_MISSING_REJECTION=PASS'
      Arguments = @{
        EvidenceStatus = 'PASS'
        EvidenceHead = $expectedCommitSha
        MissingEvidence = $true
      }
    },
    @{
      Marker = 'EXTERNAL_PREINSTALL_EVIDENCE_ROOT_REJECTION=PASS'
      Arguments = @{
        EvidenceStatus = 'PASS'
        EvidenceHead = $expectedCommitSha
        WrongEvidenceRoot = $true
      }
    }
  )
  foreach ($rejectionCase in $rejectionCases) {
    $rejectionArguments = $rejectionCase.Arguments
    $rejectedEvidence = Invoke-ExternalPreinstallVerifier @rejectionArguments
    if ($rejectedEvidence.ExitCode -eq 0 -or
        ($rejectedEvidence.Output -contains 'WINDOWS_CANDIDATE_DEFENDER_SCAN=PASS')) {
      throw "Verifier accepted invalid external preinstall evidence: $($rejectionCase.Marker)."
    }
    Write-Output $rejectionCase.Marker
  }
  Write-Output 'WINDOWS_INSTALLER_CONTRACT_VALIDATION=PASS'
}
catch {
  $contractFailure = $_
  if (-not [string]::IsNullOrWhiteSpace($ArtifactDiagnosticRoot)) {
    try {
      if ([string]::IsNullOrWhiteSpace($previousRunnerTemp)) {
        throw 'RUNNER_TEMP is required for contract diagnostic persistence.'
      }
      $directorySeparators = [char[]]@(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
      )
      $artifactRoot = [IO.Path]::GetFullPath($ArtifactDiagnosticRoot).TrimEnd(
        $directorySeparators
      )
      $runnerRoot = [IO.Path]::GetFullPath($previousRunnerTemp).TrimEnd(
        $directorySeparators
      )
      $runnerPrefix = $runnerRoot + [IO.Path]::DirectorySeparatorChar
      $artifactLeaf = Split-Path -Leaf $artifactRoot
      if (-not $artifactRoot.StartsWith(
          $runnerPrefix,
          [StringComparison]::OrdinalIgnoreCase
        ) -or
          -not $artifactLeaf.StartsWith(
            'pp02-installer-diagnostics-',
            [StringComparison]::OrdinalIgnoreCase
          )) {
        throw 'ArtifactDiagnosticRoot must be a verifier diagnostic child of RUNNER_TEMP.'
      }
      New-Item -ItemType Directory -Path $artifactRoot -Force | Out-Null
      $safeFailureMessage = Protect-ContractText -Text $contractFailure.Exception.Message
      Set-Content `
        -LiteralPath (Join-Path $artifactRoot 'diagnostic-summary.txt') `
        -Value @(
          'WINDOWS_INSTALLER_DIAGNOSTIC=CONTRACT_FAILURE',
          'failure_stage=diagnostic_contract',
          "contract_stage=$contractStage",
          "failure_type=$($contractFailure.Exception.GetType().FullName)",
          "failure_message=$safeFailureMessage"
        ) `
        -Encoding UTF8
      Set-Content `
        -LiteralPath (Join-Path $artifactRoot 'stage-report.txt') `
        -Value @(
          'WINDOWS_INSTALLER_STAGE_REPORT=AVAILABLE',
          'current_stage=diagnostic_contract',
          'current_stage_result=FAIL'
        ) `
        -Encoding UTF8
      $safeChildOutput = @(
        $contractOutput |
          Select-Object -Last 160 |
          ForEach-Object { Protect-ContractText -Text $_.ToString() }
      )
      Set-Content `
        -LiteralPath (Join-Path $artifactRoot 'contract-child-output-sanitized.log') `
        -Value $safeChildOutput `
        -Encoding UTF8
      Write-Output 'WINDOWS_INSTALLER_CONTRACT_DIAGNOSTIC=AVAILABLE'
    }
    catch {
      Write-Warning "Contract diagnostic capture failed with $($_.Exception.GetType().FullName)."
    }
  }
  throw $contractFailure
}
finally {
  [Environment]::SetEnvironmentVariable(
    'RUNNER_TEMP',
    $previousRunnerTemp,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_INSTALLER_DIAGNOSTIC_ROOT',
    $previousInstallerDiagnosticRoot,
    'Process'
  )
  foreach ($helperProcess in $helperProcesses) {
    try {
      $helperProcess.Refresh()
      if (-not $helperProcess.HasExited) {
        Stop-Process -Id $helperProcess.Id -Force -ErrorAction SilentlyContinue
      }
    }
    catch {
      # Fixture cleanup is best-effort after the contract result is recorded.
    }
  }
  if (Test-Path -LiteralPath $fixtureRoot) {
    Remove-Item -LiteralPath $fixtureRoot -Recurse -Force -ErrorAction SilentlyContinue
  }
}
