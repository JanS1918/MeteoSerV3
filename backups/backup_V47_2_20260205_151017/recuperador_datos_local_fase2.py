#!/usr/bin/env python3
"""
RECUPERACIÓN DE DATOS HISTÓRICOS - PHASE 2
============================================

Recupera datos del histórico local guardado y del sistema
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

# ═══════════════════════════════════════════════════════════════════════════════

def recuperar_datos_guardados_localmente():
    """Busca todos los datos guardados en los últimos 2 días"""
    
    logger.info("\n" + "="*80)
    logger.info("📁 FASE 1: RECUPERACIÓN DE DATOS GUARDADOS LOCALMENTE")
    logger.info("="*80 + "\n")
    
    data_dir = Path("data")
    datos_recuperados = []
    
    # Patrones de búsqueda
    patterns = [
        "*.json",  # Todos los JSON
        "**/*.json",  # Recursive
    ]
    
    for pattern in patterns:
        for file in data_dir.glob(pattern):
            # Evitar archivos de configuración
            if any(skip in file.name for skip in ["config", "indices", "settings"]):
                continue
            
            try:
                # Verificar que el archivo es reciente (últimas 48h)
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                edad_dias = (datetime.now() - mtime).days
                
                if edad_dias <= 2:
                    with open(file, 'r', encoding='utf-8') as fp:
                        contenido = json.load(fp)
                        datos_recuperados.append({
                            "archivo": str(file),
                            "tamaño_bytes": file.stat().st_size,
                            "modificado": mtime.isoformat(),
                            "datos": contenido if isinstance(contenido, dict) else {"contenido": contenido}
                        })
                        logger.info(f"✅ {file.name} ({file.stat().st_size} bytes)")
            except Exception as e:
                logger.warning(f"⚠️  {file.name}: {e}")
    
    logger.info(f"\n📊 Total recuperado: {len(datos_recuperados)} archivos")
    return datos_recuperados


def recuperar_historial_sensores():
    """Busca histórico específico de sensores"""
    
    logger.info("\n" + "="*80)
    logger.info("📊 FASE 2: HISTÓRICO DE SENSORES")
    logger.info("="*80 + "\n")
    
    historial = []
    data_dir = Path("data")
    
    # Buscar archivos de histórico de sensores
    sensor_files = list(data_dir.glob("sensor_*.json")) + \
                  list(data_dir.glob("*sensor*.json")) + \
                  list(data_dir.glob("*histórico*.json")) + \
                  list(data_dir.glob("*history*.json"))
    
    for file in sensor_files:
        try:
            with open(file, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                historial.append({
                    "archivo": str(file),
                    "tamaño": file.stat().st_size,
                    "registros": len(data) if isinstance(data, list) else 1,
                    "preview": str(data)[:200]
                })
                logger.info(f"✅ {file.name} ({len(data) if isinstance(data, list) else 1} registros)")
        except Exception as e:
            logger.warning(f"⚠️  {file.name}: {e}")
    
    return historial


def persistir_datos_recuperados(datos_locales, historial_sensores):
    """Guarda todos los datos recuperados en un archivo consolidado"""
    
    logger.info("\n" + "="*80)
    logger.info("💾 FASE 3: PERSISTENCIA DE DATOS CONSOLIDADOS")
    logger.info("="*80 + "\n")
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_dir = Path("data")
    
    # Archivo consolidado
    archivo_consolidado = data_dir / f"datos_recuperados_{timestamp_str}.json"
    
    datos_consolidados = {
        "timestamp_recuperacion": datetime.now().isoformat(),
        "periodo_ciego": {
            "inicio": (datetime.now() - timedelta(days=2)).isoformat(),
            "fin": datetime.now().isoformat(),
            "duracion_dias": 2
        },
        "sumario": {
            "total_archivos_locales": len(datos_locales),
            "total_registros_sensor": sum(h.get("registros", 1) for h in historial_sensores),
            "tamaño_total_bytes": sum(
                d.get("tamaño_bytes", 0) for d in datos_locales
            ) + sum(
                h.get("tamaño", 0) for h in historial_sensores
            )
        },
        "datos_locales": datos_locales,
        "historial_sensores": historial_sensores,
    }
    
    try:
        with open(archivo_consolidado, 'w', encoding='utf-8') as f:
            json.dump(datos_consolidados, f, indent=2, default=str)
        
        tamaño_mb = archivo_consolidado.stat().st_size / (1024*1024)
        logger.info(f"✅ Datos guardados en: {archivo_consolidado}")
        logger.info(f"   Tamaño: {tamaño_mb:.2f} MB")
        
        # Crear archivo de manifiesto
        archivo_manifiesto = data_dir / f"MANIFIESTO_RECUPERACIÓN_{timestamp_str}.txt"
        with open(archivo_manifiesto, 'w', encoding='utf-8') as f:
            f.write("MANIFIESTO DE RECUPERACIÓN DE DATOS\n")
            f.write("="*60 + "\n\n")
            f.write(f"Fecha recuperación: {datetime.now()}\n")
            f.write(f"Periodo ciego: 2 días\n")
            f.write(f"Archivos recuperados: {len(datos_locales)}\n")
            f.write(f"Registros de sensores: {datos_consolidados['sumario']['total_registros_sensor']}\n")
            f.write(f"Tamaño total: {tamaño_mb:.2f} MB\n\n")
            f.write("Archivos incluidos:\n")
            for d in datos_locales:
                f.write(f"  • {Path(d['archivo']).name} ({d['tamaño_bytes']} bytes)\n")
        
        logger.info(f"✅ Manifiesto: {archivo_manifiesto}")
        
        return archivo_consolidado
        
    except Exception as e:
        logger.error(f"❌ Error guardando datos: {e}")
        return None


def generar_reporte_final(archivo):
    """Genera reporte final de recuperación"""
    
    logger.info("\n" + "="*80)
    logger.info("📋 REPORTE FINAL DE RECUPERACIÓN")
    logger.info("="*80 + "\n")
    
    if archivo:
        with open(archivo, 'r') as f:
            datos = json.load(f)
        
        logger.info(f"✅ ÉXITO: Datos consolidados en {archivo.name}\n")
        logger.info(f"Sumario:")
        logger.info(f"  • Período ciego: 2 días")
        logger.info(f"  • Archivos locales recuperados: {datos['sumario']['total_archivos_locales']}")
        logger.info(f"  • Registros de sensores: {datos['sumario']['total_registros_sensor']}")
        logger.info(f"  • Tamaño total: {datos['sumario']['tamaño_total_bytes'] / (1024*1024):.2f} MB")
        logger.info(f"\nPróximo paso:")
        logger.info(f"  → Los datos están persistidos en el sistema")
        logger.info(f"  → Cargarlos en índices del bus usando:")
        logger.info(f"     from core.integration.data_recovery import cargar_datos_recuperados")
    else:
        logger.warning("⚠️  No se guardaron datos")
    
    logger.info("\n" + "="*80 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("\n🚀 RECUPERADOR DE DATOS HISTÓRICOS - FASE 2 (LOCAL)\n")
    
    # Fase 1: Datos locales
    datos_locales = recuperar_datos_guardados_localmente()
    
    # Fase 2: Historial sensores
    historial_sensores = recuperar_historial_sensores()
    
    # Fase 3: Persistencia
    archivo = persistir_datos_recuperados(datos_locales, historial_sensores)
    
    # Fase 4: Reporte
    generar_reporte_final(archivo)
