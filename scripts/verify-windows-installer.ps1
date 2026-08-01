param(
  [Parameter(Mandatory=$true)][string]$InstallerPath,
  [Parameter(Mandatory=$true)][string]$ExpectedVersion,
  [Parameter(Mandatory=$true)][string]$InstallRoot,
  [string]$ExpectedCommitSha = '',
  [int]$StartupTimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-NormalizedDirectoryPath {
  param([Parameter(Mandatory=$true)][string]$Path)

  return [IO.Path]::GetFullPath($Path).TrimEnd(
    [char[]]@([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
  )
}

function Test-PathInsideRoot {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Root
  )

  $normalizedPath = Get-NormalizedDirectoryPath -Path $Path
  $normalizedRoot = Get-NormalizedDirectoryPath -Path $Root
  $rootPrefix = $normalizedRoot + [IO.Path]::DirectorySeparatorChar
  return $normalizedPath.StartsWith(
    $rootPrefix,
    [StringComparison]::OrdinalIgnoreCase
  )
}

function Get-OwnedUninstallEntries {
  param([Parameter(Mandatory=$true)][string]$OwnedRoot)

  $registryRoot = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall'
  if (-not (Test-Path -LiteralPath $registryRoot)) {
    return @()
  }

  $normalizedOwnedRoot = Get-NormalizedDirectoryPath -Path $OwnedRoot
  return @(
    Get-ChildItem -LiteralPath $registryRoot -ErrorAction SilentlyContinue |
      ForEach-Object {
        try {
          $entry = Get-ItemProperty -LiteralPath $_.PSPath -ErrorAction Stop
          if ([string]::IsNullOrWhiteSpace([string]$entry.InstallLocation)) {
            return
          }
          $entryRoot = Get-NormalizedDirectoryPath -Path ([string]$entry.InstallLocation)
          if ($entryRoot.Equals($normalizedOwnedRoot, [StringComparison]::OrdinalIgnoreCase)) {
            [pscustomobject]@{
              RegistryPath = $_.PSPath
              InstallLocation = $entryRoot
              DisplayVersion = [string]$entry.DisplayVersion
            }
          }
        }
        catch {
          # Ignore unrelated or concurrently removed uninstall entries.
        }
      }
  )
}

function Stop-StartedProcessTree {
  param([System.Diagnostics.Process]$Process)

  if (-not $Process) {
    return
  }
  try {
    $Process.Refresh()
    if (-not $Process.HasExited) {
      & taskkill.exe /PID $Process.Id /T /F | Out-Null
      try {
        Wait-Process -Id $Process.Id -Timeout 20 -ErrorAction SilentlyContinue
      }
      catch {
        # The final HasExited check below remains authoritative.
      }
      $Process.Refresh()
    }
  }
  catch [System.ArgumentException] {
    return
  }
  if (-not $Process.HasExited) {
    throw "Installed application process tree did not stop: PID $($Process.Id)."
  }
}

function Remove-OwnedRootWithRetry {
  param([Parameter(Mandatory=$true)][string]$OwnedRoot)

  if (-not (Test-Path -LiteralPath $OwnedRoot)) {
    return
  }
  for ($attempt = 1; $attempt -le 15; $attempt++) {
    try {
      Remove-Item -LiteralPath $OwnedRoot -Recurse -Force -ErrorAction Stop
      if (-not (Test-Path -LiteralPath $OwnedRoot)) {
        return
      }
    }
    catch {
      if ($attempt -eq 15) {
        throw "Failed to remove verifier-owned install root after $attempt attempts."
      }
    }
    Start-Sleep -Seconds 1
  }
  throw 'Failed to remove verifier-owned install root.'
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw 'Windows installer verification requires a Windows host.'
}
if ($ExpectedVersion -notmatch '^\d+\.\d+\.\d+$') {
  throw 'ExpectedVersion must be a three-part semantic version.'
}
if ($StartupTimeoutSeconds -lt 10 -or $StartupTimeoutSeconds -gt 600) {
  throw 'StartupTimeoutSeconds must be between 10 and 600.'
}
if ([string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) {
  throw 'RUNNER_TEMP is required to scope installer verification.'
}

$installer = [IO.Path]::GetFullPath($InstallerPath)
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
  throw 'Expected Windows installer was not found.'
}
if ([IO.Path]::GetExtension($installer) -ne '.exe') {
  throw 'Windows installer must be an .exe file.'
}

$runnerTemp = Get-NormalizedDirectoryPath -Path $env:RUNNER_TEMP
$ownedRoot = Get-NormalizedDirectoryPath -Path $InstallRoot
$ownedLeaf = Split-Path -Leaf $ownedRoot
if (-not (Test-PathInsideRoot -Path $ownedRoot -Root $runnerTemp)) {
  throw 'InstallRoot must be a child of RUNNER_TEMP.'
}
if (-not $ownedLeaf.StartsWith('pp02-installer-verify-', [StringComparison]::OrdinalIgnoreCase)) {
  throw 'InstallRoot must use the pp02-installer-verify-* ownership prefix.'
}
if (Test-Path -LiteralPath $ownedRoot) {
  throw 'InstallRoot must not exist before verification.'
}

$expectedHead = $ExpectedCommitSha.Trim().ToLowerInvariant()
if ($expectedHead) {
  if ($expectedHead -notmatch '^[0-9a-f]{40}$') {
    throw 'ExpectedCommitSha must be an exact 40-character Git commit SHA.'
  }
  $currentHead = (& git rev-parse HEAD).Trim().ToLowerInvariant()
  if ($LASTEXITCODE -ne 0 -or $currentHead -notmatch '^[0-9a-f]{40}$') {
    throw 'Unable to resolve the checked-out Git commit.'
  }
  if ($currentHead -ne $expectedHead) {
    throw 'Checked-out commit does not match ExpectedCommitSha.'
  }
}

$appProcess = $null
$uninstaller = $null
$uninstallAttempted = $false
$ownedRootValidated = $true
$savedGithubActions = [Environment]::GetEnvironmentVariable('GITHUB_ACTIONS', 'Process')

try {
  Write-Output "WINDOWS_INSTALLER_EXPECTED_VERSION=$ExpectedVersion"
  if ($expectedHead) {
    Write-Output "WINDOWS_INSTALLER_HEAD=$expectedHead"
  }

  $installProcess = Start-Process -FilePath $installer `
    -ArgumentList "/S /D=$ownedRoot" -Wait -PassThru
  Write-Output "WINDOWS_INSTALLER_EXIT_CODE=$($installProcess.ExitCode)"
  if ($installProcess.ExitCode -ne 0) {
    throw "Installer exited with code $($installProcess.ExitCode)."
  }

  $appExe = Join-Path $ownedRoot 'PP02 AI Daily Stock Analysis.exe'
  $appAsar = Join-Path $ownedRoot 'resources/app.asar'
  $backendExe = Join-Path $ownedRoot 'resources/backend/stock_analysis/stock_analysis.exe'
  foreach ($requiredPath in @($appExe, $appAsar, $backendExe)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
      throw "Installed package is missing required file: $(Split-Path -Leaf $requiredPath)."
    }
  }

  $uninstallers = @(Get-ChildItem -LiteralPath $ownedRoot -Filter 'Uninstall *.exe' -File)
  if ($uninstallers.Count -ne 1) {
    throw "Installed package must contain exactly one uninstaller; found $($uninstallers.Count)."
  }
  $uninstaller = $uninstallers[0].FullName

  $productVersion = (Get-Item -LiteralPath $appExe).VersionInfo.ProductVersion
  $versionMatch = [regex]::Match([string]$productVersion, '^(\d+)\.(\d+)\.(\d+)')
  if (-not $versionMatch.Success -or $versionMatch.Value -ne $ExpectedVersion) {
    throw "Installed executable version does not match $ExpectedVersion."
  }

  $registryDeadline = (Get-Date).AddSeconds(20)
  do {
    $ownedEntries = @(Get-OwnedUninstallEntries -OwnedRoot $ownedRoot)
    if ($ownedEntries.Count -eq 1) {
      break
    }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $registryDeadline)
  if ($ownedEntries.Count -ne 1) {
    throw "Expected exactly one HKCU uninstall entry for the owned root; found $($ownedEntries.Count)."
  }
  Write-Output 'WINDOWS_INSTALLER_INSTALL_VALIDATION=PASS'

  [Environment]::SetEnvironmentVariable('GITHUB_ACTIONS', 'false', 'Process')
  $appProcess = Start-Process -FilePath $appExe -WorkingDirectory $ownedRoot -PassThru
  $desktopLog = Join-Path $ownedRoot 'logs/desktop.log'
  $startupDeadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
  $startupReady = $false
  do {
    $appProcess.Refresh()
    if ($appProcess.HasExited) {
      throw "Installed application exited before readiness with code $($appProcess.ExitCode)."
    }
    if ((Test-Path -LiteralPath $desktopLog -PathType Leaf) -and
        (Select-String -LiteralPath $desktopLog -SimpleMatch 'Main UI loaded in' -Quiet)) {
      $startupReady = $true
      break
    }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $startupDeadline)
  if (-not $startupReady) {
    throw "Installed application did not reach readiness within $StartupTimeoutSeconds seconds."
  }
  Write-Output 'WINDOWS_INSTALLED_APP_STARTUP_VALIDATION=PASS'

  Stop-StartedProcessTree -Process $appProcess
  $appProcess = $null

  $uninstallAttempted = $true
  $uninstallProcess = Start-Process -FilePath $uninstaller `
    -ArgumentList '/S /KEEP_APP_DATA /currentuser' -Wait -PassThru
  Write-Output "WINDOWS_UNINSTALLER_EXIT_CODE=$($uninstallProcess.ExitCode)"
  if ($uninstallProcess.ExitCode -ne 0) {
    throw "Uninstaller exited with code $($uninstallProcess.ExitCode)."
  }

  $uninstallDeadline = (Get-Date).AddSeconds(60)
  do {
    $ownedEntries = @(Get-OwnedUninstallEntries -OwnedRoot $ownedRoot)
    $programFilesRemain = (
      (Test-Path -LiteralPath $appExe) -or
      (Test-Path -LiteralPath $appAsar) -or
      (Test-Path -LiteralPath $backendExe) -or
      (Test-Path -LiteralPath $uninstaller)
    )
    if (-not $programFilesRemain -and $ownedEntries.Count -eq 0) {
      break
    }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $uninstallDeadline)
  if ($programFilesRemain -or $ownedEntries.Count -ne 0) {
    throw 'Uninstaller left program binaries or its HKCU uninstall registration behind.'
  }
  Write-Output 'WINDOWS_UNINSTALL_VALIDATION=PASS'
}
catch {
  Write-Output 'WINDOWS_INSTALLER_VALIDATION=FAIL'
  throw
}
finally {
  if ($appProcess) {
    Stop-StartedProcessTree -Process $appProcess
  }
  if ($uninstaller -and -not $uninstallAttempted -and
      (Test-Path -LiteralPath $uninstaller -PathType Leaf)) {
    try {
      $cleanupUninstall = Start-Process -FilePath $uninstaller `
        -ArgumentList '/S /KEEP_APP_DATA /currentuser' -Wait -PassThru
      if ($cleanupUninstall.ExitCode -ne 0) {
        Write-Warning "Cleanup uninstaller returned code $($cleanupUninstall.ExitCode)."
      }
    }
    catch {
      Write-Warning 'Cleanup uninstaller could not be completed.'
    }
  }
  [Environment]::SetEnvironmentVariable(
    'GITHUB_ACTIONS',
    $savedGithubActions,
    'Process'
  )
  if ($ownedRootValidated) {
    Remove-OwnedRootWithRetry -OwnedRoot $ownedRoot
  }
}
