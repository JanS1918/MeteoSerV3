# Script de ayuda: restaura archivos rastreados y limpia no rastreados
Param()
Push-Location $PSScriptRoot\..\
try {
    git restore .
    git clean -fd
    Write-Output "Repositorio restaurado a HEAD y limpio."
} catch {
    Write-Error "Error al restaurar: $($_.Exception.Message)"
}
Pop-Location
