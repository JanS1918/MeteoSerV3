
# Arranque robusto de MeteoSer FastAPI: libera el puerto 8080 automáticamente si está ocupado
# Ejecuta este script desde la raíz del proyecto


import socket
import os
import sys
import subprocess
import platform
import time
import secrets
from pathlib import Path



def _get_commandline_windows(pid: int) -> str:
    if not pid or not str(pid).isdigit():
        return ''
    try:
        out = subprocess.check_output(
            ['wmic', 'process', 'where', f'ProcessId={pid}', 'get', 'CommandLine'],
            encoding='utf-8', errors='ignore'
        )
        lines = [l.strip() for l in out.splitlines() if l.strip() and 'CommandLine' not in l]
        return lines[0] if lines else ''
    except Exception:
        pass
    try:
        system_root = os.environ.get('SystemRoot', r'C:\Windows')
        ps_path = os.path.join(system_root, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
        if os.path.exists(ps_path):
            out = subprocess.check_output(
                [ps_path, '-NoProfile', '-Command', f"(Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\").CommandLine"],
                encoding='utf-8', errors='ignore'
            )
            cmd = out.strip()
            return cmd
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ['pwsh', '-NoProfile', '-Command', f"(Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\").CommandLine"],
            encoding='utf-8', errors='ignore'
        )
        cmd = out.strip()
        return cmd
    except Exception:
        return ''


def _get_parent_pid_windows(pid: int) -> int | None:
    if not pid or not str(pid).isdigit():
        return None
    try:
        out = subprocess.check_output(
            ['wmic', 'process', 'where', f'ProcessId={pid}', 'get', 'ParentProcessId'],
            encoding='utf-8', errors='ignore'
        )
        lines = [l.strip() for l in out.splitlines() if l.strip() and 'ParentProcessId' not in l]
        if lines and lines[0].isdigit():
            return int(lines[0])
    except Exception:
        pass
    try:
        system_root = os.environ.get('SystemRoot', r'C:\Windows')
        ps_path = os.path.join(system_root, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
        if os.path.exists(ps_path):
            out = subprocess.check_output(
                [ps_path, '-NoProfile', '-Command', f"(Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\").ParentProcessId"],
                encoding='utf-8', errors='ignore'
            )
            ppid = out.strip()
            if ppid.isdigit():
                return int(ppid)
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ['pwsh', '-NoProfile', '-Command', f"(Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\").ParentProcessId"],
            encoding='utf-8', errors='ignore'
        )
        ppid = out.strip()
        if ppid.isdigit():
            return int(ppid)
    except Exception:
        return None
    return None


def _is_ours_cmd(cmdline: str, project_root: str) -> bool:
    if not cmdline:
        return False
    cmd = cmdline.lower()
    return (
        'main_asgi' in cmd or
        'meteoser' in cmd or
        project_root.lower() in cmd
    )


def _is_official_parent_cmd(cmdline: str, project_root: str) -> bool:
    if not cmdline:
        return False
    cmd = cmdline.lower()
    allowed = [
        'nssm.exe',
        'arrancar_meteoser.bat',
        'arrancar_meteoser_autoreload.bat',
        'start_meteoser.ps1',
        'register_service_nssm.ps1',
        'install_nssm_service.ps1',
    ]
    return any(name in cmd for name in allowed)


def _enforce_official_start(project_root: str) -> tuple[bool, str]:
    if os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('METEOSER_TESTING') == '1':
        return True, 'test'
    require_official = os.environ.get('METEOSER_REQUIRE_OFFICIAL', '1') == '1'
    if not require_official:
        return True, 'not_required'
    if os.environ.get('METEOSER_OFFICIAL_START') != '1':
        return False, 'missing_env'
    if not platform.system().lower().startswith('win'):
        return True, 'non_windows'
    parent_pid = _get_parent_pid_windows(os.getpid())
    parent_cmd = _get_commandline_windows(parent_pid) if parent_pid else ''
    source = os.environ.get('METEOSER_OFFICIAL_SOURCE', '').lower()
    if source == 'service':
        if parent_cmd:
            if 'services.exe' in parent_cmd.lower() or 'nssm.exe' in parent_cmd.lower():
                return True, 'service_parent'
        if parent_pid and not parent_cmd:
            return True, 'service_parent_unknown'
    caller = os.environ.get('METEOSER_OFFICIAL_CALLER', '').lower()
    if caller in (
        'arrancar_meteoser.bat',
        'arrancar_meteoser_autoreload.bat',
        'start_meteoser.ps1',
    ):
        return True, 'caller_env'
    if not _is_official_parent_cmd(parent_cmd, project_root):
        return False, 'parent_not_official'
    return True, 'ok'


def _pids_escuchando_8080() -> list[int]:
    pids: list[int] = []
    if platform.system().lower().startswith('win'):
        try:
            output = subprocess.check_output('netstat -ano | findstr :8080', shell=True, encoding='utf-8')
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[4]
                    if pid.isdigit() and int(pid) != 0:
                        pids.append(int(pid))
        except Exception:
            pass
    return list(set(pids))


def liberar_puerto_8080_si_es_nuestro(project_root: str) -> tuple[bool, list[int]]:
    """Intenta liberar el puerto 8080 SOLO si el proceso parece de MeteoSer.
    Devuelve (liberado, pids_ajenos).
    """
    pids = _pids_escuchando_8080()
    if not pids:
        return True, []
    foreign: list[int] = []
    for pid in pids:
        cmd = _get_commandline_windows(pid)
        if _is_ours_cmd(cmd, project_root):
            try:
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        else:
            foreign.append(pid)
    return (len(foreign) == 0), foreign


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

