import logging
# ============================================================
# MÓDULO D — SYSTEM CORE (NÚCLEO OPERATIVO)
# ============================================================

EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales

import json
import time
from pathlib import Path
from typing import Dict, Any

from core.learning.learning_feedback import LearningFeedback
from core.monitoring.vanguard_ojeador import VanguardOjeador
from core.validation.sensor_anomaly_detector import SensorAnomalyDetector
from core.monitoring.formula_change_tracker import FormulaChangeTracker
from core.monitoring.formula_duel_engine import FormulaDuelEngine
try:
    from core.virtual.virtual_sensors import VirtualSensorManager
except Exception:
    VirtualSensorManager = None


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
        # Registrar sensores HP2550A/Ecowitt por defecto y presión como sensor válido
        self.sensores = {
            "temperatura": None,
            "humedad": None,
            "viento": None,
            "lluvia": None,
            "radiacion": None,
            "presion": None
        }
        self.formulas = {}
        self.sensores_timestamp = {}
        self.sensores_metadata = {}
        self.sensores_derivados = {}
        self.sensores_derivados_metadata = {}
        self.historial_sensores = {}
        self.indices = {}
        self.data: Dict[str, Any] = {}
        self.last_data_update_time = time.time()  # NEW: Track last sensor update timestamp
        self.sensores_alertas: Dict[str, Any] = {}
        self.indices_alertas: Dict[str, Any] = {}
        self.sensores_simulados: Dict[str, Any] = {}
        self.learning_feedback = LearningFeedback()
        self.sensor_monitor = SensorAnomalyDetector()
        self.ojeador = VanguardOjeador()
        self.formula_change_tracker = FormulaChangeTracker()
        self.formula_duel_engine = FormulaDuelEngine()
        self.recommendation_engine = None
        self.auto_improvement_engine = None
        self.auto_improvement_system = None
        self.virtual_manager = None
        self.virtual_sensors = {}
        self.bloque_a = None
        self.bloque_b = None
        self.bloque_c = None
        self.bloque_d = None
        self.bloque_e = None
        self.bloque_f = None
        self.bloque_g = None
        self.bloque_h = None
        self._cargar_sensores_persistidos()
        self._cargar_formulas_persistidas()
        self._inicializar_sensores_virtuales()

    def _inicializar_sensores_virtuales(self):
        """
        Registra sensores virtuales de tendencia y anomalía para todas las variables útiles,
        además de cualquier otro sensor virtual automático definido.
        """
        if VirtualSensorManager is None:
            return
        try:
            from virtual_sensors import default_specs
            self.virtual_manager = VirtualSensorManager()
            specs = default_specs()
            if isinstance(specs, dict):
                for vid, spec in specs.items():
                    if isinstance(spec, dict):
                        self.virtual_manager.register_virtual(vid, spec)
            # Si hay otros sensores virtuales automáticos definidos en soluciones_auditoría_v49, añadirlos también
            try:
                from core.indices.soluciones_auditoría_v49 import crear_sensores_virtuales_automaticos
                specs_extra = crear_sensores_virtuales_automaticos()
                if isinstance(specs_extra, dict):
                    for vid, spec in specs_extra.items():
                        if isinstance(spec, dict):
                            self.virtual_manager.register_virtual(vid, spec)
            except Exception:
                pass  # No es obligatorio
            self.virtual_sensors = self.virtual_manager.virtuals
        except Exception:
            logging.exception("Silent except at 96 - revisar contexto")

    def actualizar_sensores_virtuales(self):
        """Actualiza valores de sensores virtuales con datos actuales."""
        if not self.virtual_manager:
            return {}
        inputs = {}
        if isinstance(self.data, dict):
            inputs.update(self.data)
        if isinstance(self.sensores, dict):
            for k, v in self.sensores.items():
                if v is not None and k not in inputs:
                    inputs[k] = v
        results = self.virtual_manager.compute_all(inputs)
        self.virtual_sensors = self.virtual_manager.virtuals
        return results

    def registrar_sensor_metadata(self, nombre, tipo=None, unidad=None, fuente=None, fiabilidad=100.0, origen=None):
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
            logging.exception("Silent except at 124 - revisar contexto")

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
            logging.exception("Silent except at 139 - revisar contexto")

    # --------------------------------------------------------
    # REGISTRO DE SENSORES
    # --------------------------------------------------------
    def registrar_sensor(self, nombre, valor_inicial=None):
        self.sensores[nombre] = valor_inicial

    def actualizar_sensor(self, nombre, valor):
        # SOLDADURA DE CLAVES: Normalizar "presion" exactamente
        nombre_canon = nombre.lower().strip()
        if nombre_canon in ["pressure", "presion_relativa", "presion_absoluta", "presion_atm", "presion_barometrica", "pres", "hpa", "mbar"]:
            nombre_canon = "presion"
        
        # NEW: Update timestamp whenever a sensor changes
        self.last_data_update_time = time.time()
        
        # Guardar todos los valores, incluyendo los originales para trazabilidad
        if nombre_canon in self.sensores:
            self.sensores[nombre_canon] = valor
        else:
            self.sensores[nombre_canon] = valor
        self.data[nombre_canon] = valor
        if nombre_canon not in self.sensores_metadata and not nombre_canon.endswith("_original"):
            self.registrar_sensor_metadata(nombre_canon, tipo=nombre_canon, fuente="autodetectado", origen="interno")
        # Si es un valor original, también lo guarda en un historial
        if nombre_canon.endswith("_original"):
            if not hasattr(self, "historial_originales"):
                self.historial_originales = {}
            if nombre_canon not in self.historial_originales:
                self.historial_originales[nombre_canon] = []
            self.historial_originales[nombre_canon].append(valor)
            return
        # Guardar histórico numérico
        try:
            valor_num = float(valor)
        except Exception:
            valor_num = None
        if valor_num is not None:
            if nombre_canon not in self.historial_sensores:
                self.historial_sensores[nombre_canon] = []
            self.historial_sensores[nombre_canon].append((time.time(), valor_num))
            if len(self.historial_sensores[nombre_canon]) > 200:
                self.historial_sensores[nombre_canon] = self.historial_sensores[nombre_canon][-200:]
        
        # INYECCIÓN DE FUERZA: Si es presión, recalcular índices inmediatamente
        if nombre_canon == "presion" and hasattr(self, "indices"):
            try:
                # Purgar valores ISA/799 antiguos del cache
                if hasattr(self.indices, "_cache_indices"):
                    self.indices._cache_indices = {}
                # Forzar recálculo inmediato
                import logging
                logging.info(f"[RECALCULO] Presión Soberana actualizada a {valor_num} hPa (Fuente: HP2550A)")
                if hasattr(self.indices, "obtener_todos"):
                    self.indices.obtener_todos()
            except Exception as e:
                logging.exception("Silent except at 195 - revisar contexto")
        
        # Persistir último valor real
        try:
            self.sensores_timestamp[nombre_canon] = time.time()
            ruta = self._ruta_sensores_persistidos()
            payload = {
                "sensores": self.sensores,
                "timestamps": self.sensores_timestamp,
            }
            ruta.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            logging.exception("Silent except at 207 - revisar contexto")

    def obtener_sensor(self, nombre):
        valor = self.sensores.get(nombre)
        if valor is not None:
            return valor
        if nombre in self.sensores_derivados:
            return self.sensores_derivados.get(nombre)
        return None

    def actualizar_sensor_derivado(self, nombre, valor, metadata=None):
        self.sensores_derivados[nombre] = valor
        self.last_data_update_time = time.time()  # NEW: Update timestamp for derived sensors too
        self.data[nombre] = valor
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
        self.last_data_update_time = time.time()  # NEW: Update timestamp for indices too

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

    def evaluar_anomalias_y_simular(self):
        """Evalúa anomalías y simula valores si aplica."""
        try:
            resultados = self.sensor_monitor.process_snapshot(self)
        except Exception:
            logging.exception("Silent except at 247 - revisar contexto")
            return

        self.sensores_alertas = resultados
        self.sensores_simulados = {}

        for sensor, info in resultados.items():
            if info.get("simulado"):
                sim_val = info.get("valor_simulado")
                if sim_val is not None:
                    self.sensores[sensor] = sim_val
                    self.data[sensor] = sim_val
                    self.sensores_simulados[sensor] = sim_val
            meta = self.sensores_metadata.setdefault(sensor, {})
            meta["simulado"] = bool(info.get("simulado"))
            meta["simulado_error"] = info.get("error_estimado")
            meta["simulado_motivo"] = info.get("motivo")
            meta["simulado_timestamp"] = info.get("timestamp")

        # Índices afectados por sensores en alerta
        self.indices_alertas = {}
        try:
            from core.indices.index_catalog import INDEX_CATALOG
            for idx, meta in INDEX_CATALOG.items():
                sensores = meta.get("sensores", []) if isinstance(meta, dict) else []
                for sensor in sensores:
                    if sensor in self.sensores_alertas:
                        alerta = self.sensores_alertas[sensor]
                        self.indices_alertas[idx] = {
                            "sensor": sensor,
                            "motivo": alerta.get("motivo"),
                            "simulado": alerta.get("simulado"),
                            "error_estimado": alerta.get("error_estimado"),
                            "timestamp": alerta.get("timestamp"),
                        }
                        break
        except Exception:
            logging.exception("Silent except at 286 - revisar contexto")

    def registrar_feedback_prediccion(self, datos: dict):
        """Feedback manual desde UI."""
        try:
            nombre = datos.get("nombre_indice") or datos.get("signal")
            pred = float(datos.get("valor_predicho"))
            real = bool(datos.get("es_correcto")) if "es_correcto" in datos else bool(datos.get("valor_real"))
            self.learning_feedback.registrar_feedback_manual(nombre, pred, real)
        except Exception:
            logging.exception("Silent except at 305 - revisar contexto")

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
            logging.exception("Silent except at 272 - revisar contexto")
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
            logging.exception("Silent except at 289 - revisar contexto")
        try:
            self.formula_duel_engine.run_if_due(self)
        except Exception:
            logging.exception("Silent except at 297 - revisar contexto")
        return {
            "sensores": self.sensores,
            "sensores_metadata": self.sensores_metadata,
            "sensores_derivados_metadata": self.sensores_derivados_metadata,
            "indices": indices,
            "recomendacion": self.obtener_recomendacion(),
            "alertas_sensores": self.sensores_alertas,
            "alertas_indices": self.indices_alertas,
            "vanguard_resumen": self.ojeador.resumen(),
            "vanguard_alertas": self.ojeador.get_top_alerts(0, 5),
            "learning_feedback": self.learning_feedback.resumen(),
            "cambios_formulas": self.formula_change_tracker.resumen_ui(),
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