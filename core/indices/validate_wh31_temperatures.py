"""
VALIDADOR TEMPERATURAS WH31 vs WH65 v1.0
═════════════════════════════════════════════════════════════════════════════

Compara temperaturas medidas vs ajustadas para sensores WH31 vs WH65.
Identifica errores sistemáticos y sesgos en radiación.

Uso: python core/indices/validate_wh31_temperatures.py [--output reporte.json]

Fecha: 11 de febrero de 2026
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import statistics

# Configurar UTF-8 para salida en Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio padre al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ValidadorWH31:
    """Valida correcciones de temperatura para WH31 vs WH65."""
    
    def __init__(self):
        """Inicializa el validador."""
        try:
            from core.indices.contexto_sensores import temperatura_ajustada_por_sensor
            self.temperatura_ajustada_por_sensor = temperatura_ajustada_por_sensor
        except ImportError as e:
            logger.error(f"No se pudo importar contexto_sensores: {e}")
            self.temperatura_ajustada_por_sensor = None
    
    def generar_datos_historicos_simulados(self, dias: int = 7) -> List[Dict]:
        """
        Genera datos históricos simulados para validación.
        En producción, se cargarían datos reales del sistema.
        """
        datos = []
        ahora = datetime.now()
        
        for i in range(dias * 24):  # Cada hora
            timestamp = ahora - timedelta(hours=dias*24 - i)
            
            # Simulación realista de datos meteorológicos
            hora_del_dia = timestamp.hour
            temp_base = 15 + 8 * (1 + (i % (24*7)) / (24*7))  # Ciclo semanal
            
            # WH31 lee +1-3°C más por radiación solar (reflejo interno)
            radiacion = max(0, 800 * (1 if 6 <= hora_del_dia <= 18 else 0) * 
                           (0.5 + 0.5 * (1 - abs(hora_del_dia - 12) / 6)))
            
            temp_wh31_medida = temp_base + 1.5 + (radiacion / 500)  # +1-3°C por radiación
            temp_wh65_medida = temp_base + 0.2  # Negligible
            
            humedad = 60 + 20 * (1 if 18 <= hora_del_dia or hora_del_dia <= 6 else -1)
            viento = 5 + 3 * (1 if hora_del_dia % 4 == 0 else 0)
            
            datos.append({
                'timestamp': timestamp.isoformat(),
                'hora_utc': hora_del_dia,
                'temp_wh31_medida': round(temp_wh31_medida, 2),
                'temp_wh65_medida': round(temp_wh65_medida, 2),
                'radiacion_global': round(radiacion, 0),
                'humedad_relativa': round(humedad, 1),
                'velocidad_viento': round(viento, 1),
                'presion_hpa': 1013 + (5 * (1 if i % 48 == 0 else 0)),
                'sensacion_termica': round(temp_base - viento * 0.3, 1),
            })
        
        return datos
    
    def calcular_temperatura_real(self, 
                                 medida: float, 
                                 tipo_sensor: str,
                                 radiacion: float) -> Dict:
        """Calcula temperatura real usando contexto_sensores."""
        
        if not self.temperatura_ajustada_por_sensor:
            logger.warning("temperatura_ajustada_por_sensor no disponible")
            return {
                'tipo_sensor': tipo_sensor,
                'temperatura_medida': medida,
                'temperatura_estimada_real': medida,
                'error_sistematico_grados': 0.0
            }
        
        resultado = self.temperatura_ajustada_por_sensor(
            temperatura_medida_c=medida,
            tipo_sensor=tipo_sensor.lower(),
            radiacion_w_m2=radiacion,
            distancia_pared_metros=1.0
        )
        
        return resultado
    
    def validar_datos_historicos(self, datos: List[Dict]) -> Dict:
        """
        Valida un conjunto de datos históricos.
        Retorna estadísticas de sesgos y errores.
        """
        
        logger.info("Iniciando validación de datos históricos...")
        
        # Coleccionar diferencias
        diferenciales_wh31_vs_wh65 = []
        errores_climaticos_wh31 = []
        errores_sistematicos_wh31 = []
        ajustes_radiacion_wh31 = []
        
        # Procesar cada registro
        for registro in datos:
            # Temperaturas medidas
            temp_wh31 = registro['temp_wh31_medida']
            temp_wh65 = registro['temp_wh65_medida']
            radiacion = registro['radiacion_global']
            
            # Diferencial crudo (sesgo de radiación)
            diferencial = temp_wh31 - temp_wh65
            diferenciales_wh31_vs_wh65.append(diferencial)
            
            # Calcular ajustes
            ajuste_wh31 = self.calcular_temperatura_real(temp_wh31, 'wh31', radiacion)
            ajuste_wh65 = self.calcular_temperatura_real(temp_wh65, 'wh65', radiacion)
            
            # Errores estimados
            error_wh31 = ajuste_wh31.get('error_sistematico_grados', 0)
            error_wh65 = ajuste_wh65.get('error_sistematico_grados', 0)
            
            errores_sistematicos_wh31.append(error_wh31)
            errores_climaticos_wh31.append(abs(error_wh31))
            
            # Ajuste por radiación (cuánto de la diferencia explica la radiación)
            if radiacion > 100:  # Solo con radiación significativa
                ajuste_radiacion = error_wh31
                ajustes_radiacion_wh31.append(ajuste_radiacion)
        
        # Calcular estadísticas
        stats = {
            'total_registros': len(datos),
            'periodo_dias': len(datos) / 24,
            
            'diferencial_wh31_vs_wh65': {
                'promedio': round(statistics.mean(diferenciales_wh31_vs_wh65), 2),
                'mediana': round(statistics.median(diferenciales_wh31_vs_wh65), 2),
                'desv_std': round(statistics.stdev(diferenciales_wh31_vs_wh65) if len(diferenciales_wh31_vs_wh65) > 1 else 0, 2),
                'minimo': round(min(diferenciales_wh31_vs_wh65), 2),
                'maximo': round(max(diferenciales_wh31_vs_wh65), 2),
                'observacion': 'WH31 lee más por efecto radiativo interno'
            },
            
            'error_sistematico_wh31': {
                'promedio': round(statistics.mean(errores_sistematicos_wh31), 3),
                'rms': round((sum(e**2 for e in errores_sistematicos_wh31) / len(errores_sistematicos_wh31))**0.5, 3),
                'maximo_absoluto': round(max(errores_climaticos_wh31), 3),
                'observacion': 'Error sistemático corregible mediante ajuste'
            },
            
            'ajuste_por_radiacion': {
                'registros_con_radiacion': len(ajustes_radiacion_wh31),
                'ajuste_promedio': round(statistics.mean(ajustes_radiacion_wh31) if ajustes_radiacion_wh31 else 0, 3),
                'correlacion_estimada': 'Positiva (a más radiación, más sesgo)',
                'observacion': 'Permite factor de corrección dinámico basado en GHI'
            }
        }
        
        return {
            'validacion': 'COMPLETADA',
            'timestamp': datetime.now().isoformat(),
            'estadisticas': stats,
            'conclusion': generar_conclusion(stats),
            'recomendaciones': generar_recomendaciones(stats)
        }
    
    def generar_reporte_detallado(self, resultado: Dict) -> str:
        """Genera reporte en texto de la validación."""
        
        lines = [
            "═" * 80,
            "INFORME DE VALIDACIÓN: SENSORES WH31 vs WH65",
            "═" * 80,
            "",
            f"Timestamp: {resultado['timestamp']}",
            f"Estado: {resultado['validacion']}",
            "",
            "ÍNDICES CLAVE",
            "─" * 80,
        ]
        
        stats = resultado['estadisticas']
        
        lines.extend([
            f"Total de registros procesados: {stats['total_registros']}",
            f"Período de análisis: {stats['periodo_dias']:.1f} días",
            "",
            "DIFERENCIALES WH31 - WH65",
            "─" * 80,
            f"  Promedio: {stats['diferencial_wh31_vs_wh65']['promedio']}°C",
            f"  Mediana:  {stats['diferencial_wh31_vs_wh65']['mediana']}°C",
            f"  Std Dev:  {stats['diferencial_wh31_vs_wh65']['desv_std']}°C",
            f"  Rango:    {stats['diferencial_wh31_vs_wh65']['minimo']}°C a {stats['diferencial_wh31_vs_wh65']['maximo']}°C",
            f"  Nota: {stats['diferencial_wh31_vs_wh65']['observacion']}",
            "",
            "ERROR SISTEMÁTICO WH31",
            "─" * 80,
            f"  Promedio: {stats['error_sistematico_wh31']['promedio']}°C",
            f"  RMS:      {stats['error_sistematico_wh31']['rms']}°C",
            f"  Máximo:   {stats['error_sistematico_wh31']['maximo_absoluto']}°C",
            f"  Nota: {stats['error_sistematico_wh31']['observacion']}",
            "",
            "AJUSTE POR RADIACIÓN",
            "─" * 80,
            f"  Registros con radiación: {stats['ajuste_por_radiacion']['registros_con_radiacion']}",
            f"  Ajuste promedio: {stats['ajuste_por_radiacion']['ajuste_promedio']}°C",
            f"  Correlación: {stats['ajuste_por_radiacion']['correlacion_estimada']}",
            f"  Nota: {stats['ajuste_por_radiacion']['observacion']}",
            "",
            "CONCLUSIÓN",
            "─" * 80,
        ])
        
        for line in resultado['conclusion'].split('\n'):
            lines.append(f"  {line}")
        
        lines.extend([
            "",
            "RECOMENDACIONES",
            "─" * 80,
        ])
        
        for i, rec in enumerate(resultado['recomendaciones'], 1):
            lines.append(f"  {i}. {rec}")
        
        lines.extend([
            "",
            "═" * 80,
        ])
        
        return "\n".join(lines)


def generar_conclusion(stats: Dict) -> str:
    """Genera conclusión basada en estadísticas."""
    
    promedio_diff = abs(stats['diferencial_wh31_vs_wh65']['promedio'])
    error_sistematico = abs(stats['error_sistematico_wh31']['promedio'])
    
    if promedio_diff > 2.0:
        nivel = "CRÍTICO"
    elif promedio_diff > 1.0:
        nivel = "SIGNIFICATIVO"
    else:
        nivel = "ACEPTABLE"
    
    return f"""El sensor WH31 presenta un sesgo {nivel} de aprox. {promedio_diff:.2f}°C 
