"""
AUDITOR AUTOMÁTICO DE STARTUP - 100% REAL
Ejecuta auditoría completa en cada arranque del sistema.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger("meteoser.startup_auditor")


class StartupAuditor:
    """Audita el sistema en cada startup y genera reporte."""
    
    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
    
    async def audit_system(self) -> Dict[str, Any]:
        """Ejecuta auditoría completa del sistema."""
        logger.info("[BUSCAR] Iniciando auditoría de startup...")
        
        self.issues.clear()
        self.warnings.clear()
        self.recommendations.clear()
        
        # 1. Verificar imports críticos
        await self._audit_imports()
        
        # 2. Verificar estructura de Bus
        await self._audit_bus()
        
        # 3. Verificar motores críticos
        await self._audit_engines()

        # 3.1 Verificar watchdog de cambios
        await self._audit_change_watchdog()
        
        # 4. Verificar física
        await self._audit_physics()
        
        # Generar reporte
        report = {
            "issues": self.issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "status": "OK" if not self.issues else "ISSUES_FOUND",
            "total_issues": len(self.issues),
            "total_warnings": len(self.warnings)
        }
        
        self._log_report(report)
        return report
    
    async def _audit_imports(self):
        """Verifica que todos los imports críticos estén disponibles."""
        critical_modules = [
            "core.indices.environmental_indices",
            "core.indices.physics_engine_2026",
            "core.indices.bus_estado_global",
        ]
        
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError as e:
                self.issues.append({
                    "category": "import",
                    "severity": "critical",
                    "module": module,
                    "error": str(e)
                })
    
    async def _audit_bus(self):
        """Verifica estructura del Bus."""
        try:
            from core.indices.bus_estado_global import BusEstadoGlobal
            bus = BusEstadoGlobal()
            
            # Verificar keys esperadas
            # Keys esperadas (no obligatorias, solo recomendadas)
            recommended_keys = [
                "utci", "evapotranspiracion_penman_monteith",
                "estabilidad_monin_obukhov", "tendencia_barometrica",
                "helada_radiativa"
            ]
            
            missing_keys = []
            for key in recommended_keys:
                if not bus.existe(key):
                    missing_keys.append(key)
            
            if missing_keys:
                # Solo recomendación, no warning
                self.recommendations.append(
                    f"Se pueden publicar keys adicionales: {', '.join(missing_keys)}"
                )
        
        except Exception as e:
            self.issues.append({
                "category": "bus",
                "severity": "high",
                "error": str(e)
            })
    
    async def _audit_engines(self):
        """Verifica disponibilidad de motores."""
        engines = {
            "statistical_brain": "core.engines.statistical_brain",
            "evolution": "evolution_engine",
            "learning": "learning_engine",
        }
        
        for name, module in engines.items():
            try:
                __import__(module)
            except ImportError:
                self.warnings.append(f"Motor {name} no disponible")

    async def _audit_change_watchdog(self):
        """Verifica estado del watchdog de cambios."""
        try:
            from core.monitoring.auto_change_watchdog import AutoChangeWatchdog
            watchdog = AutoChangeWatchdog()
            if watchdog.is_frozen():
                self.warnings.append("Watchdog de cambios está congelado (freeze activo)")
        except Exception as e:
            self.warnings.append(f"Watchdog de cambios no disponible: {e}")
    
    async def _audit_physics(self):
        """Verifica integridad de física."""
        try:
            from core.indices.physics_engine_2026 import PhysicsEngine2026
            
            # Test Factor Z
            engine = PhysicsEngine2026(latitud=45.0, temperatura_k=288.15, presion_pa=101325.0)
            Z, _ = engine.factor_compresibilidad_virial_completo(xv=0.001)
            
            # Verificar que Z está en rango físico
            if not (0.97 <= Z <= 1.01):
                self.issues.append({
                    "category": "physics",
                    "severity": "critical",
                    "parameter": "Factor Z",
                    "value": Z,
                    "expected_range": "[0.97, 1.01]"
                })
            else:
                logger.info(f"[OK] Factor Z verificado: {Z:.6f} (físicamente correcto)")
        
        except Exception as e:
            self.issues.append({
                "category": "physics",
                "severity": "critical",
                "error": str(e)
            })
    
    def _log_report(self, report: Dict[str, Any]):
        """Log del reporte de auditoría."""
        if report["status"] == "OK":
            logger.info("[OK] Auditoría de startup: TODO OK")
        else:
            logger.warning(f"[WARNING] Auditoría encontró {report['total_issues']} problemas")
            for issue in self.issues:
                logger.error(f"   • {issue}")
        
        if self.warnings:
            logger.warning(f"[WARNING] {len(self.warnings)} advertencias:")
            for warning in self.warnings:
                logger.warning(f"   • {warning}")
        
        if self.recommendations:
            logger.info(f"💡 {len(self.recommendations)} recomendaciones:")
            for rec in self.recommendations:
                logger.info(f"   • {rec}")


# Instancia global
startup_auditor = StartupAuditor()
