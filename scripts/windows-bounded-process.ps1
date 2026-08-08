function Invoke-PP02BoundedProcess {
  param(
    [Parameter(Mandatory=$true)][string]$FilePath,
    [string[]]$ArgumentList = @(),
    [string]$WorkingDirectory = '',
    [Parameter(Mandatory=$true)][int]$TimeoutSeconds,
    [Parameter(Mandatory=$true)][string]$Stage,
    [Parameter(Mandatory=$true)][string]$StageReportPath
  )

  if ($TimeoutSeconds -lt 1 -or $TimeoutSeconds -gt 1800) {
    throw 'TimeoutSeconds must be between 1 and 1800.'
  }
  if ($Stage -notmatch '^[a-z0-9_]{1,64}$') {
    throw 'Stage must be a bounded lowercase identifier.'
  }
  $resolvedFile = [IO.Path]::GetFullPath($FilePath)
  if (-not (Test-Path -LiteralPath $resolvedFile -PathType Leaf)) {
    throw "$Stage process executable is missing."
  }

  $startParameters = @{
    FilePath = $resolvedFile
    ArgumentList = $ArgumentList
    PassThru = $true
  }
  if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
    $startParameters.WorkingDirectory = [IO.Path]::GetFullPath($WorkingDirectory)
  }

  $process = Start-Process @startParameters
  $completed = $process.WaitForExit($TimeoutSeconds * 1000)
  if (-not $completed) {
    Add-Content `
      -LiteralPath $StageReportPath `
      -Value "timestamp_utc=$((Get-Date).ToUniversalTime().ToString('o')) stage=$Stage status=TIMEOUT timeout_seconds=$TimeoutSeconds" `
      -Encoding UTF8
    & taskkill.exe /PID $process.Id /T /F | Out-Null
    $null = $process.WaitForExit(20000)
    $process.Refresh()
    if (-not $process.HasExited) {
      throw "$Stage process exceeded its bounded timeout and could not be terminated."
    }
    throw "$Stage process exceeded its bounded timeout of $TimeoutSeconds seconds."
  }

  $process.Refresh()
  Add-Content `
    -LiteralPath $StageReportPath `
    -Value "timestamp_utc=$((Get-Date).ToUniversalTime().ToString('o')) stage=$Stage status=EXIT exit_code=$($process.ExitCode)" `
    -Encoding UTF8
  return $process
}
