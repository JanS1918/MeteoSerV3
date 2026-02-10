import logging
# ============================================================
#  MÓDULO 1 — INTEGRACIÓN AUTOMÁTICA DE SENSORES
#  Archivo: core/integration/integration_manager.py
# ============================================================

import json
import os

class SensorRegistry:
    """
    Registro central de sensores detectados.
    MeteoSer consulta aquí qué sensores existen y qué capacidades activan.
    """

    def __init__(self):
        self.sensors = {}
        self.capabilities = set()

    def register(self, sensor_type, sensor_id, metadata=None):
        """
        Registra un sensor detectado.
        sensor_type: "WH65", "WH57", "WH51", etc.
        sensor_id: identificador único (MAC, ID interno, etc.)
        metadata: dict opcional con detalles adicionales
        """
        if sensor_type not in self.sensors:
            self.sensors[sensor_type] = []

        self.sensors[sensor_type].append({
            "id": sensor_id,
            "metadata": metadata or {}
        })

        self._update_capabilities(sensor_type)

    def _update_capabilities(self, sensor_type):
        """
        Activa capacidades automáticas según el tipo de sensor detectado.
        """

        mapping = {
            "WH65": [
                "temp_ext", "hum_ext", "viento", "lluvia",
                "radiacion", "uv", "presion"
            ],
            "WH57": ["rayos"],
            "WH51": ["hum_suelo"],
            "WH31": ["temp_int", "hum_int"],
            "WH43": ["pm25_int"],
            "ICASA_CO2": ["co2_int"],
            "WH55": ["fugas"],
            "WN38": ["wbgt_real"],
            "TABLET": ["presencia", "luz_int", "ruido_int"]
        }

        if sensor_type in mapping:
            for cap in mapping[sensor_type]:
                self.capabilities.add(cap)

    def get_sensors(self):
        return self.sensors

    def get_capabilities(self):
        return list(self.capabilities)


class SensorIntegrationManager:
    """
    Motor de integración automática.
    Detecta sensores, los registra y activa funciones dependientes.
    """

    REGISTRY_FILE = "sensor_registry.json"

    def __init__(self, base_path):
        self.base_path = base_path
        self.registry = SensorRegistry()
        self._load_registry()

    # ------------------------------------------------------------
    # CARGA Y GUARDADO DEL REGISTRO
    # ------------------------------------------------------------

    def _registry_path(self):
        return os.path.join(self.base_path, self.REGISTRY_FILE)

    def _load_registry(self):
        """
        Carga el registro desde disco si existe.
        """
        path = self._registry_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    self.registry.sensors = data.get("sensors", {})
                    self.registry.capabilities = set(data.get("capabilities", []))
            except:
                logging.exception("Silent except at 98 - revisar contexto")

    def _save_registry(self):
        """
        Guarda el registro en disco.
        """
        data = {
            "sensors": self.registry.sensors,
            "capabilities": list(self.registry.capabilities)
        }
        with open(self._registry_path(), "w") as f:
            json.dump(data, f, indent=4)

    # ------------------------------------------------------------
    # DETECCIÓN Y REGISTRO
    # ------------------------------------------------------------

    def detect_and_register(self, sensor_type, sensor_id, metadata=None):
        """
        Punto de entrada para registrar sensores detectados.
        """
        self.registry.register(sensor_type, sensor_id, metadata)
        self._save_registry()

    # ------------------------------------------------------------
    # CONSULTAS
    # ------------------------------------------------------------

    def get_registered_sensors(self):
        return self.registry.get_sensors()

    def get_capabilities(self):
        return self.registry.get_capabilities()

    # ------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------

    def has_capability(self, capability):
        return capability in self.registry.capabilities

    def sensor_exists(self, sensor_type):
        return sensor_type in self.registry.sensors


# ============================================================
#  FIN DEL MÓDULO
# ============================================================