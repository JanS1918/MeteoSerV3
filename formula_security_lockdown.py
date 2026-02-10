#!/usr/bin/env python3
"""
FormulaSecurityLockdown: Sistema de cierre de emergencia + auditoría forense

MISIÓN CRÍTICA:
1. BLOQUEAR sistema de descubrimiento/duelo/integración
2. AUDITAR fórmula integrada
3. VERIFICAR si tiene razón o no
4. REPORTAR hallazgos de seguridad
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("formula_security_lockdown")


class FormulaSecurityLockdown:
    """Sistema de cierre de emergencia y auditoría."""

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.lockdown_file = self.data_dir / "SECURITY_LOCKDOWN.json"

    def activar_lockdown(self, razon: str = "AUDITORÍA MANUAL REQUERIDA") -> bool:
        """Congela el sistema de descubrimiento/duelo/integración."""
        logger.critical(f"[CRITICAL] ACTIVANDO LOCKDOWN: {razon}")

        lockdown_config = {
            "estado": "BLOQUEADO",
            "activado_en": datetime.now(timezone.utc).isoformat(),
            "razon": razon,
            "medidas": {
                "descubrimiento": "BLOQUEADO",
                "validacion": "BLOQUEADO",
                "duelo": "BLOQUEADO",
                "integracion": "BLOQUEADO",
                "ciclos_automaticos": "DETENIDOS"
            },
            "instrucciones": [
                "1. NO ejecutar run_continuous_optimization.py",
                "2. NO ejecutar test_formula_discovery_system.py",
                "3. Revisar audit_report.json",
                "4. Verificar integrated_external_formulas.json",
                "5. Esperar confirmación antes de desbloquear"
            ]
        }

        try:
            self.lockdown_file.write_text(
                json.dumps(lockdown_config, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            logger.critical("[OK] LOCKDOWN ACTIVADO - Sistema congelado")
            return True
        except Exception as e:
            logger.exception(f"[ERROR] Error activando lockdown: {e}")
            return False

    def obtener_formulas_integradas(self) -> List[Dict[str, Any]]:
        """Obtiene todas las fórmulas externas integradas."""
        registry_file = self.data_dir / "integrated_external_formulas.json"

        if not registry_file.exists():
            logger.warning("No hay fórmulas integradas")
            return []

        try:
            raw = json.loads(registry_file.read_text(encoding="utf-8"))
            return raw.get("registros", [])
        except Exception as e:
            logger.exception(f"Error leyendo registros: {e}")
            return []

    def auditar_formula_integrada(self, formula: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audita una fórmula integrada.

        Retorna: Dict con hallazgos de seguridad
        """
        logger.info(f"\n🔬 AUDITANDO FÓRMULA: {formula.get('externa_nombre')}")

        audit = {
            "id": formula.get("externa_id"),
            "nombre": formula.get("externa_nombre"),
            "parametro": formula.get("parametro"),
            "score_duelo": formula.get("score_duelo"),
            "timestamp_integracion": formula.get("timestamp_integracion"),
            "hallazgos": [],
            "advertencias": [],
            "es_segura": True,
            "validez_tecnica": "DESCONOCIDA"
        }

        # === AUDIT 1: Referencia de función ===
        ref = formula.get("externa_ref", "")
        logger.info(f"  Referencia: {ref}")

        if "scipy.special.erf" in ref:
            audit["hallazgos"].append({
                "nivel": "CRÍTICO",
                "problema": "Función erf (Error Function) usada para sensación térmica",
                "razon": "erf() retorna valores -1 a 1, no es adecuado para sensación térmica",
                "impacto": "RESULTADOS INVÁLIDOS"
            })
            audit["es_segura"] = False

        # === AUDIT 2: Inputs requeridos ===
        inputs = formula.get("inputs", [])
        logger.info(f"  Inputs: {inputs}")

        if len(inputs) == 1:
            audit["advertencias"].append({
                "nivel": "CRÍTICO",
                "problema": f"Solo 1 input: {inputs}",
                "razon": "Sensación térmica requiere mínimo 3 inputs (temp + viento + humedad)",
                "impacto": "FÓRMULA INCOMPLETA"
            })
            audit["es_segura"] = False

        # === AUDIT 3: Coherencia con parámetro ===
        param = formula.get("parametro", "")
        logger.info(f"  Parámetro: {param}")

        if param == "sensacion_termica" and "erf" in ref:
            audit["advertencias"].append({
                "nivel": "CRÍTICO",
                "problema": "Mismatch: sensacion_termica + scipy.erf",
                "razon": "erf es función de error matemática, no métrica meteorológica",
                "impacto": "CATEGORÍA EQUIVOCADA"
            })
            audit["es_segura"] = False

        # === AUDIT 4: Score del duelo ===
        score = formula.get("score_duelo", 0)
        logger.info(f"  Score duelo: {score:.1f}/100")

        if score >= 85.0 and audit["es_segura"] is False:
            audit["hallazgos"].append({
                "nivel": "CRÍTICO",
                "problema": "Score alto (85+) pero fórmula técnicamente inválida",
                "razon": "Datos de duelo dummy = resultados engañosos",
                "impacto": "VALIDACIÓN FALLIDA"
            })

        # === AUDIT 5: Inputs vs metadata ===
        logger.info(f"  Verificando coherencia inputs...")
        wrapper_path = formula.get("wrapper_path", "")
        if wrapper_path:
            try:
                wrapper_content = Path(wrapper_path).read_text(encoding="utf-8")
                if "def external_" in wrapper_content:
                    logger.info(f"  [OK] Wrapper existe en {wrapper_path}")
                    # Verificar si recibe inputs correctamente
                    if "temperatura" in wrapper_content and len(inputs) == 1:
                        audit["hallazgos"].append({
                            "nivel": "CRÍTICO",
                            "problema": "Wrapper solo acepta 'temperatura'",
                            "razon": f"Debería aceptar: {inputs} + viento + humedad",
                            "impacto": "INCOMPLETUD FUNCIONAL"
                        })
            except Exception as e:
                logger.debug(f"Error leyendo wrapper: {e}")

        # === RESUMEN AUDIT ===
        if audit["es_segura"]:
            audit["validez_tecnica"] = "VÁLIDA"
            logger.info(f"  [OK] Fórmula válida")
        else:
            audit["validez_tecnica"] = "INVÁLIDA"
            logger.warning(f"  [ERROR] Fórmula INVÁLIDA - {len(audit['hallazgos'])} problemas críticos")

        return audit

    def generar_reporte_audit(self, audits: List[Dict[str, Any]]) -> str:
        """Genera reporte de auditoría forense."""

        reporte = f"""
{'='*80}
🔐 REPORTE DE AUDITORÍA FORENSE - SISTEMA DE FÓRMULAS EXTERNAS
{'='*80}

TIMESTAMP: {datetime.now(timezone.utc).isoformat()}

RESUMEN EJECUTIVO
─────────────────────────────────────────────────────────────────────────────
"""

        formulas_invalidas = [a for a in audits if a["es_segura"] is False]
        formulas_validas = [a for a in audits if a["es_segura"] is True]

        reporte += f"\nTotal fórmulas integradas: {len(audits)}\n"
        reporte += f"[OK] Válidas: {len(formulas_validas)}\n"
        reporte += f"[ERROR] Inválidas: {len(formulas_invalidas)}\n"

        if formulas_invalidas:
            reporte += f"\n[WARNING]  {len(formulas_invalidas)} FÓRMULA(S) INVÁLIDA(S) DETECTADA(S)\n"

        reporte += f"\n{'='*80}\nDETALLES DE AUDITORÍA\n{'='*80}\n"

        for i, audit in enumerate(audits, 1):
            reporte += f"\n[{i}] {audit['nombre']}\n"
            reporte += f"    ID: {audit['id']}\n"
            reporte += f"    Parámetro: {audit['parametro']}\n"
            reporte += f"    Score duelo: {audit['score_duelo']:.1f}/100\n"
            reporte += f"    Validez técnica: {audit['validez_tecnica']}\n"
            reporte += f"    Es segura: {'[OK] SÍ' if audit['es_segura'] else '[ERROR] NO'}\n"

            if audit["hallazgos"]:
                reporte += f"\n    [CRITICAL] HALLAZGOS CRÍTICOS ({len(audit['hallazgos'])}):\n"
                for hallazgo in audit["hallazgos"]:
                    reporte += f"       • {hallazgo['problema']}\n"
                    reporte += f"         Razón: {hallazgo['razon']}\n"
                    reporte += f"         Impacto: {hallazgo['impacto']}\n"

            if audit["advertencias"]:
                reporte += f"\n    [WARNING]  ADVERTENCIAS ({len(audit['advertencias'])}):\n"
                for adv in audit["advertencias"]:
                    reporte += f"       • {adv['problema']}\n"
                    reporte += f"         Razón: {adv['razon']}\n"
                    reporte += f"         Impacto: {adv['impacto']}\n"

        reporte += f"\n{'='*80}\nCONCLUSIONES\n{'='*80}\n"

        if formulas_invalidas:
            reporte += f"""
[ERROR] CONCLUSIÓN: Sistema contiene {len(formulas_invalidas)} fórmula(s) inválida(s)

ACCIONES INMEDIATAS RECOMENDADAS:
1. MANTENER LOCKDOWN activo
2. NO integrar más fórmulas hasta revisión manual
3. EVALUAR si remover fórmulas inválidas
4. IMPLEMENTAR validadores de seguridad más rigurosos
5. REENTRENAR modelo de duelos con datos reales

RIESGO: CRÍTICO
"""
        else:
            reporte += f"""
[OK] CONCLUSIÓN: Todas las fórmulas pasaron auditoría

ACCIONES RECOMENDADAS:
1. Desbloquear sistema
2. Monitorear próximos ciclos
3. Mantener auditorías periódicas
"""

        reporte += f"\n{'='*80}\n"

        return reporte

    def guardar_reporte(self, reporte: str) -> bool:
        """Guarda reporte de auditoría."""
        try:
            report_file = self.data_dir / "audit_report.txt"
            report_file.write_text(reporte, encoding="utf-8")
            logger.info(f"[OK] Reporte guardado: {report_file}")
            return True
        except Exception as e:
            logger.exception(f"Error guardando reporte: {e}")
            return False


