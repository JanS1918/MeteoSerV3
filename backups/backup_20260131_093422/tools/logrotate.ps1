param(
    [int]$MaxBytes = 5242880
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root\..\

$logsDir = Join-Path (Get-Location) 'logs'
if (-not (Test-Path $logsDir)) {
    Write-Host "No logs directory found at $logsDir" -ForegroundColor Yellow
    exit 0
}

$archiveDir = Join-Path (Get-Location) 'archive\logs'
if (-not (Test-Path $archiveDir)) { New-Item -ItemType Directory -Path $archiveDir | Out-Null }

Get-ChildItem -Path $logsDir -Filter '*.log' -File | ForEach-Object {
    $f = $_.FullName
    if ($_.Length -ge $MaxBytes) {
        $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
        $dest = Join-Path $archiveDir ($_.Name + '.' + $ts)
        Move-Item -Path $f -Destination $dest -Force
        New-Item -ItemType File -Path $f | Out-Null
        Write-Host "Rotated $($_.Name) -> $dest"
    }
}

Write-Host "Log rotation complete." -ForegroundColor Green
