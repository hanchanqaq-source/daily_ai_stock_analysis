$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw 'Windows installer verifier contract requires a Windows host.'
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$verifier = Join-Path $repoRoot 'scripts/verify-windows-installer.ps1'
if (-not (Test-Path -LiteralPath $verifier -PathType Leaf)) {
  throw 'Windows installer verifier script is missing.'
}

$fixtureRoot = Join-Path ([IO.Path]::GetTempPath()) (
  'pp02-installer-contract-' + [guid]::NewGuid().ToString('N')
)
$fakeInstaller = Join-Path $fixtureRoot 'fake-installer.exe'
$installRoot = Join-Path $fixtureRoot (
  'pp02-installer-verify-contract-' + [guid]::NewGuid().ToString('N')
)
$parentSentinel = Join-Path $fixtureRoot 'parent-sentinel.txt'
$previousRunnerTemp = [Environment]::GetEnvironmentVariable('RUNNER_TEMP', 'Process')

$fakeInstallerSource = @'
using System;
using System.IO;

public static class FakeInstaller {
  public static int Main(string[] args) {
    string installRoot = null;
    foreach (string arg in args) {
      if (arg.StartsWith("/D=", StringComparison.OrdinalIgnoreCase)) {
        installRoot = arg.Substring(3);
      }
    }
    if (String.IsNullOrWhiteSpace(installRoot)) return 91;
    Directory.CreateDirectory(installRoot);
    File.WriteAllText(Path.Combine(installRoot, "created-by-fake-installer.txt"), "owned");
    return 17;
  }
}
'@

try {
  New-Item -ItemType Directory -Path $fixtureRoot -Force | Out-Null
  Set-Content -LiteralPath $parentSentinel -Value 'preserve' -Encoding ASCII
  Add-Type -TypeDefinition $fakeInstallerSource -Language CSharp `
    -OutputAssembly $fakeInstaller -OutputType ConsoleApplication

  [Environment]::SetEnvironmentVariable('RUNNER_TEMP', $fixtureRoot, 'Process')
  $powerShell = (Get-Process -Id $PID).Path
  $stdoutPath = Join-Path $fixtureRoot 'verifier.stdout.log'
  $stderrPath = Join-Path $fixtureRoot 'verifier.stderr.log'
  $arguments = @(
    '-NoLogo'
    '-NoProfile'
    '-NonInteractive'
    '-ExecutionPolicy'
    'Bypass'
    '-File'
    ('"{0}"' -f $verifier)
    '-InstallerPath'
    ('"{0}"' -f $fakeInstaller)
    '-ExpectedVersion'
    '9.9.9'
    '-InstallRoot'
    ('"{0}"' -f $installRoot)
  )
  $contractProcess = Start-Process `
    -FilePath $powerShell `
    -ArgumentList $arguments `
    -Wait `
    -PassThru `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath
  $output = @()
  foreach ($streamPath in @($stdoutPath, $stderrPath)) {
    if (Test-Path -LiteralPath $streamPath -PathType Leaf) {
      $output += @(Get-Content -LiteralPath $streamPath | ForEach-Object {
        $_.ToString()
      })
    }
  }
  $verifierExitCode = $contractProcess.ExitCode

  if ($verifierExitCode -eq 0) {
    throw 'Verifier accepted a failing installer.'
  }
  if (-not ($output -contains 'WINDOWS_INSTALLER_VALIDATION=FAIL')) {
    throw 'Verifier did not emit its stable failure marker.'
  }
  if (Test-Path -LiteralPath $installRoot) {
    throw 'Verifier did not clean its owned install root.'
  }
  if (-not (Test-Path -LiteralPath $parentSentinel -PathType Leaf)) {
    throw 'Verifier removed a parent sentinel.'
  }
  Write-Output 'WINDOWS_INSTALLER_CONTRACT_VALIDATION=PASS'
}
finally {
  [Environment]::SetEnvironmentVariable(
    'RUNNER_TEMP',
    $previousRunnerTemp,
    'Process'
  )
  if (Test-Path -LiteralPath $fixtureRoot) {
    Remove-Item -LiteralPath $fixtureRoot -Recurse -Force -ErrorAction SilentlyContinue
  }
}
