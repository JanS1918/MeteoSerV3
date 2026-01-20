# Script para automatizar la consulta y visualización de sensores, índices y recomendaciones en tiempo real
import requests
import time
import os

ENDPOINTS = {
    "sensores": "http://127.0.0.1:8080/sensores",
    "indices": "http://127.0.0.1:8080/meteorologia",
    "recomendacion": "http://127.0.0.1:8080/recomendacion_unificada",
}


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def mostrar_estado():
    def get_json_safe(url):
        try:
            r = requests.get(url, timeout=3)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": f"No disponible: {e}"}

    sensores = get_json_safe(ENDPOINTS["sensores"])
    indices = get_json_safe(ENDPOINTS["indices"])
    recomendacion = get_json_safe(ENDPOINTS["recomendacion"])
    clear()
    print("=== ESTADO METEOSER EN TIEMPO REAL ===\n")
    print("[Sensores]")
    print(sensores)
    print("\n[Índices]")
    print(indices)
    print("\n[Recomendación]")
    print(recomendacion)


if __name__ == "__main__":
    while True:
        mostrar_estado()
        time.sleep(5)
