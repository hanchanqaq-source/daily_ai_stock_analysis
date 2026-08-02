param(
  [Parameter(Mandatory=$true)][string]$InstallerPath,
  [Parameter(Mandatory=$true)][string]$ExpectedVersion,
  [Parameter(Mandatory=$true)][string]$InstallRoot,
  [Parameter(Mandatory=$true)][string]$DiagnosticRoot,
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

function Test-UninstallCommandTargetsPath {
  param(
    [string]$Command,
    [Parameter(Mandatory=$true)][string]$ExecutablePath
  )

  if ([string]::IsNullOrWhiteSpace($Command)) {
    return $false
  }

  $normalizedExecutable = [IO.Path]::GetFullPath($ExecutablePath)
  $trimmedCommand = $Command.Trim()
  $quotedExecutable = '"' + $normalizedExecutable + '"'
  return (
    $trimmedCommand.Equals($quotedExecutable, [StringComparison]::OrdinalIgnoreCase) -or
    $trimmedCommand.StartsWith($quotedExecutable + ' ', [StringComparison]::OrdinalIgnoreCase) -or
    $trimmedCommand.Equals($normalizedExecutable, [StringComparison]::OrdinalIgnoreCase) -or
    $trimmedCommand.StartsWith($normalizedExecutable + ' ', [StringComparison]::OrdinalIgnoreCase)
  )
}

function Get-OwnedUninstallEntries {
  param([Parameter(Mandatory=$true)][string]$UninstallerPath)

  $uninstallKeyPath = 'Software\Microsoft\Windows\CurrentVersion\Uninstall'
  $views = @(
    [Microsoft.Win32.RegistryView]::Registry64,
    [Microsoft.Win32.RegistryView]::Registry32
  )
  # HKCU\Software is shared across WOW64 views on supported Windows versions.
  # Scan both views, then collapse duplicate observations of one physical entry.
  $entriesByIdentity = @{}

  foreach ($view in $views) {
    $baseKey = $null
    $uninstallKey = $null
    try {
      $baseKey = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::CurrentUser,
        $view
      )
      $uninstallKey = $baseKey.OpenSubKey($uninstallKeyPath)
      if (-not $uninstallKey) {
        continue
      }

      foreach ($subKeyName in $uninstallKey.GetSubKeyNames()) {
        $entryKey = $null
        try {
          $entryKey = $uninstallKey.OpenSubKey($subKeyName)
          if (-not $entryKey) {
            continue
          }
          $uninstallString = [string]$entryKey.GetValue('UninstallString')
          $quietUninstallString = [string]$entryKey.GetValue('QuietUninstallString')
          if ((Test-UninstallCommandTargetsPath `
                -Command $uninstallString -ExecutablePath $UninstallerPath) -and
              (Test-UninstallCommandTargetsPath `
                -Command $quietUninstallString -ExecutablePath $UninstallerPath)) {
            $displayVersion = [string]$entryKey.GetValue('DisplayVersion')
            $identity = "$subKeyName|$uninstallString|$quietUninstallString|$displayVersion"
            if ($entriesByIdentity.ContainsKey($identity)) {
              $entriesByIdentity[$identity].RegistryViews += [string]$view
            }
            else {
              $entriesByIdentity[$identity] = [pscustomobject]@{
                RegistryPath = "HKCU:\$uninstallKeyPath\$subKeyName"
                RegistryViews = @([string]$view)
                UninstallString = $uninstallString
                QuietUninstallString = $quietUninstallString
                DisplayVersion = $displayVersion
              }
            }
          }
        }
        finally {
          if ($entryKey) {
            $entryKey.Dispose()
          }
        }
      }
    }
    finally {
      if ($uninstallKey) {
        $uninstallKey.Dispose()
      }
      if ($baseKey) {
        $baseKey.Dispose()
      }
    }
  }

  return @($entriesByIdentity.Values)
}

