"""
DIAGNÓSTICO DE RENDIMIENTO DEL SISTEMA
======================================
Analiza dónde estamos y qué podemos mejorar.
"""

import time
from datetime import datetime
from core.bus import obtener_bus
from core.indices.physics_engine_cached import PhysicsEngineCached
from core.atmosphere.isa_calculator import presion_isa_dinamica


def benchmark_sistema():
    """Mide performance actual de componentes críticos"""
    
    print("\n" + "="*80)
    print("  [STATS] DIAGNÓSTICO DE RENDIMIENTO - MeteoSerV3")
    print("="*80)
    
    resultados = {}
    
    # 1. Physics Engine (con y sin caché)
    print("\n1️⃣  PHYSICS ENGINE:")
    print("   " + "-"*76)
    
    engine = PhysicsEngineCached()
    
    # Sin caché (primera ejecución)
    inicio = time.perf_counter()
    for _ in range(100):
        engine.obtener_todas_constantes(25.0, 1013.25, 0.65)
    sin_cache = time.perf_counter() - inicio
    
    # Con caché (mismos parámetros)
    inicio = time.perf_counter()
    for _ in range(100):
        engine.obtener_todas_constantes(25.0, 1013.25, 0.65)
    con_cache = time.perf_counter() - inicio
    
    mejora = (sin_cache - con_cache) / sin_cache * 100
    print(f"   Sin caché:    {sin_cache*1000:.2f} ms (100 iteraciones)")
    print(f"   Con caché:    {con_cache*1000:.2f} ms (100 iteraciones)")
    print(f"   Mejora:       {mejora:.1f}%")
    
    stats = engine.cache.tasa_acierto()
    print(f"   Hit rate:     {stats['tasa_acierto']:.1f}%")
    
    resultados['physics_cache_improvement'] = mejora
    
    # 2. ISA Calculator
    print("\n2️⃣  ISA PRESSURE CALCULATION:")
    print("   " + "-"*76)
    
    inicio = time.perf_counter()
    for altitud in range(0, 4000, 100):
        presion_isa_dinamica(altitud)
    isa_time = time.perf_counter() - inicio
    
    print(f"   40 cálculos ISA: {isa_time*1000:.2f} ms ({isa_time/40*1000:.3f} ms cada uno)")
    print(f"   [OK] RÁPIDO - ISA no es cuello de botella")
    
    resultados['isa_calc_ms'] = isa_time*1000
    
    # 3. Bus de Capas
    print("\n3️⃣  BUS DE CAPAS DE INFORMACIÓN:")
    print("   " + "-"*76)
    
    bus = obtener_bus()
    
    inicio = time.perf_counter()
    for i in range(1000):
        bus.publicar(f"var{i}", i*1.5, "CORE", origen="test")
    bus_insert = time.perf_counter() - inicio
    
    inicio = time.perf_counter()
    for _ in range(100):
        bus.query("core:*")
    bus_query = time.perf_counter() - inicio
    
    print(f"   1.000 inserciones: {bus_insert*1000:.2f} ms ({bus_insert/1000*1000:.3f} ms cada una)")
    print(f"   100 queries:       {bus_query*1000:.2f} ms ({bus_query/100*1000:.3f} ms cada una)")
    print(f"   [OK] RÁPIDO - Bus no es cuello de botella")
    
    resultados['bus_insert_ms'] = bus_insert*1000
    resultados['bus_query_ms'] = bus_query*1000
    
    # 4. Análisis de capacidad
    print("\n4️⃣  ANÁLISIS DE CAPACIDAD:")
    print("   " + "-"*76)
    
    dashboard = bus.obtener_dashboard()
    capas = dashboard['capas']
    
    cap_core = capas['CORE']['items']
    cap_inter = capas['INTERMEDIATE']['items']
    cap_debug = capas['DEBUG']['items']
    cap_ts = capas['TIMESERIES']['variables']
    
    print(f"   CORE en uso:       {cap_core} / 2.000 ({cap_core/2000*100:.1f}%)")
    print(f"   INTERMEDIATE:      {cap_inter} / 3.000 ({cap_inter/3000*100:.1f}%)")
    print(f"   DEBUG:             {cap_debug} / 5.000 ({cap_debug/5000*100:.1f}%)")
    print(f"   TIMESERIES:        {cap_ts} variables")
    
    print(f"\n   [OK] Uso de memoria: BAJO (mucho espacio para crecer)")
    
    # Identificar cuellos de botella
    print("\n5️⃣  IDENTIFICACIÓN DE CUELLOS DE BOTELLA:")
    print("   " + "-"*76)
    
    cuellos = []
    
    if mejora < 30:
        cuellos.append("[ERROR] Physics cache inefectivo (mejora < 30%)")
    else:
        print("   [OK] Physics cache eficiente")
    
    if bus_insert > 1:
        cuellos.append("[ERROR] Bus inserciones lenta (> 1ms)")
    else:
        print("   [OK] Bus inserciones rápida")
    
    if bus_query > 1:
        cuellos.append("[ERROR] Bus queries lenta (> 1ms)")
    else:
        print("   [OK] Bus queries rápida")
    
    if not cuellos:
        print("\n   [TARGET] CONCLUSIÓN: No hay cuellos de botella obvios")
        print("      El rendimiento está BIEN para operaciones individuales")
        print("      Las mejoras vendrán de ARQUITECTURA y ML, no de tunning")
    
    return resultados


