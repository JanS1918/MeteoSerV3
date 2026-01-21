# ============================================================
# MÓDULO D — SYSTEM CORE (NÚCLEO OPERATIVO)
# ============================================================

EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales

import json
import time
from pathlib import Path
from typing import Any


class SystemCore:
    def autoexpandir_formulas(self, indices_actuales: dict, propuestas: list):
        """
        Recibe una lista de propuestas de fórmulas (dicts con nombre, expresion, entradas, descripcion).
        Solo registra aquellas que refuercen, amplíen o aporten valor adicional (no redundantes).
        Devuelve lista de fórmulas realmente añadidas.
        """
        nuevas = []
        for prop in propuestas:
            nombre = prop.get("nombre")
            expr = prop.get("expresion")
            entradas = prop.get("entradas", [])
            desc = prop.get("descripcion", "")
            if not nombre or not expr:
                continue
            # Si ya existe una fórmula con ese nombre, solo la sustituye si la nueva es más completa
            existente = self.formulas.get(nombre)
            if existente:
                # Si la expresión es idéntica o menos completa, no la añade
                if existente["expresion"] == expr or set(entradas).issubset(set(existente.get("entradas", []))):
                    continue
                # Si la nueva fórmula usa más entradas o lógica más rica, la sustituye
                if len(entradas) > len(existente.get("entradas", [])):
                    self.registrar_formula(nombre, expr, entradas, desc)
                    nuevas.append(nombre)
            else:
                # Solo añade si el índice/sensor no existe o la fórmula aporta un valor nuevo
                if nombre not in indices_actuales:
                    self.registrar_formula(nombre, expr, entradas, desc)
                    nuevas.append(nombre)
        return nuevas
    """
    Núcleo del sistema MeteoSer.
    Gestiona sensores, índices y recomendaciones.
    """

    def obtener_historial_original(self, nombre):
        """Devuelve el historial de valores originales grabados para un sensor."""
        if hasattr(self, "historial_originales"):
            return self.historial_originales.get(nombre + "_original", [])
        return []

    def __init__(self):
        # Registrar sensores HP2550A/Ecowitt por defecto
        self.sensores = {
            "temperatura": None,
            "humedad": None,
            "viento": None,
            "lluvia": None,
            "radiacion": None
        }
        self.formulas = {}
        self.sensores_timestamp = {}
        self.sensores_metadata = {}
        self.sensores_derivados = {}
        self.sensores_derivados_metadata = {}
        self.historial_sensores = {}
        self.indices = {}
        self.recommendation_engine = None
        self.auto_improvement_engine = None
        self.auto_improvement_system = None
        self.bloque_a = None
        self.bloque_b = None
        self.bloque_c = None
        self.bloque_d = None
        self.bloque_e = None
        self.bloque_f = None
        self.bloque_g = None
        self.bloque_h = None
        # Calibraciones globales por sensor
        self._sensores_crudos: dict[str, Any] = {}
        self._sensor_calibration_info: dict[str, dict] = {}
        self._sensor_ewma_state: dict[str, float] = {}
        self._sensor_ewma_applied: dict[str, bool] = {}
        self._cargar_sensores_persistidos()
        self._cargar_formulas_persistidas()
        # Cargar metadata de sensores si existe (offset/scale/ewma defaults)
        try:
            self._cargar_sensores_metadata()
        except Exception:
            pass
        try:
            self._load_sensor_ewma_state()
        except Exception:
            pass

    def registrar_sensor_metadata(self, nombre, tipo=None, unidad=None, fuente=None, fiabilidad=100.0, origen=None,
                                  offset=None, scale=None, ewma_alpha=None):
        if nombre not in self.sensores_metadata:
            self.sensores_metadata[nombre] = {}
        meta = self.sensores_metadata[nombre]
        if tipo is not None:
            meta["tipo"] = tipo
        if unidad is not None:
            meta["unidad"] = unidad
        if fuente is not None:
            meta["fuente"] = fuente
        if origen is not None:
            meta["origen"] = origen
        if fiabilidad is not None:
            meta["fiabilidad"] = fiabilidad
        if offset is not None:
            meta["offset"] = offset
        if scale is not None:
            meta["scale"] = scale
        if ewma_alpha is not None:
            meta["ewma_alpha"] = ewma_alpha

    def obtener_sensor_metadata(self, nombre):
        return self.sensores_metadata.get(nombre)

    def _ruta_sensores_persistidos(self) -> Path:
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "last_sensores.json"

    def _ruta_formulas_persistidas(self) -> Path:
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "formulas.json"

    def _cargar_formulas_persistidas(self):
        ruta = self._ruta_formulas_persistidas()
        if not ruta.exists():
            return
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.formulas.update(data)
        except Exception:
            pass

    def _ruta_sensores_metadata(self) -> Path:
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "sensores_metadata.json"

    def _cargar_sensores_metadata(self):
        ruta = self._ruta_sensores_metadata()
        if not ruta.exists():
            return
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # Merge without overwriting existing entries
                for k, v in data.items():
                    if k not in self.sensores_metadata:
                        self.sensores_metadata[k] = v
                    else:
                        # merge keys
                        meta = self.sensores_metadata[k]
                        if isinstance(v, dict):
                            for kk, vv in v.items():
                                if kk not in meta:
                                    meta[kk] = vv
        except Exception:
            pass

    def _sensor_ewma_state_path(self) -> Path:
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "sensor_ewma_state.json"

    def _load_sensor_ewma_state(self):
        ruta = self._sensor_ewma_state_path()
        if not ruta.exists():
            return
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for nombre, valor in data.items():
                    try:
                        self._sensor_ewma_state[nombre] = float(valor)
                    except Exception:
                        continue
        except Exception:
            pass

    def _save_sensor_ewma_state(self):
        ruta = self._sensor_ewma_state_path()
        try:
            ruta.write_text(json.dumps(self._sensor_ewma_state, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _calibrate_sensor_value(self, nombre, valor):
        info: dict[str, Any] = {}
        try:
            meta = self.obtener_sensor_metadata(nombre) or {}
        except Exception:
            meta = {}
        info["valor_crudo"] = valor
        try:
            raw_val = float(valor)
        except Exception:
            info["aplicado_ewma"] = False
            self._sensor_ewma_applied[nombre] = False
            self._sensor_calibration_info[nombre] = info
            return valor, info
        try:
            offset = float(meta.get("offset", 0.0))
        except Exception:
            offset = 0.0
        try:
            scale = float(meta.get("scale", 1.0))
        except Exception:
            scale = 1.0
        ewma_alpha = meta.get("ewma_alpha")
        try:
            ewma_alpha = None if ewma_alpha is None else float(ewma_alpha)
        except Exception:
            ewma_alpha = None
        calibrated = raw_val * scale + offset
        final_val = calibrated
        aplicado_ewma = False
        if ewma_alpha is not None and 0.0 < ewma_alpha <= 1.0:
            prev = self._sensor_ewma_state.get(nombre)
            if prev is None:
                ewma_val = calibrated
            else:
                ewma_val = ewma_alpha * calibrated + (1.0 - ewma_alpha) * prev
            final_val = ewma_val
            self._sensor_ewma_state[nombre] = ewma_val
            aplicado_ewma = True
            self._sensor_ewma_applied[nombre] = True
            self._save_sensor_ewma_state()
        else:
            self._sensor_ewma_applied[nombre] = False
        info.update({
            "valor_crudo": raw_val,
            "valor_calibrado": calibrated,
            "valor_final": final_val,
            "offset": offset,
            "scale": scale,
            "ewma_alpha": ewma_alpha,
            "aplicado_ewma": aplicado_ewma,
        })
        self._sensor_calibration_info[nombre] = info
        return final_val, info

    def obtener_sensor_crudo(self, nombre):
        return self._sensores_crudos.get(nombre)

    def obtener_sensor_calibration_info(self, nombre):
        return self._sensor_calibration_info.get(nombre, {}).copy()

    def _cargar_sensores_persistidos(self):
        ruta = self._ruta_sensores_persistidos()
        if not ruta.exists():
            return
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            valores = data.get("sensores", {})
            timestamps = data.get("timestamps", {})
            if isinstance(valores, dict):
                self.sensores.update(valores)
            if isinstance(timestamps, dict):
                self.sensores_timestamp.update(timestamps)
        except Exception:
            pass

    # --------------------------------------------------------
    # REGISTRO DE SENSORES
    # --------------------------------------------------------
    def registrar_sensor(self, nombre, valor_inicial=None):
        self.sensores[nombre] = valor_inicial

    def actualizar_sensor(self, nombre, valor):
        # Guardar todos los valores, incluyendo los originales para trazabilidad
        self._sensores_crudos[nombre] = valor
        calibrated_val, calib_info = self._calibrate_sensor_value(nombre, valor)
        stored_val = calibrated_val
        if nombre in self.sensores:
            self.sensores[nombre] = stored_val
        else:
            self.sensores[nombre] = stored_val
        if nombre not in self.sensores_metadata and not nombre.endswith("_original"):
            self.registrar_sensor_metadata(nombre, tipo=nombre, fuente="autodetectado", origen="interno")
        # Si es un valor original, también lo guarda en un historial
        if nombre.endswith("_original"):
            if not hasattr(self, "historial_originales"):
                self.historial_originales = {}
            if nombre not in self.historial_originales:
                self.historial_originales[nombre] = []
            self.historial_originales[nombre].append(valor)
            return
        # Registrar el valor original para trazabilidad
        orig_name = f"{nombre}_original"
        if not hasattr(self, "historial_originales"):
            self.historial_originales = {}
        self.historial_originales.setdefault(orig_name, []).append(valor)
        # Guardar histórico numérico
        try:
            valor_num = float(stored_val)
        except Exception:
            valor_num = None
        if valor_num is not None:
            if nombre not in self.historial_sensores:
                self.historial_sensores[nombre] = []
            self.historial_sensores[nombre].append((time.time(), valor_num))
            if len(self.historial_sensores[nombre]) > 200:
                self.historial_sensores[nombre] = self.historial_sensores[nombre][-200:]
        # Persistir último valor real
        try:
            self.sensores_timestamp[nombre] = time.time()
            ruta = self._ruta_sensores_persistidos()
            payload = {
                "sensores": self.sensores,
                "timestamps": self.sensores_timestamp,
            }
            ruta.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def obtener_sensor(self, nombre):
        valor = self.sensores.get(nombre)
        if valor is not None:
            return valor
        if nombre in self.sensores_derivados:
            return self.sensores_derivados.get(nombre)
        return None

    def actualizar_sensor_derivado(self, nombre, valor, metadata=None):
        self.sensores_derivados[nombre] = valor
        if metadata:
            self.sensores_derivados_metadata[nombre] = metadata

    def obtener_historial_sensor(self, nombre):
        return self.historial_sensores.get(nombre, [])

    # --------------------------------------------------------
    # REGISTRO DE ÍNDICES
    # --------------------------------------------------------
    def registrar_indice(self, nombre, valor_inicial=None):
        self.indices[nombre] = valor_inicial

    def actualizar_indice(self, nombre, valor):
        # Permitir crear el índice si no existe
        self.indices[nombre] = valor

    def obtener_indice(self, nombre):
        return self.indices.get(nombre)

    # --------------------------------------------------------
    # MOTOR DE RECOMENDACIONES
    # --------------------------------------------------------
    def conectar_recommendation_engine(self, engine):
        self.recommendation_engine = engine

    def conectar_auto_improvement_engine(self, engine):
        self.auto_improvement_engine = engine

    def conectar_auto_improvement_system(self, system):
        self.auto_improvement_system = system

    def obtener_recomendacion(self):
        if not self.recommendation_engine:
            return {"estado": "Sin motor de recomendaciones.", "motivos": {}}
        return self.recommendation_engine.generar()

    # --------------------------------------------------------
    # FÓRMULAS PERSONALIZADAS
    # --------------------------------------------------------
    def registrar_formula(self, nombre, expresion, entradas, descripcion):
        if not nombre or not expresion:
            return {"status": "ERROR", "message": "Nombre y expresión obligatorios"}
        self.formulas[nombre] = {
            "expresion": expresion,
            "entradas": entradas or [],
            "descripcion": descripcion or "",
        }
        try:
            ruta = self._ruta_formulas_persistidas()
            ruta.write_text(json.dumps(self.formulas, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        return {"status": "OK", "nombre": nombre}

    def obtener_formulas(self):
        return self.formulas

    # --------------------------------------------------------
    # SNAPSHOT COMPLETO
    # --------------------------------------------------------
    def obtener_estado_completo(self):
        # Forzar siempre el cálculo de índices avanzados si existe EnvironmentalIndices
        indices = self.indices
        try:
            from core.indices.environmental_indices import EnvironmentalIndices
            if isinstance(self.indices, EnvironmentalIndices):
                indices = self.indices.obtener_todos()
        except Exception:
            pass
        return {
            "sensores": self.sensores,
            "indices": indices,
            "recomendacion": self.obtener_recomendacion()
        }

    def activar_bloques_funcionales(self):
        """
        Activa y expone las funcionalidades principales de todos los bloques A-H en el sistema.
        """
        if self.bloque_a:
            self.bloque_a.escanear_sensores()
        if self.bloque_b:
            self.bloque_b.ejecutar_regla("regla_inicial")
        if self.bloque_c:
            self.bloque_c.aprender_habito("ventilacion_diaria")
        if self.bloque_d:
            self.bloque_d.monitorizar_proceso("core")
        if self.bloque_e:
            self.bloque_e.recomendaciones_hardening()
        if self.bloque_f:
            self.bloque_f.iniciar_sesion("sistema")
        if self.bloque_g:
            self.bloque_g.replicar_estado()
        if self.bloque_h:
            self.bloque_h.crear_backup("arranque")