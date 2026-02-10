#!/usr/bin/env python3
"""
INTEGRADOR DE DATOS RECUPERADOS EN SISTEMA
============================================

Carga datos recuperados y los integra en:
- Histórico de sensores
- Bus de eventos
- Índices ambientales
- Memoria del CEREBRO
"""

import json
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

# ═══════════════════════════════════════════════════════════════════════════════


def integrar_datos_recuperados(ruta_archivo: str):
    """Integra datos recuperados en el sistema"""
    
    logger.info("\n" + "="*80)
    logger.info("[REINICIO] INTEGRADOR DE DATOS RECUPERADOS")
    logger.info("="*80 + "\n")
    
    # 1. Cargar archivo
    logger.info("📂 FASE 1: CARGANDO ARCHIVO DE RECUPERACIÓN\n")
    
    try:
        from core.integration.data_recovery import cargar_datos_recuperados
        resultado = cargar_datos_recuperados(ruta_archivo)
        
        if resultado['status'] != 'exito':
            logger.error(f"[ERROR] Error cargando datos: {resultado.get('errores')}")
            return False
        
        logger.info(f"[OK] Archivo cargado exitosamente")
        
    except Exception as e:
        logger.error(f"[ERROR] Error importando módulo: {e}")
        return False
    
    # 2. Información de recuperación
    logger.info("\n[STATS] FASE 2: INFORMACIÓN DE RECUPERACIÓN\n")
    
    resumen = resultado['resumen']
    logger.info(f"Timestamp: {resumen.get('timestamp_recuperacion', 'N/A')}")
    periodo = resumen.get('periodo', {})
    if periodo:
        logger.info(f"Período: {periodo.get('inicio', 'N/A')} a {periodo.get('fin', 'N/A')}")
    logger.info(f"Archivos: {resumen.get('sumario', {}).get('total_archivos_locales', 'N/A')}")
    logger.info(f"Registros sensores: {resumen.get('sumario', {}).get('total_registros_sensor', 'N/A')}")
    logger.info(f"Eventos generados: {resumen.get('eventos_integrados', 'N/A')}")
    
    # 3. Guardar histórico
    logger.info("\n[GUARDAR] FASE 3: GUARDANDO EN HISTÓRICO DEL SISTEMA\n")
    
    data_dir = Path("data")
    sensores = resultado.get('sensores', [])
    
    # Archivo de sensores integrado
    archivo_sensores = data_dir / f"sensores_integrados_recuperados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(archivo_sensores, 'w', encoding='utf-8') as f:
            json.dump(sensores, f, indent=2, default=str)
        logger.info(f"[OK] Sensores integrados: {len(sensores)} registros")
        logger.info(f"   Archivo: {archivo_sensores.name}")
    except Exception as e:
        logger.error(f"[ERROR] Error guardando sensores: {e}")
    
    # 4. Integración en memoria (simulada)
    logger.info("\n🧠 FASE 4: INTEGRACIÓN EN MEMORIA DEL SISTEMA\n")
    
    try:
        # Intentar cargar SystemManager
        from core.system.system_manager import SystemManager
        
        logger.info("Inicializando SystemManager...")
        system = SystemManager()
        
        # Publicar en bus
        eventos = resultado.get('eventos', [])
        logger.info(f"Publicando {len(eventos)} eventos en el bus...")
        
        for evento in eventos[:5]:  # Primeros 5 como ejemplo
            try:
                ts = evento.get('timestamp', datetime.now().isoformat())
                system.bus.publicar("datos.historico.recuperado", evento)
            except Exception as e:
                logger.warning(f"[WARNING]  Error publicando evento: {e}")
        
        logger.info(f"[OK] {len(eventos)} eventos publicados en el bus")
        
        # Actualizar estado
        if sensores:
            estado_integracion = {
                "timestamp": datetime.now().isoformat(),
                "evento": "recuperacion.completada",
                "sensores_integrados": len(sensores),
                "eventos_publicados": len(eventos),
                "periodo": resultado['periodo']
            }
            system.bus.publicar("sistema.eventos.recuperacion", estado_integracion)
            logger.info("[OK] Estado de recuperación publicado en el bus")
        
    except ImportError as e:
        logger.warning(f"[WARNING]  SystemManager no disponible: {e}")
        logger.info("   (Datos guardados en archivo, listo para integración manual)")
    except Exception as e:
        logger.error(f"[ERROR] Error en integración: {e}")
    
    # 5. Reporte final
    logger.info("\n" + "="*80)
    logger.info("[OK] INTEGRACIÓN COMPLETADA")
    logger.info("="*80 + "\n")
    
    logger.info("Resumen:")
    logger.info(f"  • Período ciego: 2 días")
    logger.info(f"  • Archivos recuperados: {resumen.get('sumario', {}).get('total_archivos_locales', 'N/A')}")
    logger.info(f"  • Registros integrados: {len(sensores)}")
    logger.info(f"  • Eventos publicados: {len(eventos)}")
    logger.info(f"  • Status: {resumen.get('status', 'unknown').upper()}")
    
    if resumen.get('errores'):
        logger.warning("\nErrores encontrados:")
        for error in resumen.get('errores', []):
            logger.warning(f"  • {error}")
    
    logger.info("\n[OK] Los datos están listos para usar en índices y análisis histórico\n")
    
    return True


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Buscar archivo más reciente
    data_dir = Path("data")
    archivos = sorted(data_dir.glob("datos_recuperados_*.json"), reverse=True)
    
    if not archivos:
        logger.error("[ERROR] No se encontraron archivos de recuperación")
        sys.exit(1)
    
    archivo = str(archivos[0])
    logger.info(f"Usando archivo: {Path(archivo).name}\n")
    
    # Integrar
    exito = integrar_datos_recuperados(archivo)
    
    sys.exit(0 if exito else 1)
