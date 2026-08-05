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
if (-not (Test-Path -LiteralPath $verifier -PathType Leaf)) {
  throw 'Windows installer verifier script is missing.'
}

$fixtureRoot = Join-Path ([IO.Path]::GetTempPath()) (
  'pp02-installer-contract-' + [guid]::NewGuid().ToString('N')
)
$fakeInstaller = Join-Path $fixtureRoot 'fake-installer.exe'
$installRoot = Join-Path $fixtureRoot (
  'pp02-installer-verify-contract-' + [guid]::NewGuid().ToString('N')
)
$diagnosticRoot = Join-Path $fixtureRoot (
  'pp02-installer-diagnostics-contract-' + [guid]::NewGuid().ToString('N')
)
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

  $contractStage = 'owned_process_helper'
  $powerShell = (Get-Process -Id $PID).Path
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
