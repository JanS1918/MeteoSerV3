"""
📏 VALIDADOR DE PRECISIÓN

Verifica que mediciones y fórmulas cumplan precisión mínima requerida.
"""

import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger("meteoser.precision_validator")


class PrecisionValidator:
    """
    Valida que mediciones cumplan precisión mínima requerida para cada parámetro.
    
    Ejemplo:
    - Temperatura: ±0.1°C
    - Humedad: ±1%
    - Presión: ±0.01 hPa
    """
    
    # Precisión mínima requerida por parámetro
    PRECISION_REQUIREMENTS = {
        "temperatura": 0.1,              # ±0.1°C
        "temp": 0.1,
        "humedad_relativa": 1.0,         # ±1%
        "relative_humidity": 1.0,
        "rh": 1.0,
        "presion": 0.01,                 # ±0.01 hPa
        "pressure": 0.01,
        "p": 0.01,
        "velocidad_viento": 0.1,         # ±0.1 m/s
        "wind_speed": 0.1,
        "radiacion_solar": 5.0,          # ±5 W/m²
        "solar_radiation": 5.0,
        "sensacion_termica": 0.2,        # ±0.2°C
        "heat_index": 0.2,
        "punto_rocio": 0.1,              # ±0.1°C
        "dewpoint": 0.1,
        "evapotranspiracion": 0.1,       # ±0.1 mm
        "evapotranspiration": 0.1,
        "lluvia": 0.1,                   # ±0.1 mm
        "precipitation": 0.1,
        "visibilidad": 1.0,              # ±1 km
        "visibility": 1.0,
        "indice_uv": 0.1,                # ±0.1
        "uv_index": 0.1,
        "utci": 0.5,                     # ±0.5°C
    }
    
    def __init__(self):
        self.validation_log: list = []
    
    def validate_measurement(self,
                           parameter_name: str,
                           measured_value: float,
                           reference_value: float) -> Tuple[bool, str]:
        """
        Valida que medición cumpla precisión mínima.
        
        Args:
            parameter_name: Nombre del parámetro (ej: "temperatura")
            measured_value: Valor medido
            reference_value: Valor de referencia/esperado
        
        Returns:
            (is_valid, message)
        """
        
        required_precision = self.PRECISION_REQUIREMENTS.get(parameter_name.lower())
        
        if required_precision is None:
            # Parámetro desconocido - ser conservador
            return False, f"⚠️ Parámetro '{parameter_name}' no tiene precisión definida"
        
        error = abs(measured_value - reference_value)
        
        if error <= required_precision:
            self.validation_log.append({
                "parameter": parameter_name,
                "measured": measured_value,
                "reference": reference_value,
                "error": error,
                "required": required_precision,
                "status": "PASS"
            })
            return True, f"✅ PRECISIÓN OK: {parameter_name} error {error:.4f} <= {required_precision}"
        else:
            self.validation_log.append({
                "parameter": parameter_name,
                "measured": measured_value,
                "reference": reference_value,
                "error": error,
                "required": required_precision,
                "status": "FAIL"
            })
            return False, f"❌ PRECISIÓN INSUFICIENTE: {parameter_name} error {error:.4f} > {required_precision}"
    
    def validate_formula_output(self,
                              parameter_name: str,
                              min_output: float,
                              max_output: float,
                              measured_output: float) -> Tuple[bool, str]:
        """
        Valida que salida de fórmula esté en rango válido.
        
        Args:
            parameter_name: Nombre del parámetro
            min_output: Mínimo esperado
            max_output: Máximo esperado
            measured_output: Salida medida
        
        Returns:
            (is_valid, message)
        """
        
        if min_output <= measured_output <= max_output:
            return True, f"✅ RANGO OK: {parameter_name} = {measured_output} ∈ [{min_output}, {max_output}]"
        else:
            return False, f"❌ FUERA DE RANGO: {parameter_name} = {measured_output} ∉ [{min_output}, {max_output}]"
    
    def get_precision_for_parameter(self, parameter_name: str) -> Optional[float]:
        """Obtener precisión requerida para parámetro"""
        return self.PRECISION_REQUIREMENTS.get(parameter_name.lower())
    
    def get_all_precisions(self) -> Dict[str, float]:
        """Obtener todos los requisitos de precisión"""
        return self.PRECISION_REQUIREMENTS.copy()
    
    def get_validation_log(self) -> list:
        """Obtener log de validaciones"""
        return self.validation_log
    
    def clear_log(self):
        """Limpiar log"""
        self.validation_log = []


# Tests
if __name__ == "__main__":
    validator = PrecisionValidator()
    
    # ✅ VÁLIDA
    print("✅ MEDICIÓN VÁLIDA:")
    is_valid, msg = validator.validate_measurement("temperatura", 25.05, 25.0)
    print(f"  {msg}")
    
    # ❌ INVÁLIDA
    print("\n❌ MEDICIÓN INVÁLIDA:")
    is_valid, msg = validator.validate_measurement("temperatura", 25.5, 25.0)
    print(f"  {msg}")
    
    # ✅ RANGO VÁLIDO
    print("\n✅ RANGO VÁLIDO:")
    is_valid, msg = validator.validate_formula_output("sensacion_termica", -50, 100, 28.5)
    print(f"  {msg}")
    
    # ❌ RANGO INVÁLIDO
    print("\n❌ RANGO INVÁLIDO:")
    is_valid, msg = validator.validate_formula_output("sensacion_termica", -50, 100, 150)
    print(f"  {msg}")
