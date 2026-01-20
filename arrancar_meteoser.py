
# Arranque robusto de MeteoSer FastAPI: libera el puerto 8080 automáticamente si está ocupado
# Ejecuta este script desde la raíz del proyecto


import socket
import os
import sys
import subprocess
import platform



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
                            pass
        except Exception:
            pass

matar_procesos_puerto_8080()
puerto_libre = 8080

# Asegura que el script se ejecuta desde la raíz
os.chdir(os.path.dirname(os.path.abspath(__file__)))



# Añadir la raíz del proyecto al PYTHONPATH para que los imports funcionen siempre
project_root = os.path.dirname(os.path.abspath(__file__))
env = os.environ.copy()
env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

# Comando uvicorn correcto para la interfaz real
cmd = [
    sys.executable, '-m', 'uvicorn',
    'main_asgi:app',
    '--host', '0.0.0.0',
    '--port', str(puerto_libre)
]

print(f'Arrancando servidor MeteoSer FastAPI en http://0.0.0.0:{puerto_libre} ...')
proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, env=env)
proc.wait()
