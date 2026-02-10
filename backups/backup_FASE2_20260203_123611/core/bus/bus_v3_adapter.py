"""
Adaptador del Bus V3 Mejorado para compatibilidad con la API de BusCapasInformacion.

Objetivo:
- Hacer que obtener_bus() devuelva el Bus V3 por defecto.
- Mantener la firma publicar() usada en el código existente.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from ejemplo_bus_v3_mejorado import BusV3Mejorado


class BusV3Adapter:
    """
    Adaptador compatible con la API esperada por el código actual.
    """

    def __init__(self, tamaño_cola_escritura: int = 10000, ventana_historico: int = 100):
        self._bus = BusV3Mejorado(
            tamaño_cola_escritura=tamaño_cola_escritura,
            ventana_historico=ventana_historico
        )
        self._bus.iniciar()
        self._metadatos: Dict[str, Dict[str, Any]] = {}

    # API compatible con BusCapasInformacion
    def publicar(
        self,
        variable: str,
        valor: Any,
        nivel: str = "CORE",
        origen: str = "unknown.unknown",
        confianza: float = 1.0,
        precondiciones: Optional[List[str]] = None,
        consumidores: Optional[List[str]] = None,
        unidad: str = "",
        rango_esperado: Optional[tuple] = None,
        notas: str = ""
    ) -> bool:
        """
        Publica en el Bus V3. Mantiene firma legacy, ignora el filtrado por capas.
        """
        self._metadatos[variable] = {
            "nivel": nivel,
            "origen": origen,
            "confianza": confianza,
            "precondiciones": precondiciones or [],
            "consumidores": consumidores or [],
            "unidad": unidad,
            "rango_esperado": rango_esperado,
            "notas": notas,
            "timestamp": datetime.now()
        }
        return self._bus.publicar(variable, valor)

    def obtener(self, variable: str, default: Any = None) -> Any:
        valor = self._bus.obtener(variable)
        return default if valor is None else valor

    def consumir(self, variable: str, consumidor: str = "unknown") -> Any:
        return self._bus.obtener(variable)

    def existe(self, variable: str) -> bool:
        return self._bus.obtener(variable) is not None

    # API de búsqueda
    def obtener_familia(self, prefijo: str):
        return self._bus.obtener_familia(prefijo)

    def buscar(self, patron: str):
        return self._bus.buscar(patron)

    # API de histórico
    def obtener_serie_para_lstm(self, adn: str, ultimas_n: int = 60):
        return self._bus.obtener_serie_para_lstm(adn, ultimas_n)

    def obtener_todas_series_para_lstm(self, ultimas_n: int = 60):
        return self._bus.obtener_todas_series_para_lstm(ultimas_n)

    # API de snapshot
    def generar_snapshot(self):
        return self._bus.generar_snapshot()

    def obtener_snapshot_formateado(self):
        return self._bus.obtener_snapshot_formateado()

    def obtener_snapshot_completo_para_ia(self):
        return self._bus.obtener_snapshot_completo_para_ia()

    # Estadísticas
    def obtener_estadisticas_completas(self):
        return self._bus.obtener_estadisticas_completas()

    # Control de ciclo de vida
    def detener(self):
        self._bus.detener()
