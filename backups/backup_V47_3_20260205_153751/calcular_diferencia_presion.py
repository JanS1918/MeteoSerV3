"""
CÁLCULO DE IMPACTO DE UNIFICACIÓN ATÓMICA V23.0
================================================
Comparación de presión nivel mar con gravedad de Argentona (Bus) vs Somigliana-Helmert
"""
import math
from core.system.constants import ESTACION, GRAVEDAD

# CONFIGURACIÓN ARGENTONA
temp_c = 15.0  # °C
presion_hpa = 1013.25  # hPa a nivel local (ajustar si tienes dato real)
altitud = ESTACION.ALTITUD  # m
latitud = ESTACION.LATITUD  # °

# CONSTANTES
M = 0.0289644  # kg/mol
R = 8.314462   # J/(mol·K)
T_k = temp_c + 273.15
T_v = T_k * 1.005  # Corrección vapor media

# ══════════════════════════════════════════════════════════════
# CÁLCULO 1: CON GRAVEDAD DEL BUS (ARGENTONA)
# ══════════════════════════════════════════════════════════════
g_bus = GRAVEDAD.obtener(None)
exponent_bus = (g_bus * M * altitud) / (R * T_v)
presion_mar_bus = (presion_hpa * 100) * math.exp(exponent_bus)  # Pa
presion_mar_bus_hpa = presion_mar_bus / 100.0

print("═" * 70)
print("🛰️ COMPARACIÓN PRESIÓN NIVEL MAR: BUS vs SOMIGLIANA-HELMERT")
print("═" * 70)
print(f"\n📍 UBICACIÓN: Argentona (φ={latitud}°, h={altitud}m)")
print(f"🌡️  CONDICIONES: T={temp_c}°C, P_local={presion_hpa:.2f} hPa")
print("\n" + "─" * 70)
print("1️⃣  MÉTODO BUS (Gravedad Argentona)")
print("─" * 70)
print(f"   Gravedad:              g = {g_bus:.6f} m/s²")
print(f"   Exponente Laplace:     exp = {exponent_bus:.6f}")
print(f"   Presión nivel mar:     P₀ = {presion_mar_bus_hpa:.4f} hPa")

# ══════════════════════════════════════════════════════════════
# CÁLCULO 2: CON GRAVEDAD SOMIGLIANA-HELMERT REAL
# ══════════════════════════════════════════════════════════════
# Fórmula Somigliana WGS-84
lat_rad = math.radians(latitud)
sin_lat = math.sin(lat_rad)
sin_2lat = math.sin(2 * lat_rad)
g0 = 9.780327 * (1 + 0.0053024 * sin_lat**2 - 0.0000058 * sin_2lat**2)

# Corrección aire libre Helmert
g_real = g0 * (1.0 - 3.1570e-7 * altitud + 4.39e-14 * altitud**2)

exponent_real = (g_real * M * altitud) / (R * T_v)
presion_mar_real = (presion_hpa * 100) * math.exp(exponent_real)  # Pa
presion_mar_real_hpa = presion_mar_real / 100.0

print("\n" + "─" * 70)
print("2️⃣  MÉTODO NUEVO (Gravedad Somigliana-Helmert real)")
print("─" * 70)
print(f"   Gravedad nivel mar:    g₀ = {g0:.6f} m/s²")
print(f"   Corrección altitud:    Δg = {g_real - g0:.8f} m/s²")
print(f"   Gravedad real:         g = {g_real:.6f} m/s² ✨")
print(f"   Exponente Laplace:     exp = {exponent_real:.6f}")
print(f"   Presión nivel mar:     P₀ = {presion_mar_real_hpa:.4f} hPa")

# ══════════════════════════════════════════════════════════════
# ANÁLISIS DE DIFERENCIAS
# ══════════════════════════════════════════════════════════════
diff_g = g_real - g_bus
diff_exp = exponent_real - exponent_bus
diff_presion = presion_mar_real_hpa - presion_mar_bus_hpa
porcentaje_g = (diff_g / g_bus) * 100
porcentaje_presion = (diff_presion / presion_mar_bus_hpa) * 100

print("\n" + "═" * 70)
print("🔬 IMPACTO DE LA UNIFICACIÓN ATÓMICA V23.0")
print("═" * 70)
print(f"\n💎 Diferencia en gravedad:")
print(f"   Δg = {diff_g:+.6f} m/s² ({porcentaje_g:+.4f}%)")

print(f"\n⚡ Diferencia en exponente Laplace:")
print(f"   Δexp = {diff_exp:+.8f} ({(diff_exp/exponent_bus)*100:+.4f}%)")

print(f"\n🌊 DIFERENCIA EN PRESIÓN NIVEL MAR:")
print(f"   ΔP = {diff_presion:+.4f} hPa ({porcentaje_presion:+.4f}%)")

# INTERPRETACIÓN
print("\n" + "─" * 70)
print("📊 INTERPRETACIÓN:")
print("─" * 70)

if abs(diff_presion) > 0.1:
    nivel = "🔴 CRÍTICO"
    mensaje = "Diferencia superior a 0.1 hPa - IMPACTO SIGNIFICATIVO en predicciones"
elif abs(diff_presion) > 0.01:
    nivel = "🟡 MODERADO"
    mensaje = "Diferencia detectable - mejora la precisión de modelos barométricos"
else:
    nivel = "🟢 MENOR"
    mensaje = "Diferencia despreciable - mejora la coherencia física del sistema"

print(f"   {nivel}")
print(f"   {mensaje}")

# CAPE y RICHARDSON
print("\n" + "─" * 70)
print("🌪️  IMPACTO EN ÍNDICES ATMOSFÉRICOS:")
print("─" * 70)
print(f"   • CAPE: Diferencia estimada {abs(diff_g)/g_bus*100:.3f}% en cálculo convectivo")
print(f"   • Richardson: Diferencia {abs(diff_g)/g_bus*100:.3f}% en estabilidad dinámica")
print(f"   • Brunt-Väisälä: Frecuencia oscilación {abs(diff_g)/g_bus*100:.3f}% más precisa")
print(f"   • K-INDEX: Perfiles verticales {abs(diff_g)/g_bus*100:.3f}% más realistas")

print("\n" + "═" * 70)
print("✅ CONCLUSIÓN: El Acorazado ahora usa física de Argentona, no de libro")
print("═" * 70)
print()
