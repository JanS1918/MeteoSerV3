# ============================================================
# MÓDULO A — ARQUITECTURA UNIFICADA
# ============================================================

EXTERNAL_INTEGRATION_MODE = "mock"  # Siempre seguro


class OpenArchitecture:
    """
    Núcleo arquitectónico unificado.
    Punto central donde se conectan sensores, índices,
    recomendaciones, aprendizaje y evolución del sistema.
    """

    def __init__(self, system_core):
        self.system = system_core
        self.registrar_componentes()

    # --------------------------------------------------------
    # REGISTRO CENTRALIZADO
    # --------------------------------------------------------
    def registrar_componentes(self):
        """
        Punto único donde se registran todos los módulos del sistema.
        Cada módulo se conecta aquí, no en otros archivos.
        """
        self._registrar_sensores()
        self._registrar_indices()
        self._registrar_recomendaciones()

    # --------------------------------------------------------
    # SENSORES
    # --------------------------------------------------------
    def _registrar_sensores(self):
        """
        Registro unificado de sensores.
        Aquí se añaden todos los sensores físicos o virtuales.
        """
        try:
            self.system.registrar_sensor("temperatura", None)
            self.system.registrar_sensor("humedad", None)
            self.system.registrar_sensor("viento", None)
            self.system.registrar_sensor("lluvia", None)
        except Exception as e:
            print("Error registrando sensores:", e)

    # --------------------------------------------------------
    # ÍNDICES
    # --------------------------------------------------------
    def _registrar_indices(self):
        """
        Registro unificado de índices meteorológicos.
        """
        try:
            self.system.registrar_indice("sensacion_termica", None)
            self.system.registrar_indice("indice_uv", None)
            self.system.registrar_indice("riesgo_lluvia", None)
        except Exception as e:
            print("Error registrando índices:", e)

    # --------------------------------------------------------
    # RECOMENDACIONES
    # --------------------------------------------------------
    def _registrar_recomendaciones(self):
        """
        Registro unificado de motores de recomendación.
        """
        try:
            self.system.registrar_indice("recomendacion_general", None)
        except Exception as e:
            print("Error registrando recomendaciones:", e)

    # --------------------------------------------------------
    # INTERFAZ PÚBLICA
    # --------------------------------------------------------
    def obtener_estado(self):
        """
        Devuelve un snapshot unificado del sistema.
        """
        return {
            "sensores": self.system.sensores,
            "indices": self.system.indices,
            "recomendacion": self.system.obtener_recomendacion(),
        }
