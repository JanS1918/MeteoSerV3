param(
    [switch]$WhatIfMode
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root\..\

Write-Host "Starting repo cleanup (safe)." -ForegroundColor Cyan

# Files to archive (safe move)
$toArchive = @(
    'arrancar_meteoser_autoreload.bat',
    'autoarranque_meteoser.bat',
    'autoarranque_meteoser.bat.disabled',
    'mantener_meteoser_activo.bat',
    'Reiniciar_MeteoSer.bat',
    'auto_inicio_meteoser.reg',
    'autoarranque_meteoser.bat'
)

$archiveDir = Join-Path -Path (Get-Location) -ChildPath 'archive\disabled_bats'
if (-not (Test-Path $archiveDir)) {
    if (-not $WhatIfMode) { New-Item -ItemType Directory -Path $archiveDir | Out-Null }
}

$moved = 0
foreach ($f in $toArchive) {
    $path = Join-Path (Get-Location) $f
    if (Test-Path $path) {
        $dest = Join-Path $archiveDir ($f + '.' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
        if ($WhatIfMode) { Write-Host "Would move: $path -> $dest" }
        else { Move-Item -Path $path -Destination $dest -Force; Write-Host "Moved: $f"; $moved++ }
    }
}

Write-Host "Moved $moved files to $archiveDir." -ForegroundColor Green

# Remove __pycache__ and .pyc outside .venv and archive
Write-Host "Removing __pycache__ and .pyc (excluding .venv and archive)..." -ForegroundColor Cyan
$excludes = @('.venv','archive')
$deleted = 0

Get-ChildItem -Path . -Recurse -Force -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq '__pycache__' } | ForEach-Object {
    $p = $_.FullName
    if ($excludes -notcontains ($p.Split('\') | Select-Object -Last 1)) {
        if ($WhatIfMode) { Write-Host "Would remove directory: $p" }
        else { Remove-Item -Recurse -Force -Path $p; Write-Host "Removed __pycache__: $p"; $deleted++ }
    }
}

Get-ChildItem -Path . -Recurse -Include '*.pyc' -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\.venv\\' -and $_.FullName -notmatch '\\archive\\' } | ForEach-Object {
    if ($WhatIfMode) { Write-Host "Would remove file: $($_.FullName)" }
    else { Remove-Item -Force -Path $_.FullName; $deleted++; Write-Host "Removed file: $($_.FullName)" }
}

Write-Host "Cleanup finished. Removed items: $deleted" -ForegroundColor Green

Write-Host "Done." -ForegroundColor Cyan
