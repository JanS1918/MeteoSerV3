from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional


@dataclass
class ETControlResult:
    et_pred_mm_dia: float
    et_corregida_mm_dia: float
    factor_hoy: float
    factor_promedio: float
    delta_humedad_pct: Optional[float]
    agua_perdida_mm: Optional[float]
    estado: str
    confianza_pct: float
    muestras: int
    lluvia_24h_mm: float


class ETSoilController:
    """
    Controlador de ET basado en coherencia con humedad de suelo.

    - Aprende un factor dinámico por historial.
    - Corrige ET real sin inventar cultivo ni cobertura.
    - Detecta ganancias de agua (riego/lluvia) y baja confianza.
    """

    def __init__(self,
                 capacidad_campo_mm: float = 150.0,
                 max_historia: int = 14,
                 min_muestras: int = 5,
                 factor_min: float = 0.2,
                 factor_max: float = 1.5):
        self.capacidad_campo_mm = float(capacidad_campo_mm)
        self.max_historia = int(max_historia)
        self.min_muestras = int(min_muestras)
        self.factor_min = float(factor_min)
        self.factor_max = float(factor_max)
        self._factor_hist: Deque[float] = deque(maxlen=self.max_historia)
        self._humedad_prev: Optional[float] = None
        self._timestamp_prev: Optional[float] = None

    def update(self,
               humedad_suelo_pct: Optional[float],
               et_pred_mm_dia: Optional[float],
               lluvia_24h_mm: float = 0.0,
               capacidad_campo_mm: Optional[float] = None,
               timestamp: Optional[float] = None) -> ETControlResult:
        """
        Actualiza el controlador con nueva lectura de humedad y ET predicha.
        """
        et_pred = float(et_pred_mm_dia or 0.0)
        lluvia_24h_mm = float(lluvia_24h_mm or 0.0)

        if capacidad_campo_mm is not None:
            self.capacidad_campo_mm = float(capacidad_campo_mm)

        if humedad_suelo_pct is None:
            return ETControlResult(
                et_pred_mm_dia=et_pred,
                et_corregida_mm_dia=et_pred,
                factor_hoy=1.0,
                factor_promedio=1.0,
                delta_humedad_pct=None,
                agua_perdida_mm=None,
                estado="SIN_DATOS",
                confianza_pct=0.0,
                muestras=len(self._factor_hist),
                lluvia_24h_mm=lluvia_24h_mm,
            )

        humedad_actual = float(humedad_suelo_pct)

        # Primer dato: iniciar baseline
        if self._humedad_prev is None:
            self._humedad_prev = humedad_actual
            self._timestamp_prev = timestamp
            return ETControlResult(
                et_pred_mm_dia=et_pred,
                et_corregida_mm_dia=et_pred,
                factor_hoy=1.0,
                factor_promedio=1.0,
                delta_humedad_pct=0.0,
                agua_perdida_mm=0.0,
                estado="APRENDIENDO",
                confianza_pct=50.0,
                muestras=len(self._factor_hist),
                lluvia_24h_mm=lluvia_24h_mm,
            )

        delta_pct = self._humedad_prev - humedad_actual
        agua_perdida_mm = (delta_pct / 100.0) * self.capacidad_campo_mm

        # Ganancia de agua (riego/lluvia): no usar para factor
        if delta_pct <= 0:
            factor_hoy = 0.0
            estado = "GANANCIA_AGUA"
        elif et_pred > 0:
            factor_hoy = agua_perdida_mm / et_pred
            estado = "OK"
        else:
            factor_hoy = 1.0
            estado = "SIN_ET"

        # Clamp factor para evitar extremos
        if factor_hoy < self.factor_min:
            factor_hoy = self.factor_min if delta_pct > 0 else 0.0
        if factor_hoy > self.factor_max:
            factor_hoy = self.factor_max

        if delta_pct > 0 and et_pred > 0:
            self._factor_hist.append(factor_hoy)

        if self._factor_hist:
            factor_prom = sum(self._factor_hist) / len(self._factor_hist)
        else:
            factor_prom = 1.0

        if len(self._factor_hist) < self.min_muestras:
            estado = "APRENDIENDO"

        # Confianza basada en estabilidad del factor
        if len(self._factor_hist) >= 2:
            mean = factor_prom
            var = sum((f - mean) ** 2 for f in self._factor_hist) / len(self._factor_hist)
            std = var ** 0.5
        else:
            std = 0.0

        estabilidad = max(0.0, 1.0 - min(1.0, std / max(0.1, factor_prom)))
        progreso = min(1.0, len(self._factor_hist) / max(1, self.min_muestras))
        confianza = 40.0 + 60.0 * (estabilidad * progreso)

        et_corregida = et_pred * factor_prom if len(self._factor_hist) >= self.min_muestras else et_pred

        # Persistir
        self._humedad_prev = humedad_actual
        self._timestamp_prev = timestamp

        return ETControlResult(
            et_pred_mm_dia=et_pred,
            et_corregida_mm_dia=max(0.0, et_corregida),
            factor_hoy=factor_hoy,
            factor_promedio=factor_prom,
            delta_humedad_pct=delta_pct,
            agua_perdida_mm=agua_perdida_mm,
            estado=estado,
            confianza_pct=round(confianza, 1),
            muestras=len(self._factor_hist),
            lluvia_24h_mm=lluvia_24h_mm,
        )
