"""
[GUARDIAN] CAPA 22: CORTAFUEGOS DE CASCADA (Gatekeeper de Dependencias)

MISIÓN CRÍTICA:
Si un dato entra en modo "degradado/estimado", esta capa bloquea
automáticamente las alertas de alto impacto que dependan de ese dato.

FILOSOFÍA:
"Mejor silencio que falsedad basada en estimaciones"

CASOS DE USO:
- Sensor HR muerto → Bloquear alertas de "Riego Necesario"
- Sensor viento muerto → Bloquear alertas de "Helada Radiativa"
- Sensor presión muerto → Bloquear alertas de "Tormenta Inminente"

AUTOR: V47.4 SUMMUM - Sistema Autónomo
FECHA: 2026-02-05
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CortafuegosCascada:
    """
    Gatekeeper de dependencias: Bloquea alertas críticas si dependen
    de datos degradados.
    
    Previene decisiones erróneas basadas en estimaciones.
    """
    
    # Mapeo de alertas → sensores requeridos
    DEPENDENCIAS_ALERTAS = {
        "riego_necesario": {
            "sensores_criticos": ["hr", "temperatura", "lluvia_acumulada"],
            "sensores_opcionales": ["viento", "radiacion_solar"],
            "nivel_confianza_minimo": 90.0
        },
        
        "helada_radiativa": {
            "sensores_criticos": ["temperatura", "viento", "cobertura_nubes"],
            "sensores_opcionales": ["hr"],
            "nivel_confianza_minimo": 95.0
        },
        
        "llovizna_probable": {
            "sensores_criticos": ["hr", "temperatura", "presion"],
            "sensores_opcionales": ["viento"],
            "nivel_confianza_minimo": 85.0
        },
        
        "tormenta_inminente": {
            "sensores_criticos": ["presion", "viento", "hr"],
            "sensores_opcionales": ["temperatura"],
            "nivel_confianza_minimo": 95.0
        },
        
        "calima_probable": {
            "sensores_criticos": ["hr", "viento"],
            "sensores_opcionales": ["temperatura", "presion"],
            "nivel_confianza_minimo": 80.0
        },
        
        "estres_termico": {
            "sensores_criticos": ["temperatura", "hr", "viento", "radiacion_solar"],
            "sensores_opcionales": [],
            "nivel_confianza_minimo": 90.0
        },
        
        "evapotranspiracion_alta": {
            "sensores_criticos": ["temperatura", "hr", "viento", "radiacion_solar"],
            "sensores_opcionales": ["presion"],
            "nivel_confianza_minimo": 85.0
        }
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.estado_file = self.data_dir / "cortafuegos_cascada_estado.json"
        self.estado = self._cargar_estado()
        
        logger.info("[GUARDIAN] Cortafuegos de Cascada inicializado")
    
    def _cargar_estado(self) -> Dict:
        """Carga estado persistente."""
        if self.estado_file.exists():
            with open(self.estado_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "alertas_bloqueadas_total": 0,
            "alertas_permitidas_total": 0,
            "historico_bloqueos": [],
            "sensores_degradados_actual": [],
            "ultima_actualizacion": None
        }
    
    def _guardar_estado(self):
        """Guarda estado persistente."""
        self.estado["ultima_actualizacion"] = datetime.now().isoformat()
        with open(self.estado_file, 'w', encoding='utf-8') as f:
            json.dump(self.estado, f, indent=2, ensure_ascii=False)
    
    def registrar_sensor_degradado(self, sensor: str, razon: str):
        """
        Registra un sensor como degradado.
        
        Args:
            sensor: "hr", "temperatura", "viento", etc.
            razon: "sensor_muerto", "estimacion_historica", etc.
        """
        if sensor not in self.estado["sensores_degradados_actual"]:
            self.estado["sensores_degradados_actual"].append(sensor)
            
            logger.warning(
                f"[WARNING] Sensor {sensor} marcado como DEGRADADO: {razon}"
            )
            
            self._guardar_estado()
    
    def restaurar_sensor(self, sensor: str):
        """
        Marca un sensor como restaurado (ya no degradado).
        
        Args:
            sensor: "hr", "temperatura", etc.
        """
        if sensor in self.estado["sensores_degradados_actual"]:
            self.estado["sensores_degradados_actual"].remove(sensor)
            
            logger.info(
                f"[OK] Sensor {sensor} RESTAURADO"
            )
            
            self._guardar_estado()
    
    def validar_alerta(
        self,
        tipo_alerta: str,
        confianza_alerta: float
    ) -> Dict[str, any]:
        """
        Valida si una alerta puede emitirse o debe bloquearse.
        
        Args:
            tipo_alerta: "riego_necesario", "helada_radiativa", etc.
            confianza_alerta: Confianza del cálculo (0-100%)
        
        Returns:
            {
                "permitir": True|False,
                "razon": "...",
                "sensores_degradados_afectados": [...],
                "confianza_ajustada": float
            }
        """
        dependencias = self.DEPENDENCIAS_ALERTAS.get(tipo_alerta)
        
        if not dependencias:
            # Alerta no crítica o sin dependencias definidas
            return {
                "permitir": True,
                "razon": "Alerta sin dependencias críticas",
                "sensores_degradados_afectados": [],
                "confianza_ajustada": confianza_alerta
            }
        
        sensores_criticos = set(dependencias["sensores_criticos"])
        sensores_degradados_actuales = set(self.estado["sensores_degradados_actual"])
        
        # Verificar si algún sensor crítico está degradado
        sensores_criticos_degradados = sensores_criticos & sensores_degradados_actuales
        
        if sensores_criticos_degradados:
            # Sensor crítico degradado → BLOQUEAR ALERTA
            self.estado["alertas_bloqueadas_total"] += 1
            
            self._registrar_bloqueo(
                tipo_alerta,
                list(sensores_criticos_degradados),
                confianza_alerta
            )
            
            logger.warning(
                f"🚫 ALERTA BLOQUEADA: {tipo_alerta} - "
                f"Sensores críticos degradados: {list(sensores_criticos_degradados)}"
            )
            
            return {
                "permitir": False,
                "razon": f"Sensores críticos degradados: {', '.join(sensores_criticos_degradados)}",
                "sensores_degradados_afectados": list(sensores_criticos_degradados),
                "confianza_ajustada": 0.0
            }
        
        # Verificar sensores opcionales degradados
        sensores_opcionales = set(dependencias.get("sensores_opcionales", []))
        sensores_opcionales_degradados = sensores_opcionales & sensores_degradados_actuales
        
        if sensores_opcionales_degradados:
            # Sensor opcional degradado → REDUCIR CONFIANZA
            penalizacion = len(sensores_opcionales_degradados) * 15.0  # -15% por sensor
            confianza_ajustada = max(0.0, confianza_alerta - penalizacion)
            
            if confianza_ajustada < dependencias["nivel_confianza_minimo"]:
                # Confianza ajustada insuficiente → BLOQUEAR
                self.estado["alertas_bloqueadas_total"] += 1
                
                self._registrar_bloqueo(
                    tipo_alerta,
                    list(sensores_opcionales_degradados),
                    confianza_alerta
                )
                
                logger.warning(
                    f"🚫 ALERTA BLOQUEADA: {tipo_alerta} - "
                    f"Confianza ajustada {confianza_ajustada:.1f}% < {dependencias['nivel_confianza_minimo']}%"
                )
                
                return {
                    "permitir": False,
                    "razon": f"Confianza insuficiente tras degradación ({confianza_ajustada:.1f}%)",
                    "sensores_degradados_afectados": list(sensores_opcionales_degradados),
                    "confianza_ajustada": confianza_ajustada
                }
            
            # Confianza ajustada suficiente → PERMITIR con aviso
            self.estado["alertas_permitidas_total"] += 1
            self._guardar_estado()
            
            logger.info(
                f"[OK] ALERTA PERMITIDA: {tipo_alerta} - "
                f"Confianza ajustada: {confianza_ajustada:.1f}% "
                f"(sensores opcionales degradados: {list(sensores_opcionales_degradados)})"
            )
            
            return {
                "permitir": True,
                "razon": "Confianza suficiente pese a sensores opcionales degradados",
                "sensores_degradados_afectados": list(sensores_opcionales_degradados),
                "confianza_ajustada": confianza_ajustada
            }
        
        # Todos los sensores operativos → PERMITIR
        self.estado["alertas_permitidas_total"] += 1
        self._guardar_estado()
        
        return {
            "permitir": True,
            "razon": "Todos los sensores operativos",
            "sensores_degradados_afectados": [],
            "confianza_ajustada": confianza_alerta
        }
    
    def _registrar_bloqueo(
        self,
        tipo_alerta: str,
        sensores_degradados: List[str],
        confianza_original: float
    ):
        """Registra bloqueo en histórico."""
        self.estado["historico_bloqueos"].append({
            "timestamp": datetime.now().isoformat(),
            "tipo_alerta": tipo_alerta,
            "sensores_degradados": sensores_degradados,
            "confianza_original": confianza_original
        })
        
        # Mantener últimos 500 bloqueos
        self.estado["historico_bloqueos"] = self.estado["historico_bloqueos"][-500:]
        
        self._guardar_estado()
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas del cortafuegos.
        
        Returns:
            {
                "alertas_bloqueadas": 127,
                "alertas_permitidas": 8234,
                "tasa_bloqueo": 1.5,
                "sensores_degradados_actual": ["hr", "viento"],
                "bloqueos_ultimas_24h": 5
            }
        """
        total_bloqueadas = self.estado["alertas_bloqueadas_total"]
        total_permitidas = self.estado["alertas_permitidas_total"]
        total = total_bloqueadas + total_permitidas
        
        tasa_bloqueo = (total_bloqueadas / total * 100) if total > 0 else 0.0
        
        # Bloqueos últimas 24h
        from datetime import timedelta
        fecha_limite = datetime.now() - timedelta(hours=24)
        
        bloqueos_24h = sum(
            1 for bloqueo in self.estado["historico_bloqueos"]
            if datetime.fromisoformat(bloqueo["timestamp"]) > fecha_limite
        )
        
        return {
            "alertas_bloqueadas": total_bloqueadas,
            "alertas_permitidas": total_permitidas,
            "tasa_bloqueo": round(tasa_bloqueo, 2),
            "sensores_degradados_actual": self.estado["sensores_degradados_actual"],
            "bloqueos_ultimas_24h": bloqueos_24h
        }


