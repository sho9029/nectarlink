# SPDX-License-Identifier: GPL-3.0-or-later
# Run on the owner's Windows PC with an authenticated GitHub CLI.
# No key or password is written into the repository or command arguments.
param(
    [string]$BackupZip = (Join-Path $PSScriptRoot 'NectarLink-ja-build-keys-private.zip'),
    [string]$Repository = 'sho9029/nectarlink'
)
$ErrorActionPreference = 'Stop'
if ($Repository -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$') {
    throw 'Invalid repository name.'
}
$gh = (Get-Command gh -ErrorAction Stop).Source
& $gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Run gh auth login, then run this script again.' }
& $gh api "repos/$Repository/actions/secrets/public-key" --silent
if ($LASTEXITCODE -ne 0) {
    throw 'This gh authentication cannot manage repository Secrets. Use your own GitHub account with repository admin access.'
}
$archive = (Resolve-Path -LiteralPath $BackupZip).Path
$working = Join-Path ([IO.Path]::GetTempPath()) ('nectarlink-secrets-' + [Guid]::NewGuid().ToString('N'))

function Set-RepositorySecret([string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Empty value for $Name" }
    $start = New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName = $gh
    $start.Arguments = "secret set $Name --repo $Repository"
    $start.UseShellExecute = $false
    $start.RedirectStandardInput = $true
    $process = [System.Diagnostics.Process]::Start($start)
    try {
        $process.StandardInput.Write($Value)
        $process.StandardInput.Close()
        $process.WaitForExit()
        if ($process.ExitCode -ne 0) { throw "Failed to register $Name" }
    } finally { $process.Dispose() }
    Write-Host "Registered $Name"
}

try {
    Expand-Archive -LiteralPath $archive -DestinationPath $working
    $keyPath = Join-Path $working 'android-signing.p12'
    $passwordPath = Join-Path $working 'android-keystore-password.txt'
    $identityPath = Join-Path $working 'artifact-key.txt'
    # Preserve compatibility with the APK already delivered to the owner.
    $expected = '894665a0b80e727c93cf61f90519faf9f9d77c1f3ef73f7769c4823cb0144710'
    if ((Get-FileHash -LiteralPath $keyPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
        throw 'The archive does not contain the signing key used for the delivered APK.'
    }
    $password = [IO.File]::ReadAllText($passwordPath).Trim()
    $identity = [IO.File]::ReadAllText($identityPath).Trim()
    if ($identity -notmatch 'AGE-SECRET-KEY-') { throw 'Artifact decryption key is missing.' }
    $keystore = [Convert]::ToBase64String([IO.File]::ReadAllBytes($keyPath))
    Set-RepositorySecret 'ANDROID_KEYSTORE' $keystore
    Set-RepositorySecret 'ANDROID_KEYSTORE_PASSWORD' $password
    # Recovery copy for the owner. Encryption in CI needs only the public key.
    Set-RepositorySecret 'ARTIFACT_AGE_IDENTITY' $identity
    & $gh secret list --repo $Repository
    if ($LASTEXITCODE -ne 0) { throw 'Secrets were written, but listing them failed.' }
    Write-Host 'Done. The repository can now sign Android builds with the existing key.'
} finally {
    $password = $null
    $identity = $null
    $keystore = $null
    if (Test-Path -LiteralPath $working) { Remove-Item -LiteralPath $working -Recurse -Force }
}
