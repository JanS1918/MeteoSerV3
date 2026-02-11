import logging

# Arranque robusto de MeteoSer FastAPI: libera el puerto 8080 automáticamente si está ocupado
# Ejecuta este script desde la raíz del proyecto


import socket
import os
import sys
import subprocess
import platform
from pathlib import Path



# Matar cualquier proceso que esté usando el puerto 8080 (Windows)
def matar_procesos_puerto_8080():
    if platform.system().lower().startswith('win'):
        try:
            output = subprocess.check_output('netstat -ano | findstr :8080', shell=True, encoding='utf-8')
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[4]
                    if pid.isdigit():
                        try:
                            subprocess.run(['taskkill', '/F', '/PID', pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception:
                            logging.exception("Silent except at 26 - revisar contexto")
        except subprocess.CalledProcessError as e:
            if e.output:
                logging.exception("Silent except at 28 - revisar contexto")
        except Exception:
            logging.exception("Silent except at 28 - revisar contexto")


def _is_pid_running(pid: int) -> bool:
    """Comprueba en Windows si el PID está activo usando tasklist."""
    if not isinstance(pid, int):
        return False
    if platform.system().lower().startswith('win'):
        try:
            out = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True, encoding='utf-8', stderr=subprocess.DEVNULL)
            return str(pid) in out
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            return False

matar_procesos_puerto_8080()
puerto_libre = 8080

# Asegura que el script se ejecuta desde la raíz
os.chdir(os.path.dirname(os.path.abspath(__file__)))



# Añadir la raíz del proyecto al PYTHONPATH para que los imports funcionen siempre
project_root = os.path.dirname(os.path.abspath(__file__))
env = os.environ.copy()
env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

# Comando uvicorn correcto
cmd = [
    sys.executable, '-m', 'uvicorn',
    'main_asgi:app',
    '--host', '0.0.0.0',
    '--port', str(puerto_libre)
]

print(f'Arrancando servidor MeteoSer FastAPI en http://0.0.0.0:{puerto_libre} ...')

# Preparar directorio de logs
logs_dir = Path(project_root) / 'logs'
logs_dir.mkdir(parents=True, exist_ok=True)
out_log = logs_dir / 'servicio_out.log'
err_log = logs_dir / 'servicio_err.log'
pid_file = logs_dir / 'service.pid'

# Abrir ficheros de log en modo append y lanzar uvicorn redirigiendo salida
stdout_f = open(out_log, 'a', encoding='utf-8')
stderr_f = open(err_log, 'a', encoding='utf-8')

# Comprobar si ya existe un PID registrado y si el proceso sigue activo
if pid_file.exists():
    try:
        existing = int(pid_file.read_text().strip())
    except Exception:
        existing = None
    if existing and _is_pid_running(existing):
        print(f'Proceso ya en ejecución (PID={existing}), saliendo.')
        sys.exit(0)
    else:
        try:
            pid_file.unlink()
        except Exception:
            pass

proc = subprocess.Popen(cmd, stdout=stdout_f, stderr=stderr_f, env=env, cwd=project_root)

# Guardar PID para referencia / gestión externa
try:
    with open(pid_file, 'w') as f:
        f.write(str(proc.pid))
    print(f'PID guardado en: {pid_file} (PID={proc.pid})')
except Exception as e:
    print(f'No se pudo escribir PID: {e}')

# No bloqueamos: el proceso queda en background y las salidas se escriben en logs
