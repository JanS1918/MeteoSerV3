import shutil
import os


def rollback(origen):
    if not os.path.isdir(origen):
        print(f"No existe el backup: {origen}")
        return

    # Restaurar archivos y carpetas
    for item in os.listdir(origen):
        src = os.path.join(origen, item)
        dst = item

        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    print(f"Rollback completado desde: {origen}")