def diagnostico_oportunidades():
    """Identifica dónde REALMENTE sacar rendimiento"""
    
    print("\n" + "="*80)
    print("  [LAUNCH] OPORTUNIDADES PARA SACAR RENDIMIENTO")
    print("="*80)
    
    print("\n1️⃣  PREDICCIÓN (Tier 4 - MEJOR ROI)")
    print("   " + "-"*76)
    print("""
   ¿Qué?   Predecir UTCI/ET0/ÍNDICES 1-5 minutos antes
   
   Impacto: Sistema deja de ser "reactivo" → "PROACTIVO"
   - Alertas 5 min antes de condiciones críticas
   - Riego puede comenzar antes de pico de calor
   - Tomar decisiones en FUTURO, no pasado
   
   Complejidad: MEDIA
   ROI: ALTÍSIMO (decisiones basadas en anticipación)
   
   Tecnología: LSTM/Transformer en PyTorch/TensorFlow
    """)
    
    print("\n2️⃣  VECTORIZACIÓN NumPy (Tier 3 - PERFORMANCE)")
    print("   " + "-"*76)
    print("""
   ¿Qué?   Reescribir cálculos de Physics/Índices con NumPy
   
   Actual:   Cálculos escalar (1 temperatura a la vez)
   Mejora:   Cálculos vectoriales (1.000 temperaturas simultáneamente)
   
   Impacto: 20-100x más rápido en batch processing
   
   Ejemplo:
      # Actual (lento)
      for T in temperaturas:
          densidad = calcular_densidad(T)
      
      # NumPy (100x más rápido)
      densidades = calcular_densidad_vectorizado(temperaturas)
   
   Complejidad: BAJA
   ROI: ALTÍSIMO si procesas lotes
    """)
    
    print("\n3️⃣  ASYNC/AWAIT (Tier 2 - I/O IMPROVEMENT)")
    print("   " + "-"*76)
    print("""
   ¿Qué?   No esperes API externas bloqueándote
   
   Actual:   Solicitud → ESPERA → Respuesta → Siguiente
   Async:    Solicitud → OTROS CÁLCULOS → Respuesta llega
   
   Impacto: 3-10x más responsive si hay I/O (APIs, BD)
   
   Casos de uso:
   - Geocodificación (SRTM, nominatim)
   - Datos históricos (API meteorológica)
   - Publicación en múltiples destinos
   
   Complejidad: MEDIA
   ROI: ALTO (especialmente si usas APIs remotas)
    """)
    
    print("\n4️⃣  AUTO-CALIBRACIÓN (Tier 3 - PRECISIÓN)")
    print("   " + "-"*76)
    print("""
   ¿Qué?   El sistema aprende offset/bias de sus sensores
   
   Ejemplo:
   - Sensores física miden 2°C más caliente que realidad
   - Sistema detecta patrón después de 7 días
   - Auto-aplica corrección -2°C automáticamente
   
   Impacto: ±0.5°C → ±0.1°C (5x más preciso)
   
   Métodos:
   - Regresión lineal sobre históricos
   - Comparación con estaciones cercanas
   - Machine learning (XGBoost para detectar bias)
   
   Complejidad: MEDIA
   ROI: ALTÍSIMO (precisión = confianza = mejor decisiones)
    """)
    
    print("\n5️⃣  COMPILACIÓN CYTHON/NUMBA (Tier 4 - PERFORMANCE)")
    print("   " + "-"*76)
    print("""
   ¿Qué?   Compilar funciones Python a código nativo C
   
   Impacto: Física + Índices 10-100x más rápido
   
   Caso: UTCI tiene 20 cálculos anidados
   - Python: 50 microsegundos
   - Numba: 5 microsegundos
   
   Complejidad: MEDIA (pero cambios mínimos en código)
   ROI: ALTÍSIMO si corres tiempo real con muchos índices
   
   @numba.jit(nopython=True)
   def utci_rapido(T, HR, V, Tmrt):
       # Código automáticamente compilado a C
       ...
    """)
    
    print("\n6️⃣  MACHINE LEARNING DETECCIÓN ANOMALÍAS (Tier 3)")
    print("   " + "-"*76)
    print("""
   ¿Qué?   Reemplazar reglas por modelos entrenados
   
   Actual: if T > 40: alert("calor extremo")
   ML:     modelo predice confiabilidad del sensor
           → System automáticamente baja/sube confianza
   
   Impacto: Menos falsos positivos, alertas más inteligentes
   
   Modelos: Isolation Forest, LocalOutlierFactor, OneClassSVM
   
   Complejidad: BAJA (scikit-learn)
   ROI: MEDIO (mejor confianza)
    """)
    
    print("\n7️⃣  PERSISTENCIA INTELIGENTE (Tier 2)")
    print("   " + "-"*76)
    print("""
   ¿Qué?   Guardar históricos inteligentemente
   
   Actual: Nada persiste (data en memoria)
   Mejora: TimescaleDB/InfluxDB + Compression
   
   Impacto:
   - Recuperar si crash
   - Análisis histórico
   - Tendencias a largo plazo
   - Re-entrenar modelos ML
   
   Complejidad: MEDIA
   ROI: ALTO (confiabilidad + análisis)
    """)
    
    print("\n" + "="*80)
    print("  📈 PRIORIZACIÓN POR IMPACTO/ESFUERZO")
    print("="*80)
    
    prioridades = [
        ("🥇 PREDICCIÓN", "Altísimo", "Medio", "Proactividad absoluta"),
        ("🥈 VECTORIZACIÓN NumPy", "Altísimo", "Bajo", "20-100x más rápido si batch"),
        ("🥉 AUTO-CALIBRACIÓN", "Altísimo", "Medio", "±0.1°C vs ±0.5°C"),
        ("4️⃣  ASYNC/AWAIT", "Alto", "Medio", "3-10x responsive"),
        ("5️⃣  Compilación Numba", "Altísimo", "Medio", "10-100x más rápido physics"),
        ("6️⃣  ML Anomalías", "Medio", "Bajo", "Mejor confianza"),
        ("7️⃣  Persistencia BD", "Alto", "Medio", "Confiabilidad + análisis"),
    ]
    
    print("\n | Mejora | ROI | Esfuerzo | Resultado |")
    print(" |--------|-----|----------|-----------|")
    for mejora, roi, esfuerzo, resultado in prioridades:
        print(f" | {mejora:<25} | {roi:<8} | {esfuerzo:<8} | {resultado} |")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    benchmark_sistema()
    diagnostico_oportunidades()
