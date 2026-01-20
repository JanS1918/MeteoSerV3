Param(
    [string]$SourceDir = "${PWD}\data",
    [string]$BackupDir = "C:\ProgramData\MeteoSerV3\backups",
    [int]$KeepDays = 30
)

if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null }

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zipName = "meteoser-data-$timestamp.zip"
$zipPath = Join-Path $BackupDir $zipName

Write-Output "[INFO] Creating backup $zipPath from $SourceDir"

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($SourceDir, $zipPath)
    Write-Output "[OK] Backup creado: $zipPath"
} catch {
    Write-Error "[ERROR] Falló backup: $_"
    exit 1
}

# Cleanup old backups
Get-ChildItem -Path $BackupDir -Filter "*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$KeepDays) } | ForEach-Object {
    try { Remove-Item $_.FullName -Force; Write-Output "[CLEAN] Eliminado $_" } catch { Write-Warning "No pude eliminar $_" }
}

Write-Output "[DONE] Backup completo"

# Instrucciones para programar: ejecutar como tarea programada con cuenta que tenga permisos sobre `data` y `C:\ProgramData\MeteoSerV3`.
