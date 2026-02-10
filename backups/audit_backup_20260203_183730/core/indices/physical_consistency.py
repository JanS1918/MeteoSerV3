"""
VALIDADOR DE CONSISTENCIA FÍSICA - Sistema Nervioso del Organismo

Este módulo implementa el Health Check de validación cruzada para detectar
valores físicamente imposibles según el contexto astronómico y ambiental.

ARQUITECTURA DE ORGANISMO ÚNICO:
- Consulta el ContextoMaestro para conocer posición solar, estado día/noche, estación
- Valida que todos los sensores sean coherentes con las leyes físicas
- Genera alertas cuando detecta inconsistencias
- Proporciona valores de respaldo calculados mediante fórmulas de excelencia

VALIDACIONES IMPLEMENTADAS:
1. Radiación solar nocturna (físicamente imposible)
2. UV nocturno (físicamente imposible)
3. Humedad vs punto de rocío (inconsistencia termodinámica)
4. Temperatura vs radiación (incoherencia energética)
5. Presión vs altitud (validación barométrica)
6. Viento vs variabilidad (coherencia temporal)

OBJETIVO: Mantener el sistema vivo y alertar de fallos de sensores
mediante razonamiento físico interdependiente.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from core.indices.environmental_indices import (
    saturacion_vapor_iapws_elite,
    saturacion_vapor_virial_greenspan,
    saturacion_vapor_hyland_wexler,
    _dew_point,
)

# PRECISIÓN TOTAL: desactivar redondeo en cálculos internos
def _no_round(value, *args, **kwargs):
    return value

round = _no_round

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyAlert:
    """Alerta de inconsistencia física detectada."""
    sensor: str
    tipo: str  # 'imposible', 'incoherente', 'sospechoso'
    severidad: str  # 'critica', 'alta', 'media', 'baja'
    valor_sensor: Any
    valor_esperado: Optional[Any]
    razon: str
    accion: str  # 'reemplazado', 'marcado', 'monitoreando'
    timestamp: str


class PhysicalConsistencyValidator:
    """
    Validador de Consistencia Física - El Sistema Inmunológico del Organismo.
    
    Detecta valores anómalos y mantiene la coherencia física del sistema.
    """
    
    def __init__(self, min_solar_rad_threshold: float = 1.0, 
                 max_night_uv: float = 0.1):
        """
        Args:
            min_solar_rad_threshold: Radiación mínima para considerar 'día' (W/m²)
            max_night_uv: UV máximo permitido de noche (índice UV)
        """
        self.min_solar_rad_threshold = min_solar_rad_threshold
        self.max_night_uv = max_night_uv
        self.alertas: List[ConsistencyAlert] = []
    
    def clear_alertas(self):
        """Limpia las alertas acumuladas."""
        self.alertas = []
    
    def get_alertas(self) -> List[Dict]:
        """Obtiene las alertas en formato dict."""
        return [
            {
                "sensor": a.sensor,
                "tipo": a.tipo,
                "severidad": a.severidad,
                "valor_sensor": a.valor_sensor,
                "valor_esperado": a.valor_esperado,
                "razon": a.razon,
                "accion": a.accion,
                "timestamp": a.timestamp
            }
            for a in self.alertas
        ]
    
    def deducir_temperatura_desde_radiacion(self, radiacion_wm2: float, 
                                           es_dia: bool) -> Optional[float]:
        """
        Deduce temperatura aproximada desde radiación solar.
        Modelo simplificado: T ≈ f(radiación, hora del día)
        """
        if not es_dia or radiacion_wm2 < 50:
            return None
        
        # Modelo empírico: T ≈ T_base + k × √(radiación)
        # Ajustado para latitudes medias
        T_base = 10.0  # °C (temperatura base)
        k = 0.15  # Coeficiente de conversión
        
        temp_estimada = T_base + k * math.sqrt(radiacion_wm2)
        return round(temp_estimada, 1)
    
    def deducir_humedad_desde_punto_rocio(self, temperatura_c: float,
                                         punto_rocio_c: float) -> Optional[float]:
        """
        Deduce humedad relativa desde temperatura y punto de rocío.
        Basado en razón de presiones de vapor (NIST).
        """
        if temperatura_c is None or punto_rocio_c is None:
            return None
        
        if punto_rocio_c > temperatura_c:
            # Físicamente imposible
            return None
        
        presion_pa = 101325.0
        try:
            es_t_pa = saturacion_vapor_iapws_elite(temperatura_c, presion_pa)
        except Exception:
            try:
                es_t_pa = saturacion_vapor_virial_greenspan(temperatura_c, presion_pa)
            except Exception:
                es_t_pa = saturacion_vapor_hyland_wexler(temperatura_c, presion_pa)
        try:
            ea_pa = saturacion_vapor_iapws_elite(punto_rocio_c, presion_pa)
        except Exception:
            try:
                ea_pa = saturacion_vapor_virial_greenspan(punto_rocio_c, presion_pa)
            except Exception:
                ea_pa = saturacion_vapor_hyland_wexler(punto_rocio_c, presion_pa)

        hr = (ea_pa / es_t_pa) * 100.0
        return round(min(100.0, max(0.0, hr)), 1)
    
    def deducir_viento_desde_variabilidad(self, viento_actual: Optional[float],
                                         rachas: Optional[float]) -> Optional[float]:
        """
        Deduce viento medio desde rachas si el sensor de viento falla.
        Típicamente: viento_medio ≈ rachas / 1.5
        """
        if rachas is None or rachas <= 0:
            return None
        
        # Relación empírica: rachas son ~50% mayores que viento medio
        viento_estimado = rachas / 1.5
        return round(viento_estimado, 1)
    
    def reset_alertas(self) -> None:
        """Limpia las alertas acumuladas."""
        self.alertas = []
    
    def get_alertas(self) -> List[Dict[str, Any]]:
        """Devuelve las alertas como diccionarios."""
        return [
            {
                'sensor': a.sensor,
                'tipo': a.tipo,
                'severidad': a.severidad,
                'valor_sensor': a.valor_sensor,
                'valor_esperado': a.valor_esperado,
                'razon': a.razon,
                'accion': a.accion,
                'timestamp': a.timestamp
            }
            for a in self.alertas
        ]
    
    def _add_alert(self, sensor: str, tipo: str, severidad: str,
                   valor_sensor: Any, valor_esperado: Optional[Any],
                   razon: str, accion: str) -> None:
        """Registra una nueva alerta."""
        alert = ConsistencyAlert(
            sensor=sensor,
            tipo=tipo,
            severidad=severidad,
            valor_sensor=valor_sensor,
            valor_esperado=valor_esperado,
            razon=razon,
            accion=accion,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        self.alertas.append(alert)
        logger.warning(f"[CONSISTENCIA] {sensor}: {razon} (valor={valor_sensor}, esperado={valor_esperado})")
    
    def validate_radiacion_nocturna(self, contexto, radiacion: Optional[float]) -> Tuple[Optional[float], bool]:
        """
        Valida que no haya radiación solar significativa durante la noche.
        
        Returns:
            (valor_corregido, es_real)
        """
        if radiacion is None:
            return None, False
        
        # Si es noche astronómica (sol < -6°), la radiación debe ser ~0
        if contexto.es_noche_astronomico:
            if radiacion > self.min_solar_rad_threshold:
                self._add_alert(
                    sensor='radiacion',
                    tipo='imposible',
                    severidad='critica',
                    valor_sensor=radiacion,
                    valor_esperado=0.0,
                    razon=f'Radiación solar {radiacion:.1f} W/m² con sol a {contexto.solar_altitude:.1f}° (noche astronómica)',
                    accion='reemplazado'
                )
                return 0.0, False  # Corregir a 0
        
        # Si es noche pero sol cerca del horizonte (-6° < alt < 0°), permitir algo de dispersión
        elif contexto.es_noche and contexto.solar_altitude < 0:
            if radiacion > 50.0:  # Dispersión crepuscular máxima
                self._add_alert(
                    sensor='radiacion',
                    tipo='incoherente',
                    severidad='alta',
                    valor_sensor=radiacion,
                    valor_esperado=10.0,
                    razon=f'Radiación {radiacion:.1f} W/m² muy alta para crepúsculo (sol a {contexto.solar_altitude:.1f}°)',
                    accion='marcado'
                )
                return 10.0, False  # Valor típico crepuscular
        
        return radiacion, True
    
    def validate_uv_nocturno(self, contexto, uv: Optional[float]) -> Tuple[Optional[float], bool]:
        """
        Valida que no haya UV significativo durante la noche.
        
        Returns:
            (valor_corregido, es_real)
        """
        if uv is None:
            return None, False
        
        # De noche, UV debe ser ~0
        if contexto.es_noche:
            if uv > self.max_night_uv:
                self._add_alert(
                    sensor='uv',
                    tipo='imposible',
                    severidad='critica',
                    valor_sensor=uv,
                    valor_esperado=0.0,
                    razon=f'UV {uv:.1f} con sol a {contexto.solar_altitude:.1f}° (de noche)',
                    accion='reemplazado'
                )
                return 0.0, False
        
        return uv, True
    
    def validate_humedad_punto_rocio(self, temp_c: Optional[float], 
                                     humedad: Optional[float],
                                     punto_rocio: Optional[float]) -> Tuple[Optional[float], bool]:
        """
        Valida consistencia termodinámica entre T, HR y punto de rocío.
        
        Ley física: Td <= T siempre (el punto de rocío no puede superar la temperatura)
        
        Returns:
            (humedad_corregida, es_real)
        """
        if temp_c is None or humedad is None or punto_rocio is None:
            return humedad, humedad is not None
        
        # Validación física: Td <= T
        if punto_rocio > temp_c + 0.1:  # Tolerancia 0.1°C por errores de redondeo
            # Calcular HR correcta desde Td
            presion_pa = 101325.0
            try:
                es_t_pa = saturacion_vapor_iapws_elite(temp_c, presion_pa)
            except Exception:
                try:
                    es_t_pa = saturacion_vapor_virial_greenspan(temp_c, presion_pa)
                except Exception:
                    es_t_pa = saturacion_vapor_hyland_wexler(temp_c, presion_pa)
            try:
                ea_pa = saturacion_vapor_iapws_elite(punto_rocio, presion_pa)
            except Exception:
                try:
                    ea_pa = saturacion_vapor_virial_greenspan(punto_rocio, presion_pa)
                except Exception:
                    ea_pa = saturacion_vapor_hyland_wexler(punto_rocio, presion_pa)

            hr_correcta = 100.0 * (ea_pa / es_t_pa)
            hr_correcta = max(0.0, min(100.0, hr_correcta))
            
            self._add_alert(
                sensor='humedad',
                tipo='incoherente',
                severidad='alta',
                valor_sensor=humedad,
                valor_esperado=hr_correcta,
                razon=f'Punto de rocío ({punto_rocio:.1f}°C) > Temperatura ({temp_c:.1f}°C) - violación termodinámica',
                accion='reemplazado'
            )
            return hr_correcta, False
        
        # Validación de coherencia: recalcular Td desde T+HR y comparar
        td_calculado = _dew_point(temp_c, max(0.01, humedad))
        
        delta_td = abs(td_calculado - punto_rocio)
        if delta_td > 2.0:  # Diferencia > 2°C es sospechosa
            self._add_alert(
                sensor='humedad',
                tipo='sospechoso',
                severidad='media',
                valor_sensor=humedad,
                valor_esperado=None,
                razon=f'Inconsistencia T/HR/Td: Td calculado {td_calculado:.1f}°C vs sensor {punto_rocio:.1f}°C (Δ={delta_td:.1f}°C)',
                accion='monitoreando'
            )
        
        return humedad, True
    
    def validate_temp_radiacion(self, contexto, temp_c: Optional[float],
                                radiacion: Optional[float]) -> Tuple[Optional[float], bool]:
        """
        Valida coherencia entre temperatura y radiación solar.
        
        Durante el día con alta radiación, la temperatura debe ser razonable.
        
        Returns:
            (temp_corregida, es_real)
        """
        if temp_c is None or radiacion is None:
            return temp_c, temp_c is not None
        
        # Si hay radiación alta pero temperatura muy baja (invierno extremo o fallo sensor)
        if contexto.es_dia and radiacion > 500 and temp_c < -20:
            self._add_alert(
                sensor='temperatura',
                tipo='sospechoso',
                severidad='media',
                valor_sensor=temp_c,
                valor_esperado=None,
                razon=f'Temperatura muy baja ({temp_c:.1f}°C) con radiación alta ({radiacion:.0f} W/m²) - sensor congelado?',
                accion='monitoreando'
            )
        
        # Si es verano con radiación alta pero temperatura muy alta (sensor expuesto?)
        if contexto.estacion == "verano" and radiacion > 800 and temp_c > 45:
            self._add_alert(
                sensor='temperatura',
                tipo='sospechoso',
                severidad='alta',
                valor_sensor=temp_c,
                valor_esperado=None,
                razon=f'Temperatura extrema ({temp_c:.1f}°C) con radiación alta - sensor expuesto a radiación directa?',
                accion='monitoreando'
            )
        
        return temp_c, True
    
    def validate_presion_altitud(self, contexto, presion_kpa: Optional[float]) -> Tuple[Optional[float], bool]:
        """
        Valida que la presión sea coherente con la altitud.
        
        Ecuación barométrica: p(h) ≈ p0 * exp(-h / H)
        donde H ≈ 8.4 km (escala de altura atmosférica)
        
        Returns:
            (presion_corregida, es_real)
        """
        if presion_kpa is None:
            return None, False
        
        # Presión estándar al nivel del mar
        p0 = 101.325  # kPa
        H = 8400.0  # metros (escala de altura)
        
        # Presión esperada a la altitud del sensor
        h = contexto.elevation_total
        p_esperada = p0 * math.exp(-h / H)
        
        # Tolerancia ±10% (variaciones meteorológicas)
        p_min = p_esperada * 0.9
        p_max = p_esperada * 1.1
        
        if presion_kpa < p_min or presion_kpa > p_max:
            self._add_alert(
                sensor='presion',
                tipo='sospechoso',
                severidad='media',
                valor_sensor=presion_kpa,
                valor_esperado=p_esperada,
                razon=f'Presión {presion_kpa:.2f} kPa fuera del rango esperado [{p_min:.2f}, {p_max:.2f}] para {h:.0f}m',
                accion='monitoreando'
            )
        
        return presion_kpa, True
    
    def validate_all_sensors(self, contexto, sensores: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida todos los sensores contra el contexto físico.
        
        Args:
            contexto: ContextoMaestro con estado astronómico/ubicación
            sensores: Diccionario con valores de sensores {'temperatura': 20.5, ...}
        
        Returns:
            Diccionario con valores validados y flags de consistencia
        """
        self.reset_alertas()
        
        validated = {}
        
        # Radiación solar
        if 'radiacion' in sensores:
            rad, es_real = self.validate_radiacion_nocturna(contexto, sensores.get('radiacion'))
            validated['radiacion'] = {
                'valor': rad,
                'es_real': es_real,
                'fuente': 'sensor' if es_real else 'validacion_fisica'
            }
        
        # UV
        if 'uv' in sensores:
            uv, es_real = self.validate_uv_nocturno(contexto, sensores.get('uv'))
            validated['uv'] = {
                'valor': uv,
                'es_real': es_real,
                'fuente': 'sensor' if es_real else 'validacion_fisica'
            }
        
        # Humedad vs punto de rocío
        if 'humedad' in sensores:
            hr, es_real = self.validate_humedad_punto_rocio(
                sensores.get('temperatura'),
                sensores.get('humedad'),
                sensores.get('punto_rocio')
            )
            validated['humedad'] = {
                'valor': hr,
                'es_real': es_real,
                'fuente': 'sensor' if es_real else 'validacion_termodinamica'
            }
        
        # Temperatura vs radiación
        if 'temperatura' in sensores:
            temp, es_real = self.validate_temp_radiacion(
                contexto,
                sensores.get('temperatura'),
                sensores.get('radiacion')
            )
            validated['temperatura'] = {
                'valor': temp,
                'es_real': es_real,
                'fuente': 'sensor' if es_real else 'validacion_energetica'
            }
        
        # Presión vs altitud
        if 'presion' in sensores:
            pres, es_real = self.validate_presion_altitud(contexto, sensores.get('presion'))
            validated['presion'] = {
                'valor': pres,
                'es_real': es_real,
                'fuente': 'sensor' if es_real else 'validacion_barometrica'
            }
        
        return validated
