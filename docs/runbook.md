# Runbook operativo — MeteoSerV3

## Objetivo
Mantener el servicio estable, recuperable y con cambios controlados.

## Servicios
- MeteoSer backend: `MeteoSerBackend`
- Mosquitto (MQTT): `MeteoSerMosquitto`

## Comprobaciones rápidas
**Estado de servicios**
```powershell
Get-Service -Name MeteoSerBackend, MeteoSerMosquitto | Format-Table Name,Status,StartType
```

**Puerto del backend**
```powershell
Get-NetTCPConnection -LocalPort 8080 -State Listen
```

**Últimos logs del backend**
```powershell
Get-Content .\logs\servicio_err.log -Tail 50
Get-Content .\logs\servicio_out.log -Tail 50
```

## Reinicio controlado (backend)
```powershell
C:\Windows\System32\sc.exe stop MeteoSerBackend
Start-Sleep -Seconds 2
C:\Windows\System32\sc.exe start MeteoSerBackend
```

Si el servicio está en estado `PAUSED`, limpiar procesos duplicados y relanzar:
```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'main_asgi|uvicorn|arrancar_meteoser.py') } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Remove-Item .\logs\start.lock -ErrorAction SilentlyContinue -Force
Remove-Item .\logs\service.pid -ErrorAction SilentlyContinue -Force
C:\Windows\System32\sc.exe start MeteoSerBackend
```

## Reinicio controlado (MQTT)
```powershell
.\tools\nssm\nssm-2.24\win64\nssm.exe restart MeteoSerMosquitto
```

## Regenerar credenciales MQTT (seguro)
```powershell
.\scripts\auto_fix_mosquitto_password.ps1
```

## Forzar configuración TLS de Mosquitto
```powershell
.\scripts\fix_mosquitto_tls.ps1
.\tools\nssm\nssm-2.24\win64\nssm.exe restart MeteoSerMosquitto
```

## Backup manual
```powershell
.\tools\backup_data.ps1
```

## Rollback rápido
1. Detener `MeteoSerBackend`.
2. Restaurar `data/` desde `backups/<timestamp>/data`.
3. Iniciar `MeteoSerBackend`.

## Checklist post-incidente
- [ ] Logs sin errores críticos (5xx, MQTT TLS/Auth)
- [ ] `/estado` responde
- [ ] Sensores clave con datos (`temperatura`, `humedad`, `viento`, `lluvia`)
- [ ] Mosquitto en `Running`
