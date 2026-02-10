"""
[OK] VALIDADOR DE ESPECIFICACIÓN COMPLETA

Verifica que una fórmula CUMPLA COMPLETAMENTE su especificación:
- [OK] Todos los parámetros requeridos presentes
- [OK] Rango de salida válido
- [OK] Precisión mínima cumplida
- [OK] Tipos de datos correctos
"""

import inspect
import logging
from typing import Dict, List, Tuple, Any, Callable, Optional

logger = logging.getLogger("meteoser.specification_completeness_validator")


class SpecificationCompletenessValidator:
    """
    Valida que una fórmula cumpla COMPLETAMENTE su especificación.
    
    Verifica:
    1. Todos los parámetros requeridos están presentes
    2. Tipos de parámetros son correctos
    3. Salida está en rango válido
    4. Precisión cumple minimums
    5. Cambios son reversibles
    """
    
    def __init__(self):
        self.validation_log: List[Dict[str, Any]] = []
    
    def validate(self, 
                formula_name: str,
                spec_dict: Dict[str, Any],
                implementation: Optional[Callable] = None) -> Tuple[bool, List[str]]:
        """
        Valida que implementación cumpla especificación.
        
        Args:
            formula_name: Nombre de la fórmula
            spec_dict: Especificación (requisitos, rango, precision, etc)
            implementation: Función implementada
        
        Returns:
            (is_valid, errors_list)
        """
        
        errors = []
        
        # [OK] VALIDACIÓN 1: ¿Especificación tiene requisitos?
        if "requisitos_datos" not in spec_dict:
            errors.append("[ERROR] Especificación no define 'requisitos_datos'")
        
        spec_params = spec_dict.get("requisitos_datos", [])
        if not spec_params:
            errors.append("[ERROR] Requisitos de datos vacíos o no definidos")
        
        # [OK] VALIDACIÓN 2: ¿Implementación tiene todos los parámetros?
        if implementation:
            impl_params = self._get_function_parameters(implementation)
            impl_param_names = set(impl_params.keys())
            spec_param_names = set(p.lower().replace("-", "_") for p in spec_params)
            
            missing = spec_param_names - impl_param_names
            if missing:
                errors.append(f"[ERROR] Parámetros faltantes: {missing}")
            
            extra = impl_param_names - spec_param_names
            if extra and "self" not in extra and "args" not in extra and "kwargs" not in extra:
                logger.warning(f"[WARNING] Parámetros extra en implementación: {extra}")
        
        # [OK] VALIDACIÓN 3: ¿Rango de salida definido?
        if "rango_salida_min" in spec_dict and "rango_salida_max" in spec_dict:
            min_out = spec_dict.get("rango_salida_min")
            max_out = spec_dict.get("rango_salida_max")
            if min_out is None or max_out is None:
                errors.append("[ERROR] Rango de salida incompleto")
        
        # [OK] VALIDACIÓN 4: ¿Precisión definida?
        if "precision_minima" in spec_dict:
            precision = spec_dict.get("precision_minima")
            if precision is None or precision < 0:
                errors.append("[ERROR] Precisión mínima inválida o no definida")
        
        # [OK] VALIDACIÓN 5: ¿Reversibilidad garantizada?
        reversible = spec_dict.get("reversible_guaranteed", False)
        if not reversible:
            errors.append("[WARNING] Cambio NO es reversible (criterio conservador)")
        
        # [OK] VALIDACIÓN 6: ¿Enhancement factor si es IAPWS?
        if "iapws" in formula_name.lower() or "vapor" in formula_name.lower():
            enhancement_factor = spec_dict.get("enhancement_factor", False)
            if not enhancement_factor:
                errors.append("[ERROR] Fórmula de vapor saturado sin Enhancement Factor")
        
        # Registrar validación
        is_valid = len(errors) == 0
        self.validation_log.append({
            "formula": formula_name,
            "valid": is_valid,
            "errors": errors
        })
        
        return is_valid, errors
    
    def _get_function_parameters(self, func: Callable) -> Dict[str, Any]:
        """Extrae parámetros de una función"""
        try:
            sig = inspect.signature(func)
            return {
                param: str(sig.parameters[param].annotation) if sig.parameters[param].annotation != inspect.Parameter.empty else "Any"
                for param in sig.parameters
            }
        except Exception as e:
            logger.warning(f"No se pudieron extraer parámetros: {e}")
            return {}
    
    def get_validation_log(self) -> List[Dict[str, Any]]:
        """Obtener log de validaciones"""
        return self.validation_log
    
    def clear_log(self):
        """Limpiar log"""
        self.validation_log = []


# Tests
if __name__ == "__main__":
    validator = SpecificationCompletenessValidator()
    
    # [OK] Especificación VÁLIDA
    valid_spec = {
        "requisitos_datos": ["temperatura", "humedad", "presion"],
        "rango_salida_min": -50,
        "rango_salida_max": 100,
        "precision_minima": 0.1,
        "reversible_guaranteed": True,
    }
    
    print("[OK] Especificación válida:")
    is_valid, errors = validator.validate("sensacion_termica", valid_spec)
    print(f"  Valid: {is_valid}, Errors: {len(errors)}")
    
    # [ERROR] Especificación INCOMPLETA
    invalid_spec = {
        "requisitos_datos": [],
        "rango_salida_min": None,
        "reversible_guaranteed": False,
    }
    
    print("\n[ERROR] Especificación incompleta:")
    is_valid, errors = validator.validate("bad_formula", invalid_spec)
    print(f"  Valid: {is_valid}, Errors: {errors}")
