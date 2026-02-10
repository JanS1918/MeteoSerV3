"""
test_visibilidad_factor_z.py
============================
Comparación de visibilidad con y sin Factor Z para demostrar la diferencia
"""

from bucholtz_rayleigh_v25 import BucholtzRayleighV25


def test_visibilidad_con_sin_factor_z():
    """
    Prueba la diferencia de visibilidad con y sin Factor Z
    """
    print("="*70)
    print("COMPARACIÓN: VISIBILIDAD CON Y SIN FACTOR Z")
    print("="*70)
    
    bucholtz = BucholtzRayleighV25()
    
    # Condiciones típicas de Argentona
    temperatura_c = 18.5
    presion_hpa = 1019.1
    humedad_relativa = 0.70
    tipo_aire = "TEMPLADA"
    
    print(f"\nCondiciones:")
    print(f"  Temperatura: {temperatura_c}°C")
    print(f"  Presión: {presion_hpa} hPa")
    print(f"  Humedad relativa: {humedad_relativa*100}%")
    print(f"  Tipo de aire: {tipo_aire}")
    print("")
    
    # Comparación
    comparacion = bucholtz.comparar_con_sin_factor_z(
        temperatura_c, presion_hpa, humedad_relativa, tipo_aire
    )
    
    print(f"RESULTADOS:")
    print(f"  Visibilidad CON Factor Z: {comparacion['visibilidad_con_z_km']:.2f} km")
    print(f"  Visibilidad SIN Factor Z: {comparacion['visibilidad_sin_z_km']:.2f} km")
    print(f"  Diferencia: {comparacion['diferencia_m']:.2f} m")
    print(f"  Diferencia porcentual: {comparacion['diferencia_pct']:.4f}%")
    print(f"  Mejora: {comparacion['mejora']}")
    print("")
    
    print("="*70)
    print("INTERPRETACIÓN:")
    print("="*70)
    print(f"El Factor Z mejora la precisión de la visibilidad en {abs(comparacion['diferencia_m']):.1f} metros.")
    print(f"Esto representa una corrección del {abs(comparacion['diferencia_pct']):.4f}% sobre el cálculo ideal.")
    print("Esta es la diferencia entre un observatorio nacional y tu sistema soberano.")
    print("="*70)


if __name__ == "__main__":
    test_visibilidad_con_sin_factor_z()
