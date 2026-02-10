"""
Validador de Especificaciones - PROACTIVO
Detecta gaps entre especificación y implementación en tiempo de startup
"""

import inspect
import logging
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass

from core.bus.parametros_canonicos import (
    normalizar_parametro_entrada,
    normalizar_lista_parametros_entrada,
)

logger = logging.getLogger("spec_validation_engine")

@dataclass
class ValidationResult:
    """Resultado de validación de una fórmula"""
    formula_name: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    spec_params: List[str]
    impl_params: List[str]
    missing_params: List[str]


class SpecValidationEngine:
    """Motor de validación proactivo de especificaciones"""
    
    def __init__(self):
        self.results: Dict[str, ValidationResult] = {}
        self.fatal_errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all_formulas(self, formula_hierarchy: Dict, implementations: Dict) -> Dict[str, ValidationResult]:
        """
        Valida todas las fórmulas contra su especificación
        
        Args:
            formula_hierarchy: Dict con especificaciones (de core/bus/formula_hierarchy.py)
            implementations: Dict con funciones implementadas
        
        Returns:
            Dict de ValidationResult por fórmula
        """
        print("\n" + "="*80)
        print("🔍 VALIDACIÓN PROACTIVA DE ESPECIFICACIONES")
        print("="*80)
        
        for param_name, levels in formula_hierarchy.items():
            for level, spec in levels.items():
                formula_name = spec.nombre_tecnico
                
                result = self._validate_single_formula(
                    formula_name=formula_name,
                    spec=spec,
                    implementations=implementations
                )
                
                self.results[formula_name] = result
                self._print_result(formula_name, result)
        
        return self.results
    
    def _validate_single_formula(self, formula_name: str, spec, implementations: Dict) -> ValidationResult:
        """Valida una fórmula específica"""
        
        errors = []
        warnings = []
        spec_params = spec.requisitos_datos if hasattr(spec, 'requisitos_datos') else []
        
        # 1. ¿Existe la implementación?
        if formula_name not in implementations:
            errors.append(f"❌ No existe implementación")
            return ValidationResult(
                formula_name=formula_name,
                is_valid=False,
                errors=errors,
                warnings=warnings,
                spec_params=spec_params,
                impl_params=[],
                missing_params=spec_params
            )
        
        impl_func = implementations[formula_name]
        
        # 2. ¿Qué parámetros acepta?
        try:
            sig = inspect.signature(impl_func)
            impl_params = list(sig.parameters.keys())
        except Exception as e:
            errors.append(f"❌ No se puede inspeccionar: {e}")
            return ValidationResult(
                formula_name=formula_name,
                is_valid=False,
                errors=errors,
                warnings=warnings,
                spec_params=spec_params,
                impl_params=[],
                missing_params=spec_params
            )
        
        # 3. Normalización de lenguaje (canónico)
        normalized_spec_params = normalizar_lista_parametros_entrada(spec_params)
        normalized_impl_params = normalizar_lista_parametros_entrada(impl_params)

        non_canonical_spec = [p for p in spec_params if normalizar_parametro_entrada(p) != p]
        non_canonical_impl = [p for p in impl_params if normalizar_parametro_entrada(p) != p]

        if non_canonical_spec:
            warnings.append(
                f"⚠️ Parámetros no canónicos en spec: {non_canonical_spec}"
            )
        if non_canonical_impl:
            warnings.append(
                f"⚠️ Parámetros no canónicos en implementación: {non_canonical_impl}"
            )

        # 4. ¿Tiene todos los parámetros requeridos?
        spec_params_set = set(normalized_spec_params)
        impl_params_set = set(normalized_impl_params)
        
        missing_params = list(spec_params_set - impl_params_set)
        extra_params = list(impl_params_set - spec_params_set)
        
        if missing_params:
            errors.append(f"❌ Parámetros requeridos faltantes: {missing_params}")
        
        if extra_params:
            warnings.append(f"⚠️ Parámetros adicionales no en spec: {extra_params}")
        
        # 5. Validaciones específicas por fórmula
        if "presion_vapor" in formula_name:
            self._validate_vapor_pressure(formula_name, impl_func, spec, errors, warnings)
        
        if "densidad" in formula_name:
            self._validate_density(formula_name, impl_func, spec, errors, warnings)
        
        if "utci" in formula_name:
            self._validate_utci(formula_name, impl_func, spec, errors, warnings)
        
        # 6. ¿Está documentada correctamente?
        doc = impl_func.__doc__ or ""
        if not doc:
            warnings.append(f"⚠️ Sin documentación")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            formula_name=formula_name,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            spec_params=spec_params,
            impl_params=impl_params,
            missing_params=missing_params
        )
    
    def _validate_vapor_pressure(self, name: str, func: Callable, spec, errors: List, warnings: List):
        """Validaciones específicas para presión de vapor"""
        
        # Si dice que calcula presion_vapor_real, DEBE tener Enhancement Factor
        doc = (func.__doc__ or "").lower()
        
        if "real" in doc or "vapor actual" in doc:
            # Debería tener Enhancement Factor
            if "enhancement" not in doc and "factor" not in doc:
                warnings.append(
                    f"⚠️ Calcula presión vapor 'real' pero no menciona Enhancement Factor"
                )
        
        # Si está en PROFESIONAL/ESTÁNDAR pero no en ELITE, validar que es alternativa válida
        if "iapws" in name.lower():
            # IAPWS debería aceptar [temperatura, humedad, presion]
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            params_norm = normalizar_lista_parametros_entrada(params)
            
            if "humedad" not in params_norm:
                if "saturacion" not in name.lower():  # Si no es solo saturación
                    warnings.append(
                        f"⚠️ IAPWS sin parámetro de humedad - verificar si está incompleta"
                    )
    
    def _validate_density(self, name: str, func: Callable, spec, errors: List, warnings: List):
        """Validaciones específicas para densidad"""
        doc = (func.__doc__ or "").lower()
        
        # Densidad OMM debería mencionar "temperatura virtual"
        if "omm" in name.lower() or "virtual" in name.lower():
            if "virtual" not in doc:
                warnings.append(f"⚠️ Densidad OMM sin mención de temperatura virtual")
    
    def _validate_utci(self, name: str, func: Callable, spec, errors: List, warnings: List):
        """Validaciones específicas para UTCI"""
        doc = (func.__doc__ or "").lower()
        
        # UTCI debería incluir radiación
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        params_norm = normalizar_lista_parametros_entrada(params)
        
        if "radiacion" not in params_norm:
            warnings.append(f"⚠️ UTCI sin parámetro de radiación - verificar")
    
    def _print_result(self, name: str, result: ValidationResult):
        """Imprime resultado de validación"""
        
        if result.is_valid and not result.warnings:
            status = "✅"
            color = ""
        elif result.is_valid and result.warnings:
            status = "⚠️"
            color = ""
        else:
            status = "❌"
            color = ""
        
        print(f"{status} {name}")
        
        if result.errors:
            for error in result.errors:
                print(f"     {error}")
                self.fatal_errors.append(f"{name}: {error}")
        
        if result.warnings:
            for warning in result.warnings:
                print(f"     {warning}")
                self.warnings.append(f"{name}: {warning}")
    
    def generate_report(self) -> Tuple[int, int]:
        """Genera reporte final y retorna (fatal_count, warning_count)"""
        
        print("\n" + "="*80)
        print("📊 REPORTE DE VALIDACIÓN")
        print("="*80)
        
        total = len(self.results)
        valid = sum(1 for r in self.results.values() if r.is_valid)
        invalid = total - valid
        
        print(f"\n✅ Válidas:    {valid}/{total}")
        print(f"❌ Inválidas:   {invalid}/{total}")
        print(f"⚠️ Warnings:   {len(self.warnings)}")
        
        if self.fatal_errors:
            print(f"\n🚨 ERRORES FATALES ({len(self.fatal_errors)}):")
            for error in self.fatal_errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️ ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Max 10
                print(f"   • {warning}")
            if len(self.warnings) > 10:
                print(f"   ... y {len(self.warnings) - 10} más")
        
        print()
        
        return len(self.fatal_errors), len(self.warnings)
    
    def block_incomplete_formulas(self) -> List[str]:
        """Retorna lista de fórmulas que DEBEN ser bloqueadas (incompletas)"""
        
        blocked = []
        
        for name, result in self.results.items():
            if not result.is_valid:
                blocked.append(name)
                logger.error(f"BLOQUEADA: {name} - {result.errors}")
        
        return blocked


def validate_spec_on_startup(formula_hierarchy: Dict, implementations: Dict):
    """
    Ejecutar validación en startup de main_asgi.py
    """
    validator = SpecValidationEngine()
    validator.validate_all_formulas(formula_hierarchy, implementations)
    fatal_count, warning_count = validator.generate_report()
    
    if fatal_count > 0:
        logger.critical(f"🚨 {fatal_count} errores fatales de especificación detectados")
        logger.critical("   El sistema DEBE iniciar en modo SEGURO")
        return False  # No continuar startup normal
    
    return True  # OK para continuar
