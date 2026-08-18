$ErrorActionPreference = 'Stop'
$extensionRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$distPath = Join-Path $extensionRoot 'dist'
$releasePath = Join-Path $extensionRoot 'release'
$manifest = Get-Content -Raw -LiteralPath (Join-Path $distPath 'manifest.json') | ConvertFrom-Json
$archivePath = Join-Path $releasePath ("legacy-devbridge-private-v{0}.zip" -f $manifest.version)

if (-not (Test-Path -LiteralPath (Join-Path $distPath 'background.js'))) {
    throw 'Extension build is incomplete. Run npm run build first.'
}

New-Item -ItemType Directory -Path $releasePath -Force | Out-Null
if (Test-Path -LiteralPath $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}
Compress-Archive -Path (Join-Path $distPath '*') -DestinationPath $archivePath -CompressionLevel Optimal
Write-Output $archivePath
