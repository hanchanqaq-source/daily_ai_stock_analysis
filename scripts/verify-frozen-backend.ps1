param(
  [Parameter(Mandatory=$true)][string]$PackagedEntry,
  [int]$TimeoutSeconds = 90
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Net.Http

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
$chipProbeStdout = Join-Path $tempRoot 'chip-probe-stdout.log'; $chipProbeStderr = Join-Path $tempRoot 'chip-probe-stderr.log'
$httpHandler = [Net.Http.HttpClientHandler]::new(); $httpHandler.UseProxy = $false
$httpClient = [Net.Http.HttpClient]::new($httpHandler); $httpClient.Timeout = [TimeSpan]::FromSeconds(3)
$saved = @{}
foreach ($name in @('GITHUB_ACTIONS','PYTHONUTF8','PYTHONIOENCODING','PYTHONSAFEPATH','ENV_FILE','DATABASE_PATH','LOG_DIR','WEBUI_HOST','WEBUI_PORT','WEBUI_ENABLED','BOT_ENABLED','DSA_DESKTOP_MODE','DSA_PACKAGED_CHIP_PROBE')) { $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
try {
  $env:GITHUB_ACTIONS = 'false'; $env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONSAFEPATH = '1'
  $env:ENV_FILE = $envFile; $env:DATABASE_PATH = Join-Path $dataDir 'stock_analysis.db'; $env:LOG_DIR = $logDir
  $env:WEBUI_HOST = '127.0.0.1'; $env:WEBUI_PORT = [string]$port; $env:WEBUI_ENABLED = 'false'; $env:BOT_ENABLED = 'false'; $env:DSA_DESKTOP_MODE = 'true'
  $env:DSA_PACKAGED_CHIP_PROBE = '1'
  $chipProbeProcess = Start-Process -FilePath $entry -WorkingDirectory $tempRoot -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $chipProbeStdout -RedirectStandardError $chipProbeStderr
  if ($chipProbeProcess.ExitCode -ne 0) {
    throw "Packaged chip runtime probe failed with code $($chipProbeProcess.ExitCode).`n$(Get-Content -LiteralPath $chipProbeStderr -Raw -ErrorAction SilentlyContinue)"
  }
  Write-Host ((Get-Content -LiteralPath $chipProbeStdout -Raw).Trim())
  Remove-Item Env:DSA_PACKAGED_CHIP_PROBE -ErrorAction SilentlyContinue
  $process = Start-Process -FilePath $entry -ArgumentList @('--serve-only','--host','127.0.0.1','--port',[string]$port) -WorkingDirectory $tempRoot -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds); $healthy = $false
  $healthDiagnostic = 'not attempted'; $homeDiagnostic = 'not attempted'
  do {
    if ($process.HasExited) { throw "Frozen backend exited early with code $($process.ExitCode).`n$(Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue)" }
    try {
      $health = $httpClient.GetAsync("http://127.0.0.1:$port/api/health").GetAwaiter().GetResult()
      $healthDiagnostic = "HTTP $([int]$health.StatusCode)"
    } catch { $health = $null; $healthDiagnostic = "$($_.Exception.GetType().Name): $($_.Exception.Message)" }
    try {
      $homeResponse = $httpClient.GetAsync("http://127.0.0.1:$port/").GetAwaiter().GetResult()
      $homeDiagnostic = "HTTP $([int]$homeResponse.StatusCode)"
    } catch { $homeResponse = $null; $homeDiagnostic = "$($_.Exception.GetType().Name): $($_.Exception.Message)" }
    if ($health -and $homeResponse -and [int]$health.StatusCode -eq 200 -and [int]$homeResponse.StatusCode -eq 200) { $healthy = $true; break }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $deadline)
  if (-not $healthy) { throw "Frozen backend HTTP probes failed on dynamic port ${port}: health=$healthDiagnostic; home=$homeDiagnostic.`n$(Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue)" }
  Write-Host "Frozen backend smoke passed on dynamic port $port."
} finally {
  if ($process -and -not $process.HasExited) { & taskkill.exe /PID $process.Id /T /F | Out-Null; try { Wait-Process -Id $process.Id -Timeout 15 -ErrorAction SilentlyContinue } catch {} }
  if ($process -and -not $process.HasExited) { throw "Frozen backend process tree did not stop: PID $($process.Id)" }
  foreach ($name in $saved.Keys) { [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process') }
  $httpClient.Dispose(); $httpHandler.Dispose()
  Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
