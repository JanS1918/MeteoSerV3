# Arquitectura ENTERA + DESCOMPUESTA - V51 Lluvia Inminente

## Principio Fundamental

Cada métrica se publica EN DOS FORMAS:

1. **ENTERA:** Valor compuesto + metadatos completos (score final, ETA, confianza)
2. **DESCOMPUESTA:** Cada componente por separado para análisis granular

## Ejemplo Práctico: Alerta de Lluvia Inminente

### PUBLICACIÓN ENTERA
```python
bus.publicar(
    clave="alerta_lluvia_inminente_score",
    valor=72,                           # Score 0-100
    fuente="scheduler_v51",
    metadatos={
        "eta_minutos": 14,              # ETA comprendida
        "confianza": 0.85,              # Confianza global 0-1
        "modelo": "AlertaLluviaInmediata_V51"
    }
)
```
**Uso:** Para alertas rápidas, decisiones operacionales, UIs simplificadas

### PUBLICACIÓN DESCOMPUESTA
Cada componente se publica INDEPENDIENTEMENTE:

```python
# Componente GHI (radiación)
bus.publicar(
    clave="alerta_lluvia_componente_ghi_derivada",
    valor=-128.5,                       # dGHI/dt en W/m²/s
    fuente="scheduler_v51",
    metadatos={"unidad": "W/m²/s", "componente": "radiacion"}
)

bus.publicar(
    clave="alerta_lluvia_componente_ghi_score",
    valor=20,                           # Contribución a score final (0-25)
    fuente="scheduler_v51",
    metadatos={"rango": "0-25", "peso": 0.25}
)

# Componente Humedad
bus.publicar(
    clave="alerta_lluvia_componente_humedad_derivada",
    valor=2.8,                          # dHR/dt en %/min
    fuente="scheduler_v51",
    metadatos={"unidad": "%/min", "componente": "humedad"}
)

bus.publicar(
    clave="alerta_lluvia_componente_humedad_score",
    valor=15,                           # Contribución a score (0-15)
    fuente="scheduler_v51",
    metadatos={"rango": "0-15", "peso": 0.15}
)

# Componente Presión
bus.publicar(
    clave="alerta_lluvia_componente_presion_derivada",
    valor=-2.3,                         # dP/dt en hPa/h
    fuente="scheduler_v51",
    metadatos={"unidad": "hPa/h", "componente": "presion"}
)

bus.publicar(
    clave="alerta_lluvia_componente_presion_score",
    valor=25,                           # Contribución máxima (0-25)
    fuente="scheduler_v51",
    metadatos={"rango": "0-25", "peso": 0.25}
)

# Componente ΔT Solar
bus.publicar(
    clave="alerta_lluvia_componente_dt_solar_derivada",
    valor=0.3,                          # °C/min
    fuente="scheduler_v51",
    metadatos={"unidad": "°C/min", "componente": "dt_solar"}
)

bus.publicar(
    clave="alerta_lluvia_componente_dt_solar_score",
    valor=8,                            # Contribución (0-10)
    fuente="scheduler_v51",
    metadatos={"rango": "0-10", "peso": 0.10}
)

# Componente Sundqvist (microfísica)
bus.publicar(
    clave="alerta_lluvia_componente_sundqvist_probabilidad",
    valor=45.0,                         # Probabilidad % 
    fuente="scheduler_v51",
    metadatos={"unidad": "%", "componente": "sundqvist"}
)

bus.publicar(
    clave="alerta_lluvia_componente_sundqvist_score",
    valor=20,                           # Contribución (0-25)
    fuente="scheduler_v51",
    metadatos={"rango": "0-25", "peso": 0.25}
)

# Metadatos derivados
bus.publicar(
    clave="alerta_lluvia_eta_minutos",
    valor=14,                           # ETA descompuesta
    fuente="scheduler_v51",
    metadatos={"unidad": "minutos", "rango": "10-20"}
)

bus.publicar(
    clave="alerta_lluvia_confianza",
    valor=0.85,                         # Confianza descompuesta
    fuente="scheduler_v51",
    metadatos={"unidad": "0-1", "rango": "0.5-1.0"}
)
```

**Uso:** Para análisis científico, debugging, machine learning, visualización detallada

---

## Mapeo de Claves del Bus

### Nivel ENTERA (Score Compuesto)
| Clave Bus | Rango | Significado |
|-----------|-------|-------------|
| `alerta_lluvia_inminente_score` | 0-100 | Score final consolidado |
| `alerta_lluvia_eta_minutos` | 10-20 | Estimación tiempo lluvia |
| `alerta_lluvia_confianza` | 0.5-1.0 | Confianza predicción |

### Nivel DESCOMPUESTA (Componentes Individuales)

#### Radiación (GHI)
| Clave Bus | Unidad | Rango |
|-----------|--------|-------|
| `alerta_lluvia_componente_ghi_derivada` | W/m²/s | -∞ a +∞ |
| `alerta_lluvia_componente_ghi_score` | puntos | 0-25 |

#### Humedad
| Clave Bus | Unidad | Rango |
|-----------|--------|-------|
| `alerta_lluvia_componente_humedad_derivada` | %/min | -∞ a +∞ |
| `alerta_lluvia_componente_humedad_score` | puntos | 0-15 |

#### Presión
| Clave Bus | Unidad | Rango |
|-----------|--------|-------|
| `alerta_lluvia_componente_presion_derivada` | hPa/h | -∞ a +∞ |
| `alerta_lluvia_componente_presion_score` | puntos | 0-25 |

#### ΔT Solar
| Clave Bus | Unidad | Rango |
|-----------|--------|-------|
| `alerta_lluvia_componente_dt_solar_derivada` | °C/min | 0 a +∞ |
| `alerta_lluvia_componente_dt_solar_score` | puntos | 0-10 |

