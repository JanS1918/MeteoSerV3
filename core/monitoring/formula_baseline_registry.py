"""
FORMULA_BASELINE_REGISTRY - Inventario Centralizado V37.0
═════════════════════════════════════════════════════════

Objetivo: Mapeo COMPLETO de qué fórmulas/sensores se usan ACTUALMENTE
para que el sistema SEPA qué tiene antes de buscar mejoras.

Categorías:
├─ A: FÓRMULA_CALCULADA (ej: UTCI - necesita múltiples variables)
├─ B: MEDIDA_DIRECTA_SENSOR (ej: Humedad sensor - lectura física)
└─ C: MEDIDA_DIRECTA_SENSOR_PLUS_FORMULA (ej: Radiación sensor + teórica)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json

@dataclass
class FormulaBaseline:
    """Registro de una fórmula/medida actual en producción"""
    
    # Identificación
    parametro: str  # "sensacion_termica", "humedad_relativa", etc.
    tipo: str  # "FORMULA_CALCULADA" | "MEDIDA_DIRECTA_SENSOR" | "MEDIDA+FORMULA"
    nivel_elite: str  # "ELITE", "PROFESIONAL", "ESTÁNDAR", "HARDWARE"
    
    # Implementación
    nombre_legible: str  # "UTCI Polynomial Fiala 186"
    fuente_archivo: str  # "core/indices/utci_polynomial.py:42"
    fuente_metodo: str  # "Ecowitt_HP2550A_HR" o "calculate_utci()"
    
    # Especificaciones
    precision: str  # "±0.1°C"
    velocidad_score: float  # 0-10
    latencia_ms: Optional[float]  # Milisegundos
    
    # Dependencias (qué necesita para funcionar)
    requiere_parametros: List[str] = field(default_factory=list)  # ["temperatura", "humedad", "viento"]
    requiere_hardware: Optional[str] = None  # "HP2550A", "Piranometer", None
    
    # Hardware específico
    hardware_layer_processing: Optional[str] = None  # "HP2550A_firmware_smoothing"
    
    # Contexto histórico
    fecha_implementacion: str = ""
    validado_en_produccion: bool = False
    dias_en_produccion: int = 0
    satisfaction_score: float = 0.0  # 0-1, feedback de usuarios
    
    # Monitoreo
    ultima_actualizacion: datetime = field(default_factory=datetime.now)
    es_activo: bool = True


class FormulaBaselineRegistry:
    """Registro centralizado de TODAS las fórmulas/sensores actuales"""
    
    def __init__(self):
        self.baselines: Dict[str, FormulaBaseline] = {}
        self._initialize_known_baselines()
    
    def _initialize_known_baselines(self):
        """Inicializa las fórmulas/sensores que SABEMOS que existen"""
        
        # CATEGORÍA A: FÓRMULA CALCULADA
        self.register(FormulaBaseline(
            parametro="sensacion_termica",
            tipo="FORMULA_CALCULADA",
            nivel_elite="ELITE",
            nombre_legible="UTCI Polynomial Fiala 186",
            fuente_archivo="core/indices/utci_polynomial.py:42",
            fuente_metodo="calculate_utci()",
            precision="±0.1°C",
            velocidad_score=8.0,
            latencia_ms=45.0,
            requiere_parametros=["temperatura", "humedad", "viento", "radiacion"],
            requiere_hardware="HP2550A",
            fecha_implementacion="2023-06-15",
            validado_en_produccion=True,
            dias_en_produccion=960,
            satisfaction_score=0.92
        ))
        
        # CATEGORÍA B: MEDIDA DIRECTA SENSOR
        self.register(FormulaBaseline(
            parametro="humedad_relativa",
            tipo="MEDIDA_DIRECTA_SENSOR",
            nivel_elite="HARDWARE",
            nombre_legible="Ecowitt HP2550A HR Direct",
            fuente_archivo="main_asgi.py:3097",
            fuente_metodo="sensores.get('humedad')",
            precision="±1-2%",
            velocidad_score=10.0,
            latencia_ms=42.4,
            requiere_hardware="HP2550A",
            hardware_layer_processing="HP2550A_firmware_smoothing",
            fecha_implementacion="2021-01-01",
            validado_en_produccion=True,
            dias_en_produccion=1500,
            satisfaction_score=0.88
        ))
        
        self.register(FormulaBaseline(
            parametro="indice_uv",
            tipo="MEDIDA_DIRECTA_SENSOR",
            nivel_elite="HARDWARE",
            nombre_legible="Ecowitt HP2550A UV Direct",
            fuente_archivo="main_asgi.py:2151",
            fuente_metodo="sensores.get('uv')",
            precision="±0.5 (índice 0-11)",
            velocidad_score=10.0,
            latencia_ms=23.6,
            requiere_hardware="HP2550A",
            hardware_layer_processing="HP2550A_firmware_smoothing",
            fecha_implementacion="2021-01-01",
            validado_en_produccion=True,
            dias_en_produccion=1500,
            satisfaction_score=0.85
        ))
        
        # CATEGORÍA C: MEDIDA + FÓRMULA COMPLEMENTARIA
        self.register(FormulaBaseline(
            parametro="velocidad_viento",
            tipo="MEDIDA+FORMULA",
            nivel_elite="PROFESIONAL",
            nombre_legible="Ecowitt Wind + Logarithmic Adjustment",
            fuente_archivo="bus_expander.py:1156",
            fuente_metodo="sensores.get('viento') * factor_ajuste_altura",
            precision="±0.1 m/s",
            velocidad_score=9.2,
            latencia_ms=32.2,
            requiere_hardware="HP2550A",
            hardware_layer_processing="HP2550A_firmware_smoothing + logarithmic_correction",
            fecha_implementacion="2021-01-01",
            validado_en_produccion=True,
            dias_en_produccion=1500,
            satisfaction_score=0.89
        ))
        
        self.register(FormulaBaseline(
            parametro="radiacion_solar",
            tipo="MEDIDA+FORMULA",
            nivel_elite="ELITE",
            nombre_legible="Ecowitt Piranometer + Gueymard REST2",
            fuente_archivo="bus_expander.py:847",
            fuente_metodo="sensores.get('radiacion') + gueymard_theoretical()",
            precision="±50 W/m²",
            velocidad_score=8.1,
            latencia_ms=21.4,
            requiere_hardware="HP2550A",
            hardware_layer_processing="HP2550A_firmware_smoothing + Gueymard_REST2_theoretical",
            fecha_implementacion="2022-01-15",
            validado_en_produccion=True,
            dias_en_produccion=1200,
            satisfaction_score=0.87
        ))
    
    def register(self, baseline: FormulaBaseline):
        """Registra una fórmula/sensor en el inventario"""
        self.baselines[baseline.parametro] = baseline
    
    def get(self, parametro: str) -> Optional[FormulaBaseline]:
        """Obtiene la fórmula actual para un parámetro"""
        return self.baselines.get(parametro)
    
    def get_all(self) -> Dict[str, FormulaBaseline]:
        """Obtiene todas las fórmulas registradas"""
        return self.baselines.copy()
    
    def export_json(self) -> str:
        """Exporta el inventario como JSON"""
        data = {}
        for param, baseline in self.baselines.items():
            data[param] = {
                "tipo": baseline.tipo,
                "nivel": baseline.nivel_elite,
                "nombre": baseline.nombre_legible,
                "precision": baseline.precision,
                "velocidad": baseline.velocidad_score,
                "latencia_ms": baseline.latencia_ms,
                "hardware": baseline.requiere_hardware,
                "validado": baseline.validado_en_produccion,
                "satisfaction": baseline.satisfaction_score
            }
        return json.dumps(data, indent=2)
    
    def print_summary(self):
        """Imprime resumen de todas las fórmulas/sensores"""
        print("\n" + "="*80)
        print("INVENTARIO BASELINE V37.0 - FÓRMULAS/SENSORES ACTUALES")
        print("="*80)
        
        for param, baseline in sorted(self.baselines.items()):
            print(f"\n[{param.upper()}]")
            print(f"  Tipo:           {baseline.tipo}")
            print(f"  Nivel:          {baseline.nivel_elite}")
            print(f"  Implementación: {baseline.nombre_legible}")
            print(f"  Fuente:         {baseline.fuente_archivo}")
            print(f"  Precisión:      {baseline.precision}")
            print(f"  Velocidad:      {baseline.velocidad_score}/10")
            print(f"  Latencia:       {baseline.latencia_ms}ms")
            if baseline.requiere_hardware:
                print(f"  Hardware:       {baseline.requiere_hardware}")
            if baseline.requiere_parametros:
                print(f"  Requiere:       {', '.join(baseline.requiere_parametros)}")
            print(f"  En producción:  {baseline.dias_en_produccion} días")
            print(f"  Satisfacción:   {baseline.satisfaction_score:.0%}")


# Instancia global para acceso rápido
BASELINE_REGISTRY = FormulaBaselineRegistry()
