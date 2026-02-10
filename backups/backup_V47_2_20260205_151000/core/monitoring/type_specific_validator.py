"""
TYPE_SPECIFIC_VALIDATOR - Validación Diferenciada por Tipo V37.0
═════════════════════════════════════════════════════════════════

Objetivo: Aplicar reglas de validación DIFERENTES para cada tipo de medida:
    - FÓRMULA_CALCULADA: Validar precisión, estabilidad, compliance ISO
    - MEDIDA_DIRECTA_SENSOR: Validar que no "mata" varianzas reales
    - MEDIDA+FÓRMULA: Validar ambas partes

Esto evita confundir validaciones entre tipos incomparables.
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from datetime import datetime

class TipoMedida(Enum):
    """Categorización de medidas"""
    FORMULA_CALCULADA = "FORMULA_CALCULADA"  # UTCI, rocío
    MEDIDA_DIRECTA_SENSOR = "MEDIDA_DIRECTA_SENSOR"  # HR%, UV
    MEDIDA_PLUS_FORMULA = "MEDIDA+FORMULA"  # Radiación sensor + teórica


@dataclass
class ValidationRules:
    """Reglas de validación para cada tipo"""
    
    # Comunes
    min_justice_score: float = 0.75  # Mínimo para pasar 25 capas
    allow_override_manual: bool = True
    
    # Específicas por tipo
    # FÓRMULA_CALCULADA
    require_iso_compliance: bool = False
    require_physics_bounds: bool = True
    max_extrapolation_percent: float = 10.0  # No extrapolar >10%
    
    # MEDIDA_DIRECTA_SENSOR
    require_variance_test: bool = True  # Verificar que no mata varianza
    max_variance_reduction_percent: float = 30.0  # Alerta si reduce varianza >30%
    require_sensitivity_test: bool = True  # Detectar si "aplana" cambios reales
    
    # MEDIDA+FORMULA
    require_both_valid: bool = True  # Ambas partes deben ser válidas
    max_lag_ms: int = 100  # No introducir lag > 100ms


@dataclass
class ValidationResult:
    """Resultado de validación específica por tipo"""
    
    tipo: TipoMedida
    candidata_nombre: str
    paso_validacion: bool
    justice_score: float
    
    # Validaciones ejecutadas
    validaciones_ejecutadas: List[str] = None
    validaciones_fallidas: List[str] = None
    
    # Alerts específicas
    alerts: List[str] = None
    
    # Tiempo
    tiempo_ejecucion_ms: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.validaciones_ejecutadas is None:
            self.validaciones_ejecutadas = []
        if self.validaciones_fallidas is None:
            self.validaciones_fallidas = []
        if self.alerts is None:
            self.alerts = []
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def print_summary(self):
        print(f"\n{'='*70}")
        print(f"VALIDACIÓN ESPECÍFICA: {self.tipo.value}")
        print(f"{'='*70}")
        print(f"Candidata:      {self.candidata_nombre}")
        print(f"Justice Score:  {self.justice_score:.3f}")
        print(f"Resultado:      {'✓ PASÓ' if self.paso_validacion else '✗ FALLÓ'}")
        
        print(f"\nValidaciones ejecutadas: {len(self.validaciones_ejecutadas)}")
        for v in self.validaciones_ejecutadas:
            print(f"  ✓ {v}")
        
        if self.validaciones_fallidas:
            print(f"\nValidaciones fallidas: {len(self.validaciones_fallidas)}")
            for v in self.validaciones_fallidas:
                print(f"  ✗ {v}")
        
        if self.alerts:
            print(f"\nAlertas: {len(self.alerts)}")
            for a in self.alerts:
                print(f"  ⚠ {a}")
        
        print(f"\nTiempo: {self.tiempo_ejecucion_ms:.1f}ms")


class TypeSpecificValidator:
    """Validador con reglas específicas por tipo de medida"""
    
    def __init__(self):
        self.rules = {
            TipoMedida.FORMULA_CALCULADA: self._rules_formula_calculada(),
            TipoMedida.MEDIDA_DIRECTA_SENSOR: self._rules_medida_directa(),
            TipoMedida.MEDIDA_PLUS_FORMULA: self._rules_medida_plus_formula(),
        }
    
    def _rules_formula_calculada(self) -> ValidationRules:
        """Reglas para FÓRMULAS CALCULADAS (UTCI, rocío)"""
        return ValidationRules(
            min_justice_score=0.75,
            require_iso_compliance=False,  # Si aplica por tipo
            require_physics_bounds=True,
            max_extrapolation_percent=10.0,
        )
    
    def _rules_medida_directa(self) -> ValidationRules:
        """Reglas para MEDIDAS DIRECTAS (sensores)"""
        return ValidationRules(
            min_justice_score=0.75,
            require_variance_test=True,
            max_variance_reduction_percent=30.0,
            require_sensitivity_test=True,
        )
    
    def _rules_medida_plus_formula(self) -> ValidationRules:
        """Reglas para MEDIDA + FÓRMULA (sensor + teórico)"""
        return ValidationRules(
            min_justice_score=0.75,
            require_both_valid=True,
            max_lag_ms=100,
        )
    
    def validar_formula_calculada(self, candidata_nombre: str, 
                                   datos: np.ndarray, justice_score: float,
                                   verdad_terreno: Optional[np.ndarray] = None) -> ValidationResult:
        """Valida FÓRMULA CALCULADA con reglas científicas"""
        
        inicio = datetime.now()
        result = ValidationResult(
            tipo=TipoMedida.FORMULA_CALCULADA,
            candidata_nombre=candidata_nombre,
            paso_validacion=True,
            justice_score=justice_score
        )
        
        rules = self.rules[TipoMedida.FORMULA_CALCULADA]
        
        # 1. Justice Score mínimo
        if justice_score < rules.min_justice_score:
            result.validaciones_fallidas.append(
                f"Justice Score {justice_score:.3f} < {rules.min_justice_score}"
            )
            result.paso_validacion = False
        else:
            result.validaciones_ejecutadas.append(
                f"Justice Score OK ({justice_score:.3f} >= {rules.min_justice_score})"
            )
        
        # 2. Bounds físicos
        if rules.require_physics_bounds:
            bounds_ok, violation = self._check_physics_bounds(datos, candidata_nombre)
            if bounds_ok:
                result.validaciones_ejecutadas.append("Física bounds OK")
            else:
                result.validaciones_fallidas.append(f"Física bounds: {violation}")
                result.paso_validacion = False
        
        # 3. Extrapolación
        if verdad_terreno is not None:
            extrap_percent = self._check_extrapolation(datos, verdad_terreno)
            if extrap_percent <= rules.max_extrapolation_percent:
                result.validaciones_ejecutadas.append(
                    f"Extrapolación OK ({extrap_percent:.1f}%)"
                )
            else:
                result.alerts.append(
                    f"Extrapolación alta ({extrap_percent:.1f}% > {rules.max_extrapolation_percent}%)"
                )
        
        result.tiempo_ejecucion_ms = (datetime.now() - inicio).total_seconds() * 1000
        return result
    
    def validar_medida_directa(self, candidata_nombre: str,
                               datos_original: np.ndarray,
                               datos_candidata: np.ndarray,
                               justice_score: float) -> ValidationResult:
        """Valida MEDIDA DIRECTA (sensor) con reglas de sensibilidad"""
        
        inicio = datetime.now()
        result = ValidationResult(
            tipo=TipoMedida.MEDIDA_DIRECTA_SENSOR,
            candidata_nombre=candidata_nombre,
            paso_validacion=True,
            justice_score=justice_score
        )
        
        rules = self.rules[TipoMedida.MEDIDA_DIRECTA_SENSOR]
        
        # 1. Justice Score
        if justice_score < rules.min_justice_score:
            result.validaciones_fallidas.append(
                f"Justice Score {justice_score:.3f} < {rules.min_justice_score}"
            )
            result.paso_validacion = False
        else:
            result.validaciones_ejecutadas.append(f"Justice Score OK ({justice_score:.3f})")
        
        # 2. Test de Varianza (CRÍTICO: no matar varianzas reales)
        if rules.require_variance_test:
            var_original = np.var(datos_original)
            var_candidata = np.var(datos_candidata)
            reduction_percent = (var_original - var_candidata) / (var_original + 1e-10) * 100
            
            if reduction_percent > rules.max_variance_reduction_percent:
                result.alerts.append(
                    f"⚠ ALERTA: Varianza reducida {reduction_percent:.1f}% "
                    f"(> {rules.max_variance_reduction_percent}%). "
                    f"Posible over-smoothing que mata cambios reales."
                )
            else:
                result.validaciones_ejecutadas.append(
                    f"Varianza OK (reducción {reduction_percent:.1f}%)"
                )
        
        # 3. Test de Sensibilidad (detectar cambios bruscos reales)
        if rules.require_sensitivity_test:
            sensibilidad_ok, cambios_reales = self._check_sensitivity(
                datos_original, datos_candidata
            )
            if sensibilidad_ok:
                result.validaciones_ejecutadas.append(
                    f"Sensibilidad OK (detecta {cambios_reales} cambios reales)"
                )
            else:
                result.validaciones_fallidas.append(
                    f"Sensibilidad: No detecta cambios bruscos reales"
                )
                result.paso_validacion = False
        
        result.tiempo_ejecucion_ms = (datetime.now() - inicio).total_seconds() * 1000
        return result
    
    def validar_medida_plus_formula(self, candidata_nombre: str,
                                    parte_medida_ok: bool,
                                    parte_formula_ok: bool,
                                    justice_score: float,
                                    lag_ms: float) -> ValidationResult:
        """Valida MEDIDA + FÓRMULA (ambas partes deben ser válidas)"""
        
        inicio = datetime.now()
        result = ValidationResult(
            tipo=TipoMedida.MEDIDA_PLUS_FORMULA,
            candidata_nombre=candidata_nombre,
            paso_validacion=True,
            justice_score=justice_score
        )
        
        rules = self.rules[TipoMedida.MEDIDA_PLUS_FORMULA]
        
        # 1. Justice Score
        if justice_score < rules.min_justice_score:
            result.validaciones_fallidas.append(
                f"Justice Score {justice_score:.3f} < {rules.min_justice_score}"
            )
            result.paso_validacion = False
        else:
            result.validaciones_ejecutadas.append(f"Justice Score OK ({justice_score:.3f})")
        
        # 2. Ambas partes válidas
        if rules.require_both_valid:
            if not parte_medida_ok:
                result.validaciones_fallidas.append("Parte MEDIDA: No válida")
                result.paso_validacion = False
            else:
                result.validaciones_ejecutadas.append("Parte MEDIDA: OK")
            
            if not parte_formula_ok:
                result.validaciones_fallidas.append("Parte FÓRMULA: No válida")
                result.paso_validacion = False
            else:
                result.validaciones_ejecutadas.append("Parte FÓRMULA: OK")
        
        # 3. Lag máximo
        if lag_ms > rules.max_lag_ms:
            result.alerts.append(
                f"⚠ Latencia alta: {lag_ms:.1f}ms (max {rules.max_lag_ms}ms)"
            )
        else:
            result.validaciones_ejecutadas.append(f"Latencia OK ({lag_ms:.1f}ms)")
        
        result.tiempo_ejecucion_ms = (datetime.now() - inicio).total_seconds() * 1000
        return result
    
    def _check_physics_bounds(self, datos: np.ndarray, parametro: str) -> Tuple[bool, str]:
        """Verifica que los datos estén dentro de bounds físicos reales"""
        
        bounds = {
            "sensacion_termica": (-50, 60),  # Celsius
            "humedad_relativa": (0, 100),  # Porcentaje
            "velocidad_viento": (0, 100),  # m/s
            "indice_uv": (0, 20),  # Índice
            "radiacion_solar": (0, 1500),  # W/m²
        }
        
        if parametro not in bounds:
            return True, ""
        
        min_val, max_val = bounds[parametro]
        if np.any(datos < min_val) or np.any(datos > max_val):
            violation = f"Datos fuera de [{min_val}, {max_val}]"
            return False, violation
        
        return True, ""
    
    def _check_extrapolation(self, datos: np.ndarray, verdad: np.ndarray) -> float:
        """Calcula porcentaje de extrapolación (valores sin base física real)"""
        diferencia = np.abs(datos - verdad)
        rango = np.max(verdad) - np.min(verdad)
        extrap_points = np.sum(diferencia > rango * 0.2)  # >20% del rango = extrap
        return (extrap_points / len(datos)) * 100
    
    def _check_sensitivity(self, original: np.ndarray, candidata: np.ndarray) -> Tuple[bool, int]:
        """Detecta si candidata sigue cambios bruscos reales del original"""
        
        # Cambios bruscos en original
        cambios_original = np.abs(np.diff(original))
        umbral_brusco = np.percentile(cambios_original, 75)  # Top 25% son "bruscos"
        indices_bruscos = np.where(cambios_original > umbral_brusco)[0]
        
        if len(indices_bruscos) == 0:
            return True, 0
        
        # Cambios en candidata para los mismos índices
        cambios_candidata = np.abs(np.diff(candidata))
        cambios_reales_detectados = np.sum(cambios_candidata[indices_bruscos] > umbral_brusco * 0.5)
        
        ratio = cambios_reales_detectados / len(indices_bruscos)
        
        # Aceptable si detecta >80% de cambios bruscos
        sensibilidad_ok = ratio >= 0.8
        
        return sensibilidad_ok, cambios_reales_detectados


if __name__ == "__main__":
    # Ejemplo de uso
    import numpy as np
    
    validator = TypeSpecificValidator()
    
    # Test 1: FÓRMULA CALCULADA
    print("\n" + "="*70)
    print("TEST 1: FÓRMULA CALCULADA (UTCI)")
    print("="*70)
    
    datos_utci = np.random.normal(15, 5, 100)
    result1 = validator.validar_formula_calculada(
        "SciPy_CurveFit_WindChill",
        datos_utci,
        justice_score=0.85
    )
    result1.print_summary()
    
    # Test 2: MEDIDA DIRECTA
    print("\n" + "="*70)
    print("TEST 2: MEDIDA DIRECTA (Humedad)")
    print("="*70)
    
    datos_original = np.random.uniform(20, 80, 100)
    datos_suavizado = np.convolve(datos_original, np.ones(5)/5, mode='same')  # Suavizado ligero
    
    result2 = validator.validar_medida_directa(
        "SciPy_Interp1D",
        datos_original,
        datos_suavizado,
        justice_score=0.80
    )
    result2.print_summary()
    
    # Test 3: MEDIDA + FÓRMULA
    print("\n" + "="*70)
    print("TEST 3: MEDIDA + FÓRMULA (Radiación)")
    print("="*70)
    
    result3 = validator.validar_medida_plus_formula(
        "SciPy_Gaussian_Filter",
        parte_medida_ok=True,
        parte_formula_ok=True,
        justice_score=0.82,
        lag_ms=15.5
    )
    result3.print_summary()
