"""
MÓDULO DE INTEGRACIÓN DE DATOS RECUPERADOS
============================================

Carga y integra datos históricos recuperados del período ciego
en los índices y sensores del sistema.

Uso:
    from core.integration.data_recovery import cargar_datos_recuperados
    eventos = cargar_datos_recuperados(ruta_archivo)
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class CargadorDatosRecuperados:
    """Carga datos recuperados del archivo de recuperación"""
    
    def __init__(self):
        self.datos_recuperados = {}
        self.eventos_integrados = []
        self.errors = []
    
    def cargar_archivo(self, ruta: str) -> Dict[str, Any]:
        """Carga el archivo JSON de datos recuperados"""
        try:
            ruta_path = Path(ruta)
            with open(ruta_path, 'r', encoding='utf-8') as f:
                self.datos_recuperados = json.load(f)
            
            logger.info(f"[OK] Archivo cargado: {ruta}")
            return self.datos_recuperados
        
        except FileNotFoundError:
            msg = f"[ERROR] Archivo no encontrado: {ruta}"
            logger.error(msg)
            self.errors.append(msg)
            return {}
        except json.JSONDecodeError as e:
            msg = f"[ERROR] Error JSON en {ruta}: {e}"
            logger.error(msg)
            self.errors.append(msg)
            return {}
    
    def extraer_sensores(self) -> List[Dict[str, Any]]:
        """Extrae registros de sensores del historial"""
        sensores = []
        
        historial = self.datos_recuperados.get("historial_sensores", [])
        for item in historial:
            if "datos" in item:
                contenido = item["datos"]
                if isinstance(contenido, list):
                    sensores.extend(contenido)
                else:
                    sensores.append(contenido)
        
        logger.info(f"[STATS] {len(sensores)} registros de sensores extraídos")
        return sensores
    
    def extraer_ultimos_datos_ecowitt(self) -> Optional[Dict[str, Any]]:
        """Extrae el último payload de Ecowitt guardado"""
        datos_locales = self.datos_recuperados.get("datos_locales", [])
        
        for item in datos_locales:
            archivo = item.get("archivo", "")
            if "last_ecowitt_payload" in archivo:
                payload = item.get("datos", {})
                logger.info("📡 Payload Ecowitt encontrado")
                return payload
        
        return None
    
    def generar_eventos_historicos(self, sensores: List[Dict]) -> List[Dict[str, Any]]:
        """Genera eventos históricos a partir de registros de sensores"""
        eventos = []
        
        for sensor in sensores:
            # Extraer timestamp si existe
            ts = sensor.get("timestamp") or sensor.get("ts") or datetime.now().isoformat()
            
            evento = {
                "timestamp": ts,
                "tipo": "sensor.historico",
                "datos": sensor,
                "fuente": "recuperacion",
                "critico": False
            }
            eventos.append(evento)
        
        logger.info(f"[REINICIO] {len(eventos)} eventos históricos generados")
        self.eventos_integrados = eventos
        return eventos
    
    def crear_resumen_recuperacion(self) -> Dict[str, Any]:
        """Crea un resumen ejecutivo de la recuperación"""
        return {
            "timestamp_recuperacion": self.datos_recuperados.get("timestamp_recuperacion"),
            "periodo_ciego": self.datos_recuperados.get("periodo_ciego", {}),
            "sumario": self.datos_recuperados.get("sumario", {}),
            "eventos_integrados": len(self.eventos_integrados),
            "status": "completado" if not self.errors else "parcial",
            "errores": self.errors
        }


# ═══════════════════════════════════════════════════════════════════════════════

def cargar_datos_recuperados(ruta_archivo: str) -> Dict[str, Any]:
    """
    Función principal para cargar datos recuperados
    
    Args:
        ruta_archivo: Ruta al archivo datos_recuperados_TIMESTAMP.json
    
    Returns:
        Dict con eventos, sensores y metadatos integrados
    """
    cargador = CargadorDatosRecuperados()
    
    # Cargar
    datos = cargador.cargar_archivo(ruta_archivo)
    if not datos:
        return {"status": "error", "errores": cargador.errors}
    
    # Extraer
    sensores = cargador.extraer_sensores()
    ecowitt = cargador.extraer_ultimos_datos_ecowitt()
    
    # Generar eventos
    eventos = cargador.generar_eventos_historicos(sensores)
    
    # Resumen
    resumen = cargador.crear_resumen_recuperacion()
    
    resultado = {
        "status": "exito",
        "resumen": resumen,
        "sensores": sensores,
        "eventos": eventos,
        "ecowitt_ultimo": ecowitt,
        "periodo": datos.get("periodo_ciego", {}),
    }
    
    logger.info(f"\n[OK] RECUPERACIÓN COMPLETADA:")
    logger.info(f"   • Período: {datos.get('periodo_ciego', {}).get('inicio')} → {datos.get('periodo_ciego', {}).get('fin')}")
    logger.info(f"   • Sensores: {len(sensores)}")
    logger.info(f"   • Eventos: {len(eventos)}")
    logger.info(f"   • Status: {resultado['status']}\n")
    
    return resultado


def listar_archivos_recuperados() -> List[str]:
    """Lista todos los archivos de recuperación disponibles"""
    data_dir = Path("data")
    archivos = list(data_dir.glob("datos_recuperados_*.json"))
    
    archivos_info = []
    for archivo in sorted(archivos, reverse=True):
        archivos_info.append({
            "archivo": str(archivo),
            "nombre": archivo.name,
            "tamano_mb": archivo.stat().st_size / (1024*1024),
            "modificado": datetime.fromtimestamp(archivo.stat().st_mtime).isoformat()
        })
    
    return archivos_info


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Listar archivos disponibles
    archivos = listar_archivos_recuperados()
    print("\n📁 Archivos de recuperación disponibles:\n")
    for info in archivos:
        print(f"  • {info['nombre']}")
        print(f"    Tamaño: {info['tamano_mb']:.2f} MB")
        print(f"    Modificado: {info['modificado']}\n")
    
    # Cargar el más reciente
    if archivos:
        ruta = archivos[0]["archivo"]
        print(f"\n📂 Cargando: {archivos[0]['nombre']}\n")
        resultado = cargar_datos_recuperados(ruta)
        
        print("[OK] RESULTADO:")
        print(json.dumps(resultado, indent=2, default=str)[:500] + "...")
