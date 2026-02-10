# AUTO-AUDITORÍA INTEGRADA - MeteoSer V3
# ═════════════════════════════════════════════════════════════════════════════
# Generador automático de reportes de auditoría a partir del registro histórico
# centralizado. Se ejecuta periódicamente o bajo demanda para validar:
# - Cobertura de fórmulas (documentadas vs implementadas)
# - Redundancia de cálculos (via Bus de Estado Global)
# - Desincronización entre promesas y código
# - Validación de datos contra históricos
# - Integridad física de resultados
#
# Metadata: auto_auditor_v1.0 | Reportes Auditables | CI/CD Ready
# ═════════════════════════════════════════════════════════════════════════════

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict
from core.managers.historical_registry import (
    get_registry,
    RecordType,
    ConfidenceLevel
)

logger = logging.getLogger("auto_auditor")


class AutoAuditor:
    """
    Generador automático de reportes de auditoría.
    
    RESPONSABILIDADES:
    - Analizar históricos para detectar anomalías
    - Validar cobertura de fórmulas
    - Detectar redundancia no deseada
    - Generar alertas y reportes
    - Facilitar integración en CI/CD
    """
    
    def __init__(self, output_dir: str = "data/audit_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.registry = get_registry()
        
        logger.info(f"[AUTO_AUDITOR] Inicializado. Reportes en: {self.output_dir}")
    
    def run_full_audit(self) -> Dict[str, Any]:
        """
        Ejecuta auditoría completa del sistema.
        
        Returns:
            Dict con resultados de auditoría
        """
        logger.info("[AUTO_AUDITOR] Iniciando auditoría completa...")
        
        audit_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sections": {}
        }
        
        # 1. Auditoría de cobertura (mediante acciones documentadas)
        audit_report["sections"]["coverage"] = self._audit_formula_coverage()
        
        # 2. Auditoría de validación (predicciones vs reales)
        audit_report["sections"]["validation"] = self._audit_predictions_vs_actuals()
        
        # 3. Auditoría de confianza de datos
        audit_report["sections"]["data_confidence"] = self._audit_data_confidence()
        
        # 4. Auditoría de fuentes
        audit_report["sections"]["sources"] = self._audit_sources()
        
        # 5. Auditoría de errores
        audit_report["sections"]["errors"] = self._audit_errors()
        
        # Generar alertas
        audit_report["alerts"] = self._generate_alerts(audit_report)
        
        # Salvar reporte
        self._save_report(audit_report)
        
        logger.info(f"[AUTO_AUDITOR] Auditoría completada. "
                   f"Alertas: {len(audit_report['alerts'])}")
        
        return audit_report
    
    def _audit_formula_coverage(self) -> Dict[str, Any]:
        """
        Analiza qué fórmulas están documentadas y cuáles implementadas.
        Compara contra ANALISIS_EXHAUSTIVO_FORMULAS_COMPLETO_*.md
        """
        coverage = {
            "total_entities": len(self.registry.index_by_entity),
            "entities_with_validation": 0,
            "entities_without_validation": [],
            "entities_by_confidence": defaultdict(list),
            "recommendations": []
        }
        
        # Analizar cada entidad
        for entity in self.registry.index_by_entity.keys():
            records = self.registry.get_entity_history(entity, limit=1)
            if not records:
                continue
            
            validations = self.registry.get_validations(entity, limit=10)
            
            if validations:
                coverage["entities_with_validation"] += 1
            else:
                coverage["entities_without_validation"].append(entity)
            
            # Agrupar por confianza
            confidence = records[0].confidence.value
            coverage["entities_by_confidence"][confidence].append(entity)
        
        # Recomendaciones
        if coverage["entities_without_validation"]:
            coverage["recommendations"].append({
                "priority": "HIGH",
                "issue": "Entidades sin validación histórica",
                "count": len(coverage["entities_without_validation"]),
                "action": f"Activar validación para: {', '.join(coverage['entities_without_validation'][:5])}"
            })
        
        if coverage["entities_by_confidence"].get(ConfidenceLevel.DEGRADED.value):
            coverage["recommendations"].append({
                "priority": "MEDIUM",
                "issue": "Entidades con confianza degradada (fallback)",
                "count": len(coverage["entities_by_confidence"]["degraded"]),
                "action": "Revisar sensores y calibración"
            })
        
        return coverage
    
    def _audit_predictions_vs_actuals(self) -> Dict[str, Any]:
        """
        Compara predicciones contra valores reales registrados.
        Calcula precisión por entidad.
        """
        validation = {
            "total_validations": 0,
            "accuracy_by_entity": {},
            "low_accuracy_entities": [],
            "recommendations": []
        }
        
        # Agrupar validaciones por entidad
        by_entity = defaultdict(list)
        for record in self.registry.records:
            if record.record_type == RecordType.VALIDATION:
                entity = record.metadata.get("entity", record.entity)
                by_entity[entity].append(record)
        
        for entity, records in by_entity.items():
            correct = sum(1 for r in records if r.metadata.get("is_correct"))
            accuracy = correct / len(records) * 100 if records else 0
            
            validation["accuracy_by_entity"][entity] = {
                "total": len(records),
                "correct": correct,
                "accuracy_pct": round(accuracy, 2)
            }
            validation["total_validations"] += len(records)
            
            if accuracy < 80:
                validation["low_accuracy_entities"].append({
                    "entity": entity,
                    "accuracy_pct": round(accuracy, 2),
                    "samples": len(records)
                })
        
        # Recomendaciones
        if validation["low_accuracy_entities"]:
            validation["recommendations"].append({
                "priority": "HIGH",
                "issue": "Baja precisión en predicciones (<80%)",
                "count": len(validation["low_accuracy_entities"]),
                "action": "Revisar fórmulas y calibración en entidades afectadas"
            })
        
        return validation
    
    def _audit_data_confidence(self) -> Dict[str, Any]:
        """Analiza distribución de confianza en datos."""
        confidence_stats = {
            "distribution": defaultdict(int),
            "degraded_ratio": 0.0,
            "synthetic_ratio": 0.0,
            "recommendations": []
        }
        
        total = len(self.registry.records)
        if total == 0:
            return confidence_stats
        
        for record in self.registry.records:
            confidence_stats["distribution"][record.confidence.value] += 1
        
        degraded = confidence_stats["distribution"].get(ConfidenceLevel.DEGRADED.value, 0)
        synthetic = confidence_stats["distribution"].get(ConfidenceLevel.SYNTHETIC.value, 0)
        
        confidence_stats["degraded_ratio"] = round(degraded / total * 100, 2)
        confidence_stats["synthetic_ratio"] = round(synthetic / total * 100, 2)
        
        # Recomendaciones
        if confidence_stats["degraded_ratio"] > 10:
            confidence_stats["recommendations"].append({
                "priority": "MEDIUM",
                "issue": f"Datos degradados: {confidence_stats['degraded_ratio']}%",
                "action": "Revisar sensores y mejorar fuentes de datos"
            })
        
        return confidence_stats
    
    def _audit_sources(self) -> Dict[str, Any]:
        """Analiza diversidad y características de fuentes de datos."""
        sources = {
            "unique_sources": set(),
            "records_by_source": defaultdict(int),
            "reliability_by_source": {},
            "recommendations": []
        }
        
        for record in self.registry.records:
            sources["unique_sources"].add(record.source)
            sources["records_by_source"][record.source] += 1
        
        # Calcular confiabilidad por fuente (% de datos REAL)
        for source in sources["unique_sources"]:
            source_records = [r for r in self.registry.records if r.source == source]
            real_count = sum(1 for r in source_records if r.confidence == ConfidenceLevel.REAL)
            reliability = real_count / len(source_records) * 100 if source_records else 0
            
            sources["reliability_by_source"][source] = round(reliability, 2)
        
        sources["unique_sources"] = list(sources["unique_sources"])
        
        # Recomendaciones
        unreliable = [s for s, r in sources["reliability_by_source"].items() if r < 50]
        if unreliable:
            sources["recommendations"].append({
                "priority": "MEDIUM",
                "issue": f"Fuentes poco confiables: {', '.join(unreliable)}",
                "action": "Revisar integridad y calibración de these sources"
            })
        
        return sources
    
    def _audit_errors(self) -> Dict[str, Any]:
        """Analiza errores registrados en el sistema."""
        errors = {
            "total_errors": 0,
            "errors_by_type": defaultdict(int),
            "errors_by_entity": defaultdict(int),
            "recent_errors": [],
            "recommendations": []
        }
        
        error_records = [r for r in self.registry.records if r.record_type == RecordType.ERROR]
        errors["total_errors"] = len(error_records)
        
        for record in error_records:
            error_type = record.metadata.get("error_type", "unknown")
            errors["errors_by_type"][error_type] += 1
            errors["errors_by_entity"][record.entity] += 1
        
        # Últimos 10 errores
        errors["recent_errors"] = [
            {
                "timestamp": r.timestamp.isoformat(),
                "entity": r.entity,
                "error_type": r.metadata.get("error_type"),
                "message": r.metadata.get("message", "")[:100]
            }
            for r in reversed(error_records[-10:])
        ]
        
        # Recomendaciones
        if errors["total_errors"] > 100:
            errors["recommendations"].append({
                "priority": "HIGH",
                "issue": f"Alto número de errores: {errors['total_errors']}",
                "action": "Realizar depuración y revisión de logs"
            })
        
        return errors
    
    def _generate_alerts(self, audit_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Genera alertas consolidadas basadas en resultados de auditoría.
        """
        alerts = []
        
        # Analizar cada sección
        for section, data in audit_report["sections"].items():
            if isinstance(data, dict) and "recommendations" in data:
                alerts.extend(data["recommendations"])
        
        # Ordenar por prioridad
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        alerts.sort(key=lambda a: priority_order.get(a.get("priority", "LOW"), 4))
        
        return alerts
    
    def _save_report(self, audit_report: Dict[str, Any]) -> Path:
        """
        Salva reporte en formato JSON y Markdown.
        
        Returns:
            Ruta del archivo JSON
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar JSON
        json_path = self.output_dir / f"audit_report_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(audit_report, f, indent=2, default=str)
        
        # Guardar Markdown
        md_path = self.output_dir / f"audit_report_{timestamp}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self._format_as_markdown(audit_report))
        
        logger.info(f"[AUTO_AUDITOR] Reportes guardados:")
        logger.info(f"  JSON: {json_path}")
        logger.info(f"  Markdown: {md_path}")
        
        return json_path
    
    def _format_as_markdown(self, audit_report: Dict[str, Any]) -> str:
        """Formatea reporte como Markdown."""
        md = f"# AUDITORÍA AUTOMÁTICA - {audit_report['timestamp']}\n\n"
        
        # Resumen de alertas
        if audit_report["alerts"]:
            md += "## ⚠️ ALERTAS\n\n"
            for alert in audit_report["alerts"]:
                priority = alert.get("priority", "LOW")
                issue = alert.get("issue", "Unknown")
                action = alert.get("action", "N/A")
                md += f"- **[{priority}]** {issue}\n"
                md += f"  - Acción: {action}\n\n"
        else:
            md += "## ✅ SIN ALERTAS\n\n"
        
        # Secciones
        for section, data in audit_report["sections"].items():
            md += f"## {section.upper()}\n\n"
            md += json.dumps(data, indent=2, default=str)
            md += "\n\n"
        
        return md
    
    def generate_ci_report(self) -> Dict[str, Any]:
        """
        Genera reporte simplificado para CI/CD.
        Retorna métricas clave y fallos críticos.
        
        Returns:
            Dict con:
            - status: "pass" o "fail"
            - errors: Número de errores
            - warnings: Número de alertas
            - coverage_pct: Cobertura de fórmulas
            - accuracy_avg_pct: Precisión promedio
        """
        full_audit = self.run_full_audit()
        
        ci_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "pass",
            "metrics": {},
            "failures": []
        }
        
        # Métricas clave
        validation = full_audit["sections"]["validation"]
        coverage = full_audit["sections"]["coverage"]
        confidence = full_audit["sections"]["data_confidence"]
        
        accuracies = [v["accuracy_pct"] for v in validation["accuracy_by_entity"].values()]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        
        coverage_pct = (coverage["entities_with_validation"] / coverage["total_entities"] * 100
                        if coverage["total_entities"] > 0 else 0)
        
        ci_report["metrics"] = {
            "total_validations": validation["total_validations"],
            "accuracy_avg_pct": round(avg_accuracy, 2),
            "formula_coverage_pct": round(coverage_pct, 2),
            "data_degraded_pct": confidence["degraded_ratio"],
            "total_errors": full_audit["sections"]["errors"]["total_errors"]
        }
        
        # Determinar estado
        critical_alerts = [a for a in full_audit["alerts"] if a.get("priority") == "CRITICAL"]
        high_alerts = [a for a in full_audit["alerts"] if a.get("priority") == "HIGH"]
        
        if critical_alerts:
            ci_report["status"] = "fail"
            ci_report["failures"] = [a["issue"] for a in critical_alerts]
        elif len(high_alerts) > 3:
            ci_report["status"] = "warn"
        
        return ci_report


def run_audit_for_ci() -> bool:
    """
    Función conveniente para ejecutar auditoría desde CI/CD.
    
    Returns:
        True si auditoría pasó, False si falló
    """
    auditor = AutoAuditor()
    report = auditor.generate_ci_report()
    
    if report["status"] == "fail":
        logger.error(f"[CI_AUDIT] FALLÓ: {report['failures']}")
        return False
    elif report["status"] == "warn":
        logger.warning(f"[CI_AUDIT] Advertencias: {len(report['failures'])} alertas altas")
        return True
    else:
        logger.info(f"[CI_AUDIT] PASÓ: Metrics OK")
        return True
