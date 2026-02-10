"""
BUS INTELIGENTE CON CAPAS DE INFORMACIÓN
=========================================
Reemplaza "saturación total" con captura estructurada por niveles.
- Nivel 1 (CORE): Datos validados, confianza > 0.95
- Nivel 2 (INTERMEDIATE): Cálculos intermedios, pre-índices
- Nivel 3 (DEBUG): Variables temporales (solo si debug_mode)
- Nivel 4 (TIMESERIES): Histórico de variables clave (últimas N muestras)

Ventaja: LA INFORMACIÓN CONTROLADA Y EXPLORABLE, no ruido.
"""

from typing import Dict, Any, List, Optional, Union
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import deque, defaultdict
import threading
import json
from pathlib import Path


@dataclass
class MetadatosLinaje:
    """Genealogía completa de cada variable en el Bus"""
    variable: str
    valor: Any
    tipo: str  # core, intermediate, debug, timeseries
    origen: str  # archivo.funcion
    timestamp: datetime
    confianza: float = 1.0  # 0-1, nivel de validación
    precondiciones: List[str] = field(default_factory=list)  # Qué debe estar OK
    consumidores: List[str] = field(default_factory=list)  # Quién usa esto
    unidad: str = ""
    rango_esperado: tuple = field(default_factory=lambda: (None, None))
    notas: str = ""
    
    def a_dict(self) -> Dict:
        """Serializar con datetime como ISO"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    def a_json(self) -> str:
        return json.dumps(self.a_dict(), indent=2)


class CapaInformacion:
    """Contenedor para cada capa del Bus"""
    
    def __init__(self, nombre: str, max_items: int = 5000):
        self.nombre = nombre
        self.max_items = max_items
        self.datos: Dict[str, MetadatosLinaje] = {}
        self.lock = threading.RLock()
        self.contador_inserciones = 0
        self.contador_actualizaciones = 0
    
    def agregar_o_actualizar(self, clave: str, metadatos: MetadatosLinaje) -> None:
        """Inserta o actualiza con conteo de operaciones"""
        with self.lock:
            if clave in self.datos:
                self.contador_actualizaciones += 1
            else:
                self.contador_inserciones += 1
            
            # Limpieza si se excede max_items
            if len(self.datos) >= self.max_items:
                # Elimina entrada más antigua
                mas_vieja = min(
                    self.datos.values(),
                    key=lambda x: x.timestamp
                )
                del self.datos[mas_vieja.variable]
            
            self.datos[clave] = metadatos
    
    def obtener(self, clave: str, default: Any = None) -> Optional[MetadatosLinaje]:
        with self.lock:
            return self.datos.get(clave, default)
    
    def obtener_valor(self, clave: str, default: Any = None) -> Any:
        """Obtiene solo el valor (no los metadatos)"""
        with self.lock:
            meta = self.datos.get(clave)
            return meta.valor if meta else default
    
    def listar(self) -> List[MetadatosLinaje]:
        with self.lock:
            return list(self.datos.values())
    
    def stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "capa": self.nombre,
                "items": len(self.datos),
                "inserciones": self.contador_inserciones,
                "actualizaciones": self.contador_actualizaciones,
                "ultimos_timestamps": [
                    d.timestamp.isoformat()
                    for d in sorted(
                        self.datos.values(),
                        key=lambda x: x.timestamp,
                        reverse=True
                    )[:5]
                ]
            }


class TimeseriesVariable:
    """Contenedor para histórico de una variable específica"""
    
    def __init__(self, variable: str, max_muestras: int = 120):
        self.variable = variable
        self.max_muestras = max_muestras
        self.valores: deque = deque(maxlen=max_muestras)
        self.lock = threading.RLock()
    
    def agregar(self, valor: Any, timestamp: datetime = None) -> None:
        if timestamp is None:
            timestamp = datetime.now()
        with self.lock:
            self.valores.append((valor, timestamp))
    
    def obtener_ultimo(self) -> Optional[tuple]:
        with self.lock:
            return self.valores[-1] if self.valores else None
    
    def obtener_rango(self, minutos: int = 60) -> List[tuple]:
        """Obtiene valores de los últimos N minutos"""
        with self.lock:
            cutoff = datetime.now() - timedelta(minutes=minutos)
            return [
                (v, ts) for v, ts in self.valores
                if ts >= cutoff
            ]
    
    def estadisticas(self) -> Dict[str, Any]:
        """Genera estadísticas del histórico"""
        with self.lock:
            if not self.valores:
                return {"variable": self.variable, "muestras": 0}
            
            valores_numericos = [
                v for v, _ in self.valores
                if isinstance(v, (int, float))
            ]
            
            if not valores_numericos:
                return {"variable": self.variable, "muestras": len(self.valores)}
            
            return {
                "variable": self.variable,
                "muestras": len(self.valores),
                "min": min(valores_numericos),
                "max": max(valores_numericos),
                "promedio": sum(valores_numericos) / len(valores_numericos),
                "desvio": (
                    (sum((x - sum(valores_numericos)/len(valores_numericos))**2 for x in valores_numericos) / len(valores_numericos))**0.5
                    if len(valores_numericos) > 1 else 0
                )
            }


class BusCapasInformacion:
    """Bus Inteligente con 4 capas jerárquicas"""
    
    def __init__(self):
        self.capa_core = CapaInformacion("CORE", max_items=2000)
        self.capa_intermediate = CapaInformacion("INTERMEDIATE", max_items=3000)
        self.capa_debug = CapaInformacion("DEBUG", max_items=5000)
        self.capa_timeseries: Dict[str, TimeseriesVariable] = {}
        
        self.debug_mode = False
        self.lock = threading.RLock()
        self.registro_queries = deque(maxlen=1000)
        self.bytes_por_segundo = 0
        self.ultimo_calculo_throughput = datetime.now()
    
    def publicar(self, 
                 variable: str,
                 valor: Any,
                 nivel: str = "CORE",
                 origen: str = "unknown.unknown",
                 confianza: float = 1.0,
                 precondiciones: List[str] = None,
                 consumidores: List[str] = None,
                 unidad: str = "",
                 rango_esperado: tuple = None,
                 notas: str = "") -> None:
        """
        Publica una variable a la capa correspondiente
        
        Args:
            variable: Nombre único (archivo.funcion.variable recomendado)
            valor: Valor a publicar
            nivel: "CORE", "INTERMEDIATE", "DEBUG", o "TIMESERIES"
            origen: "archivo.funcion"
            confianza: 0-1, qué tan confiable es
            precondiciones: Lista de variables requeridas para validez
            consumidores: Quién usa esta variable
            unidad: Unidad de medida si aplica
            rango_esperado: (min, max) esperado
            notas: Cualquier anotación útil
        """
        metadatos = MetadatosLinaje(
            variable=variable,
            valor=valor,
            tipo=nivel,
            origen=origen,
            timestamp=datetime.now(),
            confianza=confianza,
            precondiciones=precondiciones or [],
            consumidores=consumidores or [],
            unidad=unidad,
            rango_esperado=rango_esperado,
            notas=notas
        )
        
        with self.lock:
            if nivel == "CORE":
                self.capa_core.agregar_o_actualizar(variable, metadatos)
            elif nivel == "INTERMEDIATE":
                self.capa_intermediate.agregar_o_actualizar(variable, metadatos)
            elif nivel == "DEBUG":
                if self.debug_mode:
                    self.capa_debug.agregar_o_actualizar(variable, metadatos)
            elif nivel == "TIMESERIES":
                if variable not in self.capa_timeseries:
                    self.capa_timeseries[variable] = TimeseriesVariable(variable)
                self.capa_timeseries[variable].agregar(valor, metadatos.timestamp)
            
            # Actualizar throughput (bytes por segundo estimado)
            self._actualizar_throughput(metadatos)
    
    def _actualizar_throughput(self, metadatos: MetadatosLinaje) -> None:
        """Estima MB/s de flujo de datos"""
        ahora = datetime.now()
        tamaño_aproximado = len(str(metadatos.valor)) + len(metadatos.variable)
        
        delta_segundos = (ahora - self.ultimo_calculo_throughput).total_seconds()
        if delta_segundos > 1.0:
            self.bytes_por_segundo = tamaño_aproximado / delta_segundos if delta_segundos > 0 else 0
            self.ultimo_calculo_throughput = ahora
    
    def query(self, filtro: str, **kwargs) -> List[MetadatosLinaje]:
        """
        Query inteligente de datos
        
        Ejemplos:
            bus.query("core:*")  # Todo de CORE
            bus.query("intermediate:physics.*")  # Physics en INTERMEDIATE
            bus.query("confianza>0.95")  # Alta confianza
            bus.query("origen:environm*")  # De environmental
            bus.query("timeseries:temperatura,ultimos_60m")  # Histórico
        """
        with self.lock:
            resultados = []
            
            # Parse del filtro
            if filtro.startswith("core:"):
                patron = filtro.split(":")[1]
                resultados = self._filtrar_por_patron(
                    self.capa_core.listar(), patron
                )
            elif filtro.startswith("intermediate:"):
                patron = filtro.split(":")[1]
                resultados = self._filtrar_por_patron(
                    self.capa_intermediate.listar(), patron
                )
            elif filtro.startswith("debug:"):
                patron = filtro.split(":")[1]
                resultados = self._filtrar_por_patron(
                    self.capa_debug.listar(), patron
                )
            elif filtro.startswith("confianza>"):
                umbral = float(filtro.split(">")[1])
                todas = (
                    self.capa_core.listar() +
                    self.capa_intermediate.listar() +
                    self.capa_debug.listar()
                )
                resultados = [m for m in todas if m.confianza > umbral]
            elif filtro.startswith("origen:"):
                patron = filtro.split(":")[1]
                todas = (
                    self.capa_core.listar() +
                    self.capa_intermediate.listar() +
                    self.capa_debug.listar()
                )
                resultados = self._filtrar_por_patron(todas, patron, campo="origen")
            else:
                resultados = (
                    self.capa_core.listar() +
                    self.capa_intermediate.listar() +
                    self.capa_debug.listar()
                )
            
            self.registro_queries.append({
                "filtro": filtro,
                "timestamp": datetime.now().isoformat(),
                "resultados": len(resultados)
            })
            
            return resultados
    
    def _filtrar_por_patron(self, items: List[MetadatosLinaje], 
                           patron: str, campo: str = "variable") -> List[MetadatosLinaje]:
        """Filtra por patrón wildcard (*, ? soportados)"""
        import fnmatch
        patron = patron.replace("*", "*")
        return [
            item for item in items
            if fnmatch.fnmatch(getattr(item, campo), patron)
        ]
    
    def obtener_dashboard(self) -> Dict[str, Any]:
        """Dashboard completo del Bus"""
        with self.lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "debug_mode": self.debug_mode,
                "throughput_bytes_seg": round(self.bytes_por_segundo, 2),
                "capas": {
                    "CORE": self.capa_core.stats(),
                    "INTERMEDIATE": self.capa_intermediate.stats(),
                    "DEBUG": self.capa_debug.stats(),
                    "TIMESERIES": {
                        "variables": len(self.capa_timeseries),
                        "principales": [
                            self.capa_timeseries[v].estadisticas()
                            for v in sorted(self.capa_timeseries.keys())[:10]
                        ]
                    }
                },
                "ultimas_queries": list(self.registro_queries)[-10:]
            }
    
    def habilitar_debug(self, enabled: bool = True) -> None:
        """Habilita captura DEBUG (capa 3)"""
        with self.lock:
            self.debug_mode = enabled
    
    def exportar_a_json(self, archivo: str) -> None:
        """Exporta todo el estado del Bus a JSON"""
        with self.lock:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "capas": {
                    "CORE": [m.a_dict() for m in self.capa_core.listar()],
                    "INTERMEDIATE": [m.a_dict() for m in self.capa_intermediate.listar()],
                    "DEBUG": [m.a_dict() for m in self.capa_debug.listar()],
                    "TIMESERIES": {
                        var: {
                            "valores": [
                                (v, ts.isoformat())
                                for v, ts in ts_var.valores
                            ],
                            "stats": ts_var.estadisticas()
                        }
                        for var, ts_var in self.capa_timeseries.items()
                    }
                }
            }
            
            Path(archivo).write_text(json.dumps(snapshot, indent=2))


# Singleton global
bus_capas_globales = BusCapasInformacion()

# Bus V3 (por defecto)
try:
    from core.bus.bus_v3_adapter import BusV3Adapter
    bus_v3_globales = BusV3Adapter()
except Exception:
    bus_v3_globales = None


def _usar_bus_v3() -> bool:
    """Determina si se usa Bus V3 por defecto."""
    valor = os.getenv("METEOSER_BUS_V3", "1").strip().lower()
    return valor not in {"0", "false", "no"}


def obtener_bus() -> Any:
    """Acceso al Bus global (V3 por defecto, legacy opcional)."""
    if _usar_bus_v3() and bus_v3_globales is not None:
        return bus_v3_globales
    return bus_capas_globales
