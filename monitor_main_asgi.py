import time
import os


def monitor_main_asgi(path, interval=2):
    print(f"[MONITOR] Vigilando cambios en: {path}")
    last_mtime = None
    while True:
        try:
            mtime = os.path.getmtime(path)
            if last_mtime is not None and mtime != last_mtime:
                print(
                    f"[ALERTA] El archivo {path} ha sido modificado externamente. ¡Revisa posibles sobrescrituras o editores!"
                )
            last_mtime = mtime
        except Exception as e:
            print(f"[ERROR] No se pudo acceder a {path}: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    monitor_main_asgi("main_asgi.py")