# ============================================================================
# INTEGRACIÓN CON SISTEMA DE ALERTAS
# ============================================================================

def integrar_cortafuegos_en_alertas():
    """
    Ejemplo de integración en sistema de alertas.
    
    ```python
    # En sistema de alertas (ej: core/alerts/alert_manager.py)
    from core.monitoring.cortafuegos_cascada import CortafuegosCascada
    
    cortafuegos = CortafuegosCascada()
    
    def emitir_alerta(tipo, confianza, mensaje):
        '''Emite alerta solo si cortafuegos lo permite'''
        
        # VALIDAR CON CORTAFUEGOS
        validacion = cortafuegos.validar_alerta(tipo, confianza)
        
        if not validacion["permitir"]:
            logger.warning(
                f"🚫 Alerta {tipo} BLOQUEADA por cortafuegos: "
                f"{validacion['razon']}"
            )
            return None
        
        # Usar confianza ajustada
        confianza_final = validacion["confianza_ajustada"]
        
        # Emitir alerta
        alerta = {
            "tipo": tipo,
            "mensaje": mensaje,
            "confianza": confianza_final,
            "timestamp": datetime.now().isoformat()
        }
        
        if validacion["sensores_degradados_afectados"]:
            alerta["aviso"] = (
                f"Alerta basada en datos parciales "
                f"(sensores degradados: {', '.join(validacion['sensores_degradados_afectados'])})"
            )
        
        return alerta
    ```
    """
    pass


