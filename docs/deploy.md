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

Variables de entorno para alertas y monitorización

Para que `tools/monitor_health.ps1` envíe alertas por correo (preferente) o por Telegram (fallback), define las siguientes variables de entorno en el host (Task Scheduler / System Environment):

- Email (Outlook / Office365):
	- `OUTLOOK_SMTP_SERVER` (por defecto: `smtp.office365.com`)
	- `OUTLOOK_SMTP_PORT` (por defecto: `587`)
	- `OUTLOOK_USERNAME` (tu cuenta de correo completa)
	- `OUTLOOK_PASSWORD` (usa contraseña de aplicación cuando sea posible)
	- `ALERT_EMAIL_TO` (dirección o lista separada por comas donde enviar alertas)

- Telegram (opcional, fallback):
	- `TELEGRAM_BOT_TOKEN`
	- `TELEGRAM_CHAT_ID`

Cómo probar `tools/monitor_health.ps1` localmente (PowerShell):

```powershell
# En la sesión de PowerShell (no persistente)
$Env:OUTLOOK_SMTP_SERVER = 'smtp.office365.com'
$Env:OUTLOOK_SMTP_PORT = '587'
$Env:OUTLOOK_USERNAME = 'tucorreo@dominio.com'
$Env:OUTLOOK_PASSWORD = 'TuPasswordApp'
$Env:ALERT_EMAIL_TO = 'mi@email.com'

# Ejecutar el monitor (ajusta BaseUrl si tu API corre en otra parte)
.\tools\monitor_health.ps1 -BaseUrl 'http://127.0.0.1:8080' -LinesToCheck 40
```

Si no quieres usar email, solo exporta `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` y el script usará Telegram.

Consejo de seguridad: guarda `OUTLOOK_PASSWORD` como secreto del sistema (no en texto plano). En servidores Windows, configura la variable de entorno del sistema o usa el Task Scheduler para pasar credenciales de forma segura.
