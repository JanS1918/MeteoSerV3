#!/usr/bin/env python3
"""
FormulaOptimizer: Sistema de auto-mejora pre-duelo

Diagnóstica debilidades de fórmulas y aplica mejoras simuladas
sin modificar el original, para entrar al duelo "limpia".
"""

import statistics
import math
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("meteoser.formula_optimizer")


@dataclass
class DiagnosticoFormula:
    """Diagnóstico de problemas en una fórmula"""
    tiene_ruido: bool
    coef_variacion: float
    tiene_outliers: bool
    pct_outliers: float
    rango_valores: float
    validos_pct: float
    problemas: List[str]


@dataclass
class MejoraAplicada:
    """Registro de una mejora aplicada"""
    tipo: str  # "ewma", "clip_outliers", "normalizacion"
    condicion_cumple: bool
    score_antes: float
    score_despues: float
    mejora_pct: float
    datos_cambio: Dict[str, Any]


class FormulaOptimizer:
    """
    Optimiza fórmulas para duelos identificando y corrigiendo:
    - Ruido aleatorio → EWMA
    - Outliers extremos → Clipping
    - Rango inestable → Normalización
    
    TODO es simulado y reversible.
    """
    
    def __init__(self):
        self.mejoras_seguras = {
            "ewma": {
                "condicion_min": 0.15,  # Coef variación mínimo para aplicar
                "factor": 0.3,           # Factor de suavizado
                "riesgo": "CERO"
            },
            "clip_outliers": {
                "iqr_multiplier": 1.5,   # Rango intercuartílico
                "min_pct": 0.03,         # Mínimo 3% outliers para aplicar
                "riesgo": "BAJO"
            },
            "normalizacion": {
                "z_score_limit": 3.0,    # Limite de desviaciones estándar
                "riesgo": "CERO"
            }
        }
    
    def diagnosticar(self, outputs: List[float]) -> DiagnosticoFormula:
        """
        Diagnóstica problemas en outputs de una fórmula.
        
        Retorna: DiagnosticoFormula con problemas identificados
        """
        if not outputs or len(outputs) < 2:
            return DiagnosticoFormula(
                tiene_ruido=False,
                coef_variacion=0.0,
                tiene_outliers=False,
                pct_outliers=0.0,
                rango_valores=0.0,
                validos_pct=1.0,
                problemas=["Insuficientes datos"]
            )
        
        problemas = []
        
        # 1. Calcular variabilidad
        media = statistics.mean(outputs)
        desv = statistics.stdev(outputs) if len(outputs) > 1 else 0
        coef_var = (desv / abs(media)) if media != 0 else 0
        
        tiene_ruido = coef_var > self.mejoras_seguras["ewma"]["condicion_min"]
        if tiene_ruido:
            problemas.append(f"Ruido: CV={coef_var:.3f}")
        
        # 2. Detectar outliers
        q1 = self._quartil(outputs, 0.25)
        q3 = self._quartil(outputs, 0.75)
        iqr = q3 - q1
        limite_bajo = q1 - self.mejoras_seguras["clip_outliers"]["iqr_multiplier"] * iqr
        limite_alto = q3 + self.mejoras_seguras["clip_outliers"]["iqr_multiplier"] * iqr
        
        outliers = [x for x in outputs if x < limite_bajo or x > limite_alto]
        pct_outliers = len(outliers) / len(outputs) if outputs else 0
        tiene_outliers = pct_outliers > self.mejoras_seguras["clip_outliers"]["min_pct"]
        
        if tiene_outliers:
            problemas.append(f"Outliers: {pct_outliers:.1%}")
        
        # 3. Rango
        rango = max(outputs) - min(outputs)
        
        # 4. Validez
        validos_pct = 1.0
        
        return DiagnosticoFormula(
            tiene_ruido=tiene_ruido,
            coef_variacion=coef_var,
            tiene_outliers=tiene_outliers,
            pct_outliers=pct_outliers,
            rango_valores=rango,
            validos_pct=validos_pct,
            problemas=problemas
        )
    
    def aplicar_mejora_simulada(
        self,
        outputs: List[float],
        nombre_formula: str = "?"
    ) -> Tuple[List[float], List[MejoraAplicada], float]:
        """
        Aplica mejoras simuladas a outputs.
        
        Retorna: (outputs_mejorados, cambios_aplicados, score_mejora_pct)
        """
        
        # Diagnóstico
        diag = self.diagnosticar(outputs)
        outputs_mejorados = outputs.copy()
        mejoras_aplicadas = []
        
        logger.debug(f"Diagnóstico {nombre_formula}: {diag.problemas}")
        
        # 1. EWMA - Suavizar ruido
        if diag.tiene_ruido:
            outputs_ewma = self._aplicar_ewma(outputs_mejorados)
            score_antes = self._calcular_consistencia(outputs_mejorados)
            score_despues = self._calcular_consistencia(outputs_ewma)
            mejora_pct = ((score_despues - score_antes) / abs(score_antes)) * 100 if score_antes != 0 else 0
            
            if mejora_pct > 0:  # Solo si mejora
                mejoras_aplicadas.append(MejoraAplicada(
                    tipo="ewma",
                    condicion_cumple=True,
                    score_antes=score_antes,
                    score_despues=score_despues,
                    mejora_pct=mejora_pct,
                    datos_cambio={"factor": self.mejoras_seguras["ewma"]["factor"]}
                ))
                outputs_mejorados = outputs_ewma
                logger.debug(f"  [OK] EWMA aplicado: {mejora_pct:.1f}% mejora")
        
        # 2. Clipping - Eliminar outliers
        if diag.tiene_outliers:
            outputs_clip = self._aplicar_clip(outputs_mejorados)
            score_antes = self._calcular_robustez(outputs_mejorados)
            score_despues = self._calcular_robustez(outputs_clip)
            mejora_pct = ((score_despues - score_antes) / abs(score_antes)) * 100 if score_antes != 0 else 0
            
            if mejora_pct > 0:
                mejoras_aplicadas.append(MejoraAplicada(
                    tipo="clip_outliers",
                    condicion_cumple=True,
                    score_antes=score_antes,
                    score_despues=score_despues,
                    mejora_pct=mejora_pct,
                    datos_cambio={"outliers_removidos": diag.pct_outliers}
                ))
                outputs_mejorados = outputs_clip
                logger.debug(f"  [OK] Clipping aplicado: {mejora_pct:.1f}% mejora")
        
        # 3. Normalización - Estabilizar rango
        if diag.rango_valores > 0 and len(outputs_mejorados) > 0:
            outputs_norm = self._aplicar_normalizacion(outputs_mejorados)
            score_antes = self._calcular_estabilidad(outputs_mejorados)
            score_despues = self._calcular_estabilidad(outputs_norm)
            mejora_pct = ((score_despues - score_antes) / abs(score_antes)) * 100 if score_antes != 0 else 0
            
            if mejora_pct > 0:
                mejoras_aplicadas.append(MejoraAplicada(
                    tipo="normalizacion",
                    condicion_cumple=True,
                    score_antes=score_antes,
                    score_despues=score_despues,
                    mejora_pct=mejora_pct,
                    datos_cambio={"rango_original": diag.rango_valores}
                ))
                outputs_mejorados = outputs_norm
                logger.debug(f"  [OK] Normalización aplicada: {mejora_pct:.1f}% mejora")
        
        # Mejora total
        mejora_total = (sum(m.mejora_pct for m in mejoras_aplicadas) / len(mejoras_aplicadas)) if mejoras_aplicadas else 0
        
        return outputs_mejorados, mejoras_aplicadas, mejora_total
    
    # ─── Métodos privados de mejora ───
    
    def _aplicar_ewma(self, outputs: List[float], factor: float = 0.3) -> List[float]:
        """Aplicar EWMA (exponential weighted moving average)"""
        if len(outputs) < 2:
            return outputs
        
        resultado = [outputs[0]]
        for i in range(1, len(outputs)):
            ema = factor * outputs[i] + (1 - factor) * resultado[-1]
            resultado.append(ema)
        
        return resultado
    
    def _aplicar_clip(self, outputs: List[float]) -> List[float]:
        """Clipear outliers usando IQR"""
        if len(outputs) < 4:
            return outputs
        
        q1 = self._quartil(outputs, 0.25)
        q3 = self._quartil(outputs, 0.75)
        iqr = q3 - q1
        
        limite_bajo = q1 - 1.5 * iqr
        limite_alto = q3 + 1.5 * iqr
        
        return [max(limite_bajo, min(limite_alto, x)) for x in outputs]
    
    def _aplicar_normalizacion(self, outputs: List[float]) -> List[float]:
        """Z-score normalization"""
        if len(outputs) < 2:
            return outputs
        
        media = statistics.mean(outputs)
        desv = statistics.stdev(outputs) if len(outputs) > 1 else 1
        
        if desv == 0:
            return outputs
        
        return [(x - media) / desv for x in outputs]
    
    # ─── Métodos de cálculo ───
    
    def _calcular_consistencia(self, outputs: List[float]) -> float:
        """Score de consistencia (inverso de CV)"""
        if not outputs or len(outputs) < 2:
            return 1.0
        
        media = statistics.mean(outputs)
        desv = statistics.stdev(outputs)
        cv = (desv / abs(media)) if media != 0 else 0
        
        return 1.0 / (1.0 + cv)  # Entre 0 y 1
    
    def _calcular_robustez(self, outputs: List[float]) -> float:
        """Score de robustez (porcentaje dentro de rango válido)"""
        if not outputs:
            return 0.0
        
        q1 = self._quartil(outputs, 0.25)
        q3 = self._quartil(outputs, 0.75)
        iqr = q3 - q1
        
        limite_bajo = q1 - 1.5 * iqr
        limite_alto = q3 + 1.5 * iqr
        
        validos = sum(1 for x in outputs if limite_bajo <= x <= limite_alto)
        return validos / len(outputs)
    
    def _calcular_estabilidad(self, outputs: List[float]) -> float:
        """Score de estabilidad (consistencia)"""
        return self._calcular_consistencia(outputs)
    
    @staticmethod
    def _quartil(datos: List[float], q: float) -> float:
        """Calcular cuartil q (0-1)"""
        if not datos or q < 0 or q > 1:
            return 0.0
        
        datos_ord = sorted(datos)
        idx = q * (len(datos_ord) - 1)
        
        if idx == int(idx):
            return datos_ord[int(idx)]
        
        i = int(idx)
        f = idx - i
        return datos_ord[i] * (1 - f) + datos_ord[i + 1] * f
