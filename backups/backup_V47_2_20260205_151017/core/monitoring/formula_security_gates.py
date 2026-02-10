#!/usr/bin/env python3
"""
SISTEMA DE CIERRE DE EMERGENCIA - PREVENCIÓN DE INYECCIONES

Este módulo debe cargarse PRIMERO en cualquier ciclo de discovery/duelo/integración.
Si está en lockdown, todo falla gracefully.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("formula_security_gates")


class FormulaSecurityGates:
    """Compuertas de seguridad para fórmulas externas."""

    LOCKDOWN_FILE = Path(__file__).resolve().parent.parent / "data" / "SECURITY_LOCKDOWN.json"
    
    @classmethod
    def esta_en_lockdown(cls) -> bool:
        """Verifica si el sistema está en lockdown."""
        if not cls.LOCKDOWN_FILE.exists():
            return False
        
        try:
            data = json.loads(cls.LOCKDOWN_FILE.read_text(encoding="utf-8"))
            return data.get("estado") == "BLOQUEADO"
        except Exception:
            return False
    
    @classmethod
    def bloquear_si_lockdown(cls, operacion: str) -> bool:
        """
        Retorna True si está bloqueado (operación FALLA).
        Retorna False si se puede continuar (operación OK).
        """
        if cls.esta_en_lockdown():
            logger.critical(f"🚨 OPERACIÓN BLOQUEADA: {operacion} (LOCKDOWN ACTIVO)")
            return True
        return False


# ============================================================================
# DECORADOR: Proteger funciones con LOCKDOWN
# ============================================================================

def proteger_con_lockdown(operacion_nombre: str):
    """Decorador que bloquea función si hay LOCKDOWN."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if FormulaSecurityGates.bloquear_si_lockdown(operacion_nombre):
                raise RuntimeError(
                    f"❌ OPERACIÓN BLOQUEADA: {operacion_nombre}\n"
                    f"Sistema en LOCKDOWN - revisar data/SECURITY_LOCKDOWN.json\n"
                    f"Contactar administrador para desbloquear."
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# SINGLETON: Almacenar configuración de LOCKDOWN
# ============================================================================

class LockdownConfig:
    """Configuración de LOCKDOWN - singleton."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.estado = "NORMAL"
            self.razon = ""
            self.timestamp = ""
            self.medidas = {}
            self._reload()
            self._initialized = True
    
    def _reload(self):
        """Recarga estado desde archivo."""
        if FormulaSecurityGates.LOCKDOWN_FILE.exists():
            try:
                data = json.loads(
                    FormulaSecurityGates.LOCKDOWN_FILE.read_text(encoding="utf-8")
                )
                self.estado = data.get("estado", "NORMAL")
                self.razon = data.get("razon", "")
                self.timestamp = data.get("activado_en", "")
                self.medidas = data.get("medidas", {})
            except Exception as e:
                logger.warning(f"Error cargando LOCKDOWN config: {e}")
    
    def mostrar_estado(self) -> str:
        """Retorna estado actual formateado."""
        self._reload()
        
        if self.estado == "BLOQUEADO":
            return f"""
╔════════════════════════════════════════════════════════════════╗
║                 🚨 SISTEMA EN LOCKDOWN 🚨                      ║
╠════════════════════════════════════════════════════════════════╣
║ Activado: {self.timestamp[:20]}                                  
║ Razón: {self.razon[:50]}...                              
║                                                                ║
║ Operaciones BLOQUEADAS:                                       ║
║   ✗ Descubrimiento de fórmulas externas                       ║
║   ✗ Duelos entre fórmulas                                     ║
║   ✗ Integración de fórmulas nuevas                            ║
║   ✗ Ciclos automáticos de optimización                        ║
║                                                                ║
║ ACCIÓN REQUERIDA:                                             ║
║   1. Revisar: data/REPORTE_AUDITORIA_CRITICA.txt              ║
║   2. Contactar: administrador@meteoser.local                  ║
║   3. Esperar: desbloqueo manual                               ║
╚════════════════════════════════════════════════════════════════╝
"""
        else:
            return "Sistema NORMAL - no hay restricciones"


# Test simple
if __name__ == "__main__":
    print("Verificando estado de LOCKDOWN...")
    print(LockdownConfig().mostrar_estado())
    print(f"En lockdown: {FormulaSecurityGates.esta_en_lockdown()}")