#### Sundqvist
| Clave Bus | Unidad | Rango |
|-----------|--------|-------|
| `alerta_lluvia_componente_sundqvist_probabilidad` | % | 0-100 |
| `alerta_lluvia_componente_sundqvist_score` | puntos | 0-25 |

---

## Ejemplo: Cómo Leer del Bus

### Lectura Simplificada (ENTERA)
```python
score = bus.consumir("alerta_lluvia_inminente_score", "mi_app")
if score > 70:
    eta = bus.consumir("alerta_lluvia_eta_minutos", "mi_app")
    print(f"Alerta lluvia en {eta} minutos")
```

### Lectura Detallada (DESCOMPUESTA)
```python
# Entender qué causó la alerta
score_ghi = bus.consumir("alerta_lluvia_componente_ghi_score", "mi_app")
score_p = bus.consumir("alerta_lluvia_componente_presion_score", "mi_app")
score_sundq = bus.consumir("alerta_lluvia_componente_sundqvist_score", "mi_app")

componentes = {
    "radiacion": score_ghi,
    "presion": score_p,
    "sundqvist": score_sundq
}

# Identificar factor dominante
factor_dominante = max(componentes, key=componentes.get)
print(f"Factor principal: {factor_dominante}")
```

---

## Arquitectura de Cálculo

### Flujo de Datos
```
[Sensores] 
    ↓
[Bus: ghi_w_m2, humedad, presion, dt_solar]
    ↓
[Calculador Indices - Scheduler]
    ├─ Calcular derivadas (dGHI/dt, dHR/dt, dP/dt)
    ├─ Evaluar Sundqvist (probabilidad lluvia)
    ├─ Calcular scores individuales (0-100)
    └─ Calcular score final ponderado
    ↓
[BUS: Publicación ENTERA + DESCOMPUESTA]
    ├─ ENTERA: alerta_lluvia_inminente_score + metadatos
    └─ DESCOMPUESTA:
        ├─ Componente GHI (derivada + score)
        ├─ Componente HR (derivada + score)
        ├─ Componente Presión (derivada + score)
        ├─ Componente ΔT (derivada + score)
        ├─ Componente Sundqvist (prob + score)
        ├─ ETA (minutos)
        └─ Confianza (0-1)
    ↓
[Consumidores]
    ├─ Alertas rápidas (solo score compuesto)
    ├─ Análisis científico (componentes)
    ├─ Machine Learning (histórico descompuesto)
    ├─ UIs (tanto entera como descompuesta)
    └─ APIs REST (filtro mostrar/ocultar según cliente)
```

---

## Opción 2: Derivadas Rápidas (1-2 min scheduler)

### PUBLICACIÓN ENTERA
```python
bus.publicar(
    clave="derivadas_resumen_rapido",
    valor={
        "derivada_ghi_w_m2_s": -78.5,
        "derivada_hr_porciento_min": 2.3,
        "derivada_presion_hpa_min": -1.2,
        "valor_ghi_actual_w_m2": 450,
        "valor_hr_actual_pct": 85,
        "valor_presion_actual_hpa": 1008,
        "puntos_historial": 18,
        "timestamp": "2026-02-11T00:50:51"
    },
    fuente="derivadas_rapidas_v51"
)
```

### PUBLICACIÓN DESCOMPUESTA
```python
# Radiación
bus.publicar("derivada_ghi_w_m2_s", -78.5)          # dGHI/dt
bus.publicar("valor_ghi_w_m2", 450)                 # GHI actual

# Humedad
bus.publicar("derivada_hr_porciento_min", 2.3)      # dHR/dt  
bus.publicar("valor_humedad_relativa_pct", 85)      # HR actual

# Presión
bus.publicar("derivada_presion_hpa_min", -1.2)      # dP/dt
bus.publicar("valor_presion_hpa", 1008)             # Presión actual
```

---

## Garantías del Sistema

✅ **Consistencia:** ENTERA y DESCOMPUESTA suman correctamente
✅ **Completitud:** Todas las claves se publican en cada ciclo
✅ **Rastreabilidad:** Cada métrica tiene fuente y timestamp
✅ **Granularidad:** Puedes usar solo lo que necesitas
✅ **Compatibilidad:** Versiones antiguas usan ENTERA, nuevas usan DESCOMPUESTA

---

## Guía para Desarrolladores

Cuando agregues un nuevo índice/métrica:

1. **Define la fórmula** en `core/indices/*.py`
2. **Crea función de cálculo** que retorne Dict con todos los componentes
3. **Publica ENTERA** en el bus (metros compuesto)
4. **Publica DESCOMPUESTA** cada componente por separado
5. **Documenta en metadatos** la unidad, rango, peso de cada parte
6. **Prueba** que ambas formas funcionen en tests

Ejemplo plantilla:
```python
def calcular_mi_indice(...):
    return {
        "score_final": 75,
        "componente_a": {
            "valor": 50,
            "score": 25,
            "peso": 0.33
        },
        "componente_b": {
            "valor": 40,
            "score": 30,
            "peso": 0.33
        },
        "componente_c": {
            "valor": 60,
            "score": 20,
            "peso": 0.33
        }
    }
```

---

## Status Implementación

✅ **Alerta Lluvia V51:** ENTERA + DESCOMPUESTA
✅ **Derivadas Rápidas:** ENTERA + DESCOMPUESTA  
✅ **Tests:** 11/11 scheduler + 13/13 derivadas = 24/24 PASS
✅ **Documentación:** Completa en lluvia_inminente_indices.py
✅ **Código Central:** core/indices/lluvia_inminente_indices.py
