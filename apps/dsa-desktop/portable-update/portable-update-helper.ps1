param(
  [Parameter(Mandatory=$true)][string]$PlanPath,
  [Parameter(Mandatory=$true)][string]$Token,
  [Parameter(Mandatory=$true)][int]$ParentPid
)
$ErrorActionPreference = 'Stop'
$ProductId = 'com.hanchanqaq.pp02.aidailystockanalysis'
$plan = Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
if ($plan.schemaVersion -ne 1 -or $plan.productId -ne $ProductId -or $plan.token -cne $Token) { throw 'Invalid update plan identity.' }
$root = [IO.Path]::GetFullPath($plan.currentRoot); $stage = [IO.Path]::GetFullPath($plan.stagedRoot); $backup = [IO.Path]::GetFullPath($plan.backupRoot)
if ($root -eq $stage -or $root -eq $backup -or -not (Test-Path -LiteralPath (Join-Path $stage $plan.manifestName))) { throw 'Invalid update roots.' }
function Resolve-Child([string]$Base, [string]$Relative) {
  if ([IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[\\/])\.\.([\\/]|$)' -or $Relative -match ':') { throw 'Unsafe plan path.' }
  $candidate = [IO.Path]::GetFullPath((Join-Path $Base $Relative))
  if (-not $candidate.StartsWith($Base + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Plan path escaped root.' }
  return $candidate
}
function Write-Result([string]$Status, [string[]]$Errors) {
  @{ status=$Status; errors=$Errors; recordedAt=(Get-Date).ToUniversalTime().ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath $plan.resultLog -Encoding UTF8
}
try { Wait-Process -Id $ParentPid -Timeout 60 -ErrorAction SilentlyContinue } catch {}
if (Get-Process -Id $ParentPid -ErrorAction SilentlyContinue) { throw 'Old Electron process did not exit.' }
$runtime = $null; $programBackup = Join-Path $backup 'program'; $applied = @(); $newProcess = $null
try {
$runtimePaths = @('.env','data/stock_analysis.db','data/stock_analysis.db-wal','data/stock_analysis.db-shm',$plan.manifestName)
$runtimeState = @{}; $runtimeBackup = Join-Path $backup 'runtime'; New-Item -ItemType Directory -Path $runtimeBackup -Force | Out-Null
foreach ($relative in $runtimePaths) {
  $source = Resolve-Child $root $relative; $exists = Test-Path -LiteralPath $source; $runtimeState[$relative] = @{ existed=$exists }
  if ($exists) { $saved = Resolve-Child $runtimeBackup $relative; New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($saved)) -Force | Out-Null; Copy-Item -LiteralPath $source -Destination $saved -Force }
}
@{ schemaVersion=1; paths=$runtimeState } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $plan.runtimeState -Encoding UTF8
$runtime = Get-Content -LiteralPath $plan.runtimeState -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Path $programBackup -Force | Out-Null
  foreach ($relative in @($plan.replace) + @($plan.remove)) {
    if ($relative -eq '.env' -or $relative.StartsWith('data/') -or $relative.StartsWith('logs/')) { throw 'Protected path in plan.' }
    $old = Resolve-Child $root $relative
    if (Test-Path -LiteralPath $old) { $saved = Resolve-Child $programBackup $relative; New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($saved)) -Force | Out-Null; Copy-Item -LiteralPath $old -Destination $saved -Force }
    $applied += $relative
  }
  foreach ($relative in $plan.replace) { $source = Resolve-Child $stage $relative; $target = Resolve-Child $root $relative; New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null; Copy-Item -LiteralPath $source -Destination $target -Force }
  foreach ($relative in $plan.remove) { Remove-Item -LiteralPath (Resolve-Child $root $relative) -Recurse -Force -ErrorAction SilentlyContinue }
  Copy-Item -LiteralPath (Join-Path $stage $plan.manifestName) -Destination (Join-Path $root $plan.manifestName) -Force
  $exe = Resolve-Child $root $plan.entryExecutable
  $args = @('--pp02-update-token', $Token, '--pp02-update-plan', $PlanPath, '--pp02-ready-signal', $plan.readySignal)
  $newProcess = Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -PassThru
  $deadline = (Get-Date).AddSeconds(90)
  do {
    Start-Sleep -Seconds 2
    if (Test-Path -LiteralPath $plan.readySignal) {
      $ready = Get-Content -LiteralPath $plan.readySignal -Raw | ConvertFrom-Json
      if ($ready.token -ceq $Token -and $ready.productId -eq $ProductId -and $ready.version -eq $plan.targetVersion -and $ready.homeLoaded -eq $true -and $ready.port -ge 1 -and $ready.port -le 65535) {
        $health = Invoke-WebRequest -Uri "http://127.0.0.1:$($ready.port)/api/health" -UseBasicParsing -TimeoutSec 5
        $home = Invoke-WebRequest -Uri "http://127.0.0.1:$($ready.port)/" -UseBasicParsing -TimeoutSec 5
        if ($health.StatusCode -eq 200 -and $home.StatusCode -eq 200) { Write-Result 'success' @(); exit 0 }
      }
    }
  } while ((Get-Date) -lt $deadline)
  throw 'New version readiness handshake failed.'
} catch {
  $restoreErrors = @("update: $($_.Exception.Message)")
  if ($newProcess) { try { & taskkill.exe /PID $newProcess.Id /T /F | Out-Null; try { Wait-Process -Id $newProcess.Id -Timeout 15 -ErrorAction SilentlyContinue } catch {}; if (Get-Process -Id $newProcess.Id -ErrorAction SilentlyContinue) { throw 'New Electron process tree is still running.' } } catch { $restoreErrors += "stop-new-tree: $($_.Exception.Message)" } }
  foreach ($relative in $applied) {
    try { $target = Resolve-Child $root $relative; $saved = Resolve-Child $programBackup $relative; if (Test-Path -LiteralPath $saved) { New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null; Copy-Item -LiteralPath $saved -Destination $target -Force } else { Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue } } catch { $restoreErrors += "program:$relative`: $($_.Exception.Message)" }
  }
  foreach ($property in @($runtime.paths.PSObject.Properties)) {
    $relative = $property.Name; $target = Resolve-Child $root $relative; $saved = Resolve-Child (Join-Path $backup 'runtime') $relative
    try { if ($property.Value.existed -eq $true) { New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null; Copy-Item -LiteralPath $saved -Destination $target -Force } else { Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue } } catch { $restoreErrors += "runtime:$relative`: $($_.Exception.Message)" }
  }
  if ($restoreErrors.Count -gt 1) { Write-Result 'restore-failed' $restoreErrors; exit 2 }
  try { Start-Process -FilePath (Resolve-Child $root $plan.entryExecutable) -WindowStyle Hidden; Write-Result 'restored' $restoreErrors; exit 1 } catch { $restoreErrors += "restart-old: $($_.Exception.Message)"; Write-Result 'restore-failed' $restoreErrors; exit 2 }
}
