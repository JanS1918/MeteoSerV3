"""
═══════════════════════════════════════════════════════════════════════════════
GRIFO INTELIGENTE V30.0 - PUBLICACIÓN HÍBRIDA (OMNISCIENTE + BAJO DEMANDA)
═══════════════════════════════════════════════════════════════════════════════

Arquitectura Definitiva:
  TIER 1 (Whitelist Sagrada V30.0): 50 parámetros SIEMPRE publicados, sin excepciones
  TIER 2 (Layout-Aware): Datos requeridos por paneles activos del dashboard
  TIER 3 (Centinela): Vigilancia silenciosa en RAM; publica + alerta si riesgo >= 0.7
  HEARTBEAT: Detección de Consola de Guardia - Patrulla Eterna 24/7

Integración: Whitelist + Suscripción + Centinela + Heartbeat = OMNISCIENTE
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from core.bus.whitelist_sagrados_v30 import (
    WhitelistSagradosV30,
    SuscripcionLayoutV30,
    CentinelaV30,
    HeartbeatConsolaV30
)

logger = logging.getLogger("bus_grifo_inteligente")


class GrifoInteligente:
    """
    Controla qué se publica y qué queda en sombra (RAM).
    Integra Whitelist Sagrada V30.0, Layout-Aware Publishing, Centinela y Heartbeat.
    """

    _instance = None
    _lock = threading.RLock()

    def __init__(self) -> None:
        self._dashboard_activo = True  # Tablet encendida 24/7 (default)
        self._ia_activa = True
        self._modo_dashboard = "always"

        # TIER 1: Usar Whitelist Sagrada V30.0 (50 parámetros inmutables)
        self._whitelist_sagrada = WhitelistSagradosV30.obtener_categoria(None)  # Get all
        self._whitelist_exact = WhitelistSagradosV30.TODOS_50_SAGRADOS

        # TIER 2: Suscripción Layout-Aware
        self._suscripcion_layout = SuscripcionLayoutV30()

        # TIER 3: Centinela de emergencia
        self._centinela = CentinelaV30()

        # HEARTBEAT: Consola de Guardia
        self._heartbeat = HeartbeatConsolaV30()

        # Cache local (RAM) para valores en sombra
        self._cache_local: Dict[str, Dict[str, Any]] = {}

        self._cargar_config_desde_env()

    @classmethod
    def obtener_instancia(cls) -> "GrifoInteligente":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set_dashboard_activo(self, activo: bool) -> None:
        with self._lock:
            self._dashboard_activo = activo
            logger.info(f"🟢 Dashboard activo: {activo}")

    def set_ia_activa(self, activo: bool) -> None:
        with self._lock:
            self._ia_activa = activo

    def set_modo_dashboard(self, modo: str) -> None:
        """Modo: always | auto | off"""
        modo_norm = (modo or "").strip().lower()
        if modo_norm not in {"always", "auto", "off"}:
            logger.warning(f"⚠️ Modo dashboard inválido: {modo}")
            return
        with self._lock:
            self._modo_dashboard = modo_norm
            if modo_norm == "always":
                self._dashboard_activo = True
            elif modo_norm == "off":
                self._dashboard_activo = False
            logger.info(f"🟢 Modo dashboard: {self._modo_dashboard}")

    def _cargar_config_desde_env(self) -> None:
        """Configura el grifo según variables de entorno."""
        modo = os.getenv("METEOSER_DASHBOARD_MODE", "always")
        self.set_modo_dashboard(modo)

    def _es_numero(self, valor: Any) -> bool:
        return isinstance(valor, (int, float)) and not isinstance(valor, bool)

    def _nombre_en_whitelist(self, nombre: str) -> bool:
        if nombre in self._whitelist_exact:
            return True
        return any(nombre.startswith(prefix) for prefix in self._whitelist_prefixes)

    def _dashboard_interesado(self, nombre: str) -> bool:
        return any(pat in nombre for pat in self._dashboard_patterns)

    def _cruza_umbral(self, nombre: str, valor: Any) -> bool:
        if not self._es_numero(valor):
            return False
        nombre_lower = nombre.lower()
        for clave, umbral in self._umbrales_criticos.items():
            if clave in nombre_lower and valor >= umbral:
                return True
        return False

    def _nombre_en_whitelist_sagrada(self, nombre: str) -> bool:
        """Verifica si está en la Whitelist Sagrada V30.0 (TIER 1)."""
        return WhitelistSagradosV30.es_sagrado(nombre)

    def _debe_publicar_layout_aware(self, nombre: str) -> bool:
        """Verifica si debe publicarse por Tier 2 (Layout-Aware)."""
        return self._suscripcion_layout.debe_publicar_tier2(nombre)

    def _centinela_alerta_emergencia(self, nombre: str, valor: Any) -> bool:
        """Verifica si debe publicarse por Tier 3 (Centinela con umbral >= 0.7)."""
        return self._centinela.evaluar_parametro(nombre, valor)

    def _guardar_cache(self, nombre: str, valor: Any, unidad: str, origen: str) -> None:
        self._cache_local[nombre] = {
            "valor": valor,
            "unidad": unidad,
            "origen": origen,
            "timestamp": datetime.now()
        }

    def obtener_cache(self, nombre: str) -> Optional[Dict[str, Any]]:
        return self._cache_local.get(nombre)

    def obtener_valor(self, nombre: str) -> Any:
        dato = self.obtener_cache(nombre)
        return None if dato is None else dato.get("valor")

    # ════════════════════════════════════════════════════════════════════════════
    # LÓGICA CENTRALIZADA: TIER 1 + TIER 2 + TIER 3 + HEARTBEAT
    # ════════════════════════════════════════════════════════════════════════════

    def permitir_publicacion(self, nombre: str, valor: Any) -> bool:
        """
        Decisión centralizada: ¿Publicar o mantener en RAM?

        TIER 1 (Whitelist Sagrada): SIEMPRE publica
        TIER 2 (Layout-Aware): Publica si panel activo lo requiere
        TIER 3 (Centinela): Publica si riesgo >= 0.7 (emergencia)
        """
        # TIER 1: Whitelist Sagrada V30.0 - SIEMPRE PUBLICA
        if self._nombre_en_whitelist_sagrada(nombre):
            return True

        # TIER 3: Centinela - PUBLICA SI ALERTA >= 0.7
        if self._centinela_alerta_emergencia(nombre, valor):
            return True

        # TIER 2: Layout-Aware - PUBLICA SI PANEL LO REQUIERE
        if self._debe_publicar_layout_aware(nombre):
            return True

        # Default: Mantener en RAM (Tier 3)
        return False

    def publicar_si_interes(
        self,
        bus: Any,
        nombre: str,
        valor: Any,
        unidad: str = "",
        origen: str = "auto"
    ) -> bool:
        """Publica aplicando la lógica Tier 1 + Tier 2 + Tier 3 + Heartbeat."""
        # Guardar en cache local (Tier 3 - RAM)
        self._guardar_cache(nombre, valor, unidad, origen)

        # Registrar heartbeat si es requerido
        if nombre in ["heartbeat", "consola_latido", "estado_dashboard"]:
            self._heartbeat.registrar_heartbeat()

        # Decidir si publicar
        if not self.permitir_publicacion(nombre, valor):
            return False

        # Publicar en bus
        return self._publicar_en_bus(bus, nombre, valor, unidad, origen)

    def _publicar_en_bus(
        self,
        bus: Any,
        nombre: str,
        valor: Any,
        unidad: str,
        origen: str
    ) -> bool:
        """Intenta publicar usando firma flexible."""
        try:
            bus.publicar(
                nombre,
                valor,
                nivel="CORE" if self._nombre_en_whitelist_sagrada(nombre) else "INTERMEDIATE",
                origen=origen,
                unidad=unidad
            )
            return True
        except TypeError:
            try:
                bus.publicar(nombre, valor, unidad)
                return True
            except TypeError:
                bus.publicar(nombre, valor)
                return True

    # ════════════════════════════════════════════════════════════════════════════
    # MÉTODOS DE CONTROL: LAYOUT-AWARE + CENTINELA + HEARTBEAT
    # ════════════════════════════════════════════════════════════════════════════

    def activar_panel(self, nombre_panel: str) -> None:
        """Activa un panel del dashboard (Tier 2 - Layout-Aware)."""
        self._suscripcion_layout.activar_panel(nombre_panel)

    def desactivar_panel(self, nombre_panel: str) -> None:
        """Desactiva un panel del dashboard."""
        self._suscripcion_layout.desactivar_panel(nombre_panel)

    def obtener_alertas_centinela(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todas las alertas activas del Centinela (Tier 3)."""
        return self._centinela.obtener_alertas_activas()

    def obtener_estado_heartbeat(self) -> Dict[str, Any]:
        """Obtiene el estado del Heartbeat de Consola de Guardia."""
        return self._heartbeat.obtener_estado()

    def obtener_diagnostico_completo(self) -> Dict[str, Any]:
        """Genera un diagnóstico completo del estado actual del Grifo."""
        return {
            "timestamp": datetime.now().isoformat(),
            "version": "V30.0",
            "whitelist_sagrada": {
                "total": WhitelistSagradosV30.contar(),
                "estado": "ACTIVA ✅" if self._nombre_en_whitelist_sagrada("temperatura") else "ERROR ❌"
            },
            "tier2_layout": {
                "paneles_activos": list(self._suscripcion_layout.paneles_activos),
                "datos_requeridos": sorted(self._suscripcion_layout.obtener_datos_requeridos())
            },
            "tier3_centinela": {
                "alertas_activas": len(self._centinela.obtener_alertas_activas()),
                "alertas": self._centinela.obtener_alertas_activas()
            },
            "heartbeat": self._heartbeat.obtener_estado(),
            "cache_size": len(self._cache_local)
        }

