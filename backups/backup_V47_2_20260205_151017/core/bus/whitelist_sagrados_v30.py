"""
═══════════════════════════════════════════════════════════════════════════════
WHITELIST SAGRADA V30.0 - EDICIÓN OMNISCIENTE
═══════════════════════════════════════════════════════════════════════════════

Define explícitamente los 50 parámetros sagrados (Tier 1) que SIEMPRE se publican
al Bus, independientemente del layout, interacción o modo de operación.

Estos son los "pilares del Acorazado": datos físicos validados que garantizan
la seguridad y continuidad del sistema 24/7 en modo patrulla.

ESTRATIFICACIÓN:
  • FÍSICA DE ÉLITE (Trinity - 15): Hardy, OMM, REST2 - Patrones de medida absolutos
  • SOBERANÍA GEOGRÁFICA (5): Gravedad, Altitud, Coordenadas - Fundamento del lugar
  • METEOROLOGÍA CRÍTICA (20): Temp, Humedad, Presión, Viento, Lluvia, Radiación
  • SEGURIDAD E ÍNDICES (10): CPU, Disco, Red, Riesgos, Alertas, Salud del sistema

Total: 50 parámetros sagrados = Vigilancia Omnisciente
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
from typing import Set, Dict, List, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger("meteoser.whitelist_sagrados_v30")


class CategoriaT1(Enum):
    """Categorías de los 50 Sagrados"""
    FISICA_ELITE = "FISICA_ELITE"
    SOBERANIA_GEOGRAFICA = "SOBERANIA_GEOGRAFICA"
    METEOROLOGIA_CRITICA = "METEOROLOGIA_CRITICA"
    SEGURIDAD_INDICES = "SEGURIDAD_INDICES"


class WhitelistSagradosV30:
    """
    Whitelist Sagrada V30.0 - Los 50 parámetros inmutables del Acorazado.
    Publicación GARANTIZADA, sin excepciones.
    """

    # ════════════════════════════════════════════════════════════════════════════
    # LOS 50 SAGRADOS - DEFINICIÓN EXPLÍCITA
    # ════════════════════════════════════════════════════════════════════════════

    # GRUPO 1: FÍSICA DE ÉLITE (Trinity - 15 parámetros)
    FISICA_ELITE = {
        # Hardy (NIST) - 5 parámetros
        "hardy_temperatura_bulbo_humedo",      # Tb
        "hardy_temperatura_bulbo_seco",         # Tbs
        "hardy_presion_vapor_saturado",         # Ps
        "hardy_densidad_aire",                  # ρ
        "hardy_entalpia_especifica",            # h

        # OMM (WMO) - 5 parámetros
        "omm_densidad_temperatura_virtual",     # ρv
        "omm_temperatura_equivalente",          # θe
        "omm_presion_vapor",                    # e
        "omm_humedad_relativa_calidad",         # Qc
        "omm_exponente_adiabatic",              # Γ

        # REST2 (Gueymard) - 5 parámetros
        "rest2_irradiancia_directa_normal",     # DNI
        "rest2_irradiancia_difusa_horizontal",  # DHI
        "rest2_irradiancia_global_horizontal",  # GHI
        "rest2_clearness_index",                # Kt
        "rest2_aerosol_optical_depth",          # AOD
    }

    # GRUPO 2: SOBERANÍA GEOGRÁFICA (5 parámetros)
    SOBERANIA_GEOGRAFICA = {
        "gravedad_argentona",                   # g = 9.80272394 m/s²
        "altitud",                              # elevation (m)
        "latitud",                              # latitude (decimal degrees)
        "longitud",                             # longitude (decimal degrees)
        "huso_horario",                         # timezone offset
    }

    # GRUPO 3: METEOROLOGÍA CRÍTICA (20 parámetros)
    METEOROLOGIA_CRITICA = {
        # Temperatura (4)
        "temperatura",                          # T (°C)
        "temperatura_exterior",                 # T_ext (°C)
        "temperatura_interior",                 # T_int (°C)
        "punto_rocio",                          # Td (°C)

        # Humedad (3)
        "humedad",                              # HR (%)
        "humedad_relativa",                     # RH (%)
        "humedad_suelo",                        # Θ_soil (%)

        # Presión (3)
        "presion",                              # P (hPa)
        "presion_relativa",                     # P_rel (hPa)
        "presion_absoluta",                     # P_abs (hPa)

        # Viento (5)  ⬆️ ASCENDIDO A TIER 1 (27 FEB 2026)
        "viento",                               # V (m/s) - Agregado como compuesto
        "velocidad_viento",                     # Vwind (m/s)
        "racha_viento",                         # Vgust (m/s)
        "direccion_viento",                     # θ_wind (°)
        "racha_maxima_horaria",                 # Vgust_max (m/s)

        # Lluvia (3)
        "lluvia",                               # P_rain (mm/h)
        "lluvia_tasa",                          # P_rate (mm/h)
        "lluvia_acumulada",                     # P_acum (mm)

        # Radiación (3)
        "radiacion_solar",                      # G (W/m²)
        "radiacion_uv",                         # UV (MED)
        "radiacion_infrarroja",                 # R_IR (W/m²)
    }

    # GRUPO 4: SEGURIDAD E ÍNDICES (10 parámetros)
    SEGURIDAD_INDICES = {
        # Índices humanos de confort/salud (4)
        "utci",                                 # Universal Thermal Climate Index
        "pmv",                                  # Predicted Mean Vote
        "wbgt",                                 # Wet Bulb Globe Temperature
        "sensacion_termica",                    # Apparent Temperature

        # Riesgos climáticos (4)
        "riesgo_helada",                        # Frost risk (0-1)
        "riesgo_tormenta",                      # Storm risk (0-1)
        "riesgo_inundacion",                    # Flood risk (0-1)
        "riesgo_incendio",                      # Fire risk (0-1)

        # Salud del sistema (2)
        "sistema_cpu_carga",                    # CPU load (%)
        "sistema_salud_general",                # System health (0-1)
    }

    # Reunir todos los sagrados
    TODOS_50_SAGRADOS = (
        FISICA_ELITE |
        SOBERANIA_GEOGRAFICA |
        METEOROLOGIA_CRITICA |
        SEGURIDAD_INDICES
    )

    # Verificación de conteo
    assert len(TODOS_50_SAGRADOS) == 51, f"❌ ERROR: Whitelist tiene {len(TODOS_50_SAGRADOS)} sagrados, no 51 (Viento ascendido 27-FEB-2026)"

    # ════════════════════════════════════════════════════════════════════════════
    # MAPEO CATEGORIA -> SAGRADOS
    # ════════════════════════════════════════════════════════════════════════════

    SAGRADOS_POR_CATEGORIA: Dict[CategoriaT1, Set[str]] = {
        CategoriaT1.FISICA_ELITE: FISICA_ELITE,
        CategoriaT1.SOBERANIA_GEOGRAFICA: SOBERANIA_GEOGRAFICA,
        CategoriaT1.METEOROLOGIA_CRITICA: METEOROLOGIA_CRITICA,
        CategoriaT1.SEGURIDAD_INDICES: SEGURIDAD_INDICES,
    }

    # ════════════════════════════════════════════════════════════════════════════
    # MÉTODOS DE CONSULTA
    # ════════════════════════════════════════════════════════════════════════════

    @classmethod
    def es_sagrado(cls, nombre: str) -> bool:
        """Verifica si un parámetro es sagrado (Tier 1)."""
        return nombre in cls.TODOS_50_SAGRADOS

    @classmethod
    def obtener_categoria(cls, nombre: str) -> CategoriaT1 | None:
        """Obtiene la categoría de un parámetro sagrado."""
        for categoria, sagrados in cls.SAGRADOS_POR_CATEGORIA.items():
            if nombre in sagrados:
                return categoria
        return None

    @classmethod
    def listar_por_categoria(cls, categoria: CategoriaT1) -> Set[str]:
        """Lista todos los sagrados de una categoría."""
        return cls.SAGRADOS_POR_CATEGORIA.get(categoria, set())

    @classmethod
    def listar_todos(cls) -> Set[str]:
        """Lista los 50 sagrados."""
        return cls.TODOS_50_SAGRADOS.copy()

    @classmethod
    def contar(cls) -> int:
        """Retorna el conteo total de sagrados (siempre 50)."""
        return len(cls.TODOS_50_SAGRADOS)

    @classmethod
    def generar_certificado(cls) -> Dict[str, Any]:
        """Genera un certificado de la Whitelist Sagrada."""
        return {
            "timestamp": datetime.now().isoformat(),
            "version": "V30.0",
            "nombre": "Whitelist Sagrada - Edición Omnisciente",
            "total_sagrados": cls.contar(),
            "categorias": {
                cat.value: {
                    "cantidad": len(sagrados),
                    "parametros": sorted(list(sagrados))
                }
                for cat, sagrados in cls.SAGRADOS_POR_CATEGORIA.items()
            },
            "garantia": "Publicación GARANTIZADA, sin excepciones, 24/7"
        }

    @classmethod
    def imprimir_diagnostico(cls) -> None:
        """Imprime un diagnóstico completo de la Whitelist."""
        cert = cls.generar_certificado()
        print("\n" + "="*80)
        print("📋 WHITELIST SAGRADA V30.0 - DIAGNÓSTICO COMPLETO")
        print("="*80)
        print(f"Timestamp: {cert['timestamp']}")
        print(f"Total de parámetros sagrados: {cert['total_sagrados']} ✅")
        print("\nDesglose por categoría:")
        for cat, data in cert['categorias'].items():
            print(f"\n  {cat} ({data['cantidad']})")
            for param in data['parametros']:
                print(f"    • {param}")
        print("\n" + "="*80)
        print("✅ ACORAZADO LISTO PARA PATRULLA ETERNA")
        print("="*80 + "\n")


# ════════════════════════════════════════════════════════════════════════════════
# SUSCRIPCIÓN INTELIGENTE DE LAYOUT (Tier 2)
# ════════════════════════════════════════════════════════════════════════════════

class SuscripcionLayoutV30:
    """
    Tier 2: Publicación dinámica basada en paneles activos del dashboard.
    El sistema detecta qué datos el dashboard está mostrando y mantiene
    esos datos frescos y disponibles sin latencia.
    """

    def __init__(self):
        self.paneles_activos: Set[str] = set()
        self.patrones_panel: Dict[str, Set[str]] = {
            "sensors": {
                "temperatura", "humedad", "presion", "viento", "lluvia", "radiacion"
            },
            "indices": {
                "utci", "pmv", "wbgt", "sensacion_termica",
                "riesgo_helada", "riesgo_tormenta", "riesgo_inundacion", "riesgo_incendio"
            },
            "physics": {
                "hardy_temperatura_bulbo_humedo", "hardy_temperatura_bulbo_seco",
                "hardy_densidad_aire", "omm_densidad_temperatura_virtual",
                "rest2_irradiancia_directa_normal", "rest2_irradiancia_global_horizontal"
            },
            "location": {
                "gravedad_argentona", "altitud", "latitud", "longitud"
            },
            "health": {
                "sistema_cpu_carga", "sistema_salud_general"
            },
        }
        self.ultima_actualizacion = datetime.now()

    def activar_panel(self, nombre_panel: str) -> None:
        """Activa un panel y marca sus datos para publicación."""
        self.paneles_activos.add(nombre_panel)
        self.ultima_actualizacion = datetime.now()
        logger.info(f"✅ Panel activado: {nombre_panel}")

    def desactivar_panel(self, nombre_panel: str) -> None:
        """Desactiva un panel."""
        self.paneles_activos.discard(nombre_panel)
        logger.info(f"❌ Panel desactivado: {nombre_panel}")

    def obtener_datos_requeridos(self) -> Set[str]:
        """Retorna todos los datos que los paneles activos necesitan (Tier 2)."""
        datos = set()
        for panel in self.paneles_activos:
            datos.update(self.patrones_panel.get(panel, set()))
        return datos

    def debe_publicar_tier2(self, nombre: str) -> bool:
        """Verifica si un parámetro debe publicarse por demanda Tier 2."""
        datos_requeridos = self.obtener_datos_requeridos()
        return nombre in datos_requeridos


# ════════════════════════════════════════════════════════════════════════════════
# CENTINELA CON SALTO DE EMERGENCIA (Tier 3)
# ════════════════════════════════════════════════════════════════════════════════

class CentinelaV30:
    """
    Tier 3: Vigilancia silenciosa de datos técnicos en RAM.
    Si un parámetro cruza el umbral de alarma (>= 0.7), el sistema
    publica la alerta y la hace visible en el dashboard.
    """

    def __init__(self):
        self.umbrales_emergencia: Dict[str, float] = {
            "riesgo_helada": 0.7,
            "riesgo_tormenta": 0.7,
            "riesgo_inundacion": 0.7,
            "riesgo_incendio": 0.7,
            "alerta_helada": 0.7,
            "alerta_tormenta": 0.7,
            "alerta_frio_extremo": 0.8,
            "alerta_calor_extremo": 0.8,
            "temperatura_anomalia": 0.75,
            "presion_anomalia": 0.75,
            "viento_anomalia": 0.75,
        }
        self.alertas_activas: Dict[str, Dict[str, Any]] = {}

    def evaluar_parametro(self, nombre: str, valor: float) -> bool:
        """Evalúa si un parámetro ha cruzado umbral y debe publicarse."""
        if not isinstance(valor, (int, float)):
            return False

        umbral = self.umbrales_emergencia.get(nombre)
        if umbral is None:
            return False

        if valor >= umbral:
            self.alertas_activas[nombre] = {
                "valor": valor,
                "umbral": umbral,
                "timestamp": datetime.now().isoformat(),
                "severidad": "CRÍTICA" if valor >= 0.9 else "ALTA"
            }
            logger.warning(f"🚨 CENTINELA ALERTA: {nombre} = {valor} (umbral: {umbral})")
            return True

        self.alertas_activas.pop(nombre, None)
        return False

    def obtener_alertas_activas(self) -> Dict[str, Dict[str, Any]]:
        """Retorna todas las alertas activas."""
        return self.alertas_activas.copy()


# ════════════════════════════════════════════════════════════════════════════════
# HEARTBEAT DE CONSOLA DE GUARDIA (Latido del Acorazado)
# ════════════════════════════════════════════════════════════════════════════════

class HeartbeatConsolaV30:
    """
    Detección de "Consola de Guardia": La tablet/PC que vigila el sistema 24/7.
    El sistema detecta cuándo la consola está conectada y activa el modo
    vigilancia perpetua (Patrulla Eterna).
    """

    def __init__(self):
        self.consola_conectada = False
        self.modo_patrulla_eterna = False
        self.ultimo_heartbeat = None
        self.intervalo_heartbeat = 30  # segundos

    def registrar_heartbeat(self) -> None:
        """Registra que la consola está viva y conectada."""
        self.consola_conectada = True
        self.ultimo_heartbeat = datetime.now()
        self.modo_patrulla_eterna = True
        logger.info("💓 Heartbeat recibido - Consola de Guardia ACTIVA - Patrulla Eterna ACTIVADA")

    def verificar_heartbeat(self, timeout_segundos: int = 120) -> bool:
        """Verifica si el heartbeat sigue activo (dentro del timeout)."""
        if self.ultimo_heartbeat is None:
            return False

        elapsed = (datetime.now() - self.ultimo_heartbeat).total_seconds()
        if elapsed > timeout_segundos:
            self.consola_conectada = False
            self.modo_patrulla_eterna = False
            logger.warning(f"⚠️ Heartbeat PERDIDO - Consola de Guardia desconectada (timeout: {elapsed}s)")
            return False

        return True

    def obtener_estado(self) -> Dict[str, Any]:
        """Retorna el estado del heartbeat y la consola."""
        return {
            "consola_conectada": self.consola_conectada,
            "modo_patrulla_eterna": self.modo_patrulla_eterna,
            "ultimo_heartbeat": self.ultimo_heartbeat.isoformat() if self.ultimo_heartbeat else None,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Diagnóstico completo
    WhitelistSagradosV30.imprimir_diagnostico()

    # Ejemplos de uso
    print("\n📌 EJEMPLOS DE USO")
    print("="*80)

    # Verificar si un parámetro es sagrado
    print("\n✅ Verificar sagrados:")
    for param in ["temperatura", "utci", "cpu_carga", "desconocido"]:
        es_sag = WhitelistSagradosV30.es_sagrado(param)
        print(f"  {param}: {es_sag}")

    # Obtener categoría
    print("\n📂 Categorías:")
    for param in ["temperatura", "gravedad_argentona", "utci"]:
        cat = WhitelistSagradosV30.obtener_categoria(param)
        print(f"  {param}: {cat.value if cat else 'N/A'}")

    # Suscripción de layout
    print("\n🎯 Suscripción de Layout (Tier 2):")
    suscripcion = SuscripcionLayoutV30()
    suscripcion.activar_panel("sensors")
    suscripcion.activar_panel("indices")
    datos = suscripcion.obtener_datos_requeridos()
    print(f"  Paneles activos: {suscripcion.paneles_activos}")
    print(f"  Datos requeridos: {sorted(datos)}")

    # Centinela
    print("\n🚨 Centinela (Tier 3):")
    centinela = CentinelaV30()
    centinela.evaluar_parametro("riesgo_helada", 0.75)
    centinela.evaluar_parametro("riesgo_tormenta", 0.5)
    print(f"  Alertas activas: {centinela.obtener_alertas_activas()}")

    # Heartbeat
    print("\n💓 Heartbeat de Consola:")
    heartbeat = HeartbeatConsolaV30()
    heartbeat.registrar_heartbeat()
    print(f"  Estado: {heartbeat.obtener_estado()}")
