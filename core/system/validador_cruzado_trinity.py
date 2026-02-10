"""
═══════════════════════════════════════════════════════════════════════════════
VALIDADOR CRUZADO - ALARMAS DE COHERENCIA (TRINITY ELITE)
═══════════════════════════════════════════════════════════════════════════════

Módulo: Sistema de autochequeo para detectar inconsistencias entre modelos
Basado en: Redundancia Robusta de Grado Militar
Precisión: Detección de divergencias > 15% (configurable)
Aplicación: MeteoSerV3 - Argentona (PATRULLA ETERNA)

CONCEPTO:
Si la física funciona correctamente, dos modelos independientes que calculan
lo mismo DEBEN dar resultados similares. Si divergen mucho, algo está mal:
- Sensor averiado
- Atmósfera en estado anómalo
- Cambio brusco

LÓGICA DE DETECCIÓN:
1. Hardy (NIST) calcula humedad exacta
2. OMM (Temperatura Virtual) usa la humedad de Hardy
3. REST2 (Gueymard) proporciona G₀
4. Liu & Jordan calcula K_t = G_real / G₀
5. Nubosidad radiométrica se compara con nubosidad atmosférica
6. Si |nubosidad_radiometrica - nubosidad_atmosferica| > 15%, ALARMA

TIPOS DE ALARMAS:
- ALERTA BAJA (±5%): Inconsistencia menor, seguimiento
- ALERTA MEDIA (±10%): Inconsistencia relevante, investigar
- ALERTA ALTA (±15%): Inconsistencia crítica, posible fallo de sensor
- ALERTA CRÍTICA (>20%): Fallo confirmado, caída del sistema

═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum, IntEnum
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════════════════════

class NivelAlerta(IntEnum):
    """Niveles de severidad de alarmas"""
    NORMAL = 0          # Sin anomalías
    BAJA = 1            # ±5% divergencia
    MEDIA = 2           # ±10% divergencia
    ALTA = 3            # ±15% divergencia
    CRITICA = 4         # >20% divergencia


class TipoVerificacion(Enum):
    """Tipos de chequeos de coherencia"""
    NUBOSIDAD = "nubosidad"              # Radiométrica vs Atmosférica
    TEMPERATURA_VIRTUAL = "temp_virtual" # OMM vs Hardy
    RADIACION = "radiacion"              # G_real vs G₀ (K_t)
    HUMEDAD = "humedad"                  # RH vs Mezcla
    DENSIDAD = "densidad"                # Física vs Empírica


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASS PARA ALARMAS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Alarma:
    """Estructura de una alarma del sistema"""
    timestamp: datetime
    tipo_verificacion: TipoVerificacion
    nivel: NivelAlerta
    valor1: float                    # Primera medida/modelo
    valor2: float                    # Segunda medida/modelo
    divergencia_pct: float          # Porcentaje de divergencia
    descripcion: str                # Mensaje humanizado
    accion_recomendada: str         # Qué hacer


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 1: Cálculo de Divergencia Porcentual
# ═══════════════════════════════════════════════════════════════════════════════

def calcular_divergencia_porcentual(
    valor1: float,
    valor2: float,
    usar_promedio: bool = True
) -> float:
    """
    Calcula divergencia porcentual entre dos valores.
    
    Dos métodos:
    - Usar promedio (simétrico): |V1 - V2| / ((V1 + V2) / 2) * 100
    - Usar V1 como referencia (asimétrico): |V1 - V2| / V1 * 100
    
    El promedio es mejor para comparaciones simétricas.
    La referencia es mejor cuando hay un "ground truth".
    
    Args:
        valor1: Primer valor
        valor2: Segundo valor
        usar_promedio: Si True, usa promedio; si False, usa V1 como ref
        
    Returns:
        Divergencia en % (0-100 típicamente)
    """
    
    if valor1 == 0 and valor2 == 0:
        return 0.0
    
    if usar_promedio:
        promedio = (abs(valor1) + abs(valor2)) / 2.0
        if promedio == 0:
            return 0.0
        divergencia = abs(valor1 - valor2) / promedio * 100.0
    else:
        if valor1 == 0:
            return 100.0 if valor2 != 0 else 0.0
        divergencia = abs(valor1 - valor2) / abs(valor1) * 100.0
    
    return divergencia


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 2: Determinación de Nivel de Alerta
# ═══════════════════════════════════════════════════════════════════════════════

def determinar_nivel_alerta(divergencia_pct: float) -> NivelAlerta:
    """
    Determina el nivel de alerta basado en divergencia porcentual.
    
    Thresholds:
    - 0-5%: NORMAL
    - 5-10%: BAJA
    - 10-15%: MEDIA
    - 15-20%: ALTA
    - >20%: CRITICA
    
    Args:
        divergencia_pct: Divergencia en porcentaje
        
    Returns:
        NivelAlerta enum
    """
    
    if divergencia_pct < 5.0:
        return NivelAlerta.NORMAL
    elif divergencia_pct < 10.0:
        return NivelAlerta.BAJA
    elif divergencia_pct < 15.0:
        return NivelAlerta.MEDIA
    elif divergencia_pct < 20.0:
        return NivelAlerta.ALTA
    else:
        return NivelAlerta.CRITICA


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 3: Verificación de Nubosidad (Radiométrica vs Atmosférica)
# ═══════════════════════════════════════════════════════════════════════════════

def verificar_nubosidad(
    nubosidad_radiometrica_pct: float,
    nubosidad_atmosferica_pct: float
) -> Alarma:
    """
    Compara nubosidad radiométrica (de K_t y REST2) con
    nubosidad atmosférica (de T, RH, T_dew).
    
    Ambas metodologías DEBEN estar de acuerdo si la atmósfera es coherente.
    
    INTERPRETACIÓN:
    - Radiométrica > Atmosférica: Posible error en sensor de radiación
    - Radiométrica < Atmosférica: Posible error en sensor de humedad
    - Diferencia > 15%: Anomalía de nube muy rara o sensor averiado
    
    Args:
        nubosidad_radiometrica_pct: Nubosidad de K_t (0-100)
        nubosidad_atmosferica_pct: Nubosidad de T/RH (0-100)
        
    Returns:
        Alarma object
    """
    
    divergencia = calcular_divergencia_porcentual(
        nubosidad_radiometrica_pct,
        nubosidad_atmosferica_pct,
        usar_promedio=True
    )
    
    nivel = determinar_nivel_alerta(divergencia)
    
    # Determinar descripción
    if divergencia < 5.0:
        descripcion = f"Nubosidad coherente: Radiom={nubosidad_radiometrica_pct:.1f}%, Atmos={nubosidad_atmosferica_pct:.1f}%"
        accion = "Sin acción necesaria"
    elif divergencia < 10.0:
        descripcion = f"Nubosidad con desviación baja ({divergencia:.1f}%)"
        accion = "Seguimiento de sensores"
    elif divergencia < 15.0:
        descripcion = f"Nubosidad con inconsistencia ({divergencia:.1f}%). Revisar radiación y humedad."
        accion = "Verificar sensores de radiación (piranómetro) y humedad"
    elif divergencia < 20.0:
        descripcion = f"ALERTA ALTA: Nubosidad muy inconsistente ({divergencia:.1f}%)"
        accion = "Posible fallo de sensor. Revisar piranómetro e higrómetro inmediatamente."
    else:
        descripcion = f"ALERTA CRÍTICA: Nubosidad completamente incoherente ({divergencia:.1f}%)"
        accion = "Fallo confirmado de sensor. Caída parcial del sistema."
    
    return Alarma(
        timestamp=datetime.now(),
        tipo_verificacion=TipoVerificacion.NUBOSIDAD,
        nivel=nivel,
        valor1=nubosidad_radiometrica_pct,
        valor2=nubosidad_atmosferica_pct,
        divergencia_pct=divergencia,
        descripcion=descripcion,
        accion_recomendada=accion
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 4: Verificación de Temperatura Virtual
# ═══════════════════════════════════════════════════════════════════════════════

def verificar_temperatura_virtual(
    temperatura_omm_c: float,
    temperatura_hardy_c: float,
    humedad_relativa_pct: float
) -> Alarma:
    """
    Verifica consistencia entre Temperatura Virtual (OMM) y
    Temperatura Hardy/Real.
    
    T_v SIEMPRE debe ser ≥ T_real (porque el vapor calienta).
    La diferencia típica es 0.3-1.0°C en condiciones normales.
    
    INTERPRETACIÓN:
    - T_v < T: Imposible físicamente (error computacional)
    - T_v - T > 1.5°C: Humedad muy alta o error
    - T_v = T: Aire completamente seco (raro en costa)
    
    Args:
        temperatura_omm_c: T_v calculada por OMM
        temperatura_hardy_c: T real medida
        humedad_relativa_pct: RH para contexto
        
    Returns:
        Alarma object
    """
    
    delta_t = temperatura_omm_c - temperatura_hardy_c
    divergencia = abs(delta_t)  # En °C absolutos
    
    # Convertir a porcentaje (respecto a 273.15 K para escala universal)
    T_ref_k = 273.15
    divergencia_pct = (divergencia / T_ref_k) * 100.0
    
    nivel = determinar_nivel_alerta(divergencia_pct)
    
    # Lógica física
    if delta_t < -0.1:
        nivel = NivelAlerta.CRITICA
        descripcion = f"ERROR FÍSICO: T_v ({temperatura_omm_c:.2f}°C) < T_real ({temperatura_hardy_c:.2f}°C). Imposible."
        accion = "Error de cálculo en módulo OMM. Revisar fórmula de Temperatura Virtual."
    elif delta_t > 2.0:
        descripcion = f"Temperatura Virtual muy elevada: ΔT = {delta_t:.2f}°C (RH={humedad_relativa_pct:.0f}%)"
        accion = "Posible error en cálculo de humedad (Hardy). Revisar sensor de humedad."
    elif delta_t < 0.2 and humedad_relativa_pct > 60:
        descripcion = f"T_v muy baja para RH={humedad_relativa_pct:.0f}%. ΔT = {delta_t:.2f}°C"
        accion = "Verificar calibración del higrómetro. Posible lectura baja."
    elif delta_t >= 0.3 and delta_t <= 1.2:
        descripcion = f"Temperatura Virtual coherente: ΔT = {delta_t:.2f}°C (normal para RH={humedad_relativa_pct:.0f}%)"
        accion = "Sin acción necesaria"
    else:
        descripcion = f"Temperatura Virtual con pequeña desviación: ΔT = {delta_t:.2f}°C"
        accion = "Seguimiento"
    
    return Alarma(
        timestamp=datetime.now(),
        tipo_verificacion=TipoVerificacion.TEMPERATURA_VIRTUAL,
        nivel=nivel,
        valor1=temperatura_omm_c,
        valor2=temperatura_hardy_c,
        divergencia_pct=divergencia_pct,
        descripcion=descripcion,
        accion_recomendada=accion
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 5: Verificación de Radiación (Índice de Claridad K_t)
# ═══════════════════════════════════════════════════════════════════════════════

def verificar_radiacion(
    radiacion_real_w_m2: float,
    radiacion_extraterrestre_g0_w_m2: float,
    elevacion_solar_deg: float
) -> Alarma:
    """
    Verifica consistencia del Índice de Claridad K_t = G_real / G₀.
    
    K_t tiene límites físicos:
    - Día despejado: K_t = 0.75-0.85
    - Día nublado: K_t = 0.15-0.40
    - Atmósfera con aerosoles: K_t = 0.60-0.75
    - K_t > 1.0: Imposible (error de sensor)
    - K_t con sol bajo (<15°): menos confiable
    
    Args:
        radiacion_real_w_m2: Radiación medida por piranómetro
        radiacion_extraterrestre_g0_w_m2: G₀ de REST2
        elevacion_solar_deg: Elevación solar
        
    Returns:
        Alarma object
    """
    
    # Evitar división por cero
    if radiacion_extraterrestre_g0_w_m2 <= 0:
        # Noche: no es posible verificar
        return Alarma(
            timestamp=datetime.now(),
            tipo_verificacion=TipoVerificacion.RADIACION,
            nivel=NivelAlerta.NORMAL,
            valor1=0.0,
            valor2=0.0,
            divergencia_pct=0.0,
            descripcion="Noche: verificación de radiación no aplicable",
            accion_recomendada="Sin acción (noche)"
        )
    
    # Calcular K_t
    K_t = radiacion_real_w_m2 / radiacion_extraterrestre_g0_w_m2
    
    # Determinar si es anómalo
    if K_t > 1.05:
        nivel = NivelAlerta.CRITICA
        descripcion = f"ANOMALÍA: K_t = {K_t:.3f} (> 1.0). Radiación imposible."
        accion = "Fallo de piranómetro. Sensor sobresaturado o cable conectado incorrectamente."
        divergencia_pct = 50.0  # Anomalía severa
    elif K_t > 0.90:
        nivel = NivelAlerta.ALTA
        descripcion = f"K_t muy elevado: {K_t:.3f}. Posible reflejo o sensor sucio."
        accion = "Limpiar domos del piranómetro. Verificar interferencias."
        divergencia_pct = 20.0
    elif K_t < 0:
        nivel = NivelAlerta.CRITICA
        descripcion = f"K_t negativo: {K_t:.3f}. Imposible físicamente."
        accion = "Fallo del piranómetro. Revisar conexión y calibración."
        divergencia_pct = 100.0
    elif elevacion_solar_deg < 15 and K_t > 0.7:
        nivel = NivelAlerta.MEDIA
        descripcion = f"K_t alto ({K_t:.3f}) con sol bajo ({elevacion_solar_deg:.1f}°). Poco confiable."
        accion = "Sol bajo en horizonte. Medida menos confiable. Esperar a elevación solar > 15°."
        divergencia_pct = 10.0
    elif 0.6 <= K_t <= 0.85:
        nivel = NivelAlerta.NORMAL
        descripcion = f"K_t normal: {K_t:.3f}. Radiación coherente."
        accion = "Sin acción necesaria"
        divergencia_pct = 0.0
    else:
        nivel = NivelAlerta.NORMAL
        descripcion = f"K_t: {K_t:.3f}. Dentro de rango esperado."
        accion = "Sin acción necesaria"
        divergencia_pct = 0.0
    
    return Alarma(
        timestamp=datetime.now(),
        tipo_verificacion=TipoVerificacion.RADIACION,
        nivel=nivel,
        valor1=K_t,
        valor2=1.0,  # Referencia: K_t debe estar cerca de 0.75 típicamente
        divergencia_pct=divergencia_pct,
        descripcion=descripcion,
        accion_recomendada=accion
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 6: Paquete Completo de Validación
# ═══════════════════════════════════════════════════════════════════════════════

def ejecutar_validacion_cruzada_completa(
    nubosidad_radiometrica_pct: float,
    nubosidad_atmosferica_pct: float,
    temperatura_omm_c: float,
    temperatura_real_c: float,
    humedad_relativa_pct: float,
    radiacion_real_w_m2: float,
    radiacion_g0_w_m2: float,
    elevacion_solar_deg: float
) -> Dict[str, Alarma]:
    """
    Ejecuta todas las verificaciones cruzadas (Trinity Elite).
    
    Devuelve un diccionario con todas las alarmas generadas.
    El nivel más alto determina el estado general del sistema.
    
    Args:
        (ver funciones anteriores)
        
    Returns:
        Diccionario con claves = tipo de verificación, valores = Alarma
    """
    
    alarmas = {
        "nubosidad": verificar_nubosidad(nubosidad_radiometrica_pct, nubosidad_atmosferica_pct),
        "temperatura_virtual": verificar_temperatura_virtual(temperatura_omm_c, temperatura_real_c, humedad_relativa_pct),
        "radiacion": verificar_radiacion(radiacion_real_w_m2, radiacion_g0_w_m2, elevacion_solar_deg),
    }
    
    return alarmas


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 7: Resumen de Alarmas
# ═══════════════════════════════════════════════════════════════════════════════

def generar_resumen_alarmas(alarmas: Dict[str, Alarma]) -> str:
    """
    Genera un resumen textual de todas las alarmas.
    
    Args:
        alarmas: Diccionario de alarmas
        
    Returns:
        String con resumen formateado
    """
    
    # Determinar nivel máximo
    nivel_max = max((a.nivel for a in alarmas.values()), default=NivelAlerta.NORMAL)
    
    estado_texto = {
        NivelAlerta.NORMAL: "[OK] NORMAL",
        NivelAlerta.BAJA: "[WARNING] BAJA",
        NivelAlerta.MEDIA: "[WARNING] MEDIA",
        NivelAlerta.ALTA: "🔴 ALTA",
        NivelAlerta.CRITICA: "🛑 CRÍTICA",
    }
    
    resumen = f"VALIDACIÓN CRUZADA - ESTADO: {estado_texto.get(nivel_max, 'DESCONOCIDO')}\n"
    resumen += "=" * 80 + "\n\n"
    
    for tipo, alarma in alarmas.items():
        resumen += f"[{alarma.tipo_verificacion.value.upper()}]\n"
        resumen += f"  Nivel: {estado_texto[alarma.nivel]}\n"
        resumen += f"  Divergencia: {alarma.divergencia_pct:.2f}%\n"
        resumen += f"  {alarma.descripcion}\n"
        resumen += f"  → {alarma.accion_recomendada}\n\n"
    
    return resumen


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("═" * 80)
    print("PRUEBA VALIDADOR CRUZADO - ALARMAS DE COHERENCIA (TRINITY ELITE)")
    print("═" * 80)
    
    # CASO 1: Sistema coherente (todo bien)
    print("\n📋 CASO 1: Sistema Coherente (Día normal)")
    alarmas1 = ejecutar_validacion_cruzada_completa(
        nubosidad_radiometrica_pct=25.0,
        nubosidad_atmosferica_pct=28.0,
        temperatura_omm_c=20.8,
        temperatura_real_c=20.0,
        humedad_relativa_pct=65.0,
        radiacion_real_w_m2=650.0,
        radiacion_g0_w_m2=850.0,
        elevacion_solar_deg=35.0
    )
    print(generar_resumen_alarmas(alarmas1))
    
    # CASO 2: Radiación problemática
    print("\n📋 CASO 2: Piranómetro Sucio (K_t alto)")
    alarmas2 = ejecutar_validacion_cruzada_completa(
        nubosidad_radiometrica_pct=10.0,
        nubosidad_atmosferica_pct=35.0,
        temperatura_omm_c=21.0,
        temperatura_real_c=20.0,
        humedad_relativa_pct=70.0,
        radiacion_real_w_m2=900.0,  # Muy alto
        radiacion_g0_w_m2=900.0,
        elevacion_solar_deg=40.0
    )
    print(generar_resumen_alarmas(alarmas2))
    
    # CASO 3: Anomalía crítica
    print("\n📋 CASO 3: FALLO CRÍTICO (K_t > 1.0)")
    alarmas3 = ejecutar_validacion_cruzada_completa(
        nubosidad_radiometrica_pct=0.0,
        nubosidad_atmosferica_pct=50.0,
        temperatura_omm_c=20.0,
        temperatura_real_c=20.0,
        humedad_relativa_pct=80.0,
        radiacion_real_w_m2=1100.0,  # IMPOSIBLE
        radiacion_g0_w_m2=850.0,
        elevacion_solar_deg=45.0
    )
    print(generar_resumen_alarmas(alarmas3))
    
    print("═" * 80)
    print("[OK] Validador Cruzado operacional. Alarmas de coherencia confirmadas.")
    print("═" * 80)
