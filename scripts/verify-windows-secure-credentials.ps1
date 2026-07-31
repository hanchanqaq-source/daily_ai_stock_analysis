$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$originalLocation = Get-Location
try {
    Set-Location -LiteralPath $repoRoot
    $currentHead = (& git rev-parse HEAD).Trim().ToLowerInvariant()
    $expectedHead = $env:DSA_EXPECTED_PR_HEAD_SHA
    if ([string]::IsNullOrWhiteSpace($expectedHead)) {
        $expectedHead = $currentHead
    }
    $expectedHead = $expectedHead.Trim().ToLowerInvariant()
    if ($currentHead -notmatch '^[0-9a-f]{40}$' -or $expectedHead -notmatch '^[0-9a-f]{40}$') {
        throw 'Windows secure credential validation requires an exact 40-character Head SHA.'
    }
    if ($currentHead -ne $expectedHead) {
        throw 'Checked out commit does not match the expected PR Head.'
    }

    $hashAlgorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $fakeBytes = [System.Text.Encoding]::UTF8.GetBytes("pp02-r37-fake:$currentHead")
        $fakeHash = $hashAlgorithm.ComputeHash($fakeBytes)
        $fakeSuffix = -join ($fakeHash | ForEach-Object { $_.ToString('x2') })
    }
    finally {
        $hashAlgorithm.Dispose()
    }
    $fakeCredential = "pp02-r37-$fakeSuffix"
    $previousFakeCredential = [Environment]::GetEnvironmentVariable('DSA_WINDOWS_TEST_FAKE_CREDENTIAL', 'Process')
    [Environment]::SetEnvironmentVariable('DSA_WINDOWS_TEST_FAKE_CREDENTIAL', $fakeCredential, 'Process')

    try {
        $commandOutput = @(& npm.cmd --prefix apps/dsa-desktop run test:windows-credentials 2>&1 | ForEach-Object { $_.ToString() })
        $commandExitCode = $LASTEXITCODE
    }
    finally {
        [Environment]::SetEnvironmentVariable('DSA_WINDOWS_TEST_FAKE_CREDENTIAL', $previousFakeCredential, 'Process')
    }
    $joinedOutput = $commandOutput -join "`n"
    if ($commandExitCode -ne 0) {
        throw 'Electron safeStorage fake credential harness failed.'
    }
    if ($joinedOutput.Contains($fakeCredential)) {
        throw 'Fake credential plaintext was emitted by the Windows validation harness.'
    }
    $passCount = ([regex]::Matches($joinedOutput, 'R3_7_WINDOWS_FAKE_CREDENTIAL_VALIDATION=PASS')).Count
    if ($passCount -ne 1) {
        throw 'Windows secure credential validation did not emit exactly one PASS marker.'
    }

    & node scripts/scan-windows-fake-credential.js --head $currentHead --path .
    if ($LASTEXITCODE -ne 0) {
        throw 'Source fake credential scan failed.'
    }

    Write-Output 'R3_7_WINDOWS_FAKE_CREDENTIAL_VALIDATION=PASS'
    Write-Output "R3_7_WINDOWS_FAKE_CREDENTIAL_HEAD=$currentHead"
}
finally {
    Set-Location -LiteralPath $originalLocation
}
