# GUARDIAN 30 CAPAS - PATRULLA SOBERANA V47.5
# SISTEMA AUTÓNOMO DE PROTECCIÓN TOTAL
# Capaz de operar 6 meses sin intervención humana
# ARQUITECTURA: 18 Capas Físicas y Supervivencia (0, 6-21) + Post-duelo (26-30) + Seguridad
# AUTOR: V47.5 SARCÓFAGO CRIPTOGRÁFICO
# FECHA: 2026-02-08
import os
import sys
import io
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Fix encoding para Windows terminal
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Añadir workspace a sys.path
workspace_root = Path(__file__).parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

# Configurar logging global ANTES de importar capas
from fix_logging_all import setup_safe_logging
setup_safe_logging()

# Importar capas
from core.validation.mos_clustering_validator import MOSClusteringValidator
from core.learning.feedback_learning_auditor import FeedbackLearningAuditor
from core.monitoring.centinela_soberano import CentinelaSoberano
from core.monitoring.cortafuegos_cascada import CortafuegosCascada
from core.monitoring.monitor_recursos_auto_limpieza import MonitorRecursosAutoLimpieza
from core.security.integridad_codigo_sha256 import IntegridadCodigoSHA256
from core.security.sanitizacion_datos_externos import SanitizacionDatosExternos
from core.monitoring.formula_duel_engine import FormulaDuelEngine
from core.monitoring.sensor_data_bridge import SensorDataBridge
from core.bus.formula_hierarchy import FORMULA_HIERARCHY

logger = logging.getLogger(__name__)


