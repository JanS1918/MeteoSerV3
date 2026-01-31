# NSSM (Non-Sucking Service Manager) — configuración recomendada

Breve guía para ejecutar MeteoSer como servicio en Windows usando `nssm`.

1. Descargar e instalar NSSM
   - Descarga la versión apropiada desde https://nssm.cc/download
   - Extrae `nssm.exe` en `C:\Windows\System32` o una carpeta en `PATH`.

2. Instalar el servicio (ejecutar en PowerShell como Administrador)
   - Ejemplo usando `uvicorn` como ejecutable del servicio (ajusta la ruta/args según tu despliegue):

```powershell
nssm install MeteoSer "C:\Users\kioko\Desktop\MeteoSerV3\.venv\Scripts\uvicorn.exe" "main_asgi:app --host 0.0.0.0 --port 8080 --proxy-headers --loop asyncio"
```

3. Configurar stdout/stderr y working directory
   - Usa `nssm set MeteoSer AppDirectory C:\Users\kioko\Desktop\MeteoSerV3`
   - Usa `nssm set MeteoSer AppStdout C:\ProgramData\MeteoSerV3\logs\service_stdout.log` y `AppStderr` para errores.
   - Habilita `AppRotateFiles` o usa nuestra tarea `MeteoSer LogRotate` para rotación periódica.

4. Politica de reinicio y permisos
   - Configura `Exit actions` para reiniciar en fallo: `nssm set MeteoSer AppRestartDelay 5000` (ms).
   - Ejecutar el servicio con una cuenta de servicio con permisos mínimos o `LocalSystem` si necesita abrir puertos.

5. Comprobaciones y control
   - Iniciar/Parar: `nssm start MeteoSer`, `nssm stop MeteoSer`.
   - Logs: revisa `C:\ProgramData\MeteoSerV3\logs\service_stdout.log` y `service_stderr.log`.

6. Notas
   - Si usas virtualenv, apunta `nssm` al ejecutable `python.exe`/`uvicorn.exe` dentro de `.venv\Scripts`.
   - Documenta en el administrador del sistema sobre excepciones en antivirus/defensa para evitar bloqueos de lectura de logs.
