"""
DUELO MEJORADO: SciPy vs Actual (CON BASELINE CORRECTO)

Ejecuta todos 5 duelos usando SISTEMA_PSICOTECNICO_MAESTRO_V36
con la baseline REAL de cada parámetro.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from SISTEMA_PSICOTECNICO_MAESTRO_V36 import PsychotechnicValidator
import numpy as np
from scipy.stats import weibull_min
from scipy.interpolate import interp1d
from scipy.integrate import quad
from scipy.ndimage import gaussian_filter
from scipy.optimize import curve_fit
import warnings

warnings.filterwarnings('ignore')

async def main():
    # Inicializar sistema
    sistema = PsychotechnicValidator()
    
    print("="*70)
    print("DUELO MEJORADO: SCIPY VS ACTUAL (CON BASELINE CORRECTO)")
    print("="*70)

# Datos simulados (baseados en rango real de sensores Ecowitt)
np.random.seed(42)

# Duelo 1: SENSACION_TERMICA (REEMPLAZO)
print("\n[DUELO 1] SENSACION_TERMICA: UTCI vs SciPy curve_fit")
print("-" * 70)

temp = np.linspace(-10, 50, 50) + np.random.normal(0, 0.5, 50)
humedad = np.linspace(20, 100, 50) + np.random.normal(0, 2, 50)
viento = np.linspace(0, 25, 50) + np.random.normal(0, 0.2, 50)
radiacion = np.linspace(0, 1000, 50) + np.random.normal(0, 10, 50)

# ACTUAL: UTCI Polynomial (simulado)
utci_actual = temp - 0.55 * (1 - 0.161 * viento) * (temp - 14.5)
utci_actual = np.clip(utci_actual, -50, 60)

# SCIPY: curve_fit Wind Chill
def wind_chill(data, a, b, c):
    return a + b * data[0] + c * np.sqrt(data[1])

try:
    popt, _ = curve_fit(wind_chill, [temp, viento], utci_actual, maxfev=1000)
    scipy_sensacion = wind_chill([temp, viento], *popt)
    scipy_sensacion = np.clip(scipy_sensacion, -50, 60)
except:
    scipy_sensacion = utci_actual.copy()

# Validar ambos
print("\n> VALIDANDO UTCI (ACTUAL)...")
resultado_utci = sistema.validar_formula(
    nombre="UTCI_Polynomial_Fiala186",
    datos=utci_actual,
    parametro="sensacion_termica",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score UTCI: {resultado_utci['justice_score']:.3f}")
print(f"  Precisión: {resultado_utci['precision']:.1f}%")
print(f"  Velocidad: {resultado_utci['velocidad_score']:.1f}/10")

print("\n> VALIDANDO SciPy curve_fit (NUEVO)...")
resultado_scipy_1 = sistema.validar_formula(
    nombre="SciPy_CurveFit_WindChill",
    datos=scipy_sensacion,
    parametro="sensacion_termica",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score SciPy: {resultado_scipy_1['justice_score']:.3f}")
print(f"  Precisión: {resultado_scipy_1['precision']:.1f}%")
print(f"  Velocidad: {resultado_scipy_1['velocidad_score']:.1f}/10")

ganador_1 = "UTCI" if resultado_utci['justice_score'] > resultado_scipy_1['justice_score'] else "SciPy"
print(f"\n✓ GANADOR DUELO 1: {ganador_1}")

# Duelo 2: HUMEDAD_RELATIVA (MEJORA)
print("\n\n[DUELO 2] HUMEDAD_RELATIVA: Sensor vs SciPy interp1d")
print("-" * 70)

# ACTUAL: Sensor Ecowitt con ruido
humedad_sensor = np.linspace(20, 95, 50) + np.random.normal(0, 3, 50)
humedad_sensor = np.clip(humedad_sensor, 10, 100)

# SCIPY: interp1d suavizado
x_orig = np.arange(len(humedad_sensor))
f_interp = interp1d(x_orig, humedad_sensor, kind='cubic', fill_value='extrapolate')
scipy_humedad = f_interp(x_orig)
scipy_humedad = np.clip(scipy_humedad, 10, 100)

print("\n> VALIDANDO SENSOR RAW (ACTUAL)...")
resultado_sensor = sistema.validar_formula(
    nombre="Ecowitt_Sensor_Direct_HR",
    datos=humedad_sensor,
    parametro="humedad_relativa",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score Sensor: {resultado_sensor['justice_score']:.3f}")
print(f"  Precisión: {resultado_sensor['precision']:.1f}%")
print(f"  Velocidad: {resultado_sensor['velocidad_score']:.1f}/10")

print("\n> VALIDANDO SciPy interp1d (MEJORA)...")
resultado_scipy_2 = sistema.validar_formula(
    nombre="SciPy_Interp1D_HR",
    datos=scipy_humedad,
    parametro="humedad_relativa",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score SciPy: {resultado_scipy_2['justice_score']:.3f}")
print(f"  Precisión: {resultado_scipy_2['precision']:.1f}%")
print(f"  Velocidad: {resultado_scipy_2['velocidad_score']:.1f}/10")

ganador_2 = "Interp1D" if resultado_scipy_2['justice_score'] > resultado_sensor['justice_score'] else "Sensor"
print(f"\n✓ GANADOR DUELO 2: {ganador_2}")

# Duelo 3: VELOCIDAD_VIENTO (MEJORA)
print("\n\n[DUELO 3] VELOCIDAD_VIENTO: Sensor+Ajuste vs SciPy Weibull")
print("-" * 70)

# ACTUAL: Sensor + ajuste logarítmico
viento_sensor = weibull_min.rvs(c=1.5, loc=0, scale=5, size=50)
viento_ajustado = viento_sensor * 1.1  # factor_ajuste_altura

# SCIPY: Weibull distribution fit
params_weibull = weibull_min.fit(viento_sensor)
scipy_viento = weibull_min.ppf(np.linspace(0.01, 0.99, 50), *params_weibull)

print("\n> VALIDANDO SENSOR + AJUSTE (ACTUAL)...")
resultado_viento = sistema.validar_formula(
    nombre="Ecowitt_Wind_LogAdjust",
    datos=viento_ajustado,
    parametro="velocidad_viento",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score Sensor+Ajuste: {resultado_viento['justice_score']:.3f}")
print(f"  Precisión: {resultado_viento['precision']:.1f}%")
print(f"  Velocidad: {resultado_viento['velocidad_score']:.1f}/10")

print("\n> VALIDANDO SciPy Weibull (MEJORA)...")
resultado_scipy_3 = sistema.validar_formula(
    nombre="SciPy_Weibull_Wind",
    datos=scipy_viento,
    parametro="velocidad_viento",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score SciPy: {resultado_scipy_3['justice_score']:.3f}")
print(f"  Precisión: {resultado_scipy_3['precision']:.1f}%")
print(f"  Velocidad: {resultado_scipy_3['velocidad_score']:.1f}/10")

ganador_3 = "Weibull" if resultado_scipy_3['justice_score'] > resultado_viento['justice_score'] else "Sensor+Ajuste"
print(f"\n✓ GANADOR DUELO 3: {ganador_3}")

# Duelo 4: INDICE_UV (MEJORA)
print("\n\n[DUELO 4] INDICE_UV: Sensor vs SciPy quad")
print("-" * 70)

# ACTUAL: Sensor directo UV
uv_sensor = np.linspace(0, 11, 50) + np.random.normal(0, 0.3, 50)
uv_sensor = np.clip(uv_sensor, 0, 15)

# SCIPY: quad (espectro UV integrado)
def uv_spectrum(wl):
    return np.exp(-(wl - 330)**2 / 500)

scipy_uv = np.array([quad(uv_spectrum, 290, 400)[0] / 100 for _ in range(50)])
scipy_uv = scipy_uv * 11 / scipy_uv.max()  # Normalizar a escala 0-11

print("\n> VALIDANDO SENSOR UV (ACTUAL)...")
resultado_uv = sistema.validar_formula(
    nombre="Ecowitt_UV_Direct",
    datos=uv_sensor,
    parametro="indice_uv",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score Sensor: {resultado_uv['justice_score']:.3f}")
print(f"  Precisión: {resultado_uv['precision']:.1f}%")
print(f"  Velocidad: {resultado_uv['velocidad_score']:.1f}/10")

print("\n> VALIDANDO SciPy quad (MEJORA)...")
resultado_scipy_4 = sistema.validar_formula(
    nombre="SciPy_Quad_UVSpectrum",
    datos=scipy_uv,
    parametro="indice_uv",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score SciPy: {resultado_scipy_4['justice_score']:.3f}")
print(f"  Precisión: {resultado_scipy_4['precision']:.1f}%")
print(f"  Velocidad: {resultado_scipy_4['velocidad_score']:.1f}/10")

ganador_4 = "Quad" if resultado_scipy_4['justice_score'] > resultado_uv['justice_score'] else "Sensor"
print(f"\n✓ GANADOR DUELO 4: {ganador_4}")

# Duelo 5: RADIACION_SOLAR (MEJORA)
print("\n\n[DUELO 5] RADIACION_SOLAR: Sensor+Gueymard vs SciPy Gaussian")
print("-" * 70)

# ACTUAL: Sensor + Gueymard
radiacion_sensor = np.linspace(0, 1000, 50) + np.random.normal(0, 30, 50)
radiacion_sensor = np.clip(radiacion_sensor, 0, 1200)
radiacion_gueymard = radiacion_sensor * 0.95  # factor_gueymard

# SCIPY: Gaussian filter
scipy_radiacion = gaussian_filter(radiacion_sensor, sigma=2)

print("\n> VALIDANDO SENSOR + GUEYMARD (ACTUAL)...")
resultado_radiacion = sistema.validar_formula(
    nombre="Ecowitt_Rad_Gueymard",
    datos=radiacion_gueymard,
    parametro="radiacion_solar",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score Sensor+Gueymard: {resultado_radiacion['justice_score']:.3f}")
print(f"  Precisión: {resultado_radiacion['precision']:.1f}%")
print(f"  Velocidad: {resultado_radiacion['velocidad_score']:.1f}/10")

print("\n> VALIDANDO SciPy Gaussian (MEJORA)...")
resultado_scipy_5 = sistema.validar_formula(
    nombre="SciPy_Gaussian_Rad",
    datos=scipy_radiacion,
    parametro="radiacion_solar",
    tipo_calibracion="PSICOTECNICA"
)
print(f"  Justice Score SciPy: {resultado_scipy_5['justice_score']:.3f}")
print(f"  Precisión: {resultado_scipy_5['precision']:.1f}%")
print(f"  Velocidad: {resultado_scipy_5['velocidad_score']:.1f}/10")

ganador_5 = "Gaussian" if resultado_scipy_5['justice_score'] > resultado_radiacion['justice_score'] else "Sensor+Gueymard"
print(f"\n✓ GANADOR DUELO 5: {ganador_5}")

# Resumen
print("\n\n" + "="*70)
print("RESUMEN FINAL: TODOS LOS DUELOS")
print("="*70)

resultados = [
    ("1. SENSACION_TERMICA", ganador_1, resultado_utci['justice_score'], resultado_scipy_1['justice_score']),
    ("2. HUMEDAD_RELATIVA", ganador_2, resultado_sensor['justice_score'], resultado_scipy_2['justice_score']),
    ("3. VELOCIDAD_VIENTO", ganador_3, resultado_viento['justice_score'], resultado_scipy_3['justice_score']),
    ("4. INDICE_UV", ganador_4, resultado_uv['justice_score'], resultado_scipy_4['justice_score']),
    ("5. RADIACION_SOLAR", ganador_5, resultado_radiacion['justice_score'], resultado_scipy_5['justice_score']),
]

scipy_wins = 0
for duelo, ganador, score_actual, score_scipy in resultados:
    print(f"\n{duelo}")
    print(f"  Actual:  {score_actual:.3f}")
    print(f"  SciPy:   {score_scipy:.3f}")
    print(f"  → {ganador} GANA")
    if "SciPy" in ganador or "Quad" in ganador or "Weibull" in ganador or "Gaussian" in ganador or "Interp1D" in ganador:
        scipy_wins += 1

print(f"\n{'='*70}")
print(f"RESUMEN: SciPy gana en {scipy_wins}/5 duelos")
print(f"{'='*70}")
