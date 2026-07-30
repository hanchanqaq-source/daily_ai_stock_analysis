param(
  [Parameter(Mandatory=$true)][string]$PlanPath,
  [Parameter(Mandatory=$true)][string]$Token,
  [Parameter(Mandatory=$true)][int]$ParentPid
)
$ErrorActionPreference = 'Stop'
$plan = Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
if ($plan.schemaVersion -ne 1 -or $plan.productId -ne 'com.hanchanqaq.pp02.aidailystockanalysis' -or $plan.token -cne $Token) { throw 'Invalid update plan identity.' }
$root = [IO.Path]::GetFullPath($plan.currentRoot); $stage = [IO.Path]::GetFullPath($plan.stagedRoot); $backup = [IO.Path]::GetFullPath($plan.backupRoot)
if ($root -eq $stage -or $root -eq $backup -or -not (Test-Path -LiteralPath (Join-Path $stage $plan.manifestName))) { throw 'Invalid update roots.' }
function Resolve-Child([string]$Base, [string]$Relative) {
  if ([IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[\\/])\.\.([\\/]|$)' -or $Relative -match ':') { throw 'Unsafe plan path.' }
  $candidate = [IO.Path]::GetFullPath((Join-Path $Base $Relative)); if (-not $candidate.StartsWith($Base + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Plan path escaped root.' }; $candidate
}
try { Wait-Process -Id $ParentPid -Timeout 60 -ErrorAction SilentlyContinue } catch {}
New-Item -ItemType Directory -Path $backup -Force | Out-Null
$protected = @('.env','data','logs'); $applied = @()
try {
  foreach ($relative in @($plan.replace) + @($plan.remove)) { if ($protected -contains $relative -or $relative.StartsWith('data/') -or $relative.StartsWith('logs/')) { throw 'Protected path in plan.' }; $old = Resolve-Child $root $relative; if (Test-Path -LiteralPath $old) { $saved = Resolve-Child $backup $relative; New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($saved)) -Force | Out-Null; Copy-Item -LiteralPath $old -Destination $saved -Force }; $applied += $relative }
  foreach ($relative in $plan.replace) { $source = Resolve-Child $stage $relative; $target = Resolve-Child $root $relative; New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null; Copy-Item -LiteralPath $source -Destination $target -Force }
  foreach ($relative in $plan.remove) { Remove-Item -LiteralPath (Resolve-Child $root $relative) -Force -ErrorAction SilentlyContinue }
  Copy-Item -LiteralPath (Join-Path $stage $plan.manifestName) -Destination (Join-Path $root $plan.manifestName) -Force
  $exe = Resolve-Child $root $plan.entryExecutable; Start-Process -FilePath $exe -ArgumentList @('--pp02-update-token', $Token) -WindowStyle Hidden
  $deadline = (Get-Date).AddSeconds(90); do { Start-Sleep -Seconds 2; try { $health = Invoke-WebRequest -Uri $plan.health.backendUrl -UseBasicParsing -TimeoutSec 5; $home = Invoke-WebRequest -Uri $plan.health.homeUrl -UseBasicParsing -TimeoutSec 5; if ((Test-Path -LiteralPath $plan.readySignal) -and $health.StatusCode -eq 200 -and $home.StatusCode -eq 200) { $ready = Get-Content -LiteralPath $plan.readySignal -Raw | ConvertFrom-Json; if ($ready.token -ceq $Token -and $ready.productId -eq $plan.productId -and $ready.version -eq $plan.targetVersion) { exit 0 } } } catch {} } while ((Get-Date) -lt $deadline)
  throw 'New version health check failed.'
} catch {
  Get-Process -Name 'PP02 AI Daily Stock Analysis' -ErrorAction SilentlyContinue | Stop-Process -Force
  foreach ($relative in $applied) { $target = Resolve-Child $root $relative; $saved = Resolve-Child $backup $relative; if (Test-Path -LiteralPath $saved) { New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null; Copy-Item -LiteralPath $saved -Destination $target -Force } else { Remove-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue } }
  foreach ($runtime in @('.env','data/stock_analysis.db','data/stock_analysis.db-wal','data/stock_analysis.db-shm')) { $saved = Resolve-Child $backup $runtime; if (Test-Path -LiteralPath $saved) { Copy-Item -LiteralPath $saved -Destination (Resolve-Child $root $runtime) -Force } }
  Start-Process -FilePath (Resolve-Child $root $plan.entryExecutable) -WindowStyle Hidden; exit 1
}
