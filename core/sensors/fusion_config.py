"""
═══════════════════════════════════════════════════════════════════════════════
MÓDULO: CONFIGURACIÓN DINÁMICA DE FUSIÓN DE SENSORES
═══════════════════════════════════════════════════════════════════════════════

Carga y gestiona la configuración JSON para ponderaciones adaptativas.
Permite recargar configuración sin reiniciar servidor.
"""

import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfiguracionFusion:
    """Gestor de configuración de fusión de sensores."""
    
    _instancia = None
    _config_cache = None
    _ultima_carga = None
    
    def __new__(cls):
        """Singleton pattern para garantizar una instancia única."""
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia
    
    def __init__(self):
        """Inicializar gestor de configuración."""
        if not self._inicializado:
            self.ruta_config = Path('config/sensor_fusion_config.json')
            self._config_cache = None
            self._ultima_carga = None
            self._inicializado = True
            self._cargar_config()
    
    def _cargar_config(self) -> bool:
        """Cargar configuración desde archivo JSON."""
        try:
            if not self.ruta_config.exists():
                logger.warning(f"[CONFIG] No existe {self.ruta_config}, usando defaults")
                self._config_cache = self._defaults()
                return False
            
            with open(self.ruta_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self._config_cache = config
            self._ultima_carga = datetime.now()
            logger.info(f"[CONFIG] Configuración cargada desde {self.ruta_config}")
            return True
        
        except json.JSONDecodeError as e:
            logger.error(f"[CONFIG] Error JSON en {self.ruta_config}: {e}")
            self._config_cache = self._defaults()
            return False
        except Exception as e:
            logger.error(f"[CONFIG] Error cargando {self.ruta_config}: {e}")
            self._config_cache = self._defaults()
            return False
    
    def recargar(self) -> bool:
        """Recargar configuración desde archivo (útil para cambios sin reinicio)."""
        logger.info("[CONFIG] Recargando configuración...")
        return self._cargar_config()
    
    def obtener(self, clave: str, default: Any = None) -> Any:
        """
        Obtener valor de configuración por clave.
        
        Ejemplos:
            - obtener('ponderaciones.confort.temperatura.wh65')
            - obtener('umbrales_anomalia.temperatura_delta_max_celsius')
        """
        if self._config_cache is None:
            self._cargar_config()
        
        partes = clave.split('.')
        valor = self._config_cache
        
        try:
            for parte in partes:
                valor = valor[parte]
            return valor
        except (KeyError, TypeError):
            logger.warning(f"[CONFIG] Clave '{clave}' no encontrada, usando default")
            return default
    
    def obtener_ponderaciones(self, contexto: str) -> Optional[Dict]:
        """Obtener dict de ponderaciones para contexto específico."""
        return self.obtener(f'ponderaciones.{contexto}')
    
    def obtener_peso_temperatura(self, contexto: str, sensor: str) -> float:
        """
        Obtener peso (0-1) para temperatura de sensor en contexto.
        
        Args:
            contexto: 'confort', 'lluvia', 'rocio_niebla', etc.
            sensor: 'wh65' o 'wh31'
        
        Returns:
            Peso (0-1), default 0.5 si no encontrado
        """
        return self.obtener(
            f'ponderaciones.{contexto}.temperatura.{sensor}',
            default=0.5
        )
    
    def obtener_peso_humedad(self, contexto: str, sensor: str) -> float:
        """
        Obtener peso (0-1) para humedad de sensor en contexto.
        
        Args:
            contexto: 'confort', 'lluvia', 'rocio_niebla', etc.
            sensor: 'wh65' o 'wh31'
        
        Returns:
            Peso (0-1), default 0.5 si no encontrado
        """
        return self.obtener(
            f'ponderaciones.{contexto}.humedad.{sensor}',
            default=0.5
        )
    
    def obtener_umbral_anomalia_temperatura(self) -> float:
        """Obtener umbral máximo de diferencia de temperatura en °C."""
        return self.obtener('umbrales_anomalia.temperatura_delta_max_celsius', default=15.0)
    
    def obtener_umbral_anomalia_humedad(self) -> float:
        """Obtener umbral máximo de diferencia de humedad en %."""
        return self.obtener('umbrales_anomalia.humedad_delta_max_porcentaje', default=40.0)
    
    def obtener_umbral_microclima_temperatura(self) -> float:
        """Obtener diferencia mínima de temperatura para detectar microclima."""
        return self.obtener('umbrales_microclima.temperatura_delta_min_celsius', default=3.0)
    
    def obtener_umbral_microclima_humedad(self) -> float:
        """Obtener diferencia mínima de humedad para detectar microclima."""
        return self.obtener('umbrales_microclima.humedad_delta_min_porcentaje', default=15.0)
    
    def esta_habilitado_indice(self, nombre_indice: str) -> bool:
        """Verificar si un índice tiene habilitada fusión."""
        return self.obtener(f'indices_integracion.{nombre_indice}.habilitado', default=False)
    
    def obtener_contexto_indice(self, nombre_indice: str) -> str:
        """Obtener contexto de ponderación para un índice."""
        return self.obtener(f'indices_integracion.{nombre_indice}.contexto', default='prediccion_general')
    
    def obtener_ruta_log_decisiones(self) -> str:
        """Obtener ruta del archivo de log de decisiones."""
        return self.obtener('logging.archivo_decisiones', default='data/fusion_decisions.jsonl')
    
    def obtener_ruta_log_alertas(self) -> str:
        """Obtener ruta del archivo de log de alertas."""
        return self.obtener('logging.archivo_alertas', default='data/fusion_alerts.jsonl')
    
    def debe_guardar_decisiones(self) -> bool:
        """Verificar si se deben guardar decisiones."""
        return self.obtener('logging.guardar_decisiones', default=True)
    
    def debe_guardar_alertas(self) -> bool:
        """Verificar si se deben guardar alertas."""
        return self.obtener('logging.guardar_alertas', default=True)
    
    def exportar_json(self) -> Dict:
        """Exportar configuración actual como dict."""
        if self._config_cache is None:
            self._cargar_config()
        return self._config_cache.copy()
    
    def actualizar_dinamico(self, nuevos_valores: Dict) -> bool:
        """
        Actualizar configuración con nuevos valores (merge shallow).
        
        Útil para actualizar ponderaciones desde API sin guardar en disco.
        """
        try:
            if self._config_cache is None:
                self._cargar_config()
            
            def merge_dict(original, nuevo):
                """Merge shallow de dicts."""
                for clave, valor in nuevo.items():
                    if isinstance(valor, dict) and clave in original:
                        if isinstance(original[clave], dict):
                            merge_dict(original[clave], valor)
                        else:
                            original[clave] = valor
                    else:
                        original[clave] = valor
            
            merge_dict(self._config_cache, nuevos_valores)
            logger.info(f"[CONFIG] Configuración actualizada dinámicamente")
            return True
        except Exception as e:
            logger.error(f"[CONFIG] Error en actualización dinámica: {e}")
            return False
    
    def guardar_cambios(self) -> bool:
        """Guardar cambios de configuración en disk."""
        try:
            self.ruta_config.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ruta_config, 'w', encoding='utf-8') as f:
                json.dump(self._config_cache, f, indent=2, ensure_ascii=False)
            logger.info(f"[CONFIG] Cambios guardados en {self.ruta_config}")
            return True
        except Exception as e:
            logger.error(f"[CONFIG] Error guardando cambios: {e}")
            return False
    
    @staticmethod
    def _defaults() -> Dict:
        """Retornar configuración por defecto si no se puede cargar."""
        return {
            'ponderaciones': {
                'confort': {
                    'temperatura': {'wh65': 0.3, 'wh31': 0.7},
                    'humedad': {'wh65': 0.4, 'wh31': 0.6},
                },
                'lluvia': {
                    'temperatura': {'wh65': 0.7, 'wh31': 0.3},
                    'humedad': {'wh65': 0.65, 'wh31': 0.35},
                },
                'alerta': {
                    'temperatura': {'wh65': 0.5, 'wh31': 0.5},
                    'humedad': {'wh65': 0.5, 'wh31': 0.5},
                },
                'microclima': {
                    'temperatura': {'wh65': 0.5, 'wh31': 0.5},
                    'humedad': {'wh65': 0.5, 'wh31': 0.5},
                },
                'rocio_niebla': {
                    'temperatura': {'wh65': 0.4, 'wh31': 0.6},
                    'humedad': {'wh65': 0.35, 'wh31': 0.65},
                },
                'prediccion_general': {
                    'temperatura': {'wh65': 0.6, 'wh31': 0.4},
                    'humedad': {'wh65': 0.55, 'wh31': 0.45},
                },
            },
            'umbrales_anomalia': {
                'temperatura_delta_max_celsius': 15.0,
                'humedad_delta_max_porcentaje': 40.0,
            },
            'logging': {
                'archivo_decisiones': 'data/fusion_decisions.jsonl',
                'guardar_decisiones': True,
            }
        }


# Instancia singleton global
configuracion = ConfiguracionFusion()
