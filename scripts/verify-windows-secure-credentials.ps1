$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$originalLocation = Get-Location
try {
    Set-Location -LiteralPath $repoRoot
    $head = $env:GITHUB_SHA
    if ([string]::IsNullOrWhiteSpace($head)) {
        $head = (& git rev-parse HEAD).Trim()
    }
    if ($head -notmatch '^[0-9a-fA-F]{40}$') {
        throw 'Windows secure credential validation requires an exact 40-character Head SHA.'
    }

    $commandOutput = @(& npm.cmd --prefix apps/dsa-desktop run test:windows-credentials 2>&1 | ForEach-Object { $_.ToString() })
    $commandExitCode = $LASTEXITCODE
    $joinedOutput = $commandOutput -join "`n"
    if ($commandExitCode -ne 0) {
        throw 'Electron safeStorage fake credential harness failed.'
    }
    if ($joinedOutput -match 'pp02-r37-[0-9a-fA-F]{64}') {
        throw 'Fake credential plaintext was emitted by the Windows validation harness.'
    }
    $passCount = ([regex]::Matches($joinedOutput, 'R3_7_WINDOWS_FAKE_CREDENTIAL_VALIDATION=PASS')).Count
    if ($passCount -ne 1) {
        throw 'Windows secure credential validation did not emit exactly one PASS marker.'
    }

    Write-Output 'R3_7_WINDOWS_FAKE_CREDENTIAL_VALIDATION=PASS'
    Write-Output "R3_7_WINDOWS_FAKE_CREDENTIAL_HEAD=$head"
}
finally {
    Set-Location -LiteralPath $originalLocation
}
