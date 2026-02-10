"""
Machine Learning - Auto-aprendizaje de ponderaciones adaptativas
Autor: MeteoSerV3 System
Fecha: 2026-02-10
Descripción: Adapta automáticamente los pesos de fusión basado en evaluación contra índices reales
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math
import logging

logger = logging.getLogger(__name__)


class MLPonderacionesAdaptativas:
    """
    Machine Learning para optimización automática de ponderaciones.
    
    Algoritmo:
    - Recolecta decisiones de fusión (WH65, WH31, resultado fusionado)
    - Evalúa contra índices meteorológicos reales (WBGT, predicción lluvia, etc.)
    - Usa correlación de Pearson para medir bondad del ajuste
    - Ajusta pesos iterativamente maximizando correlación
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.fusion_log = self.data_dir / "fusion_ml_historico.jsonl"
        self.ponderaciones_log = self.data_dir / "ponderaciones_aprendidas.json"
        
        self.ventana_min = 100  # Mínimo de muestras antes de adaptar
        self.learning_rate = 0.02  # Velocidad de cambio de pesos (2% por iteración)
        self.threshold_mejora = 0.01  # Mejora mínima para aceptar nuevo ajuste
        
        # Cargar ponderaciones previas si existen
        self.ponderaciones_aprendidas = self._cargar_ponderaciones()
    
    def _cargar_ponderaciones(self) -> Dict:
        """Carga ponderaciones aprendidas del archivo"""
        if self.ponderaciones_log.exists():
            try:
                with open(self.ponderaciones_log, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Ponderaciones ML cargadas: {len(data)} contextos")
                    return data
            except Exception as e:
                logger.warning(f"Error cargando ponderaciones ML: {e}")
        return {}
    
    def _guardar_ponderaciones(self):
        """Persiste ponderaciones aprendidas al archivo"""
        try:
            with open(self.ponderaciones_log, 'w') as f:
                json.dump(self.ponderaciones_aprendidas, f, indent=2)
        except Exception as e:
            logger.warning(f"Error guardando ponderaciones ML: {e}")
    
    def registrar_decision(self, temp_wh65: float, hum_wh65: float, 
                          temp_wh31: float, hum_wh31: float,
                          temp_fusionado: float, hum_fusionado: float,
                          contexto: str, indices_reales: Dict = None):
        """Registra una decisión de fusión para aprendizaje posterior"""
        try:
            evento = {
                "timestamp": datetime.now().isoformat(),
                "sensores": {
                    "wh65": {"temp": temp_wh65, "hum": hum_wh65},
                    "wh31": {"temp": temp_wh31, "hum": hum_wh31}
                },
                "fusion": {"temp": temp_fusionado, "hum": hum_fusionado},
                "contexto": contexto,
                "indices": indices_reales or {}
            }
            
            with open(self.fusion_log, 'a') as f:
                f.write(json.dumps(evento) + '\n')
        except Exception as e:
            logger.warning(f"Error registrando decisión de fusión: {e}")
    
    def _leer_historico(self, ultimas_n: int = 1000) -> List[Dict]:
        """Lee las últimas N decisiones del histórico"""
        eventos = []
        try:
            with open(self.fusion_log, 'r') as f:
                for linea in f:
                    try:
                        eventos.append(json.loads(linea))
                    except:
                        pass
            return eventos[-ultimas_n:] if len(eventos) > ultimas_n else eventos
        except:
            return []
    
    @staticmethod
    def _correlacion_pearson(x: List[float], y: List[float]) -> float:
        """Calcula correlación de Pearson entre dos listas"""
        if len(x) < 2 or len(y) < 2:
            return 0.0
        
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        
        numerador = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
        denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
        
        if denom_x == 0 or denom_y == 0:
            return 0.0
        
        return numerador / (denom_x * denom_y)
    
    def _evaluar_bondad_ajuste(self, contexto: str, ponderaciones: Dict) -> Tuple[float, Dict]:
        """
        Evalúa qué tan bien funcionan las ponderaciones contra índices reales.
        
        Returns:
            (score_general, detalles_por_indice)
        """
        eventos = self._leer_historico(ultimas_n=500)
        
        # Filtrar por contexto
        eventos_contexto = [e for e in eventos if e.get('contexto') == contexto]
        
        if len(eventos_contexto) < self.ventana_min:
            return 0.0, {"razon": "insuficientes_datos", "eventos": len(eventos_contexto)}
        
        # Generar series temporales de fusión con ponderaciones propuestas
        series_temp = []
        series_hum = []
        
        for evento in eventos_contexto:
            wh65_t = evento['sensores']['wh65']['temp']
            wh65_h = evento['sensores']['wh65']['hum']
            wh31_t = evento['sensores']['wh31']['temp']
            wh31_h = evento['sensores']['wh31']['hum']
            
            p_t = ponderaciones['temperatura']
            p_h = ponderaciones['humedad']
            
            temp_calc = wh65_t * p_t['wh65'] + wh31_t * p_t['wh31']
            hum_calc = wh65_h * p_h['wh65'] + wh31_h * p_h['wh31']
            
            series_temp.append(temp_calc)
            series_hum.append(hum_calc)
        
        detalles = {"eventos": len(eventos_contexto), "indices": {}}
        score = 0.0
        
        # Evaluar contra índices reales disponibles
        if eventos_contexto[0].get('indices'):
            indices_keys = list(eventos_contexto[0]['indices'].keys())
            
            for idx_key in indices_keys:
                series_idx = [e['indices'].get(idx_key) for e in eventos_contexto 
                             if e.get('indices', {}).get(idx_key) is not None]
                
                if len(series_idx) > 1:
                    # Para temperatura, usar primer sensor fusionado
                    if idx_key in ['wbgt', 'utci']:
                        corr = self._correlacion_pearson(series_temp, series_idx)
                    elif idx_key in ['punto_rocio', 'humedad']:
                        corr = self._correlacion_pearson(series_hum, series_idx)
                    else:
                        corr = 0.0
                    
                    detalles['indices'][idx_key] = corr
                    score += corr / max(1, len(indices_keys))
        
        return score, detalles
    
    def adaptar_ponderaciones(self, contexto: str) -> Optional[Dict]:
        """
        Optimiza ponderaciones para un contexto específico.
        
        Usa descenso de gradiente estocástico simple.
        """
        # Obtener ponderaciones actuales (base)
        try:
            from core.sensors.fusion_config import FusionConfig
            config = FusionConfig()
            pond_actual = config.obtener_ponderaciones(contexto)
        except:
            return None
        
        # Si ya tenemos ponderaciones aprendidas, usar como punto de partida
        if contexto in self.ponderaciones_aprendidas:
            pond_actual = self.ponderaciones_aprendidas[contexto]
        
        # Evaluar bondad actual
        score_actual, _ = self._evaluar_bondad_ajuste(contexto, pond_actual)
        
        if score_actual < 0.5:
            logger.info(f"ML: Score bajo ({score_actual:.3f}) para contexto {contexto}, evaluando ajustes...")
        
        mejor_pond = pond_actual.copy()
        mejor_score = score_actual
        
        # Intentar pequeños ajustes (hill climbing)
        intentos = 0
        max_intentos = 20
        
        while intentos < max_intentos:
            # Generar variante: aumentar WH31, disminuir WH65 (gradualmente)
            pond_prueba = {
                'temperatura': {
                    'wh65': max(0.1, pond_actual['temperatura']['wh65'] - self.learning_rate),
                    'wh31': min(0.9, pond_actual['temperatura']['wh31'] + self.learning_rate)
                },
                'humedad': {
                    'wh65': max(0.1, pond_actual['humedad']['wh65'] - self.learning_rate * 0.5),
                    'wh31': min(0.9, pond_actual['humedad']['wh31'] + self.learning_rate * 0.5)
                }
            }
            
            # Evaluar
            score_prueba, detalles = self._evaluar_bondad_ajuste(contexto, pond_prueba)
            
            if score_prueba > mejor_score + self.threshold_mejora:
                mejor_score = score_prueba
                mejor_pond = pond_prueba
                pond_actual = pond_prueba
                logger.info(f"ML: Mejora en {contexto}: {score_actual:.3f} → {score_prueba:.3f}")
            
            intentos += 1
        
        # Guardar si hay mejora significativa
        if mejor_score > score_actual + self.threshold_mejora:
            self.ponderaciones_aprendidas[contexto] = mejor_pond
            self._guardar_ponderaciones()
            return {
                "contexto": contexto,
                "ponderaciones_anteriores": pond_actual,
                "ponderaciones_nuevas": mejor_pond,
                "score_anterior": score_actual,
                "score_nuevo": mejor_score,
                "mejora": mejor_score - score_actual
            }
        
        return None
    
    def obtener_ponderaciones_aprendidas(self, contexto: str) -> Optional[Dict]:
        """Retorna ponderaciones aprendidas para un contexto, o None si no hay"""
        return self.ponderaciones_aprendidas.get(contexto)
    
    def generar_reporte_aprendizaje(self) -> Dict:
        """Genera reporte de estado del aprendizaje"""
        eventos = self._leer_historico(ultimas_n=10000)
        contextos = list(set(e.get('contexto') for e in eventos))
        
        reporte = {
            "timestamp": datetime.now().isoformat(),
            "total_eventos": len(eventos),
            "contextos_disponibles": contextos,
            "ponderaciones_aprendidas": {},
            "resumen": {}
        }
        
        for ctx in contextos:
            eventos_ctx = [e for e in eventos if e.get('contexto') == ctx]
            
            if ctx in self.ponderaciones_aprendidas:
                reporte['ponderaciones_aprendidas'][ctx] = self.ponderaciones_aprendidas[ctx]
            
            score, _ = self._evaluar_bondad_ajuste(ctx, 
                self.ponderaciones_aprendidas.get(ctx, 
                {'temperatura': {'wh65': 0.3, 'wh31': 0.7}, 
                 'humedad': {'wh65': 0.4, 'wh31': 0.6}}
            ))
            
            reporte['resumen'][ctx] = {
                "muestras": len(eventos_ctx),
                "score_actual": round(score, 3),
                "aprendizado_activo": ctx in self.ponderaciones_aprendidas
            }
        
        return reporte


# Instancia global
_ml_ponderaciones = None

def obtener_ml_ponderaciones() -> MLPonderacionesAdaptativas:
    """Obtiene instancia singleton de ML"""
    global _ml_ponderaciones
    if _ml_ponderaciones is None:
        _ml_ponderaciones = MLPonderacionesAdaptativas()
    return _ml_ponderaciones
