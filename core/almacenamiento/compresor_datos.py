"""
═══════════════════════════════════════════════════════════════════════════════
STEP 25: COMPRESIÓN Y ALMACENAMIENTO EFICIENTE
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Comprimir datos históricos
  - Reducir uso de disco
  - Archivado automático
  - Rotación de logs

Fecha: 2026-02-11
"""

import logging
import gzip
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfiguracionAlmacenamiento:
    """Configuración de almacenamiento."""
    directorio_datos: str = "data/"
    max_edad_dias_sin_comprimir: int = 7
    max_edad_dias_antes_eliminar: int = 90
    umbral_tamaño_mb: int = 100  # Comprimir si > 100MB


class CompresorDatos:
    """Compresor de datos históricos."""
    
    def __init__(self, config: ConfiguracionAlmacenamiento = None):
        self.config = config or ConfiguracionAlmacenamiento()
        self.estadisticas = {
            'archivos_comprimidos': 0,
            'bytes_ahorrados': 0,
            'tasa_compresion': 0.0
        }
    
    def comprimir_archivo(self, ruta_archivo: str) -> bool:
        """Comprime un archivo con gzip."""
        
        try:
            ruta_path = Path(ruta_archivo)
            
            if not ruta_path.exists():
                logger.warning(f"[COMPRESS] Archivo no existe: {ruta_archivo}")
                return False
            
            # Si ya está comprimido, saltar
            if ruta_path.suffix == '.gz':
                return True
            
            # Obtener tamaño original
            tamaño_original = ruta_path.stat().st_size
            
            # Comprimir
            ruta_comprimida = f"{ruta_archivo}.gz"
            
            with open(ruta_archivo, 'rb') as f_in:
                with gzip.open(ruta_comprimida, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            # Obtener tamaño comprimido
            tamaño_comprimido = Path(ruta_comprimida).stat().st_size
            
            # Calcular ahorro
            ahorro = tamaño_original - tamaño_comprimido
            tasa = (1 - tamaño_comprimido / tamaño_original) * 100
            
            # Eliminar original
            ruta_path.unlink()
            
            # Actualizar estadísticas
            self.estadisticas['archivos_comprimidos'] += 1
            self.estadisticas['bytes_ahorrados'] += ahorro
            
            logger.info(
                f"[COMPRESS] {ruta_path.name}: "
                f"{tamaño_original / 1024:.1f}KB → "
                f"{tamaño_comprimido / 1024:.1f}KB "
                f"({tasa:.1f}% reducción)"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error comprimiendo {ruta_archivo}: {e}")
            return False
    
    def descomprimir_archivo(self, ruta_archivo_gz: str) -> bool:
        """Descomprime un archivo."""
        
        try:
            ruta_path = Path(ruta_archivo_gz)
            
            if not ruta_path.exists():
                logger.warning(f"[COMPRESS] Archivo no existe: {ruta_archivo_gz}")
                return False
            
            # Obtener nombre sin .gz
            ruta_original = str(ruta_path).replace('.gz', '')
            
            with gzip.open(ruta_archivo_gz, 'rb') as f_in:
                with open(ruta_original, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            logger.info(f"[COMPRESS] Descomprimido: {ruta_path.name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error descomprimiendo {ruta_archivo_gz}: {e}")
            return False
    
    def archivos_para_comprimir(self, directorio: str) -> List[str]:
        """Encuentra archivos que deben comprimirse."""
        
        archivos = []
        
        try:
            dir_path = Path(directorio)
            if not dir_path.exists():
                return archivos
            
            ahora = datetime.now()
            
            for archivo in dir_path.glob('*.json'):
                # Ignorar archivos ya comprimidos
                if archivo.suffix == '.gz':
                    continue
                
                # Obtener edad del archivo
                timestamp_mod = datetime.fromtimestamp(archivo.stat().st_mtime)
                edad_dias = (ahora - timestamp_mod).days
                
                # Obtener tamaño en MB
                tamaño_mb = archivo.stat().st_size / (1024 * 1024)
                
                # Criterios de compresión
                si_es_antiguo = edad_dias >= self.config.max_edad_dias_sin_comprimir
                si_es_grande = tamaño_mb >= self.config.umbral_tamaño_mb
                
                if si_es_antiguo or si_es_grande:
                    archivos.append(str(archivo))
        
        except Exception as e:
            logger.error(f"Error buscando archivos para comprimir: {e}")
        
        return archivos
    
    def comprimir_lote(self, directorio: str) -> Dict[str, int]:
        """Comprime múltiples archivos."""
        
        archivos = self.archivos_para_comprimir(directorio)
        
        resultados = {
            'exitosos': 0,
            'fallidos': 0,
            'total_procesados': len(archivos)
        }
        
        for archivo in archivos:
            if self.comprimir_archivo(archivo):
                resultados['exitosos'] += 1
            else:
                resultados['fallidos'] += 1
        
        return resultados


class GestorArchivoHistorico:
    """Gestiona archivado y rotación de archivos."""
    
    def __init__(self, config: ConfiguracionAlmacenamiento = None):
        self.config = config or ConfiguracionAlmacenamiento()
        self.compresor = CompresorDatos(config)
    
    def archibvar_datos_historicos(self, directorio: str) -> Dict[str, Any]:
        """Archiva datos históricos."""
        
        try:
            # Primero, comprimir archivos antiguos
            resultado_compresion = self.compresor.comprimir_lote(directorio)
            
            # Luego, eliminar archivos muy antiguos
            resultado_limpieza = self._eliminar_archivos_muy_antiguos(directorio)
            
            return {
                'estado': 'EXITOSO',
                'compresion': resultado_compresion,
                'limpieza': resultado_limpieza,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error archivando datos: {e}")
            return {'estado': 'ERROR', 'detalles': str(e)}
    
    def _eliminar_archivos_muy_antiguos(self, directorio: str) -> Dict[str, int]:
        """Elimina archivos muy antiguos."""
        
        resultados = {'eliminados': 0, 'fallos': 0}
        
        try:
            dir_path = Path(directorio)
            if not dir_path.exists():
                return resultados
            
            ahora = datetime.now()
            max_edad = timedelta(days=self.config.max_edad_dias_antes_eliminar)
            
            for archivo in dir_path.glob('**/*.json.gz'):
                timestamp_mod = datetime.fromtimestamp(archivo.stat().st_mtime)
                edad = ahora - timestamp_mod
                
                if edad > max_edad:
                    try:
                        archivo.unlink()
                        resultados['eliminados'] += 1
                    except Exception as e:
                        logger.warning(f"Error eliminando {archivo}: {e}")
                        resultados['fallos'] += 1
        
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
        
        return resultados
    
    def obtener_estadisticas_almacenamiento(self, 
                                           directorio: str) -> Dict[str, Any]:
        """Obtiene estadísticas de uso de disco."""
        
        try:
            dir_path = Path(directorio)
            
            if not dir_path.exists():
                return {'estado': 'ERROR', 'directorio_no_existe': True}
            
            tamaño_total = 0
            tamaño_comprimido = 0
            archivos_json = 0
            archivos_gz = 0
            
            for archivo in dir_path.glob('**/*'):
                if archivo.is_file():
                    tamaño = archivo.stat().st_size
                    tamaño_total += tamaño
                    
                    if archivo.suffix == '.json':
                        archivos_json += 1
                    elif archivo.suffix == '.gz':
                        archivos_gz += 1
                        tamaño_comprimido += tamaño
            
            return {
                'directorio': directorio,
                'tamaño_total_mb': round(tamaño_total / (1024 * 1024), 2),
                'tamaño_comprimido_mb': round(tamaño_comprimido / (1024 * 1024), 2),
                'archivos_json': archivos_json,
                'archivos_gz': archivos_gz,
                'tasa_compresion': f"{(tamaño_comprimido / tamaño_total * 100):.1f}%" if tamaño_total > 0 else "N/A",
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'estado': 'ERROR', 'detalles': str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_gestor_archivo_historic_instance = None


def obtener_gestor_archivo_historico() -> GestorArchivoHistorico:
    """Obtiene instancia singleton."""
    global _gestor_archivo_historic_instance
    if _gestor_archivo_historic_instance is None:
        _gestor_archivo_historic_instance = GestorArchivoHistorico()
    
    return _gestor_archivo_historic_instance


def iniciar_gestor_archivado() -> Dict[str, Any]:
    """Inicializa gestor de archivado."""
    try:
        gestor = obtener_gestor_archivo_historico()
        
        contexto = {
            'estado': 'ACTIVO',
            'directorio_datos': gestor.config.directorio_datos,
            'max_edad_dias_sin_comprimir': gestor.config.max_edad_dias_sin_comprimir,
            'max_edad_dias_antes_eliminar': gestor.config.max_edad_dias_antes_eliminar,
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info("[COMPRESS] Gestor de archivado iniciado")
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando archivado: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
