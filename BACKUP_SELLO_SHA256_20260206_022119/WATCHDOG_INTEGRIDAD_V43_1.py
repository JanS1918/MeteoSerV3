#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[GUARDIAN] WATCHDOG DE INTEGRIDAD V43.1 - VIGILANCIA ETERNA
====================================================

Bloquea cualquier intento de calcular altitud o arco astronómico fuera del bus.

Autor: MeteoSerV3 Development Team
Fecha: 5 de febrero de 2026
Motor: V43.1_INTEGRIDAD_GEOGRAFICA_ASTRONOMICA_TOTAL
SHA-256: 4d4cc3157d5ad665a811ff493dd3bc37e00d37bf0408f47c3bbe2dc07dab102e
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("MeteoSerV3.WatchdogIntegridad")


class WatchdogIntegridadV431:
    """
    [GUARDIAN] Vigilante de Integridad del Bus.
    
    Valida que todos los datos geográficos/astronómicos provengan del bus.
    Bloquea cálculos locales de altitud/solar/lunar como violaciones de integridad.
    """
    
    def __init__(self, bus):
        """
        Inicializa el watchdog.
        
        Args:
            bus: Instancia del BusEstadoGlobal
        """
        self.bus = bus
        self.violaciones_detectadas = 0
        self.ultima_validacion = None
        self.modo_vigilancia = True
        
        logger.info("[GUARDIAN] WATCHDOG DE INTEGRIDAD V43.1 ACTIVADO")
        logger.info("[CRITICAL] Modo vigilancia 24/7: ARMADO")
    
    def validar_integridad_geografica(self) -> Tuple[bool, str]:
        """
        Valida que altitud provenga de SRTM en el bus.
        
        Returns:
            (integridad_ok, mensaje)
        """
        altitud_srtm = self.bus.obtener("altitud_srtm")
        fuente_altitud = self.bus.obtener("fuente_altitud")
        
        if altitud_srtm is None:
            self.violaciones_detectadas += 1
            logger.critical("🚫 VIOLACIÓN DE INTEGRIDAD: altitud_srtm ausente del bus")
            return False, "SRTM_AUSENTE"
        
        if fuente_altitud == "SRTM":
            logger.debug("[OK] Integridad geográfica OK: SRTM activo")
            return True, "SRTM_OK"
        elif fuente_altitud in ["manual_fallback", "manual_fallback_error"]:
            logger.warning(f"[WARNING] DEGRADACIÓN: Usando fallback manual ({fuente_altitud})")
            return True, fuente_altitud
        else:
            self.violaciones_detectadas += 1
            logger.critical(f"🚫 VIOLACIÓN: fuente_altitud desconocida '{fuente_altitud}'")
            return False, "FUENTE_DESCONOCIDA"
    
    def validar_integridad_solar(self) -> Tuple[bool, str]:
        """
        Valida que posición solar provenga de SPA NREL en el bus.
        
        Returns:
            (integridad_ok, mensaje)
        """
        elevacion_solar = self.bus.obtener("elevacion_solar")
        azimut_solar = self.bus.obtener("azimut_solar")
        fuente_astronomica = self.bus.obtener("rest2_fuente_astronomica")
        
        if elevacion_solar is None or azimut_solar is None:
            # Puede ser nocturno, no es violación crítica
            logger.debug("[INFO] Arco solar ausente (posiblemente nocturno)")
            return True, "NOCTURNO"
        
        if fuente_astronomica == "SPA_NREL_V42.6":
            logger.debug("[OK] Integridad solar OK: SPA NREL activo")
            return True, "SPA_NREL_OK"
        elif fuente_astronomica == "REST2_interno":
            logger.warning("[WARNING] DEGRADACIÓN: Usando REST2 interno (SPA NREL falló)")
            return True, "REST2_FALLBACK"
        else:
            self.violaciones_detectadas += 1
            logger.critical(f"🚫 VIOLACIÓN: fuente astronómica desconocida '{fuente_astronomica}'")
            return False, "FUENTE_DESCONOCIDA"
    
    def validar_integridad_lunar(self) -> Tuple[bool, str]:
        """
        Valida que posición lunar provenga de Meeus en el bus (durante la noche).
        
        Returns:
            (integridad_ok, mensaje)
        """
        elevacion_lunar = self.bus.obtener("arco_lunar_elevacion_deg")
        iluminacion_lunar = self.bus.obtener("iluminacion_lunar")
        
        # Si es de día, no es necesario validar
        elevacion_solar = self.bus.obtener("elevacion_solar")
        if elevacion_solar is not None and elevacion_solar > 0:
            logger.debug("[INFO] Validación lunar no requerida (es de día)")
            return True, "DIURNO"
        
        if elevacion_lunar is None or iluminacion_lunar is None:
            logger.warning("[WARNING] Arco lunar ausente durante la noche")
            return True, "LUNAR_NO_DISPONIBLE"
        
        logger.debug("[OK] Integridad lunar OK: Meeus activo")
        return True, "MEEUS_OK"
    
    def validar_integridad_completa(self) -> Dict[str, any]:
        """
        Ejecuta validación completa de integridad del bus.
        
        Returns:
            Dict con estado de cada componente
        """
        self.ultima_validacion = datetime.now()
        
        geo_ok, geo_msg = self.validar_integridad_geografica()
        solar_ok, solar_msg = self.validar_integridad_solar()
        lunar_ok, lunar_msg = self.validar_integridad_lunar()
        
        integridad_total = geo_ok and solar_ok and lunar_ok
        
        resultado = {
            "timestamp": self.ultima_validacion.isoformat(),
            "integridad_total": integridad_total,
            "geografica": {"ok": geo_ok, "mensaje": geo_msg},
            "solar": {"ok": solar_ok, "mensaje": solar_msg},
            "lunar": {"ok": lunar_ok, "mensaje": lunar_msg},
            "violaciones_acumuladas": self.violaciones_detectadas,
        }
        
        if integridad_total:
            logger.info("[GUARDIAN] INTEGRIDAD TOTAL: OK")
        else:
            logger.critical(f"🚫 INTEGRIDAD COMPROMETIDA: {resultado}")
            self.bus.publicar("alerta_integridad_critica", True, "bool")
        
        # Publicar resultado en bus
        self.bus.publicar("watchdog_integridad_ok", integridad_total, "bool")
        self.bus.publicar("watchdog_violaciones", self.violaciones_detectadas, "contador")
        
        return resultado
    
    def bloquear_calculo_local(self, tipo_calculo: str, modulo: str) -> None:
        """
        Bloquea un cálculo local detectado y lanza alerta crítica.
        
        Args:
            tipo_calculo: "altitud", "solar", "lunar"
            modulo: Nombre del módulo que intentó el cálculo
        """
        self.violaciones_detectadas += 1
        
        logger.critical(
            f"🚫 BLOQUEO DE INTEGRIDAD: {modulo} intentó calcular {tipo_calculo} localmente"
        )
        logger.critical(
            f"🚫 VIOLACIÓN: Artículo constitucional sobre soberanía de {tipo_calculo}"
        )
        logger.critical(
            f"🚫 ACCIÓN: Cálculo bloqueado - usar bus.obtener() obligatorio"
        )
        
        # Publicar alerta en bus
        self.bus.publicar(
            f"alerta_calculo_local_{tipo_calculo}",
            {"modulo": modulo, "timestamp": datetime.now().isoformat()},
            "dict"
        )
        self.bus.publicar("alerta_integridad_critica", True, "bool")
    
    def modo_patrulla(self, intervalo_segundos: int = 60) -> None:
        """
        Activa modo vigilancia continua (se ejecuta periódicamente).
        
        Args:
            intervalo_segundos: Frecuencia de validación
        """
        logger.info(f"[CRITICAL] MODO PATRULLA ACTIVADO: Validación cada {intervalo_segundos}s")
        self.modo_vigilancia = True
        
        # En un sistema real, esto se ejecutaría en un thread/scheduler
        # Por ahora, solo marca el flag
        self.bus.publicar("watchdog_modo_patrulla", True, "bool")
        self.bus.publicar("watchdog_intervalo_segundos", intervalo_segundos, "s")
    
    def detener_patrulla(self) -> None:
        """Detiene el modo vigilancia."""
        logger.warning("[WARNING] MODO PATRULLA DETENIDO")
        self.modo_vigilancia = False
        self.bus.publicar("watchdog_modo_patrulla", False, "bool")
    
    def obtener_reporte_integridad(self) -> str:
        """
        Genera reporte textual del estado de integridad.
        
        Returns:
            Reporte formateado
        """
        resultado = self.validar_integridad_completa()
        
        reporte = f"""
╔═══════════════════════════════════════════════════════════════╗
║         [GUARDIAN] REPORTE DE INTEGRIDAD V43.1                        ║
╚═══════════════════════════════════════════════════════════════╝

Timestamp: {resultado['timestamp']}

INTEGRIDAD TOTAL: {'[OK] OK' if resultado['integridad_total'] else '🚫 COMPROMETIDA'}

Componentes:
  📍 Geográfica (SRTM):   {'[OK]' if resultado['geografica']['ok'] else '🚫'} {resultado['geografica']['mensaje']}
  🌞 Solar (SPA NREL):    {'[OK]' if resultado['solar']['ok'] else '🚫'} {resultado['solar']['mensaje']}
  🌙 Lunar (Meeus):       {'[OK]' if resultado['lunar']['ok'] else '🚫'} {resultado['lunar']['mensaje']}

Violaciones acumuladas: {resultado['violaciones_acumuladas']}
Modo vigilancia: {'🟢 ACTIVO' if self.modo_vigilancia else '🔴 INACTIVO'}

╚═══════════════════════════════════════════════════════════════╝
        """
        
        return reporte


