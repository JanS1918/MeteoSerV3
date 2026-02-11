"""
═══════════════════════════════════════════════════════════════════════════════
STEP 18: DOCUMENT GENERATION - REPORTES PDF
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Generar reportes en PDF
  - Exportar datos a Excel
  - Documentación automática

Fecha: 2026-02-11
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

DATA_PATH = Path("data/reportes")
DATA_PATH.mkdir(parents=True, exist_ok=True)


class GeneradorReportesExportacion:
    """Genera reportes en múltiples formatos."""
    
    def __init__(self):
        self.ruta_reportes = DATA_PATH
    
    def generar_reporte_html(self, titulo: str, 
                            datos: Dict[str, Any],
                            seccion: str = None) -> str:
        """Genera reporte HTML."""
        
        html_contenido = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{titulo}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .timestamp {{ color: #999; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h1>{titulo}</h1>
            <p class="timestamp">Generado: {datetime.now().isoformat()}</p>
            <section>
                <h2>{seccion or 'Datos'}</h2>
                <pre>{json.dumps(datos, indent=2, default=str)}</pre>
            </section>
        </body>
        </html>
        """
        
        # Guardar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = self.ruta_reportes / f"reporte_{timestamp}.html"
        
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(html_contenido)
        
        return str(archivo)
    
    def generar_reporte_csv(self, datos: list, 
                           nombre_archivo: str) -> str:
        """Genera CSV a partir de lista de dicts."""
        
        if not datos:
            return ""
        
        import csv
        
        archivo = self.ruta_reportes / f"{nombre_archivo}.csv"
        
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=datos[0].keys())
            writer.writeheader()
            writer.writerows(datos)
        
        return str(archivo)
    
    def obtener_reportes_generados(self, limites: int = 20) -> list:
        """Obtiene lista de reportes generados."""
        
        reportes = sorted(
            self.ruta_reportes.glob("reporte_*.html"),
            reverse=True
        )[:limites]
        
        return [str(r) for r in reportes]
