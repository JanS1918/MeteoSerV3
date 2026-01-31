# MeteoSerV3

Proyecto MeteoSer: servidor ligero para ingestión y procesamiento de datos de sensores meteorológicos.

Resumen rápido
- Entrypoint ASGI: `main_asgi:app` (uvicorn).
- Scripts de mantenimiento en `tools/`: `monitor_health.ps1`, `logrotate.ps1`.
- Logs en `C:\ProgramData\MeteoSerV3\logs` (recomendado para servicio SYSTEM).

Cómo ejecutar localmente
1. Crear y activar el entorno virtual:
```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2. Ejecutar con uvicorn (desde la raíz del proyecto):
```powershell
.venv\Scripts\uvicorn.exe main_asgi:app --host 0.0.0.0 --port 8080
```

Automatización / despliegue
- Monitor de salud (`tools/monitor_health.ps1`) y rotador de logs (`tools/logrotate.ps1`) se crearon y hay tareas programadas en Windows Task Scheduler por defecto en `ProgramData`.
- Para ejecutar como servicio en producción se recomienda usar `nssm` (ver `docs/NSSM.md`).

Tests
- Ejecutar tests con `pytest -q`.

Contribuir
- Abrir issues o pull requests. Añadir `.gitattributes` y `CI` para mantener line endings y pruebas automáticas.