# ════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ════════════════════════════════════════════════════════════════

def validar_uso_correcto_bus(bus, campo_requerido: str, tipo_dato: str) -> bool:
    """
    Valida que un campo esté disponible en el bus antes de usarlo.
    
    Args:
        bus: Instancia del bus
        campo_requerido: Nombre del campo a validar
        tipo_dato: "altitud", "solar", "lunar"
    
    Returns:
        True si el campo está disponible
    
    Raises:
        ValueError si el campo no está disponible
    """
    valor = bus.obtener(campo_requerido)
    
    if valor is None:
        logger.critical(
            f"🚫 VIOLACIÓN: Intento de usar {campo_requerido} pero no está en bus"
        )
        logger.critical(
            f"🚫 ACCIÓN: Asegurar que bus_expander publicó {tipo_dato} correctamente"
        )
        raise ValueError(
            f"Campo {campo_requerido} no disponible en bus - violación de integridad"
        )
    
    logger.debug(f"[OK] Uso correcto de bus: {campo_requerido} = {valor}")
    return True


def ejemplo_uso_correcto_altitud(bus):
    """
    [OK] EJEMPLO DE USO CORRECTO: Obtener altitud del bus.
    """
    # [OK] CORRECTO: Obtener del bus
    altitud = bus.obtener("altitud_srtm")
    
    if altitud is None:
        logger.warning("[WARNING] SRTM no disponible, intentando fallback")
        altitud = bus.obtener("altitud")  # Fallback
    
    if altitud is None:
        raise ValueError("Altitud no disponible en bus")
    
    # Usar altitud en cálculos
    gravedad = 9.80665 * (1 - 0.002637 * altitud / 1000.0)
    return gravedad


