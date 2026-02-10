"""
Modelo GAB de Sorción (Guggenheim-Anderson-de Boer) para paredes activas.
Conexión directa con psicrometría Hyland-Wexler (Nivel 1).

⚛️ FUSIÓN TRANSVERSAL V1.3: Integración con EKF para predicción de humedad profunda.

Motor: Quantum_Universal_Metrology_v1.3
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
    # Corrección térmica opcional (ajuste físico suave)
    if temp_c is not None:
        delta_t = temp_c - 25.0
        a = a * (1 + 0.0005 * delta_t)
        b = b * (1 - 0.0002 * delta_t)
        c = c * (1 + 0.0003 * delta_t)
        a = max(0.01, min(2.0, a))
        b = max(0.01, min(1.0, b))
        c = max(0.01, min(2.0, c))
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

def humedad_pared_activa(hr_ambiente, temp_ambiente, parametros_pared, statistical_brain=None):
    """
    Calcula la humedad adsorbida en la pared usando GAB y la psicrometría ambiente.
    
    ⚛️ FUSIÓN TRANSVERSAL V1.3: EKF para predicción de humedad profunda con inercia térmica.
    
    parametros_pared: dict con 'a', 'b', 'c', 'tipo' y 'masa_seca'
    statistical_brain: Cerebro Estadístico para predicción EKF
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
    
    # ⚛️ FUSIÓN TRANSVERSAL: EKF para predecir humedad profunda con inercia térmica
    humedad_profunda_predicha = None
    if statistical_brain:
        # Modelo físico de transición para GAB (inercia térmica)
        def gab_physical_model(state, dt):
            # Estado: [humedad_superficial, humedad_profunda]
            # Inercia térmica: la humedad profunda sigue a la superficial con delay
            tau = 3600.0  # Constante de tiempo (1 hora para paredes típicas)
            if dt > 0:
                alpha = dt / (tau + dt)
            else:
                alpha = 0.0
            
            humedad_sup = state[0]
            humedad_prof = state[1]
            
            # Transición: humedad_profunda → humedad_superficial (con inercia)
            humedad_prof_nueva = humedad_prof + alpha * (humedad_sup - humedad_prof)
            
            return [humedad_sup, humedad_prof_nueva]
        
        # Predecir con EKF
        humedad_profunda_predicha = statistical_brain.predict_with_ekf(
            "humedad_pared_profunda",
            gab_physical_model,
            dt=60.0  # 1 minuto
        )
    
    contenido_agua_pared = fraccion_adsorbida * masa_seca
    
    # Predicción de moho (si humedad profunda > 80% durante tiempo prolongado)
    riesgo_moho = 0.0
    if humedad_profunda_predicha and humedad_profunda_predicha > 0.8:
        riesgo_moho = min(100.0, (humedad_profunda_predicha - 0.8) * 500.0)
    
    return {
        'fraccion_adsorbida': fraccion_adsorbida,
        'presion_vapor': psic.get('presion_vapor') if isinstance(psic, dict) else psic,
        'contenido_agua_pared': contenido_agua_pared,
        'humedad_profunda_predicha': humedad_profunda_predicha,
        'riesgo_moho_pct': round(riesgo_moho, 1),
        'tipo_material': tipo,
        'parametros': {'a': a, 'b': b, 'c': c, 'masa_seca': masa_seca},
        'referencia': 'van den Berg & Bruin (1981), GAB, ASHRAE 2026',
        'motor': 'Quantum_Universal_Metrology_v1.3',
        'fusion_transversal': 'ekf_inercia_termica' if statistical_brain else 'none'
    }
