param(
  [Parameter(Mandatory=$true)][string]$InstallerPath,
  [Parameter(Mandatory=$true)][string]$ExpectedVersion,
  [Parameter(Mandatory=$true)][string]$InstallRoot,
  [Parameter(Mandatory=$true)][string]$DiagnosticRoot,
  [string]$MalwareScannerPath = '',
  [string]$MalwareReportPath = '',
  [string]$PreinstallMalwareReportPath = '',
  [string]$PortableArchivePath = '',
  [string]$ExpectedCommitSha = '',
  [int]$StartupTimeoutSeconds = 120,
  [int]$InstallTimeoutSeconds = 300,
  [int]$UninstallTimeoutSeconds = 300,
  [switch]$RequireValidSignature
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$boundedProcessHelper = Join-Path $PSScriptRoot 'windows-bounded-process.ps1'
if (-not (Test-Path -LiteralPath $boundedProcessHelper -PathType Leaf)) {
  throw 'Bounded Windows process helper is missing.'
}
. $boundedProcessHelper

if ($InstallTimeoutSeconds -lt 1 -or $InstallTimeoutSeconds -gt 1800) {
  throw 'InstallTimeoutSeconds must be between 1 and 1800.'
}
if ($UninstallTimeoutSeconds -lt 1 -or $UninstallTimeoutSeconds -gt 1800) {
  throw 'UninstallTimeoutSeconds must be between 1 and 1800.'
}

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

function Get-RelativePathInsideRoot {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Root
  )

  $normalizedPath = [IO.Path]::GetFullPath($Path)
  $normalizedRoot = Get-NormalizedDirectoryPath -Path $Root
  $rootPrefix = $normalizedRoot + [IO.Path]::DirectorySeparatorChar
  if (-not $normalizedPath.StartsWith(
      $rootPrefix,
      [StringComparison]::OrdinalIgnoreCase
    )) {
    throw 'Installed-file inventory encountered a path outside the owned root.'
  }
  return $normalizedPath.Substring($rootPrefix.Length)
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
  $protected = [regex]::Replace(
    $protected,
    '\bpp02-r37-[0-9a-f]{64}\b',
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

function Add-ProtectedDiagnosticContent {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [AllowEmptyString()][string]$Text
  )

  $protected = Protect-DiagnosticText -Text $Text
  Add-Content -LiteralPath $Path -Value $protected -Encoding UTF8
}

function Add-InstallerStageReport {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Stage,
    [Parameter(Mandatory=$true)][string]$Status
  )

  Add-Content `
    -LiteralPath $Path `
    -Value "timestamp_utc=$((Get-Date).ToUniversalTime().ToString('o')) stage=$Stage status=$Status" `
    -Encoding UTF8
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

  $matchedPort = $null
  foreach ($line in $DesktopLines) {
    $match = [regex]::Match($line, 'Using port (?<port>\d+)')
    if ($match.Success) {
      $matchedPort = [int]$match.Groups['port'].Value
    }
  }
  if ($null -ne $matchedPort) {
    return $matchedPort
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

function Get-DesktopReadyMarkerCount {
  param([string]$LogPath)

  if (-not $LogPath -or -not (Test-Path -LiteralPath $LogPath -PathType Leaf)) {
    return 0
  }
  return @(
    Select-String `
      -LiteralPath $LogPath `
      -SimpleMatch 'Main UI loaded in' `
      -ErrorAction Stop
  ).Count
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

function Get-ExactOwnedProcesses {
  param(
    [Parameter(Mandatory=$true)][string]$AppExecutable,
    [Parameter(Mandatory=$true)][string]$BackendExecutable
  )

  $expectedPaths = @(
    [IO.Path]::GetFullPath($AppExecutable),
    [IO.Path]::GetFullPath($BackendExecutable)
  )
  $matches = @()
  foreach ($candidate in @(Get-CimInstance Win32_Process -ErrorAction Stop)) {
    $candidatePath = [string]$candidate.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($candidatePath)) {
      continue
    }
    foreach ($expectedPath in $expectedPaths) {
      if ($candidatePath.Equals($expectedPath, [StringComparison]::OrdinalIgnoreCase)) {
        $matches += $candidate
        break
      }
    }
  }
  return $matches
}

