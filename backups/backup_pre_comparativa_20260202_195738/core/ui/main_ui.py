# ============================================================
# MÓDULO G — MAIN UI
# ============================================================

from core.system.system_manager import SystemManager

EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales

class MainUI:
    """
    # ...comentario obsoleto eliminado...
    Punto de entrada para obtener el estado del sistema.
    """

    def __init__(self):
        self.manager = SystemManager()
        self.system = None

    # --------------------------------------------------------
    # ARRANQUE
    # --------------------------------------------------------
    def iniciar(self):
        """
        Inicia el sistema completo.
        """
        self.system = self.manager.iniciar()

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------
    def mostrar_estado(self):
        """
        Devuelve un snapshot del estado del sistema.
        """
        if not self.system:
            return {"estado": "Sistema no iniciado."}
        return self.manager.obtener_estado()

    # --------------------------------------------------------
    # REINICIO
    # --------------------------------------------------------
    def reiniciar(self):
        """
        Reinicia el sistema completo.
        """
        self.system = self.manager.reiniciar()
        return self.mostrar_estado()