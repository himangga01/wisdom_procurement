param([switch]$Force)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$installRoot = Join-Path $projectRoot 'backend\tools\rhwp'
$executable = Join-Path $installRoot 'rhwp.exe'
$expectedHash = '867e0a84b778ebda92b88433ede301818eaea21e7d58eb77ff9a732f41d170d9'

if (-not $Force -and (Test-Path -LiteralPath $executable)) {
    $installedVersion = & $executable --version
    if ($LASTEXITCODE -eq 0 -and $installedVersion -eq 'rhwp v0.8.6') {
        Write-Output 'RHWP 0.8.6 is already installed.'
        exit 0
    }
}

$temporaryBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$downloadRoot = Join-Path $temporaryBase ('wisdom-rhwp-setup-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $downloadRoot | Out-Null
try {
    $archive = Join-Path $downloadRoot 'rhwp.zip'
    Invoke-WebRequest -Uri 'https://github.com/edwardkim/rhwp/releases/download/v0.8.6/rhwp-v0.8.6-windows-x86_64.zip' -OutFile $archive
    $actualHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) { throw 'RHWP archive checksum verification failed.' }
    $extracted = Join-Path $downloadRoot 'extracted'
    Expand-Archive -LiteralPath $archive -DestinationPath $extracted
    $candidates = @(Get-ChildItem -LiteralPath $extracted -Recurse -File -Filter 'rhwp.exe')
    if ($candidates.Count -ne 1) { throw 'The release must contain exactly one rhwp.exe.' }
    New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
    Copy-Item -LiteralPath $candidates[0].FullName -Destination $executable -Force
    $installedVersion = & $executable --version
    if ($LASTEXITCODE -ne 0 -or $installedVersion -ne 'rhwp v0.8.6') { throw 'RHWP executable version verification failed.' }
    Write-Output "Installed $installedVersion; archive SHA-256 verified."
} finally {
    $resolvedDownload = [IO.Path]::GetFullPath($downloadRoot)
    $basePrefix = $temporaryBase.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if (-not $resolvedDownload.StartsWith($basePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing cleanup outside the temporary directory.'
    }
    Remove-Item -LiteralPath $resolvedDownload -Recurse -Force
}
