<#
  clear_ps_history.ps1
  - Borra el fichero de historial de PSReadLine para limpiar el historial persistente de PowerShell
  - No toca historial en la nube u otros servicios externos. Ejecutar con permisos de usuario actual.
#>
Set-StrictMode -Version Latest
$hist = Join-Path $env:APPDATA "Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"
if (Test-Path $hist) {
    try {
        Remove-Item -LiteralPath $hist -Force -ErrorAction Stop
        Write-Host "Historial de PowerShell eliminado: $hist" -ForegroundColor Green
    } catch {
        Write-Host "No se pudo eliminar el historial: $_" -ForegroundColor Red
    }
} else {
    Write-Host "No se encontró fichero de historial en: $hist" -ForegroundColor Yellow
}