# Raíz del proyecto y lock atómico de arranque
project_root = os.path.dirname(os.path.abspath(__file__))
allowed, reason = _enforce_official_start(project_root)
if not allowed:
    print(f'Arranque no oficial bloqueado ({reason}). Usa el arranque oficial.')
    sys.exit(2)
locks_dir = Path(project_root) / 'logs'
locks_dir.mkdir(parents=True, exist_ok=True)
start_lock = locks_dir / 'start.lock'
matador_lock_fd = None
try:
    matador_lock_fd = os.open(str(start_lock), os.O_CREAT | os.O_EXCL | os.O_RDWR)
    os.write(matador_lock_fd, str(os.getpid()).encode('utf-8'))
except FileExistsError:
    try:
        existing = start_lock.read_text().strip()
        existing_pid = int(existing) if existing.isdigit() else None
        if existing_pid and _is_pid_running(existing_pid):
            print(f'Otra instancia de arranque en curso (PID={existing_pid}), saliendo.')
            sys.exit(0)
        else:
            try:
                start_lock.unlink()
            except Exception:
                print('No se pudo eliminar el lock de arranque anterior; abortando para evitar duplicados.')
                sys.exit(1)
            matador_lock_fd = os.open(str(start_lock), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.write(matador_lock_fd, str(os.getpid()).encode('utf-8'))
    except Exception:
        print('No se pudo asegurar el lock de arranque; abortando para evitar duplicados.')
        sys.exit(1)

# Asegura que el script se ejecuta desde la raíz
os.chdir(project_root)

# Añadir la raíz del proyecto al PYTHONPATH para que los imports funcionen siempre
env = os.environ.copy()
env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

# Configuración de host/puerto desde variables de entorno (por defecto estable)
host = env.get("METEOSER_HOST", "0.0.0.0")
try:
    puerto_libre = int(env.get("METEOSER_PORT", "8080"))
except ValueError:
    puerto_libre = 8080

# Si ya hay un PID vivo registrado, no arrancar otra instancia
logs_dir = Path(project_root) / 'logs'
logs_dir.mkdir(parents=True, exist_ok=True)
pid_file = logs_dir / 'service.pid'
if pid_file.exists():
    try:
        existing = int(pid_file.read_text().strip())
    except Exception:
        existing = None
    if existing and _is_pid_running(existing):
        try:
            if matador_lock_fd is not None:
                os.close(matador_lock_fd)
        except Exception:
            pass
        print(f'Proceso ya en ejecución (PID={existing}), saliendo.')
        sys.exit(0)
    else:
        try:
            pid_file.unlink()
        except Exception:
            pass

# Liberar puerto sólo si es nuestro; si no, esperar y abortar para evitar daños
max_retries = 3
wait_seconds = 10
for attempt in range(1, max_retries + 1):
    ok, foreign = liberar_puerto_8080_si_es_nuestro(project_root)
    if ok:
        break
    print(f'Puerto 8080 ocupado por procesos ajenos {foreign}. Reintento {attempt}/{max_retries}...')
    time.sleep(wait_seconds)
else:
    try:
        if matador_lock_fd is not None:
            os.close(matador_lock_fd)
    except Exception:
        pass
    print('Puerto 8080 sigue ocupado por procesos ajenos. Abortando para evitar interferencias.')
    sys.exit(1)

# Comando uvicorn correcto para la interfaz real
cmd = [
    sys.executable, '-m', 'uvicorn',
    'main_asgi:app',
    '--host', host,
    '--port', str(puerto_libre)
]
if env.get('METEOSER_AUTORELOAD', '0') == '1':
    cmd.append('--reload')

# Sello oficial para el proceso hijo
env['METEOSER_OFFICIAL_START'] = '1'
env['METEOSER_REQUIRE_OFFICIAL'] = env.get('METEOSER_REQUIRE_OFFICIAL', '1')
token_file = logs_dir / 'official.token'
token = f"{os.getpid()}-{int(time.time())}-{secrets.token_hex(16)}"
try:
    token_file.write_text(token, encoding='utf-8')
except Exception:
    pass
env['METEOSER_OFFICIAL_TOKEN'] = token
env['METEOSER_OFFICIAL_PARENT_OK'] = '1'

print(f'Arrancando servidor MeteoSer FastAPI en http://{host}:{puerto_libre} ...')

# Preparar directorio de logs
out_log = logs_dir / 'servicio_out.log'
err_log = logs_dir / 'servicio_err.log'

# Abrir ficheros de log en modo append y lanzar uvicorn redirigiendo salida
stdout_f = open(out_log, 'a', encoding='utf-8')
stderr_f = open(err_log, 'a', encoding='utf-8')

proc = subprocess.Popen(cmd, stdout=stdout_f, stderr=stderr_f, env=env, cwd=project_root)

# Guardar PID para referencia / gestión externa
try:
    with open(pid_file, 'w') as f:
        f.write(str(proc.pid))
    print(f'PID guardado en: {pid_file} (PID={proc.pid})')
except Exception as e:
    print(f'No se pudo escribir PID: {e}')

# No bloqueamos: el proceso queda en background y las salidas se escriben en logs
try:
    if matador_lock_fd is not None:
        os.close(matador_lock_fd)
except Exception:
    pass
