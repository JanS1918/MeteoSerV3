# Monitor de procesos sospechosos de PowerShell
# Este script captura información de procesos de PowerShell que se ejecuten

Write-Host "🔍 Monitoreando procesos de PowerShell..." -ForegroundColor Cyan
Write-Host "Presiona Ctrl+C para detener el monitoreo" -ForegroundColor Yellow
Write-Host ""

$procesosPrevios = @()

while ($true) {
    $procesosActuales = Get-WmiObject Win32_Process -Filter "name='powershell.exe' OR name='pwsh.exe' OR name='cmd.exe' OR name='python.exe' OR name='pythonw.exe'" | 
        Select-Object ProcessId, Name, CommandLine, ParentProcessId, CreationDate
    
    foreach ($proceso in $procesosActuales) {
        if ($proceso.ProcessId -notin $procesosPrevios.ProcessId) {
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Write-Host "[$timestamp] 🆕 NUEVO PROCESO DETECTADO:" -ForegroundColor Red
            Write-Host "  PID: $($proceso.ProcessId)" -ForegroundColor Yellow
            Write-Host "  Nombre: $($proceso.Name)" -ForegroundColor Yellow
            Write-Host "  Comando: $($proceso.CommandLine)" -ForegroundColor Cyan
            Write-Host "  Padre PID: $($proceso.ParentProcessId)" -ForegroundColor Yellow
            Write-Host "  Creado: $($proceso.CreationDate)" -ForegroundColor Yellow
            
            # Obtener info del proceso padre
            $padre = Get-WmiObject Win32_Process -Filter "ProcessId=$($proceso.ParentProcessId)" -ErrorAction SilentlyContinue
            if ($padre) {
                Write-Host "  Proceso Padre: $($padre.Name) - $($padre.CommandLine)" -ForegroundColor Magenta
            }
            Write-Host ""
            
            # Guardar en log
            Add-Content -Path ".\proceso_monitor.log" -Value "[$timestamp] PID=$($proceso.ProcessId) | $($proceso.Name) | CMD=$($proceso.CommandLine) | ParentPID=$($proceso.ParentProcessId)"
        }
    }
    
    $procesosPrevios = $procesosActuales
    Start-Sleep -Milliseconds 500
}
