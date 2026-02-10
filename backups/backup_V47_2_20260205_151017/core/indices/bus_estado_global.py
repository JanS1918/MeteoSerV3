# ⚡ BUS DE ESTADO GLOBAL - ARQUITECTURA DE CASCADA INTEGRAL
# ════════════════════════════════════════════════════════════════════════════
# Este módulo implementa el Bus de Estado Global (Singleton por Ciclo)
# para garantizar CERO REDUNDANCIA en los cálculos físicos.
#
# PARADIGMA:
# - Cada variable física se calcula UNA SOLA VEZ por ciclo
# - Las fórmulas complejas publican todos sus subresultados
# - Los demás nodos consumen del Bus sin recalcular nada
#
# ARQUITECTURA:
# - Single Source of Truth: Un solo valor por variable por ciclo
# - Herencia de Muñecas Rusas: Los cálculos complejos alimentan a los simples
# - Consistencia Atómica: Cambios se propagan instantáneamente
# ════════════════════════════════════════════════════════════════════════════

import logging
import threading
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
import json

logger = logging.getLogger("bus_estado_global")


class BusEstadoGlobal:
    """
    Bus de Estado Global (Singleton por Ciclo de Datos).
    
    Garantiza que cada variable física se calcule UNA SOLA VEZ por ciclo,
    eliminando redundancia y asegurando consistencia atómica.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Inicializa el bus de estado."""
        self._estado: Dict[str, Any] = {}
        self._metadatos: Dict[str, Dict[str, Any]] = {}
        self._dependencias: Dict[str, Set[str]] = {}
        self._ciclo_id: Optional[str] = None
        self._timestamp: Optional[datetime] = None
        self._log_accesos: Dict[str, int] = {}
        
    @classmethod
    def obtener_instancia(cls) -> 'BusEstadoGlobal':
        """Obtiene la instancia singleton del bus."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def nuevo_ciclo(cls, ciclo_id: str) -> 'BusEstadoGlobal':
        """
        Crea un nuevo ciclo de cálculo, reseteando el bus.
        
        Args:
            ciclo_id: Identificador único del ciclo (ej: timestamp)
        
        Returns:
            Instancia del bus resetada
        """
        with cls._lock:
            cls._instance = cls()
            cls._instance._ciclo_id = ciclo_id
            cls._instance._timestamp = datetime.now()
            logger.info(f"[BUS] Nuevo ciclo iniciado: {ciclo_id}")
        return cls._instance
    
    def publicar(
        self,
        clave: str,
        valor: Any,
        fuente: str,
        metadatos: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Publica una variable en el bus.
        
        Args:
            clave: Nombre de la variable (ej: 'densidad_aire', 'punto_rocio')
            valor: Valor calculado
            fuente: Predicción o módulo que publica (ej: 'visibilidad_bucholtz')
            metadatos: Información adicional (fórmula, unidades, etc.)
        """
        if clave in self._estado:
            logger.warning(
                f"[BUS] Variable '{clave}' ya publicada por '{self._metadatos[clave]['fuente']}'. "
                f"Intento de sobrescritura por '{fuente}' ignorado."
            )
            return
        
        self._estado[clave] = valor
        self._metadatos[clave] = {
            "fuente": fuente,
            "timestamp": datetime.now(),
            "metadatos": metadatos or {}
        }
        self._log_accesos[clave] = 0
        
        logger.debug(f"[BUS] Publicado '{clave}' = {valor} por '{fuente}'")
    
    def consumir(self, clave: str, consumidor: str) -> Optional[Any]:
        """
        Consume una variable del bus.
        
        Args:
            clave: Nombre de la variable
            consumidor: Predicción o módulo que consume
        
        Returns:
            Valor de la variable, o None si no existe
        """
        if clave not in self._estado:
            logger.debug(f"[BUS] Variable '{clave}' no disponible para '{consumidor}'")
            return None
        
        # Registrar dependencia
        if consumidor not in self._dependencias:
            self._dependencias[consumidor] = set()
        self._dependencias[consumidor].add(self._metadatos[clave]["fuente"])
        
        # Incrementar contador de accesos
        self._log_accesos[clave] += 1
        
        logger.debug(
            f"[BUS] '{consumidor}' consumió '{clave}' "
            f"(publicado por '{self._metadatos[clave]['fuente']}')"
        )
        
        return self._estado[clave]
    
    def existe(self, clave: str) -> bool:
        """Verifica si una variable existe en el bus."""
        return clave in self._estado
    
    def obtener_dependencias(self) -> Dict[str, List[str]]:
        """
        Retorna el grafo de dependencias del ciclo actual.
        
        Returns:
            Dict donde cada clave es un consumidor y su valor es la lista
            de fuentes de las que depende.
        """
        return {k: list(v) for k, v in self._dependencias.items()}
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del ciclo actual.
        
        Returns:
            Dict con métricas de uso del bus
        """
        total_variables = len(self._estado)
        variables_usadas = sum(1 for count in self._log_accesos.values() if count > 0)
        variables_no_usadas = total_variables - variables_usadas
        
        # Variables más reutilizadas
        top_reutilizadas = sorted(
            self._log_accesos.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "ciclo_id": self._ciclo_id,
            "timestamp": self._timestamp.isoformat() if self._timestamp else None,
            "total_variables": total_variables,
            "variables_usadas": variables_usadas,
            "variables_no_usadas": variables_no_usadas,
            "eficiencia": f"{(variables_usadas / total_variables * 100):.1f}%" if total_variables > 0 else "N/A",
            "top_reutilizadas": [
                {"variable": k, "accesos": v} for k, v in top_reutilizadas if v > 0
            ],
            "grafo_dependencias": self.obtener_dependencias()
        }
    
    def obtener_todas_variables(self) -> Dict[str, Any]:
        """Retorna todas las variables publicadas en el ciclo."""
        return self._estado.copy()
    
    def limpiar(self) -> None:
        """Limpia el bus (usado al finalizar un ciclo)."""
        self._estado.clear()
        self._metadatos.clear()
        self._dependencias.clear()
        self._log_accesos.clear()
        logger.info(f"[BUS] Ciclo {self._ciclo_id} finalizado y limpiado")


# ============================================================
# GRAFO DE DEPENDENCIAS DE LAS 25 PREDICCIONES
# ============================================================

GRAFO_DEPENDENCIAS_V20 = {
    "tendencia_barometrica": {
        "publica": ["presion_filtrada", "delta_presion_tidal", "delta_presion_wind", "densidad_aire"],
        "consume": []
    },
    "lluvia_local": {
        "publica": ["pwv", "eta_convective", "tau_uv"],  # nubosidad eliminada (fuente única: nubosidad_haurwitz)
        "consume": ["densidad_aire", "nubosidad"]
    },
    "cota_nieve": {
        "publica": ["temp_bulbo_humedo", "isoterma_0c", "densidad_virial"],
        "consume": ["densidad_aire", "punto_rocio"]
    },
    "tormenta_inminente": {
        "publica": ["cape", "gradiente_presion", "indice_severidad"],
        "consume": ["nubosidad", "densidad_aire", "punto_rocio"]
    },
    "helada_radiativa": {
        "publica": ["radiacion_neta", "temp_superficie", "kappa_suelo"],
        "consume": []
    },
    "visibilidad_bucholtz": {
        "publica": ["beta_ext", "beta_rayleigh", "indice_refraccion"],  # densidad_aire eliminada (fuente única: tendencia_barometrica)
        "consume": ["nubosidad", "densidad_aire"]
    },
    "riesgo_niebla": {
        "publica": ["deficit_saturacion"],  # punto_rocio y presion_vapor eliminadas (fuente única: punto_rocio_wexler)
        "consume": ["temp_bulbo_humedo", "nubosidad", "punto_rocio", "presion_vapor"]
    },
    "disipacion_humo": {
        "publica": ["lambda_ach", "tasa_renovacion_aire"],
        "consume": ["densidad_aire"]
    },
    "saturacion_co2": {
        "publica": ["concentracion_co2_equilibrio", "tasa_acumulacion"],
        "consume": ["densidad_aire", "tasa_renovacion_aire"]
    },
    "et_real": {
        "publica": ["et0_penman", "kcb", "ke", "deficit_presion_vapor"],
        "consume": ["punto_rocio", "densidad_aire", "radiacion_neta"]
    },
    "utci": {
        "publica": ["utci", "temp_radiante_media", "velocidad_viento_corregida"],
        "consume": ["punto_rocio", "densidad_aire", "radiacion_neta"]
    },
    "monin_obukhov": {
        "publica": ["zeta", "longitud_obukhov", "u_star", "flujo_calor"],
        "consume": ["densidad_aire"]
    },
    "nubosidad_haurwitz": {
        "publica": ["nubosidad", "transmitancia", "radiacion_teorica"],
        "consume": []
    },
    "incomodidad_termica": {
        "publica": ["thi", "indice_calor"],
        "consume": ["punto_rocio", "densidad_aire"]
    },
    "punto_rocio_wexler": {
        "publica": ["punto_rocio", "presion_vapor", "factor_compresibilidad"],
        "consume": []
    },
    "indice_sequia": {
        "publica": ["deficit_hidrico", "spi"],
        "consume": ["et0_penman", "pwv"]
    },
    "recomendacion_riego": {
        "publica": ["volumen_agua_necesario", "deficit_mad"],
        "consume": ["et0_penman", "deficit_hidrico"]
    },
    "wbgt_stull": {
        "publica": ["wbgt", "temp_globo", "temp_bulbo_natural"],
        "consume": ["punto_rocio", "densidad_aire", "radiacion_neta"]
    },
    "tiempo_ventilacion": {
        "publica": ["caudal_ventilacion_stack", "caudal_ventilacion_wind"],
        "consume": ["densidad_aire"]
    },
    "riesgo_mojar_ropa": {
        "publica": ["tiempo_secado", "coef_transferencia_masa"],
        "consume": ["punto_rocio", "deficit_presion_vapor"]
    },
    "pseudo_voc": {
        "publica": ["voc_estimado", "tasa_degradacion_uv"],
        "consume": ["tasa_renovacion_aire"]
    },
    "temp_radiante_int": {
        "publica": ["tmrt_interior", "factor_forma"],
        "consume": ["radiacion_neta"]
    },
    "ruido_relativo": {
        "publica": ["nivel_sonoro_eq"],
        "consume": []
    },
    "corrientes_internas": {
        "publica": ["velocidad_flujo_interior", "diferencial_presion"],
        "consume": ["densidad_aire"]
    },
    "riesgo_moho": {
        "publica": ["indice_moho", "tiempo_germinacion"],
        "consume": ["punto_rocio", "tasa_renovacion_aire"]
    }
}


def exportar_mapa_dependencias(ruta_salida: str) -> tuple:
    """
    Exporta el mapa de dependencias a formato JSON y Markdown.
    
    Args:
        ruta_salida: Directorio donde guardar los archivos
        
    Returns:
        tuple: (ruta_json, ruta_markdown)
    """
    from pathlib import Path
    
    ruta = Path(ruta_salida)
    ruta.mkdir(parents=True, exist_ok=True)
    
    # Exportar JSON
    json_path = ruta / "MAPA_DEPENDENCIAS_V20.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(GRAFO_DEPENDENCIAS_V20, f, indent=2, ensure_ascii=False)
    
    # Exportar Markdown
    md_path = ruta / "MAPA_DEPENDENCIAS_V20.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# MAPA DE DEPENDENCIAS - ARQUITECTURA DE CASCADA V2.0\n\n")
        f.write("**Generado:** " + datetime.now().isoformat() + "\n\n")
        f.write("## Filosofía del Sistema\n\n")
        f.write("Este sistema implementa una Arquitectura de Cascada Integral donde:\n")
        f.write("- Cada variable física se calcula UNA SOLA VEZ por ciclo\n")
        f.write("- Las fórmulas complejas publican todos sus subresultados\n")
        f.write("- Los demás nodos consumen del Bus de Estado Global sin recalcular\n")
        f.write("- Se garantiza consistencia atómica en toda la cadena de cálculo\n\n")
        
        f.write("## Grafo de Dependencias\n\n")
        
        for pred_id, info in GRAFO_DEPENDENCIAS_V20.items():
            f.write(f"### {pred_id}\n\n")
            f.write(f"**Publica:**\n")
            for var in info["publica"]:
                f.write(f"- `{var}`\n")
            f.write(f"\n**Consume:**\n")
            if info["consume"]:
                for var in info["consume"]:
                    f.write(f"- `{var}`\n")
            else:
                f.write("- (ninguna - predicción base)\n")
            f.write("\n")
        
        f.write("## Análisis de Reutilización\n\n")
        
        # Contar cuántas veces se consume cada variable
        consumos: Dict[str, List[str]] = {}
        for pred_id, info in GRAFO_DEPENDENCIAS_V20.items():
            for var in info["consume"]:
                if var not in consumos:
                    consumos[var] = []
                consumos[var].append(pred_id)
        
        f.write("Variables más reutilizadas:\n\n")
        for var, consumidores in sorted(consumos.items(), key=lambda x: len(x[1]), reverse=True):
            f.write(f"- **`{var}`**: {len(consumidores)} consumidores\n")
            for cons in consumidores:
                f.write(f"  - {cons}\n")
        
        f.write("\n## Predicciones Base (No consumen de otras)\n\n")
        for pred_id, info in GRAFO_DEPENDENCIAS_V20.items():
            if not info["consume"]:
                f.write(f"- **{pred_id}**: Publica {', '.join([f'`{v}`' for v in info['publica']])}\n")
    
    logger.info(f"[MAPA] Dependencias exportadas a {ruta}")
    
    return (str(json_path), str(md_path))