if __name__ == "__main__":
    # Test básico
    logging.basicConfig(level=logging.INFO)
    
    cortafuegos = CortafuegosCascada()
    
    # Test 1: Todos los sensores operativos
    validacion = cortafuegos.validar_alerta(
        "riego_necesario",
        confianza_alerta=92.0
    )
    print(f"\n[OK] Test 1 - Todos operativos:")
    print(f"   Permitir: {validacion['permitir']}")
    print(f"   Razón: {validacion['razon']}")
    print(f"   Confianza: {validacion['confianza_ajustada']:.1f}%")
    
    # Test 2: Sensor crítico degradado
    cortafuegos.registrar_sensor_degradado("hr", "sensor_muerto")
    
    validacion = cortafuegos.validar_alerta(
        "riego_necesario",
        confianza_alerta=92.0
    )
    print(f"\n🚫 Test 2 - Sensor HR degradado:")
    print(f"   Permitir: {validacion['permitir']}")
    print(f"   Razón: {validacion['razon']}")
    print(f"   Sensores afectados: {validacion['sensores_degradados_afectados']}")
    
    # Test 3: Sensor opcional degradado
    cortafuegos.restaurar_sensor("hr")
    cortafuegos.registrar_sensor_degradado("viento", "estimacion_historica")
    
    validacion = cortafuegos.validar_alerta(
        "riego_necesario",
        confianza_alerta=92.0
    )
    print(f"\n[WARNING] Test 3 - Sensor opcional degradado:")
    print(f"   Permitir: {validacion['permitir']}")
    print(f"   Confianza original: 92.0%")
    print(f"   Confianza ajustada: {validacion['confianza_ajustada']:.1f}%")
    
    # Estadísticas
    stats = cortafuegos.obtener_estadisticas()
    print(f"\n[STATS] Estadísticas:")
    print(f"   {json.dumps(stats, indent=2)}")