def main():
    logger.info("\n" + "="*80)
    logger.info("[CRITICAL] ACTIVANDO SISTEMA DE CIERRE DE EMERGENCIA Y AUDITORÍA")
    logger.info("="*80)

    lockdown = FormulaSecurityLockdown()

    # === PASO 1: ACTIVAR LOCKDOWN ===
    logger.info("\n[PASO 1] ACTIVANDO BLOQUEO DE EMERGENCIA")
    lockdown.activar_lockdown(
        razon="AUDITORÍA FORENSE CRÍTICA - Posible inyección de fórmula inválida"
    )

    # === PASO 2: OBTENER FÓRMULAS INTEGRADAS ===
    logger.info("\n[PASO 2] RECUPERANDO FÓRMULAS INTEGRADAS")
    formulas = lockdown.obtener_formulas_integradas()
    logger.info(f"[OK] Recuperadas {len(formulas)} fórmulas integradas")

    if not formulas:
        logger.info("No hay fórmulas integradas - sistema limpio")
        return

    # === PASO 3: AUDITAR CADA FÓRMULA ===
    logger.info("\n[PASO 3] AUDITANDO CADA FÓRMULA")
    audits = []
    for formula in formulas:
        audit = lockdown.auditar_formula_integrada(formula)
        audits.append(audit)

    # === PASO 4: GENERAR REPORTE ===
    logger.info("\n[PASO 4] GENERANDO REPORTE FORENSE")
    reporte = lockdown.generar_reporte_audit(audits)
    lockdown.guardar_reporte(reporte)

    # === MOSTRAR REPORTE ===
    print(reporte)

    logger.info("\n" + "="*80)
    logger.info("[OK] AUDITORÍA COMPLETADA")
    logger.info("="*80)
    logger.info("\n📋 ACCIONES REQUERIDAS:")
    logger.info("1. Leer audit_report.txt")
    logger.info("2. Revisar SECURITY_LOCKDOWN.json")
    logger.info("3. NO DESBLOQUEAR hasta verificación manual")
    logger.info("4. Esperar instrucciones del administrador")


if __name__ == "__main__":
    main()
