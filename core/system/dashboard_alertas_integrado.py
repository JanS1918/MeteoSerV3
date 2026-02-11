"""
DASHBOARD INTEGRADO CON ALERTAS EN VIVO v1.0
═════════════════════════════════════════════════════════════════════════════

Genera dashboard HTML interactivo que muestra:
- Alertas predictivas en tiempo real
- Estado de auditoría post-ciclo
- Validaciones WH31 (última y tendencias)
- Estadísticas y histórico
- Auto-refresh cada 30 segundos

Uso: python core/system/dashboard_alertas_integrado.py

Fecha: 11 de febrero de 2026
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generar_dashboard_alertas_integrado(
    alertas_activas: Dict = None,
    auditoria_estado: Dict = None,
    validacion_wh31: Dict = None,
    estadisticas: Dict = None
) -> str:
    """
    Genera dashboard HTML completo con alertas integradas.
    """
    
    # Preparar datos
    alertas = alertas_activas or {'total': 0, 'criticas': 0, 'alertas': {}}
    auditoria = auditoria_estado or {'estado': 'PENDING', 'cobertura': 0}
    wh31 = validacion_wh31 or {'estado': 'SIN_DATOS'}
    stats = estadisticas or {'total_generadas': 0, 'total_resueltas': 0}
    
    # Contar alertas por nivel
    alertas_criticas = sum(1 for a in alertas.get('alertas', {}).values() if a.get('nivel') == 'CRÍTICO')
    alertas_severas = sum(1 for a in alertas.get('alertas', {}).values() if a.get('nivel') == 'SEVERO')
    alertas_leves = sum(1 for a in alertas.get('alertas', {}).values() if a.get('nivel') == 'LEVE')
    
    # Colores por estado
    color_auditoria = "green" if auditoria.get('estado') == 'PASS' else "red"
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard MeteoSerV3 - Alertas & Auditoría</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 5px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        header p {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }}
        
        .card h2 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .card-content {{
            line-height: 1.8;
        }}
        
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .metric:last-child {{
            border-bottom: none;
        }}
        
        .metric-label {{
            font-weight: 600;
            color: #555;
        }}
        
        .metric-value {{
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .status-pass {{
            background: #4CAF50;
            color: white;
        }}
        
        .status-fail {{
            background: #F44336;
            color: white;
        }}
        
        .status-warning {{
            background: #FF9800;
            color: white;
        }}
        
        .alert-item {{
            background: #f5f5f5;
            padding: 12px;
            border-left: 4px solid #667eea;
            margin: 10px 0;
            border-radius: 4px;
        }}
        
        .alert-critico {{
            border-left-color: #F44336;
            background: #FFEBEE;
        }}
        
        .alert-severo {{
            border-left-color: #FF9800;
            background: #FFF3E0;
        }}
        
        .alert-leve {{
            border-left-color: #2196F3;
            background: #E3F2FD;
        }}
        
        .alert-dominio {{
            font-weight: bold;
            color: #333;
        }}
        
        .alert-magnitud {{
            font-size: 0.85em;
            color: #666;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #eee;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.75em;
            transition: width 0.3s;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            font-size: 0.85em;
            padding: 20px;
            opacity: 0.9;
        }}
        
        .refresh-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #4CAF50;
            border-radius: 50%;
            margin-right: 5px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .emoji {{
            font-size: 1.2em;
            margin-right: 5px;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 30px;
            color: #999;
        }}
        
        .full-width {{
            grid-column: 1 / -1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1><span class="emoji">📊</span>MeteoSerV3 Dashboard</h1>
            <p><span class="refresh-indicator"></span>Auto-refresh cada 30 segundos</p>
        </header>
        
        <div class="dashboard-grid">
            
            <!-- CARD: ALERTAS ACTIVAS -->
            <div class="card">
                <h2><span class="emoji">🚨</span>Alertas Activas</h2>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label">Total Activas:</span>
                        <span class="metric-value">{alertas['total']}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">🔴 Críticas:</span>
                        <span class="metric-value" style="color: #F44336;">{alertas_criticas}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">🟠 Severas:</span>
                        <span class="metric-value" style="color: #FF9800;">{alertas_severas}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">🔵 Leves:</span>
                        <span class="metric-value" style="color: #2196F3;">{alertas_leves}</span>
                    </div>
                </div>
            </div>
            
            <!-- CARD: AUDITORÍA POST-CICLO -->
            <div class="card">
                <h2><span class="emoji">✅</span>Auditoría Post-Ciclo</h2>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label">Estado:</span>
                        <span class="status-badge status-{('pass' if color_auditoria == 'green' else 'fail')}">
                            {auditoria.get('estado', 'UNKNOWN')}
                        </span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Cobertura:</span>
                        <span class="metric-value">{auditoria.get('cobertura', 0):.0f}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {auditoria.get('cobertura', 0):.0f}%; background: {'#4CAF50' if color_auditoria == 'green' else '#F44336'};">
                            {auditoria.get('cobertura', 0):.0f}%
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- CARD: VALIDACIÓN WH31 -->
            <div class="card">
                <h2><span class="emoji">🌡️</span>Validación WH31</h2>
                <div class="card-content">
                    {'<div class="metric">' +
                     f'<span class="metric-label">Estado:</span>' +
                     f'<span class="status-badge status-warning">{wh31.get("estado", "SIN_DATOS")}</span>' +
                     '</div>' +
                     (f'<div class="metric">' +
                      f'<span class="metric-label">Diferencial:</span>' +
                      f'<span class="metric-value">{wh31.get("diferencial", 0):+.2f}°C</span>' +
                      '</div>' +
                      f'<div class="metric">' +
                      f'<span class="metric-label">Error Sist.:</span>' +
                      f'<span class="metric-value">{wh31.get("error_sistematico", 0):.3f}°C</span>' +
                      '</div>' if wh31.get('estado') != 'SIN_DATOS' else '')}
                </div>
            </div>
            
            <!-- CARD: ESTADÍSTICAS GLOBALES -->
            <div class="card">
                <h2><span class="emoji">📈</span>Estadísticas</h2>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label">Alertas Generadas:</span>
                        <span class="metric-value">{stats['total_generadas']}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Alertas Resueltas:</span>
                        <span class="metric-value">{stats['total_resueltas']}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Tasa Resolución:</span>
                        <span class="metric-value">
                            {(stats['total_resueltas'] / max(stats['total_generadas'], 1) * 100):.1f}%
                        </span>
                    </div>
                </div>
            </div>
            
            <!-- CARD: ALERTAS DETALLADAS -->
            <div class="card full-width">
                <h2><span class="emoji">🔔</span>Alertas Detalladas</h2>
                <div class="card-content">
                    {(''.join([f'''
                    <div class="alert-item alert-{a.get('nivel', 'LEVE').lower()}">
                        <div class="alert-dominio">{d.upper()}</div>
                        <div class="alert-magnitud">Magnitud: {a.get('impacto_magnitud', 'N/A')}</div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">{a.get('recomendacion', 'Monitorear')}</div>
                    </div>
                    ''') for d, a in alertas.get('alertas', {}).items()]) if alertas['total'] > 0 
                    else '<div class="empty-state">✓ Sin alertas activas</div>')}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>MeteoSerV3 v3.0 | Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            <p>Dashboard auto-actualizado cada 30 segundos</p>
        </div>
    </div>
    
    <script>
        // Auto-refresh cada 30 segundos
        setTimeout(function() {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>
"""
    
    return html


