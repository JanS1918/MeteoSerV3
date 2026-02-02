$NSSM = 'C:\Users\kioko\Desktop\MeteoSerV3\tools\nssm\nssm-2.24\win64\nssm.exe'
Write-Output '=== fix_mosquitto.ps1 started ==='
Write-Output "NSSM path: $NSSM"

Write-Output '--- Deteniendo procesos mosquitto (si existen) ---'
$procs = Get-Process -Name mosquitto -ErrorAction SilentlyContinue
if ($procs) {
    foreach ($p in $procs) {
        try { Stop-Process -Id $p.Id -Force -ErrorAction Stop; Write-Output "Stopped mosquitto PID $($p.Id)" } catch { Write-Output "No se pudo detener PID $($p.Id): $_" }
    }
} else { Write-Output 'No se encontraron procesos mosquitto en ejecución.' }

Start-Sleep -Milliseconds 800

Write-Output '--- Intentando detener servicio via NSSM ---'
try { & $NSSM stop MeteoSerMosquitto 2>&1 | Write-Output } catch { Write-Output "NSSM stop error: $_" }
Start-Sleep -Milliseconds 800

Write-Output '--- Intentando iniciar/continuar servicio via NSSM ---'
try { & $NSSM start MeteoSerMosquitto 2>&1 | Write-Output } catch { Write-Output "NSSM start error: $_" }
Start-Sleep -Seconds 1

Write-Output '--- Estado del servicio ---'
try { Get-Service -Name MeteoSerMosquitto | Format-List | Write-Output } catch { Write-Output 'Service MeteoSerMosquitto no encontrado.' }

Write-Output '--- Asegurando permisos en C:\mosquitto\log ---'
try { & 'C:\Windows\System32\icacls.exe' 'C:\mosquitto\log' /grant 'NT AUTHORITY\SYSTEM:(OI)(CI)F' /grant 'BUILTIN\Administradores:(OI)(CI)F' /grant 'BUILTIN\Usuarios:(OI)(CI)M' /T 2>&1 | Write-Output } catch { Write-Output "icacls error: $_" }

Write-Output '--- Leyendo últimos logs (stdout/stderr/mosquitto.log) ---'
try { Get-Content -Path 'C:\mosquitto\log\mosquitto_stdout.log' -Tail 200 -ErrorAction Stop | Write-Output } catch { Write-Output "Get-Content stdout error: $_" }
try { Get-Content -Path 'C:\mosquitto\log\mosquitto_stderr.log' -Tail 200 -ErrorAction Stop | Write-Output } catch { Write-Output "Get-Content stderr error: $_" }
try { Get-Content -Path 'C:\mosquitto\log\mosquitto.log' -Tail 200 -ErrorAction Stop | Write-Output } catch { Write-Output "Get-Content mosquitto.log error: $_" }

Write-Output '--- Comprobando conexiones TCP en 1883 ---'
try { Get-NetTCPConnection -LocalPort 1883 -ErrorAction Stop | Format-Table | Write-Output } catch { Write-Output "Get-NetTCPConnection error: $_" }

Write-Output '--- Test-NetConnection localhost:1883 ---'
Test-NetConnection -ComputerName localhost -Port 1883 | Format-List | Write-Output

Write-Output '=== fix_mosquitto.ps1 finished ==='