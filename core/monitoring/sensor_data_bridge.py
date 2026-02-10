"""
Puente de datos: conecta last_sensores.json con el motor de duelos.

Este módulo asegura que el motor de duelos SIEMPRE tenga datos disponibles,
leyendo de last_sensores.json y rellenando el histórico del sistema.
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger("meteoser.sensor_data_bridge")


class SensorDataBridge:
    """
    Conecta fuentes de datos (last_sensores.json, episodic_memory.db, etc.)
    con system.historial_sensores para que el motor pueda acceder.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
        self.last_sensores_path = base_dir / "data" / "last_sensores.json"
        self.sensores_historico_path = base_dir / "data" / "sensores_historico.json"
        self.max_historico = 1000  # Muestras por parámetro
        
        # Cache de último acceso
        self._last_load_ts = 0
        self._cache_interval = 5  # segundos entre recargas
        self._cached_data = {}

    def cargar_y_llenar(self, system) -> int:
        """
        Lee last_sensores.json y llena system.historial_sensores.
        Retorna cantidad de parámetros rellenados.
        """
        ahora = time.time()
        
        # Cache: no recargar si es muy reciente
        if (ahora - self._last_load_ts) < self._cache_interval:
            return self._aplicar_cache(system)
        
        datos = self._leer_last_sensores()
        if not datos:
            logger.warning("No se pudo leer last_sensores.json")
            return 0

        # Normalizar y completar sensores faltantes
        datos = self._normalizar_datos(datos)
        
        # Actualizar históricos del sistema
        rellenados = self._llenar_historial_sistema(system, datos, ahora)
        
        # Persistir para auditorías futuras
        self._persistir_historico(datos, ahora)
        
        self._last_load_ts = ahora
        self._cached_data = datos
        
        return rellenados

    def _leer_last_sensores(self) -> Dict[str, Any]:
        """Lee y parsea last_sensores.json."""
        if not self.last_sensores_path.exists():
            return {}
        
        try:
            raw = json.loads(self.last_sensores_path.read_text(encoding="utf-8"))
            return raw
        except Exception as e:
            logger.error(f"Error leyendo last_sensores.json: {e}")
            return {}

    def _normalizar_datos(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Completa valores faltantes y normaliza unidades para el motor.
        No modifica el archivo fuente, solo el payload en memoria.
        """
        sensores = dict(datos.get("sensores", {}) or {})
        timestamps = dict(datos.get("timestamps", {}) or {})

        # Helpers de conversión
        def _to_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return None

        def _f_to_c(f):
            v = _to_float(f)
            if v is None:
                return None
            return (v - 32.0) * 5.0 / 9.0

        def _mph_to_kmh(mph):
            v = _to_float(mph)
            if v is None:
                return None
            return v * 1.60934

        def _inhg_to_hpa(inhg):
            v = _to_float(inhg)
            if v is None:
                return None
            return v * 33.8638866667

        def _in_to_mm(inches):
            v = _to_float(inches)
            if v is None:
                return None
            return v * 25.4

        # Temperatura (°C)
        if sensores.get("temperatura") is None:
            sensores["temperatura"] = (
                _to_float(sensores.get("temperatura_interior"))
                or _f_to_c(sensores.get("tempf_original"))
                or _f_to_c(sensores.get("tempinf_original"))
            )

        # Humedad (%)
        if sensores.get("humedad") is None:
            sensores["humedad"] = (
                _to_float(sensores.get("humedad_interior"))
                or _to_float(sensores.get("humidity_original"))
                or _to_float(sensores.get("humidityin_original"))
            )

        # Viento (km/h)
        if sensores.get("viento") is None:
            sensores["viento"] = _mph_to_kmh(sensores.get("windspeedmph_original"))

        # Presión (hPa)
        if sensores.get("presion") is None:
            sensores["presion"] = (
                _to_float(sensores.get("presion"))
                or _inhg_to_hpa(sensores.get("baromrelin_original"))
                or _inhg_to_hpa(sensores.get("baromabsin_original"))
            )

        # Radiación (W/m2)
        if sensores.get("radiacion") is None:
            sensores["radiacion"] = _to_float(sensores.get("solarradiation_original"))

        # UV
        if sensores.get("uv") is None:
            sensores["uv"] = _to_float(sensores.get("uv_original"))

        # Lluvia rate (mm/h)
        if sensores.get("lluvia_rate") is None:
            sensores["lluvia_rate"] = _in_to_mm(sensores.get("rainratein_original"))

        # Timestamp base si faltan
        ts_base = timestamps.get("ultimo_ecowitt") or time.time()
        for key in ["temperatura", "humedad", "viento", "presion", "radiacion", "uv", "lluvia_rate"]:
            if key in sensores and key not in timestamps:
                timestamps[key] = ts_base

        return {
            "sensores": sensores,
            "timestamps": timestamps,
        }

    def _llenar_historial_sistema(
        self,
        system,
        datos: Dict[str, Any],
        ts: float
    ) -> int:
        """
        Rellena system.historial_sensores con los datos actuales.
        Mantiene deques de hasta max_historico muestras.
        """
        if not hasattr(system, "historial_sensores"):
            system.historial_sensores = {}
        
        sensores = datos.get("sensores", {})
        timestamps = datos.get("timestamps", {})
        
        rellenados = 0
        for param_name, valor in sensores.items():
            if valor is None:
                continue
            
            # Inicializar deque si no existe
            if param_name not in system.historial_sensores:
                system.historial_sensores[param_name] = deque(maxlen=self.max_historico)
            
            # Obtener timestamp específico o usar el actual
            param_ts = timestamps.get(param_name, ts)
            
            # Agregar a histórico (tupla: (timestamp, valor))
            try:
                system.historial_sensores[param_name].append((float(param_ts), float(valor)))
                rellenados += 1
            except (ValueError, TypeError):
                continue
        
        logger.debug(f"SensorDataBridge: {rellenados} parámetros rellenados en historial_sensores")
        return rellenados

    def _persistir_historico(self, datos: Dict[str, Any], ts: float) -> None:
        """
        Persiste los datos en sensores_historico.json para auditorías.
        Mantiene los últimos N registros para análisis histórico.
        """
        try:
            # Leer histórico existente
            historico_data = []
            if self.sensores_historico_path.exists():
                try:
                    historico_data = json.loads(
                        self.sensores_historico_path.read_text(encoding="utf-8")
                    )
                    if not isinstance(historico_data, list):
                        historico_data = []
                except Exception:
                    historico_data = []
            
            # Agregar nuevo registro
            record = {
                "timestamp": ts,
                "sensores": datos.get("sensores", {}),
                "timestamps": datos.get("timestamps", {})
            }
            historico_data.append(record)
            
            # Mantener últimas N muestras (evitar archivos enormes)
            max_records = 10000  # ~2 semanas si se actualiza cada minuto
            if len(historico_data) > max_records:
                historico_data = historico_data[-max_records:]
            
            # Escribir
            self.sensores_historico_path.write_text(
                json.dumps(historico_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
        except Exception as e:
            logger.error(f"Error persistiendo sensores_historico.json: {e}")

    def _aplicar_cache(self, system) -> int:
        """Aplica datos cacheados sin releer."""
        if not self._cached_data:
            return 0
        return self._llenar_historial_sistema(system, self._cached_data, time.time())

    def obtener_historico_parametro(
        self,
        parametro: str,
        max_muestras: int = 100
    ) -> List[Tuple[float, float]]:
        """
        Obtiene histórico completo de un parámetro desde sensores_historico.json.
        Útil para análisis post-duelos.
        """
        if not self.sensores_historico_path.exists():
            return []
        
        try:
            historico_data = json.loads(
                self.sensores_historico_path.read_text(encoding="utf-8")
            )
            if not isinstance(historico_data, list):
                return []
            
            muestras = []
            for record in historico_data[-max_muestras:]:
                sensores = record.get("sensores", {})
                timestamps = record.get("timestamps", {})
                
                if parametro in sensores:
                    valor = sensores[parametro]
                    ts = timestamps.get(parametro, record.get("timestamp", 0))
                    
                    if valor is not None:
                        try:
                            muestras.append((float(ts), float(valor)))
                        except (ValueError, TypeError):
                            continue
            
            return muestras
        
        except Exception as e:
            logger.error(f"Error leyendo histórico de {parametro}: {e}")
            return []

    def estadisticas_parametro(self, parametro: str) -> Optional[Dict[str, float]]:
        """
        Calcula estadísticas básicas del histórico de un parámetro.
        """
        muestras = self.obtener_historico_parametro(parametro, max_muestras=1000)
        
        if not muestras:
            return None
        
        valores = [v for _, v in muestras]
        
        import statistics
        
        return {
            "count": len(valores),
            "mean": statistics.mean(valores),
            "stdev": statistics.stdev(valores) if len(valores) > 1 else 0.0,
            "min": min(valores),
            "max": max(valores),
            "range": max(valores) - min(valores),
        }
