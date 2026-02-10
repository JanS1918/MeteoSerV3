"""
[GUARDIAN] PROTECTOR DE PARÁMETROS SAGRADOS

Bloquea modificaciones de los 50 parámetros sagrados del sistema.
"""

import logging
import time
from typing import Tuple, List, Dict, Any
from pathlib import Path

logger = logging.getLogger("meteoser.whitelist_enforcer")


class WhitelistEnforcer:
    """
    Bloquea modificaciones de los 50 parámetros sagrados definidos en WhitelistSagradosV30.
    
    Los 50 sagrados son:
    - FÍSICA DE ÉLITE (15): Hardy, OMM, REST2
    - SOBERANÍA GEOGRÁFICA (5): Gravedad, Altitud, Coordenadas
    - METEOROLOGÍA CRÍTICA (20): Temp, Humedad, Presión, Viento, Lluvia, Radiación
    - SEGURIDAD E ÍNDICES (10): CPU, Disco, Red, Salud del sistema
    """
    
    # Los 50 parámetros SAGRADOS - NO pueden modificarse
    SACRED_PARAMETERS = {
        # FÍSICA DE ÉLITE (15)
        "hardness_nist_value", "hardness_nist_variance",
        "omm_wmo_component_1", "omm_wmo_component_2", "omm_wmo_component_3",
        "rest2_irradiance_direct", "rest2_irradiance_diffuse",
        "liu_jordan_diffuse", "perez_diffuse",
        "erbs_decomposition", "spline_kt",
        "liu_jordan_extraterrestrial", "angstrom_angstrom_diffuse",
        "correlations_index", "validation_score",
        
        # SOBERANÍA GEOGRÁFICA (5)
        "latitude", "longitude", "altitude_srtm",
        "gravedad_local", "zona_geografica",
        
        # METEOROLOGÍA CRÍTICA (20)
        "temperatura", "humedad_relativa", "presion_atmosferica",
        "velocidad_viento", "direccion_viento",
        "radiacion_solar_global", "radiacion_ultravioleta",
        "lluvia_acumulada", "nieve",
        "punto_rocio", "visibilidad",
        "cobertura_nubosa", "altura_nube_base",
        "velocidad_rafaga", "viento_intermitente",
        "indice_radiacion", "indice_humedad",
        "calidad_aire_pm25", "calidad_aire_pm10",
        "presion_vapor_saturado",
        
        # SEGURIDAD E ÍNDICES (10)
        "cpu_load", "memoria_disponible", "espacio_disco",
        "conectividad_red", "numero_alertas_activas",
        "timestamp_ultimo_sync", "status_sensor_principal",
        "indice_riesgo_sistema", "version_firmware",
        "timestamp_calibracion_sensores",
    }
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self.base_dir = Path(base_dir)
        self.modification_log_path = self.base_dir / "data" / "whitelist_modifications_log.json"
        self.modification_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.modification_log: List[Dict[str, Any]] = []
        self._load_log()
    
    def validate_modification(self,
                            param_name: str,
                            old_value: Any,
                            new_value: Any,
                            modifier: str = "unknown") -> Tuple[bool, str]:
        """
        Valida si una modificación está permitida.
        
        Args:
            param_name: Nombre del parámetro
            old_value: Valor anterior
            new_value: Valor nuevo
            modifier: Quién intenta modificar
        
        Returns:
            (allowed, message)
        """
        
        param_normalized = param_name.lower().replace("-", "_")
        
        if param_normalized in self.SACRED_PARAMETERS:
            # [ERROR] BLOQUEADO
            self.modification_log.append({
                "timestamp": time.time(),
                "parameter": param_name,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "modifier": modifier,
                "status": "BLOCKED",
                "reason": "Parámetro sagrado protegido"
            })
            self._save_log()
            
            logger.critical(f"🚫 BLOQUEO SAGRADO: Intento de modificar {param_name} (modifier: {modifier})")
            return False, f"[ERROR] PARÁMETRO SAGRADO: '{param_name}' está protegido y NO puede modificarse"
        
        else:
            # [OK] PERMITIDO
            self.modification_log.append({
                "timestamp": time.time(),
                "parameter": param_name,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "modifier": modifier,
                "status": "ALLOWED",
                "reason": "Parámetro no es sagrado"
            })
            self._save_log()
            
            return True, f"[OK] Modificación permitida: {param_name}"
    
    def is_sacred(self, param_name: str) -> bool:
        """¿Es parámetro sagrado?"""
        return param_name.lower().replace("-", "_") in self.SACRED_PARAMETERS
    
    def get_sacred_parameters(self) -> set:
        """Obtener todos los parámetros sagrados"""
        return self.SACRED_PARAMETERS.copy()
    
    def get_modification_log(self) -> List[Dict[str, Any]]:
        """Obtener log de intentos de modificación"""
        return self.modification_log.copy()
    
    def get_blocked_attempts(self) -> List[Dict[str, Any]]:
        """Obtener solo intentos bloqueados"""
        return [log for log in self.modification_log if log["status"] == "BLOCKED"]
    
    def clear_log(self):
        """Limpiar log"""
        self.modification_log = []
        self._save_log()
    
    def _load_log(self):
        """Cargar log de archivo"""
        try:
            import json
            if self.modification_log_path.exists():
                with open(self.modification_log_path, 'r') as f:
                    data = json.load(f)
                    self.modification_log = data.get("modifications", [])
        except Exception as e:
            logger.warning(f"No se pudo cargar log de modificaciones: {e}")
    
    def _save_log(self):
        """Guardar log en archivo"""
        try:
            import json
            with open(self.modification_log_path, 'w') as f:
                json.dump({"modifications": self.modification_log}, f, indent=2)
        except Exception as e:
            logger.warning(f"No se pudo guardar log de modificaciones: {e}")


# Tests
if __name__ == "__main__":
    enforcer = WhitelistEnforcer()
    
    # [OK] PERMITIDO
    print("[OK] MODIFICACIÓN PERMITIDA:")
    allowed, msg = enforcer.validate_modification("my_custom_param", 10, 20, modifier="algorithm")
    print(f"  {msg}")
    
    # [ERROR] BLOQUEADO
    print("\n[ERROR] MODIFICACIÓN BLOQUEADA:")
    allowed, msg = enforcer.validate_modification("temperatura", 25.0, 30.0, modifier="malicious_code")
    print(f"  {msg}")
    
    print(f"\n[STATS] Total sagrados: {len(enforcer.get_sacred_parameters())}")
    print(f"[STATS] Intentos bloqueados: {len(enforcer.get_blocked_attempts())}")
