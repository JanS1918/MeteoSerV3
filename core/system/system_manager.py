# ============================================================
# MÓDULO F — SYSTEM MANAGER (GESTOR OPERATIVO)
# ============================================================

from core.system.system_core import SystemCore
from typing import Dict
from core.system.system_launcher import SystemLauncher
from core.location.location_engine import LocationEngine

EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales


class SystemManager:
    """
    Gestor operativo del sistema.
    Permite iniciar, reiniciar y obtener el estado del sistema.
    """

    def obtener_sensores(self):
        """
        Devuelve el diccionario de sensores actuales del sistema.
        """
        if not self.system:
            return {}
        return getattr(self.system, "sensores", {})

    def __init__(self) -> None:
        self.launcher = SystemLauncher()
        self.system = None
        self.location = LocationEngine()

    # --------------------------------------------------------
    # INICIAR SISTEMA
    # --------------------------------------------------------
    def iniciar(self) -> SystemCore:
        """
        Arranca el sistema completo usando el launcher.
        """
        self.system: SystemCore = self.launcher.launch()
        return self.system

    def set_manual_coordinates(self, lat: float, lon: float) -> None:
        self.location.set_manual_coordinates(lat, lon)

    def obtener_coordenadas(self) -> None | Dict[str, float]:
        if not self.system:
            return None
        return self.location.get_coordinates(self.system)

    # --------------------------------------------------------
    # REINICIAR SISTEMA
    # --------------------------------------------------------
    def reiniciar(self) -> SystemCore:
        """
        Reinicia todo el sistema desde cero.
        """
        self.system = None
        return self.iniciar()

    # --------------------------------------------------------
    # ESTADO COMPLETO
    # --------------------------------------------------------
    def obtener_estado(self):
        """
        Devuelve el estado completo del sistema.
        """
        if not self.system:
            return {"estado": "Sistema no iniciado."}
        return self.system.obtener_estado_completo()
