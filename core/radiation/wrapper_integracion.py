"""
═══════════════════════════════════════════════════════════════════════════════
WRAPPER DE INTEGRACIÓN - Radiación Robusta V51 ↔ Sistema Actual
═══════════════════════════════════════════════════════════════════════════════

Esta es la "zona de contacto" entre la nueva arquitectura robusta y el sistema existente.

PROPÓSITO:
- Permitir activar/desactivar la nueva arquitectura sin código changes
- Mantener compatibilidad con radiacion_hibrida.py existente
- Validar que el nuevo sistema no rompe nada
- Permitir "dry-run" en paralelo

MODO DE USO:

1. SIN NUEVA ARQUITECTURA (fallback a radiacion_hibrida actual):
   wrapper = WrapperRadiacionRobusta(enabled=False)
   resultado = wrapper.processar(sensores, rest2_output)

2. CON NUEVA ARQUITECTURA (en paralelo):
   wrapper = WrapperRadiacionRobusta(enabled=True)
   resultado_robusto = wrapper.processar(sensores, rest2_output)
   resultado_antiguo = wrapper.processar_fallback(sensores, rest2_output)

3. COMPARATIVA:
   diferencias = wrapper.comparar_resultados()

Autor: Sistema Robusto V51.0
Fecha: 10 de febrero de 2026
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class WrapperRadiacionRobusta:
    """
    Wrapper que adapta radiación robusta al sistema existente.
    
    Permite modo híbrido: usar nueva arquitectura en paralelo sin romper nada.
    """
    
    def __init__(self, enabled: bool = True, modo_comparativa: bool = False):
        """
        Inicializa el wrapper.
        
        Args:
            enabled: ¿Activar nueva arquitectura?
            modo_comparativa: ¿Comparar resultados antiguo vs nuevo?
        """
        self.enabled = enabled
        self.modo_comparativa = modo_comparativa
        
        # Inicializar componentes de nueva arquitectura (si está habilitada)
        if self.enabled:
            try:
                from core.radiation.clasificador_contexto_radiativo import ClasificadorContextoRadiativo
                from core.radiation.estrategias_aprendizaje import EstiloAprendizajeCorrectivo, EstiloAprendizajeDiagnostico
                from core.radiation.publicador_radiacion_robusto import PublicadorRadiacionRobusto, ValidadorCruzadoRadiacion
                from core.radiation.controlador_radiacion_robusto import ControladorRadiacionRobusto
                
                self.clasificador = ClasificadorContextoRadiativo()
                self.aprendizaje_correctivo = EstiloAprendizajeCorrectivo()
                self.aprendizaje_diagnostico = EstiloAprendizajeDiagnostico()
                self.publicador = PublicadorRadiacionRobusto(bus_estado_global=None)
                self.validador_cruzado = ValidadorCruzadoRadiacion()
                
                self.controlador = ControladorRadiacionRobusto(
                    clasificador=self.clasificador,
                    aprendizaje_correctivo=self.aprendizaje_correctivo,
                    aprendizaje_diagnostico=self.aprendizaje_diagnostico,
                    publicador=self.publicador,
                    validador_cruzado=self.validador_cruzado
                )
                
                logger.info("[WRAPPER] Nueva arquitectura radiativa robusta V51 ACTIVADA")
            except ImportError as e:
                logger.error(f"[WRAPPER] Error importando módulos robustos: {e}")
                self.enabled = False
        
        # Historial para comparativas
        self._historial_comparativas = []
    
    def procesar(self,
                 elevacion_solar_deg: float,
                 ghi_w_m2_medida: Optional[float],
                 presion_hpa: float,
                 humedad_rel: float,
                 temperatura_c: float,
                 velocidad_viento_ms: float,
                 precipitacion_mm: float,
                 visibilidad_km: Optional[float],
                 rest2_output: Dict,
                 sensor_real_confiable: bool = True) -> Dict:
        """
        Procesa radiación usando arquitectura robusta (si habilitada).
        
        Args:
            elevacion_solar_deg: Ángulo solar
            ghi_w_m2_medida: GHI medida (si disponible)
            presion_hpa: Presión
            humedad_rel: Humedad relativa
            temperatura_c: Temperatura
            velocidad_viento_ms: Velocidad viento
            precipitacion_mm: Precipitación
            visibilidad_km: Visibilidad
            rest2_output: Dict con salida de REST2 {ghi, dni, dhi, clear_sky_index}
            sensor_real_confiable: ¿Sensor real confiable?
        
        Returns:
            Dict con resultado:
            {
                "usada_nueva_arquitectura": bool,
                "ghi": float,
                "dni": float,
                "dhi": float,
                "confianza": float,
                "contexto": Dict,
                "advertencias": List[str]
            }
        """
        
        resultado = {
            "usada_nueva_arquitectura": False,
            "ghi": rest2_output.get("ghi", 0),
            "dni": rest2_output.get("dni", 0),
            "dhi": rest2_output.get("dhi", 0),
            "confianza": 1.0,
            "contexto": {},
            "advertencias": [],
            "detalles_debug": {}
        }
        
        if not self.enabled:
            logger.debug("[WRAPPER] Arquitectura robusta deshabilitada, usando REST2 directo")
            return resultado
        
        try:
            # Procesar con nueva arquitectura
            resultado_robusto = self.controlador.procesar_ciclo_radiacion(
                elevacion_solar_deg=elevacion_solar_deg,
                ghi_w_m2_medida=ghi_w_m2_medida or 0,
                presion_hpa=presion_hpa,
                humedad_rel=humedad_rel,
                temperatura_c=temperatura_c,
                velocidad_viento_ms=velocidad_viento_ms,
                precipitacion_mm=precipitacion_mm,
                visibilidad_km=visibilidad_km,
                ghi_modelo_rest2=rest2_output.get("ghi", 0),
                dni_modelo_rest2=rest2_output.get("dni", 0),
                dhi_modelo_rest2=rest2_output.get("dhi", 0),
                timestamp=datetime.now(),
                sensor_real_confiable=sensor_real_confiable
            )
            
            # Mapear resultado robusto a formato de salida
            resultado["usada_nueva_arquitectura"] = True
            resultado["ghi"] = resultado_robusto["ghi_final"]
            resultado["dni"] = resultado_robusto["dni_final"]
            resultado["dhi"] = resultado_robusto["dhi_final"]
            resultado["confianza"] = resultado_robusto["confianza"]
            resultado["advertencias"] = resultado_robusto.get("advertencias", [])
            resultado["detalles_debug"] = {
                "contexto_bloqueado": resultado_robusto["contexto"].motivos_bloqueo if resultado_robusto["contexto"] else [],
                "estados_publicados": resultado_robusto.get("estados_publicados", [])
            }
            
            if resultado_robusto["contexto"]:
                resultado["contexto"] = {
                    "es_limpio": resultado_robusto["contexto"].es_valido_para_aprendizaje,
                    "confianza": resultado_robusto["contexto"].confianza_general,
                    "motivos_bloqueo": resultado_robusto["contexto"].motivos_bloqueo,
                    "motivos_degradacion": resultado_robusto["contexto"].motivos_degradacion
                }
            
            # COMPARATIVA (si está habilitada)
            if self.modo_comparativa:
                self._registrar_comparativa(
                    rest2_output=rest2_output,
                    resultado_robusto=resultado,
                    elevacion=elevacion_solar_deg
                )
        
        except Exception as e:
            logger.error(f"[WRAPPER] Error in arquitectura robusta: {e}")
            logger.warning("[WRAPPER] Fallback a REST2 directo")
            resultado["usada_nueva_arquitectura"] = False
            resultado["advertencias"].append(f"FALLBACK: {str(e)}")
        
        return resultado
    
    def procesar_fallback(self,
                         elevacion_solar_deg: float,
                         ghi_w_m2_medida: Optional[float],
                         presion_hpa: float,
                         humedad_rel: float,
                         temperatura_c: float,
                         velocidad_viento_ms: float,
                         precipitacion_mm: float,
                         visibilidad_km: Optional[float],
                         rest2_output: Dict) -> Dict:
        """
        Procesa usando arquitectura antigua (para comparativa).
        Retorna resultado de REST2 directo sin cambios.
        """
        return {
            "usada_nueva_arquitectura": False,
            "ghi": rest2_output.get("ghi", 0),
            "dni": rest2_output.get("dni", 0),
            "dhi": rest2_output.get("dhi", 0),
            "confianza": 1.0,
            "contexto": {},
            "advertencias": []
        }
    
    def _registrar_comparativa(self,
                               rest2_output: Dict,
                               resultado_robusto: Dict,
                               elevacion: float) -> None:
        """Registra comparativa para posterior análisis."""
        
        diferencia_ghi = abs(resultado_robusto["ghi"] - rest2_output.get("ghi", 0))
        diferencia_dni = abs(resultado_robusto["dni"] - rest2_output.get("dni", 0))
        diferencia_dhi = abs(resultado_robusto["dhi"] - rest2_output.get("dhi", 0))
        
        self._historial_comparativas.append({
            "timestamp": datetime.now(),
            "elevacion": elevacion,
            "diferencia_ghi_w_m2": diferencia_ghi,
            "diferencia_dni_w_m2": diferencia_dni,
            "diferencia_dhi_w_m2": diferencia_dhi,
            "confianza_robusto": resultado_robusto["confianza"],
            "advertencias": len(resultado_robusto["advertencias"])
        })
        
        if len(self._historial_comparativas) % 100 == 0:
            logger.info(
                f"[WRAPPER] Comparativa: {len(self._historial_comparativas)} ciclos procesados"
            )
    
    def obtener_estadisticas_comparativa(self) -> Optional[Dict]:
        """Retorna estadísticas de comparativa (si modo_comparativa=True)."""
        
        if not self._historial_comparativas:
            return None
        
        diferencias_ghi = [
            r["diferencia_ghi_w_m2"] for r in self._historial_comparativas
            if r["elevacion"] > 10  # Filtrar noche
        ]
        
        confianzas = [
            r["confianza_robusto"] for r in self._historial_comparativas
        ]
        
        return {
            "ciclos_procesados": len(self._historial_comparativas),
            "diferencia_ghi_media": sum(diferencias_ghi) / len(diferencias_ghi) if diferencias_ghi else 0,
            "diferencia_ghi_max": max(diferencias_ghi) if diferencias_ghi else 0,
            "diferencia_ghi_percentil_95": sorted(diferencias_ghi)[int(len(diferencias_ghi) * 0.95)] if diferencias_ghi else 0,
            "confianza_media": sum(confianzas) / len(confianzas) if confianzas else 1.0,
            "advertencias_frecuencia": sum(
                1 for r in self._historial_comparativas if r["advertencias"] > 0
            ) / len(self._historial_comparativas) * 100
        } if self._historial_comparativas else None
    
    def resetear_comparativa(self) -> None:
        """Resetea historial de comparativa."""
        self._historial_comparativas.clear()
        logger.info("[WRAPPER] Historial de comparativa reseteado")
    
    def deshabilitar(self) -> None:
        """Deshabilita arquitectura robusta."""
        self.enabled = False
        logger.warning("[WRAPPER] Arquitectura robusta deshabilitada")
    
    def habilitar(self) -> None:
        """Habilita arquitectura robusta."""
        if self.controlador is not None:
            self.enabled = True
            logger.info("[WRAPPER] Arquitectura robusta habilitada")
        else:
            logger.error("[WRAPPER] No se puede habilitar: módulos no disponibl)")
