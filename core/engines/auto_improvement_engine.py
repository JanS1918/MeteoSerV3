"""
Módulo de auto-mejora y auto-expansión de MeteoSer.

Incluye:
- MotorAutoMejora
- MotorAutoExpansion
- Registro de patrones de uso
- Ajuste dinámico de pesos y umbrales
- Evolución del sistema según el uso real
"""

from typing import Dict, Any, List, Optional
from core.logging.log_engine import LogEngine


# ============================================================
# MOTOR DE AUTO-MEJORA
# ============================================================


class MotorAutoMejora:
    """
    Observa el comportamiento del sistema y del usuario y ajusta:
    - pesos de índices
    - umbrales de avisos
    - sensibilidad de recomendaciones
    """

    def __init__(self, log_engine: Optional[LogEngine] = None):
        self._log = log_engine
        self._historial_eventos: List[Dict[str, Any]] = []
        self._pesos_indices: Dict[str, float] = {}
        self._umbrales_alerta: Dict[str, float] = {}

    # ---------------- UTILIDADES ----------------

    def _log_info(self, msg: str) -> None:
        if self._log:
            self._log.log("info", msg)

    def _log_debug(self, msg: str) -> None:
        if self._log:
            self._log.log("debug", msg)

    # ---------------- REGISTRO ----------------

    def registrar_evento(self, evento: Dict[str, Any]) -> None:
        """
        Registra un evento relevante:
        - tipo: 'alerta', 'recomendacion', 'accion_usuario', etc.
        - indice_relacionado
        - valor_indice
        - aceptado / ignorado
        """
        self._historial_eventos.append(evento)
        self._log_debug(f"[AutoMejora] Evento registrado: {evento}")

    # ---------------- AJUSTE DE PESOS ----------------

    def ajustar_pesos(self) -> None:
        """
        Ajusta pesos de índices según:
        - qué avisos se ignoran siempre
        - qué avisos se aceptan siempre
        - qué recomendaciones se usan más
        """
        if not self._historial_eventos:
            return

        contador_uso: Dict[str, int] = {}
        contador_ignorado: Dict[str, int] = {}

        for ev in self._historial_eventos:
            indice = ev.get("indice_relacionado")
            if not indice:
                continue

            if ev.get("aceptado"):
                contador_uso[indice] = contador_uso.get(indice, 0) + 1
            else:
                contador_ignorado[indice] = contador_ignorado.get(indice, 0) + 1

        for indice in set(list(contador_uso.keys()) + list(contador_ignorado.keys())):
            uso = contador_uso.get(indice, 0)
            ign = contador_ignorado.get(indice, 0)

            peso_actual = self._pesos_indices.get(indice, 1.0)

            if uso > ign:
                peso_actual *= 1.05
            elif ign > uso:
                peso_actual *= 0.95

            self._pesos_indices[indice] = max(0.1, min(5.0, peso_actual))

        self._log_info(f"[AutoMejora] Pesos ajustados: {self._pesos_indices}")

    # ---------------- AJUSTE DE UMBRALES ----------------

    def ajustar_umbrales(self) -> None:
        """
        Ajusta umbrales de alerta según:
        - frecuencia de disparo
        - frecuencia de aceptación
        """
        if not self._historial_eventos:
            return

        contador_alertas: Dict[str, int] = {}
        contador_aceptadas: Dict[str, int] = {}

        for ev in self._historial_eventos:
            if ev.get("tipo") != "alerta":
                continue
            indice = ev.get("indice_relacionado")
            if not indice:
                continue

            contador_alertas[indice] = contador_alertas.get(indice, 0) + 1
            if ev.get("aceptado"):
                contador_aceptadas[indice] = contador_aceptadas.get(indice, 0) + 1

        for indice, total in contador_alertas.items():
            aceptadas = contador_aceptadas.get(indice, 0)
            ratio = aceptadas / total if total > 0 else 0.0

            umbral_actual = self._umbrales_alerta.get(indice, 70.0)

            if ratio < 0.2:
                umbral_actual += 2.0
            elif ratio > 0.8:
                umbral_actual -= 2.0

            self._umbrales_alerta[indice] = max(10.0, min(90.0, umbral_actual))

        self._log_info(f"[AutoMejora] Umbrales ajustados: {self._umbrales_alerta}")

    # ---------------- CONSULTA ----------------

    def obtener_peso(self, indice: str) -> float:
        return self._pesos_indices.get(indice, 1.0)

    def obtener_umbral(self, indice: str) -> float:
        return self._umbrales_alerta.get(indice, 70.0)

    # ---------------- CICLO PRINCIPAL ----------------

    def ciclo(self) -> None:
        """
        Ciclo periódico de auto-mejora.
        """
        self.ajustar_pesos()
        self.ajustar_umbrales()


# ============================================================
# MOTOR DE AUTO-EXPANSIÓN
# ============================================================


class MotorAutoExpansion:
    """
    Observa patrones de uso y propone:
    - nuevas funciones
    - nuevos índices
    - nuevas pantallas
    - nuevas automatizaciones
    (solo propone, no ejecuta cambios estructurales sin intervención humana)
    """

    def __init__(self, log_engine: Optional[LogEngine] = None):
        self._log = log_engine
        self._historial_peticiones: List[Dict[str, Any]] = []
        self._sugerencias: List[str] = []

    def registrar_peticion(self, peticion: Dict[str, Any]) -> None:
        """
        Registra una petición del usuario:
        - tipo: 'consulta', 'accion', 'repetida', etc.
        - texto
        - contexto
        """
        self._historial_peticiones.append(peticion)
        if self._log:
            self._log.log("debug", f"[AutoExpansion] Petición registrada: {peticion}")

    def generar_sugerencias(self) -> List[str]:
        """
        Analiza el historial y genera sugerencias de expansión.
        (Implementación simple: detecta repeticiones de patrones)
        """
        contador: Dict[str, int] = {}

        for p in self._historial_peticiones:
            texto = p.get("texto", "").strip().lower()
            if not texto:
                continue
            contador[texto] = contador.get(texto, 0) + 1

        self._sugerencias = [
            f"Crear función específica para: '{texto}' (usada {n} veces)"
            for texto, n in contador.items()
            if n >= 5
        ]

        if self._log:
            self._log.log(
                "info", f"[AutoExpansion] Sugerencias generadas: {self._sugerencias}"
            )

        return self._sugerencias

    def obtener_sugerencias(self) -> List[str]:
        return self._sugerencias


# ============================================================
# SISTEMA DE AUTO-MEJORA COMPLETO
# ============================================================


class AutoImprovementSystem:
    """
    Sistema completo de auto-mejora + auto-expansión.
    """

    def __init__(self, log_engine: Optional[LogEngine] = None):
        self.auto_mejora = MotorAutoMejora(log_engine)
        self.auto_expansion = MotorAutoExpansion(log_engine)

    def registrar_evento(self, evento: Dict[str, Any]) -> None:
        self.auto_mejora.registrar_evento(evento)

    def registrar_peticion(self, peticion: Dict[str, Any]) -> None:
        self.auto_expansion.registrar_peticion(peticion)

    def ciclo(self) -> Dict[str, Any]:
        """
        Ejecuta un ciclo de auto-mejora y genera sugerencias de expansión.
        """
        self.auto_mejora.ciclo()
        sugerencias = self.auto_expansion.generar_sugerencias()

        return {
            "pesos_indices": self.auto_mejora._pesos_indices,
            "umbrales_alerta": self.auto_mejora._umbrales_alerta,
            "sugerencias_expansion": sugerencias,
        }