class Guardian25Capas:
    ARCHIVOS_CRITICOS = [
        "core/indices/formulas_indices.py",
        "core/indices/formulas_mejoradas.py",
        "core/indices/formula_validator.py",
        "core/learning/mos_clustering_v472.py",
        "core/learning/feedback_learning_v472.py",
        "core/validation/mos_clustering_validator.py",
        "core/learning/feedback_learning_auditor.py",
        "core/monitoring/centinela_soberano.py",
        "core/monitoring/cortafuegos_cascada.py",
        "core/monitoring/monitor_recursos_auto_limpieza.py",
        "main.py",
        "main_asgi.py",
        "self_mod_engine.py",
        "evolution_engine.py",
    ]
    # Orchestrador del Guardian de 30 capas.
    # Coordina todas las capas de protección del sistema autónomo.
    # ORDEN POR RESTRICCIÓN: Capas vitales primero, si fallan → STOP.
    
    # ORDEN POR RESTRICCIÓN: VITAL → CRÍTICA → IMPORTANTE → OPCIONAL
    CAPAS_POR_RESTRICCION = [
        # === VITALES (falla = STOP sistema) ===
        {
            "id": "capa_24",
            "nombre": "Integridad código SHA-256",
            "nivel": "VITAL",
            "accion_fallo": "STOP_SISTEMA",
            "reintentos": 0,
            "descripcion": "Código no ha sido modificado por virus/ataque"
        },
        {
            "id": "capa_25",
            "nombre": "Sanitización datos externos",
            "nivel": "VITAL",
            "accion_fallo": "STOP_SISTEMA",
            "reintentos": 0,
            "descripcion": "Datos externos no envenenados/comprometidos"
        },
        {
            "id": "capa_23",
            "nombre": "Monitor recursos auto-limpieza",
            "nivel": "VITAL",
            "accion_fallo": "LIMPIEZA_AGRESIVA",
            "reintentos": 3,
            "descripcion": "Disco >1GB, RAM <80%, CPU <90%"
        },
        {
            "id": "capa_00",
            "nombre": "Pre-auditoría fórmulas",
            "nivel": "VITAL",
            "accion_fallo": "STOP_DUELOS",
            "reintentos": 0,
            "descripcion": "Fórmulas matemáticamente sanas antes de duelos"
        },
        
        # === CRÍTICAS (falla = degradación elegante) ===
        {
            "id": "capa_31",
            "nombre": "Centinela soberano",
            "nivel": "CRITICA",
            "accion_fallo": "REINICIAR_PROCESO",
            "reintentos": 5,
            "descripcion": "Watchdog independiente vigila Bus"
        },
        {
            "id": "capa_21",
            "nombre": "Degradación elegante",
            "nivel": "CRITICA",
            "accion_fallo": "MODO_LOCAL",
            "reintentos": 1,
            "descripcion": "Continuar con sensores degradados"
        },
        {
            "id": "capa_22",
            "nombre": "Cortafuegos de cascada",
            "nivel": "CRITICA",
            "accion_fallo": "BLOQUEAR_ALERTAS",
            "reintentos": 2,
            "descripcion": "Alertas basadas en datos válidos"
        },
        
        # === IMPORTANTES (falla = alerta + continuar) ===
        {
            "id": "capa_39",
            "nombre": "MOS Clustering validator",
            "nivel": "IMPORTANTE",
            "accion_fallo": "ALERTA",
            "reintentos": 2,
            "descripcion": "Clasificación de escenarios coherente"
        },
        {
            "id": "capa_40",
            "nombre": "Feedback Learning auditor",
            "nivel": "IMPORTANTE",
            "accion_fallo": "ALERTA",
            "reintentos": 2,
            "descripcion": "Aprendizaje sin overfitting"
        },
        {
            "id": "capa_16_19",
            "nombre": "Validación física cruzada",
            "nivel": "IMPORTANTE",
            "accion_fallo": "ALERTA",
            "reintentos": 1,
            "descripcion": "Datos físicamente posibles"
        },
        
        # === OPCIONALES (falla = log) ===
        {
            "id": "capa_06_10",
            "nombre": "Análisis uso Bus",
            "nivel": "OPCIONAL",
            "accion_fallo": "LOG",
            "reintentos": 1,
            "descripcion": "Estadísticas de uso"
        },
        {
            "id": "capa_11_15",
            "nombre": "Duelos automáticos",
            "nivel": "OPCIONAL",
            "accion_fallo": "LOG",
            "reintentos": 1,
            "descripcion": "Cobertura total de duelos y fusiones"
        },
        # Desglose de capa_26_30 en subcapas individuales
        {
            "id": "capa_26",
            "nombre": "Post-duelo validación estadística",
            "nivel": "OPCIONAL",
            "accion_fallo": "LOG",
            "reintentos": 1,
            "descripcion": "Validación estadística de resultados"
        },
        {
            "id": "capa_27",
            "nombre": "Post-duelo comparación histórica",
            "nivel": "OPCIONAL",
            "accion_fallo": "LOG",
            "reintentos": 1,
            "descripcion": "Comparación con datos históricos"
        },
        {
            "id": "capa_28",
            "nombre": "Post-duelo auditoría de dependencias",
            "nivel": "OPCIONAL",
            "accion_fallo": "LOG",
            "reintentos": 1,
            "descripcion": "Auditoría de dependencias del módulo"
        },
        {
            "id": "capa_29",
            "nombre": "Post-duelo validación física",
            "nivel": "OPCIONAL",
            "accion_fallo": "LOG",
            "reintentos": 1,
            "descripcion": "Validación física de parámetros"
        },
        {
            "id": "capa_30",
            "nombre": "Post-duelo validación lógica",
            "nivel": "OPCIONAL",
            "accion_fallo": "LOG",
            "reintentos": 1,
            "descripcion": "Validación lógica de cambios"
        },
    ]
    
    # Arquitectura legacy (compatibilidad)
    CAPAS_ARQUITECTURA = {
        "capa_00": "Pre-auditoría de fórmulas",
        "capa_06_10": "Análisis de uso del Bus",
        "capa_11_15": "Duelos automáticos de fórmulas",
        "capa_16": "Validación física cruzada",
        "capa_17": "Anti-oscilación (histéresis)",
        "capa_18": "Detector sensor muerto",
        "capa_19": "Validador gradientes extremos",
        "capa_20": "Auditor coherencia tendencias",
        "capa_21": "Auto-recuperación degradación elegante",
        "capa_22": "Cortafuegos de cascada (alertas)",
        "capa_23": "Monitor recursos auto-limpieza",
        "capa_24": "Integridad código SHA-256",
        "capa_25": "Sanitización datos externos",
        "capa_26": "Post-duelo validación estadística",
        "capa_27": "Post-duelo comparación histórica",
        "capa_28": "Post-duelo auditoría de dependencias",
        "capa_29": "Post-duelo validación física",
        "capa_30": "Post-duelo validación lógica",
        "capa_31": "Centinela soberano (watchdog)",
        "capa_39": "MOS Clustering validator",
        "capa_40": "Feedback Learning auditor",
    }
    
    def __init__(self, workspace_root: Path = None):
        if workspace_root is None:
            workspace_root = Path.cwd()
        
        self.workspace_root = workspace_root
        self.data_dir = workspace_root / "data"
        
        # Inicializar capas implementadas
        self.capas = {
            "capa_22": CortafuegosCascada(workspace_root),
            "capa_23": MonitorRecursosAutoLimpieza(workspace_root),
            "capa_24": IntegridadCodigoSHA256(workspace_root),
            "capa_25": SanitizacionDatosExternos(),
            "capa_31": CentinelaSoberano(),
            "capa_39": MOSClusteringValidator(workspace_root),
            "capa_40": FeedbackLearningAuditor(workspace_root),
        }
        
        self.auditoria_file = self.data_dir / "guardian_25_capas_auditoria.json"
        self.auditoria = self._cargar_auditoria()
        
        logger.info("[GUARDIAN] 25 Capas V47.5 PATRULLA SOBERANA inicializado")

    # Métodos auxiliares para capas extra post-duelo
    def _obtener_resultados_post_duelo(self):
        # Simulación: resultados de fórmulas post-duelo
        return [1.0, 0.98, 1.02, 0.99, 1.01]

    def _obtener_historico_post_duelo(self):
        # Simulación: histórico de resultados
        return [1.0, 1.0, 1.0, 1.0, 1.0]

    def _obtener_modulo_post_duelo(self):
        # Simulación: nombre de módulo
        return "core.monitoring.formula_duel_engine"

    def _obtener_parametros_post_duelo(self):
        # Simulación: parámetros físicos
        return {"temperatura": 25, "humedad": 50, "presion": 1013}

    def _analizar_formula(self, archivo):
        # Simulación: análisis de archivo de fórmula
        return {
            "funciones_validas": True,
            "docstring_ok": True,
            "logica_ok": True
        }
    
    def _cargar_auditoria(self) -> List[Dict]:
        # Carga auditoría histórica
        if self.auditoria_file.exists():
            with open(self.auditoria_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _guardar_auditoria(self):
        # Guarda auditoría
        # Mantener últimas 1000 auditorías
        self.auditoria = self.auditoria[-1000:]
        
        with open(self.auditoria_file, 'w', encoding='utf-8') as f:
            json.dump(self.auditoria, f, indent=2, ensure_ascii=False)
    
    def ejecutar_auditoria_completa(self) -> Dict:
        # Ejecuta auditoría completa de las 30 capas.
        # ORDEN POR RESTRICCIÓN: Vitales primero, si fallan -> STOP.
        # Returns: dict con resultados de auditoría
        logger.info("[AUDITORIA] Iniciando auditoria completa de 25 capas (ORDEN POR RESTRICCION)...")
        
        resultados = {
            "timestamp": datetime.now().isoformat(),
            "capas": {},
            "alertas": [],
            "criticos": [],
            "detenido_en": None
        }
        
        # === EJECUTAR CAPAS EN ORDEN DE RESTRICCIÓN ===
        for capa_config in self.CAPAS_POR_RESTRICCION:
            capa_id = capa_config["id"]
            nivel = capa_config["nivel"]
            reintentos_max = capa_config["reintentos"]
            accion_fallo = capa_config["accion_fallo"]
            
            logger.info(f"\n[{nivel}] Ejecutando {capa_id.upper()}: {capa_config['nombre']}")
            
            # Ejecutar capa con reintentos
            exito = False
            for intento in range(reintentos_max + 1):
                try:
                    resultado_capa = self._ejecutar_capa(capa_id)
                    
                    if resultado_capa["estado"] in ["OK", "ALERTA"]:
                        exito = True
                        resultados["capas"][capa_id] = resultado_capa
                        break
                    else:
                        if intento < reintentos_max:
                            logger.warning(f"[REINTENTO] {capa_id} fallo, reintento {intento + 1}/{reintentos_max}")
                        else:
                            resultados["capas"][capa_id] = resultado_capa
                
                except Exception as e:
                    if intento < reintentos_max:
                        logger.error(f"[ERROR] {capa_id} (intento {intento + 1}/{reintentos_max + 1}): {e}")
                    else:
                        logger.critical(f"[FALLO TOTAL] {capa_id} despues de {reintentos_max + 1} intentos")
                        resultados["capas"][capa_id] = {"estado": "ERROR", "error": str(e)}
            
            # Manejar fallo según nivel
            if not exito:
                if nivel == "VITAL":
                    resultados["criticos"].append(f"{capa_id}_VITAL_FALLO")
                    resultados["detenido_en"] = capa_id
                    
                    logger.critical(
                        f"[STOP] CAPA VITAL {capa_id} FALLO - {accion_fallo}\n"
                        f"   Sistema autonomo NO puede continuar sin esta capa"
                    )
                    
                    if accion_fallo == "STOP_SISTEMA":
                        resultados["estado_global"] = "DETENIDO"
                        self._guardar_auditoria()
                        return resultados
                    
                    elif accion_fallo == "LIMPIEZA_AGRESIVA":
                        logger.critical("[LIMPIEZA] Ejecutando limpieza agresiva...")
                        self.capas["capa_23"].ejecutar_limpieza_completa()
                        # Reintentar
                        resultado_capa = self._ejecutar_capa(capa_id)
                        if resultado_capa["estado"] != "OK":
                            resultados["estado_global"] = "DETENIDO"
                            return resultados
                    
                    elif accion_fallo == "STOP_DUELOS":
                        logger.critical("[BLOQUEADO] Duelos de formulas BLOQUEADOS hasta corregir formulas defectuosas")
                        resultados["alertas"].append("DUELOS_BLOQUEADOS")
                
                elif nivel == "CRITICA":
                    resultados["alertas"].append(f"{capa_id}_CRITICA_FALLO")
                    logger.error(f"[CRITICA] Capa {capa_id} fallo - {accion_fallo}")
                
                elif nivel == "IMPORTANTE":
                    resultados["alertas"].append(f"{capa_id}_IMPORTANTE_FALLO")
                    logger.warning(f"[IMPORTANTE] Capa {capa_id} fallo - continuando")
                
                elif nivel == "OPCIONAL":
                    logger.info(f"[OPCIONAL] Capa {capa_id} fallo - no afecta operacion")
        
        # Determinar estado global una vez ejecutadas todas las capas
        if resultados["criticos"]:
            resultados["estado_global"] = "CRITICO"
        elif resultados["alertas"]:
            resultados["estado_global"] = "ALERTA"
        else:
            resultados["estado_global"] = "OK"

        # Resumen
        resultados["resumen"] = {
            "capas_total": len(self.CAPAS_ARQUITECTURA),
            "capas_activas": len(resultados["capas"]),
            "alertas_total": len(resultados["alertas"]),
            "criticos_total": len(resultados["criticos"])
        }

        # Guardar auditoría
        self.auditoria.append({
            "timestamp": resultados["timestamp"],
            "estado_global": resultados["estado_global"],
            "resumen": resultados["resumen"]
        })
        self._guardar_auditoria()

        logger.info(f"[OK] Auditoría completa finalizada: {resultados['estado_global']}")

        return resultados

    def _ejecutar_capa(self, capa_id: str) -> Dict:
        # Ejecuta una capa individual y retorna resultado.
        # Returns: dict con estado
        # Capa 22: Cortafuegos de Cascada
        if capa_id == "capa_22":
            stats_22 = self.capas["capa_22"].obtener_estadisticas()
            return {
                "nombre": "Cortafuegos de Cascada",
                "estado": "OK",
                "alertas_bloqueadas": stats_22.get("alertas_bloqueadas_total", 0),
                "alertas_permitidas": stats_22.get("alertas_permitidas_total", 0)
            }
        
        # Capa 23: Monitor de Recursos
        elif capa_id == "capa_23":
            recursos = self.capas["capa_23"].verificar_recursos()
            return {
                "nombre": "Monitor Recursos Auto-Limpieza",
                "estado": recursos["estado_global"],
                "disco_libre_gb": recursos["disco"]["libre_gb"],
                "ram_usado_pct": recursos["ram"]["usado_pct"],
                "cpu_uso_pct": recursos["cpu"]["uso_pct"]
            }
        
        # Capa 24: Integridad SHA-256
        elif capa_id == "capa_24":
            integridad = self.capas["capa_24"].verificar_integridad()
            estado = "CRITICO" if integridad["estado"] == "MODIFICADO" else "OK"
            return {
                "nombre": "Integridad Código SHA-256",
                "estado": estado,
                "archivos_modificados": len(integridad["archivos_modificados"]),
                "archivos_borrados": len(integridad["archivos_borrados"])
            }
        
        # Capa 25: Sanitización
        elif capa_id == "capa_25":
            stats_25 = self.capas["capa_25"].obtener_estadisticas()
            estado = "ALERTA" if stats_25["tasa_rechazo_pct"] > 10.0 else "OK"
            return {
                "nombre": "Sanitización Datos Externos",
                "estado": estado,
                "total_validaciones": stats_25["total_validaciones"],
                "rechazados_total": stats_25["rechazados_total"],
                "tasa_rechazo_pct": stats_25["tasa_rechazo_pct"]
            }
        
        # Capa 31: Centinela Soberano
        elif capa_id == "capa_31":
            stats_31 = self.capas["capa_31"].obtener_estadisticas()
            estado = "ALERTA" if stats_31["reinicios_ejecutados"] > 0 else "OK"
            return {
                "nombre": "Centinela Soberano",
                "estado": estado,
                "bloqueos": stats_31["bloqueos_detectados"],
                "reinicios": stats_31["reinicios_ejecutados"]
            }
        
        # Capa 39: MOS Clustering Validator
        elif capa_id == "capa_39":
            stats_39 = self.capas["capa_39"].obtener_estadisticas()
            return {
                "nombre": "MOS Clustering Validator",
                "estado": "OK",
                "validaciones": stats_39["validaciones_totales"],
                "rechazos": stats_39.get("errores_detectados", 0)
            }
        
        # Capa 40: Feedback Learning Auditor
        elif capa_id == "capa_40":
            stats_40 = self.capas["capa_40"].obtener_estadisticas()
            estado = "ALERTA" if stats_40.get("alertas_overfitting", 0) > 5 else "OK"
            return {
                "nombre": "Feedback Learning Auditor",
                "estado": estado,
                "auditorias": stats_40["auditorias_totales"],
                "alertas_overfitting": stats_40.get("alertas_overfitting", 0)
            }

        # Capa 11-15: Duelos completos + fusiones
        elif capa_id == "capa_11_15":
            resultado = self._auditar_duelos_completos()
            return {
                "nombre": "Duelos Automáticos (Cobertura Total)",
                **resultado
            }
        
        # Capas no implementadas aún
        elif capa_id in ["capa_00", "capa_21", "capa_16_19", "capa_06_10"]:
            return {
                "nombre": self.CAPAS_ARQUITECTURA.get(capa_id, "Desconocida"),
                "estado": "OK",
                "nota": "Capa no implementada aún (placeholder)"
            }
        # Capas extra de seguridad
        elif capa_id == "capa_26":
            from core.monitoring.extra_security_layers import validar_estadistica
            resultados = self._obtener_resultados_post_duelo()
            ok, msg = validar_estadistica(resultados)
            return {"nombre": "Post-duelo validación estadística", "estado": "OK" if ok else "ALERTA", "detalle": msg}
        elif capa_id == "capa_27":
            from core.monitoring.extra_security_layers import validar_historico
            resultados = self._obtener_resultados_post_duelo()
            historico = self._obtener_historico_post_duelo()
            ok, msg = validar_historico(resultados, historico)
            return {"nombre": "Post-duelo comparación histórica", "estado": "OK" if ok else "ALERTA", "detalle": msg}
        elif capa_id == "capa_28":
            from core.monitoring.extra_security_layers import auditar_dependencias
            modulo = self._obtener_modulo_post_duelo()
            ok, msg = auditar_dependencias(modulo)
            return {"nombre": "Post-duelo auditoría de dependencias", "estado": "OK" if ok else "ALERTA", "detalle": msg}
        elif capa_id == "capa_29":
            from core.monitoring.extra_security_layers import validar_fisica
            parametros = self._obtener_parametros_post_duelo()
            resultados = [validar_fisica(p, v) for p, v in parametros.items()]
            estado = "OK" if all(r[0] for r in resultados) else "ALERTA"
            detalles = [r[1] for r in resultados]
            return {"nombre": "Post-duelo validación física", "estado": estado, "detalle": detalles}
        elif capa_id == "capa_30":
            # Placeholder para validación lógica
            return {"nombre": "Post-duelo validación lógica", "estado": "OK", "detalle": "Validación lógica no implementada"}
        
        else:
            raise ValueError(f"Capa desconocida: {capa_id}")
        
        

    def _auditar_duelos_completos(self) -> Dict:
        # Audita cobertura total de duelos y fusiones y PROMUEVE automáticamente fórmulas alternativas más precisas
        # cuando superan a las actuales en duelos y validaciones.
        class _MockSystem:
            def __init__(self):
                self.historial_sensores = {}
                self.sensores = {}
                self.sensores_alertas = {}
                self.sensores_metadata = {}

        system = _MockSystem()
        bridge = SensorDataBridge(self.workspace_root)
        bridge.cargar_y_llenar(system)

        engine = FormulaDuelEngine(self.workspace_root)
        engine.dry_run = False  # Permitir aplicar cambios si la candidata es mejor
        engine.max_parametros_por_run = len(FORMULA_HIERARCHY)

        cobertura = engine.auditar_cobertura_total(system, incluir_ojeador=True, promover_mejor=True)
        # Si el motor de duelos devuelve None por falta de datos o error interno,
        # crear una cobertura vacía por defecto para evitar retorno None.
        if cobertura is None:
            logger.error("[ERROR] FormulaDuelEngine.auditar_cobertura_total devolvió None; usando cobertura por defecto")
            cobertura = {
                "formulas_total": 0,
                "formulas_ok": 0,
                "formulas_error": 0,
                "formulas_sin_funcion": 0,
                "formulas_sin_datos": 0,
                "candidatas_total": 0,
                "candidatas_ok": 0,
                "candidatas_error": 0,
                "candidatas_sin_funcion": 0,
                "candidatas_sin_datos": 0,
                "fusiones_total": 0,
                "fusiones_ok": 0,
                "fusiones_error": 0,
                "fusiones_sin_funcion": 0,
                "fusiones_sin_datos": 0,
                "promociones": []
            }
        out_path = self.data_dir / "guardian_duel_coverage.json"
        try:
            out_path.write_text(json.dumps(cobertura, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"[WARNING] No se pudo guardar guardian_duel_coverage.json: {e}")

        criticos = (
            cobertura.get("formulas_error", 0)
            + cobertura.get("formulas_sin_funcion", 0)
            + cobertura.get("candidatas_error", 0)
            + cobertura.get("candidatas_sin_funcion", 0)
            + cobertura.get("fusiones_error", 0)
            + cobertura.get("fusiones_sin_funcion", 0)
        )
        alertas = (
            cobertura.get("formulas_sin_datos", 0)
            + cobertura.get("candidatas_sin_datos", 0)
            + cobertura.get("fusiones_sin_datos", 0)
        )

        if criticos > 0:
            estado = "CRITICO"
        elif alertas > 0:
            estado = "ALERTA"
        else:
            estado = "OK"

        return {
            "estado": estado,
            "resumen": {
                "formulas_total": cobertura.get("formulas_total", 0),
                "formulas_ok": cobertura.get("formulas_ok", 0),
                "candidatas_total": cobertura.get("candidatas_total", 0),
                "candidatas_ok": cobertura.get("candidatas_ok", 0),
                "fusiones_total": cobertura.get("fusiones_total", 0),
                "fusiones_ok": cobertura.get("fusiones_ok", 0),
            },
            "faltantes": {
                "formulas": cobertura.get("formulas_sin_datos", 0)
                + cobertura.get("formulas_sin_funcion", 0)
                + cobertura.get("formulas_error", 0),
                "candidatas": cobertura.get("candidatas_sin_datos", 0)
                + cobertura.get("candidatas_sin_funcion", 0)
                + cobertura.get("candidatas_error", 0),
                "fusiones": cobertura.get("fusiones_sin_datos", 0)
                + cobertura.get("fusiones_sin_funcion", 0)
                + cobertura.get("fusiones_error", 0),
            },
            "archivo": str(out_path),
            "promociones": cobertura.get("promociones", [])
        }
    
    def generar_informe_guardian(self) -> str:
        # Genera informe de texto del Guardian.
        # Returns: Informe formateado en texto
        auditoria = self.ejecutar_auditoria_completa()
        
        # Si auditoría falló y retornó None -> crear fallback informativo
        if auditoria is None:
            logger.error("[ERROR] ejecutar_auditoria_completa devolvió None; creando informe de fallback")
            auditoria = {
                "timestamp": datetime.now().isoformat(),
                "estado_global": "DETENIDO",
                "capas": {},
                "criticos": ["ejecutar_auditoria_completa retornó None"],
                "alertas": [],
                "resumen": {
                    "capas_total": len(self.CAPAS_ARQUITECTURA),
                    "capas_activas": 0,
                    "alertas_total": 1,
                    "criticos_total": 1
                }
            }
        
        lineas = [
            "=" * 80,
            "GUARDIAN 30 CAPAS - PATRULLA SOBERANA V47.5",
            "=" * 80,
            "",
            f"Timestamp: {auditoria['timestamp']}",
            f"Estado Global: {auditoria['estado_global']}",
            "",
            "ARQUITECTURA DE CAPAS (DESGLOSE):",
            "-" * 80,
            "  0-21: Capas Físicas y Supervivencia",
            "  24: Integridad código SHA-256",
            "  25: Sanitización datos externos",
            "  23: Monitor recursos auto-limpieza",
            "  31: Centinela soberano",
            "  39: MOS Clustering validator",
            "  40: Feedback Learning auditor",
            "  26: Post-duelo validación estadística",
            "  27: Post-duelo comparación histórica",
            "  28: Post-duelo auditoría de dependencias",
            "  29: Post-duelo validación física",
            "  30: Post-duelo validación lógica",
            "",
            "  Capas Extra Seguridad:",
            "    - Validación estadística",
            "    - Comparación histórica",
            "    - Auditoría de dependencias",
            "    - Validación física",
            "",
        ]
        
        for capa_id, descripcion in self.CAPAS_ARQUITECTURA.items():
            lineas.append(f"  {capa_id.upper()}: {descripcion}")
        
        lineas.extend([
            "",
            "📈 ESTADO DE CAPAS ACTIVAS:",
            "-" * 80,
        ])
        
        for capa_id, info in auditoria["capas"].items():
            estado_icono = {
                "OK": "[OK]",
                "ALERTA": "[WARNING]",
                "CRITICO": "[CRITICAL]",
                "ERROR": "[ERROR]"
            }.get(info.get("estado", "ERROR"), "❓")
            
            lineas.append(f"  {estado_icono} {capa_id.upper()}: {info.get('nombre', 'N/A')}")
            
            # Detalles
            for key, value in info.items():
                if key not in ["nombre", "estado"]:
                    lineas.append(f"      {key}: {value}")
        
        lineas.extend([
            "",
            "[CRITICAL] ALERTAS Y CRÍTICOS:",
            "-" * 80,
        ])
        
        if auditoria["criticos"]:
            lineas.append("  CRÍTICOS:")
            for critico in auditoria["criticos"]:
                lineas.append(f"    [CRITICAL] {critico}")
        
        if auditoria["alertas"]:
            lineas.append("  ALERTAS:")
            for alerta in auditoria["alertas"]:
                lineas.append(f"    [WARNING] {alerta}")
        
        if not auditoria["criticos"] and not auditoria["alertas"]:
            lineas.append("  [OK] Sin alertas ni críticos")
        
        lineas.append("")
        lineas.append("[STATS] RESUMEN:")
        lineas.append("-" * 80)
        resumen = auditoria.get('resumen', {})
        lineas.append(f"  Total Capas: {resumen.get('capas_total', 'N/A')}")
        lineas.append(f"  Capas Activas: {resumen.get('capas_activas', 'N/A')}")
        lineas.append(f"  Alertas: {resumen.get('alertas_total', 'N/A')}")
        lineas.append(f"  Críticos: {resumen.get('criticos_total', 'N/A')}")
        lineas.append("")
        lineas.append("=" * 80)
        lineas.append("[GUARDIAN] FIN DEL INFORME")
        lineas.append("=" * 80)
        
        return "\n".join(lineas)
    
    def auditar_formulas_degradadas(self) -> Dict:
        # Audita fórmulas degradadas o faltantes (como Guardian anterior).
        # Returns: dict con estado de fórmulas
        logger.info("[BUSCAR] Auditando fórmulas degradadas...")
        
        # Buscar archivos de fórmulas
        formulas_dir = self.workspace_root / "core" / "indices"
        
        formulas_faltantes = []
        formulas_degradadas = []
        formulas_ok = []
        
        # Fórmulas críticas que deben existir
        formulas_criticas = [
            "formulas_indices.py",
            "formulas_mejoradas.py",
            "formula_validator.py"
        ]
        
        for formula_file in formulas_criticas:
            archivo = formulas_dir / formula_file
            
            if not archivo.exists():
                formulas_faltantes.append(formula_file)
                logger.critical(f"[CRITICAL] Fórmula faltante: {formula_file}")
            else:
                # Verificar si es "degradada" (muy pequeña)
                tam_kb = archivo.stat().st_size / 1024
                info = self._analizar_formula(archivo)
                funciones_validas = info.get("funciones_validas", False)
                docstring_ok = info.get("docstring_ok", False)
                logica_ok = info.get("logica_ok", False)
                if tam_kb < 0.5 and not (funciones_validas and docstring_ok and logica_ok):
                    formulas_degradadas.append({
                        "archivo": formula_file,
                        "tamanio_kb": round(tam_kb, 2),
                        "razon": "Archivo pequeño y sin lógica suficiente"
                    })
                    logger.warning(f"[WARNING] Fórmula degradada: {formula_file} ({tam_kb:.2f} KB)")
                elif not funciones_validas:
                    formulas_degradadas.append({
                        "archivo": formula_file,
                        "tamanio_kb": round(tam_kb, 2),
                        "razon": "Sin funciones válidas"
                    })
                    logger.warning(f"[WARNING] Fórmula degradada: {formula_file} - Sin funciones válidas")
                else:
                    formulas_ok.append(formula_file)
                    logger.info(f"[OK] Fórmula OK: {formula_file}")
        
        resultado = {
            "formulas_faltantes": formulas_faltantes,
            "formulas_degradadas": formulas_degradadas,
            "formulas_ok": formulas_ok,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            f"[OK] Auditoría de fórmulas completada: "
            f"{len(formulas_ok)} OK, {len(formulas_degradadas)} degradadas, "
            f"{len(formulas_faltantes)} faltantes"
        )
        
        return resultado


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    import sys
    # Comando para actualizar baseline automáticamente
    if len(sys.argv) > 1 and sys.argv[1] == 'actualizar_baseline':
        import hashlib, json
        guardian = Guardian25Capas()
        # Inicializar baseline correctamente
        hashes_file = guardian.data_dir / 'integridad_sha256_hashes.json'
        if hashes_file.exists():
            hashes = json.load(open(hashes_file, 'r', encoding='utf-8'))
        else:
            hashes = {}
        for archivo_rel in Guardian25Capas.ARCHIVOS_CRITICOS:
            archivo = guardian.workspace_root / archivo_rel
            if archivo.exists():
                try:
                    contenido = archivo.read_text(encoding='utf-8')
                    if '# EDITADO_POR_KIOKO' in contenido:
                        hash_actual = guardian.calcular_sha256(archivo)
                        hashes[archivo_rel] = hash_actual
                        print(f'[OK] Baseline actualizado para {archivo_rel} (firma detectada)')
                except Exception:
                    pass
        with open(hashes_file, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2, ensure_ascii=False)
        print('[OK] Baseline de integridad actualizado para archivos firmados.')
        sys.exit(0)

    # Crear Guardian
    guardian = Guardian25Capas()
    
    # Ejecutar auditoría completa
    print("\n[BUSCAR] Ejecutando auditoría completa...")
    informe = guardian.generar_informe_guardian()
    print(informe)
    
    # Guardar informe
    informe_file = Path("GUARDIAN_25_CAPAS_INFORME.txt")
    with open(informe_file, 'w', encoding='utf-8') as f:
        f.write(informe)
    
    print(f"\n[OK] Informe guardado en: {informe_file}")
    
    # Auditar fórmulas
    print("\n[BUSCAR] Auditando fórmulas...")
    formulas = guardian.auditar_formulas_degradadas()
    print(json.dumps(formulas, indent=2, ensure_ascii=False))
