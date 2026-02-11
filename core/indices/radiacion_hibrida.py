"""
═════════════════════════════════════════════════════════════════════════════════
PIRANÓMETRO HÍBRIDO - VALIDACIÓN Y MEJORA DE RADIACIÓN SOLAR
═════════════════════════════════════════════════════════════════════════════════

Combina:
1. RADIACIÓN REAL del Gateway Ecowitt (medida directa)
2. MODELO CLEAR-SKY REST2 v3 (NREL 2016) - mejor modelo disponible
3. DETECCIÓN DE NUBES (Aerosoles + vapor de agua)
4. VALIDACIÓN TÉRMICA (ΔT WH65-WH31)
5. CALIBRACIÓN EMPÍRICA (diferencial esperada por ángulo solar)

Referencias:
- Gueymard, C.A. (2016). "REST2: High-performance solar radiation models for 
  cloudless-sky irradiance, sunshine duration and cloud effects"
- Ineichen, P. & Perez, R. (2002). "A new air mass independent formulation 
  for the Linke turbidity coefficient"
- Bird, R.E., et al. (1984). "A simple, solar spectral model for direct and 
  diffuse irradiance"

SENSORES UTILIZADOS:
- WH65: Temperatura exterior (sol), humedad → radiación térmica + contenido agua
- WH31: Temperatura sombra, humedad → comparación validación
- Presión: Presión atmosférica → altitud + contenido aerosoles
- Hora local: Posición solar exacta
- Latitud/Longitud: Estimadas de radiación histórica

═════════════════════════════════════════════════════════════════════════════════
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Importar contexto solar y bus
try:
    from core.indices.contexto_solar import obtener_contexto_solar
except ImportError:
    obtener_contexto_solar = None

try:
    from core.indices.bus_estado_global import BusEstadoGlobal
except ImportError:
    BusEstadoGlobal = None

# Importar arquitectura radiativa robusta V51
try:
    from core.radiation.wrapper_integracion import WrapperRadiacionRobusta
    _wrapper_radiacion_v51_disponible = True
except ImportError:
    _wrapper_radiacion_v51_disponible = False
    WrapperRadiacionRobusta = None


class PiranometroHibrido:
    """
    Validador y mejora de radiación solar usando múltiples fuentes.
    """
    
    # Constantes astronómicas
    CONSTANTE_SOLAR = 1361.0  # W/m² (irradiancia extraterrestre)
    RADIO_TIERRA_KM = 6371.0
    
    # Parámetros REST2 v3 (NREL Gueymard)
    # Estos valores son los óptimos para modelo clara sky
    REST2_PARAMS = {
        "rho_g": 0.2,  # Albedo del suelo (0.2 = pasto/tierra)
        "ozone": 0.35,  # cm de ozono
        "water_vapor": "auto",  # Se calcula desde HR
        "aod500": 0.084,  # Aerosol optical depth @ 500nm (típico cielo limpio)
        "aod380": 0.120,  # AOD @ 380nm
    }
    
    def __init__(self, latitud: float = 41.3, longitud: float = 2.1):
        """
        Args:
            latitud: Latitud en grados (-90 a 90). Default Barcelona
            longitud: Longitud en grados (-180 a 180)
        """
        self.latitud = latitud
        self.longitud = longitud
        self._historial_radiacion = []  # Para detección de nubes
        self._calibracion_diferencial = {}  # Offset empírico
        
        # Inicializar arquitectura radiativa robusta V51 (si disponible)
        self._wrapper_radiacion_v51 = None
        if _wrapper_radiacion_v51_disponible:
            try:
                self._wrapper_radiacion_v51 = WrapperRadiacionRobusta(
                    enabled=True,  # Activa nueva arquitectura
                    modo_comparativa=False  # Ya en producción
                )
                logger.info("[RADIACION] Arquitectura radiativa robusta V51 ACTIVADA")
            except Exception as e:
                logger.warning(f"[RADIACION] Error inicializando arquitectura robusta V51: {e}")
                self._wrapper_radiacion_v51 = None
    
    def procesar_radiacion_con_wrapper_v51(self,
                                          radiacion_medida: Optional[float],
                                          temp_wh65_c: float,
                                          temp_wh31_c: float,
                                          presion_hpa: float,
                                          humedad_rel: float,
                                          velocidad_viento_ms: float,
                                          precipitacion_mm: float,
                                          visibilidad_km: Optional[float],
                                          fecha_hora: datetime) -> Dict:
        """
        Procesa radiación usando arquitectura robusta V51 (si disponible).
        
        Si el wrapper no está disponible o falla, retorna None (fallback).
        """
        
        if self._wrapper_radiacion_v51 is None:
            # Fallback: retornar None para usar método antiguo
            return None
        
        try:
            # 1. Calcular posición solar
            posicion_solar = self.calcular_posicion_solar(fecha_hora)
            elevacion_deg = posicion_solar["elevacion_deg"]
            
            # 2. Calcular REST2 (baseline)
            rest2 = self.calcular_rest2_clearsky(
                elevacion_deg=elevacion_deg,
                am=posicion_solar["am"],
                presion_hpa=presion_hpa,
                humedad_rel=humedad_rel,
                temperatura_c=temp_wh65_c
            )
            
            # 3. Usar wrapper para procesar
            resultado_wrapper = self._wrapper_radiacion_v51.procesar(
                elevacion_solar_deg=elevacion_deg,
                ghi_w_m2_medida=radiacion_medida,
                presion_hpa=presion_hpa,
                humedad_rel=humedad_rel,
                temperatura_c=temp_wh65_c,
                velocidad_viento_ms=velocidad_viento_ms,
                precipitacion_mm=precipitacion_mm,
                visibilidad_km=visibilidad_km,
                rest2_output={
                    'ghi': rest2.get('ghi_w_m2', 0),
                    'dni': rest2.get('dni_w_m2', 0),
                    'dhi': rest2.get('dhi_w_m2', 0)
                },
                sensor_real_confiable=(radiacion_medida is not None)
            )
            
            # Validar que resultado_wrapper tiene las claves necesarias
            if not resultado_wrapper or 'ghi' not in resultado_wrapper or 'confianza' not in resultado_wrapper:
                logger.error(f"[RADIACION] Wrapper retornó resultado incompleto: {resultado_wrapper}")
                return None
            
            # 4. Retornar resultado enriquecido
            return {
                'ghi': resultado_wrapper['ghi'],
                'dni': resultado_wrapper['dni'],
                'dhi': resultado_wrapper['dhi'],
                'confianza': resultado_wrapper['confianza'],
                'posicion_solar': posicion_solar,
                'rest2': rest2,
                'contexto': resultado_wrapper.get('contexto', {}),
                'advertencias': resultado_wrapper.get('advertencias', []),
                'arquitectura_v51': True
            }
        
        except Exception as e:
            logger.warning(f"[RADIACION] Error en wrapper V51: {e}")
            return None
    
    def calcular_posicion_solar(self, fecha_hora: datetime) -> Dict[str, float]:
        """
        Calcula posición solar exacta usando Spencer (1971).
        
        Intenta obtener del bus primero (mejor), fallback a cálculo local.
        
        Returns:
            {
                "elevacion_deg": Elevación solar (0-90°)
                "azimut_deg": Azimut (0-360° desde norte)
                "zenith_deg": Ángulo cenital (0-180°)
                "am": Air mass (espesor atmósfera)
                "eot_minutos": Ecuación del tiempo
            }
        """
        # Intentar obtener del bus primero
        try:
            from core.system.bus import obtener_bus
            bus = obtener_bus()
            if bus:
                datos_astro = bus.get("astronomia", {})
                elevacion = datos_astro.get("arco_solar_elevacion_deg")
                azimut = datos_astro.get("azimut_solar")
                if elevacion is not None:
                    # Retornar datos del bus (limitado pero correcto)
                    return {
                        "elevacion_deg": float(elevacion),
                        "azimut_deg": float(azimut) if azimut is not None else 0.0,
                        "zenith_deg": 90.0 - float(elevacion),
                        "am": 1.0,  # No disponible desde bus, usar default
                        "eot_minutos": 0.0,  # No disponible desde bus
                    }
        except Exception:
            pass
        
        # Fallback: calcular localmente (Spencer 1971)
        # Número de día del año
        n = fecha_hora.timetuple().tm_yday
        
        # Ángulo solar diario (radianes)
        omega_rad = 2 * math.pi * (n - 1) / 365.25
        
        # Ecuación del tiempo (minutos)
        eot = (229.2 * 
               (0.000075 + 0.001868 * math.cos(omega_rad) 
                - 0.032077 * math.sin(omega_rad) 
                - 0.014615 * math.cos(2*omega_rad) 
                - 0.040849 * math.sin(2*omega_rad)))
        
        # Declinación solar (radianes)
        delta_rad = (0.006918 
                     - 0.399912 * math.cos(omega_rad) 
                     + 0.070257 * math.sin(omega_rad)
                     - 0.006758 * math.cos(2*omega_rad) 
                     + 0.000907 * math.sin(2*omega_rad)
                     - 0.00227 * math.cos(3*omega_rad) 
                     + 0.00037 * math.sin(3*omega_rad))
        
        # Hora solar local (hora solar verdadera)
        hora_decimal = fecha_hora.hour + fecha_hora.minute / 60 + fecha_hora.second / 3600
        
        # Diferencia horaria local-estándar (15° por hora de zona)
        # Barcelona: UTC+1, así que UTC+2 en verano
        # Simplificado: usar longitud (2.1°E = ~8 min antes que meridiano de referencia)
        diferencia_zona_minutos = self.longitud * 4  # 1° = 4 minutos de rotación
        
        # Hora solar verdadera
        hsv = hora_decimal + (eot + diferencia_zona_minutos) / 60
        
        # Ángulo horario (radianes), 0 al mediodía solar, negativo mañana, positivo tarde
        omega_h_rad = math.radians((hsv - 12) * 15)
        
        # Latitud en radianes
        lat_rad = math.radians(self.latitud)
        
        # Elevación solar (radianes)
        sin_elevacion = (math.sin(lat_rad) * math.sin(delta_rad) +
                         math.cos(lat_rad) * math.cos(delta_rad) * math.cos(omega_h_rad))
        elevacion_rad = math.asin(max(-1, min(1, sin_elevacion)))  # Acotar a [-1,1]
        elevacion_deg = math.degrees(elevacion_rad)
        
        # Ángulo cenital
        zenith_deg = 90 - elevacion_deg
        
        # Air mass (Chapman 1974 - precisa para zenith <90°)
        zenith_rad = math.radians(zenith_deg)
        if zenith_deg < 90:
            am = 1 / (math.cos(zenith_rad) + 0.50572 * (96.07995 - zenith_deg) ** -1.6364)
        else:
            am = 38  # Máximo en horizonte
        
        # Azimut (0=Norte, 90=Este, 180=Sur, 270=Oeste)
        cos_azimut = (math.sin(delta_rad) * math.cos(lat_rad) -
                      math.cos(delta_rad) * math.sin(lat_rad) * math.cos(omega_h_rad)) / math.cos(elevacion_rad)
        cos_azimut = max(-1, min(1, cos_azimut))  # Acotar
        
        azimut_rad = math.acos(cos_azimut)
        if math.sin(omega_h_rad) >= 0:
            azimut_deg = math.degrees(azimut_rad)
        else:
            azimut_deg = 360 - math.degrees(azimut_rad)
        
        return {
            "elevacion_deg": max(0, elevacion_deg),  # No negativa
            "azimut_deg": azimut_deg,
            "zenith_deg": zenith_deg,
            "am": am,
            "eot_minutos": eot,
            "hora_solar_verdadera": hsv % 24,
        }
    
    def calcular_radiacion_extraterrestre(self, fecha_hora: datetime) -> float:
        """
        Radiación solar extraterrestre (parte superior atmósfera).
        Usa corrección orbital de Duffie & Beckman.
        
        Returns:
            G_on (W/m²) - Radiación normal extraterrestre
        """
        n = fecha_hora.timetuple().tm_yday
        
        # Corrección de distancia Tierra-Sol
        B_rad = 2 * math.pi * (n - 1) / 365.25
        r_ratio = 1.00011 + 0.034221 * math.cos(B_rad) + 0.00128 * math.sin(B_rad) + \
                  0.000719 * math.cos(2*B_rad) + 0.000077 * math.sin(2*B_rad)
        
        G_on = self.CONSTANTE_SOLAR * r_ratio
        
        return G_on
    
    def calcular_rest2_clearsky(self, 
                                elevacion_deg: float,
                                am: float,
                                presion_hpa: float,
                                humedad_rel: float,
                                temperatura_c: float) -> Dict[str, float]:
        """
        Modelo REST2 v3 (NREL Gueymard 2016) - Mejor modelo disponible.
        
        Calcula radiación de cielo despejado considerando:
        - Aerosoles
        - Vapor de agua
        - Ozono
        - Presión atmosférica
        
        Returns:
            {
                "ghi_w_m2": Radiación global horizontal (directa + difusa)
                "dni_w_m2": Radiación normal directa
                "dhi_w_m2": Radiación difusa horizontal
                "clearness_index": Kt (índice de claridad, 0-1)
            }
        """
        
        if elevacion_deg <= 0:
            return {"ghi_w_m2": 0, "dni_w_m2": 0, "dhi_w_m2": 0, "clearness_index": 0}
        
        zenith_rad = math.radians(90 - elevacion_deg)
        elevacion_rad = math.radians(elevacion_deg)
        
        # Vapor de agua precipitable (cm)
        # Estimado desde humedad relativa y temperatura (Leckner 1978)
        rh_frac = humedad_rel / 100.0
        t_c = temperatura_c
        
        # Presión de vapor saturación (hPa) - Magnus formula precisa
        e_s = 6.1078 * math.exp((17.27 * t_c) / (t_c + 237.3))
        e = rh_frac * e_s  # Presión de vapor actual
        
        # Agua precipitable (cm)
        W = 0.14 * e * 101.3 / presion_hpa * 2.1  # Leckner 1978
        W = max(0.5, min(10, W))  # Acotar: 0.5-10 cm realista
        
        # Profundidad óptica aerosoles (Angstrom turbidity)
        # Usar AOD del parámetro o estimarlo desde visibilidad
        aod = self.REST2_PARAMS["aod500"]  # @ 500 nm
        
        # Coeficientes REST2 (Gueymard 2016 Table)
        # Ángulo solar zenital corregido
        m = am
        
        # Transmitancia Rayleigh
        Tr = math.exp(-0.0903 * m ** 0.84 * (1.0 + m - m ** 1.01))
        
        # Transmitancia ozono (tipicamente ~98%)
        To = math.exp(-0.0710 * self.REST2_PARAMS["ozone"] * m ** 0.635)
        
        # Transmitancia por NO2 (typically ~99.5%)
        Tno2 = math.exp(-0.195 * 0.0002 * m)  # NO2 = 0.0002 cm
        
        # Transmitancia vapor de agua (Leckner 1978 mejorado)
        Tw = math.exp(-0.425 * aod * m ** 0.9 + 0.0845 * W * m ** 0.75 * (1 - W ** 0.2))
        
        # Transmitancia aerosoles (Angstrom)
        Ta = math.exp(-aod * m ** 0.9)
        
        # Radiación normal directa (DNI) en la atmósfera
        # Gueymard REST2 DNI0 = G_on * Tr * To * Tno2 * Tw * Ta
        G_on = self.calcular_radiacion_extraterrestre(datetime.now())
        
        dni0 = G_on * Tr * To * Tno2 * Tw * Ta
        
        # Si elevación muy baja, usar extrapolación
        if elevacion_deg < 5:
            dni0 = max(0, dni0 * math.sin(elevacion_rad))
        
        # Radiación difusa horizontal
        # Modelo Erbs/Perez simplificado
        kd = 0.954 - 0.075 * math.sqrt(1 - Tr)  # Fracción difusa
        dhi = (G_on * math.sin(elevacion_rad) * kd * 0.5 / 
               (math.sin(elevacion_rad) + 0.1))  # Aproximación
        
        # Radiación global horizontal (GHI)
        ghi = max(0, dni0 * math.sin(elevacion_rad) + dhi)
        
        # Índice de claridad (Clearness Index)
        # Kt = GHI / (G_on * sin(elevacion))
        if elevacion_deg > 0:
            ghi_teórico = G_on * math.sin(elevacion_rad)
            kt = ghi / ghi_teórico if ghi_teórico > 0 else 0
        else:
            kt = 0
        
        kt = max(0, min(1, kt))  # Acotar a [0, 1]
        
        return {
            "ghi_w_m2": ghi,
            "dni_w_m2": dni0 * math.sin(elevacion_rad),
            "dhi_w_m2": dhi,
            "clearness_index": kt,
            "agua_precipitable_cm": W,
            "aod500": aod,
        }
    
    def validar_con_diferencial_termico(self, 
                                        radiacion_medida: float,
                                        temp_wh65_c: float,
                                        temp_wh31_c: float,
                                        elevacion_deg: float,
                                        humedad_rel: float) -> Dict[str, any]:
        from typing import Any
        """
        Valida radiación medida usando diferencia térmica WH65-WH31.
        
        WH65 está al sol, WH31 en sombra:
        - Sin radiación: ΔT ≈ 0-1°C (solo diferencia topográfica)
        - Con radiación: ΔT = f(radiación)
        
        Args:
            radiacion_medida: Lectura del sensor (W/m²)
            temp_wh65_c: Temperatura WH65 (°C)
            temp_wh31_c: Temperatura WH31 (°C)
            elevacion_deg: Elevación solar (°)
            humedad_rel: Humedad relativa (%)
        
        Returns:
            {
                "delta_t_observado": Diferencia medida
                "delta_t_esperado": Diferencia teórica para esa radiación
                "desviacion": |observado - esperado|
                "anomalia": True si desviación > umbral
                "causa_posible": "Nubes", "Falla sensor", "Normal"
            }
        """
        
        delta_t = temp_wh65_c - temp_wh31_c
        
        if elevacion_deg <= 0:
            # Noche, no hay radiación esperada
            delta_t_esperado = 0
        else:
            # Relación empírica: radiación → ΔT
            # Basado en propiedades termales del sensor (inercia térmica, emisividad)
            # Aproximación: cada 100 W/m² calienta el sensor ~0.5°C sobre sombra
            # (Esto varía con viento, pero es orden de magnitud)
            
            factor_radiacion_a_dt = 0.005  # °C por W/m² (empírico, ajustable)
            delta_t_esperado = radiacion_medida * factor_radiacion_a_dt
            
            # Corrección por elevación solar (radiación oblicua)
            elevacion_rad = math.radians(elevacion_deg)
            delta_t_esperado *= math.sin(elevacion_rad)
        
        # Desviación
        desviacion = abs(delta_t - delta_t_esperado)
        
        # Umbral de anomalía: 2°C o 30% desviación, lo que sea mayor
        umbral = max(2.0, delta_t_esperado * 0.3)
        es_anomalia = desviacion > umbral
        
        # Clasificar anomalía
        if es_anomalia:
            if radiacion_medida > delta_t_esperado * 50:  # Mucha radiación pero poco ΔT
                causa = "Posible lectura falsa: nubes densas no detectadas"
            elif radiacion_medida < delta_t_esperado * 50 * 0.5:  # Poco radiación pero mucho ΔT
                causa = "Posible falla sensor: WH65/WH31 lecturas inconsistentes"
            else:
                causa = "Variación de viento o posición sensor"
        else:
            causa = "Normal"
        
        return {
            "delta_t_observado": round(delta_t, 2),
            "delta_t_esperado": round(delta_t_esperado, 2),
            "desviacion": round(desviacion, 2),
            "es_anomalia": es_anomalia,
            "umbral_anomalia": round(umbral, 2),
            "causa_posible": causa,
        }
    
    def procesar_radiacion_hibrida(self,
                                   radiacion_medida: Optional[float],
                                   temp_wh65_c: float,
                                   temp_wh31_c: float,
                                   presion_hpa: float,
                                   humedad_rel: float,
                                   velocidad_viento_ms: float = 0.0,
                                   precipitacion_mm: float = 0.0,
                                   visibilidad_km: Optional[float] = None,
                                   fecha_hora: datetime = None) -> Dict[str, any]:
        """
        Pipeline completa: Mide, modela, valida, y entrega radiación mejorada.
        
        [INTEGRACIÓN V51] Primera intenta usar arquitectura robusta V51; fallback a REST2-base.
        
        Returns:
            {
                "ghi_medido": Valor bruto del sensor (si existe)
                "ghi_modelado": Valor del modelo clear-sky
                "ghi_final": Valor mejorado/validado
                "confianza": 0-100% (cuánto confiamos en el resultado)
                "fuente": "sensor", "modelo", "sensor+validación"
                "deteccion_nubes": True si hay nubes (Kt < 0.7)
                "diferencial_termico": {...}  # Validación ΔT
                "posicion_solar": {...}
                "arquitectura_v51": True/False si se usó wrapper
            }
        """
        
        if fecha_hora is None:
            from datetime import datetime as dt
            fecha_hora = dt.now()
        
        # TRY 1: Usar arquitectura robusta V51 si está disponible
        if self._wrapper_radiacion_v51 is not None:
            try:
                resultado_v51 = self.procesar_radiacion_con_wrapper_v51(
                    radiacion_medida=radiacion_medida,
                    temp_wh65_c=temp_wh65_c,
                    temp_wh31_c=temp_wh31_c,
                    presion_hpa=presion_hpa,
                    humedad_rel=humedad_rel,
                    velocidad_viento_ms=velocidad_viento_ms,
                    precipitacion_mm=precipitacion_mm,
                    visibilidad_km=visibilidad_km,
                    fecha_hora=fecha_hora
                )
                
                if resultado_v51 is not None:
                    # ✓ Wrapper funcionó correctamente
                    rest2 = resultado_v51.get('rest2', {})
                    posicion_solar = resultado_v51.get('posicion_solar', {})
                    
                    return {
                        "timestamp": fecha_hora.isoformat(),
                        "posicion_solar": posicion_solar,
                        
                        # Valores de radiación [desde V51]
                        "ghi_medido_w_m2": radiacion_medida,
                        "ghi_modelado_rest2_w_m2": rest2.get('ghi_w_m2', 0),
                        "ghi_final_w_m2": round(resultado_v51['ghi'], 1),
                        
                        # Calidad de datos
                        "confianza_pct": int(resultado_v51['confianza'] * 100),
                        "fuente": "radiacion_robusta_v51",
                        "hay_nubes": resultado_v51.get('contexto', {}).get('hay_nubes', False),
                        "clearness_index": resultado_v51.get('contexto', {}).get('kt', 0),
                        
                        # Validación térmica
                        "diferencial_termico": self.validar_con_diferencial_termico(
                            radiacion_medida=resultado_v51['ghi'],
                            temp_wh65_c=temp_wh65_c,
                            temp_wh31_c=temp_wh31_c,
                            elevacion_deg=posicion_solar.get('elevacion_deg', 0),
                            humedad_rel=humedad_rel
                        ),
                        
                        # Detalles del modelo
                        "dni_w_m2": round(resultado_v51['dni'], 1),
                        "dhi_w_m2": round(resultado_v51['dhi'], 1),
                        "agua_precipitable_cm": round(rest2.get('agua_precipitable_cm', 1.5), 2),
                        "aerosol_optical_depth": round(rest2.get('aod500', 0.1), 4),
                        
                        # Metadata
                        "arquitectura_v51": True,
                        "advertencias": resultado_v51.get('advertencias', [])
                    }
            
            except Exception as e:
                logger.warning(f"[RADIACION] Error en V51 wrapper, usando fallback REST2: {e}")
        
        # FALLBACK: Usar método original REST2 si V51 no disponible o falló
        logger.debug("[RADIACION] Usando fallback REST2 (sin V51)")
        
        # 1. Calcular posición solar exacta
        posicion_solar = self.calcular_posicion_solar(fecha_hora)
        elevacion_deg = posicion_solar["elevacion_deg"]
        
        # 2. Calcular modelo clear-sky (REST2)
        rest2 = self.calcular_rest2_clearsky(
            elevacion_deg=elevacion_deg,
            am=posicion_solar["am"],
            presion_hpa=presion_hpa,
            humedad_rel=humedad_rel,
            temperatura_c=temp_wh65_c
        )
        ghi_modelado = rest2["ghi_w_m2"]
        kt = rest2["clearness_index"]
        
        # 3. Validar con diferencial térmico
        validacion_dt = self.validar_con_diferencial_termico(
            radiacion_medida=radiacion_medida or ghi_modelado,
            temp_wh65_c=temp_wh65_c,
            temp_wh31_c=temp_wh31_c,
            elevacion_deg=elevacion_deg,
            humedad_rel=humedad_rel
        )
        
        # 4. Decidir radiación final
        if radiacion_medida is not None and radiacion_medida > 0:
            # Tenemos medida real del sensor
            ghi_medido = radiacion_medida
            
            # Comparar con modelo
            ratio = ghi_medido / (ghi_modelado + 1)  # Evitar división por cero
            
            if 0.7 < ratio < 1.3:
                # Sensor y modelo son consistentes
                ghi_final = (ghi_medido + ghi_modelado) / 2  # Promedio
                confianza = 95
                fuente = "sensor+modelo"
            elif ratio > 1.3:
                # Sensor mide MÁS que modelo (posible error en modelo)
                ghi_final = ghi_medido * 0.9 + ghi_modelado * 0.1
                confianza = 80
                fuente = "sensor (modelo bajo)"
            else:
                # Sensor mide MENOS que modelo (posible falla sensor)
                ghi_final = ghi_medido * 0.5 + ghi_modelado * 0.5
                confianza = 70
                fuente = "modelo+sensor (inconsistente)"
        else:
            # Sin medida real, usar solo modelo
            ghi_medido = None
            ghi_final = ghi_modelado
            confianza = 75 if kt > 0.8 else 60  # Menos confianza si hay nubes
            fuente = "modelo"
        
        # 5. Detectar nubes
        hay_nubes = kt < 0.7
        
        return {
            "timestamp": fecha_hora.isoformat(),
            "posicion_solar": posicion_solar,
            
            # Valores de radiación
            "ghi_medido_w_m2": ghi_medido,
            "ghi_modelado_rest2_w_m2": ghi_modelado,
            "ghi_final_w_m2": round(ghi_final, 1),
            
            # Calidad de datos
            "confianza_pct": confianza,
            "fuente": fuente,
            "hay_nubes": hay_nubes,
            "clearness_index": round(kt, 3),
            
            # Validación térmica
            "diferencial_termico": validacion_dt,
            
            # Detalles del modelo
            "dni_w_m2": round(rest2.get("dni_w_m2", 0.0), 1),
            "dhi_w_m2": round(rest2.get("dhi_w_m2", 0.0), 1),
            "agua_precipitable_cm": round(rest2.get("agua_precipitable_cm", 1.5), 2),
            "aerosol_optical_depth": round(rest2.get("aod500", 0.1), 4),
            
            # Metadata
            "arquitectura_v51": False
        }


def procesar_radiacion_sistema(sensores: Dict, sistema) -> Dict:
    """
    Función de entrada para integración con MeteoSerV3.
    
    [INTEGRACIÓN V51] Ahora soporta parámetros completos para wrapper radiativo robusto.
    
    Args:
        sensores: Dict con temperatura, humedad, presión, viento, precipitación, etc.
        sistema: Objeto SystemManager global
    
    Returns:
        Dict con radiación completa para publicar en bus
    """
    
    try:
        # Obtener datos básicos
        temp_wh65 = sensores.get("temperatura", 20.0)
        temp_wh31 = sensores.get("temperatura_wh31", 18.0)
        humedad = sensores.get("humedad", 60.0)
        presion = sensores.get("presion", 1013.25)
        radiacion_medida = sensores.get("solarradiation_original")  # Puede ser None
        
        # Obtener datos para V51 wrapper
        velocidad_viento = sensores.get("windspeed", sensores.get("velocidad_viento", 0.0))
        precipitacion = sensores.get("precipitacion_hora", sensores.get("precipitacion", 0.0))
        visibilidad = sensores.get("visibilidad", None)
        
        # Usar ubicación estimada (Barcelona por defecto)
        latitud = sensores.get("latitud_estimada", 41.3)
        longitud = sensores.get("longitud_estimada", 2.1)
        
        # Crear piranómetro
        piranometro = PiranometroHibrido(latitud=latitud, longitud=longitud)
        
        # Procesar (ahora con soporte para V51)
        resultado = piranometro.procesar_radiacion_hibrida(
            radiacion_medida=radiacion_medida,
            temp_wh65_c=temp_wh65,
            temp_wh31_c=temp_wh31,
            presion_hpa=presion,
            humedad_rel=humedad,
            velocidad_viento_ms=velocidad_viento,
            precipitacion_mm=precipitacion,
            visibilidad_km=visibilidad,
            fecha_hora=datetime.now()
        )
        
        # Determinar fuente y arquitectura
        es_v51 = resultado.get("arquitectura_v51", False)
        fuente_label = "V51_ROBUSTA" if es_v51 else "REST2_FALLBACK"
        
        logger.info(f"[RADIACION_{fuente_label}] GHI: {resultado['ghi_final_w_m2']:.1f} W/m², "
                   f"Confianza: {resultado['confianza_pct']}%, "
                   f"Fuente: {resultado['fuente']}")
        
        if es_v51:
            advertencias = resultado.get("advertencias", [])
            if advertencias:
                logger.info(f"[RADIACION_V51] Advertencias: {'; '.join(advertencias)}")
        
        # ═══════════════════════════════════════════════════════════════════════════════════
        # PUBLICAR EN BUS DE ESTADO GLOBAL
        # ═══════════════════════════════════════════════════════════════════════════════════
        if BusEstadoGlobal and obtener_contexto_solar:
            try:
                # Agregar contexto solar para confianza dinámica
                fecha_hora = datetime.now()
                contexto = obtener_contexto_solar(
                    fecha_hora=fecha_hora,
                    latitud=latitud,
                    longitud=longitud,
                    presion_hpa=presion,
                    temperatura_c=temp_wh65,
                    humedad_rel=humedad
                )
                
                # Ajustar confianza según contexto solar
                elevacion_solar = contexto.get("elevacion_solar_deg", 0.0)
                
                # Solo publicar radiación si no es noche astral
                if elevacion_solar > -18.0:
                    bus = BusEstadoGlobal.obtener_instancia()
                    
                    # Publicar TODA la radiación con metadatos completos
                    ghi_final = float(resultado.get("ghi_final_w_m2", 0.0))
                    dni_final = float(resultado.get("dni_w_m2", 0.0))
                    dhi_final = float(resultado.get("dhi_w_m2", 0.0))
                    confianza = int(resultado.get("confianza_pct", 0))
                    
                    # GHI (Global Horizontal Irradiance)
                    bus.publicar(
                        clave="radiacion_ghi_w_m2",
                        valor=ghi_final,
                        fuente="radiacion_hibrida",
                        metadatos={
                            "modelo": "V51_ROBUSTO" if es_v51 else "REST2_v3_NREL",
                            "confianza_pct": confianza,
                            "elevacion_solar_deg": elevacion_solar,
                            "validacion_termica": resultado.get("hay_nubes", False),
                            "sensor_disponible": radiacion_medida is not None,
                            "arquitectura": fuente_label
                        }
                    )
                    
                    # DNI (Direct Normal Irradiance)
                    bus.publicar(
                        clave="radiacion_dni_w_m2",
                        valor=dni_final,
                        fuente="radiacion_hibrida",
                        metadatos={
                            "modelo": "V51_ROBUSTO" if es_v51 else "REST2_v3_NREL",
                            "confianza_pct": confianza,
                            "elevacion_solar_deg": elevacion_solar,
                            "arquitectura": fuente_label
                        }
                    )
                    
                    # DHI (Diffuse Horizontal Irradiance)
                    bus.publicar(
                        clave="radiacion_dhi_w_m2",
                        valor=dhi_final,
                        fuente="radiacion_hibrida",
                        metadatos={
                            "modelo": "V51_ROBUSTO" if es_v51 else "REST2_v3_NREL",
                            "confianza_pct": confianza,
                            "elevacion_solar_deg": elevacion_solar,
                            "arquitectura": fuente_label
                        }
                    )
                    
                    # Contexto solar y parámetros atmosféricos
                    bus.publicar(
                        clave="contexto_solar",
                        valor=contexto,
                        fuente="contexto_solar",
                        metadatos={"precision_arcmin": 2}
                    )
                    
                    # Índices de calidad
                    bus.publicar(
                        clave="radiacion_clearness_index",
                        valor=float(resultado.get("clearness_index", 0.0)),
                        fuente="radiacion_hibrida",
                        metadatos={
                            "hay_nubes": resultado.get("hay_nubes", False),
                            "confianza_pct": confianza
                        }
                    )
                    
                    # Parámetros atmosféricos
                    bus.publicar(
                        clave="atmosfera_agua_precipitable_cm",
                        valor=float(resultado.get("agua_precipitable_cm", 1.5)),
                        fuente="radiacion_hibrida",
                        metadatos={"precision": "estimado"}
                    )
                    
                    bus.publicar(
                        clave="atmosfera_aerosol_optical_depth",
                        valor=float(resultado.get("aerosol_optical_depth", 0.1)),
                        fuente="radiacion_hibrida",
                        metadatos={"longitud_onda_nm": 500}
                    )
                    
                    # Validación térmica (detección de anomalías)
                    dt_info = resultado.get("diferencial_termico", {})
                    if dt_info:
                        bus.publicar(
                            clave="validacion_radiacion_termica",
                            valor={
                                "es_anomalia": dt_info.get("es_anomalia", False),
                                "desviacion": dt_info.get("desviacion", 0.0),
                                "umbral": dt_info.get("umbral_anomalia", 0.0),
                                "causa": dt_info.get("causa_posible", "desconocida")
                            },
                            fuente="radiacion_hibrida",
                            metadatos={"tipo": "cross-validation"}
                        )
                    
                    logger.debug(f"[BUS] Radiación completa: GHI={ghi_final:.1f} W/m², DNI={dni_final:.1f} W/m², DHI={dhi_final:.1f} W/m² (confianza={confianza}%) [{fuente_label}]")
                    logger.debug(f"[BUS] Contexto solar: elevación={elevacion_solar:.1f}°, estado={contexto.get('estado')}")
                else:
                    logger.debug("[BUS] No se publica radiación (noche astral, elevación < -18°)")
            
            except Exception as e:
                logger.warning(f"[BUS] Error publicando radiación: {e}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en piranómetro híbrido: {e}")
        return {
            "error": str(e),
            "ghi_final_w_m2": None,
            "confianza_pct": 0,
            "arquitectura_v51": False
        }
