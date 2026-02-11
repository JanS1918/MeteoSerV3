"""
═══════════════════════════════════════════════════════════════════════════════
STEP 9: SISTEMA DE PUNTUACIÓN DE SALUD DEL SISTEMA
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Puntuación 0-100 agregada del sistema
  - Factores: cobertura audit + errores WH31 + alertas críticas
  - Trending score (últimos 7 días)
  - Recomendaciones automáticas
  - Detección de degradación

Fecha de creación: 2026-02-11
Versión: 1.0
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Any, Tuple
from statistics import mean

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)
DATA_PATH = Path("data/salud")
DATA_PATH.mkdir(parents=True, exist_ok=True)

# Pesos de factores (deben sumar 100)
PESOS_FACTORES = {
    'cobertura_audit': 25,      # Calidad de auditoría (> 90% es ideal)
    'estabilidad_wh31': 25,     # Estabilidad del sensor (< 1°C error es ideal)
    'tasa_criticos': 20,        # Alertas críticas (0 idealmente)
    'tasa_resolucion': 20,      # % de alertas resueltas vs generadas
    'disponibilidad': 10        # Disposición general del sistema
}

assert sum(PESOS_FACTORES.values()) == 100, "Los pesos deben sumar 100"


# ═══════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: CALCULADOR DE SALUD
# ═══════════════════════════════════════════════════════════════════════════

class CalculadorSalud:
    """Calcula puntuación integral de salud del sistema."""
    
    def __init__(self):
        self.ruta_alertas = Path("data/alertas")
        self.ruta_validaciones = Path("data/wh31_validations")
        self.ruta_salud = DATA_PATH / "puntuaciones"
        self.ruta_salud.mkdir(parents=True, exist_ok=True)
        
        # Historial de puntuaciones (últimos 7 días = 168 horas)
        self.historial_puntuaciones = deque(maxlen=168)
        self._cargar_historial()
    
    def _cargar_historial(self):
        """Carga historial existente de archivo."""
        archivo_historial = self.ruta_salud / "historial.json"
        if archivo_historial.exists():
            try:
                with open(archivo_historial, 'r') as f:
                    datos = json.load(f)
                    self.historial_puntuaciones = deque(
                        datos.get('historial', []),
                        maxlen=168
                    )
            except:
                pass
    
    def _guardar_historial(self):
        """Guarda historial en archivo."""
        archivo_historial = self.ruta_salud / "historial.json"
        with open(archivo_historial, 'w') as f:
            json.dump({
                'fecha_guardado': datetime.now().isoformat(),
                'historial': list(self.historial_puntuaciones)
            }, f, indent=2, default=str)
    
    # ─────────────────────────────────────────────────────────────────────
    # CÁLCULO DE SUBPUNTUACIONES
    # ─────────────────────────────────────────────────────────────────────
    
    def calcular_cobertura_audit(self) -> Tuple[int, str]:
        """
        Puntuación de cobertura de auditoría (0-100).
        Basada en qué porcentaje de ciclos fueron auditados.
        
        > 95%: 100 puntos
        85-95%: 80-100 puntos
        70-85%: 50-80 puntos
        < 70%: 0-50 puntos
        """
        try:
            from core.system.auditor_bus import obtener_resultado_ultima_auditoria
            
            resultado = obtener_resultado_ultima_auditoria()
            if not resultado:
                return 50, "Sin datos de auditoría reciente"
            
            cobertura = resultado.get('estadisticas', {}).get('cobertura_total', 0)
            
            if cobertura >= 95:
                puntuacion = 100
                estado = "EXCELENTE"
            elif cobertura >= 85:
                puntuacion = int(80 + (cobertura - 85) * 4)
                estado = "BUENO"
            elif cobertura >= 70:
                puntuacion = int(50 + (cobertura - 70) * 2)
                estado = "ACEPTABLE"
            else:
                puntuacion = int(cobertura / 70 * 50)
                estado = "DEFICIENTE"
            
            return max(0, min(100, puntuacion)), estado
            
        except Exception as e:
            logger.warning(f"Error calculando cobertura audit: {e}")
            return 50, f"Error: {str(e)}"
    
    def calcular_estabilidad_wh31(self) -> Tuple[int, str]:
        """
        Puntuación de estabilidad WH31 (0-100).
        Basada en el error sistemático del sensor.
        
        < 0.5°C: 100 puntos (excelente)
        0.5-1.0°C: 80-100 puntos (bueno)
        1.0-1.5°C: 50-80 puntos (aceptable)
        > 1.5°C: 0-50 puntos (crítico)
        """
        try:
            from core.scheduler.scheduler_wh31_validator import obtener_scheduler
            
            validador = obtener_scheduler()
            resultado = validador.obtener_resultado_actual()
            
            if not resultado:
                return 70, "Sin validación WH31 reciente"
            
            stats = resultado.get('estadisticas', {})
            error = abs(stats.get('error_sistematico_wh31', {}).get('promedio', 0))
            
            if error < 0.5:
                puntuacion = 100
                estado = "EXCELENTE"
            elif error < 1.0:
                puntuacion = int(100 - (error - 0.5) * 40)
                estado = "BUENO"
            elif error < 1.5:
                puntuacion = int(80 - (error - 1.0) * 60)
                estado = "ACEPTABLE"
            else:
                # Punción degradada por cada 0.1°C sobre límite
                exceso = min(1.5, error - 1.5)
                puntuacion = max(0, int(50 - exceso * 30))
                estado = "CRÍTICO"
            
            return min(100, puntuacion), estado
            
        except Exception as e:
            logger.warning(f"Error calculando estabilidad WH31: {e}")
            return 70, f"Error: {str(e)}"
    
    def calcular_tasa_criticos(self) -> Tuple[int, str]:
        """
        Puntuación inversamente proporcional a alertas críticas.
        
        0 críticas: 100 puntos
        1-5 críticas: 80-100 puntos
        5-10 críticas: 50-80 puntos
        > 10 críticas: 0-50 puntos
        """
        try:
            from core.system.servicio_alertas_vivo import obtener_servicio
            
            servicio = obtener_servicio()
            stats = servicio.obtener_estadisticas()
            
            criticas = stats.get('criticas_activas', 0)
            
            if criticas == 0:
                return 100, "Sin alertas críticas"
            elif criticas <= 5:
                puntuacion = int(100 - criticas * 4)
                estado = "BUENO"
            elif criticas <= 10:
                puntuacion = int(80 - (criticas - 5) * 6)
                estado = "ACEPTABLE"
            else:
                puntuacion = max(0, int(50 - (criticas - 10) * 3))
                estado = "CRÍTICO"
            
            return min(100, max(0, puntuacion)), estado
            
        except Exception as e:
            logger.warning(f"Error calculando tasa críticos: {e}")
            return 80, f"Error: {str(e)}"
    
    def calcular_tasa_resolucion(self) -> Tuple[int, str]:
        """
        Porcentaje de alertas resueltas vs generadas.
        
        > 80% resueltas: 100 puntos
        60-80% resueltas: 80-100 puntos
        40-60% resueltas: 50-80 puntos
        < 40% resueltas: 0-50 puntos
        """
        try:
            from core.system.servicio_alertas_vivo import obtener_servicio
            
            servicio = obtener_servicio()
            stats = servicio.obtener_estadisticas()
            
            generadas = stats.get('total_generadas', 1)
            resueltas = stats.get('total_resueltas', 0)
            
            tasa = (resueltas / generadas * 100) if generadas > 0 else 50
            
            if tasa >= 80:
                puntuacion = 100
                estado = "EXCELENTE"
            elif tasa >= 60:
                puntuacion = int(80 + (tasa - 60) / 20 * 20)
                estado = "BUENO"
            elif tasa >= 40:
                puntuacion = int(50 + (tasa - 40) / 20 * 30)
                estado = "ACEPTABLE"
            else:
                puntuacion = int(tasa / 40 * 50)
                estado = "DEFICIENTE"
            
            return min(100, max(0, puntuacion)), estado
            
        except Exception as e:
            logger.warning(f"Error calculando tasa resolución: {e}")
            return 75, f"Error: {str(e)}"
    
    def calcular_disponibilidad(self) -> Tuple[int, str]:
        """
        Verificación de disponibilidad de servicios.
        
        Todos operativos: 100 puntos
        Un servicio con problemas: 70-80 puntos
        Múltiples problemas: 0-70 puntos
        """
        servicios_ok = 0
        servicios_total = 3
        problemas = []
        
        # Verificar auditor
        try:
            from core.system.auditor_bus import obtener_resultado_ultima_auditoria
            if obtener_resultado_ultima_auditoria():
                servicios_ok += 1
            else:
                problemas.append("Auditor sin datos recientes")
        except:
            problemas.append("Auditor no disponible")
        
        # Verificar WH31 validator
        try:
            from core.scheduler.scheduler_wh31_validator import obtener_scheduler
            if obtener_scheduler():
                servicios_ok += 1
            else:
                problemas.append("Validador WH31 sin datos")
        except:
            problemas.append("Validador WH31 no disponible")
        
        # Verificar alertas
        try:
            from core.system.servicio_alertas_vivo import obtener_servicio
            if obtener_servicio():
                servicios_ok += 1
            else:
                problemas.append("Servicio alertas sin datos")
        except:
            problemas.append("Servicio alertas no disponible")
        
        # Calcular puntuación
        if servicios_ok == servicios_total:
            return 100, "Todos los servicios operativos"
        else:
            puntuacion = int((servicios_ok / servicios_total) * 100)
            estado = f"{servicios_ok}/{servicios_total} servicios"
            return puntuacion, estado
    
    # ─────────────────────────────────────────────────────────────────────
    # CÁLCULO AGREGADO Y ANÁLISIS
    # ─────────────────────────────────────────────────────────────────────
    
    def calcular_puntuacion_total(self) -> Dict[str, Any]:
        """Calcula la puntuación integral del sistema."""
        
        # Obtener subpuntuaciones
        cobertura_pts, cobertura_est = self.calcular_cobertura_audit()
        estabilidad_pts, estabilidad_est = self.calcular_estabilidad_wh31()
        criticos_pts, criticos_est = self.calcular_tasa_criticos()
        resolucion_pts, resolucion_est = self.calcular_tasa_resolucion()
        disponibilidad_pts, disponibilidad_est = self.calcular_disponibilidad()
        
        # Calcular puntuación ponderada
        puntuacion_ponderada = (
            cobertura_pts * PESOS_FACTORES['cobertura_audit'] / 100 +
            estabilidad_pts * PESOS_FACTORES['estabilidad_wh31'] / 100 +
            criticos_pts * PESOS_FACTORES['tasa_criticos'] / 100 +
            resolucion_pts * PESOS_FACTORES['tasa_resolucion'] / 100 +
            disponibilidad_pts * PESOS_FACTORES['disponibilidad'] / 100
        )
        
        puntuacion_total = int(puntuacion_ponderada)
        
        # Determinar estado general
        if puntuacion_total >= 90:
            estado_general = "EXCELENTE"
            emoji = "🟢"
        elif puntuacion_total >= 75:
            estado_general = "BUENO"
            emoji = "🟡"
        elif puntuacion_total >= 60:
            estado_general = "ACEPTABLE"
            emoji = "🟠"
        else:
            estado_general = "CRÍTICO"
            emoji = "🔴"
        
        # Compilar resultado
        resultado = {
            'timestamp': datetime.now().isoformat(),
            'puntuacion_total': puntuacion_total,
            'estado_general': estado_general,
            'emoji': emoji,
            'factores': {
                'cobertura_audit': {
                    'puntuacion': cobertura_pts,
                    'peso': PESOS_FACTORES['cobertura_audit'],
                    'estado': cobertura_est
                },
                'estabilidad_wh31': {
                    'puntuacion': estabilidad_pts,
                    'peso': PESOS_FACTORES['estabilidad_wh31'],
                    'estado': estabilidad_est
                },
                'tasa_criticos': {
                    'puntuacion': criticos_pts,
                    'peso': PESOS_FACTORES['tasa_criticos'],
                    'estado': criticos_est
                },
                'tasa_resolucion': {
                    'puntuacion': resolucion_pts,
                    'peso': PESOS_FACTORES['tasa_resolucion'],
                    'estado': resolucion_est
                },
                'disponibilidad': {
                    'puntuacion': disponibilidad_pts,
                    'peso': PESOS_FACTORES['disponibilidad'],
                    'estado': disponibilidad_est
                }
            },
            'detalles': self._generar_detalles(
                cobertura_pts, estabilidad_pts, criticos_pts, 
                resolucion_pts, disponibilidad_pts
            )
        }
        
        # Agregar al historial
        self.historial_puntuaciones.append({
            'timestamp': datetime.now().isoformat(),
            'puntuacion': puntuacion_total
        })
        self._guardar_historial()
        
        return resultado
    
    def _generar_detalles(self, *puntuaciones) -> List[str]:
        """Genera detalles y recomendaciones basados en subpuntuaciones."""
        detalles = []
        
        cobertura_pts, estabilidad_pts, criticos_pts, resolucion_pts, disponibilidad_pts = puntuaciones
        
        # Alertas por factor bajo
        if cobertura_pts < 70:
            detalles.append("⚠️  Cobertura de auditoría baja - revisar ciclos no auditados")
        
        if estabilidad_pts < 70:
            detalles.append("⚠️  Estabilidad WH31 comprometida - considere recalibración")
        
        if criticos_pts < 70:
            detalles.append("⚠️  Múltiples alertas críticas activas - investigación requerida")
        
        if resolucion_pts < 70:
            detalles.append("⚠️  Tasa de resolución baja - alertas acumulándose sin cierre")
        
        if disponibilidad_pts < 90:
            detalles.append("⚠️  Disponibilidad de servicios comprometida")
        
        # Recomendaciones positivas
        factores_buenos = sum([
            1 for p in puntuaciones if p >= 80
        ])
        
        if factores_buenos >= 4:
            detalles.append("✅ Sistema en buena forma general")
        
        return detalles
    
    def obtener_tendencia_7dias(self) -> Dict[str, Any]:
        """Obtiene tendencia de puntuación últimos 7 días."""
        if len(self.historial_puntuaciones) == 0:
            return {
                'disponible': False,
                'mensaje': 'Sin datos históricos'
            }
        
        puntuaciones_recientes = list(self.historial_puntuaciones)[-168:]  # 7 días
        
        if not puntuaciones_recientes:
            return {
                'disponible': False,
                'mensaje': 'Sin datos en período de 7 días'
            }
        
        valores = [p['puntuacion'] for p in puntuaciones_recientes]
        
        minimo = min(valores)
        maximo = max(valores)
        promedio = int(mean(valores))
        
        # Determinar tendencia
        primeros = valores[:len(valores)//2]
        ultimos = valores[len(valores)//2:]
        
        promedio_antiguo = mean(primeros) if primeros else 0
        promedio_reciente = mean(ultimos) if ultimos else 0
        
        if promedio_reciente > promedio_antiguo + 5:
            tendencia = "MEJORANDO 📈"
        elif promedio_reciente < promedio_antiguo - 5:
            tendencia = "DEGRADÁNDOSE 📉"
        else:
            tendencia = "ESTABLE ➡️"
        
        return {
            'disponible': True,
            'datos_puntos': len(puntuaciones_recientes),
            'minimo': minimo,
            'maximo': maximo,
            'promedio': promedio,
            'tendencia': tendencia,
            'puntuaciones_recientes': puntuaciones_recientes[-24:]  # Últimas 24 horas
        }
    
    def obtener_resumen_salud(self) -> Dict[str, Any]:
        """Obtiene resumen completo de salud del sistema."""
        puntuacion = self.calcular_puntuacion_total()
        tendencia = self.obtener_tendencia_7dias()
        
        return {
            'fecha_analisis': datetime.now().isoformat(),
            'puntuacion_actual': puntuacion,
            'tendencia_7dias': tendencia,
            'resumen_ejecutivo': self._generar_resumen_ejecutivo(puntuacion, tendencia)
        }
    
    def _generar_resumen_ejecutivo(self, puntuacion: Dict, tendencia: Dict) -> str:
        """Genera resumen ejecutivo de una línea."""
        pts = puntuacion['puntuacion_total']
        estado = puntuacion['estado_general']
        emoji = puntuacion['emoji']
        
        lineas = [
            f"{emoji} SALUD SISTEMA: {pts}/100 ({estado})",
        ]
        
        if tendencia.get('disponible'):
            lineas.append(f"Tendencia: {tendencia['tendencia']}")
        
        # Factores críticos
        factores_bajos = [
            k for k, v in puntuacion['factores'].items()
            if v['puntuacion'] < 70
        ]
        
        if factores_bajos:
            lineas.append(f"Factores críticos: {', '.join(factores_bajos)}")
        
        return ' | '.join(lineas)


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES Y GETTERS
# ═══════════════════════════════════════════════════════════════════════════

_calculador_instance = None


def obtener_calculador() -> CalculadorSalud:
    """Obtiene instancia singleton del calculador."""
    global _calculador_instance
    if _calculador_instance is None:
        _calculador_instance = CalculadorSalud()
    return _calculador_instance


def iniciar_calculador_salud() -> Dict[str, Any]:
    """Inicializa el calculador de salud."""
    try:
        calculador = obtener_calculador()
        salud = calculador.obtener_resumen_salud()
        
        logger.info(
            f"[SALUD] Sistema iniciado - "
            f"Puntuación: {salud['puntuacion_actual']['puntuacion_total']}/100"
        )
        
        return {
            'estado': 'ACTIVO',
            'timestamp_inicio': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error iniciando calculador de salud: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    calculador = obtener_calculador()
    resumen = calculador.obtener_resumen_salud()
    
    puntuacion = resumen['puntuacion_actual']
    
    print(f"\n{puntuacion['emoji']} PUNTUACIÓN DE SALUD")
    print(f"Total: {puntuacion['puntuacion_total']}/100 ({puntuacion['estado_general']})")
    print("\nFactores:")
    
    for factor, datos in puntuacion['factores'].items():
        print(
            f"  • {factor}: {datos['puntuacion']}/100 "
            f"({datos['estado']}) - Peso {datos['peso']}%"
        )
    
    if puntuacion['detalles']:
        print("\nDetalles:")
        for detalle in puntuacion['detalles']:
            print(f"  {detalle}")
    
    print(f"\n{resumen['resumen_ejecutivo']}")