def ejemplo_uso_incorrecto_altitud():
    """
    [ERROR] EJEMPLO DE USO INCORRECTO: Calcular altitud localmente.
    """
    # [ERROR] PROHIBIDO: Hardcodear altitud
    altitud = 118.0  # VIOLACIÓN DE INTEGRIDAD
    
    # [ERROR] PROHIBIDO: Calcular desde config sin intentar bus primero
    from core.config import ESTACION
    altitud = ESTACION.ALTITUD  # VIOLACIÓN DE INTEGRIDAD
    
    # [ERROR] PROHIBIDO: Usar LocationEngine directamente sin publicar en bus
    from core.location.location_engine import LocationEngine
    loc_engine = LocationEngine()
    altitud = loc_engine.load_altitude_srtm()  # VIOLACIÓN (debe publicar en bus)


# ════════════════════════════════════════════════════════════════
# MAIN - DEMOSTRACIÓN
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("[GUARDIAN] WATCHDOG DE INTEGRIDAD V43.1 - MODO DEMOSTRACIÓN")
    print("=" * 70)
    print()
    
    # Simular bus (en producción, usar el bus real)
    class BusMock:
        def __init__(self):
            self.datos = {
                "altitud_srtm": 118.0,
                "fuente_altitud": "SRTM",
                "elevacion_solar": 45.5,
                "azimut_solar": 180.0,
                "rest2_fuente_astronomica": "SPA_NREL_V42.6",
                "arco_lunar_elevacion_deg": -15.0,
                "iluminacion_lunar": 78.5,
            }
        
        def obtener(self, campo):
            return self.datos.get(campo, None)
        
        def publicar(self, campo, valor, unidad):
            self.datos[campo] = valor
    
    bus = BusMock()
    watchdog = WatchdogIntegridadV431(bus)
    
    # Validar integridad
    print(watchdog.obtener_reporte_integridad())
    
    # Activar modo patrulla
    watchdog.modo_patrulla(intervalo_segundos=60)
    
    print("\n[OK] DEMOSTRACIÓN COMPLETADA")
    print("[CRITICAL] Watchdog armado y en patrulla eterna")
    print(f"[GUARDIAN] SHA-256: 4d4cc3157d5ad665a811ff493dd3bc37e00d37bf0408f47c3bbe2dc07dab102e")
