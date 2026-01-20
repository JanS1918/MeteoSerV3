# Script para enviar datos reales simulados Ecowitt/HP2550A al endpoint /ecowitt
import requests

data = {
    "tempf": 23.7,  # Temperatura en ºF (puedes cambiar a ºC si tu estación lo envía así)
    "humidity": 56,  # Humedad relativa %
    "windspeedmph": 4.2,  # Viento en mph
    "rainratein": 0.01,  # Lluvia en pulgadas/hora
}

url = "http://127.0.0.1:8080/ecowitt"

resp = requests.post(url, data=data)
print("Respuesta:", resp.status_code, resp.json())
