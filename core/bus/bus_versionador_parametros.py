"""
═══════════════════════════════════════════════════════════════════════════════
GUARDRAIL 2: VERSIONADOR DE PARÁMETROS
═══════════════════════════════════════════════════════════════════════════════

Rastreo de cambios en fórmulas de parámetros.
Si Hardy cambia su fórmula de presión de vapor, versionamos el cambio.

SISTEMA DE VERSIONES:
- hardy_presion_pa:v1 = Fórmula Tetens original
- hardy_presion_pa:v2 = Fórmula Wexler mejorada
- hardy_presion_pa:v3 = Corrección por altitud

Ventaja: Depuración histórica + rollback posible
"""

import logging
import threading
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json

logger = logging.getLogger("bus_versionador_parametros")


@dataclass
class VersionParametro:
    """Una versión específica de un parámetro"""
    nombre: str
    version: str
    modulo: str
    timestamp: datetime
    formula: Optional[str] = None  # Código de la fórmula
    formula_hash: str = ""  # SHA256 de la fórmula
    cambios_respecto_anterior: str = ""  # Descripción de qué cambió
    confianza: float = 1.0  # 0-1, nivel de validación de la nueva versión
    
    def a_dict(self) -> Dict:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


class VersionadorParametros:
    """
    Sistema de versionado de parámetros del Bus.
    
    Mantiene:
    - Historial completo de versiones
    - Hash de fórmulas para detectar cambios
    - Metadatos de cambios
    - Comparación entre versiones
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __init__(self):
        self.historial: Dict[str, List[VersionParametro]] = {}  # nombre → [v1, v2, v3...]
        self.versiones_actuales: Dict[str, str] = {}  # nombre → versión_actual
        
    @classmethod
    def obtener_instancia(cls) -> 'VersionadorParametros':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _calcular_hash_formula(self, formula: str) -> str:
        """Calcula SHA256 de una fórmula"""
        return hashlib.sha256(formula.encode()).hexdigest()[:16]
    
    def registrar_version(
        self,
        nombre: str,
        modulo: str,
        formula: Optional[str] = None,
        cambios: str = "",
        confianza: float = 1.0
    ) -> str:
        """
        Registra una nueva versión de un parámetro.
        
        Args:
            nombre: Nombre del parámetro (ej: "hardy_presion_pa")
            modulo: Módulo origen
            formula: Código de la fórmula (opcional, para auditoria)
            cambios: Descripción de qué cambió respecto a versión anterior
            confianza: Nivel de confianza (0-1)
        
        Returns:
            Versión asignada (v1, v2, v3, etc.)
        """
        with self._lock:
            # Determinar número de versión
            if nombre not in self.historial:
                self.historial[nombre] = []
                num_version = 1
            else:
                num_version = len(self.historial[nombre]) + 1
            
            version_str = f"v{num_version}"
            
            # Calcular hash de fórmula
            formula_hash = self._calcular_hash_formula(formula) if formula else ""
            
            # Crear versión
            version_obj = VersionParametro(
                nombre=nombre,
                version=version_str,
                modulo=modulo,
                timestamp=datetime.now(),
                formula=formula,
                formula_hash=formula_hash,
                cambios_respecto_anterior=cambios,
                confianza=confianza
            )
            
            # Guardar en historial
            self.historial[nombre].append(version_obj)
            self.versiones_actuales[nombre] = version_str
            
            # Log
            accion = "Creada" if num_version == 1 else "Actualizada"
            logger.info(f"[REINICIO] {accion}: {nombre}:{version_str} (confianza: {confianza*100:.0f}%)")
            
            if cambios:
                logger.info(f"   Cambios: {cambios}")
            
            return version_str
    
    def obtener_version_actual(self, nombre: str) -> Optional[str]:
        """Obtiene versión actual de un parámetro"""
        with self._lock:
            return self.versiones_actuales.get(nombre)
    
    def obtener_historial(self, nombre: str) -> List[VersionParametro]:
        """Obtiene historial completo de versiones"""
        with self._lock:
            return self.historial.get(nombre, []).copy()
    
    def comparar_versiones(self, nombre: str, v1: str, v2: str) -> Dict:
        """Compara dos versiones de un parámetro"""
        with self._lock:
            historial = self.historial.get(nombre, [])
            
            version1 = next((v for v in historial if v.version == v1), None)
            version2 = next((v for v in historial if v.version == v2), None)
            
            if not version1 or not version2:
                return {"error": "Versión no encontrada"}
            
            return {
                "parametro": nombre,
                "v1": v1,
                "v2": v2,
                "fecha_v1": version1.timestamp.isoformat(),
                "fecha_v2": version2.timestamp.isoformat(),
                "cambios": version2.cambios_respecto_anterior,
                "formula_hash_cambio": version1.formula_hash != version2.formula_hash,
                "confianza_v1": version1.confianza,
                "confianza_v2": version2.confianza
            }
    
    def generar_audit_trail(self, nombre: str) -> str:
        """Genera auditoría completa de un parámetro"""
        with self._lock:
            historial = self.historial.get(nombre, [])
            
            if not historial:
                return f"No hay historial para '{nombre}'"
            
            audit = f"\n📋 AUDITORÍA: {nombre}\n"
            audit += "=" * 60 + "\n"
            
            for v in historial:
                audit += f"  {v.version}: {v.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                audit += f"    Módulo: {v.modulo}\n"
                audit += f"    Confianza: {v.confianza*100:.0f}%\n"
                if v.cambios_respecto_anterior:
                    audit += f"    Cambios: {v.cambios_respecto_anterior}\n"
                if v.formula_hash:
                    audit += f"    Hash: {v.formula_hash}\n"
                audit += "\n"
            
            return audit
    
    def resumen(self) -> Dict:
        """Resumen de estado del versionador"""
        with self._lock:
            return {
                "parametros_versionados": len(self.historial),
                "total_versiones": sum(len(v) for v in self.historial.values()),
                "parametros_con_cambios": len([h for h in self.historial.values() if len(h) > 1]),
                "ultimos_cambios": [
                    {
                        "parametro": p,
                        "version_actual": self.versiones_actuales[p],
                        "versions_totales": len(self.historial[p])
                    }
                    for p in list(self.versiones_actuales.keys())[-10:]
                ]
            }
