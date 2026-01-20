from dataclasses import dataclass, field
from typing import Dict, Optional, List

@dataclass
class SensorRaw:
    value: float
    unit: str
    ts: float
    source: str

@dataclass
class SensorNormalized:
    value: float
    unit: str
    ts: float
    source: str
    quality: str = "ok"

@dataclass
class DerivedMetric:
    name: str
    value: Optional[float]
    unit: str
    ts: float
    quality: str = "ok"
    depends_on: List[str] = field(default_factory=list)

@dataclass
class MeteoSnapshot:
    ts: float
    sensors: Dict[str, SensorNormalized] = field(default_factory=dict)
    derived: Dict[str, DerivedMetric] = field(default_factory=dict)

# Importar funciones de normalización y cálculo desde el módulo meteorológico principal
from core.meteo.meteo_utils import normalize_sensor, compute_derived
