# Despliegue y restauración — MeteoSerV3

Resumen rápido:

- Requisitos: Python 3.10+, `uvicorn`, `gunicorn`/`nssm` para windows service, variables de entorno con claves en `meteoser_configuracion.txt` o secretos de GitHub Actions.
- Entrypoint ASGI: `main_asgi:app` (run con `uvicorn main_asgi:app --host 0.0.0.0 --port 8000`).

Pasos mínimos de despliegue:

1. Crear entorno virtual y deps:

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Ejecutar localmente (dev):

```
uvicorn main_asgi:app --reload --host 0.0.0.0 --port 8000
```

3. Producción en Windows (opciones):
- Usar NSSM para registrar `uvicorn`/`python` como servicio. Ver `docs/NSSM.md`.
- Alternativa: crear un servicio con `nssm` o usar un wrapper que reinicie en crash.

Branch protection y CI:

- Antes de proteger `main` como rama requerida, verificar que el workflow de GitHub Actions pase en la rama `main`.
- Recomendación de reglas: Require status checks (CI), Require PR reviews (1), Dismiss stale reviews, Require linear history.

Habilitar Dependabot:

- Ya existe `.github/dependabot.yml` para actualizaciones semanales de `pip`.
- Dependabot puede abrir PRs automáticas; revisa y mergea con CI verde.

Backups y restauración:

- Los datos se guardan en `data/`. Se recomienda programar una copia periódica (zip) a un directorio seguro, p.ej. `C:\ProgramData\MeteoSerV3\backups`.
- Para restaurar, descomprimir el backup y reiniciar el servicio.

Notas de seguridad:

- No almacenes claves en el repo. Usa GitHub Secrets para CI o `meteoser_configuracion.txt` con permisos restringidos en el host.