function Write-StartupDiagnostics {
  param([Parameter(Mandatory=$true)][string]$LogPath)

  Write-Output 'WINDOWS_INSTALLED_APP_STARTUP_DIAGNOSTIC_BEGIN'
  if (-not (Test-Path -LiteralPath $LogPath -PathType Leaf)) {
    Write-Output 'WINDOWS_INSTALLED_APP_STARTUP_DIAGNOSTIC=desktop_log_missing'
  }
  else {
    $safeLines = @(
      Get-Content -LiteralPath $LogPath -ErrorAction Stop |
        Where-Object {
          $_.Contains('] Desktop app starting') -or
          $_.Contains('] [startup +') -or
          $_ -match '\] \[backend\] (spawned|first stdout|first stderr|exited|failed to start)'
        } |
        Select-Object -Last 120
    )
    if ($safeLines.Count -eq 0) {
      Write-Output 'WINDOWS_INSTALLED_APP_STARTUP_DIAGNOSTIC=no_safe_startup_lines'
    }
    else {
      foreach ($line in $safeLines) {
        Write-Output "WINDOWS_INSTALLED_APP_STARTUP_DIAGNOSTIC=$line"
      }
    }
  }
  Write-Output 'WINDOWS_INSTALLED_APP_STARTUP_DIAGNOSTIC_END'
}

function Protect-DiagnosticText {
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

function Set-ProtectedDiagnosticContent {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [AllowEmptyString()][string]$Text
  )

  $protected = Protect-DiagnosticText -Text $Text
  Set-Content -LiteralPath $Path -Value $protected -Encoding UTF8
}

function Get-DesktopDiagnosticLines {
  param([string]$LogPath)

  if (-not $LogPath -or -not (Test-Path -LiteralPath $LogPath -PathType Leaf)) {
    return @('desktop_log_missing')
  }

  return @(
    Get-Content -LiteralPath $LogPath -ErrorAction Stop |
      Where-Object {
        $_.Contains('] Desktop app starting') -or
        $_.Contains('] [startup +') -or
        $_ -match '\] \[backend\] (spawned|first stdout|first stderr|exited|failed to start)'
      } |
      Select-Object -Last 240 |
      ForEach-Object { Protect-DiagnosticText -Text $_.ToString() }
  )
}

function Get-DesktopBackendPort {
  param([string[]]$DesktopLines)

  foreach ($line in $DesktopLines) {
    $match = [regex]::Match($line, 'Using port (?<port>\d+)')
    if ($match.Success) {
      return [int]$match.Groups['port'].Value
    }
  }
  return 8000
}

function Get-DesktopBackendPid {
  param([string[]]$DesktopLines)

  foreach ($line in $DesktopLines) {
    $match = [regex]::Match($line, '\[backend\] spawned pid=(?<pid>\d+)')
    if ($match.Success) {
      return [int]$match.Groups['pid'].Value
    }
  }
  return $null
}

function Get-SafeProcessState {
  param(
    [Parameter(Mandatory=$true)][int]$ProcessId,
    [string]$Label = 'process'
  )

  try {
    $process = Get-Process -Id $ProcessId -ErrorAction Stop
    $process.Refresh()
    $path = ''
    try { $path = [string]$process.Path } catch { $path = '<unavailable>' }
    $startTime = ''
    try { $startTime = $process.StartTime.ToUniversalTime().ToString('o') } catch { $startTime = '<unavailable>' }
    return "$Label pid=$ProcessId name=$($process.ProcessName) start_utc=$startTime state=running path=$path"
  }
  catch {
    return "$Label pid=$ProcessId state=not_running"
  }
}

