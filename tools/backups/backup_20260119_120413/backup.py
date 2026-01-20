import shutil
import datetime
import os

def crear_backup():
    fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = f"backup_{fecha}"

    os.makedirs(destino, exist_ok=True)

    archivos = [
        "meteoser.py",
        "core"
    ]

    for item in archivos:
        if os.path.isdir(item):
            shutil.copytree(item, os.path.join(destino, item))
        else:
            shutil.copy2(item, destino)

    print(f"Backup creado en: {destino}")