function Get-AuthenticodeStatus {
  param([Parameter(Mandatory=$true)][string]$Path)

  $signature = Get-AuthenticodeSignature -FilePath $Path -ErrorAction Stop
  return [string]$signature.Status
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
    $relativePath = Get-RelativePathInsideRoot -Path $file.FullName -Root $OwnedRoot
    if ($relativePath -eq '.env' -or
        $relativePath.StartsWith('data\', [StringComparison]::OrdinalIgnoreCase) -or
        $relativePath.StartsWith('logs\', [StringComparison]::OrdinalIgnoreCase) -or
        @('.db', '.sqlite', '.sqlite3').Contains(
          [IO.Path]::GetExtension($relativePath).ToLowerInvariant()
        )) {
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
    [Parameter(Mandatory=$true)][string]$FailureStage,
    [Parameter(Mandatory=$true)][string]$StageProcess,
    [Parameter(Mandatory=$true)][string]$StageProcessStartedUtc,
    [Parameter(Mandatory=$true)][string]$StageProcessExitedUtc,
    [Parameter(Mandatory=$true)][string]$StageProcessExitCode,
    [string]$Installer,
    [string]$OwnedRoot,
    [string]$AppExecutable,
    [string]$BackendExecutable,
    [System.Diagnostics.Process]$AppProcess,
    [string]$DesktopLog
  )

  New-Item -ItemType Directory -Path $DiagnosticRoot -Force | Out-Null
  $summaryPath = Join-Path $DiagnosticRoot 'diagnostic-summary.txt'
  $summary = @(
    'WINDOWS_INSTALLER_DIAGNOSTIC=AVAILABLE',
    "verification_start_utc=$($VerificationStartedAt.ToUniversalTime().ToString('o'))",
    "diagnostic_capture_utc=$((Get-Date).ToUniversalTime().ToString('o'))",
    "failure_stage=$FailureStage",
    "failure_type=$($FailureRecord.Exception.GetType().FullName)",
    "failure_message=$(Protect-DiagnosticText -Text $FailureRecord.Exception.Message)",
    "failure_stack=$(Protect-DiagnosticText -Text ([string]$FailureRecord.ScriptStackTrace))",
    "stage_process=$StageProcess",
    "stage_process_start_utc=$StageProcessStartedUtc",
    "stage_process_exit_utc=$StageProcessExitedUtc",
    "stage_process_exit_code=$StageProcessExitCode",
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
    -Path $summaryPath `
    -Text ($summary -join [Environment]::NewLine)

  $collectorStatuses = @()
  $desktopLines = @('desktop_diagnostic_not_collected')
  $backendPort = 8000
  $backendProcessId = 0
  try {
    $desktopLines = @(Get-DesktopDiagnosticLines -LogPath $DesktopLog)
    Set-ProtectedDiagnosticContent `
      -Path (Join-Path $DiagnosticRoot 'desktop-startup-sanitized.log') `
      -Text ($desktopLines -join [Environment]::NewLine)
    $backendPort = Get-DesktopBackendPort -DesktopLines $desktopLines
    $resolvedBackendProcessId = Get-DesktopBackendPid -DesktopLines $desktopLines
    if ($resolvedBackendProcessId) {
      $backendProcessId = [int]$resolvedBackendProcessId
    }
    Add-ProtectedDiagnosticContent -Path $summaryPath -Text "backend_port=$backendPort"
    $collectorStatuses += 'desktop_startup=PASS'
  }
  catch {
    $collectorStatuses += "desktop_startup=FAIL:$($_.Exception.GetType().FullName)"
  }

  try {
    Write-PortAndProcessDiagnostics `
      -Path (Join-Path $DiagnosticRoot 'port-process-state.txt') `
      -Port $backendPort `
      -AppProcess $AppProcess `
      -BackendProcessId $backendProcessId
    $collectorStatuses += 'port_process=PASS'
  }
  catch {
    $collectorStatuses += "port_process=FAIL:$($_.Exception.GetType().FullName)"
  }

  try {
    Write-InstalledFileDiagnostics `
      -Path (Join-Path $DiagnosticRoot 'installed-files.txt') `
      -OwnedRoot $OwnedRoot
    $collectorStatuses += 'installed_files=PASS'
  }
  catch {
    $collectorStatuses += "installed_files=FAIL:$($_.Exception.GetType().FullName)"
  }

  try {
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
    $collectorStatuses += 'windows_events=PASS'
  }
  catch {
    $collectorStatuses += "windows_events=FAIL:$($_.Exception.GetType().FullName)"
  }

  if ($AppProcess) {
    try {
      Stop-StartedProcessTree -Process $AppProcess
      $collectorStatuses += 'app_process_stop=PASS'
    }
    catch {
      $collectorStatuses += "app_process_stop=FAIL:$($_.Exception.GetType().FullName)"
    }
  }
  else {
    $collectorStatuses += 'app_process_stop=NOT_REQUIRED'
  }

  if ($BackendExecutable -and
      (Test-Path -LiteralPath $BackendExecutable -PathType Leaf) -and
      $OwnedRoot -and
      (Test-Path -LiteralPath $OwnedRoot -PathType Container)) {
    try {
      Invoke-BackendDiagnosticProbe `
        -BackendExecutable $BackendExecutable `
        -WorkingDirectory $OwnedRoot `
        -Port $backendPort `
        -DiagnosticRoot $DiagnosticRoot
      $collectorStatuses += 'backend_probe=PASS'
    }
    catch {
      $collectorStatuses += "backend_probe=FAIL:$($_.Exception.GetType().FullName)"
    }
  }
  else {
    $collectorStatuses += 'backend_probe=NOT_REQUIRED'
  }

  Set-ProtectedDiagnosticContent `
    -Path (Join-Path $DiagnosticRoot 'diagnostic-collector-status.txt') `
    -Text ($collectorStatuses -join [Environment]::NewLine)
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

function Get-PP02SyntheticCredential {
  param([Parameter(Mandatory=$true)][string]$Head)

  $sha256 = [Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [Text.Encoding]::UTF8.GetBytes("pp02-r37-fake:$Head")
    $digest = $sha256.ComputeHash($bytes)
    $suffix = -join ($digest | ForEach-Object { $_.ToString('x2') })
    return "pp02-r37-$suffix"
  }
  finally {
    $sha256.Dispose()
  }
}

function Invoke-PP02LocalJsonRequest {
  param(
    [Parameter(Mandatory=$true)][ValidateSet('GET', 'POST', 'PUT')][string]$Method,
    [Parameter(Mandatory=$true)][string]$Uri,
    [object]$Body = $null,
    [int]$TimeoutSeconds = 30,
    [string]$RawOutputPath = ''
  )

  if ($TimeoutSeconds -lt 1 -or $TimeoutSeconds -gt 120) {
    throw 'Local JSON request timeout must be between 1 and 120 seconds.'
  }
  $parsedUri = [Uri]$Uri
  if (-not $parsedUri.IsLoopback -or $parsedUri.Scheme -ne 'http') {
    throw 'Installed configuration acceptance permits only loopback HTTP.'
  }
  $request = @{
    Method = $Method
    Uri = $parsedUri.AbsoluteUri
    TimeoutSec = $TimeoutSeconds
    ErrorAction = 'Stop'
    UseBasicParsing = $true
  }
  if ($null -ne $Body) {
    $request.ContentType = 'application/json'
    $request.Body = ConvertTo-Json -InputObject $Body -Depth 12 -Compress
  }
  $response = Invoke-WebRequest @request
  $content = [string]$response.Content
  if (-not [string]::IsNullOrWhiteSpace($RawOutputPath)) {
    Set-Content -LiteralPath $RawOutputPath -Value $content -Encoding UTF8
  }
  if ([string]::IsNullOrWhiteSpace($content)) {
    return $null
  }
  return $content | ConvertFrom-Json
}

function Get-PP02ConfigItem {
  param(
    [Parameter(Mandatory=$true)][object]$Config,
    [Parameter(Mandatory=$true)][string]$Key
  )

  $matches = @($Config.items | Where-Object { [string]$_.key -eq $Key })
  if ($matches.Count -ne 1) {
    throw "Installed configuration did not return exactly one $Key item."
  }
  return $matches[0]
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
$repoRoot = Split-Path -Parent $PSScriptRoot
$malwareScanner = if ([string]::IsNullOrWhiteSpace($MalwareScannerPath)) {
  [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'windows-defender-scan.js'))
}
else {
  [IO.Path]::GetFullPath($MalwareScannerPath)
}
$malwareReport = if ([string]::IsNullOrWhiteSpace($MalwareReportPath)) {
  [IO.Path]::GetFullPath((Join-Path $diagnosticRoot 'defender-installed.json'))
}
else {
  [IO.Path]::GetFullPath($MalwareReportPath)
}
$malwareReportRoot = Get-NormalizedDirectoryPath -Path (Split-Path -Parent $malwareReport)
$preinstallEvidenceProvided = -not [string]::IsNullOrWhiteSpace(
  $PreinstallMalwareReportPath
)
$preinstallReport = if ($preinstallEvidenceProvided) {
  [IO.Path]::GetFullPath($PreinstallMalwareReportPath)
}
else {
  Join-Path $malwareReportRoot 'defender-preinstall.json'
}
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
if (-not (Test-Path -LiteralPath $malwareScanner -PathType Leaf)) {
  throw 'MalwareScannerPath must identify the checked-in scanner.'
}
if (-not (Test-PathInsideRoot -Path $malwareReport -Root $runnerTemp)) {
  throw 'MalwareReportPath must be a child of RUNNER_TEMP.'
}
if (-not (Test-PathInsideRoot -Path $preinstallReport -Root $runnerTemp) -or
    -not (Get-NormalizedDirectoryPath -Path (Split-Path -Parent $preinstallReport)).Equals(
      $malwareReportRoot,
      [StringComparison]::OrdinalIgnoreCase
    )) {
  throw 'PreinstallMalwareReportPath must share the owned Defender report root.'
}
$malwareReportUsesDiagnosticRoot = $malwareReportRoot.Equals(
  $diagnosticRoot,
  [StringComparison]::OrdinalIgnoreCase
)
if (-not $malwareReportUsesDiagnosticRoot -and
    -not (Split-Path -Leaf $malwareReportRoot).StartsWith(
      'pp02-defender-reports-',
      [StringComparison]::OrdinalIgnoreCase
    )) {
  throw 'MalwareReportPath must use the diagnostic root or a pp02-defender-reports-* parent.'
}
foreach ($freshReport in @($malwareReport)) {
  if (Test-Path -LiteralPath $freshReport) {
    throw 'Microsoft Defender report paths must not exist before verification.'
  }
}
if ($preinstallEvidenceProvided) {
  if (-not (Test-Path -LiteralPath $preinstallReport -PathType Leaf)) {
    throw 'PreinstallMalwareReportPath must identify a preserved Defender report.'
  }
}
elseif (Test-Path -LiteralPath $preinstallReport) {
  throw 'Microsoft Defender preinstall report path must not exist before verification.'
}
New-Item -ItemType Directory -Path $diagnosticRoot -Force | Out-Null
New-Item -ItemType Directory -Path $malwareReportRoot -Force | Out-Null
$ownedProcessEvidencePath = Join-Path `
  $diagnosticRoot 'owned-process-cleanup-evidence.json'

$verificationStartedAt = Get-Date
$failureStage = 'preflight'
$stageProcess = '<not_started>'
$stageProcessStartedUtc = '<not_started>'
$stageProcessExitedUtc = '<not_observed>'
$stageProcessExitCode = '<not_observed>'
Set-Content `
  -LiteralPath (Join-Path $diagnosticRoot 'stage-report.txt') `
  -Value @(
    'WINDOWS_INSTALLER_STAGE_REPORT=AVAILABLE',
    "verification_start_utc=$($verificationStartedAt.ToUniversalTime().ToString('o'))",
    'current_stage=preflight'
  ) `
  -Encoding UTF8
$stageReportPath = Join-Path $diagnosticRoot 'stage-report.txt'

$expectedHead = $ExpectedCommitSha.Trim().ToLowerInvariant()
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

$installerDirectory = Split-Path -Parent $installer
$blockmap = "$installer.blockmap"
$latest = Join-Path $installerDirectory 'latest.yml'
$portableZip = if ([string]::IsNullOrWhiteSpace($PortableArchivePath)) {
  Join-Path $repoRoot "dist/pp02-ai-daily-stock-analysis-windows-noinstall-v$ExpectedVersion.zip"
}
else {
  [IO.Path]::GetFullPath($PortableArchivePath)
}
$checksum = "$portableZip.sha256"
$winUnpacked = Join-Path $installerDirectory 'win-unpacked'
$candidateExtract = Join-Path $runnerTemp "pp02-defender-extract-$expectedHead"
if (Test-Path -LiteralPath $candidateExtract) {
  throw 'Defender extraction root must not exist before verification.'
}

$acceptanceRoot = Join-Path $runnerTemp "pp02-config-acceptance-$expectedHead"
if (Test-Path -LiteralPath $acceptanceRoot) {
  throw 'Installed configuration acceptance root must not exist before verification.'
}
$acceptanceAppData = Join-Path $acceptanceRoot 'appdata'
$acceptanceLocalAppData = Join-Path $acceptanceRoot 'localappdata'
$desktopPackageMetadataPath = Join-Path $repoRoot 'apps/dsa-desktop/package.json'
$desktopPackageMetadata = Get-Content -LiteralPath $desktopPackageMetadataPath -Raw |
  ConvertFrom-Json
$desktopApplicationName = [string]$desktopPackageMetadata.productName
if ([string]::IsNullOrWhiteSpace($desktopApplicationName)) {
  $desktopApplicationName = [string]$desktopPackageMetadata.name
}
if ([string]::IsNullOrWhiteSpace($desktopApplicationName) -or
    [IO.Path]::GetFileName($desktopApplicationName) -ne $desktopApplicationName -or
    $desktopApplicationName -in @('.', '..')) {
  throw 'Desktop package metadata does not define a safe Electron application name.'
}
$acceptanceUserData = Join-Path $acceptanceAppData $desktopApplicationName
if (-not (Test-PathInsideRoot -Path $acceptanceUserData -Root $acceptanceAppData)) {
  throw 'Desktop userData acceptance path must stay inside verifier-owned APPDATA.'
}
$acceptanceReadyPath = Join-Path $acceptanceRoot 'mock-ready.json'
$acceptanceReceiptPath = Join-Path $acceptanceRoot 'mock-receipt.json'
$acceptanceMockStdout = Join-Path $acceptanceRoot 'mock-stdout.log'
$acceptanceMockStderr = Join-Path $acceptanceRoot 'mock-stderr.log'
$acceptanceConfigExport = Join-Path $acceptanceRoot 'config-export.json'
$acceptanceFullBackup = Join-Path $acceptanceRoot 'full-data-backup.json'
$installedConfigMock = Join-Path `
  $repoRoot 'apps/dsa-desktop/tests/installed-config-smoke-server.js'
$installedConfigVaultHarness = Join-Path `
  $repoRoot 'apps/dsa-desktop/tests/windows-installed-config-vault-harness.js'
$fakeCredentialScanner = Join-Path $repoRoot 'scripts/scan-windows-fake-credential.js'
foreach ($acceptanceSource in @(
  $installedConfigMock,
  $installedConfigVaultHarness,
  $fakeCredentialScanner
)) {
  if (-not (Test-Path -LiteralPath $acceptanceSource -PathType Leaf)) {
    throw 'Installed configuration acceptance source is missing.'
  }
}
New-Item -ItemType Directory -Path $acceptanceAppData -Force | Out-Null
New-Item -ItemType Directory -Path $acceptanceLocalAppData -Force | Out-Null

$appProcess = $null
$appExe = $null
$backendExe = $null
$desktopLog = $null
$uninstaller = $null
$uninstallAttempted = $false
$mockProcess = $null
$ownedRootValidated = $true
$savedGithubActions = [Environment]::GetEnvironmentVariable('GITHUB_ACTIONS', 'Process')
$savedAppData = [Environment]::GetEnvironmentVariable('APPDATA', 'Process')
$savedLocalAppData = [Environment]::GetEnvironmentVariable('LOCALAPPDATA', 'Process')
$savedAcceptanceHead = [Environment]::GetEnvironmentVariable(
  'DSA_CONFIG_ACCEPTANCE_HEAD',
  'Process'
)
$savedAcceptanceReceipt = [Environment]::GetEnvironmentVariable(
  'DSA_CONFIG_ACCEPTANCE_RECEIPT_PATH',
  'Process'
)
$savedAcceptanceReady = [Environment]::GetEnvironmentVariable(
  'DSA_CONFIG_ACCEPTANCE_READY_PATH',
  'Process'
)
$savedAcceptanceUserData = [Environment]::GetEnvironmentVariable(
  'DSA_CONFIG_ACCEPTANCE_USER_DATA',
  'Process'
)
$savedAcceptanceEnvPath = [Environment]::GetEnvironmentVariable(
  'DSA_CONFIG_ACCEPTANCE_ENV_PATH',
  'Process'
)
$savedAcceptanceBackendVersion = [Environment]::GetEnvironmentVariable(
  'DSA_CONFIG_ACCEPTANCE_BACKEND_VERSION',
  'Process'
)
$savedInstallerDiagnosticRoot = [Environment]::GetEnvironmentVariable(
  'DSA_INSTALLER_DIAGNOSTIC_ROOT',
  'Process'
)
try {
  Write-Output "WINDOWS_INSTALLER_EXPECTED_VERSION=$ExpectedVersion"
  Write-Output "WINDOWS_INSTALLER_HEAD=$expectedHead"
  if ($RequireValidSignature) {
    Write-Output 'WINDOWS_SIGNATURE_POLICY=REQUIRE_VALID'
  }
  else {
    Write-Output 'WINDOWS_SIGNATURE_POLICY=AUDIT_ONLY'
  }
  $installerSignatureStatus = Get-AuthenticodeStatus -Path $installer
  Write-Output "WINDOWS_INSTALLER_SIGNATURE_STATUS=$installerSignatureStatus"
  if ($RequireValidSignature -and $installerSignatureStatus -ne 'Valid') {
    throw "Authenticode signature is required but installer status is $installerSignatureStatus."
  }

  $failureStage = 'candidate_payload_defender_scan'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  if (-not $preinstallEvidenceProvided) {
    foreach ($candidateTarget in @(
      $installer,
      $blockmap,
      $latest,
      $portableZip,
      $checksum,
      $winUnpacked
    )) {
      if (-not (Test-Path -LiteralPath $candidateTarget)) {
        throw "Microsoft Defender candidate target is missing: $(Split-Path -Leaf $candidateTarget)."
      }
    }
    Expand-Archive -LiteralPath $portableZip -DestinationPath $candidateExtract
    node $malwareScanner `
      --head $expectedHead `
      --report $preinstallReport `
      --path $installer `
      --path $blockmap `
      --path $latest `
      --path $portableZip `
      --path $checksum `
      --path $winUnpacked `
      --path $candidateExtract
    if ($LASTEXITCODE -ne 0) {
      throw "Microsoft Defender rejected the candidate payload with exit code $LASTEXITCODE."
    }
  }
  if (-not (Test-Path -LiteralPath $preinstallReport -PathType Leaf)) {
    throw 'Microsoft Defender did not preserve the candidate-payload report.'
  }
  $preinstallResult = Get-Content -LiteralPath $preinstallReport -Raw |
    ConvertFrom-Json
  if ([string]$preinstallResult.status -ne 'PASS' -or
      [string]$preinstallResult.head -ne $expectedHead) {
    throw 'Microsoft Defender candidate-payload report identity is invalid.'
  }
  Write-Output 'WINDOWS_CANDIDATE_DEFENDER_SCAN=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'installer_process'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  $stageProcess = 'installer'
  $stageProcessStartedUtc = (Get-Date).ToUniversalTime().ToString('o')
  $stageProcessExitedUtc = '<not_observed>'
  $stageProcessExitCode = '<not_observed>'
  $installProcess = Invoke-PP02BoundedProcess `
    -FilePath $installer `
    -ArgumentList "/S /D=$ownedRoot" `
    -TimeoutSeconds $InstallTimeoutSeconds `
    -Stage $failureStage `
    -StageReportPath $stageReportPath
  $stageProcessExitedUtc = (Get-Date).ToUniversalTime().ToString('o')
  $stageProcessExitCode = [string]$installProcess.ExitCode
  Write-Output "WINDOWS_INSTALLER_EXIT_CODE=$($installProcess.ExitCode)"
  if ($installProcess.ExitCode -ne 0) {
    throw "Installer exited with code $($installProcess.ExitCode)."
  }
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'installed_payload'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  $appExe = Join-Path $ownedRoot 'PP02 AI Daily Stock Analysis.exe'
  $appAsar = Join-Path $ownedRoot 'resources/app.asar'
  $backendExe = Join-Path $ownedRoot 'resources/backend/stock_analysis/stock_analysis.exe'
  foreach ($requiredPath in @($appExe, $appAsar, $backendExe)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
      throw "Installed package is missing required file: $(Split-Path -Leaf $requiredPath)."
    }
  }

  $appSignatureStatus = Get-AuthenticodeStatus -Path $appExe
  Write-Output "WINDOWS_APP_SIGNATURE_STATUS=$appSignatureStatus"
  if ($RequireValidSignature -and $appSignatureStatus -ne 'Valid') {
    throw "Authenticode signature is required but application status is $appSignatureStatus."
  }

  $uninstallers = @(Get-ChildItem -LiteralPath $ownedRoot -Filter 'Uninstall *.exe' -File)
  if ($uninstallers.Count -ne 1) {
    throw "Installed package must contain exactly one uninstaller; found $($uninstallers.Count)."
  }
  $uninstaller = $uninstallers[0].FullName

  $appFileVersion = [string](Get-Item -LiteralPath $appExe).VersionInfo.FileVersion
  $appProductVersion = [string](Get-Item -LiteralPath $appExe).VersionInfo.ProductVersion
  foreach ($versionResource in @(
    @{ Name = 'FileVersion'; Value = $appFileVersion },
    @{ Name = 'ProductVersion'; Value = $appProductVersion }
  )) {
    $versionMatch = [regex]::Match(
      $versionResource.Value,
      '^(\d+)\.(\d+)\.(\d+)'
    )
    if (-not $versionMatch.Success -or $versionMatch.Value -ne $ExpectedVersion) {
      throw "Installed executable $($versionResource.Name) does not match $ExpectedVersion."
    }
  }
  Write-Output "WINDOWS_APP_FILE_VERSION=$appFileVersion"
  Write-Output "WINDOWS_APP_PRODUCT_VERSION=$appProductVersion"

  $webBuildInfoCandidates = @(
    (Join-Path $ownedRoot 'resources/backend/stock_analysis/_internal/static/build-info.json'),
    (Join-Path $ownedRoot 'resources/backend/stock_analysis/static/build-info.json')
  )
  $webBuildInfoPaths = @(
    $webBuildInfoCandidates |
      Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }
  )
  if ($webBuildInfoPaths.Count -ne 1) {
    throw "Installed package must contain exactly one Web build-info.json; found $($webBuildInfoPaths.Count)."
  }
  $webBuildInfo = Get-Content -LiteralPath $webBuildInfoPaths[0] -Raw |
    ConvertFrom-Json
  if ([string]$webBuildInfo.version -ne $ExpectedVersion) {
    throw "Installed Web build metadata version does not match $ExpectedVersion."
  }
  Write-Output "WINDOWS_WEB_BUILD_VERSION=$($webBuildInfo.version)"

  $failureStage = 'uninstall_registration'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
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

  $failureStage = 'installed_payload_defender_scan'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  node $malwareScanner `
    --head $expectedHead `
    --report $malwareReport `
    --path $ownedRoot
  if ($LASTEXITCODE -ne 0) {
    throw "Microsoft Defender rejected the installed payload with exit code $LASTEXITCODE."
  }
  if (-not (Test-Path -LiteralPath $malwareReport -PathType Leaf)) {
    throw 'Microsoft Defender did not preserve the installed-payload report.'
  }
  $malwareResult = Get-Content -LiteralPath $malwareReport -Raw |
    ConvertFrom-Json
  if ([string]$malwareResult.status -ne 'PASS' -or
      [string]$malwareResult.head -ne $expectedHead) {
    throw 'Microsoft Defender installed-payload report identity is invalid.'
  }
  Write-Output 'WINDOWS_INSTALLED_DEFENDER_SCAN=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  [Environment]::SetEnvironmentVariable('GITHUB_ACTIONS', 'false', 'Process')
  [Environment]::SetEnvironmentVariable(
    'DSA_INSTALLER_DIAGNOSTIC_ROOT',
    $diagnosticRoot,
    'Process'
  )
  [Environment]::SetEnvironmentVariable('APPDATA', $acceptanceAppData, 'Process')
  [Environment]::SetEnvironmentVariable(
    'LOCALAPPDATA',
    $acceptanceLocalAppData,
    'Process'
  )
  $failureStage = 'installed_app_startup'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  $stageProcess = 'installed_app'
  $stageProcessStartedUtc = (Get-Date).ToUniversalTime().ToString('o')
  $stageProcessExitedUtc = '<not_observed>'
  $stageProcessExitCode = '<not_observed>'
  $appProcess = Start-Process -FilePath $appExe -WorkingDirectory $ownedRoot -PassThru
  $desktopLog = Join-Path $ownedRoot 'logs/desktop.log'
  $startupDeadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
  $startupReady = $false
  do {
    $appProcess.Refresh()
    if ($appProcess.HasExited) {
      $stageProcessExitedUtc = (Get-Date).ToUniversalTime().ToString('o')
      $stageProcessExitCode = [string]$appProcess.ExitCode
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
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'installed_config_validation'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_HEAD',
    $expectedHead,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_RECEIPT_PATH',
    $acceptanceReceiptPath,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_READY_PATH',
    $acceptanceReadyPath,
    'Process'
  )
  $nodeCommand = (Get-Command node -ErrorAction Stop).Source
  $mockProcess = Start-Process `
    -FilePath $nodeCommand `
    -ArgumentList @($installedConfigMock) `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $acceptanceMockStdout `
    -RedirectStandardError $acceptanceMockStderr `
    -PassThru
  $mockReadyDeadline = (Get-Date).AddSeconds(20)
  do {
    $mockProcess.Refresh()
    if ($mockProcess.HasExited) {
      throw 'Installed configuration mock exited before readiness.'
    }
    if (Test-Path -LiteralPath $acceptanceReadyPath -PathType Leaf) {
      break
    }
    Start-Sleep -Milliseconds 200
  } while ((Get-Date) -lt $mockReadyDeadline)
  if (-not (Test-Path -LiteralPath $acceptanceReadyPath -PathType Leaf)) {
    throw 'Installed configuration mock did not become ready within 20 seconds.'
  }
  $mockReady = Get-Content -LiteralPath $acceptanceReadyPath -Raw | ConvertFrom-Json
  if ([int]$mockReady.schemaVersion -ne 1 -or
      [string]$mockReady.head -ne $expectedHead -or
      [string]$mockReady.host -ne '127.0.0.1' -or
      [int]$mockReady.port -lt 1 -or
      [int]$mockReady.port -gt 65535) {
    throw 'Installed configuration mock readiness identity is invalid.'
  }

  $desktopLines = Get-DesktopDiagnosticLines -LogPath $desktopLog
  $backendPort = Get-DesktopBackendPort -DesktopLines $desktopLines
  $backendBaseUrl = "http://127.0.0.1:$backendPort"
  $mockBaseUrl = "http://127.0.0.1:$([int]$mockReady.port)/v1"
  $initialConfig = Invoke-PP02LocalJsonRequest `
    -Method 'GET' `
    -Uri "$backendBaseUrl/api/v1/system/config?include_schema=false" `
    -TimeoutSeconds 30
  if ([string]$initialConfig.config_version -notmatch '^sha256:[0-9a-f]{64}$') {
    throw 'Installed backend returned an invalid initial configuration version.'
  }

  $fakeCredential = Get-PP02SyntheticCredential -Head $expectedHead
  $publicAcceptanceItems = @(
    [ordered]@{ key = 'GENERATION_BACKEND'; value = 'codex_cli' },
    [ordered]@{ key = 'GENERATION_FALLBACK_BACKEND'; value = 'litellm' },
    [ordered]@{ key = 'LLM_CHANNELS'; value = 'aihubmix' },
    [ordered]@{ key = 'LLM_AIHUBMIX_PROTOCOL'; value = 'openai' },
    [ordered]@{ key = 'LLM_AIHUBMIX_BASE_URL'; value = $mockBaseUrl },
    [ordered]@{ key = 'LLM_AIHUBMIX_MODELS'; value = 'openai/pp02-acceptance' },
    [ordered]@{ key = 'LITELLM_MODEL'; value = 'openai/pp02-acceptance' },
    [ordered]@{ key = 'LITELLM_FALLBACK_MODELS'; value = '' },
    [ordered]@{ key = 'AGENT_LITELLM_MODEL'; value = '' }
  )
  $validationItems = @($publicAcceptanceItems) + @(
    [ordered]@{ key = 'LLM_AIHUBMIX_API_KEY'; value = $fakeCredential }
  )
  $validationResult = Invoke-PP02LocalJsonRequest `
    -Method 'POST' `
    -Uri "$backendBaseUrl/api/v1/system/config/validate" `
    -Body ([ordered]@{ items = $validationItems }) `
    -TimeoutSeconds 30
  if (-not [bool]$validationResult.valid) {
    throw 'Fresh installed AIHubMix configuration validation failed.'
  }
  Write-Output 'WINDOWS_INSTALLED_CONFIG_VALIDATION=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'installed_config_save'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  $backendItems = @($publicAcceptanceItems) + @(
    [ordered]@{ key = 'LLM_AIHUBMIX_API_KEY'; value = '******' }
  )
  $saveResult = Invoke-PP02LocalJsonRequest `
    -Method 'PUT' `
    -Uri "$backendBaseUrl/api/v1/system/config" `
    -Body ([ordered]@{
      config_version = [string]$initialConfig.config_version
      mask_token = '******'
      reload_now = $false
      items = $backendItems
    }) `
    -TimeoutSeconds 30
  if (-not [bool]$saveResult.success -or
      [bool]$saveResult.reload_triggered -or
      [string]$saveResult.config_version -notmatch '^sha256:[0-9a-f]{64}$' -or
      [string]$saveResult.config_version -eq [string]$initialConfig.config_version) {
    throw 'Installed backend did not persist the public AI configuration generation.'
  }
  Write-Output 'WINDOWS_INSTALLED_CONFIG_SAVE=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'installed_app_shutdown'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  Stop-StartedProcessTree -Process $appProcess
  $stageProcessExitedUtc = (Get-Date).ToUniversalTime().ToString('o')
  $stageProcessExitCode = '0'
  $appProcess = $null
  Write-Output 'WINDOWS_INSTALLED_APP_EXIT_VALIDATION=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'installed_config_vault_commit'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_USER_DATA',
    $acceptanceUserData,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_ENV_PATH',
    (Join-Path $ownedRoot '.env'),
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_BACKEND_VERSION',
    [string]$saveResult.config_version,
    'Process'
  )
  $npmCommand = (Get-Command npm.cmd -ErrorAction Stop).Source
  $vaultProcess = Invoke-PP02BoundedProcess `
    -FilePath $npmCommand `
    -ArgumentList @(
      '--prefix',
      'apps/dsa-desktop',
      '--silent',
      'run',
      'test:windows-installed-config-vault'
    ) `
    -WorkingDirectory $repoRoot `
    -TimeoutSeconds 120 `
    -Stage $failureStage `
    -StageReportPath $stageReportPath
  if ($vaultProcess.ExitCode -ne 0 -or
      -not (Test-Path `
        -LiteralPath (Join-Path $acceptanceUserData 'secure-credentials.v1.json') `
        -PathType Leaf)) {
    throw 'Windows safeStorage did not commit the installed AI credential.'
  }
  Write-Output 'WINDOWS_INSTALLED_CONFIG_VAULT=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $restartReadyMarkerBaseline = Get-DesktopReadyMarkerCount -LogPath $desktopLog
  $failureStage = 'installed_app_restart'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  $stageProcess = 'installed_app_restart'
  $stageProcessStartedUtc = (Get-Date).ToUniversalTime().ToString('o')
  $stageProcessExitedUtc = '<not_observed>'
  $stageProcessExitCode = '<not_observed>'
  $appProcess = Start-Process -FilePath $appExe -WorkingDirectory $ownedRoot -PassThru
  $restartDeadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
  $restartReady = $false
  do {
    $appProcess.Refresh()
    if ($appProcess.HasExited) {
      $stageProcessExitedUtc = (Get-Date).ToUniversalTime().ToString('o')
      $stageProcessExitCode = [string]$appProcess.ExitCode
      Write-StartupDiagnostics -LogPath $desktopLog
      throw "Restarted installed application exited before readiness with code $($appProcess.ExitCode)."
    }
    $restartReadyMarkerCount = Get-DesktopReadyMarkerCount -LogPath $desktopLog
    if ($restartReadyMarkerCount -gt $restartReadyMarkerBaseline) {
      $restartReady = $true
      break
    }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $restartDeadline)
  if (-not $restartReady) {
    Write-StartupDiagnostics -LogPath $desktopLog
    throw "Restarted installed application did not reach readiness within $StartupTimeoutSeconds seconds."
  }
  Write-Output 'WINDOWS_INSTALLED_APP_RESTART_VALIDATION=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $restartedDesktopLines = Get-DesktopDiagnosticLines -LogPath $desktopLog
  $restartedBackendPort = Get-DesktopBackendPort -DesktopLines $restartedDesktopLines
  $backendBaseUrl = "http://127.0.0.1:$restartedBackendPort"
  $failureStage = 'installed_config_masked_restart'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  $restartedConfig = Invoke-PP02LocalJsonRequest `
    -Method 'GET' `
    -Uri "$backendBaseUrl/api/v1/system/config?include_schema=true" `
    -TimeoutSeconds 30
  $expectedPublicValues = [ordered]@{
    GENERATION_BACKEND = 'codex_cli'
    GENERATION_FALLBACK_BACKEND = 'litellm'
    LLM_CHANNELS = 'aihubmix'
    LLM_AIHUBMIX_PROTOCOL = 'openai'
    LLM_AIHUBMIX_BASE_URL = $mockBaseUrl
    LLM_AIHUBMIX_MODELS = 'openai/pp02-acceptance'
    LITELLM_MODEL = 'openai/pp02-acceptance'
    LITELLM_FALLBACK_MODELS = ''
    AGENT_LITELLM_MODEL = ''
  }
  foreach ($entry in $expectedPublicValues.GetEnumerator()) {
    $item = Get-PP02ConfigItem -Config $restartedConfig -Key $entry.Key
    if ([string]$item.value -ne [string]$entry.Value) {
      throw "Installed configuration did not preserve $($entry.Key) after restart."
    }
  }
  $secretItem = Get-PP02ConfigItem `
    -Config $restartedConfig `
    -Key 'LLM_AIHUBMIX_API_KEY'
  if ([string]$secretItem.value -ne '******' -or
      -not [bool]$secretItem.is_masked -or
      -not [bool]$secretItem.secure_value_exists -or
      [string]$secretItem.credential_source -ne 'windows_dpapi') {
    throw 'Installed AI credential did not return as a Windows DPAPI mask after restart.'
  }
  Write-Output 'WINDOWS_INSTALLED_CONFIG_MASKED_RESTART=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'installed_config_smoke'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  $smokeResult = Invoke-PP02LocalJsonRequest `
    -Method 'POST' `
    -Uri "$backendBaseUrl/api/v1/system/config/generation-backends/smoke-test" `
    -Body ([ordered]@{
      backend_id = 'litellm'
      mode = 'json'
      items = @()
      mask_token = '******'
      timeout_seconds = 30
    }) `
    -TimeoutSeconds 45
  if (-not [bool]$smokeResult.success -or
      [string]$smokeResult.status.backend_id -ne 'litellm' -or
      [string]$smokeResult.status.health_status -ne 'passed') {
    throw 'Installed generation backend smoke request did not pass.'
  }
  if (-not (Test-Path -LiteralPath $acceptanceReceiptPath -PathType Leaf)) {
    throw 'Installed generation backend smoke request did not preserve a receipt.'
  }
  $smokeReceipt = Get-Content -LiteralPath $acceptanceReceiptPath -Raw |
    ConvertFrom-Json
  if ([int]$smokeReceipt.schemaVersion -ne 1 -or
      [string]$smokeReceipt.head -ne $expectedHead -or
      -not [bool]$smokeReceipt.authorizationMatched -or
      -not [bool]$smokeReceipt.routeMatched -or
      -not [bool]$smokeReceipt.modelMatched -or
      [int]$smokeReceipt.requestCount -ne 1) {
    throw 'Installed generation backend smoke receipt is invalid.'
  }
  if (-not $mockProcess.WaitForExit(20000)) {
    Stop-StartedProcessTree -Process $mockProcess
    throw 'Installed configuration mock did not stop after its accepted request.'
  }
  if ($mockProcess.ExitCode -ne 0) {
    throw 'Installed configuration mock exited with a failure.'
  }
  $mockProcess = $null
  Write-Output 'WINDOWS_INSTALLED_CONFIG_SMOKE=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'installed_config_exports'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  $configExportResult = Invoke-PP02LocalJsonRequest `
    -Method 'GET' `
    -Uri "$backendBaseUrl/api/v1/system/config/export" `
    -TimeoutSeconds 30 `
    -RawOutputPath $acceptanceConfigExport
  if (-not [bool]$configExportResult.credentials_excluded -or
      [string]$configExportResult.config_version -ne [string]$restartedConfig.config_version -or
      [string]$configExportResult.content -match 'LLM_AIHUBMIX_API_KEY') {
    throw 'Installed configuration export did not exclude credentials.'
  }
  $null = Invoke-PP02LocalJsonRequest `
    -Method 'GET' `
    -Uri "$backendBaseUrl/api/v1/system/full-data-backup/export" `
    -TimeoutSeconds 60 `
    -RawOutputPath $acceptanceFullBackup
  foreach ($exportPath in @($acceptanceConfigExport, $acceptanceFullBackup)) {
    if (-not (Test-Path -LiteralPath $exportPath -PathType Leaf) -or
        (Get-Content -LiteralPath $exportPath -Raw).Contains($fakeCredential)) {
      throw 'Installed export or complete backup contains synthetic credential plaintext.'
    }
  }
  Write-Output 'WINDOWS_INSTALLED_CONFIG_EXPORTS=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'installed_config_leakage_scan'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  node $fakeCredentialScanner `
    --head $expectedHead `
    --path $ownedRoot `
    --path $acceptanceRoot `
    --path $diagnosticRoot
  if ($LASTEXITCODE -ne 0) {
    throw 'Installed configuration synthetic credential leakage scan failed.'
  }
  Write-Output 'WINDOWS_INSTALLED_CONFIG_LEAKAGE_SCAN=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $uninstallAttempted = $true
  $failureStage = 'uninstaller_process'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
  $stageProcess = 'uninstaller'
  $stageProcessStartedUtc = (Get-Date).ToUniversalTime().ToString('o')
  $stageProcessExitedUtc = '<not_observed>'
  $stageProcessExitCode = '<not_observed>'
  $uninstallProcess = Invoke-PP02BoundedProcess `
    -FilePath $uninstaller `
    -ArgumentList '/S /KEEP_APP_DATA /currentuser' `
    -TimeoutSeconds $UninstallTimeoutSeconds `
    -Stage $failureStage `
    -StageReportPath $stageReportPath
  $stageProcessExitedUtc = (Get-Date).ToUniversalTime().ToString('o')
  $stageProcessExitCode = [string]$uninstallProcess.ExitCode
  Write-Output "WINDOWS_UNINSTALLER_EXIT_CODE=$($uninstallProcess.ExitCode)"
  if ($uninstallProcess.ExitCode -ne 0) {
    throw "Uninstaller exited with code $($uninstallProcess.ExitCode)."
  }
  if (-not (Test-Path -LiteralPath $ownedProcessEvidencePath -PathType Leaf)) {
    throw 'Official uninstaller did not preserve owned-process helper evidence.'
  }
  $ownedProcessEvidence = Get-Content `
    -LiteralPath $ownedProcessEvidencePath `
    -Raw | ConvertFrom-Json
  if ([int]$ownedProcessEvidence.schemaVersion -ne 1 -or
      [string]$ownedProcessEvidence.status -ne 'PASS' -or
      [int]$ownedProcessEvidence.initialOwnedProcessCount -lt 1 -or
      [int]$ownedProcessEvidence.remainingOwnedProcessCount -ne 0) {
    throw 'Owned-process helper evidence did not prove live-process cleanup.'
  }
  Write-Output (
    'WINDOWS_UNINSTALL_HELPER_INITIAL_OWNED_COUNT=' +
    [int]$ownedProcessEvidence.initialOwnedProcessCount
  )
  Write-Output 'WINDOWS_UNINSTALL_HELPER_REMAINING_OWNED_COUNT=0'
  Write-Output 'WINDOWS_UNINSTALL_HELPER_EXECUTION_VALIDATION=PASS'
  $appProcess.Refresh()
  if (-not $appProcess.HasExited) {
    throw 'One normal uninstaller run did not close the running installed application.'
  }
  $ownedProcessesAfterUninstall = @(
    Get-ExactOwnedProcesses `
      -AppExecutable $appExe `
      -BackendExecutable $backendExe
  )
  if ($ownedProcessesAfterUninstall.Count -ne 0) {
    throw 'One normal uninstaller run left a product-owned process behind.'
  }
  $appProcess = $null
  Write-Output 'WINDOWS_OWNED_PROCESS_COUNT_AFTER_UNINSTALL=0'
  Write-Output 'WINDOWS_UNINSTALL_LIVE_PROCESS_VALIDATION=PASS'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'

  $failureStage = 'uninstall_cleanup'
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'ENTER'
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
  Add-InstallerStageReport -Path $stageReportPath -Stage $failureStage -Status 'PASS'
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
      -FailureStage $failureStage `
      -StageProcess $stageProcess `
      -StageProcessStartedUtc $stageProcessStartedUtc `
      -StageProcessExitedUtc $stageProcessExitedUtc `
      -StageProcessExitCode $stageProcessExitCode `
      -Installer $installer `
      -OwnedRoot $ownedRoot `
      -AppExecutable $appExe `
      -BackendExecutable $backendExe `
      -AppProcess $appProcess `
      -DesktopLog $desktopLog
    Write-Output 'WINDOWS_INSTALLER_DIAGNOSTIC=AVAILABLE'
  }
  catch {
    $captureFailure = $_
    try {
      Set-ProtectedDiagnosticContent `
        -Path (Join-Path $diagnosticRoot 'diagnostic-capture-fallback.txt') `
        -Text (@(
          'WINDOWS_INSTALLER_DIAGNOSTIC=CAPTURE_FAILED',
          "failure_stage=$failureStage",
          "diagnostic_capture_exception_type=$($captureFailure.Exception.GetType().FullName)"
        ) -join [Environment]::NewLine)
    }
    catch {
      Write-Warning 'Diagnostic fallback capture could not be completed.'
    }
    Write-Warning "Diagnostic capture failed with $($captureFailure.Exception.GetType().FullName)."
  }
  throw $originalFailure
}
finally {
  if ($mockProcess) {
    try {
      Stop-StartedProcessTree -Process $mockProcess
    }
    catch {
      Write-Warning 'Installed configuration mock cleanup could not be completed.'
    }
  }
  if ($appProcess) {
    Stop-StartedProcessTree -Process $appProcess
  }
  if ($uninstaller -and -not $uninstallAttempted -and
      (Test-Path -LiteralPath $uninstaller -PathType Leaf)) {
    try {
      $cleanupUninstall = Invoke-PP02BoundedProcess `
        -FilePath $uninstaller `
        -ArgumentList '/S /KEEP_APP_DATA /currentuser' `
        -TimeoutSeconds $UninstallTimeoutSeconds `
        -Stage 'cleanup_uninstaller_process' `
        -StageReportPath $stageReportPath
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
  [Environment]::SetEnvironmentVariable('APPDATA', $savedAppData, 'Process')
  [Environment]::SetEnvironmentVariable(
    'LOCALAPPDATA',
    $savedLocalAppData,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_HEAD',
    $savedAcceptanceHead,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_RECEIPT_PATH',
    $savedAcceptanceReceipt,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_READY_PATH',
    $savedAcceptanceReady,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_USER_DATA',
    $savedAcceptanceUserData,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_ENV_PATH',
    $savedAcceptanceEnvPath,
    'Process'
  )
  [Environment]::SetEnvironmentVariable(
    'DSA_CONFIG_ACCEPTANCE_BACKEND_VERSION',
    $savedAcceptanceBackendVersion,
    'Process'
  )
  if ($ownedRootValidated) {
    Remove-OwnedRootWithRetry -OwnedRoot $ownedRoot
  }
  if ($candidateExtract -and (Test-Path -LiteralPath $candidateExtract)) {
    Remove-Item -LiteralPath $candidateExtract -Recurse -Force
  }
  if ($acceptanceRoot -and (Test-Path -LiteralPath $acceptanceRoot)) {
    Remove-Item -LiteralPath $acceptanceRoot -Recurse -Force
  }
}
