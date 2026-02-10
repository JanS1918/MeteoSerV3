import logging
# ============================================================
# MÓDULO D — SYSTEM CORE (NÚCLEO OPERATIVO)
# ============================================================

EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales

import json
import time
from pathlib import Path


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
        self.last_data_update_time = time.time()  # NEW: Track last sensor update timestamp
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
        self._cargar_sensores_persistidos()
        self._cargar_formulas_persistidas()

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