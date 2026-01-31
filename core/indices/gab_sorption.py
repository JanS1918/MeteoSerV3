"""
Modelo GAB de Sorción (Guggenheim-Anderson-de Boer) para paredes activas.
Conexión directa con psicrometría Hyland-Wexler (Nivel 1).
"""

import math

def gab_sorption_isotherm(hr, a, b, c, temp_c=None):
    """
    Isoterma GAB para sorción de humedad en materiales porosos.
    Referencia: van den Berg & Bruin (1981), Guggenheim-Anderson-de Boer.
    hr: humedad relativa (0-100)
    a, b, c: parámetros del material (ajustar para cada tipo de pared)
    temp_c: temperatura (°C), opcional para futuras extensiones (corrección térmica)
    Devuelve fracción de humedad adsorbida (kg H2O / kg material seco)
    """
    # Validación física de parámetros
    if not (0.01 < a < 2.0 and 0.01 < b < 1.0 and 0.01 < c < 2.0):
        raise ValueError(f"Parámetros GAB fuera de rango físico: a={a}, b={b}, c={c}")
    rh = max(0.0, min(1.0, hr / 100.0))
    # Corrección térmica opcional (placeholder, para materiales avanzados)
    if temp_c is not None:
        # Ejemplo: a *= (1 + 0.0005 * (temp_c - 25))
        pass
    num = a * b * c * rh
    den = (1 - b * rh) * (1 - b * rh + b * c * rh)
    if abs(den) < 1e-12:
        return 0.0
    resultado = num / den
    # Protección contra valores no físicos
    if resultado < 0 or math.isnan(resultado) or math.isinf(resultado):
        return 0.0
    return resultado

# Ejemplo de conexión con psicrometría Hyland-Wexler
from core.indices.environmental_indices import psicrometria_hyland_wexler

def humedad_pared_activa(hr_ambiente, temp_ambiente, parametros_pared):
    """
    Calcula la humedad adsorbida en la pared usando GAB y la psicrometría ambiente.
    parametros_pared: dict con 'a', 'b', 'c', 'tipo' y 'masa_seca'
    """
    a = parametros_pared.get('a', 0.95)
    b = parametros_pared.get('b', 0.85)
    c = parametros_pared.get('c', 0.90)
    masa_seca = parametros_pared.get('masa_seca', 1.0)
    tipo = parametros_pared.get('tipo', 'desconocido')
    # Se puede ajustar según material: ladrillo, yeso, madera, etc.
    fraccion_adsorbida = gab_sorption_isotherm(hr_ambiente, a, b, c, temp_c=temp_ambiente)
    # Conexión a psicrometría: obtener presión de vapor, etc.
    psic = psicrometria_hyland_wexler(temp_ambiente, hr_ambiente)
    return {
        'fraccion_adsorbida': fraccion_adsorbida,
        'presion_vapor': psic.get('presion_vapor') if isinstance(psic, dict) else psic,
        'contenido_agua_pared': fraccion_adsorbida * masa_seca,
        'tipo_material': tipo,
        'parametros': {'a': a, 'b': b, 'c': c, 'masa_seca': masa_seca},
        'referencia': 'van den Berg & Bruin (1981), GAB, ASHRAE 2026',
    }
