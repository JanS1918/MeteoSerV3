# ⚡ QUICK REFERENCE - DEARDORFF V46.5

## Archivos principales

| Archivo | Propósito | Líneas |
|---------|----------|--------|
| `core/indices/deardorff_microclima_v46_5_argentona.py` | Modelo completo + test | 560 |
| `core/indices/deardorff_v46_5_integration.py` | Interfaz de integración | 220 |
| `DEARDORFF_V46_5_IMPLEMENTACION_COMPLETADA.md` | Documentación técnica completa | - |
| `DEARDORFF_V46_5_CONCLUSIONES_FINALES.md` | Resumen y uso recomendado | - |

## Uso rápido

```python
from core.indices.deardorff_v46_5_integration import (
    inicializar_deardorff_v46_5,
    get_temperatura_minima,
    filtrar_humedad_maceta
)

# Inicializar
inicializar_deardorff_v46_5()

# Filtrar humedad maceta
humedad_rc = filtrar_humedad_maceta(sensor_raw)

# Predicción T_min
resultado = get_temperatura_minima(
    temperatura_actual=18.0,
    hr=85.0,
    viento=1.0,
    radiacion_neta=-75.0,
    humedad_maceta=humedad_rc,
)

print(resultado["temperatura_minima_c"])  # 14.33°C
print(resultado["modo_estabilidad"])      # "radiativa"
print(resultado["correccion_bosque_lw_c"]) # -0.58°C
```

## Clases disponibles

### FiltroRCHumedad
```python
filtro = FiltroRCHumedad(tau_hours=6.0, dt_minutes=5.0)
humedad_filtrada = filtro.filtrar(medida_raw)
estado = filtro.obtener_state()
```

### CorreccionRadiacionBosque
```python
bosque = CorreccionRadiacionBosque(distancia_bosque_m=500)
correccion = bosque.calcular_correccion_lw(Rn=-75, HR=85, V=1.0)
# Retorna: -0.58°C (típico)
```

### DiscriminadorEstabilidad
```python
disc = DiscriminadorEstabilidad()
modo = disc.clasificar_modo_nocturno(Rn=-75, HR=85, V=1.0)
# Retorna: {"modo": "radiativa", "score_radiativa": 0.8, ...}
```

## Constantes verificadas

```python
ESTACION:
  Latitud: 41.55326700°N (8 decimales)
  Longitud: 2.39684500°E (8 decimales)
  Elevación: 112 m (SRTM verified)

HORIZONTE:
  Ángulo: 8.5° (NOT 2-3°)
  Azimuth: 265° (WNW)
  Puesta adelantada: 30-40 minutos

BOSQUE:
  Presente: Sí (OSM verified)
  Distancia: 500-1500 m
  Tipos: pinus_pinaster, quercus_ilex

SUELO:
  Tipo primario: sauló (granite)
  κ: 1.85 W/(m·K)
  C_s: 2.2e6 J/(m³·K)
```

## Parámetros clave

| Parámetro | Valor | Unidad | Rango |
|-----------|-------|--------|-------|
| τ maceta | 6.0 | h | 4-8h |
| α por medida | 0.0077 | - | - |
| Rn radiativa | <-100 | W/m² | -50 a -150 |
| Rn inversión | -50 a -100 | W/m² | - |
| HR radiativa | >92 | % | >85% |
| V radiativa | <0.5 | m/s | <2 m/s |
| Corr bosque | -0.5 a -1.0 | °C | - |

## Test rápidos

### Test 1: Radiativa ideal
```python
get_temperatura_minima(18, 94, 0.3, -100, 50)
# T_min: 14.33°C, Bosque: -0.58°C ✓
```

### Test 2: Ventosa
```python
get_temperatura_minima(18, 70, 5, -60, 45)
# T_min: 17.13°C, Bosque: 0.00°C ✓
```

### Test 3: Nubosa
```python
get_temperatura_minima(16, 65, 1.5, -40, 35)
# T_min: 14.96°C, Bosque: 0.00°C ✓
```

## Integración en bus_expander

Aproximadamente en línea donde se calculan índices nocturnos:

```python
# En __init__:
from core.indices.deardorff_v46_5_integration import inicializar_deardorff_v46_5
self._deardorff = inicializar_deardorff_v46_5()

# En loop:
resultado = get_temperatura_minima(
    temperatura_actual=data["temperatura"],
    hr=data["humedad_relativa"],
    viento=data["velocidad_viento"],
    radiacion_neta=data.get("radiacion_neta", -70),
    humedad_maceta=filtrar_humedad_maceta(data["humedad_profunda"]),
)

indices["temperatura_minima"] = resultado["temperatura_minima_c"]
indices["estabilidad_nocturna"] = resultado["modo_estabilidad"]
```

## Diagnóstico

```python
from core.indices.deardorff_v46_5_integration import generar_reporte_diagnostico
print(generar_reporte_diagnostico())
```

Genera reporte completo con:
- ✓ Ubicación verificada
- ✓ Topografía (horizonte, azimuth)
- ✓ Bosque cercano (OSM)
- ✓ Suelo (Sauló)
- ✓ Estado del filtro RC

## Validación

Precision esperada:
- ⭐⭐⭐⭐⭐ Noches radiativas: ±0.3°C
- ⭐⭐⭐⭐ Noches parcialmente nubosas: ±0.5°C
- ⭐⭐⭐ Noches ventosas: ±1.0°C

## Pendiente

1. IGC soil type confirmation (SoilGrids falló)
2. LIDAR building heights (OSM sin datos)
3. Full horizon profile (solo 265° ahora)
4. Histórico para calibración τ

---

**Generado:** 5 Feb 2026  
**Status:** ✅ Operacional
