"""
DASHBOARD HTML - 8 DOMINIOS V1.0
═════════════════════════════════════════════════════════════════════════════

Genera dashboard HTML interactivo mostrando:
- 8 índices sintéticos principales (0-100)
- Confianza por dominio
- Impactos cruzados
- Recomendaciones

Ejecutar: python core/system/dashboard_generator.py

Fecha: 11 de febrero de 2026
"""

from typing import Dict, List
from datetime import datetime
import json


def generar_dashboard_html(
    indices_sinteticos: Dict[str, float],
    confianzas: Dict[str, float],
    contextos: Dict[str, float],
    impactos: Dict[str, Dict],
    en_tiempo_real: bool = False
) -> str:
    """
    Genera HTML interactivo con 8 dominios, confianzas e impactos.
    
    Args:
        indices_sinteticos: {'cetreria': 75, 'lluvia': 45, ...}
        confianzas: {'cetreria': 85, ...} (meta-confianza)
        contextos: {'lluvia_1h': 2.5, 'amplitud_termica': 60, ...}
        impactos: Matriz de impactos cruzados
        en_tiempo_real: Si True, agregaAuto-refresh cada 30s
    
    Returns:
        HTML string listo para escribir a archivo
    """
    
    dominios = [
        ("🪶 CETRERÍA", "cetreria", "#FF6B6B"),
        ("🌧️ LLUVIA", "lluvia", "#4ECDC4"),
        ("😊 CONFORT", "confort", "#FFE66D"),
        ("⚽ DEPORTE", "deporte", "#95E1D3"),
        ("💧 RIEGO", "riego", "#6BCB77"),
        ("🌙 ASTRONOMÍA", "astronomia", "#4D96FF"),
        ("❤️ SALUD", "salud", "#FF6B9D"),
        ("💦 HIDROLOGÍA", "hidrologia", "#A8E6CF"),
    ]
    
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    refresh_tag = '<meta http-equiv="refresh" content="30">' if en_tiempo_real else ""
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {refresh_tag}
    <title>MeteoSerV3 Dashboard - 8 Dominios</title>
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
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 5px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .timestamp {{
            text-align: center;
            color: #ddd;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .dominio-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .dominio-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }}
        
        .dominio-header {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .indice-valor {{
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            border-radius: 10px;
            padding: 10px;
        }}
        
        .indicador {{
            width: 100%;
            height: 12px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }}
        
        .indicador-relleno {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s;
        }}
        
        .confianza {{
            margin-top: 15px;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
            font-size: 0.9em;
            color: #666;
        }}
        
        .confianza-valor {{
            font-weight: bold;
            color: #333;
        }}
        
        .estado {{
            text-align: center;
            margin-top: 10px;
            padding: 8px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .estado.optimo {{
            background: #d4edda;
            color: #155724;
        }}
        
        .estado.bueno {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        
        .estado.neutral {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .estado.malo {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .impactos {{
            background: #f9f9f9;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .impactos h3 {{
            margin-bottom: 15px;
            color: #333;
        }}
        
        .contextos {{
            background: #f0f4ff;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .contextos h3 {{
            margin-bottom: 15px;
            color: #333;
        }}
        
        .contexto-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .contexto-item:last-child {{
            border-bottom: none;
        }}
        
        .contexto-label {{
            font-weight: 500;
        }}
        
        .contexto-valor {{
            font-weight: bold;
            color: #667eea;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            font-size: 0.9em;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 MeteoSerV3</h1>
            <p>Dashboard Integrado - 8 Dominios Sintéticos</p>
        </div>
        
        <div class="timestamp">
            Actualizado: {ahora}
            {"(Auto-refresco cada 30s)" if en_tiempo_real else "(Datos estáticos)"}
        </div>
        
        <div class="grid">
"""
    
    # Generar tarjetas para cada dominio
    for label, key, color in dominios:
        valor = indices_sinteticos.get(key, 0.0)
        confianza = confianzas.get(key, 0.0)
        
        # Clasificar estado
        if valor >= 75:
            estado_class = "optimo"
            estado_texto = "✓ ÓPTIMO"
        elif valor >= 50:
            estado_class = "bueno"
            estado_texto = "⚠️ BUENO"
        elif valor >= 25:
            estado_class = "neutral"
            estado_texto = "⚠️ MODERADO"
        else:
            estado_class = "malo"
            estado_texto = "❌ CRÍTICO"
        
        html += f"""
        <div class="dominio-card">
            <div class="dominio-header">
                <span>{label}</span>
                <span style="font-size: 0.8em; color: #999;">Confianza: {confianza:.0f}%</span>
            </div>
            
            <div class="indicador">
                <div class="indicador-relleno" style="width: {valor}%; background-color: {color};"></div>
            </div>
            
            <div class="indice-valor" style="background-color: {color}20; color: {color};">
                {valor:.0f}%
            </div>
            
            <div class="estado {estado_class}">
                {estado_texto}
            </div>
            
            <div class="confianza">
                Confianza métrica: <span class="confianza-valor">{confianza:.0f}%</span>
            </div>
        </div>
"""
    
    html += """
        </div>
        
"""
    
    # Contextos actuales
    if contextos:
        html += """
        <div class="contextos">
            <h3>📊 Contextos Actuales</h3>
"""
        for clave, valor in contextos.items():
            if valor is not None:
                html += f"""
            <div class="contexto-item">
                <span class="contexto-label">{clave}:</span>
                <span class="contexto-valor">{valor:.1f}</span>
            </div>
"""
        html += """
        </div>
"""
    
    # Impactos cruzados simplificado
    if impactos:
        html += """
        <div class="impactos">
            <h3>⚡ Impactos Cruzados Detectados</h3>
            <p style="color: #666; font-size: 0.9em;">
                Sistema monitoreando dependencias entre dominios.
                Impactos críticos serían mostrados aquí.
            </p>
        </div>
"""
    
    html += f"""
        <div class="footer">
            <p>
                MeteoSerV3 v1.0 | Dashboard actualizado el {ahora}
                <br>
                8 dominios integrados con cross-validation y meta-confianza
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def guardar_dashboard(
    filename: str,
    indices_sinteticos: Dict[str, float],
    confianzas: Dict[str, float],
    contextos: Dict[str, float],
    impactos: Dict[str, Dict]
) -> str:
    """
    Genera y guarda dashboard HTML a archivo.
    
    Returns:
        Ruta del archivo guardado
    """
    
    html_content = generar_dashboard_html(
        indices_sinteticos,
        confianzas,
        contextos,
        impactos,
        en_tiempo_real=True
    )
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Dashboard guardado: {filename}")
    return filename


if __name__ == "__main__":
    # Ejemplo de uso con datos ficticios
    ejemplo_indices = {
        "cetreria": 72.0,
        "lluvia": 35.0,
        "confort": 68.0,
        "deporte": 45.0,
        "riego": 82.0,
        "astronomia": 85.0,
        "salud": 78.0,
        "hidrologia": 72.0,
    }
    
    ejemplo_confianzas = {
        "cetreria": 88.0,
        "lluvia": 75.0,
        "confort": 82.0,
        "deporte": 80.0,
        "riego": 78.0,
        "astronomia": 92.0,
        "salud": 85.0,
        "hidrologia": 80.0,
    }
    
    ejemplo_contextos = {
        "lluvia_1h": 0.0,
        "amplitud_termica": 35.0,
        "humedad_suelo": 65.0,
        "capacidad_infiltracion": 75.0,
    }
    
    html = generar_dashboard_html(
        ejemplo_indices,
        ejemplo_confianzas,
        ejemplo_contextos,
        {}
    )
    
    filename = "dashboard_meteoser_v3.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Dashboard ejemplo guardado: {filename}")
