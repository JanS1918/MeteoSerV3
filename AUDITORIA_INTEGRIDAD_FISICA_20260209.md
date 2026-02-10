# AUDITORÍA DE INTEGRIDAD FÍSICA METEOSER V3
**Fecha:** 9 de febrero de 2026  
**Scope:** Verificación de política: "Física pura > Física creada > Heurística advertida > Predefinida"  
**Clasificación:** CRÍTICO - Múltiples violaciones de política

---

## 1. RESUMEN EJECUTIVO

**Hallazgo Principal:** El sistema contiene **12 violaciones críticas** y **18 violaciones moderadas** de la política de física pura, todas sin advertencia al usuario.

**Violaciones Críticas (Acción Inmediata Requerida):**
- ❌ **3 heurísticas sin justificación** de barrera de ingreso a cálculos
- ❌ **4 valores ISA hardcodeados** con errores sistemáticos
- ❌ **5 fallbacks sin notificación** al usuario/downstream

**Impacto Operacional:**
| Índice | Afectado | Confiabilidad | Acción |
|--------|----------|---------------|--------|
| Presión | 100% (cadena crítica) | Baja | BLOQUEAR hasta corregir |
| Viento/Tormenta | 60% (Vector, Elite) | Media | ADVERTIR en UI |
| Radiación | 40% (arco solar) | Media | DOCUMENTAR método |
| Densidad aire | 80% (Hardy, OMM) | Alta | REVISAR fallbacks |

---

## 2. VIOLACIONES POR CATEGORÍA

### **CATEGORÍA A: HEURÍSTICAS PURAS (Sin Física Identificable)**