def guardar_dashboard(filename: str = "dashboard_alertas_meteoser.html", **datos):
    """Guarda el dashboard en archivo."""
    try:
        html = generar_dashboard_alertas_integrado(**datos)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"✓ Dashboard guardado: {filename}")
        
        return filename
        
    except Exception as e:
        logger.error(f"Error guardando dashboard: {e}")
        return None


async def generar_dashboard_desde_servicios() -> str:
    """Genera dashboard capturando datos en vivo de los servicios."""
    try:
        # Obtener datos de servicios
        from core.system.servicio_alertas_vivo import obtener_servicio as obtener_alertas
        from core.scheduler.scheduler_wh31_validator import obtener_scheduler as obtener_wh31
        
        alertas = obtener_alertas().obtener_alertas_activas()
        wh31 = obtener_wh31().obtener_resultado_actual()
        stats = obtener_alertas().obtener_estadisticas()
        
        # Auditoría (simulada)
        auditoria = {
            'estado': 'PENDING',
            'cobertura': 91.0
        }
        
        # Validación WH31
        validacion_wh31 = None
        if wh31:
            stats_w31 = wh31.get('estadisticas', {})
            validacion_wh31 = {
                'estado': 'COMPLETADO',
                'diferencial': stats_w31.get('diferencial_wh31_vs_wh65', {}).get('promedio', 0),
                'error_sistematico': stats_w31.get('error_sistematico_wh31', {}).get('promedio', 0)
            }
        
        # Generar
        return generar_dashboard_alertas_integrado(
            alertas_activas=alertas,
            auditoria_estado=auditoria,
            validacion_wh31=validacion_wh31,
            estadisticas=stats
        )
        
    except Exception as e:
        logger.error(f"Error generando dashboard: {e}")
        return generar_dashboard_alertas_integrado()


if __name__ == "__main__":
    # Test con datos simulados
    datos_simulados = {
        'alertas_activas': {
            'total': 2,
            'criticas': 2,
            'alertas': {
                'cetreria': {
                    'nivel': 'CRÍTICO',
                    'impacto_magnitud': -80.0,
                    'recomendacion': 'Cancelar entrenamientos: condiciones adversas'
                },
                'lluvia': {
                    'nivel': 'CRÍTICO',
                    'impacto_magnitud': 90.0,
                    'recomendacion': 'Aprovechar para riego'
                }
            }
        },
        'auditoria_estado': {
            'estado': 'PASS',
            'cobertura': 91.0
        },
        'validacion_wh31': {
            'estado': 'COMPLETADO',
            'diferencial': 1.93,
            'error_sistematico': 0.950
        },
        'estadisticas': {
            'total_generadas': 12,
            'total_resueltas': 10
        }
    }
    
    guardar_dashboard("dashboard_alertas_meteoser.html", **datos_simulados)
    print("✓ Dashboard de ejemplo generado")
