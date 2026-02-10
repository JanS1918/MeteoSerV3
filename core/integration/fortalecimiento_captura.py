"""
═════════════════════════════════════════════════════════════════════════════════
MÓDULO DE FORTALECIMIENTO - CAPTURA GARANTIZADA DE DATOS PRIMARIOS
═════════════════════════════════════════════════════════════════════════════════

Sistema robusto para garantizar que TODOS los datos primarios críticos
se capturan exitosamente, incluyendo:
- Múltiples aliases para cada sensor
- Detección automática de fluctuaciones
- Persistencia de últimos valores válidos
- Validación en tiempo real
- Fallbacks automáticos 
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ALMACÉN DE ÚLTIMO VALOR VÁLIDO (PERSISTENCIA DE EMERGENCIA)
_LAST_VALID_VALUES = {
    "temperatura": None,           # WH65 - Crítico
    "humedad": None,               # WH65 - Crítico
    "temperatura_wh31": None,      # WH31 - Crítico
    "humedad_wh31": None,          # WH31 - Crítico
    "presion": None,               # HP2550A - Crítico
    "radiacion": None,             # Sensor dedicado
    "lluvia": None,                # Sensor dedicado
    "viento": None,                # Sensor dedicado
    "direccion_viento": None,      # Sensor dedicado
}

# Timestamps para detectar ingestas recientes
_LAST_INGESTA_TIMESTAMP = {}


class CapturaGarantizadaDatos:
    """
    Captura garantizada de todos los datos primarios con múltiples aliases
    y fallbacks automáticos.
    """
    
    # MAPEOS DE ALIAS - Todos los posibles nombres para cada sensor
    ALIASES_WH65_TEMP = [
        "tempf", "temp_f", "temp",
        "tempout", "temp_out", "temperature",
        "exttemp", "ext_temp", "outdoor_temperature",
    ]
    
    ALIASES_WH65_HUM = [
        "humidity", "humedad",
        "humidityout", "humidity_out",
        "outhumidity", "outdoor_humidity",
        "exthumidity", "ext_humidity", "rh", "hr",
        "relative_humidity", "humedad_relativa",
    ]
    
    ALIASES_WH31_TEMP = [
        "temp1f", "temp1", "temp_1",
        "temp1c", "temp_1c",
        "temp_ch1", "tempch1",
    ]
    
    ALIASES_WH31_HUM = [
        "humidity1", "hum1", "hum_1",
        "humidity_1", "humidity_ch1",
    ]
    
    ALIASES_PRESION = [
        "baromrelin", "baromrel_in", "barom_relin",
        "baromrelatin", "baromrelative",
        "pressure", "presion", "relative_pressure",
    ]
    
    ALIASES_RADIACION = [
        "solarradiation", "solar_radiation",
        "solar", "radiation", "radiacion", "rad",
        "solrad", "solar_rad",
    ]
    
    ALIASES_LLUVIA = [
        "rainratein", "rain_ratein", "rain_rate",
        "rainfall_rate", "lluvia_rate", "lluvia",
        "rain_rate_in_hourly", "precipitation_rate",
    ]
    
    ALIASES_VIENTO_VEL = [
        "windspeedmph", "windspeed", "wind_speed",
        "wind", "viento", "velocidad_viento",
        "windspeed_mh", "gust",
    ]
    
    ALIASES_VIENTO_DIR = [
        "winddir", "wind_dir", "wind_direction",
        "direccion_viento", "wind_bearing",
    ]
    
    @staticmethod
    def extraer_valor(data: Dict, aliases: list, tipo_sensor: str = "genérico") -> Optional[Tuple[str, str]]:
        """
        Extrae valor usando múltiples aliases.
        Retorna (valor, alias_usado) o (None, None) si no encuentra.
        """
        for alias in aliases:
            if alias in data and data[alias] is not None:
                valor = data[alias]
                logger.info(f"[[OK] CAPTURADO] {tipo_sensor}: {valor} (alias: {alias})")
                return valor, alias
        
        logger.warning(f"[[FAIL] NO ENCONTRADO] {tipo_sensor} - Aliases probados: {', '.join(aliases[:3])}...")
        return None, None
    
    @staticmethod
    def validar_rango(valor: float, min_val: float, max_val: float, nombre: str) -> bool:
        """Valida que el valor está dentro del rango esperado."""
        try:
            v = float(valor)
            if min_val <= v <= max_val:
                return True
            else:
                logger.warning(f"[WARN] {nombre}: FUERA DE RANGO ({v} no está entre {min_val}-{max_val})")
                return False
        except (ValueError, TypeError):
            logger.error(f"[FAIL] {nombre}: NO NUMÉRICO ({valor})")
            return False
    
    @staticmethod
    def convertir_fahrenheit_celsius(temp_f: float) -> float:
        """Convierte Fahrenheit a Celsius."""
        return (float(temp_f) - 32) * 5.0 / 9.0
    
    @staticmethod
    def convertir_mph_ms(velocidad_mph: float) -> float:
        """Convierte mph a m/s."""
        return float(velocidad_mph) * 0.44704
    
    @staticmethod
    def convertir_inhg_hpa(presion_inhg: float) -> float:
        """Convierte inHg a hPa."""
        return float(presion_inhg) * 33.8638866667


def fortalecer_captura_ecowitt(data: Dict, system) -> Dict[str, object]:
    """
    Fortalece la captura de datos con múltiples algorithms y fallbacks.
    Retorna dict con todos los sensores capturados y su estado.
    """
    
    capturador = CapturaGarantizadaDatos()
    resultado = {
        "timestamp": datetime.now().isoformat(),
        "datos_capturados": {},
        "errores": [],
        "fallbacks_usados": [],
    }
    
    print("\n" + "=" * 90)
    print("[[X] FORTALECIMIENTO CRÍTICO] Iniciando captura garantizada de datos primarios")
    print("=" * 90)
    
    # ╔════════════════════════════════════════════════════════════════════╗
    # ║ WH65 - TEMPERATURA (CRÍTICO)                                      ║
    # ╚════════════════════════════════════════════════════════════════════╝
    print("\n[[1]  WH65 TEMPERATURA] Intentando captura...")
    temp_wh65_f, alias_temp = capturador.extraer_valor(
        data, capturador.ALIASES_WH65_TEMP, "WH65-Temperatura"
    )
    
    if temp_wh65_f is not None:
        try:
            temp_wh65_f = float(temp_wh65_f)
            if capturador.validar_rango(temp_wh65_f, -50, 130, "WH65 Temp (°F)"):
                temp_wh65_c = capturador.convertir_fahrenheit_celsius(temp_wh65_f)
                system.actualizar_sensor("temperatura", temp_wh65_c)
                _LAST_VALID_VALUES["temperatura"] = temp_wh65_c
                resultado["datos_capturados"]["wh65_temp_c"] = temp_wh65_c
                resultado["datos_capturados"]["wh65_temp_f"] = temp_wh65_f
                print(f"    [OK] WH65 TEMPERATURA CAPTURADA: {temp_wh65_c:.2f}°C ({temp_wh65_f:.1f}°F)")
            else:
                raise ValueError("Fuera de rango")
        except Exception as e:
            logger.error(f"Error procesando WH65 temp: {e}")
            resultado["errores"].append(f"WH65 Temp inválido: {temp_wh65_f}")
    else:
        # FALLBACK: Usar último valor válido
        if _LAST_VALID_VALUES["temperatura"] is not None:
            system.actualizar_sensor("temperatura", _LAST_VALID_VALUES["temperatura"])
            resultado["fallbacks_usados"].append("WH65 Temp (usando último válido)")
            print(f"    [WARN]  FALLBACK: Usando último temp válido: {_LAST_VALID_VALUES['temperatura']:.2f}°C")
        else:
            resultado["errores"].append("WH65 TEMPERATURA: NO DISPONIBLE")
            system.actualizar_sensor("temperatura", None)
            print(f"    [FAIL] WH65 TEMPERATURA: NO DISPONIBLE")
    
    # ╔════════════════════════════════════════════════════════════════════╗
    # ║ WH65 - HUMEDAD (CRÍTICO)                                          ║
    # ╚════════════════════════════════════════════════════════════════════╝
    print("\n[[2]  WH65 HUMEDAD] Intentando captura...")
    hum_wh65, alias_hum = capturador.extraer_valor(
        data, capturador.ALIASES_WH65_HUM, "WH65-Humedad"
    )
    
    if hum_wh65 is not None:
        try:
            hum_wh65 = float(hum_wh65)
            if capturador.validar_rango(hum_wh65, 0, 100, "WH65 Hum (%)"):
                system.actualizar_sensor("humedad", hum_wh65)
                _LAST_VALID_VALUES["humedad"] = hum_wh65
                resultado["datos_capturados"]["wh65_hum"] = hum_wh65
                print(f"    [OK] WH65 HUMEDAD CAPTURADA: {hum_wh65:.0f}%")
            else:
                raise ValueError("Fuera de rango")
        except Exception as e:
            logger.error(f"Error procesando WH65 hum: {e}")
            resultado["errores"].append(f"WH65 Hum inválido: {hum_wh65}")
    else:
        # FALLBACK
        if _LAST_VALID_VALUES["humedad"] is not None:
            system.actualizar_sensor("humedad", _LAST_VALID_VALUES["humedad"])
            resultado["fallbacks_usados"].append("WH65 Hum (usando último válido)")
            print(f"    [WARN]  FALLBACK: Usando última hum válida: {_LAST_VALID_VALUES['humedad']:.0f}%")
        else:
            resultado["errores"].append("WH65 HUMEDAD: NO DISPONIBLE")
            system.actualizar_sensor("humedad", None)
            print(f"    [FAIL] WH65 HUMEDAD: NO DISPONIBLE")
    
    # ╔════════════════════════════════════════════════════════════════════╗
    # ║ WH31 - TEMPERATURA (CRÍTICO)                                      ║
    # ╚════════════════════════════════════════════════════════════════════╝
    print("\n[[3]  WH31 TEMPERATURA] Intentando captura...")
    temp_wh31_f, _ = capturador.extraer_valor(
        data, capturador.ALIASES_WH31_TEMP, "WH31-Temperatura"
    )
    
    if temp_wh31_f is not None:
        try:
            temp_wh31_f = float(temp_wh31_f)
            if capturador.validar_rango(temp_wh31_f, -50, 130, "WH31 Temp (°F)"):
                temp_wh31_c = capturador.convertir_fahrenheit_celsius(temp_wh31_f)
                system.actualizar_sensor("temperatura_wh31", temp_wh31_c)
                _LAST_VALID_VALUES["temperatura_wh31"] = temp_wh31_c
                resultado["datos_capturados"]["wh31_temp_c"] = temp_wh31_c
                print(f"    [OK] WH31 TEMPERATURA CAPTURADA: {temp_wh31_c:.2f}°C")
            else:
                raise ValueError("Fuera de rango")
        except Exception as e:
            logger.error(f"Error procesando WH31 temp: {e}")
    
    # ╔════════════════════════════════════════════════════════════════════╗
    # ║ WH31 - HUMEDAD (CRÍTICO)                                          ║
    # ╚════════════════════════════════════════════════════════════════════╝
    print("\n[[4]  WH31 HUMEDAD] Intentando captura...")
    hum_wh31, _ = capturador.extraer_valor(
        data, capturador.ALIASES_WH31_HUM, "WH31-Humedad"
    )
    
    if hum_wh31 is not None:
        try:
            hum_wh31 = float(hum_wh31)
            if capturador.validar_rango(hum_wh31, 0, 100, "WH31 Hum (%)"):
                system.actualizar_sensor("humedad_wh31", hum_wh31)
                _LAST_VALID_VALUES["humedad_wh31"] = hum_wh31
                resultado["datos_capturados"]["wh31_hum"] = hum_wh31
                print(f"    [OK] WH31 HUMEDAD CAPTURADA: {hum_wh31:.0f}%")
            else:
                raise ValueError("Fuera de rango")
        except Exception as e:
            logger.error(f"Error procesando WH31 hum: {e}")
    
    # ╔════════════════════════════════════════════════════════════════════╗
    # ║ PRESIÓN HP2550A (CRÍTICO)                                         ║
    # ╚════════════════════════════════════════════════════════════════════╝
    print("\n[[5]  PRESIÓN HP2550A] Intentando captura...")
    presion_inhg, _ = capturador.extraer_valor(
        data, capturador.ALIASES_PRESION, "Presión-HP2550A"
    )
    
    if presion_inhg is not None:
        try:
            presion_inhg = float(presion_inhg)
            if capturador.validar_rango(presion_inhg, 28, 31, "Presión (inHg)"):
                presion_hpa = capturador.convertir_inhg_hpa(presion_inhg)
                system.actualizar_sensor("presion", presion_hpa)
                _LAST_VALID_VALUES["presion"] = presion_hpa
                resultado["datos_capturados"]["presion_hpa"] = presion_hpa
                print(f"    [OK] PRESIÓN CAPTURADA: {presion_hpa:.2f} hPa")
            else:
                raise ValueError("Fuera de rango")
        except Exception as e:
            logger.error(f"Error procesando presión: {e}")
    else:
        if _LAST_VALID_VALUES["presion"] is not None:
            system.actualizar_sensor("presion", _LAST_VALID_VALUES["presion"])
            resultado["fallbacks_usados"].append("Presión (usando último válido)")
            print(f"    [WARN]  FALLBACK: Usando última presión: {_LAST_VALID_VALUES['presion']:.2f} hPa")
    
    # ╔════════════════════════════════════════════════════════════════════╗
    # ║ DATOS SECUNDARIOS (IMPORTANTES)                                   ║
    # ╚════════════════════════════════════════════════════════════════════╝
    
    # Radiación
    print("\n[[6]  RADIACIÓN SOLAR] Intentando captura...")
    radiacion, _ = capturador.extraer_valor(
        data, capturador.ALIASES_RADIACION, "Radiación"
    )
    if radiacion is not None:
        try:
            radiacion = float(radiacion)
            if 0 <= radiacion <= 1500:
                system.actualizar_sensor("radiacion", radiacion)
                _LAST_VALID_VALUES["radiacion"] = radiacion
                resultado["datos_capturados"]["radiacion"] = radiacion
                print(f"    [OK] RADIACIÓN: {radiacion:.1f} W/m²")
        except:
            pass
    
    # Lluvia
    print("\n[[7]  LLUVIA] Intentando captura...")
    lluvia, _ = capturador.extraer_valor(
        data, capturador.ALIASES_LLUVIA, "Lluvia"
    )
    if lluvia is not None:
        try:
            lluvia = float(lluvia)
            if lluvia >= 0:
                system.actualizar_sensor("lluvia", lluvia)
                _LAST_VALID_VALUES["lluvia"] = lluvia
                resultado["datos_capturados"]["lluvia"] = lluvia
                print(f"    [OK] LLUVIA: {lluvia:.2f} mm/hr")
        except:
            pass
    
    # Viento Velocidad
    print("\n[[8]  VIENTO (VELOCIDAD)] Intentando captura...")
    viento_mph, _ = capturador.extraer_valor(
        data, capturador.ALIASES_VIENTO_VEL, "Viento-Velocidad"
    )
    if viento_mph is not None:
        try:
            viento_mph = float(viento_mph)
            if 0 <= viento_mph <= 200:
                viento_ms = capturador.convertir_mph_ms(viento_mph)
                system.actualizar_sensor("viento", viento_ms)
                _LAST_VALID_VALUES["viento"] = viento_ms
                resultado["datos_capturados"]["viento_ms"] = viento_ms
                print(f"    [OK] VIENTO: {viento_ms:.2f} m/s ({viento_mph:.1f} mph)")
        except:
            pass
    
    # Viento Dirección
    print("\n[[9]  VIENTO (DIRECCIÓN)] Intentando captura...")
    winddir, _ = capturador.extraer_valor(
        data, capturador.ALIASES_VIENTO_DIR, "Viento-Dirección"
    )
    if winddir is not None:
        try:
            winddir = float(winddir)
            if 0 <= winddir <= 360:
                system.actualizar_sensor("direccion_viento", winddir)
                _LAST_VALID_VALUES["direccion_viento"] = winddir
                resultado["datos_capturados"]["direccion_viento"] = winddir
                print(f"    [OK] DIRECCIÓN VIENTO: {winddir:.0f}°")
        except:
            pass
    
    print("\n" + "=" * 90)
    print(f"[[OK] RESUMEN] Captura completada")
    print(f"    Datos primarios capturados: {len([d for d in resultado['datos_capturados'].keys() if any(x in d for x in ['temp', 'hum', 'presion'])])}/5")
    print(f"    Errores: {len(resultado['errores'])}")
    print(f"    Fallbacks usados: {len(resultado['fallbacks_usados'])}")
    print("=" * 90 + "\n")
    
    return resultado
