"""
MainLoop — Ciclo principal de MeteoSer.
"""

from time import sleep
from core.context.context_engine import ContextEngine
from core.api.api_engine import ApiEngine
from core.logging.log_engine import LogEngine


def main():
    log = LogEngine()
    ctx = ContextEngine(log)
    api = ApiEngine(ctx, log)

    # Datos de ejemplo (reemplazar por lecturas reales)
    datos = {
        "temperatura_interior": 21.5,
        "humedad_interior": 45.0,
        "co2": 650,
        "temperatura_exterior": 12.3,
    }

    while True:
        ctx.actualizar(datos)
        api.anunciar_estado()
        sleep(5)


if __name__ == "__main__":
    main()
