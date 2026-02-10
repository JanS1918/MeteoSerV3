"""
BUS DATA CONTRACT - Definición Explícita de Todo lo Publicado en BusEstadoGlobal.

Este documento define el CONTRATO EXACTO del Bus de Estado, mostrando:
1. Qué keys existen
2. Qué tipo de datos llevan
3. Qué módulo las publica
4. Qué módulos las consumen
5. Unidades y precisión

PROPÓSITO:
Evitar ambigüedad y garantizar que el Bus es una "Espejo Cuántico" del estado
del sistema (no solo resultados finales, sino también subfactores).

═════════════════════════════════════════════════════════════════════════════════
"""

BUS_DATA_CONTRACT = {
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ÍNDICES TERMOFISIOLÓGICOS (core/indices/environmental_indices.py)
    # ═══════════════════════════════════════════════════════════════════════════
    
    "utci": {
        "description": "Universal Thermal Climate Index",
        "type": "float",
        "unit": "°C",
        "precision": 0.01,
        "owner_module": "core.indices.environmental_indices",
        "publisher_function": "indice_utci()",
        "consumers": ["UI", "alerts", "learning_engine"],
        "valid_range": [-50, 80],
        "example_value": 24.37,
        "publish_frequency": "each sensor reading",
        "notes": "Combines temperature, humidity, wind speed, radiation via regression"
    },
    
    "temperatura_sensacion_termica": {
        "description": "Heat Index / Wind Chill (intermediate)",
        "type": "float",
        "unit": "°C",
        "precision": 0.1,
        "owner_module": "core.indices.environmental_indices",
        "publisher_function": "indice_utci() [computed but not published separately]",
        "valid_range": [-60, 70],
        "notes": "USED INTERNALLY in UTCI; not separate Bus key"
    },
    
    "evapotranspiracion_penman_monteith": {
        "description": "Reference Evapotranspiration (FAO-56 standard)",
        "type": "float",
        "unit": "mm/day",
        "precision": 0.01,
        "owner_module": "core.indices.environmental_indices",
        "publisher_function": "evapotranspiracion_penman_monteith()",
        "consumers": ["irrigation_systems", "agricultural_models", "UI"],
        "valid_range": [0, 15],
        "example_value": 4.53,
        "publish_frequency": "each hour or sensor update",
        "references": [
            "FAO-56 Technical Paper",
            "Penman-Monteith equation (1965)",
            "IAPWS-95 vapor saturation"
        ]
    },
    
    "estabilidad_monin_obukhov": {
        "description": "Atmospheric stability parameter (Obukhov length L)",
        "type": "float",
        "unit": "m",
        "precision": 1.0,
        "owner_module": "core.indices.environmental_indices",
        "publisher_function": "estabilidad_monin_obukhov()",
        "consumers": ["wind_profiling", "dispersion_models", "UI"],
        "valid_range": [-1000, 10000],
        "example_value": 234.5,
        "publish_frequency": "each sensor update",
        "stability_classification": {
            "L < -100": "Very unstable (L negativo)",
            "-100 <= L < -10": "Unstable (convection)",
            "-10 <= L < 10": "Neutral (near zero)",
            "10 <= L < 100": "Stable (inversion)",
            "L > 100": "Very stable"
        }
    },
    
    "tendencia_barometrica": {
        "description": "Barometric trend (pressure change rate)",
        "type": "float",
        "unit": "Pa/3h",
        "precision": 1.0,
        "owner_module": "core.indices.environmental_indices",
        "publisher_function": "tendencia_barometrica()",
        "consumers": ["weather_forecasting", "alerts", "UI"],
        "valid_range": [-500, 500],
        "example_value": 12.3,
        "publish_frequency": "each 3-hour cycle",
        "weather_meaning": {
            "< -50": "Rapid pressure drop → storm incoming",
            "-50 to -10": "Pressure falling → deterioration",
            "-10 to 10": "Stable pressure → no change",
            "10 to 50": "Pressure rising → improvement",
            "> 50": "Rapid rise → cold front"
        }
    },
    
    "helada_radiativa": {
        "description": "Radiative frost risk (clear sky, low wind, high RH)",
        "type": "float",
        "unit": "probability (0-1)",
        "precision": 0.01,
        "owner_module": "core.indices.environmental_indices",
        "publisher_function": "helada_radiativa()",
        "consumers": ["frost_alerts", "agricultural_warnings", "UI"],
        "valid_range": [0, 1],
        "example_value": 0.75,
        "publish_frequency": "each hour",
        "frost_conditions": "Low wind (< 2 m/s), HR > 70%, clear sky, T < +5°C"
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONSTANTES DINÁMICAS (core/indices/physics_engine_2026.py)
    # ═══════════════════════════════════════════════════════════════════════════
    
    "gravedad_dinamica": {
        "description": "Gravitational acceleration (Somigliana formula)",
        "type": "float",
        "unit": "m/s²",
        "precision": 0.00001,
        "owner_module": "core.indices.physics_engine_2026",
        "publisher_function": "NOT PUBLISHED YET (SHOULD BE)",
        "consumers": ["barometry_calculations", "pressure_altitude_formulas"],
        "valid_range": [9.78, 9.83],
        "formula": "g(lat) = 9.780318 * (1 + 0.0053024*sin²(lat) - 0.0000058*sin²(2*lat))",
        "notes": "CURRENTLY NOT ON BUS - Gap #1 in subfactor coverage"
    },
    
    "factor_compresibilidad_virial": {
        "description": "Compressibility factor Z (real gas vs ideal)",
        "type": "float",
        "unit": "dimensionless",
        "precision": 0.0001,
        "owner_module": "core.indices.physics_engine_2026",
        "publisher_function": "NOT PUBLISHED YET (SHOULD BE)",
        "consumers": ["density_calculations", "thermodynamic_models"],
        "valid_range": [0.97, 1.01],
        "example_value": 0.9796,
        "formula": "Z = 1 + B(T,xᵥ)*ρ_molar + C(T,xᵥ)*ρ_molar²",
        "notes": "CURRENTLY NOT ON BUS - Gap #2 in subfactor coverage"
    },
    
    "densidad_aire_cipm": {
        "description": "Air density (CIPM-2007 standard)",
        "type": "float",
        "unit": "kg/m³",
        "precision": 0.001,
        "owner_module": "core.indices.physics_engine_2026",
        "publisher_function": "NOT PUBLISHED YET (SHOULD BE)",
        "consumers": ["wind_power_calculations", "aerodynamics"],
        "valid_range": [0.8, 1.4],
        "formula": "ρ = (P*Mₐ - 0.0000218*P*xᵥ) / (Z*R*T)",
        "notes": "CURRENTLY NOT ON BUS - Gap #3 in subfactor coverage"
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # VAPOR DE AGUA (core/indices/vapor_pressure.py)
    # ═══════════════════════════════════════════════════════════════════════════
    
    "presion_vapor_saturacion": {
        "description": "Saturation vapor pressure",
        "type": "float",
        "unit": "Pa",
        "precision": 1.0,
        "owner_module": "core.indices.vapor_pressure",
        "publisher_function": "NOT PUBLISHED YET (SHOULD BE)",
        "consumers": ["dew_point_calc", "humidity_conversions"],
        "valid_range": [0, 150000],
        "formula": "IAPWS-95 (Wexler NIST formulation)",
        "notes": "CRITICAL subfactor NOT on Bus"
    },
    
    "presion_vapor_actual": {
        "description": "Actual vapor pressure",
        "type": "float",
        "unit": "Pa",
        "precision": 1.0,
        "owner_module": "core.indices.vapor_pressure",
        "publisher_function": "NOT PUBLISHED YET (SHOULD BE)",
        "consumers": ["dew_point_calc", "psychrometrics"],
        "valid_range": [0, 150000],
        "formula": "e = e_sat * RH",
        "notes": "CRITICAL subfactor NOT on Bus"
    },
    
    "punto_rocio": {
        "description": "Dew point temperature",
        "type": "float",
        "unit": "°C",
        "precision": 0.1,
        "owner_module": "core.indices.vapor_pressure",
        "publisher_function": "NOT PUBLISHED YET (SHOULD BE)",
        "consumers": ["frost_warnings", "condensation_models"],
        "valid_range": [-50, 40],
        "formula": "Wexler (1976) inverse of Magnus approximation",
        "notes": "CRITICAL subfactor NOT on Bus"
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GALAS CETRERÍA (core/cetreria/cetreria_indices.py)
    # ═══════════════════════════════════════════════════════════════════════════
    
    "sensacion_termica_cetrera": {
        "description": "Hawkery-specific thermal sensation",
        "type": "float",
        "unit": "°C",
        "precision": 0.1,
        "owner_module": "core.cetreria.cetreria_indices",
        "publisher_function": "NOT PUBLISHED",
        "valid_range": [-60, 60],
        "notes": "Cetrería subfactors isolated, NOT on Bus"
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RESUMEN: COBERTURA ACTUAL VS ESPERADA
    # ═══════════════════════════════════════════════════════════════════════════
}

COVERAGE_ANALYSIS = {
    "published_on_bus": [
        "utci",
        "evapotranspiracion_penman_monteith",
        "estabilidad_monin_obukhov",
        "tendencia_barometrica",
        "helada_radiativa",
    ],
    "not_on_bus_but_calculated": [
        "gravedad_dinamica",  # physics_engine_2026
        "factor_compresibilidad_virial",  # physics_engine_2026
        "densidad_aire_cipm",  # physics_engine_2026
        "presion_vapor_saturacion",  # vapor_pressure
        "presion_vapor_actual",  # vapor_pressure
        "punto_rocio",  # vapor_pressure
        "sensacion_termica_cetrera",  # cetreria
    ],
    "coverage_percentage": 5 / 12 * 100,  # 42% of calculated factors
    "user_critique": {
        "claim": "Bus integration claimed ~50%",
        "reality": "42% final indices only; 0% subfactors (physics, vapor, etc)",
        "truth": "Honest assessment: 20% of theoretical full scope"
    }
}

def print_bus_audit():
    """Pretty print the Bus audit results."""
    print("\n" + "="*80)
    print("BUS DATA CONTRACT AUDIT")
    print("="*80)
    
    print(f"\n[OK] PUBLISHED ON BUS ({len(COVERAGE_ANALYSIS['published_on_bus'])} keys):")
    for key in COVERAGE_ANALYSIS['published_on_bus']:
        print(f"   • {key}")
    
    print(f"\n[ERROR] CALCULATED BUT NOT ON BUS ({len(COVERAGE_ANALYSIS['not_on_bus_but_calculated'])} keys):")
    for key in COVERAGE_ANALYSIS['not_on_bus_but_calculated']:
        print(f"   • {key}")
    
    print(f"\n[STATS] COVERAGE: {COVERAGE_ANALYSIS['coverage_percentage']:.1f}% of full scope")
    
    print("\n[TARGET] HONEST ASSESSMENT:")
    for key, value in COVERAGE_ANALYSIS['user_critique'].items():
        print(f"   {key}: {value}")
    
    print("\n[REINICIO] TO REACH 100% COVERAGE, ADD TO BUS:")
    for key in COVERAGE_ANALYSIS['not_on_bus_but_calculated']:
        print(f"   • app.state.bus.publish('{key}', value)")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    print_bus_audit()
