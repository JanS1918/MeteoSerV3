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
from core.bus.bus_grifo_inteligente import GrifoInteligente


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
        if valor is not None:
            return valor
        grifo = GrifoInteligente.obtener_instancia()
        cache_valor = grifo.obtener_valor(variable)
        return default if cache_valor is None else cache_valor

    def consumir(self, variable: str, consumidor: str = "unknown") -> Any:
        valor = self._bus.obtener(variable)
        if valor is not None:
            return valor
        grifo = GrifoInteligente.obtener_instancia()
        return grifo.obtener_valor(variable)
    
    def obtener_valor(self, variable: str, nivel: str = "CORE", default: Any = None) -> Any:
        """Obtiene valor de una variable. Compatible con BusCapasInformacion."""
        valor = self._bus.obtener(variable)
        if valor is not None:
            return valor
        grifo = GrifoInteligente.obtener_instancia()
        cache_valor = grifo.obtener_valor(variable)
        return default if cache_valor is None else cache_valor

    def existe(self, variable: str) -> bool:
        if self._bus.obtener(variable) is not None:
            return True
        grifo = GrifoInteligente.obtener_instancia()
        return grifo.obtener_valor(variable) is not None

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
    
    # API OMNISCIENCIA V30.1 - Selección automática de fórmulas
    def consumir_elite(self, parametro_abstracto: str, consumidor: str) -> tuple:
        """
        Obtiene la mejor versión disponible de un parámetro según jerarquía de fórmulas.
        
        Args:
            parametro_abstracto: Nombre lógico ("punto_rocio", "sensacion_termica", etc)
            consumidor: Quién solicita (ej: "niebla_module", "cetreria_engine")
        
        Returns:
            (valor, nivel_elite, nombre_tecnico) o (None, 0, None) si no disponible
        """
        from core.bus.parametros_canonicos import normalizar_parametro_bus
        from core.bus.formula_hierarchy import FORMULA_HIERARCHY
        from core.monitoring.formula_override_manager import FormulaOverrideManager
        from core.monitoring.formula_candidate_registry import FormulaCandidateRegistry
        import logging

        logger = logging.getLogger("bus_omniscience")

        parametro_normalizado = normalizar_parametro_bus(parametro_abstracto)
        if parametro_normalizado != parametro_abstracto:
            logger.warning(
                "[WARNING] Parámetro no canónico recibido: '%s' -> '%s'",
                parametro_abstracto,
                parametro_normalizado,
            )

        jerarquia = FORMULA_HIERARCHY.get(parametro_normalizado)
        if not jerarquia:
            logger.error(
                f"[ERROR] Parámetro '{parametro_normalizado}' NO está en Registro de Élite V30.1"
            )
            return (None, 0, None)
        
        # Aplicar override si existe
        try:
            override_mgr = FormulaOverrideManager()
            temp_actual = self._bus.obtener("temperatura")
            temp_val = None
            try:
                if isinstance(temp_actual, dict):
                    temp_val = temp_actual.get("valor")
                else:
                    temp_val = temp_actual
                if temp_val is not None:
                    temp_val = float(temp_val)
            except Exception:
                temp_val = None
            override = override_mgr.get_override(parametro_normalizado, temp_val)
            if override:
                valor_override = self._bus.obtener(override)
                if valor_override is not None:
                    return (valor_override, 0, override)
                registry = FormulaCandidateRegistry()
                cand = registry.resolver(override) or registry.resolver_por_alias(override)
                if cand:
                    fn = registry.obtener_funcion(cand)
                    if fn:
                        inputs = registry.obtener_inputs(cand)
                        args = [self._bus.obtener(k) for k in inputs]
                        if all(v is not None for v in args):
                            try:
                                res = fn(*args)
                                if isinstance(res, dict) and "valor" in res:
                                    res = res["valor"]
                                return (res, 0, cand.get("id"))
                            except Exception:
                                pass
        except Exception:
            pass

        # Ordenar niveles de mejor a peor
        from core.bus.formula_hierarchy import NivelElite
        niveles_ordenados = sorted(jerarquia.keys(), 
                                  key=lambda n: n.value, 
                                  reverse=True)
        
        for nivel in niveles_ordenados:
            formula = jerarquia[nivel]
            nombre_tecnico = formula.nombre_tecnico
            
            # Buscar en Bus V3
            valor = self._bus.obtener(nombre_tecnico)
            
            if valor is not None:
                # LOG TRANSPARENTE
                if nivel.value < max(j.value for j in niveles_ordenados):
                    logger.warning(
                        f"[WARNING] {consumidor} solicitó '{parametro_normalizado}' → "
                        f"Usando nivel {nivel.value} ({formula.nombre_legible}). "
                        f"ELITE (nivel {max(j.value for j in niveles_ordenados)}) no disponible."
                    )
                else:
                    logger.info(
                        f"[OK] {consumidor} → '{parametro_normalizado}' "
                        f"ELITE nivel {nivel.value} ({formula.nombre_legible})"
                    )
                
                return (valor, nivel.value, nombre_tecnico)
        
        # No hay ninguna versión disponible
        logger.error(
            f"[ERROR] {consumidor} pidió '{parametro_normalizado}' - "
            f"NINGUNA versión disponible en Bus"
        )
        return (None, 0, None)
    
    def publicar_elite(self, parametro_abstracto: str, valor: Any, 
                      nivel_elite: int, publicador: str, metadata: dict = None) -> None:
        """
        Publica un valor CON su nivel de calidad declarado en Registro de Élite.
        
        Args:
            parametro_abstracto: "punto_rocio", "sensacion_termica", etc.
            valor: El valor a publicar
            nivel_elite: NivelElite.ELITE.value (10), .PROFESIONAL.value (7), etc.
            publicador: Quién publica (ej: "hardy_module")
            metadata: Diccionario con {"formula": "...", "precision": "..."}
        """
        from core.bus.parametros_canonicos import normalizar_parametro_bus
        from core.bus.formula_hierarchy import FORMULA_HIERARCHY, NivelElite
        import logging
        logger = logging.getLogger("bus_omniscience")

        parametro_normalizado = normalizar_parametro_bus(parametro_abstracto)
        if parametro_normalizado != parametro_abstracto:
            logger.warning(
                "[WARNING] Parámetro no canónico recibido: '%s' -> '%s'",
                parametro_abstracto,
                parametro_normalizado,
            )

        jerarquia = FORMULA_HIERARCHY.get(parametro_normalizado, {})
        
        # Encontrar la fórmula para este nivel
        nivel_obj = None
        for n in jerarquia.keys():
            if n.value == nivel_elite:
                nivel_obj = n
                break
        
        if not nivel_obj:
            logger.error(
                f"Nivel {nivel_elite} no definido para '{parametro_normalizado}' en Registro"
            )
            return
        
        formula = jerarquia[nivel_obj]
        nombre_tecnico = formula.nombre_tecnico
        
        # Publicar en Bus V3 con nombre técnico
        self._bus.publicar(nombre_tecnico, valor)
        
        # Guardar metadatos
        if nombre_tecnico not in self._metadatos:
            self._metadatos[nombre_tecnico] = {}
        
        meta = metadata or {}
        meta.setdefault("formula", formula.nombre_legible)
        meta.setdefault("precision", formula.precisión)
        meta.setdefault("referencia", formula.referencia)
        
        self._metadatos[nombre_tecnico].update({
            "nivel_elite": nivel_elite,
            "nivel_nombre": nivel_obj.name,
            "publicador": publicador,
            "formula": formula.nombre_legible,
            "timestamp": datetime.now()
        })
        
        logger.info(
            f"📤 {publicador} publicó '{parametro_normalizado}' "
            f"nivel {nivel_elite} ({nivel_obj.name}) como '{nombre_tecnico}'"
        )
