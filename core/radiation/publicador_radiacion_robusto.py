"""
═══════════════════════════════════════════════════════════════════════════════
PUBLICADOR DE RADIACIÓN CON JERARQUÍA DE CONFIANZA
═══════════════════════════════════════════════════════════════════════════════

Reemplaza la publicación "plana" de radiación con una publicación inteligente:
- Cada estado radiativo publica: valor, confianza, contexto, fuente
- Los índices consumen con jerarquía (algunos estados son prioritarios)
- Las anomalías no sobreescriben valores, solo degradan confianza

Estructura de estados radiativos:

NIVEL 1: Estados fundamentales (calculados siempre)
  - GHI (horizontal)
  - DNI (normal directo)
  - DHI (difusa horizontal)
  - Rn_noche (radiación neta nocturna)

NIVEL 2: Estados derivados (transposición inclinada)
  - POA_humano (plano ~60° variable)
  - POA_suelo
  - POA_vertical_sur / norte

NIVEL 3: Estados de diagnóstico (flags)
  - calima_presente
  - ensuciamiento_factor
  - nubosidad_fina

Cada uno publica con confianza [0, 1] que determina su peso en fusiones.

Autor: Sistema Robusto MeteoSerV3
Fecha: Feb 10, 2026
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EstadoRadiativo:
    """Un estado radiativo con metadatos de confianza."""
    
    clave: str  # Nombre del estado (ej: 'ghi', 'dni', 'poa_humano')
    valor: float  # Valor numérico
    unidad: str  # Unidad (ej: 'W/m²')
    confianza: float  # [0.0 (sin confianza), 1.0 (confianza máxima)]
    fuente: str  # 'modelo', 'sensor', 'hibrido'
    contexto_limpio: bool  # ¿El contexto radiativo era limpio?
    timestamp: datetime
    
    # Metadatos
    formula: str = ""  # Qué fórmula se usó
    anotaciones: Dict[str, Any] = None  # Diagnosticos adicionales
    
    def __post_init__(self):
        if self.anotaciones is None:
            self.anotaciones = {}
        
        # Acotar confianza
        self.confianza = max(0.0, min(1.0, self.confianza))
    
    def es_confiable(self, umbral_minimo: float = 0.5) -> bool:
        """¿Esta estado supera el umbral de confianza?"""
        return self.confianza >= umbral_minimo


class PublicadorRadiacionRobusto:
    """
    Publicia estados radiativos con jerarquía de confianza.
    
    Interfaz con el bus global (BusEstadoGlobal).
    """
    
    # Definición de jerarquía de confianza por índice
    JERARQUIA_CONFIANZA = {
        "wbgt": {
            "prioritarios": ["poa_humano", "dni", "dhi"],
            "secundarios": ["ghi"],
            "no_usar": []
        },
        "et0": {
            "prioritarios": ["dni", "dhi", "poa_suelo"],
            "secundarios": ["ghi"],
            "no_usar": []
        },
        "t_min": {
            "prioritarios": ["rn_noche", "lw_down"],
            "secundarios": ["temperatura_c"],
            "no_usar": ["ghi"]  # GHI es irrelevante de noche
        },
        "default": {
            "prioritarios": ["ghi", "dni", "dhi"],
            "secundarios": [],
            "no_usar": []
        }
    }
    
    def __init__(self, bus_estado_global=None):
        """
        Inicializa el publicador.
        
        Args:
            bus_estado_global: Instancia de BusEstadoGlobal (inyectable)
        """
        self.bus = bus_estado_global
        self._historial_estados: Dict[str, EstadoRadiativo] = {}
    
    def publicar_estado(self, 
                        estado: EstadoRadiativo,
                        descripcion: str = "") -> None:
        """
        Publica un estado radiativo en el bus.
        
        Args:
            estado: EstadoRadiativo a publicar
            descripcion: Descripción legible para logs
        """
        
        # Validar
        if estado.confianza < 0 or estado.confianza > 1:
            logger.warning(
                f"[RADIACION] Confianza inválida para {estado.clave}: {estado.confianza}"
            )
            return
        
        # Registrar en historial
        self._historial_estados[estado.clave] = estado
        
        # Log
        nivel_log = "info" if estado.confianza >= 0.7 else "warning"
        msg = (
            f"[RADIACION] Publicado '{estado.clave}' = {estado.valor:.1f} {estado.unidad} "
            f"(confianza={estado.confianza:.2f}, fuente={estado.fuente}, "
            f"contexto_limpio={estado.contexto_limpio})"
        )
        
        if descripcion:
            msg += f" - {descripcion}"
        
        if nivel_log == "info":
            logger.info(msg)
        else:
            logger.warning(msg)
        
        # Publicar en bus si está disponible
        if self.bus is not None:
            metadatos = {
                "confianza": estado.confianza,
                "fuente": estado.fuente,
                "contexto_limpio": estado.contexto_limpio,
                "formula": estado.formula,
                "anotaciones": estado.anotaciones
            }
            try:
                self.bus.publicar(
                    clave=estado.clave,
                    valor=estado.valor,
                    fuente="radiacion_hibrida",
                    metadatos=metadatos
                )
            except Exception as e:
                logger.error(f"Error publicando en bus: {e}")
    
    def consumir_para_indice(self, 
                             indice_nombre: str,
                             estado_clave: str) -> Optional[float]:
        """
        Consume un estado radiativo respetando jerarquía de confianza.
        
        Args:
            indice_nombre: Nombre del índice (ej: 'wbgt', 'et0')
            estado_clave: Clave del estado a consumir
        
        Returns:
            Valor del estado si existe y es confiable, None en otro caso
        """
        
        # Obtener jerarquía para este índice
        jerarquia = self.JERARQUIA_CONFIANZA.get(
            indice_nombre,
            self.JERARQUIA_CONFIANZA["default"]
        )
        
        # Verificar si este estado está en la lista de "no usar"
        if estado_clave in jerarquia["no_usar"]:
            logger.debug(
                f"[RADIACION] {indice_nombre} no debe usar {estado_clave}"
            )
            return None
        
        # Obtener estado
        estado = self._historial_estados.get(estado_clave)
        
        if estado is None:
            logger.debug(
                f"[RADIACION] Estado {estado_clave} no disponible"
            )
            return None
        
        # Verificar confianza mínima
        # Prioritarios: requieren >= 0.6
        # Secundarios: requieren >= 0.5
        if estado_clave in jerarquia["prioritarios"]:
            umbral = 0.6
        else:
            umbral = 0.5
        
        if not estado.es_confiable(umbral):
            logger.debug(
                f"[RADIACION] Estado {estado_clave} bajo confianza "
                f"({estado.confianza:.2f} < {umbral})"
            )
            return None
        
        logger.debug(
            f"[RADIACION] {indice_nombre} consumió {estado_clave} "
            f"(valor={estado.valor:.1f}, confianza={estado.confianza:.2f})"
        )
        
        return estado.valor
    
    def obtener_confianza(self, estado_clave: str) -> Optional[float]:
        """Retorna la confianza de un estado."""
        estado = self._historial_estados.get(estado_clave)
        return estado.confianza if estado else None
    
    def obtener_todos_estados(self) -> Dict[str, EstadoRadiativo]:
        """Retorna todos los estados activos."""
        return self._historial_estados.copy()
    
    def listar_estados_por_confianza(self) -> list:
        """Retorna lista de estados ordenados por confianza (mayor primero)."""
        estados = sorted(
            self._historial_estados.values(),
            key=lambda e: e.confianza,
            reverse=True
        )
        
        resultado = []
        for estado in estados:
            resultado.append({
                "clave": estado.clave,
                "valor": estado.valor,
                "unidad": estado.unidad,
                "confianza": f"{estado.confianza:.2f}",
                "fuente": estado.fuente,
                "contexto_limpio": estado.contexto_limpio
            })
        
        return resultado


class ValidadorCruzadoRadiacion:
    """
    Valida radiación y temperatura de forma cruzada.
    
    Evita que un sensor defectuoso "engañe" al sistema.
    
    Regla: radiación alta + temperatura no responde → dudar radiación
           radiación baja + temperatura sube → dudar temperatura
    """
    
    def __init__(self):
        """Inicializa el validador."""
        self._historial_balance: list = []
    
    def validar(self,
                ghi_w_m2: float,
                temperatura_c: float,
                temperatura_anterior_c: float,
                minutos_transcurridos: float = 1.0) -> Dict[str, bool]:
        """
        Valida balance entre radiación y temperatura.
        
        Args:
            ghi_w_m2: Radiación global horizontal
            temperatura_c: Temperatura actual
            temperatura_anterior_c: Temperatura hace N minutos
            minutos_transcurridos: Tiempo para calcular derivada
        
        Returns:
            Dict con flags de alerta:
            {
                "radiacion_sospechosa": bool,
                "temperatura_sospechosa": bool,
                "balance_ok": bool
            }
        """
        resultado = {
            "radiacion_sospechosa": False,
            "temperatura_sospechosa": False,
            "balance_ok": True
        }
        
        if minutos_transcurridos <= 0:
            return resultado
        
        # Calcular derivada de temperatura
        derivada_temp = (temperatura_c - temperatura_anterior_c) / minutos_transcurridos
        
        # Regla 1: Radiación alta pero T no sube
        if ghi_w_m2 > 600 and derivada_temp < 0.1:  # Radiación fuerte, T estancada
            resultado["radiacion_sospechosa"] = True
            resultado["balance_ok"] = False
            logger.warning(
                f"[VALIDACIÓN] Radiación alta (GHI={ghi_w_m2:.0f}) "
                f"pero temperatura no sube (dT/dt={derivada_temp:.2f}°C/min)"
            )
        
        # Regla 2: Radiación baja pero T sube mucho
        if ghi_w_m2 < 200 and derivada_temp > 2.0:  # Radiación débil, T sube mucho
            resultado["temperatura_sospechosa"] = True
            resultado["balance_ok"] = False
            logger.warning(
                f"[VALIDACIÓN] Temperatura sube rápido (dT/dt={derivada_temp:.2f}°C/min) "
                f"pero radiación baja (GHI={ghi_w_m2:.0f})"
            )
        
        return resultado
