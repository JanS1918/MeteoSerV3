"""
COORDINADOR DE APRENDIZAJE UNIVERSAL - MeteoSerV3 V50.5
═══════════════════════════════════════════════════════════════════════════════════
Integrador transparente: permite que módulos de índices aprendan sin cambios.

MODO DE USO EN MÓDULOS:

    # Al inicio del cálculo de índice
    coordinador = obtener_coordinador_aprendizaje()
    prediccion_id = coordinador.marcar_inicio_calculo("wbgt",
        contexto={"elevacion_solar": 30, "hora": 14, "estado": "dia"})
    
    # Ejecutar cálculo normal
    wbgt = calcular_wbgt(...)
    
    # Al final
    coordinador.marcar_fin_calculo(prediccion_id, wbgt, confianza=85)
    
    # Cuando conocemos la realidad (ej: después de 24h para T_min)
    coordinador.registrar_realidad("temperatura_minima", observacion=22.5)

Esto es completamente TRANSPARENTE para los módulos:
- No rompe código existente
- Agrega capacidad de aprendizaje automáticamente  
- Los valores retornados YA INCLUYEN la corrección aprendida

Autor: V50.5 (Feb 10, 2026)
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from core.learning.framework_aprendizaje_universal import obtener_framework_aprendizaje

logger = logging.getLogger(__name__)


class CoordinadorAprendizaje:
    """
    Coordinador que maneja toda la integración del aprendizaje universal.
    
    Funciona como puente entre:
    - Módulos de índices (que calculan predicciones)
    - Framework de aprendizaje (que aprende de errores)
    - Datos reales (feedback que llega después)
    """
    
    def __init__(self):
        self.framework = obtener_framework_aprendizaje()
        self.calculos_en_curso = {}  # {prediccion_id: {tipo, contexto, ts_inicio}}
    
    def marcar_inicio_calculo(
        self,
        tipo_indice: str,
        contexto: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Marca inicio de cálculo de un índice (para rastreabilidad completa).
        
        Args:
            tipo_indice: Ej "wbgt", "et0", "temperatura_minima"
            contexto: Info de contexto (elevacion_solar, hora, etc.)
            metadata: Información adicional (modelo versión, etc.)
        
        Returns:
            ID de predicción para marcar después
        """
        # Registrar sólo contexto del inicio
        prediccion_id = f"inicio_{tipo_indice}_{datetime.now(timezone.utc).timestamp()}"
        
        self.calculos_en_curso[prediccion_id] = {
            "tipo": tipo_indice,
            "contexto": contexto or {},
            "metadata": metadata or {},
            "ts_inicio": datetime.now(timezone.utc)
        }
        
        logger.debug(f"[COORDINADOR] Inicio cálculo: {tipo_indice} (id={prediccion_id[:30]}...)")
        return prediccion_id
    
    def marcar_fin_calculo(
        self,
        prediccion_id: str,
        valor_predicho: float,
        confianza: Optional[float] = None,
        aplicar_correccion: bool = True
    ) -> float:
        """
        Marca fin de cálculo y registra predicción.
        También aplica automáticamente correcciones aprendidas.
        
        Args:
            prediccion_id: ID retornado por marcar_inicio_calculo
            valor_predicho: Valor calculado (sin corrección)
            confianza: Confianza en la predicción (0-100)
            aplicar_correccion: Si aplicar correcciones aprendidas
        
        Returns:
            Valor potencialmente corregido con aprendizaje
        """
        try:
            if prediccion_id not in self.calculos_en_curso:
                logger.warning(f"ID predicción desconocido: {prediccion_id}")
                return valor_predicho
            
            inicio_info = self.calculos_en_curso.pop(prediccion_id)
            tipo_indice = inicio_info["tipo"]
            contexto = inicio_info["contexto"]
            
            # Registrar predicción sin corrección
            self.framework.registrar_prediccion(
                tipo_indice=tipo_indice,
                prediccion=valor_predicho,
                contexto=contexto,
                confianza_prediccion=confianza,
                metadata=inicio_info["metadata"]
            )
            
            # Aplicar corrección si hay aprendizaje disponible
            if aplicar_correccion:
                valor_corregido, confianza_final = self.framework.obtener_prediccion_corregida(
                    tipo_indice=tipo_indice,
                    prediccion=valor_predicho,
                    contexto=contexto
                )
                
                # Actualizar confianza si fue corregido
                if valor_corregido != valor_predicho:
                    logger.debug(f"[COORDINADOR] {tipo_indice}: {valor_predicho:.2f} → {valor_corregido:.2f} "
                                f"(confianza={confianza_final:.0f}%)")
                    return valor_corregido
                else:
                    return valor_predicho
            else:
                return valor_predicho
                
        except Exception as e:
            logger.error(f"Error marcando fin de cálculo: {e}")
            return valor_predicho
    
    def registrar_realidad(
        self,
        tipo_indice: str,
        observacion: float,
        contexto: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Registra observación real para que sistema aprenda.
        Se empareja automáticamente con predicción más reciente.
        
        Ejemplos:
        - WBGT: al día siguiente, cuando conocemos la temp real de globo
        - Lluvia: cuando pasa el evento
        - T_mín: mañana siguiente
        - ET0: mediante balance hídrico
        
        Args:
            tipo_indice: Tipo de predicción observada
            observacion: Valor real observado
            contexto: Contexto de observación
            timestamp: Momento de observación
        """
        try:
            self.framework.registrar_observacion(
                tipo_indice=tipo_indice,
                observacion=observacion,
                contexto=contexto,
                timestamp_observacion=timestamp
            )
            
            logger.debug(f"[COORDINADOR] Realidad registrada: {tipo_indice}={observacion:.2f}")
            
            # Cada 100 observaciones, recalcular ajustes
            eventos = self.framework._leer_historico()
            observaciones = len([e for e in eventos if "observacion" in e])
            
            if observaciones % 100 == 0:
                logger.info(f"[COORDINADOR] Recalculando ajustes ({observaciones} observaciones)")
                self.framework.calcular_ajustes(muestras_minimas=50)
                
        except Exception as e:
            logger.error(f"Error registrando realidad: {e}")
    
    def obtener_reporte_aprendizaje(self) -> Dict:
        """Retorna reporte completo del estado de aprendizaje del sistema."""
        return self.framework.generar_reporte_aprendizaje()
    
    def obtener_estado_indice(self, tipo_indice: str) -> Optional[Dict]:
        """Retorna estado actual de aprendizaje para un índice específico."""
        modelo = self.framework.modelos_aprendidos.get("tipos_indice", {}).get(tipo_indice)
        if modelo:
            return {
                "tipo": tipo_indice,
                "error_medio_pct": modelo.get("error_medio_pct"),
                "confiabilidad_pct": modelo.get("confiabilidad_pct"),
                "muestras": modelo.get("muestras"),
                "contextos_aprendidos": len(modelo.get("factores_correccion", {})),
                "aprendiendo": modelo.get("muestras", 0) > 0
            }
        return None


# Instancia global singleton
_coordinador_instance = None

def obtener_coordinador_aprendizaje() -> CoordinadorAprendizaje:
    """Obtiene instancia singleton del coordinador."""
    global _coordinador_instance
    if _coordinador_instance is None:
        _coordinador_instance = CoordinadorAprendizaje()
    return _coordinador_instance


# ═══════════════════════════════════════════════════════════════════════════════════
# EJEMPLO DE INTEGRACIÓN EN UN MÓDULO DE ÍNDICE
# ═══════════════════════════════════════════════════════════════════════════════════
"""
# En core/indices/environmental_indices.py (en la función calcular_wbgt):

def calcular_wbgt_con_aprendizaje(temperatura, humedad, velocidad_viento, radiacion):
    coordinador = obtener_coordinador_aprendizaje()
    
    # Marcar inicio
    pred_id = coordinador.marcar_inicio_calculo(
        "wbgt",
        contexto={
            "elevacion_solar": contexto_solar.get("elevacion_solar_deg"),
            "hora": datetime.now().hour,
            "estado": contexto_solar.get("estado")
        }
    )
    
    # Cálculo normal existente
    wbgt = _calcular_wbgt_interno(temperatura, humedad, velocidad_viento, radiacion)
    
    # Marcar fin (automáticamente aplica correcciones aprendidas)
    wbgt_con_aprendizaje = coordinador.marcar_fin_calculo(
        pred_id,
        wbgt, 
        confianza=85  # Tu confianza normal
    )
    
    return wbgt_con_aprendizaje  # ← Retorna ya corregido!

# Y cuando conocamos la realidad (ej: temperatura de globo real al día siguiente):
coordinador.registrar_realidad("wbgt", observacion=28.7, contexto={...})

# ¡Y ya aprendió! La próxima predicción de WBGT saldrá automáticamente ajustada.
"""

# ═══════════════════════════════════════════════════════════════════════════════════
# CASOS DE USO POR MÓDULO
# ═══════════════════════════════════════════════════════════════════════════════════
"""
WBGT (environmental_indices.py):
  Registra: temperatura_interior, humedad_interior, radiacion_solar
  Realidad: temperatura_interior_real (del sensor las 24h después)
  
ET0 (environmental_indices.py):
  Registra: presión, humedad, viento, radiación, temperatura
  Realidad: balance_hidrico_real (consumo observado en riego)
  
T_MIN (deardorff_force_restore.py):
  Registra: inversión, nubosidad, viento nocturno
  Realidad: temperatura_minima_observada (mañana siguiente)
  
RADIACION (radiacion_hibrida.py):
  Registra: modelo REST2, contexto solar
  Realidad: medición piranómetro (si disponible)
  
SENSORES VIRTUALES:
  Registra: predicción del sensor sintético
  Realidad: comparación con sensor real o calibración
  
FUSIÓN DE SENSORES:
  Registra: temperatura fusionada WH65+WH31
  Realidad: comparación con estación de referencia
"""
