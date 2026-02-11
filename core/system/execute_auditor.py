"""
EJECUTOR AUDITOR BUS v1.0
═════════════════════════════════════════════════════════════════════════════

Script que ejecuta la auditoría post-ciclo y genera reporte.

Uso: python core/system/execute_auditor.py [--output reporte.txt] [--html]

Fecha: 11 de febrero de 2026
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from io import StringIO

# Configurar UTF-8 para salida en Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio padre al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def obtener_constantes_bus_simuladas() -> Dict[str, float]:
    """
    SIMULADOR: En producción, esto llamaría al bus real.
    
    Para pruebas, retorna un dict con constantes esperadas
    """
    constantes = {
        # CETRERÍA
        "cetreria_viento": 75.0,
        "cetreria_visibilidad": 80.0,
        "cetreria_termales": 60.0,
        "cetreria_barro": 40.0,
        "indice_cetreria_sintetico": 72.0,
        "confianza_cetreria": 88.0,
        
        # LLUVIA
        "lluvia_riesgo_inundacion": 25.0,
        "lluvia_visibilidad_carretera": 85.0,
        "lluvia_adherencia_terreno": 70.0,
        "lluvia_probabilidad_rayos": 15.0,
        "lluvia_derivada_ghi_w_m2_min": 5.0,
        "lluvia_derivada_presion_hpa_min": 0.5,
        "lluvia_derivada_humedad_pct_min": 2.0,
        "indice_lluvia_sintetico": 50.0,
        "confianza_lluvia": 75.0,
        
        # CONFORT
        "confort_temperatura_ideal": 75.0,
        "confort_humedad_ideal": 65.0,
        "confort_uvi": 45.0,
        "confort_sensacion_termica": 70.0,
        "indice_confort_sintetico": 68.0,
        "confianza_confort": 82.0,
        
        # DEPORTE
        "deporte_adherencia_terreno": 68.0,
        "deporte_visibilidad": 80.0,
        "deporte_viento_juego": 65.0,
        "deporte_confort_atletas": 62.0,
        "indice_deporte_sintetico": 69.0,
        "confianza_deporte": 80.0,
        
        # RIEGO
        "riego_balance_hidrico": 55.0,
        "riego_estres_cultivo": 40.0,
        "riego_disponibilidad_agua": 65.0,
        "riego_eficiencia_infiltr": 72.0,
        "indice_riego_sintetico": 58.0,
        "confianza_riego": 78.0,
        
        # ASTRONOMÍA
        "astro_horas_luz": 45.0,
        "astro_obs_nocturna": 82.0,
        "astro_amplitud_termica": 35.0,
        "astro_claridad_kt": 48.0,
        "astro_visibilidad_noche": 85.0,
        "indice_astronomia_sintetico": 75.0,
        "confianza_astronomia": 92.0,
        
        # SALUD
        "salud_uvi": 45.0,
        "salud_riesgo_calor": 25.0,
        "salud_riesgo_frio": 15.0,
        "salud_riesgo_helada": 5.0,
        "salud_aire_interior": 78.0,
        "salud_aire_exterior": 70.0,
        "indice_salud_sintetico": 65.0,
        "confianza_salud": 85.0,
        
        # HIDROLOGÍA
        "hidro_infiltracion": 72.0,
        "hidro_escorrentia": 20.0,
        "hidro_spi": 55.0,
        "hidro_humedad_tendencial": 68.0,
        "indice_hidrologia_sintetico": 65.0,
        "confianza_hidrologia": 80.0,
        
        # ÍNDICES COMPARTIDOS
        "comfort_universal": 70.0,
        "riesgo_termico_integrado": 32.0,
        "estabilidad_atmosferica": 65.0,
        "humedad_suelo_integrada": 60.0,
        "capacidad_infiltracion_compartida": 72.0,
        "radiacion_compuesta": 52.0,
        
        # META-ÍNDICES
        "indice_fusion_sinteticos": 68.5,
        "confianza_fusion_sinteticos": 83.0,
    }
    
    return constantes


def ejecutar_auditoria(
    output_file: Optional[str] = None,
    html: bool = False
) -> Dict:
    """
    Ejecuta auditoría completa del bus y retorna resultado.
    """
    
    logger.info("═" * 80)
    logger.info("INICIANDO AUDITORÍA DE BUS")
    logger.info("═" * 80)
    
    # Importar auditor
    try:
        from core.system.auditor_bus import auditar_publicacion_bus, generar_reporte_auditoria
    except ImportError as e:
        logger.error(f"No se pudo importar auditor_bus: {e}")
        return None
    
    # Obtener constantes (simuladas para demostración)
    logger.info("[1/3] Obteniendo constantes del bus...")
    constantes_bus = obtener_constantes_bus_simuladas()
    logger.info(f"  ✓ {len(constantes_bus)} constantes obtenidas")
    
    # Ejecutar auditoría
    logger.info("[2/3] Ejecutando auditoría...")
    resultado_auditoria = auditar_publicacion_bus(constantes_bus, reporte_detallado=True)
    logger.info(f"  ✓ Estado: {resultado_auditoria['estado_auditoria']}")
    logger.info(f"  ✓ Cobertura: {resultado_auditoria['cobertura_porcentaje']:.0f}%")
    
    # Generar reporte
    logger.info("[3/3] Generando reporte...")
    reporte_texto = generar_reporte_auditoria(resultado_auditoria)
    
    # Imprimir resumen
    print("\n" + reporte_texto)
    
    # Guardar archivos si se solicita
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(reporte_texto)
            logger.info(f"✓ Reporte TXT guardado: {output_file}")
        except Exception as e:
            logger.error(f"Error guardando TXT: {e}")
    
    if html:
        html_file = output_file.replace('.txt', '.html') if output_file else 'reporte_auditoria.html'
        try:
            html_content = generar_reporte_html(resultado_auditoria)
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"✓ Reporte HTML guardado: {html_file}")
        except Exception as e:
            logger.error(f"Error guardando HTML: {e}")
    
    logger.info("═" * 80)
    logger.info("AUDITORÍA COMPLETADA")
    logger.info("═" * 80)
    
    return resultado_auditoria


def generar_reporte_html(auditoria: Dict) -> str:
    """Genera versión HTML del reporte de auditoría."""
    
    estado_color = {
        "PASS": "#4CAF50",
        "WARN": "#FF9800",
        "FAIL": "#F44336"
    }
    
    color = estado_color.get(auditoria['estado_auditoria'], "#999")
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Auditoría Bus MeteoSerV3</title>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: {color};
            text-align: center;
        }}
        .estado {{
            font-size: 2em;
            color: {color};
            text-align: center;
            padding: 20px;
            border: 2px solid {color};
            border-radius: 5px;
            margin: 20px 0;
        }}
        .seccion {{
            margin: 30px 0;
            padding: 20px;
            background: #f9f9f9;
            border-left: 4px solid {color};
            border-radius: 5px;
        }}
        .seccion h2 {{
            margin-top: 0;
            color: #333;
        }}
        .item {{
            display: flex;
            justify-content: space-between;
            padding: 8px;
            border-bottom: 1px solid #eee;
        }}
        .item:last-child {{
            border-bottom: none;
        }}
        .ok {{ color: #4CAF50; font-weight: bold; }}
        .warn {{ color: #FF9800; font-weight: bold; }}
        .fail {{ color: #F44336; font-weight: bold; }}
        .timestamp {{
            text-align: center;
            color: #999;
            margin-top: 30px;
            font-size: 0.9em;
        }}
        .recomendacion {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #2196F3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Auditoría de Publicación en Bus</h1>
        
        <div class="estado">
            {auditoria['estado_auditoria']}
        </div>
        
        <div class="seccion">
            <h2>📊 Cobertura</h2>
            <div class="item">
                <span>Constantes Presentes:</span>
                <span class="ok">{auditoria['constantes_presentes']}/{auditoria['total_constantes_esperadas']}</span>
            </div>
            <div class="item">
                <span>Cobertura:</span>
                <span class="ok">{auditoria['cobertura_porcentaje']:.0f}%</span>
            </div>
        </div>
        
        <div class="seccion">
            <h2>🎯 Dominios</h2>
            <div class="item">
                <span>✓ Completos:</span>
                <span>{', '.join(auditoria['dominios_completos']) or 'Ninguno'}</span>
            </div>
            <div class="item">
                <span>⚠️ Parciales:</span>
                <span>{', '.join(auditoria['dominios_parciales']) or 'Ninguno'}</span>
            </div>
            <div class="item">
                <span>❌ Fallos:</span>
                <span>{', '.join(auditoria['dominios_fallidos']) or 'Ninguno'}</span>
            </div>
        </div>
        
        <div class="seccion">
            <h2>🔧 Contexto Compartido</h2>
            <div class="item">
                <span>Índices Compartidos:</span>
                <span>{auditoria['indices_compartidos_presentes']}/7</span>
            </div>
            <div class="item">
                <span>Meta-Índices:</span>
                <span>{auditoria['meta_indices_presente']}/2</span>
            </div>
        </div>
        
        <div class="seccion">
            <h2>💡 Recomendaciones</h2>
            {"".join(f'<div class="recomendacion">{r}</div>' for r in auditoria['recomendaciones'])}
        </div>
        
        <div class="timestamp">
            Auditoría ejecutada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
    
    return html


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejecutor de Auditoría Bus MeteoSerV3')
    parser.add_argument('--output', '-o', help='Archivo de salida TXT', default=None)
    parser.add_argument('--html', action='store_true', help='Generar también HTML')
    
    args = parser.parse_args()
    
    resultado = ejecutar_auditoria(output_file=args.output, html=args.html)
    
    sys.exit(0 if resultado and resultado['estado_auditoria'] == 'PASS' else 1)
