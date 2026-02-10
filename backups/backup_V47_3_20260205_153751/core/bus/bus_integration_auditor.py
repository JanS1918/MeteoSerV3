#!/usr/bin/env python3
"""CAPA 13: Bus Integration Auditor - Valida trazabilidad de subfactores declarados vs publicados"""

import logging
from dataclasses import dataclass, field
from typing import Set, Dict, List

logger = logging.getLogger("bus_integration_auditor")


@dataclass
class BusAuditResult:
    formula_name: str
    declared_subfactors: Set[str]
    published_subfactors: Set[str]
    missing_from_bus: Set[str]
    audit_passed: bool
    reason: str


class BusIntegrationAuditor:
    """Audita que subfactores declarados se publiquen en el Bus MQTT."""
    
    def __init__(self):
        self.formula_registry: Dict[str, Set[str]] = {}
        logger.info("✅ BusIntegrationAuditor inicializado")
    
    def register_formula(self, formula_name: str, declared_subfactors: Set[str]):
        """Registra subfactores declarados por una fórmula."""
        self.formula_registry[formula_name] = declared_subfactors
        logger.debug(f"📝 Registrado {formula_name}: {declared_subfactors}")
    
    def audit_formula(self, formula_name: str, published_subfactors: Set[str]) -> BusAuditResult:
        """Audita que subfactores se hayan publicado en Bus."""
        
        if formula_name not in self.formula_registry:
            reason = f"❌ {formula_name} NO REGISTRADA"
            return BusAuditResult(formula_name, set(), published_subfactors, set(), False, reason)
        
        declared = self.formula_registry[formula_name]
        missing = declared - published_subfactors
        
        if missing:
            reason = f"❌ Subfactores faltantes en Bus: {missing}"
            logger.warning(reason)
            return BusAuditResult(formula_name, declared, published_subfactors, missing, False, reason)
        else:
            reason = f"✅ Todos los subfactores publicados en Bus"
            logger.info(f"{formula_name}: {reason}")
            return BusAuditResult(formula_name, declared, published_subfactors, set(), True, reason)
    
    def get_audit_summary(self) -> Dict[str, List[str]]:
        """Resumen de auditoría por fórmula."""
        return {
            name: list(subfactors)
            for name, subfactors in self.formula_registry.items()
        }