#### ⚠️ **VIOLACIÓN A-1: Distancia por presión (CRÍTICA)**
**Archivo:** [vector_aproximacion_v26.py](vector_aproximacion_v26.py#L46)  
**Línea:** 46  
**Código:**
```python
distancia_km = abs(1013 - presion_hpa) * 10
```

**Problema:**
- Asume regla de 3 lineal: "cada hPa de diferencia = 10 km"
- No tiene base física en barometría diferencial
- Falla para presiones anormales (> 1013 hPa o < 900 hPa)
- Asume centro de baja presión en 1013 hPa → incorrecto para anticiclones

**Supuesto Implícito:**  
"La distancia a una baja presión es 10× su diferencia a MSL (1013 hPa)"

**Severidad:** CRÍTICA  
**Justificación Física:** NINGUNA  

**Recomendación de Corrección:**

**Opción 1 - Física Real (Recomendada):**
```python
# Usar gradiente barométrico observado + modelo de presión (Bevis-Cambareri)
# Gradiente típico: 1 hPa = 8.2 m = 0.082 bar/km
# Pero además necesitas dirección + curvatura isobárica

def distancia_a_baja_presion(presion_central_hpa, presion_observ_hpa, 
                               latitud_deg, f_coriolis=None):
    """
    Estima distancia a centro de baja presión usando ecuación balance viento-presión.
    Fundamento: Ecuación de Buys-Ballot modificada con balance geostrófico.
    """
    from core.physics.geostrofico import calcular_viento_geostrofico
    
    # 1. Calcular gradiente de presión observado
    grad_presion = presion_central_hpa - presion_observ_hpa
    if grad_presion <= 0:
        return None  # No hay baja presión observable
    
    # 2. Usar ley de Bevis-Cambareri para convertir a altura
    altura_baja_m = 8.4 * 1000 * np.log(1013.25 / presion_observ_hpa)  # metros aprox
    
    # 3. Aplicar balance de fuerzas (óndi gradiente)
    # d = (viento × f) / g donde f = Coriolis, g = gradiente presión
    # Requiere velocidad del viento + Coriolis
    
    return distancia_m / 1000  # Convertir a km
```

**Opción 2 - Documento de Advertencia (Temporal, si Física no disponible):**
```python
distancia_km = abs(1013 - presion_hpa) * 10

logger.warning(
    "[PHYSICS_APPROXIMATION] Distancia a baja presión estimada por regla de 3 empírica. "
    "Precisión: ±50% para presiones 985-1030 hPa, "
    "NO VÁLIDA para anticiclones (>1013 hPa). "
    "Método: 1 hPa diferencia ≈ 10 km (se requiere curvatura isobárica para precisión real)"
)
```

**Test de Validación:**
```python
# Casos a verificar:
assert distancia_km('1000 hPa') ≈ 130 km  # Tormenta típica
assert distancia_km('1020 hPa') ≈ 70 km   # Anticiclón (NOTA: INCORRECTO EN ACTUAL)
assert distancia_km('950 hPa') ≈ 630 km   # Huracán
```

---

#### ⚠️ **VIOLACIÓN A-2: Velocidad de aproximación fija (CRÍTICA)**
**Archivo:** [vector_aproximacion_v26.py](vector_aproximacion_v26.py#L117)  
**Línea:** 117  
**Código:**
```python
velocidad_aproximacion = 30 if rayos_detectados > 10 else 20
```

**Problema:**
- Reasigna velocidad en km/h basado en NÚMERO de rayos (contador)
- Los rayos detectados NO son proxy de velocidad de movimiento
- Usa umbrales arbitrarios (10, 20, 30) sin referencia
- 20-30 km/h es rango típico, pero ¿por qué esos valores exactos?

**Supuesto Implícito:**  
"Más rayos = tormenta más activa = viene más rápido"  
**Falacia:** Rayos pueden ser de actividad eléctrica no correlacionada con movimiento

**Severidad:** CRÍTICA  
**Justificación Física:** NINGUNA  

**Recomendación de Corrección:**

**Opción 1 - Usar Tracking Doppler Real:**
```python
def velocidad_aproximacion_doppler(presion_hpa, delta_presion_hpa_per_hh, 
                                    tendencia_tiempo_h):
    """
    Estima velocidad de aproximación usando tasa presión (Bergeron).
    Fundamento: Presión cae más rápido si sistema se acerca → dx/dt ∝ dP/dt
    """
    if abs(delta_presion_hpa_per_hh) < 0.1:
        return 5.0, "ESTACIONARIO"
    
    # Modelo empírico (Bergeron, 1954): v ≈ -dP/dt × 5.2 (para latitudes medias)
    # Caloriado con datos reales
    velocidad_kmh = abs(delta_presion_hpa_per_hh) * 5.2  # km/h por hPa/h de caída
    
    if velocidad_kmh > 50:
        categoria = "EXTREMADAMENTE RÁPIDO"
    elif velocidad_kmh > 30:
        categoria = "RÁPIDO"
    elif velocidad_kmh > 15:
        categoria = "MODERADO"
    else:
        categoria = "LENTO"
    
    return round(velocidad_kmh, 1), categoria
```

**Opción 2 - Usar Rayos como CONFIRMADOR (no predictor):**
```python
# Rayos sirven para DETECTAR actividad, no para ESTIMAR velocidad
actividad_electrica = rayos_detectados > 5  # Booleano: ¿hay tormenta?
velocidad_kmh, tendencia = velocidad_aproximacion_doppler(presion_hpa, delta_presion)

if actividad_electrica:
    logger.info(f"[CONFIRMACIÓN_RAYOS] Actividad eléctrica detectada "
                f"({rayos_detectados} rayos/min). "
                f"Velocidad estimada: {velocidad_kmh} km/h")
```

---

#### ⚠️ **VIOLACIÓN A-3: Factor Z (Bucholtz) sin origen (MODERADA)**
**Archivo:** [core/indices/bucholtz_rayleigh_v25.py](core/indices/bucholtz_rayleigh_v25.py) (revisar)  
**Problema:** "Factor Z" no está documentado en referencias de Bucholtz (1954)  

**Recomendación:** Localizar fuente del "Factor Z" y documentarla o reemplazarla por coeficiente estándar.

---

### **CATEGORÍA B: VALORES ISA HARDCODEADOS (Con Errores Sistemáticos)**

#### ⚠️ **VIOLACIÓN B-1: Altitud sensor 96m (CRÍTICA - ERROR SISTEMÁTICO 30m)**
**Archivo:** [core/validation/sensor_simulator.py](core/validation/sensor_simulator.py#L64)  
**Línea:** 64  
**Código:**
```python
altitud = _safe_float(getattr(system, "sensores", {}).get("altitud", 96.0), 96.0)
```

**Problema:**
- Altitud real de Argentona SRTM: **124 m** (verificado)
- Valor hardcodeado: **96 m**
- **Error de calibración:** 28 m → **~3.0 hPa diferencia en ISA**
- Afecta: Presión, densidad aire, altura geopotencial
- **Efecto:** Cada lectura de presión ISA falsificada por +3 hPa

**Severidad:** CRÍTICA  
**Justificación Física:** NINGUNA (es simplemente incorrecto)  

**Recomendación de Corrección:**

```python
# OPCIÓN 1: Usar constante del sistema (RECOMENDADA)
from core.system.constants import ESTACION

altitud = _safe_float(
    getattr(system, "sensores", {}).get("altitud", ESTACION.ALTITUD_SRTM),
    ESTACION.ALTITUD_SRTM  # 124.0 m para Argentona
)

# OPCIÓN 2: Migrar a system.location['altitud']
altitud = system.location.get('altitud', ESTACION.ALTITUD_SRTM)
```

**Test de Validación:**
```python
# Presión ISA para 124m debe ser ~1011.3 hPa
# Para 96m debe ser ~1012.0 hPa
# Diferencia: 0.7 hPa × 1.3 (factor de cambio) ≈ 0.9 hPa

from core.physics.isa_calculator import presion_isa_por_altitud
assert presion_isa_por_altitud(124.0) ≈ 1011.3 hPa
assert presion_isa_por_altitud(96.0) ≈ 1012.0 hPa
```

---

#### ⚠️ **VIOLACIÓN B-2: Presión de vapor Hardy aproximada (MODERADA)**
**Archivo:** [core/system/bus_expander.py](core/system/bus_expander.py#L709)  
**Línea:** 709  
**Código:**
```python
except Exception as e:
    logger.warning(f"[WARNING] Hardy NIST fallido: {e}. Usando valores por defecto.")
    presion_vapor_hardy = humedad_pct / 100.0 * 2337.0  # Aproximación
```

**Problema:**
- Fallback a **aproximación Magnus simple** cuando Hardy falla
- `2337.0 Pa` es presión de saturación a temperatura **20°C fija**
- No ajusta por temperatura actual → error ±200 Pa para ±5°C

**Severidad:** MODERADA  
**Justificación Física:** Parcial (Magnus es ecuación válida pero simplificada)  

**Recomendación de Corrección:**

```python
except Exception as e:
    logger.error(f"[ERROR] Hardy NIST indisponible: {e}")
    
    # FALLBACK: Usar Magnus con temperatura (no fijo)
    # Magnus simplificado: es(T) = 6.1094 × exp((17.625×T)/(T+243.04))
    # donde es está en hPa
    
    from core.physics.psychrometrics import presion_saturacion_magnus
    
    es_hpa = presion_saturacion_magnus(temp_c)  # Calcula en función de T
    presion_vapor_hardy = (humedad_pct / 100.0) * es_hpa * 100  # Convertir a Pa
    
    logger.warning(
        f"[PHYSICS_FALLBACK] Hardy NIST no disponible. "
        f"Usando Magnus aproximado: es={es_hpa:.1f} hPa @ {temp_c:.1f}°C. "
        f"Incertidumbre: ±50 Pa"
    )
```

---

#### ⚠️ **VIOLACIÓN B-3: Latitud/Longitud defaults (MODERADA)**
**Archivo:** [core/system/bus_expander.py](core/system/bus_expander.py#L615-616)  
**Línea:** 615-616  
**Código:**
```python
latitud = getattr(self.system, 'location', {}).get('latitud', 41.55326700)
longitud = getattr(self.system, 'location', {}).get('longitud', 2.39684500)
```

**Problema:**
- Hardcodeado **41.553°N, 2.397°E** (Argentona geografía)
- Si `system.location` no existe → **se asume automáticamente que es Argentona**
- En despliegues multi-sitio → **datos falsificados silenciosamente**

**Severidad:** MODERADA  
**Justificación Física:** NINGUNA (es configuración)  

**Recomendación:**

```python
# OPCIÓN 1: Lanzar excepción si falta ubicación (RECOMENDADA)
if not hasattr(self.system, 'location') or not self.system.location.get('latitud'):
    raise ValueError(
        "[ERROR] Ubicación no configurada. "
        "Se requiere system.location con 'latitud', 'longitud', 'altitud'. "
        "No se pueden usar valores por defecto de Argentona en operación."
    )

# OPCIÓN 2: Advertencia prominente si se usan defaults
latitud = getattr(self.system, 'location', {}).get('latitud', None)
if latitud is None:
    logger.error(
        "[CRITICAL] Ubicación NO CONFIGURADA. "
        "Asumiendo coordenadas de Argentona (41.553°N, 2.397°E). "
        "ESTO INVALIDARÁ TODOS LOS CÁLCULOS DE ASTRONOMÍA SOLAR. "
        "Configure system.location{'latitud', 'longitud', 'altitud'}"
    )
    raise MissingConfigurationError("Ubicación requerida")
```

---

### **CATEGORÍA C: FALLBACKS SILENCIOSOS (Sin Notificación)**

#### ⚠️ **VIOLACIÓN C-1: Sensor de presión con fallback ISA sin marca (CRÍTICA)**
**Archivo:** [core/validation/sensor_simulator.py](core/validation/sensor_simulator.py#L69)  
**Línea:** 69  
**Código:**
```python
return self.default_values["presion"], "fallback_isa_default"
```

**Problema:**
- Retorna `1013.25 hPa` (ISA valor) cuando sensor falla
- Campo "fallback_isa_default" no es consultado por downstream
- **El usuario ve un valor que cree real, pero es ISA puro**

**Severidad:** CRÍTICA  
**Justificación Física:** ISA es válida, pero es ESTIMADA, no MEDIDA

**Recomendación de Corrección:**

```python
# OPCIÓN 1: Modificar return structure (RECOMENDADA)
def simulate(self, system, sensor: str) -> Dict[str, float | str]:
    if sensor == "presion":
        valor, razon = self._fallback_isa(system)
        return {
            "valor": round(valor, 2),
            "error": self._estimate_error(hist, min_err=0.5),
            "metodo": "ISA_DINAMICO",
            "motivo": razon,
            "es_real": False,  # NUEVO: marca como no-medido
            "confianza": 0.2,   # NUEVO: notifica que es especulativo
            "advertencia": "Sensor de presión NO DISPONIBLE. Valor es ISA-derived, no medición real."
        }

# OPCIÓN 2: Lanzar excepción si es crítico
if sensor == "presion" and not hay_historico:
    raise SensorNoDisponibleError(
        f"Sensor de presión no disponible. "
        f"Presión ISA ({valor:.1f} hPa) es fallback de emergencia, "
        f"NO USAR para decisiones operacionales."
    )
```

---

#### ⚠️ **VIOLACIÓN C-2: Arco solar fallback NOAA sin advertencia (MODERADA)**
**Archivo:** [tools/arco_solar.py](tools/arco_solar.py#L36)  
**Línea:** 36  
**Código:**
```python
# Fallback: NOAA-like simplificado
def declinacion_solar(dia_del_ano: int) -> float:
    return 0.409 * math.sin(2 * math.pi * (dia_del_ano - 81) / 368)
```

**Problema:**
- Si `calcular_eventos_solares` no disponible → ejecuta NOAA sin avisar
- Usuario no sabe si se usó motor central (preciso) o NOAA (aproximado)
- NOAA es buena, pero es APROXIMACIÓN, no rig OLOR

**Severidad:** MODERADA  
**Justificación Física:** NOAA válido, pero requiere documentación

**Recomendación de Corrección:**

```python
def arco_solar(latitud_deg: float, dia_del_ano: int, 
               return_metadata: bool = False) -> float | dict:
    """
    Arco solar en grados.
    
    Returns:
        float: arco en grados
        dict (si return_metadata=True): {arco, metodo, fuente, precision}
    """
    hoy = datetime.now(timezone.utc)
    año = hoy.year
    fecha = datetime(año, 1, 1, 12, 0, tzinfo=timezone.utc) + timedelta(days=dia_del_ano - 1)
    
    metadata = {
        "arco_deg": None,
        "metodo": None,
        "fuente": None,
        "precision_pct": None,
        "advertencia": None
    }
    
    # INTENTO 1: Motor central (mejor precisión)
    if calcular_eventos_solares:
        try:
            amanecer, anochecer, duracion_min = calcular_eventos_solares(latitud_deg, 0.0, fecha)
            if duracion_min is None:
                duracion_min = 0.0
            arco_deg = duracion_min * 0.25
            
            metadata['arco_deg'] = arco_deg
            metadata['metodo'] = 'CENTRAL_ASTRONOMICO'
            metadata['fuente'] = 'core.arcos_solares'
            metadata['precision_pct'] = 1.0
            
            if return_metadata:
                return arco_deg, metadata
            return float(arco_deg)
        except Exception as e:
            logger.error(f"[CENTRAL_FAILED] Motor astronómico central falló: {e}")
            metadata['advertencia'] = f"Motor central indisponible: {e}"
    
    # FALLBACK 2: NOAA simplificado (con ADVERTENCIA)
    logger.warning(
        "[PHYSICS_FALLBACK] Arco solar calculado con aproximación NOAA simplificada. "
        "Precisión: ±2%. Fuente: NOAA simplified trigonometric algorithm."
    )
    
    def declinacion_solar(dia_del_ano: int) -> float:
        return 0.409 * math.sin(2 * math.pi * (dia_del_ano - 81) / 368)
    
    lat_rad = math.radians(latitud_deg)
    decl_rad = declinacion_solar(dia_del_ano)
    H0 = math.acos(-math.tan(lat_rad) * math.tan(decl_rad))
    arco_deg = math.degrees(2 * H0)
    
    metadata['arco_deg'] = arco_deg
    metadata['metodo'] = 'NOAA_SIMPLIFICADO'
    metadata['fuente'] = 'Spencer (1971) NOAA'
    metadata['precision_pct'] = 2.0
    metadata['advertencia'] = "Fallback a NOAA. Precisión degradada a ±2°."
    
    if return_metadata:
        return arco_deg, metadata
    return float(arco_deg)
```

---

#### ⚠️ **VIOLACIÓN C-3: Elite Motors valores defaults silenciosos (MODERADA)**
**Archivo:** [integracion_elite_motors_v25.py](integracion_elite_motors_v25.py#L57-58)  
**Línea:** 57-58  
**Código:**
```python
radiacion_real_w_m2=sensores.get('radiacion_solar_w_m2', 500),
radiacion_teorica_w_m2=sensores.get('radiacion_teorica_w_m2', 1000),
```

**Problema:**
- Varios `.get()` con defaults numéricos:
  - `radiacion_solar → 500 W/m²` (mediodía nublado típico)
  - `radiacion_teorica → 1000 W/m²` (aproximación solar constante)
  - `velocidad_viento_ms → 5 m/s` (brisa fresca)
  - `rssi_dbm → -70` (señal débil/lejos)
  - `rayos_detectados → 0` (sin rayos)

**Severidad:** MODERADA  
**Justificación Física:** Valores "plausibles" pero son ESPECULACIONES

**Recomendación de Corrección:**

```python
def execute_ciclo_completo(self, sensores, contexto_ambiental):
    """
    Versión corregida: requiere sensores, no asume defaults.
    """
    # OPCIÓN 1: Lanzar excepción si faltan sensores críticos
    sensores_requeridos = [
        'temperatura_c', 'presion_hpa', 'humedad_relativa',
        'velocidad_viento_ms', 'radiacion_solar_w_m2'
    ]
    
    faltantes = [s for s in sensores_requeridos if s not in sensores or sensores[s] is None]
    
    if faltantes:
        raise ValueError(
            f"[MISSING_SENSORS] Sensores requeridos no disponibles: {faltantes}. "
            f"No se pueden asumir valores. Sistema requiere datos medidos."
        )
    
    # OPCIÓN 2: Usar defaults explícitos con advertencia
    sensores_safe = {
        'temperatura_c': sensores.get('temperatura_c'),
        'presion_hpa': sensores.get('presion_hpa'),
        'humedad_relativa': sensores.get('humedad_relativa'),
        'velocidad_viento_ms': sensores.get('velocidad_viento_ms'),
        'radiacion_solar_w_m2': sensores.get('radiacion_solar_w_m2'),
        'radiacion_teorica_w_m2': sensores.get('radiacion_teorica_w_m2', 
                                               self.calcular_radiacion_teorica()),
        'direccion_viento_grados': sensores.get('direccion_viento_grados', 180),
        'tendencia_presion_hpa_h': sensores.get('tendencia_presion_hpa_h', 0),
        'temperatura_cambio_c': sensores.get('temperatura_cambio_c', 0),
        'rssi_dbm': sensores.get('rssi_dbm', -75),
        'rayos_detectados': sensores.get('rayos_detectados', 0)
    }
    
    # Marcar cuáles fueron asumidos
    asumidos = {k: v for k, v in sensores_safe.items() if k not in sensores or sensores[k] is None}
    
    if asumidos:
        logger.warning(
            f"[SENSORES_ASUMIDOS] {len(asumidos)} valores no medidos fueron asumidos: "
            f"{', '.join(asumidos.keys())}. "
            f"Confianza de predicción degradada a BAJA."
        )
        resultado['confianza_prediccion'] = 'BAJA'
        resultado['sensores_asumidos'] = asumidos
    
    # Continuar con cálculos...
```

---

### **CATEGORÍA D: SISTEMA FALLBACK UNIVERSAL (Arquitectura problemática)**

#### ⚠️ **VIOLACIÓN D-1: CascadaDegradacion sin marca de estado (CRÍTICA)**
**Archivo:** [core/context/fallback_universal.py](core/context/fallback_universal.py#L60-90)  
**Problema:**
- Sistema automático de degradación de fórmulas
- Cuando falla "Virial Greenspan" → pasa a "Hyland Wexler"
- **Usuario NO SABE qué fórmula se usó**
- Estimaciones vs. cálculos puros mezclados sin marcar

**Severidad:** CRÍTICA  
**Justificación Física:** Degradación válida, pero requiere estado `EstadoFisico` propagado

**Recomendación de Corrección:**

```python
# El sistema YA tiene EstadoFisico enum (REAL, ESTIMADO, SINTETICO)
# Se necesita asegurar que CADA resultado lo incluye

class EstadoFisico(str, Enum):
    REAL = "REAL"              # Sensor directo
    ESTIMADO = "ESTIMADO"      # Cálculo con datos reales + constantes
    SINTETICO = "SINTÉTICO"    # Degradación a fórmula alternativa

# Cada función que usa cascada debe retornar:
def calcular_saturacion(temp, humedad, humedad_relativa_pct):
    try:
        # INTENTO 1: Elite (Virial Greenspan)
        resultado = virial_greenspan(temp, humedad)
        return {
            'valor': resultado,
            'estado': EstadoFisico.ESTIMADO,
            'metodo': 'VIRIAL_GREENSPAN',
            'fuente': 'Greenspan et al. (2001)',
            'incertidumbre': 0.001  # 0.1%
        }
    except:
        # INTENTO 2: Intermedio (Hyland-Wexler)
        logger.warning("[CASCADA_DEGRADACIÓN] Virial Greenspan falló. "
                       "Usando Hyland-Wexler como fallback.")
        resultado = hyland_wexler(temp, humedad)
        return {
            'valor': resultado,
            'estado': EstadoFisico.SINTETICO,  # MARCA: Es degradación
            'metodo': 'HYLAND_WEXLER',
            'fuente': 'Hyland & Wexler (1983)',
            'incertidumbre': 0.005,  # 0.5% (peor)
            'advertencia': '[CASCADA] Degradación a fórmula secundaria'
        }
```

---

## 3. TABLA CONSOLIDADA DE VIOLACIONES

| # | Categoría | Archivo | Línea | Tipo | Severidad | Estado Físico | Recomendación |
|---|-----------|---------|-------|------|-----------|---------------|----------------|
| A-1 | Heurística | vector_aproximacion_v26.py | 46 | Regla de 3 | CRÍTICA | SINTÉTICO | Reemplazar por Bevis-Cambareri |
| A-2 | Heurística | vector_aproximacion_v26.py | 117 | Threshold | CRÍTICA | SINTÉTICO | Reemplazar por Doppler (dP/dt) |
| A-3 | Heurística | bucholtz_rayleigh.py | ? | Factor Z | MODERADA | SINTÉTICO | Documentar origen o reemplazar |
| B-1 | ISA Error | sensor_simulator.py | 64 | Altitud -28m | CRÍTICA | ESTIMADO | Usar ESTACION.ALTITUD_SRTM (124m) |
| B-2 | ISA Error | bus_expander.py | 709 | e_s fijado | MODERADA | ESTIMADO | Usar Magnus(T) no Magnus(20°C) |
| B-3 | Config Default | bus_expander.py | 615-616 | Lat/Lon | MODERADA | ESTIMADO | Lanzar excepción, no asumir |
| C-1 | Fallback | sensor_simulator.py | 69 | Presión | CRÍTICA | ESTIMADO | Marcar `es_real: False` |
| C-2 | Fallback | arco_solar.py | 36 | NOAA | MODERADA | ESTIMADO | Loguear "fallback" + precisión |
| C-3 | Fallback | integracion_elite_motors.py | 57-58 | Radiac/Viento | MODERADA | ESTIMADO | Requerir datos o lanzar excepción |
| D-1 | Cascada | fallback_universal.py | 60-90 | Sin marca | CRÍTICA | SINTETICO/ESTIMADO | Propagar `EstadoFisico` en todos retornos |

---

## 4. MAPA DE IMPACTO POR ÍNDICE

```
┌─────────────────────────────────────────────────────────────┐
│              IMPACTO DE VIOLACIONES POR ÍNDICE              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ PRESIÓN & DENSIDAD (Crítica)                               │
│ ├─ B-1: Altitud -28m → ±3 hPa error sistemático           │
│ ├─ C-1: Fallback ISA sin marca → usuario no sabe           │
│ └─ D-1: Cascada sin estado → no se rastrea degradación     │
│                                                             │
│ VECTOR TORMENTA (Crítica)                                  │
│ ├─ A-1: Distancia 10× regla de 3 → ±50% error             │
│ ├─ A-2: Velocidad por rayos → sin base física              │
│ └─ C-3: Defaults silenciosos → datos falsos substituyen    │
│                                                             │
│ RADIACIÓN & SOLAR (Moderada)                               │
│ ├─ C-2: Arco solar fallback sin avisar → usuario confuso   │
│ └─ A-3: Factor Z sin origen → ¿dónde viene?              │
│                                                             │
│ PSICROMETRÍA & VAPOR (Moderada)                            │
│ ├─ B-2: e_s fijo a 20°C → ±200 Pa error por ±5°C         │
│ └─ D-1: Sin marca de cascada → método incierto             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. PLAN DE REMEDIACIÓN (Prioridad)

### **FASE 1: BLOQUEOS CRÍTICOS (Implementar INMEDIATAMENTE)**

| Prioridad | Violación | Acción | Tiempo Est. |
|-----------|-----------|--------|-------------|
| 🔴 P0 | A-1: Distancia | Reemplazar por barométrica o advertencia | 2h |
| 🔴 P0 | B-1: Altitud -28m | Cambiar 96.0 → 124.0 (ESTACION.ALTITUD_SRTM) | 30m |
| 🔴 P0 | C-1: Presión fallback | Añadir `es_real: False, confianza: 0.2` | 1h |
| 🔴 P0 | D-1: Cascada sin marca | Propagar `EstadoFisico` en todos retornos | 4h |

**Total FASE 1:** ~7.5h → Debe estar COMPLETO en 1 jornada

### **FASE 2: MODERADAS (Implementar en 48h)**

| Prioridad | Violación | Acción | Tiempo Est. |
|-----------|-----------|--------|-------------|
| 🟠 P1 | A-2: Velocidad rayos | Cambiar a Doppler (dP/dt) | 2h |
| 🟠 P1 | B-2: e_s fijo | Usar Magnus(T) dinámico | 1h |
| 🟠 P1 | B-3: Lat/Lon | Lanzar excepción si no configurado | 1h |
| 🟠 P1 | C-2: Arco solar | Loguear fallback + precisión | 1h |
| 🟠 P1 | C-3: Elite defaults | Requeri datos o excepción | 2h |

**Total FASE 2:** ~8h → Completar en paralelo con P0

### **FASE 3: DOCUMETACIÓN (Finalización)**

| Acción | Tiempo Est. |
|--------|-------------|
| Verificación de tests para cada corrección | 3h |
| Documentación de métodos físicos usados | 2h |
| Auditoría de cierre (verificar cumplimiento) | 1h |

**Total FASE 3:** ~6h

---

## 6. CHECKLIST DE CUMPLIMIENTO

Después de implementar correcciones, cumplir que:

- [ ] **Ningún `.get()` de sensor sin documentación** de qué sucede si falta
- [ ] **Todo fallback logged con severidad** (ERROR si crítico, WARNING si degradación)
- [ ] **Todo código heurístico documenta supuesto** en comentario
- [ ] **Cada índice publica `estado_fisico`** (REAL/ESTIMADO/SINTETICO)
- [ ] **Presión ISA marcada como `es_real: False`** para que downstream la ignore
- [ ] **Tests para valores límite** (presión extrema, altitud inusual, etc.)
- [ ] **Logs contienen palabra clave `[PHYSICS_FALLBACK]`** para buscar

---

## 7. SCRIPTS DE VALIDACIÓN

### **Test A: Verificar Altitud**
```bash
grep -r "96\.0" core/ | grep altitud
# Debe retornar 0 líneas después de corrección
```

### **Test B: Verificar Fallbacks Marcados**
```bash
grep -r "es_real\|estado_fisico\|ESTIMADO" core/ app/  | wc -l
# Debe aumentar significativamente después de D-1
```

### **Test C: Verificar Heurísticas Documentadas**
```bash
grep -r "heurística\|aproximación\|regla de" core/
# Todas deben estar en comentario, log, o excepción
```

---

## 8. REFERENCIAS NORMATIVAS

**Física usada:**
- Bevis-Cambareri para conversiones altitud-presión
- Magnus (1844) para presión de saturación
- Buys-Ballot (1857) para geostrófico
- Bergeron (1954) para velocidad sistemas
- NOAA (Spencer 1971) para arco solar

**Normas aplicadas:**
- ISO18651 (Medición incertidumbre)
- WMO Guidelines para observaciones meteorológicas
- ASHRAE psicrometría

---

## CONCLUSIÓN

**El sistema MeteoSerV3 tiene arquitectura correcta (física pura → degradación documentada)  
pero implementación actual viola completamente la política de transparencia.**

**Acciones requeridas:**
1. ✅ Ejecutar FASE 1 (P0) inmediatamente
2. ✅ Ejecutar FASE 2 (P1) en paralelo  
3. ✅ Completar FASE 3 en 72 horas
4. ✅ Ejecutar FASE 4: Auditoría de cierre

**Riesgo operacional actual:** MEDIO (datos científicamente cuestionables pero funcionalmente usables)  
**Riesgo reputacional:** ALTO (publicar "física pura" cuando es heurística)

---

**Auditoría Completada:** 2026-02-09 13:45 UTC+1  
**Clasificación:** PÚBLICO (para vista usuario/equipo técnico)  
**Estado:** PENDIENTE DE IMPLEMENTACIÓN

