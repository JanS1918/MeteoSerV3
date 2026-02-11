param(
    [switch]$WhatIf
)

<#
  cleanup_workspace.ps1
  - Escanea el repositorio y elimina artefactos comunes que causan incoherencias
  - Por defecto muestra una previsualización. Para ejecutar realmente, pasar -WhatIf:$false -Confirm (se requiere escribir YES)
#>

Set-StrictMode -Version Latest
# Determinar la raíz del repositorio (carpeta padre de 'tools')
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$root = Split-Path -Parent $scriptDir
Write-Host "Workspace cleanup script running in: $root"

# Patrones seguros para eliminar (artefactos y caches)
$filePatterns = @('**\\*.pyc','**\\*.pyo','**\\*.pyd','**\\*.log','**\\*.zip','**\\*.bak')
$dirNames = @('__pycache__','logs','.backup','backups')

# Rutas a EXCLUIR (relativas a la raíz) para evitar borrar datos o binarios necesarios
# Añade aquí carpetas que no quieres tocar: ejemplo 'data', 'tools\\nssm', 'tools\\backups'
$excludePaths = @('data','.venv','venv','tools\\nssm','tools\\backups','archive','backups')

$candidates = @()
foreach ($pat in $filePatterns) {
    $items = Get-ChildItem -Path $root -Recurse -Force -ErrorAction SilentlyContinue -Include $pat | Where-Object { -not ($_.FullName -match "\\.git\\") }
    foreach ($it in $items) { $candidates += $it }
}
foreach ($d in $dirNames) {
    $items = Get-ChildItem -Path $root -Recurse -Force -ErrorAction SilentlyContinue -Directory -Filter $d | Where-Object { -not ($_.FullName -match "\\.git\\") }
    foreach ($it in $items) { $candidates += $it }
}

# Filtrar candidatos que estén dentro de rutas excluidas
$candidates = $candidates | Where-Object {
    $full = $_.FullName.ToLower()
    $keep = $true
    foreach ($ex in $excludePaths) {
        $exFull = (Join-Path $root $ex).ToLower()
        if ($full.StartsWith($exFull)) { $keep = $false; break }
    }
    return $keep
}

$candidates = $candidates | Sort-Object FullName -Unique

if (-not $candidates) {
    Write-Host "No artefactos detectados para eliminar."
    exit 0
}

Write-Host "Se han detectado los siguientes items candidatos a eliminación:" -ForegroundColor Yellow
foreach ($it in $candidates) {
    Write-Host " - $($it.FullName)"
}

if ($WhatIf) {
    Write-Host "Modo PREVISUALIZACIÓN: ningún fichero será borrado. Para ejecutar, vuelve a lanzar sin -WhatIf y confirma." -ForegroundColor Cyan
    exit 0
}

Write-Host "Si estás de acuerdo con la eliminación, escribe YES y pulsa Enter. Cualquier otra entrada cancela." -ForegroundColor Red
$confirm = Read-Host "CONFIRMAR (YES to proceed)"
if ($confirm -ne 'YES') {
    Write-Host "Operación cancelada por el usuario." -ForegroundColor Yellow
    exit 0
}

Write-Host "Eliminando items..." -ForegroundColor Green
foreach ($it in $candidates) {
    try {
        if ($it.PSIsContainer) {
            Remove-Item -LiteralPath $it.FullName -Recurse -Force -ErrorAction Stop
            Write-Host "Dir removed: $($it.FullName)"
        } else {
            Remove-Item -LiteralPath $it.FullName -Force -ErrorAction Stop
            Write-Host "File removed: $($it.FullName)"
        }
    } catch {
        Write-Host "Failed to remove $($it.FullName): $_" -ForegroundColor Red
    }
}

Write-Host "Limpieza completada." -ForegroundColor Green
