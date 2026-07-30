param(
  [Parameter(Mandatory=$true)][string]$PackagedEntry,
  [int]$TimeoutSeconds = 90
)
$ErrorActionPreference = 'Stop'

function Get-FreeTcpPort {
  $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
  $listener.Start()
  try { return ([Net.IPEndPoint]$listener.LocalEndpoint).Port } finally { $listener.Stop() }
}

$entry = [IO.Path]::GetFullPath($PackagedEntry)
if (-not (Test-Path -LiteralPath $entry -PathType Leaf)) { throw "Frozen backend entrypoint not found: $entry" }
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ("pp02-frozen-smoke-" + [guid]::NewGuid().ToString('N'))
$dataDir = Join-Path $tempRoot 'data'; $logDir = Join-Path $tempRoot 'logs'; $envFile = Join-Path $tempRoot '.env'
New-Item -ItemType Directory -Path $dataDir,$logDir -Force | Out-Null
Set-Content -LiteralPath $envFile -Value "WEBUI_HOST=127.0.0.1`nWEBUI_ENABLED=false`nBOT_ENABLED=false`n" -Encoding UTF8
$port = Get-FreeTcpPort
$stdout = Join-Path $tempRoot 'stdout.log'; $stderr = Join-Path $tempRoot 'stderr.log'; $process = $null
$saved = @{}
foreach ($name in @('ENV_FILE','DATABASE_PATH','LOG_DIR','WEBUI_HOST','WEBUI_PORT','WEBUI_ENABLED','BOT_ENABLED','DSA_DESKTOP_MODE')) { $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
try {
  $env:ENV_FILE = $envFile; $env:DATABASE_PATH = Join-Path $dataDir 'stock_analysis.db'; $env:LOG_DIR = $logDir
  $env:WEBUI_HOST = '127.0.0.1'; $env:WEBUI_PORT = [string]$port; $env:WEBUI_ENABLED = 'false'; $env:BOT_ENABLED = 'false'; $env:DSA_DESKTOP_MODE = 'true'
  $process = Start-Process -FilePath $entry -ArgumentList @('--serve-only','--host','127.0.0.1','--port',[string]$port) -WorkingDirectory ([IO.Path]::GetDirectoryName($entry)) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds); $healthy = $false
  do {
    if ($process.HasExited) { throw "Frozen backend exited early with code $($process.ExitCode).`n$(Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue)" }
    try {
      $health = Invoke-WebRequest -Uri "http://127.0.0.1:$port/api/health" -UseBasicParsing -TimeoutSec 3
      $home = Invoke-WebRequest -Uri "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 3
      if ($health.StatusCode -eq 200 -and $home.StatusCode -eq 200) { $healthy = $true; break }
    } catch { Start-Sleep -Milliseconds 500 }
  } while ((Get-Date) -lt $deadline)
  if (-not $healthy) { throw "Frozen backend did not become healthy on dynamic port $port.`n$(Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue)" }
  Write-Host "Frozen backend smoke passed on dynamic port $port."
} finally {
  if ($process -and -not $process.HasExited) { & taskkill.exe /PID $process.Id /T /F | Out-Null; try { Wait-Process -Id $process.Id -Timeout 15 -ErrorAction SilentlyContinue } catch {} }
  if ($process -and -not $process.HasExited) { throw "Frozen backend process tree did not stop: PID $($process.Id)" }
  foreach ($name in $saved.Keys) { [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process') }
  Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
