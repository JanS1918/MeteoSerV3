"""
═══════════════════════════════════════════════════════════════════════════════
STEP 19: SCHEDULED REPORTS - REPORTES AUTOMÁTICOS
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Reportes automáticos diarios/semanales
  - Envío por email
  - Resúmenes ejecutivos

Fecha: 2026-02-11
"""

import logging
import asyncio
from datetime import datetime, time
from typing import Dict, Any, Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class FrecuenciaReporte(str, Enum):
    """Frecuencias de reportes."""
    DIARIO = "diario"
    SEMANAL = "semanal"
    MENSUAL = "mensual"
    BAJO_DEMANDA = "bajo_demanda"


class GeneradorReportesAutomaticos:
    """Genera reportes programados automáticamente."""
    
    def __init__(self):
        self.reportes_programados: Dict[str, Dict[str, Any]] = {}
        self.ultima_ejecucion: Dict[str, datetime] = {}
    
    def programar_reporte(self, nombre: str,
                         generador: Callable,
                         frecuencia: str,
                         hora_ejecucion: str = "09:00",
                         recipients: list = None,
                         habilitado: bool = True):
        """Programa nuevo reporte."""
        
        self.reportes_programados[nombre] = {
            'generador': generador,
            'frecuencia': FrecuenciaReporte(frecuencia),
            'hora_ejecucion': hora_ejecucion,
            'recipients': recipients or [],
            'habilitado': habilitado,
            'timestamp_creacion': datetime.now().isoformat()
        }
        
        logger.info(f"Reporte programado: {nombre} ({frecuencia})")
    
    async def ejecutar_reporte(self, nombre: str) -> Dict[str, Any]:
        """Ejecuta reporte específico."""
        
        reporte_config = self.reportes_programados.get(nombre)
        if not reporte_config:
            return {'error': 'Reporte no existe'}
        
        try:
            generador = reporte_config['generador']
            
            # Ejecutar generador
            if asyncio.iscoroutinefunction(generador):
                resultado = await generador()
            else:
                resultado = generador()
            
            self.ultima_ejecucion[nombre] = datetime.now()
            
            logger.info(f"Reporte ejecutado: {nombre}")
            
            return {
                'nombre': nombre,
                'estado': 'exitoso',
                'timestamp': datetime.now().isoformat(),
                'resultado': resultado
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando reporte {nombre}: {e}")
            return {
                'nombre': nombre,
                'estado': 'error',
                'error': str(e)
            }
    
    async def ejecutar_reportes_debidos(self) -> Dict[str, Any]:
        """Ejecuta reportes que están debido ejecutarse."""
        
        resultados = {}
        ahora = datetime.now()
        
        for nombre, config in self.reportes_programados.items():
            if not config['habilitado']:
                continue
            
            ultima = self.ultima_ejecucion.get(nombre)
            
            # Determinar si debe ejecutarse
            debe_ejecutar = False
            
            if config['frecuencia'] == FrecuenciaReporte.DIARIO:
                if not ultima or (ahora - ultima).days >= 1:
                    debe_ejecutar = True
            
            elif config['frecuencia'] == FrecuenciaReporte.SEMANAL:
                if not ultima or (ahora - ultima).days >= 7:
                    debe_ejecutar = True
            
            elif config['frecuencia'] == FrecuenciaReporte.MENSUAL:
                if not ultima or (ahora - ultima).days >= 30:
                    debe_ejecutar = True
            
            # Ejecutar si es hora
            if debe_ejecutar:
                resultado = await self.ejecutar_reporte(nombre)
                resultados[nombre] = resultado
        
        return resultados
    
    def obtener_estado_reportes(self) -> Dict[str, Any]:
        """Obtiene estado de todos los reportes."""
        
        return {
            'total_programados': len(self.reportes_programados),
            'reportes': [
                {
                    'nombre': nombre,
                    'frecuencia': config['frecuencia'].value,
                    'habilitado': config['habilitado'],
                    'ultima_ejecucion': self.ultima_ejecucion.get(nombre, 'NUNCA')
                }
                for nombre, config in self.reportes_programados.items()
            ]
        }


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES PREDEFINIDAS DE REPORTES
# ═══════════════════════════════════════════════════════════════════════════

async def generar_reporte_diario_alertas() -> Dict[str, Any]:
    """Genera reporte diario de alertas."""
    
    try:
        from core.analytics.analisis_historico import obtener_analizador
        
        analizador = obtener_analizador()
        tendencia = analizador.analizar_tendencia_alertas(dias=1)
        
        return {
            'titulo': 'Reporte Diario de Alertas',
            'fecha': datetime.now().isoformat(),
            'datos': tendencia
        }
    except Exception as e:
        logger.error(f"Error generando reporte diario: {e}")
        return {}


async def generar_reporte_diario_salud() -> Dict[str, Any]:
    """Genera reporte diario de salud del sistema."""
    
    try:
        from core.analytics.calculador_salud import obtener_calculador
        
        calculador = obtener_calculador()
        resumen = calculador.obtener_resumen_salud()
        
        return {
            'titulo': 'Reporte Diario de Salud',
            'fecha': datetime.now().isoformat(),
            'datos': resumen
        }
    except Exception as e:
        logger.error(f"Error generando reporte salud: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_generador_reportes_instance = None


def obtener_generador_reportes() -> GeneradorReportesAutomaticos:
    """Obtiene instancia singleton."""
    global _generador_reportes_instance
    if _generador_reportes_instance is None:
        _generador_reportes_instance = GeneradorReportesAutomaticos()
    return _generador_reportes_instance


def iniciar_generador_reportes() -> Dict[str, Any]:
    """Inicializa generador de reportes."""
    try:
        generador = obtener_generador_reportes()
        
        # Programar reportes por defecto
        generador.programar_reporte(
            'diario_alertas',
            generar_reporte_diario_alertas,
            'diario',
            '09:00'
        )
        
        generador.programar_reporte(
            'diario_salud',
            generar_reporte_diario_salud,
            'diario',
            '06:00'
        )
        
        contexto = {
            'estado': 'ACTIVO',
            'reportes_programados': len(generador.reportes_programados),
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[REPORTES] Generador iniciado - "
            f"{contexto['reportes_programados']} reportes programados"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando generador de reportes: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
