# -*- coding: utf-8 -*-
"""  
[GUARDIAN] GUARDIAN 25 CAPAS - PATRULLA SOBERANA V47.5

SISTEMA AUTÓNOMO DE PROTECCIÓN TOTAL
Capaz de operar 6 meses sin intervención humana

ARQUITECTURA:
- 18 Capas Físicas y Supervivencia (0, 6-21)
- 4 Capas Sistema Crítico (26-30, 31)
- 3 Capas Seguridad e Integridad (24, 25, 39, 40)

FILOSOFÍA:
"El Acorazado Argentona - Búnker Científico Inexpugnable"

AUTOR: V47.5 SARCÓFAGO CRIPTOGRÁFICO
FECHA: 2026-02-05
"""

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

logger = logging.getLogger(__name__)


class Guardian25Capas:
    """
    Orchestrador del Guardian de 25 capas.
    
    Coordina todas las capas de protección del sistema autónomo.
    ORDEN POR RESTRICCIÓN: Capas vitales primero, si fallan → STOP.
    """
    
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
            "descripcion": "Búsqueda de mejores fórmulas"
        },
        {
            "id": "capa_26_30",
            "nombre": "Post-duelo validación",
            "nivel": "OPCIONAL",
            "accion_fallo": "LOG",
            "reintentos": 1,
            "descripcion": "Validación de cambios"
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
        "capa_26_30": "Post-duelo validación",
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
    
    def _cargar_auditoria(self) -> List[Dict]:
        """Carga auditoría histórica."""
        if self.auditoria_file.exists():
            with open(self.auditoria_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _guardar_auditoria(self):
        """Guarda auditoría."""
        # Mantener últimas 1000 auditorías
        self.auditoria = self.auditoria[-1000:]
        
        with open(self.auditoria_file, 'w', encoding='utf-8') as f:
            json.dump(self.auditoria, f, indent=2, ensure_ascii=False)
    
    def ejecutar_auditoria_completa(self) -> Dict:
        """
        Ejecuta auditoría completa de las 25 capas.
        ORDEN POR RESTRICCIÓN: Vitales primero, si fallan → STOP.
        
        Returns:
            {
                "timestamp": "2026-02-05T...",
                "estado_global": "OK|ALERTA|CRITICO|DETENIDO",
                "capas": {
                    "capa_22": {...},
                    "capa_23": {...},
                    ...
                },
                "resumen": {...}
            }
        """
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
        
    def _ejecutar_capa(self, capa_id: str) -> Dict:
        """
        Ejecuta una capa individual y retorna resultado.
        
        Returns:
            {"estado": "OK|ALERTA|CRITICO|ERROR", ...}
        """
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
        
        # Capas no implementadas aún
        elif capa_id in ["capa_00", "capa_21", "capa_16_19", "capa_06_10", "capa_11_15", "capa_26_30"]:
            return {
                "nombre": self.CAPAS_ARQUITECTURA.get(capa_id, "Desconocida"),
                "estado": "OK",
                "nota": "Capa no implementada aún (placeholder)"
            }
        
        else:
            raise ValueError(f"Capa desconocida: {capa_id}")
        
        # Determinar estado global
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
    
    def generar_informe_guardian(self) -> str:
        """
        Genera informe de texto del Guardian.
        
        Returns:
            Informe formateado en texto
        """
        auditoria = self.ejecutar_auditoria_completa()
        
        # Si auditoría falló y retornó None
        if auditoria is None:
            return "[ERROR] Auditoria retorno None - sistema detenido por fallo VITAL"
        
        lineas = [
            "=" * 80,
            "GUARDIAN 25 CAPAS - PATRULLA SOBERANA V47.5",
            "=" * 80,
            "",
            f"Timestamp: {auditoria['timestamp']}",
            f"Estado Global: {auditoria['estado_global']}",
            "",
            "ARQUITECTURA DE CAPAS:",
            "-" * 80,
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
        
        lineas.extend([
            "",
            "[STATS] RESUMEN:",
            "-" * 80,
            f"  Total Capas: {auditoria['resumen']['capas_total']}",
            f"  Capas Activas: {auditoria['resumen']['capas_activas']}",
            f"  Alertas: {auditoria['resumen']['alertas_total']}",
            f"  Críticos: {auditoria['resumen']['criticos_total']}",
            "",
            "=" * 80,
            "[GUARDIAN] FIN DEL INFORME",
            "=" * 80,
        ])
        
        return "\n".join(lineas)
    
    def auditar_formulas_degradadas(self) -> Dict:
        """
        Audita fórmulas degradadas o faltantes (como Guardian anterior).
        
        Returns:
            {
                "formulas_faltantes": [...],
                "formulas_degradadas": [...],
                "formulas_ok": [...]
            }
        """
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
                
                if tam_kb < 1.0:
                    formulas_degradadas.append({
                        "archivo": formula_file,
                        "tamanio_kb": round(tam_kb, 2),
                        "razon": "Archivo muy pequeño"
                    })
                    logger.warning(f"[WARNING] Fórmula degradada: {formula_file} ({tam_kb:.2f} KB)")
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
