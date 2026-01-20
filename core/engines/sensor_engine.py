"""
Módulo de sensores, autoconfiguración y fusión MeteoSer.

Incluye:
- Detección automática de sensores
- Autoconfiguración de funciones
- Autocalibración ligera
- Fusión de sensores primarios
- Sensores virtuales serios (permitidos)
- Estimaciones de refuerzo (permitidas)
- Prohibiciones estrictas (no inventar datos, no sustituir sensores)
"""

from typing import Dict, Any, Optional
from core.logging.log_engine import LogEngine


# ============================================================
# SENSOR MANAGER
# ============================================================

class SensorManager:
    """
    Gestiona sensores reales, su disponibilidad y su fiabilidad.
    """

    def __init__(self, log_engine: Optional[LogEngine] = None):
        self._log = log_engine
        self._sensores: Dict[str, Dict[str, Any]] = {}

    def registrar_sensor(self, nombre: str, tipo: str, fiabilidad: float = 100.0) -> None:
        """
        Registra un sensor real.
        """
        self._sensores[nombre] = {
            "tipo": tipo,
            "fiabilidad": fiabilidad,
            "activo": True,
        }
        if self._log:
            self._log.log("info", f"[SensorManager] Registrado sensor {nombre} ({tipo})")

    def desactivar_sensor(self, nombre: str) -> None:
        if nombre in self._sensores:
            self._sensores[nombre]["activo"] = False
            if self._log:
                self._log.log("info", f"[SensorManager] Sensor {nombre} desactivado")

    def obtener_sensores_activos(self) -> Dict[str, Dict[str, Any]]:
        return {k: v for k, v in self._sensores.items() if v["activo"]}

    def obtener_fiabilidad(self, nombre: str) -> float:
        sensor = self._sensores.get(nombre)
        if not sensor:
            return 0.0
        return sensor.get("fiabilidad", 0.0)


# ============================================================
# AUTOCONFIGURACIÓN
# ============================================================

class AutoConfigEngine:
    """
    Detecta qué funciones están disponibles según los sensores reales.
    """

    def __init__(self, sensor_manager: SensorManager, log_engine: Optional[LogEngine] = None):
        self._sensor_manager = sensor_manager
        self._log = log_engine
        self._funciones_activas: Dict[str, bool] = {}

    def actualizar(self) -> None:
        sensores = self._sensor_manager.obtener_sensores_activos()

        self._funciones_activas = {
            "confort": all(s in sensores for s in ["temperatura_interior", "humedad_interior", "co2"]),
            "edificio": "humedad_interior" in sensores,
            "meteorologia": "temperatura_exterior" in sensores,
            "ventilacion": "co2" in sensores,
            "prediccion_local": True,  # siempre disponible
        }

        if self._log:
            self._log.log("info", f"[AutoConfig] Funciones activas: {self._funciones_activas}")

    def funcion_activa(self, nombre: str) -> bool:
        return self._funciones_activas.get(nombre, False)


# ============================================================
# FUSIÓN DE SENSORES
# ============================================================

class SensorFusionEngine:
    """
    Fusión de sensores primarios + estimaciones de refuerzo.
    Prohibiciones:
    - NO sustituir sensores reales
    - NO inventar datos
    - NO generar valores sin base
    """

    def __init__(self, sensor_manager: SensorManager, log_engine: Optional[LogEngine] = None):
        self._sensor_manager = sensor_manager
        self._log = log_engine

    # ------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------

    def _log_debug(self, msg: str) -> None:
        if self._log:
            self._log.log("debug", msg)

    # ------------------------------------------------------------
    # FUSIÓN DE TEMPERATURA
    # ------------------------------------------------------------

    def fusionar_temperatura(self, contexto: Dict[str, Any]) -> Optional[float]:
        """
        Fusión simple:
        - Si hay un sensor principal → usarlo
        - Si hay varios → media ponderada por fiabilidad
        - Si falta → NO inventar → devolver None
        """

        valores = []
        pesos = []

        for nombre, datos in self._sensor_manager.obtener_sensores_activos().items():
            if datos["tipo"] == "temperatura_interior":
                valor = contexto.get(nombre)
                if valor is not None:
                    valores.append(valor)
                    pesos.append(datos["fiabilidad"])

        if not valores:
            return None

        if len(valores) == 1:
            return valores[0]

        total_peso = sum(pesos)
        fusion = sum(v * p for v, p in zip(valores, pesos)) / total_peso

        self._log_debug(f"[FusionTemp] valores={valores}, pesos={pesos}, fusion={fusion}")
        return fusion

    # ------------------------------------------------------------
    # FUSIÓN DE HUMEDAD
    # ------------------------------------------------------------

    def fusionar_humedad(self, contexto: Dict[str, Any]) -> Optional[float]:
        valores = []
        pesos = []

        for nombre, datos in self._sensor_manager.obtener_sensores_activos().items():
            if datos["tipo"] == "humedad_interior":
                valor = contexto.get(nombre)
                if valor is not None:
                    valores.append(valor)
                    pesos.append(datos["fiabilidad"])

        if not valores:
            return None

        if len(valores) == 1:
            return valores[0]

        total_peso = sum(pesos)
        fusion = sum(v * p for v, p in zip(valores, pesos)) / total_peso

        self._log_debug(f"[FusionHR] valores={valores}, pesos={pesos}, fusion={fusion}")
        return fusion

    # ------------------------------------------------------------
    # SENSORES VIRTUALES PERMITIDOS
    # ------------------------------------------------------------

    def estimar_punto_rocio(self, temperatura: float, humedad: float) -> Optional[float]:
        """
        Sensor virtual permitido: punto de rocío.
        Basado en fórmula científica real.
        """
        if temperatura is None or humedad is None:
            return None

        import math
        a, b = 17.27, 237.7
        alpha = ((a * temperatura) / (b + temperatura)) + math.log(humedad / 100.0)
        return (b * alpha) / (a - alpha)

    def estimar_ot(self, temperatura: float, radiacion: float = 0.0) -> Optional[float]:
        """
        Sensor virtual permitido: temperatura operativa.
        """
        if temperatura is None:
            return None
        return temperatura + radiacion * 0.1

    # ------------------------------------------------------------
    # PROHIBICIONES
    # ------------------------------------------------------------

    def prohibido_inventar(self) -> None:
        """
        Llamada explícita para recordar que NO se inventan datos.
        """
        if self._log:
            self._log.log("warning", "[SensorFusion] PROHIBIDO inventar datos")


# ============================================================
# ENVOLVENTE PRINCIPAL
# ============================================================

class SensorSystem:
    """
    Sistema completo de sensores:
    - manager
    - autoconfig
    - fusion
    """

    def __init__(self, log_engine: Optional[LogEngine] = None):
        self.manager = SensorManager(log_engine)
        self.autoconfig = AutoConfigEngine(self.manager, log_engine)
        self.fusion = SensorFusionEngine(self.manager, log_engine)

    def actualizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza autoconfiguración y devuelve valores fusionados.
        """
        self.autoconfig.actualizar()

        temperatura = self.fusion.fusionar_temperatura(contexto)
        humedad = self.fusion.fusionar_humedad(contexto)

        punto_rocio = None
        if temperatura is not None and humedad is not None:
            punto_rocio = self.fusion.estimar_punto_rocio(temperatura, humedad)

        return {
            "temperatura_fusionada": temperatura,
            "humedad_fusionada": humedad,
            "punto_rocio_estimado": punto_rocio,
            "funciones_activas": self.autoconfig._funciones_activas,
        }
