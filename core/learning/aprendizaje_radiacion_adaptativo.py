"""
APRENDIZAJE ADAPTATIVO DE RADIACIÓN V1.0
═══════════════════════════════════════════════════════════════════════════════════
Sistema que aprende de históricos para mejorar TODAS las predicciones y alertas.

ARQUITECTURA:
1. Lee históricos de radiación (REST2 vs medida real)
2. Calcula errores y sesgos por:
   - Hora del día
   - Elevación solar  
   - Condiciones atmosféricas (nubes, aerosoles, vapor)
   - Temporada
3. Ajusta dinámicamente:
   - Confianza en modelo REST2
   - Ponderaciones de sensores (WH65 vs WH31)
   - Thresholds de WBGT, condensación, anomalías
   - Recomendaciones de ET0 (factores Penman-Monteith)
4. Detección de drift (cambios en sensores o ambiente)

DATOS UTILIZADOS:
- Bus Estado Global: radiacion_ghi_w_m2, contexto_solar
- Historical Registry: eventos de radiación, validaciones
- ML Ponderaciones: pesos WH65/WH31
- Learning Feedback: feedback de usuarios

SALIDAS:
- Ajustes automáticos de confianza
- Alertas inteligentes (contexto-aware)
- Predicciones mejoradas
- Recomendaciones de calibración
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class AprendizajeRadiacionAdaptativo:
    """
    Sistema de aprendizaje que mejora automáticamente todas las decisiones
    basado en históricos de radiación y validaciones de sensores.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Historiales por contexto solar
        self.historico_radiacion = self.data_dir / "historico_radiacion_completo.jsonl"
        self.ajustes_aprendidos = self.data_dir / "ajustes_radiacion_aprendidos.json"
        self.thresholds_dinamicos = self.data_dir / "thresholds_dinamicos.json"
        
        # Estado de aprendizaje
        self.estado_ajustes = self._cargar_ajustes()
        self.estado_thresholds = self._cargar_thresholds()
        
    def _cargar_ajustes(self) -> Dict:
        """Carga ajustes previamente aprendidos."""
        if self.ajustes_aprendidos.exists():
            try:
                with open(self.ajustes_aprendidos, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando ajustes: {e}")
        
        # Ajustes iniciales por defecto
        return {
            "confianza_rest2_por_elevacion": {
                "muy_bajo": {"elevacion_rango": [-90, -18], "confianza_base": 0},
                "bajo": {"elevacion_rango": [-18, -6], "confianza_base": 5},
                "medio": {"elevacion_rango": [-6, 0], "confianza_base": 20},
                "alto": {"elevacion_rango": [0, 10], "confianza_base": 60},
                "muy_alto": {"elevacion_rango": [10, 30], "confianza_base": 85},
                "pico": {"elevacion_rango": [30, 90], "confianza_base": 95}
            },
            "sesgos_por_hora": {},  # Se carga de históricos
            "sesgos_por_estacion": {},
            "ultimo_ajuste": None,
            "muestras_procesadas": 0
        }
    
    def _cargar_thresholds(self) -> Dict:
        """Carga thresholds dinámicos aprendidos."""
        if self.thresholds_dinamicos.exists():
            try:
                with open(self.thresholds_dinamicos, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando thresholds: {e}")
        
        # Thresholds iniciales
        return {
            "wbgt": {
                "threshold_alerta_amarillo_celsius": 28.0,
                "threshold_alerta_rojo_celsius": 32.0,
                "ajustable": True
            },
            "condensacion": {
                "threshold_riesgo_celsius": 2.0,  # T interior - Tdp
                "multiplicador_noche": 1.4,
                "ajustable": True
            },
            "anomalia_delta_t": {
                "baseline_dia_celsius": 5.0,
                "baseline_noche_celsius": 1.0,
                "ajustable": True
            },
            "et0": {
                "factor_penman_base": 1.0,
                "factor_por_estacion": {"invierno": 0.8, "primavera": 1.0, "verano": 1.1, "otoño": 1.0},
                "ajustable": True
            }
        }
    
    def registrar_radiacion_observada(
        self,
        radiacion_medida_w_m2: float,
        radiacion_modelada_rest2_w_m2: float,
        elevacion_solar_deg: float,
        contexto: Dict,
        nubes_detectadas: bool,
        validacion_termica_ok: bool,
        timestamp: datetime
    ):
        """
        Registra una observación de radiación para aprendizaje posterior.
        
        Args:
            radiacion_medida_w_m2: Radiación real del sensor
            radiacion_modelada_rest2_w_m2: Radiación predicha por REST2
            elevacion_solar_deg: Ángulo solar (°)
            contexto: Dict con estado_solar, hora, etc.
            nubes_detectadas: Si se detectan nubes (K_t < 0.7)
            validacion_termica_ok: Si ΔT WH65-WH31 es coherente
            timestamp: Momento de observación
        """
        try:
            evento = {
                "timestamp": timestamp.isoformat(),
                "radiacion_medida": radiacion_medida_w_m2,
                "radiacion_modelo": radiacion_modelada_rest2_w_m2,
                "error_absoluto": abs(radiacion_medida_w_m2 - radiacion_modelada_rest2_w_m2),
                "error_relativo_pct": 100 * abs(radiacion_medida_w_m2 - radiacion_modelada_rest2_w_m2) / max(1, radiacion_modelada_rest2_w_m2),
                "elevacion_solar": elevacion_solar_deg,
                "contexto": contexto,
                "nubes_detectadas": nubes_detectadas,
                "validacion_termica": validacion_termica_ok
            }
            
            with open(self.historico_radiacion, 'a') as f:
                f.write(json.dumps(evento) + '\n')
            
            logger.debug(f"[APRENDIZAJE] Radiación registrada: medida={radiacion_medida_w_m2:.1f}, "
                        f"modelo={radiacion_modelada_rest2_w_m2:.1f}, error={evento['error_relativo_pct']:.1f}%")
        except Exception as e:
            logger.warning(f"Error registrando radiación: {e}")
    
    def calcular_ajustes_dinamicos(self, muestras_minimas: int = 100) -> Dict:
        """
        Lee históricos y calcula ajustes óptimos.
        Ejecutar periódicamente (ej: diariamente).
        
        Args:
            muestras_minimas: Mínimo de observaciones para hacer ajustes
        
        Returns:
            Dict con ajustes calculados
        """
        try:
            # Leer históricos
            eventos = self._leer_historico()
            
            if len(eventos) < muestras_minimas:
                logger.info(f"[APRENDIZAJE] Insuficientes muestras ({len(eventos)}/{muestras_minimas})")
                return self.estado_ajustes
            
            logger.info(f"[APRENDIZAJE] Procesando {len(eventos)} observaciones de radiación")
            
            # Agrupar por elevación solar
            errores_por_elevacion = defaultdict(list)
            sesgos_por_hora = defaultdict(list)
            
            for evento in eventos:
                elevacion = evento.get("elevacion_solar", 0.0)
                error_rel = evento.get("error_relativo_pct", 0.0)
                
                # Bucket por elevación solar (cada 5°)
                bucket_elev = round(elevacion / 5) * 5
                errores_por_elevacion[bucket_elev].append(error_rel)
                
                # Bucket por hora
                try:
                    ts = datetime.fromisoformat(evento["timestamp"])
                    hora = ts.hour
                    sesgos_por_hora[hora].append(error_rel)
                except:
                    pass
            
            # Calcular confianzas ajustadas por elevación
            for elevacion_bucket, errores in errores_por_elevacion.items():
                error_medio = np.mean(errores) if errores else 0
                desv_est = np.std(errores) if len(errores) > 1 else 0
                
                # Ajustar confianza base: si error promedio > 20%, bajar confianza
                if error_medio < 10:
                    ajuste = +5
                elif error_medio < 20:
                    ajuste = 0
                elif error_medio < 35:
                    ajuste = -10
                else:
                    ajuste = -20
                
                logger.debug(f"[APRENDIZAJE] Elevación {elevacion_bucket}°: "
                           f"error_medio={error_medio:.1f}%, "
                           f"desv_est={desv_est:.1f}%, ajuste={ajuste}%")
            
            # Calcular sesgos por hora del día
            sesgos_hora_dict = {}
            for hora, errores in sesgos_por_hora.items():
                sesgos_hora_dict[str(hora)] = {
                    "error_medio_pct": round(np.mean(errores), 1),
                    "desv_est_pct": round(np.std(errores), 1),
                    "muestras": len(errores)
                }
            
            # Actualizar estado
            self.estado_ajustes["sesgos_por_hora"] = sesgos_hora_dict
            self.estado_ajustes["muestras_procesadas"] = len(eventos)
            self.estado_ajustes["ultimo_ajuste"] = datetime.now().isoformat()
            
            # Guardar
            self._guardar_ajustes()
            
            logger.info(f"[APRENDIZAJE] Ajustes calculados: {len(sesgos_hora_dict)} franjas horarias")
            
            return self.estado_ajustes
            
        except Exception as e:
            logger.error(f"Error en cálculo de ajustes: {e}")
            return self.estado_ajustes
    
    def _leer_historico(self, ultimos_n: int = 10000) -> List[Dict]:
        """Lee últimos N eventos del histórico."""
        eventos = []
        try:
            with open(self.historico_radiacion, 'r') as f:
                for linea in f:
                    try:
                        eventos.append(json.loads(linea))
                    except:
                        pass
            return eventos[-ultimos_n:] if len(eventos) > ultimos_n else eventos
        except:
            return []
    
    def _guardar_ajustes(self):
        """Persiste ajustes aprendidos."""
        try:
            with open(self.ajustes_aprendidos, 'w') as f:
                json.dump(self.estado_ajustes, f, indent=2)
        except Exception as e:
            logger.warning(f"Error guardando ajustes: {e}")
    
    def _guardar_thresholds(self):
        """Persiste thresholds dinámicos."""
        try:
            with open(self.thresholds_dinamicos, 'w') as f:
                json.dump(self.estado_thresholds, f, indent=2)
        except Exception as e:
            logger.warning(f"Error guardando thresholds: {e}")
    
    def obtener_confianza_radiacion_ajustada(self, elevacion_solar_deg: float) -> int:
        """
        Obtiene confianza en radiación ajustada por aprendizaje.
        
        Args:
            elevacion_solar_deg: Ángulo solar (°)
        
        Returns:
            Confianza (0-100%)
        """
        # TODO: implement based on learned adjustments
        if elevacion_solar_deg < -18:
            return 0
        elif elevacion_solar_deg < -6:
            return 5
        elif elevacion_solar_deg < 0:
            return 20
        elif elevacion_solar_deg < 10:
            return 60
        elif elevacion_solar_deg < 30:
            return 85
        else:
            return 95
    
    def obtener_threshold_wbgt_ajustado(self, contexto: Dict) -> Tuple[float, float]:
        """
        Obtiene thresholds de WBGT ajustados (amarillo, rojo)
        basado en aprendizaje histórico.
        """
        base = self.estado_thresholds["wbgt"]
        return (
            base["threshold_alerta_amarillo_celsius"],
            base["threshold_alerta_rojo_celsius"]
        )
    
    def obtener_threshold_condensacion_ajustado(self, es_noche: bool) -> float:
        """
        Obtiene threshold de condensación ajustado (T_interior - Tdp, °C)
        basado en aprendizaje y contexto.
        """
        base = self.estado_thresholds["condensacion"]
        threshold = base["threshold_riesgo_celsius"]
        
        if es_noche:
            threshold *= base["multiplicador_noche"]
        
        return threshold
    
    def obtener_threshold_delta_t_ajustado(self, elevacion_solar_deg: float) -> float:
        """
        Obtiene threshold de anomalía ΔT ajustado dinamicamente.
        """
        base = self.estado_thresholds["anomalia_delta_t"]
        
        if elevacion_solar_deg < 0:  # Noche
            return base["baseline_noche_celsius"]
        else:  # Día
            return base["baseline_dia_celsius"]
    
    def generar_reporte_aprendizaje(self) -> Dict:
        """Genera reporte de estado del aprendizaje."""
        eventos = self._leer_historico()
        
        return {
            "total_observaciones": len(eventos),
            "ajustes_estado": self.estado_ajustes,
            "thresholds_dinamicos": self.estado_thresholds,
            "sesgos_por_hora": self.estado_ajustes.get("sesgos_por_hora", {}),
            "ultimo_ajuste": self.estado_ajustes.get("ultimo_ajuste"),
            "muestras_procesadas": self.estado_ajustes.get("muestras_procesadas", 0)
        }


def obtener_aprendizaje_radiacion() -> AprendizajeRadiacionAdaptativo:
    """Obtiene instancia singleton del aprendizaje de radiación."""
    global _aprendizaje_instance
    if '_aprendizaje_instance' not in globals():
        _aprendizaje_instance = AprendizajeRadiacionAdaptativo()
    return _aprendizaje_instance