function Write-PortAndProcessDiagnostics {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][int]$Port,
    [System.Diagnostics.Process]$AppProcess,
    [int]$BackendProcessId = 0
  )

  $lines = @("port=$Port")
  if ($AppProcess) {
    $lines += Get-SafeProcessState -ProcessId $AppProcess.Id -Label 'desktop'
  }
  if ($BackendProcessId -gt 0) {
    $lines += Get-SafeProcessState -ProcessId $BackendProcessId -Label 'backend'
  }
  try {
    $listeners = @(
      Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
        Sort-Object OwningProcess
    )
    if ($listeners.Count -eq 0) {
      $lines += 'listener=none'
    }
    foreach ($listener in $listeners) {
      $lines += "listener address=$($listener.LocalAddress) port=$($listener.LocalPort) pid=$($listener.OwningProcess)"
      $lines += Get-SafeProcessState -ProcessId $listener.OwningProcess -Label 'listener_process'
    }
  }
  catch {
    $lines += "listener_query_error=$($_.Exception.GetType().FullName)"
  }
  Set-ProtectedDiagnosticContent -Path $Path -Text ($lines -join [Environment]::NewLine)
}

function Write-InstalledFileDiagnostics {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$OwnedRoot
  )

  if (-not (Test-Path -LiteralPath $OwnedRoot -PathType Container)) {
    Set-Content -LiteralPath $Path -Value 'install_root_missing' -Encoding UTF8
    return
  }

  $lines = @()
  foreach ($file in Get-ChildItem -LiteralPath $OwnedRoot -Recurse -File -ErrorAction SilentlyContinue) {
    $relativePath = [IO.Path]::GetRelativePath($OwnedRoot, $file.FullName)
    if ($relativePath -eq '.env' -or
        $relativePath.StartsWith('data\', [StringComparison]::OrdinalIgnoreCase) -or
        $relativePath.StartsWith('logs\', [StringComparison]::OrdinalIgnoreCase)) {
      continue
    }
    $lines += "$relativePath`t$($file.Length)"
    if ($lines.Count -ge 10000) {
      $lines += '<file_list_truncated>'
      break
    }
  }
  Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
}

function Write-WindowsApplicationEventDiagnostics {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][datetime]$StartedAt,
    [string[]]$RelatedExecutableNames
  )

  $lines = @()
  try {
    $events = @(
      Get-WinEvent -FilterHashtable @{
        LogName = 'Application'
        StartTime = $StartedAt.AddMinutes(-1)
      } -ErrorAction Stop |
        Where-Object {
          $eventRecord = $_
          $eventRecord.Id -in @(1000, 1001, 1026) -and
          @($RelatedExecutableNames | Where-Object {
            $executableName = $_
            $executableName -and
              $eventRecord.Message -and
              $eventRecord.Message.Contains($executableName)
          }).Count -gt 0
        } |
        Select-Object -First 20
    )
    foreach ($event in $events) {
      $message = Protect-DiagnosticText -Text ([string]$event.Message)
      $lines += "time_utc=$($event.TimeCreated.ToUniversalTime().ToString('o')) id=$($event.Id) provider=$($event.ProviderName)"
      $lines += $message
      $lines += '---'
    }
  }
  catch {
    $lines += "event_query_error=$($_.Exception.GetType().FullName)"
  }
  if ($lines.Count -eq 0) {
    $lines += 'related_events=none'
  }
  Set-ProtectedDiagnosticContent -Path $Path -Text ($lines -join [Environment]::NewLine)
}

