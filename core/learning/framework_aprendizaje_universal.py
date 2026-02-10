"""
FRAMEWORK UNIVERSAL DE APRENDIZAJE - MeteoSerV3 V50.5
═══════════════════════════════════════════════════════════════════════════════════
Sistema centralizado de aprendizaje para TODOS los índices, sensores y predicciones.

ARQUITECTURA:
1. Cada módulo registra predicción + contexto (ej: WBGT=28°C, confidence=95%)
2. Históricos acumulan predicción vs realidad
3. Sistema detecta errores sistemáticos por:
   - Hora del día
   - Contexto solar (noche/día)
   - Condiciones atmosféricas
   - Estación del año
   - Elevación solar
4. Auto-ajusta parámetros:
   - Factores correctivos
   - Thresholds de alertas
   - Pesos de fusión
   - Confianzas predichas
5. Sin código adicional en módulos - es transparente

FLUJO:
  Predicción (ej: WBGT=28°C) 
    → registrar_prediccion("wbgt", 28.0, {"contexto": {...}})
    → [almacena en histórico]
    
  Realidad (temperatura de globo real = 28.5°C)
    → registrar_observacion("wbgt", 28.5)
    → [compara con predicción registrada]
    → [calcula error = 0.5°C]
    → [actualiza modelo de corrección]
  
  Próxima predicción (WBGT con aprendizaje)
    → obtener_prediccion("wbgt", 28.0)
    → aplica corrección aprendida automáticamente
    → retorna WBGT 28.5°C (corregido)

Módulos que DEBEN usar este framework:
- core/indices/environmental_indices.py (WBGT, ET0)
- core/indices/deardorff_force_restore.py (T_mín)
- core/indices/et_nocturna_wright.py (ET0 nocturna)
- core/sensors/sensores_virtuales/* (todos)
- core/sensors/ml_ponderaciones_adaptativas.py (ya usa feedback, integrar aquí)
- Predicciones de lluvia, presión, etc.

Autor: V50.5 (Feb 10, 2026)
"""

import logging
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple
from collections import defaultdict
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class TipoIndice(Enum):
    """Tipos de índices/sensores que pueden aprender."""
    WBGT = "wbgt"
    ET0 = "et0"
    ET0_NOCTURNA = "et0_nocturna"
    TEMPERATURA_MINIMA = "temperatura_minima"
    PUNTO_ROCIO = "punto_rocio"
    PREDICCION_LLUVIA = "prediccion_lluvia"
    HUMEDAD_SUELO = "humedad_suelo"
    RADIACION = "radiacion"
    PRESION = "presion"
    VELOCIDAD_VIENTO = "velocidad_viento"
    SENSOR_VIRTUAL = "sensor_virtual"  # Cualquier sensor sintético
    ALERTA = "alerta"  # Alertas y umbrales
    FUSION = "fusion"  # Fusión de sensores


