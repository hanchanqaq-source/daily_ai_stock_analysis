$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$manifestFileName = 'owned-processes.json'
$evidenceFileName = 'owned-process-cleanup-evidence.json'
$gracefulTimeoutSeconds = 10
$forcedTimeoutSeconds = 5
$initialOwnedCount = 0
$gracefulRequests = 0
$forcedStops = 0
$remainingOwnedCount = -1

function Get-NormalizedFilePath {
  param([Parameter(Mandatory=$true)][string]$Path)

  return [IO.Path]::GetFullPath($Path)
}

function Write-OwnedProcessEvidence {
  param(
    [Parameter(Mandatory=$true)][ValidateSet('PASS', 'FAIL')][string]$Status,
    [Parameter(Mandatory=$true)][int]$InitialOwnedProcessCount,
    [Parameter(Mandatory=$true)][int]$GracefulRequestCount,
    [Parameter(Mandatory=$true)][int]$ForcedStopCount,
    [Parameter(Mandatory=$true)][int]$RemainingOwnedProcessCount
  )

  $diagnosticRootValue = [Environment]::GetEnvironmentVariable(
    'DSA_INSTALLER_DIAGNOSTIC_ROOT',
    'Process'
  )
  if ([string]::IsNullOrWhiteSpace($diagnosticRootValue)) {
    return
  }

  $diagnosticRoot = [IO.Path]::GetFullPath($diagnosticRootValue).TrimEnd(
    [char[]]@(
      [IO.Path]::DirectorySeparatorChar,
      [IO.Path]::AltDirectorySeparatorChar
    )
  )
  $diagnosticLeaf = Split-Path -Leaf $diagnosticRoot
  if (-not $diagnosticLeaf.StartsWith(
      'pp02-installer-diagnostics-',
      [StringComparison]::OrdinalIgnoreCase
    ) -or
      -not (Test-Path -LiteralPath $diagnosticRoot -PathType Container)) {
    return
  }

  $evidencePath = Join-Path $diagnosticRoot $evidenceFileName
  $temporaryEvidencePath = "$evidencePath.$PID.tmp"
  $evidence = [ordered]@{
    schemaVersion = 1
    status = $Status
    initialOwnedProcessCount = $InitialOwnedProcessCount
    gracefulRequestCount = $GracefulRequestCount
    forcedStopCount = $ForcedStopCount
    remainingOwnedProcessCount = $RemainingOwnedProcessCount
  }
  try {
    $evidence | ConvertTo-Json -Compress | Set-Content `
      -LiteralPath $temporaryEvidencePath -Encoding UTF8
    Move-Item `
      -LiteralPath $temporaryEvidencePath `
      -Destination $evidencePath `
      -Force
  }
  finally {
    if (Test-Path -LiteralPath $temporaryEvidencePath -PathType Leaf) {
      Remove-Item -LiteralPath $temporaryEvidencePath -Force -ErrorAction SilentlyContinue
    }
  }
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

try {
  $resourcesRoot = Get-NormalizedFilePath -Path $PSScriptRoot
  $installRoot = Get-NormalizedFilePath -Path (Split-Path -Parent $resourcesRoot)
  if (-not (Test-Path -LiteralPath $installRoot -PathType Container)) {
    throw 'Install root does not exist.'
  }
  $rootPrefix = $installRoot.TrimEnd('\') + '\'
  $manifestPath = Join-Path $resourcesRoot $manifestFileName
  if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw 'Owned-process manifest is missing.'
  }

  $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  $manifestProperties = @($manifest.PSObject.Properties.Name | Sort-Object)
  if (($manifestProperties -join ',') -ne 'executables,schemaVersion' -or
      [int]$manifest.schemaVersion -ne 1) {
    throw 'Owned-process manifest schema is invalid.'
  }
  $entries = @($manifest.executables)
  if ($entries.Count -ne 2) {
    throw 'Owned-process manifest must declare exactly two executables.'
  }

  $ownedExecutablePaths = @()
  $gracefulExecutablePaths = @()
  $roles = @{}
  foreach ($entry in $entries) {
    $entryProperties = @($entry.PSObject.Properties.Name | Sort-Object)
    if (($entryProperties -join ',') -ne 'relativePath,requestMainWindowClose,role') {
      throw 'Owned-process manifest entry schema is invalid.'
    }
    $role = [string]$entry.role
    if ($role -notin @('desktop', 'backend') -or $roles.ContainsKey($role)) {
      throw 'Owned-process manifest roles are invalid.'
    }
    if ($entry.requestMainWindowClose -isnot [bool]) {
      throw 'Owned-process close policy must be a boolean.'
    }
    if (($role -eq 'desktop') -ne [bool]$entry.requestMainWindowClose) {
      throw 'Owned-process close policy does not match its role.'
    }
    $relativePath = [string]$entry.relativePath
    if ([string]::IsNullOrWhiteSpace($relativePath) -or
        [IO.Path]::IsPathRooted($relativePath)) {
      throw 'Owned executable path must be a non-empty relative path.'
    }
    $ownedPath = Get-NormalizedFilePath -Path (Join-Path $installRoot $relativePath)
    if (-not $ownedPath.StartsWith(
        $rootPrefix,
        [StringComparison]::OrdinalIgnoreCase
      )) {
      throw 'Owned executable path escaped the install root.'
    }
    $roles[$role] = $true
    $ownedExecutablePaths += $ownedPath
    if ([bool]$entry.requestMainWindowClose) {
      $gracefulExecutablePaths += $ownedPath
    }
  }
  foreach ($requiredRole in @('desktop', 'backend')) {
    if (-not $roles.ContainsKey($requiredRole)) {
      throw 'Owned-process manifest is missing a required role.'
    }
  }

  $initialOwned = @(Get-ExactOwnedProcesses -ExecutablePaths $ownedExecutablePaths)
  $initialOwnedCount = $initialOwned.Count
  foreach ($owned in $initialOwned) {
    if (-not ($gracefulExecutablePaths -contains $owned.ExecutablePath)) {
      continue
    }
    try {
      $process = Get-Process -Id $owned.ProcessId -ErrorAction Stop
      if ([string]$process.Path -and
          ([string]$process.Path).Equals(
            $owned.ExecutablePath,
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

  if (-not (Wait-ForExactOwnedProcessExit `
      -ExecutablePaths $ownedExecutablePaths `
      -TimeoutSeconds $gracefulTimeoutSeconds)) {
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
      -TimeoutSeconds $forcedTimeoutSeconds)) {
    throw 'Product-owned processes did not exit before uninstall cleanup.'
  }
  $remainingOwnedCount = @(
    Get-ExactOwnedProcesses -ExecutablePaths $ownedExecutablePaths
  ).Count
  if ($remainingOwnedCount -ne 0) {
    throw 'Product-owned process final count is not zero.'
  }

  Write-OwnedProcessEvidence `
    -Status 'PASS' `
    -InitialOwnedProcessCount $initialOwnedCount `
    -GracefulRequestCount $gracefulRequests `
    -ForcedStopCount $forcedStops `
    -RemainingOwnedProcessCount $remainingOwnedCount
  Write-Output "PP02_OWNED_PROCESS_INITIAL_COUNT=$initialOwnedCount"
  Write-Output "PP02_OWNED_PROCESS_GRACEFUL_REQUEST_COUNT=$gracefulRequests"
  Write-Output "PP02_OWNED_PROCESS_FORCED_STOP_COUNT=$forcedStops"
  Write-Output 'PP02_OWNED_PROCESS_EXIT_VALIDATION=PASS'
}
catch {
  try {
    Write-OwnedProcessEvidence `
      -Status 'FAIL' `
      -InitialOwnedProcessCount $initialOwnedCount `
      -GracefulRequestCount $gracefulRequests `
      -ForcedStopCount $forcedStops `
      -RemainingOwnedProcessCount $remainingOwnedCount
  }
  catch {
    # The original fail-closed helper error remains authoritative.
  }
  throw
}