function Invoke-BackendDiagnosticProbe {
  param(
    [Parameter(Mandatory=$true)][string]$BackendExecutable,
    [Parameter(Mandatory=$true)][string]$WorkingDirectory,
    [Parameter(Mandatory=$true)][int]$Port,
    [Parameter(Mandatory=$true)][string]$DiagnosticRoot
  )

  $rawBackendStdout = Join-Path $DiagnosticRoot '.backend-stdout.raw'
  $rawBackendStderr = Join-Path $DiagnosticRoot '.backend-stderr.raw'
  $sanitizedStderr = Join-Path $DiagnosticRoot 'backend-probe-stderr-sanitized.log'
  $probeSummary = Join-Path $DiagnosticRoot 'backend-probe-summary.txt'
  $probeProcess = $null
  $startedAt = Get-Date
  $exitObservedAt = $null
  $exitCode = '<not_started>'
  $exceptionType = '<none>'
  $listenerObserved = $false
  $arguments = @('--serve-only', '--host', '127.0.0.1', '--port', [string]$Port)

  try {
    $probeProcess = Start-Process -FilePath $BackendExecutable `
      -ArgumentList $arguments `
      -WorkingDirectory $WorkingDirectory `
      -RedirectStandardOutput $rawBackendStdout `
      -RedirectStandardError $rawBackendStderr `
      -PassThru
    $deadline = (Get-Date).AddSeconds(20)
    do {
      $probeProcess.Refresh()
      if ($probeProcess.HasExited) {
        $exitObservedAt = Get-Date
        $exitCode = [string]$probeProcess.ExitCode
        break
      }
      try {
        $listenerObserved = @(
          Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
            Where-Object { $_.OwningProcess -eq $probeProcess.Id }
        ).Count -gt 0
      }
      catch {
        $listenerObserved = $false
      }
      if ($listenerObserved) {
        break
      }
      Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
  }
  catch {
    $exceptionType = $_.Exception.GetType().FullName
  }
  finally {
    if ($probeProcess) {
      try {
        $probeProcess.Refresh()
        if (-not $probeProcess.HasExited) {
          & taskkill.exe /PID $probeProcess.Id /T /F | Out-Null
          try { Wait-Process -Id $probeProcess.Id -Timeout 20 -ErrorAction SilentlyContinue } catch {}
          $probeProcess.Refresh()
        }
        if ($probeProcess.HasExited) {
          $exitObservedAt = Get-Date
          $exitCode = [string]$probeProcess.ExitCode
        }
      }
      catch {
        if ($exceptionType -eq '<none>') {
          $exceptionType = $_.Exception.GetType().FullName
        }
      }
    }

    try {
      $stderrText = ''
      if (Test-Path -LiteralPath $rawBackendStderr -PathType Leaf) {
        $stderrLines = @(Get-Content -LiteralPath $rawBackendStderr -ErrorAction SilentlyContinue | Select-Object -Last 500)
        $stderrText = $stderrLines -join [Environment]::NewLine
      }
      Set-ProtectedDiagnosticContent -Path $sanitizedStderr -Text $stderrText
    }
    finally {
      if (Test-Path -LiteralPath $rawBackendStderr) {
        Remove-Item -LiteralPath $rawBackendStderr -Force -ErrorAction SilentlyContinue
      }
      if (Test-Path -LiteralPath $rawBackendStdout) {
        Remove-Item -LiteralPath $rawBackendStdout -Force -ErrorAction SilentlyContinue
      }
    }

    $summary = @(
      "start_utc=$($startedAt.ToUniversalTime().ToString('o'))",
      "exit_utc=$(if ($exitObservedAt) { $exitObservedAt.ToUniversalTime().ToString('o') } else { '<not_observed>' })",
      "exit_code=$exitCode",
      "exception_type=$exceptionType",
      "listener_observed=$listenerObserved",
      "executable=$BackendExecutable",
      "working_directory=$WorkingDirectory",
      "command_structure=<backend-executable> --serve-only --host 127.0.0.1 --port <selected-port>"
    )
    Set-ProtectedDiagnosticContent -Path $probeSummary -Text ($summary -join [Environment]::NewLine)
  }
}

function Save-InstallerDiagnostics {
  param(
    [Parameter(Mandatory=$true)][string]$DiagnosticRoot,
    [Parameter(Mandatory=$true)][System.Management.Automation.ErrorRecord]$FailureRecord,
    [Parameter(Mandatory=$true)][datetime]$VerificationStartedAt,
    [string]$Installer,
    [string]$OwnedRoot,
    [string]$AppExecutable,
    [string]$BackendExecutable,
    [System.Diagnostics.Process]$AppProcess,
    [string]$DesktopLog
  )

  New-Item -ItemType Directory -Path $DiagnosticRoot -Force | Out-Null
  $desktopLines = @(Get-DesktopDiagnosticLines -LogPath $DesktopLog)
  Set-ProtectedDiagnosticContent `
    -Path (Join-Path $DiagnosticRoot 'desktop-startup-sanitized.log') `
    -Text ($desktopLines -join [Environment]::NewLine)

  $backendPort = Get-DesktopBackendPort -DesktopLines $desktopLines
  $backendProcessId = Get-DesktopBackendPid -DesktopLines $desktopLines
  Write-PortAndProcessDiagnostics `
    -Path (Join-Path $DiagnosticRoot 'port-process-state.txt') `
    -Port $backendPort `
    -AppProcess $AppProcess `
    -BackendProcessId $backendProcessId
  Write-InstalledFileDiagnostics `
    -Path (Join-Path $DiagnosticRoot 'installed-files.txt') `
    -OwnedRoot $OwnedRoot

  $relatedNames = @()
  foreach ($candidate in @($AppExecutable, $BackendExecutable)) {
    if ($candidate) {
      $relatedNames += Split-Path -Leaf $candidate
    }
  }
  Write-WindowsApplicationEventDiagnostics `
    -Path (Join-Path $DiagnosticRoot 'windows-application-events-sanitized.log') `
    -StartedAt $VerificationStartedAt `
    -RelatedExecutableNames $relatedNames

  $summary = @(
    'WINDOWS_INSTALLER_DIAGNOSTIC=AVAILABLE',
    "verification_start_utc=$($VerificationStartedAt.ToUniversalTime().ToString('o'))",
    "diagnostic_capture_utc=$((Get-Date).ToUniversalTime().ToString('o'))",
    "failure_type=$($FailureRecord.Exception.GetType().FullName)",
    "failure_message=$(Protect-DiagnosticText -Text $FailureRecord.Exception.Message)",
    "failure_stack=$(Protect-DiagnosticText -Text ([string]$FailureRecord.ScriptStackTrace))",
    "installer=$Installer",
    "install_root=$OwnedRoot",
    "app_executable=$AppExecutable",
    "app_executable_exists=$(if ($AppExecutable) { Test-Path -LiteralPath $AppExecutable -PathType Leaf } else { $false })",
    "backend_executable=$BackendExecutable",
    "backend_executable_exists=$(if ($BackendExecutable) { Test-Path -LiteralPath $BackendExecutable -PathType Leaf } else { $false })",
    'app_command_structure=<installed-app-executable>',
    'backend_command_structure=<backend-executable> --serve-only --host 127.0.0.1 --port <selected-port>'
  )
  Set-ProtectedDiagnosticContent `
    -Path (Join-Path $DiagnosticRoot 'diagnostic-summary.txt') `
    -Text ($summary -join [Environment]::NewLine)

  if ($AppProcess) {
    Stop-StartedProcessTree -Process $AppProcess
  }
  if ($BackendExecutable -and
      (Test-Path -LiteralPath $BackendExecutable -PathType Leaf) -and
      $OwnedRoot -and
      (Test-Path -LiteralPath $OwnedRoot -PathType Container)) {
    Invoke-BackendDiagnosticProbe `
      -BackendExecutable $BackendExecutable `
      -WorkingDirectory $OwnedRoot `
      -Port $backendPort `
      -DiagnosticRoot $DiagnosticRoot
  }
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
$diagnosticRoot = Get-NormalizedDirectoryPath -Path $DiagnosticRoot
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
$diagnosticLeaf = Split-Path -Leaf $diagnosticRoot
if (-not (Test-PathInsideRoot -Path $diagnosticRoot -Root $runnerTemp)) {
  throw 'DiagnosticRoot must be a child of RUNNER_TEMP.'
}
if (-not $diagnosticLeaf.StartsWith('pp02-installer-diagnostics-', [StringComparison]::OrdinalIgnoreCase)) {
  throw 'DiagnosticRoot must use the pp02-installer-diagnostics-* prefix.'
}
if (Test-Path -LiteralPath $diagnosticRoot) {
  throw 'DiagnosticRoot must not exist before verification.'
}
New-Item -ItemType Directory -Path $diagnosticRoot -Force | Out-Null

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
$appExe = $null
$backendExe = $null
$desktopLog = $null
$uninstaller = $null
$uninstallAttempted = $false
$ownedRootValidated = $true
$savedGithubActions = [Environment]::GetEnvironmentVariable('GITHUB_ACTIONS', 'Process')
$savedInstallerDiagnosticRoot = [Environment]::GetEnvironmentVariable(
  'DSA_INSTALLER_DIAGNOSTIC_ROOT',
  'Process'
)
$verificationStartedAt = Get-Date

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
    $ownedEntries = @(Get-OwnedUninstallEntries -UninstallerPath $uninstaller)
    if ($ownedEntries.Count -eq 1) {
      break
    }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $registryDeadline)
  if ($ownedEntries.Count -ne 1) {
    throw "Expected exactly one HKCU uninstall entry for the owned uninstaller; found $($ownedEntries.Count)."
  }
  if ($ownedEntries[0].DisplayVersion -ne $ExpectedVersion) {
    throw "HKCU uninstall entry version does not match $ExpectedVersion."
  }
  Write-Output 'WINDOWS_INSTALLER_INSTALL_VALIDATION=PASS'

  [Environment]::SetEnvironmentVariable('GITHUB_ACTIONS', 'false', 'Process')
  [Environment]::SetEnvironmentVariable(
    'DSA_INSTALLER_DIAGNOSTIC_ROOT',
    $diagnosticRoot,
    'Process'
  )
  $appProcess = Start-Process -FilePath $appExe -WorkingDirectory $ownedRoot -PassThru
  $desktopLog = Join-Path $ownedRoot 'logs/desktop.log'
  $startupDeadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
  $startupReady = $false
  do {
    $appProcess.Refresh()
    if ($appProcess.HasExited) {
      Write-StartupDiagnostics -LogPath $desktopLog
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
    Write-StartupDiagnostics -LogPath $desktopLog
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
    $ownedEntries = @(Get-OwnedUninstallEntries -UninstallerPath $uninstaller)
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
  Set-Content `
    -LiteralPath (Join-Path $diagnosticRoot 'diagnostic-summary.txt') `
    -Value 'WINDOWS_INSTALLER_DIAGNOSTIC=NOT_REQUIRED_VALIDATION_PASS' `
    -Encoding UTF8
}
catch {
  Write-Output 'WINDOWS_INSTALLER_VALIDATION=FAIL'
  $originalFailure = $_
  try {
    Save-InstallerDiagnostics `
      -DiagnosticRoot $diagnosticRoot `
      -FailureRecord $originalFailure `
      -VerificationStartedAt $verificationStartedAt `
      -Installer $installer `
      -OwnedRoot $ownedRoot `
      -AppExecutable $appExe `
      -BackendExecutable $backendExe `
      -AppProcess $appProcess `
      -DesktopLog $desktopLog
    Write-Output 'WINDOWS_INSTALLER_DIAGNOSTIC=AVAILABLE'
  }
  catch {
    Write-Warning "Diagnostic capture failed with $($_.Exception.GetType().FullName)."
  }
  throw $originalFailure
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
  [Environment]::SetEnvironmentVariable(
    'DSA_INSTALLER_DIAGNOSTIC_ROOT',
    $savedInstallerDiagnosticRoot,
    'Process'
  )
  if ($ownedRootValidated) {
    Remove-OwnedRootWithRetry -OwnedRoot $ownedRoot
  }
}
