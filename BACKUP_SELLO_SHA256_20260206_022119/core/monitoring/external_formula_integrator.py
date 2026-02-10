#!/usr/bin/env python3
"""
ExternalFormulaIntegrator: Integración de ganadora externa a FORMULA_HIERARCHY

Si una fórmula externa gana el duelo, se integra aquí.
Crea un wrapper compatible con FORMULA_HIERARCHY.
"""

from __future__ import annotations

import json
import logging
import importlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any, List, Callable

logger = logging.getLogger("meteoser.external_formula_integrator")


@dataclass
class IntegrationLog:
    """Log de integración"""
    timestamp: float
    parametro: str
    externa_id: str
    externa_nombre: str
    wrapper_id: str
    status: str  # "created", "tested", "integrated"
    notas: str


class ExternalFormulaIntegrator:
    """
    Integra fórmulas externas ganadoras en FORMULA_HIERARCHY.
    
    Proceso:
    1. Validar que ganadora pasó duelo
    2. Crear wrapper compatible con FORMULA_HIERARCHY
    3. Registrar en FORMULA_HIERARCHY
    4. Guardar como backup
    5. Marcar como "ganadora_integrada"
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.integration_log_file = self.data_dir / "formula_integration_log.json"
        self.wrappers_dir = base_dir / "core" / "monitoring" / "external_wrappers"
        self.wrappers_dir.mkdir(parents=True, exist_ok=True)
        self._logs: List[Dict[str, Any]] = []
        self._load_logs()

    def _load_logs(self) -> None:
        """Carga histórico de integraciones."""
        if not self.integration_log_file.exists():
            self._logs = []
            return
        try:
            raw = json.loads(self.integration_log_file.read_text(encoding="utf-8"))
            self._logs = raw.get("integraciones", [])
        except Exception as e:
            logger.exception(f"Error cargando logs de integración: {e}")
            self._logs = []

    def _save_logs(self) -> None:
        """Persiste logs de integración."""
        try:
            payload = {"integraciones": self._logs[-200:]}  # Últimas 200
            self.integration_log_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            logger.exception(f"Error guardando logs de integración: {e}")

    def integrar_ganadora(
        self,
        parametro: str,
        externa_id: str,
        externa_nombre: str,
        externa_ref: str,
        inputs_requeridos: List[str],
        score_duelo: float,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Integra fórmula externa ganadora.

        Args:
            parametro: parámetro afectado (ej: "sensacion_termica")
            externa_id: ID de candidata externa
            externa_nombre: nombre legible
            externa_ref: referencia a función (ej: "scipy.special.erf")
            inputs_requeridos: inputs que necesita
            score_duelo: score que obtuvo en el duelo
            metadata: datos adicionales

        Returns:
            True si integración fue exitosa
        """

        logger.info(f"🔧 Integrando ganadora: {externa_nombre}")
        logger.info(f"   Parámetro: {parametro}")
        logger.info(f"   Score: {score_duelo:.2f}/100")

        # === FASE 1: Crear wrapper ===
        wrapper_id = f"external_{parametro}_{externa_id}"
        wrapper_code = self._generar_wrapper(
            wrapper_id,
            externa_nombre,
            externa_ref,
            inputs_requeridos,
            parametro,
            metadata
        )

        if not wrapper_code:
            logger.error("[ERROR] No se pudo generar wrapper")
            self._log_integracion(
                parametro, externa_id, externa_nombre, wrapper_id,
                "failed", "No se pudo generar wrapper"
            )
            return False

        # === FASE 2: Guardar wrapper ===
        wrapper_path = self.wrappers_dir / f"{wrapper_id}.py"
        try:
            wrapper_path.write_text(wrapper_code, encoding="utf-8")
            logger.info(f"   [OK] Wrapper guardado: {wrapper_path}")
        except Exception as e:
            logger.error(f"[ERROR] Error guardando wrapper: {e}")
            self._log_integracion(
                parametro, externa_id, externa_nombre, wrapper_id,
                "failed", f"Error guardando: {str(e)}"
            )
            return False

        # === FASE 3: Validar que sea importable ===
        try:
            # Importar el módulo dinámicamente
            import importlib.util
            try:
                spec = importlib.util.spec_from_file_location(wrapper_id, wrapper_path)
                modulo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modulo)
            except (AttributeError, TypeError):
                # Fallback para versiones antiguas de Python
                import sys
                import types
                modulo = types.ModuleType(wrapper_id)
                with open(str(wrapper_path), "r", encoding="utf-8") as f:
                    code = compile(f.read(), str(wrapper_path), "exec")
                    exec(code, modulo.__dict__)
            logger.info(f"   [OK] Wrapper importable")
        except Exception as e:
            logger.error(f"[ERROR] Wrapper no importable: {e}")
            self._log_integracion(
                parametro, externa_id, externa_nombre, wrapper_id,
                "failed", f"Error importación: {str(e)}"
            )
            return False

        # === FASE 4: Registrar metadata ===
        registro = {
            "parametro": parametro,
            "externa_id": externa_id,
            "externa_nombre": externa_nombre,
            "wrapper_id": wrapper_id,
            "wrapper_path": str(wrapper_path),
            "externa_ref": externa_ref,
            "inputs": inputs_requeridos,
            "score_duelo": score_duelo,
            "timestamp_integracion": datetime.now(timezone.utc).timestamp(),
            "metadata": metadata,
            "status": "integrated"
        }

        # Guardar en registry de externas integradas
        self._guardar_registro_integracion(registro)

        self._log_integracion(
            parametro, externa_id, externa_nombre, wrapper_id,
            "integrated", "Integración exitosa"
        )

        logger.info(f"[OK] Ganadora integrada exitosamente")
        return True

    def _generar_wrapper(
        self,
        wrapper_id: str,
        nombre: str,
        ref: str,
        inputs: List[str],
        parametro: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Genera código wrapper compatible con FORMULA_HIERARCHY.
        """

        inputs_str = ", ".join(inputs)

        codigo = f'''#!/usr/bin/env python3
"""
Wrapper para fórmula externa: {nombre}
ID: {wrapper_id}
Ref: {ref}

GANADORA del duelo para parámetro: {parametro}
Score: {metadata.get('score', 0):.2f}/100
Integrada: {datetime.now(timezone.utc).isoformat()}
"""

import logging

logger = logging.getLogger(__name__)


def {wrapper_id}({inputs_str}) -> dict:
    """
    Wrapper de fórmula externa ganadora.
    
    Entrada compatible con bus de parámetros.
    Salida: dict con 'valor' y 'metadata'.
    """
    try:
        # Importar función externa
        from {ref.rsplit(".", 1)[0]} import {ref.rsplit(".", 1)[1]}
        fn = {ref.rsplit(".", 1)[1]}
        
        # Ejecutar con inputs
        resultado = fn({inputs_str})
        
        # Normalizar resultado
        if isinstance(resultado, dict):
            valor = resultado.get("valor") or list(resultado.values())[0]
        else:
            valor = resultado
            
        return {{
            "valor": float(valor),
            "metadata": {{
                "fuente": "externa",
                "wrapper": "{wrapper_id}",
                "parametro": "{parametro}"
            }}
        }}
    
    except Exception as e:
        logger.error(f"Error en {wrapper_id}: {{e}}")
        return {{
            "valor": None,
            "metadata": {{"error": str(e)}}
        }}


# === Para compatibilidad con FORMULA_HIERARCHY ===
__formula_id__ = "{wrapper_id}"
__nombre__ = "{nombre}"
__parametro__ = "{parametro}"
__inputs__ = {inputs}
__score__ = {metadata.get('score', 0.0)}
__status__ = "integrated_external"
'''

        return codigo

    def _guardar_registro_integracion(self, registro: Dict[str, Any]) -> None:
        """Registra integración en archivo."""
        try:
            registry_file = self.data_dir / "integrated_external_formulas.json"
            registros = []

            if registry_file.exists():
                raw = json.loads(registry_file.read_text(encoding="utf-8"))
                registros = raw.get("registros", [])

            registros.append(registro)

            payload = {"registros": registros}
            registry_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
            logger.info(f"   📝 Registro de integración guardado")

        except Exception as e:
            logger.exception(f"Error guardando registro: {e}")

    def _log_integracion(
        self,
        parametro: str,
        externa_id: str,
        externa_nombre: str,
        wrapper_id: str,
        status: str,
        notas: str
    ) -> None:
        """Registra evento de integración."""
        log = {
            "timestamp": datetime.now(timezone.utc).timestamp(),
            "parametro": parametro,
            "externa_id": externa_id,
            "externa_nombre": externa_nombre,
            "wrapper_id": wrapper_id,
            "status": status,
            "notas": notas
        }
        self._logs.append(log)
        self._save_logs()

    def listar_integradas(self) -> List[Dict[str, Any]]:
        """Lista fórmulas externas integradas."""
        registry_file = self.data_dir / "integrated_external_formulas.json"
        if not registry_file.exists():
            return []

        try:
            raw = json.loads(registry_file.read_text(encoding="utf-8"))
            return raw.get("registros", [])
        except Exception:
            return []

    def obtener_wrapper_id(self, parametro: str) -> Optional[str]:
        """
        Obtiene wrapper ID de fórmula externa integrada más reciente
        para un parámetro.
        """
        integradas = self.listar_integradas()
        filtradas = [r for r in integradas if r.get("parametro") == parametro]

        if filtradas:
            # Más reciente
            return max(filtradas, key=lambda r: r.get("timestamp_integracion", 0)).get("wrapper_id")

        return None

    def obtener_info_integrada(self, parametro: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de fórmula integrada para un parámetro."""
        integradas = self.listar_integradas()
        filtradas = [r for r in integradas if r.get("parametro") == parametro]

        if filtradas:
            return max(filtradas, key=lambda r: r.get("timestamp_integracion", 0))

        return None
