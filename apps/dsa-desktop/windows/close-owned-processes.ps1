param(
  [Parameter(Mandatory=$true)][ValidateNotNullOrEmpty()][string]$InstallRoot,
  [Parameter(Mandatory=$true)][ValidateNotNullOrEmpty()][string]$ProductExecutableName,
  [Parameter(Mandatory=$true)][ValidateNotNullOrEmpty()][string]$BackendRelativePath,
  [int]$GracefulTimeoutSeconds = 10,
  [int]$ForcedTimeoutSeconds = 5
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-NormalizedFilePath {
  param([Parameter(Mandatory=$true)][string]$Path)

  return [IO.Path]::GetFullPath($Path)
}

function Get-ExactOwnedProcesses {
  param([Parameter(Mandatory=$true)][string[]]$ExecutablePaths)

  $matches = @()
  foreach ($candidate in @(Get-CimInstance Win32_Process -ErrorAction Stop)) {
    $candidatePath = [string]$candidate.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($candidatePath)) {
      continue
    }
    foreach ($expectedPath in $ExecutablePaths) {
      if ($candidatePath.Equals($expectedPath, [StringComparison]::OrdinalIgnoreCase)) {
        $matches += [pscustomobject]@{
          ProcessId = [int]$candidate.ProcessId
          ExecutablePath = $candidatePath
        }
        break
      }
    }
  }
  return $matches
}

function Wait-ForExactOwnedProcessExit {
  param(
    [Parameter(Mandatory=$true)][string[]]$ExecutablePaths,
    [Parameter(Mandatory=$true)][int]$TimeoutSeconds
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    $remaining = @(Get-ExactOwnedProcesses -ExecutablePaths $ExecutablePaths)
    if ($remaining.Count -eq 0) {
      return $true
    }
    Start-Sleep -Milliseconds 100
  } while ((Get-Date) -lt $deadline)
  return $false
}

$normalizedInstallRoot = Get-NormalizedFilePath -Path $InstallRoot
if (-not (Test-Path -LiteralPath $normalizedInstallRoot -PathType Container)) {
  throw 'Install root does not exist.'
}
$rootPrefix = $normalizedInstallRoot.TrimEnd('\') + '\'
if ([IO.Path]::GetFileName($ProductExecutableName) -ne $ProductExecutableName) {
  throw 'Product executable name must be one file name.'
}
if ([IO.Path]::IsPathRooted($BackendRelativePath)) {
  throw 'Backend executable path must be relative to the install root.'
}

$productExecutablePath = Get-NormalizedFilePath -Path (
  Join-Path $normalizedInstallRoot $ProductExecutableName
)
$backendExecutablePath = Get-NormalizedFilePath -Path (
  Join-Path $normalizedInstallRoot $BackendRelativePath
)
foreach ($ownedPath in @($productExecutablePath, $backendExecutablePath)) {
  if (-not $ownedPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Owned executable path escaped the install root.'
  }
}
$ownedExecutablePaths = @($productExecutablePath, $backendExecutablePath)

$initialOwned = @(Get-ExactOwnedProcesses -ExecutablePaths $ownedExecutablePaths)
$gracefulRequests = 0
foreach ($owned in $initialOwned) {
  if (-not $owned.ExecutablePath.Equals(
      $productExecutablePath,
      [StringComparison]::OrdinalIgnoreCase
    )) {
    continue
  }
  try {
    $process = Get-Process -Id $owned.ProcessId -ErrorAction Stop
    if ([string]$process.Path -and
        ([string]$process.Path).Equals(
          $productExecutablePath,
          [StringComparison]::OrdinalIgnoreCase
        )) {
      $null = $process.CloseMainWindow()
      $gracefulRequests += 1
    }
  }
  catch {
    # Exit/access races are resolved by the exact-path recheck and final gate.
  }
}

$forcedStops = 0
if (-not (Wait-ForExactOwnedProcessExit `
    -ExecutablePaths $ownedExecutablePaths `
    -TimeoutSeconds $GracefulTimeoutSeconds)) {
  foreach ($owned in @(Get-ExactOwnedProcesses -ExecutablePaths $ownedExecutablePaths)) {
    try {
      $process = Get-Process -Id $owned.ProcessId -ErrorAction Stop
      if ([string]$process.Path -and
          ([string]$process.Path).Equals(
            $owned.ExecutablePath,
            [StringComparison]::OrdinalIgnoreCase
          )) {
        Stop-Process -Id $process.Id -Force -ErrorAction Stop
        $forcedStops += 1
      }
    }
    catch {
      # Exit/access races are resolved by the exact-path final gate below.
    }
  }
}

if (-not (Wait-ForExactOwnedProcessExit `
    -ExecutablePaths $ownedExecutablePaths `
    -TimeoutSeconds $ForcedTimeoutSeconds)) {
  throw 'Product-owned processes did not exit before uninstall cleanup.'
}

Write-Output "PP02_OWNED_PROCESS_INITIAL_COUNT=$($initialOwned.Count)"
Write-Output "PP02_OWNED_PROCESS_GRACEFUL_REQUEST_COUNT=$gracefulRequests"
Write-Output "PP02_OWNED_PROCESS_FORCED_STOP_COUNT=$forcedStops"
Write-Output 'PP02_OWNED_PROCESS_EXIT_VALIDATION=PASS'