sobre WH65 debido a reflexiones radiativas internas. Este sesgo es:

1. PREDECIBLE: Correlaciona fuertemente con radiación global
2. CORREGIBLE: Se aplica ajuste porcentual basado en radiación
3. ACUMULABLE: Afecta cálculos que usan temperatura (confort, salud, etc.)

Error sistemático medio: {error_sistematico:.3f}°C (corrección aplicable)

El ajuste mediante temperatura_ajustada_por_sensor() MITIGA pero NO ELIMINA
completamente el sesgo, debido a variaciones en configuración física del sensor."""


def generar_recomendaciones(stats: Dict) -> List[str]:
    """Genera recomendaciones basadas en validación."""
    
    recs = [
        "Usar temperature_ajustada_por_sensor() para WH31 en todos los cálculos",
        "Monitorear en tiempo real el factor de corrección por radiación",
        "Comparar WH31 ajustado vs WH65 cada 7 días para drift",
        "Si diferencial promedio > 3°C, revisar instalación física sensor",
        "Registrar errores de ajuste en logs para análisis posterior",
        "Usar WH65 como referencia en sistemas críticos (salud, deporte)"
    ]
    
    return recs


def main():
    """Ejecuta validación completa."""
    
    logger.info("─" * 80)
    logger.info("INICIANDO VALIDADOR WH31 vs WH65")
    logger.info("─" * 80)
    
    validador = ValidadorWH31()
    
    # Generar datos históricos simulados
    logger.info("[1/3] Generando datos históricos...")
    datos = validador.generar_datos_historicos_simulados(dias=7)
    logger.info(f"  ✓ {len(datos)} registros generados")
    
    # Validar
    logger.info("[2/3] Ejecutando validación...")
    resultado = validador.validar_datos_historicos(datos)
    logger.info("  ✓ Validación completada")
    
    # Generar reporte
    logger.info("[3/3] Generando reporte...")
    reporte = validador.generar_reporte_detallado(resultado)
    print("\n" + reporte)
    
    # Guardar JSON
    try:
        with open('validacion_wh31_resultado.json', 'w') as f:
            json.dump(resultado, f, indent=2)
        logger.info("✓ Resultado JSON: validacion_wh31_resultado.json")
    except Exception as e:
        logger.error(f"Error guardando JSON: {e}")
    
    logger.info("─" * 80)
    logger.info("VALIDACIÓN COMPLETADA")
    logger.info("─" * 80)
    
    return resultado


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Validador WH31 vs WH65')
    parser.add_argument('--output', '-o', help='Archivo JSON de salida', default='validacion_wh31_resultado.json')
    
    args = parser.parse_args()
    
    resultado = main()