class FrameworkAprendizajeUniversal:
    """
    Sistema centralizado de aprendizaje para todo MeteoSerV3.
    
    Cada índice, sensor, predicción puede registrarse y aprender automáticamente
    de sus errores históricos sin cambios de código en los módulos.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Almacenamiento de históricos por tipo de índice
        self.historico_predicciones = self.data_dir / "historico_predicciones_universal.jsonl"
        self.ajustes_aprendidos = self.data_dir / "ajustes_aprendizaje_universal.json"
        
        # Estado en memoria (para velocidad)
        self.predicciones_pendientes = defaultdict(list)  # {"wbgt": [{"pred": 28, "ts": ...}, ...]}
        self.modelos_aprendidos = self._cargar_modelos_aprendidos()
        
        # Estadísticas de error por contexto
        self.errores_por_contexto = defaultdict(lambda: defaultdict(list))  # {tipo_indice: {contexto: [errores]}}
    
    def _cargar_modelos_aprendidos(self) -> Dict:
        """Carga modelos/ajustes previamente aprendidos."""
        if self.ajustes_aprendidos.exists():
            try:
                with open(self.ajustes_aprendidos, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando modelos aprendidos: {e}")
        
        # Estructura inicial
        return {
            "tipos_indice": {},  # {tipo: {parámetros aprendidos}}
            "correlaciones": {},  # Qué índices se correlacionan
            "ultimo_ajuste": None,
            "total_observaciones": 0
        }
    
    def registrar_prediccion(
        self,
        tipo_indice: str,  # ej: "wbgt", "et0", "temperatura_minima"
        prediccion: float,
        contexto: Optional[Dict] = None,
        confianza_prediccion: Optional[float] = None,
        timestamp_prediccion: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Registra una predicción para posterior comparación con realidad.
        
        Args:
            tipo_indice: Tipo de índice ("wbgt", "et0", etc.)
            prediccion: Valor predicho
            contexto: Dict con contexto (elevacion_solar, hora, estado, etc.)
            confianza_prediccion: Confianza en predicción (0-100%)
            timestamp_prediccion: Momento de predicción
            metadata: Información adicional (modelo usado, etc.)
        
        Returns:
            ID de predicción para matchear con observación posterior
        """
        try:
            if timestamp_prediccion is None:
                timestamp_prediccion = datetime.now(timezone.utc)
            
            prediccion_id = f"{tipo_indice}_{timestamp_prediccion.timestamp()}_{np.random.randint(1000)}"
            
            evento = {
                "id": prediccion_id,
                "tipo_indice": tipo_indice,
                "prediccion": float(prediccion),
                "confianza_prediccion": float(confianza_prediccion) if confianza_prediccion else None,
                "timestamp_prediccion": timestamp_prediccion.isoformat(),
                "contexto": contexto or {},
                "metadata": metadata or {},
                "observacion": None,  # Se llena después
                "error": None,
                "error_relativo_pct": None
            }
            
            # Guardar en histórico
            with open(self.historico_predicciones, 'a') as f:
                f.write(json.dumps(evento) + '\n')
            
            # Guardar en memoria para lookup rápido
            self.predicciones_pendientes[tipo_indice].append({
                "id": prediccion_id,
                "prediccion": prediccion,
                "ts": timestamp_prediccion,
                "evento": evento
            })
            
            logger.debug(f"[APRENDIZAJE] Predicción registrada: {tipo_indice}={prediccion:.1f} (id={prediccion_id[:20]}...)")
            
            return prediccion_id
            
        except Exception as e:
            logger.error(f"Error registrando predicción: {e}")
            return None
    
    def registrar_observacion(
        self,
        tipo_indice: str,
        observacion: float,
        prediccion_id: Optional[str] = None,
        contexto: Optional[Dict] = None,
        timestamp_observacion: Optional[datetime] = None
    ):
        """
        Registra la observación real (realidad) para comparar con predicción.
        Se empareja automáticamente con predicción más reciente del mismo tipo.
        
        Args:
            tipo_indice: Tipo de índice
            observacion: Valor observado (real)
            prediccion_id: ID de predicción específica (opcional, si no empareja automáticamente)
            contexto: Contexto de observación
            timestamp_observacion: Momento de observación
        """
        try:
            if timestamp_observacion is None:
                timestamp_observacion = datetime.now(timezone.utc)
            
            # Encontrar predicción para emparejar
            if prediccion_id is None and self.predicciones_pendientes[tipo_indice]:
                # Usar la más reciente
                evento_pred = self.predicciones_pendientes[tipo_indice][-1]["evento"]
                prediccion_id = evento_pred["id"]
                prediccion_valor = evento_pred["prediccion"]
            else:
                # Buscar por ID en histórico
                prediccion_valor = None
                evento_pred = None
            
            # Calcular error
            if prediccion_valor is not None:
                error_absoluto = observacion - prediccion_valor
                error_relativo = 100 * error_absoluto / max(1, abs(prediccion_valor))
            else:
                error_absoluto = None
                error_relativo = None
            
            # Registrar observación
            evento_obs = {
                "tipo_indice": tipo_indice,
                "prediccion_id": prediccion_id,
                "observacion": float(observacion),
                "prediccion": prediccion_valor,
                "error_absoluto": error_absoluto,
                "error_relativo_pct": error_relativo,
                "timestamp_observacion": timestamp_observacion.isoformat(),
                "contexto": contexto or {}
            }
            
            with open(self.historico_predicciones, 'a') as f:
                f.write(json.dumps(evento_obs) + '\n')
            
            logger.debug(f"[APRENDIZAJE] Observación registrada: {tipo_indice}={observacion:.1f}, "
                        f"error={error_relativo:.1f}%" if error_relativo else "")
            
            # Guardar error para análisis posterior
            contexto_clave = self._generar_clave_contexto(contexto or {})
            self.errores_por_contexto[tipo_indice][contexto_clave].append(error_absoluto)
            
        except Exception as e:
            logger.error(f"Error registrando observación: {e}")
    
    def calcular_ajustes(self, muestras_minimas: int = 100) -> Dict:
        """
        Analiza históricos y calcula ajustes óptimos para todos los índices.
        Ejecutar periódicamente (ej: cada 1000 observaciones).
        
        Returns:
            Dict con ajustes calculados por tipo de índice
        """
        try:
            eventos = self._leer_historico()
            
            if len(eventos) < muestras_minimas:
                logger.info(f"[APRENDIZAJE] Insuficientes muestras ({len(eventos)}/{muestras_minimas})")
                return self.modelos_aprendidos
            
            logger.info(f"[APRENDIZAJE] Procesando {len(eventos)} predicciones para ajustes")
            
            # Agrupar observaciones por tipo de índice
            observaciones_por_tipo = defaultdict(list)
            
            for evento in eventos:
                if "observacion" in evento:  # Es una observación (realidad)
                    tipo = evento.get("tipo_indice")
                    error = evento.get("error_relativo_pct", 0.0)
                    contexto = evento.get("contexto", {})
                    observaciones_por_tipo[tipo].append({
                        "error": error,
                        "contexto": contexto,
                        "observacion": evento.get("observacion"),
                        "prediccion": evento.get("prediccion")
                    })
            
            # Calcular ajustes por tipo de índice
            ajustes_nuevos = {}
            
            for tipo_indice, observaciones in observaciones_por_tipo.items():
                if len(observaciones) < 20:  # Mínimo 20 observaciones por tipo
                    continue
                
                # Estadísticas básicas
                errores = [o["error"] for o in observaciones if o["error"] is not None]
                error_medio = np.mean(errores) if errores else 0
                desv_est = np.std(errores) if len(errores) > 1 else 0
                
                # Ajustes por contexto (hora, elevación, etc.)
                errores_por_contexto = defaultdict(list)
                for obs in observaciones:
                    ctx_key = self._generar_clave_contexto(obs["contexto"])
                    errores_por_contexto[ctx_key].append(obs["error"])
                
                # Calcular factores de corrección
                factores_correccion = {}
                for ctx_key, errs in errores_por_contexto.items():
                    err_medio_ctx = np.mean(errs)
                    # Factor: si error promedio es -5% (predicción 5% baja), multiplicar por 1.05
                    if err_medio_ctx != 0:
                        factor = 1.0 - (err_medio_ctx / 100.0) * 0.5  # Suavizar corrección (50%)
                        factores_correccion[ctx_key] = max(0.7, min(1.3, factor))  # Clamp [0.7, 1.3]
                
                # Determinar si modelo es confiable
                confiabilidad = max(0, 100 - abs(error_medio) * 2)  # Penaliza error medio
                
                ajustes_nuevos[tipo_indice] = {
                    "error_medio_pct": round(error_medio, 2),
                    "desv_est_pct": round(desv_est, 2),
                    "confiabilidad_pct": round(confiabilidad, 1),
                    "muestras": len(observaciones),
                    "factores_correccion": factores_correccion,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"[APRENDIZAJE] {tipo_indice}: error_medio={error_medio:.2f}%, "
                           f"confiabilidad={confiabilidad:.0f}%, muestras={len(observaciones)}")
            
            # Actualizar modelos
            self.modelos_aprendidos["tipos_indice"].update(ajustes_nuevos)
            self.modelos_aprendidos["ultimo_ajuste"] = datetime.now(timezone.utc).isoformat()
            self.modelos_aprendidos["total_observaciones"] = len(eventos)
            
            self._guardar_modelos()
            
            return self.modelos_aprendidos
            
        except Exception as e:
            logger.error(f"Error calculando ajustes: {e}")
            return self.modelos_aprendidos
    
    def obtener_prediccion_corregida(
        self,
        tipo_indice: str,
        prediccion: float,
        contexto: Optional[Dict] = None
    ) -> Tuple[float, float]:
        """
        Retorna predicción corregida según aprendizaje histórico.
        
        Args:
            tipo_indice: Tipo de índice
            prediccion: Valor predicho sin corrección
            contexto: Contexto actual
        
        Returns:
            Tuple[prediccion_corregida, confianza (0-100)]
        """
        try:
            modelo = self.modelos_aprendidos.get("tipos_indice", {}).get(tipo_indice)
            
            if not modelo or not modelo.get("factores_correccion"):
                # No hay aprendizaje aún, retornar sin cambios
                return prediccion, 50.0  # Confianza media por defecto
            
            # Generar contexto clave y buscar factor de corrección
            ctx_key = self._generar_clave_contexto(contexto or {})
            
            # Intentar match exacto, luego match parcial
            factor = modelo["factores_correccion"].get(ctx_key)
            
            if factor is None:
                # Fallback: usar factor promedio si no hay match exacto
                factores = list(modelo["factores_correccion"].values())
                factor = np.mean(factores) if factores else 1.0
            
            # Aplicar corrección
            prediccion_corregida = prediccion * factor
            
            # Confianza = 100% - error_medio_pct (con techo)
            confianza = min(95.0, max(20.0, 100.0 - abs(modelo.get("error_medio_pct", 0))))
            
            logger.debug(f"[APRENDIZAJE] {tipo_indice}: {prediccion:.1f} → {prediccion_corregida:.1f} "
                        f"(factor={factor:.2f}, confianza={confianza:.0f}%)")
            
            return prediccion_corregida, confianza
            
        except Exception as e:
            logger.warning(f"Error corrigiendo predicción: {e}")
            return prediccion, 50.0
    
    def _generar_clave_contexto(self, contexto: Dict) -> str:
        """Genera clave única para agrupar por contexto."""
        try:
            # Extraer características clave del contexto
            hora = contexto.get("hora", "XX")
            estado_solar = contexto.get("estado_solar", "desconocido")[:3]  # Primeras 3 letras
            elevacion = int(contexto.get("elevacion_solar_deg", 0) / 5) * 5  # Bucketing cada 5°
            estacion = contexto.get("estacion", "XX")[:2]
            
            return f"{hora}_{estado_solar}_{elevacion}_{estacion}"
        except:
            return "general"
    
    def _leer_historico(self, ultimos_n: int = 20000) -> List[Dict]:
        """Lee últimas N líneas del histórico."""
        eventos = []
        try:
            with open(self.historico_predicciones, 'r') as f:
                for linea in f:
                    try:
                        eventos.append(json.loads(linea))
                    except:
                        pass
            return eventos[-ultimos_n:] if len(eventos) > ultimos_n else eventos
        except:
            return []
    
    def _guardar_modelos(self):
        """Persiste modelos aprendidos."""
        try:
            with open(self.ajustes_aprendidos, 'w') as f:
                json.dump(self.modelos_aprendidos, f, indent=2)
        except Exception as e:
            logger.warning(f"Error guardando modelos: {e}")
    
    def generar_reporte_aprendizaje(self) -> Dict:
        """Genera reporte completo del estado de aprendizaje."""
        eventos = self._leer_historico()
        
        # Contar predicciones vs observaciones
        predicciones = len([e for e in eventos if "prediccion" in e and "observacion" not in e])
        observaciones = len([e for e in eventos if "observacion" in e])
        
        # Agrupar modelos por tipo
        resumen_por_tipo = {}
        for tipo, modelo in self.modelos_aprendidos.get("tipos_indice", {}).items():
            resumen_por_tipo[tipo] = {
                "error_medio": modelo.get("error_medio_pct", 0),
                "confiabilidad": modelo.get("confiabilidad_pct", 0),
                "muestras": modelo.get("muestras", 0),
                "contextos_aprendidos": len(modelo.get("factores_correccion", {}))
            }
        
        return {
            "total_predicciones_registradas": predicciones,
            "total_observaciones_registradas": observaciones,
            "tasa_matching_pct": 100 * observaciones / max(1, predicciones) if predicciones > 0 else 0,
            "modelos_aprendidos": resumen_por_tipo,
            "ultimo_ajuste": self.modelos_aprendidos.get("ultimo_ajuste"),
            "tipos_indice_activos": list(self.modelos_aprendidos.get("tipos_indice", {}).keys())
        }


# Instancia global singleton
_framework_instance = None

def obtener_framework_aprendizaje() -> FrameworkAprendizajeUniversal:
    """Obtiene instancia singleton del framework de aprendizaje."""
    global _framework_instance
    if _framework_instance is None:
        _framework_instance = FrameworkAprendizajeUniversal()
    return _framework_instance
