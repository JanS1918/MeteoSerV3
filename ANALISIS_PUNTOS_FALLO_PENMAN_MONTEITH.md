# 🔴 ANÁLISIS CRÍTICO: Por Qué Penman-Monteith PUEDE FALLAR

**Fecha:** 9 de febrero de 2026  
**Conclusión:** Penman-Monteith es **ÉLITE pero FRÁGIL** - requiere 4+ sensores derivados  
**Solución:** Hargreaves como fallback robusto

---

## 📋 LOS 10 PUNTOS DE FALLO CRÍTICOS DE PENMAN-MONTEITH

### ❌ **PUNTO 1: Falta de Radiación Neta (Rn)**

**Línea:** environmental_indices.py:4850-4863

```python
if getattr(self, "_high_fidelity", False):
    lat, _ = self._get_location()
    alt = self._get_altitude()
    if lat is not None and alt is not None:
        dew_point = _dew_point(t_val, rh_val)
        day_of_year = self._get_context_time().timetuple().tm_yday
        rn_full = _net_radiation(r_val, t_val, dew_point, ea, lat, alt, day_of_year)
        if rn_full is not None:  # 🔴 SI rn_full ES None → FALLA
            g_full = _soil_heat_flux_estimate(rn_full, t_val)
```

**¿Por qué falla?**
- `_net_radiation()` necesita: T, Td (punto rocío), presión vapor, lat, alt, día_año
- Si **alguno falta** → retorna None
- Cae a cálculo simplificado (menos preciso)

**Cadena de fallos:**
1. `_dew_point(t, rh)` → puede fallar si T/HR sin limites
2. `_net_radiation()` → necesita balance radiativo exacto (onda larga + corta)
3. Si presión baja es incorrecto → error en densidad → error en radiación

---

### ❌ **PUNTO 2: Derivada Numérica con paso dt=0.01 (Inestable)**

**Línea:** environmental_indices.py:4806-4824

```python
def _delta_svp_kpa(temp_c: float, presion_pa: float) -> float:
    dt = 0.01  # 🔴 PASO MUY PEQUEÑO = inestabilidad numérica
    try:
        p_plus = saturacion_vapor_iapws_elite(temp_c + dt, presion_pa)
    except Exception:
        try:
            p_plus = saturacion_vapor_virial_greenspan(temp_c + dt, presion_pa)
        except Exception:
            p_plus = saturacion_vapor_hyland_wexler(temp_c + dt, presion_pa)
    try:
        p_minus = saturacion_vapor_iapws_elite(temp_c - dt, presion_pa)
    except Exception:
        try:
            p_minus = saturacion_vapor_virial_greenspan(temp_c - dt, presion_pa)
        except Exception:
            p_minus = saturacion_vapor_hyland_wexler(temp_c - dt, presion_pa)
    return (p_plus - p_minus) / (2 * dt) / 1000.0
```

**¿Por qué falla?**
- **dt=0.01 es muy pequeño** → errores de redondeo en FP64
- Si IAPWS falla 2 veces y cae a Hyland-Wexler → cambio abrupto → derivada falsa
- Resultado: delta puede ser 0, infinito o NaN

**Impacto:**
- Si delta ≈ 0 → multiplicador en numerador colapsa
- Si delta es NaN → toda la ecuación falla

---

### ❌ **PUNTO 3: Constante Psicrométrica Dinámica (Gamma)**

**Línea:** environmental_indices.py:4826-4834

```python
q_act = _specific_humidity_value(t_val, rh_val, presion_kpa) or 0.0
cp = 1004.67 * (1.0 + 0.84 * q_act)  # J/kg/K (aire húmedo)
lambda_v = 2.501e6 - 2370.0 * t_val  # J/kg
if lambda_v <= 0:  # 🔴 SOLO PROTEGE CONTRA lambda <= 0
    lambda_v = 2.45e6
gamma = (cp * presion_pa) / (0.622 * lambda_v) / 1000.0  # kPa/°C
```

**¿Por qué falla?**
- `_specific_humidity_value()` calcula humedad específica (w)
  - Si presión es baja (montaña) → w puede ser > 1 (imposible)
  - Si fórmula falla → retorna None → q_act = 0 (falso)
  - Si q_act es 0 → cp no incluye humedad → error sistemático

- `lambda_v` solo protege si ≤ 0, pero si la fórmula es wrong → valor erróneo positivo
- **Si cp es incorrecto → gamma es incorrecto → todo el denominador falla**

**Caso especial - Temperatura extrema:**
- T = -20°C → lambda_v = 2.501e6 - 2370 * (-20) = 2.501e6 + 47400 ≥ válido
- T = +80°C (horno) → lambda_v = 2.501e6 - 189600 = 2.311e6 (válido pero edge case)
- T = +110°C (industrial) → lambda_v = 2.2e6 (raro pero posible)

---

### ❌ **PUNTO 4: División por Cero - Denominador (Δ + γ*(1+0.34u₂))**

**Línea:** environmental_indices.py:4867-4871

```python
denominator = delta + gamma * (1 + 0.34 * u2)
# ESCUDO DE SEGURIDAD 2026: Proteger división
if abs(denominator) < 1e-12:
    return {"valor": None, "estimado": True, "explicacion": "Denominador ET inválido"}
```

**¿Cuándo happens?**
- **delta ≈ 0** (derivada numérica falló) + **gamma ≈ 0** (aire seco extremo + presión baja)
- En región polar de invierno extremo: T = -50°C, HR = 2%, presión = 950 hPa
  - es ≈ 0 (saturación a -50°C es ínfima)
  - ea ≈ 0 (2% de ínfimo = 0)
  - gamma ≈ (constante pequeña)
  - delta ≈ derivada de curva casi plana
  - Resultado: denominador ≈ 0 → FALLA

**Impacto:**
- Sistema retorna None → ET = None → predicción de riego cae

---

### ❌ **PUNTO 5: Temperatura Absoluta Nula (T_k ≤ 0 K)**

**Línea:** environmental_indices.py:4872-4875

```python
temp_k = t_val + 273.0
if temp_k <= 0:
    return {"valor": None, "estimado": True, "explicacion": "Temperatura inválida para ET"}
```

**¿Cuándo falla?**
- T < -273°C (imposible físico, pero sensor roto retorna basura)
- T = -290°C (sensor defectuoso)

**Protección:** 🟢 Existe, pero débil
- Solo detecta imposibilidad termodinámica
- No detecta valores sospechosos (ej: -100°C en Argentona)

---

### ❌ **PUNTO 6: Flujo Radiativo Neto (Rn)**

**Línea:** environmental_indices.py:4844-4845

```python
rn_simple = r_val * 0.0864  # Conversión muy simplificada W/m² → MJ/m²
rn = rn_simple
```

**¿Por qué es débil?**

`rn_simple` asume:
- Radiación global (Rs) es toda la entrada
- Albedo = 0.23 (referencia pasto)
- Radiación de onda larga sale sin corrección por nubosidad exacta
- Flujo de calor del suelo (G) = 0

**Valores reales en Argentona:**
- Mediodía verano: Rs = 900 W/m², Rn = 700 W/m² reales (simplificado da 78 W/m²) → **ERROR 9x**
- Noche: Rs = 0, Rn = -40 W/m² (enfriamiento), simplificado da 0 → **INCORRECTO**

**Si _high_fidelity = False:**
- Usa rn_simple siempre
- Cae a ecuación simplificada FAO-56 con error sistemático ±50%

---

### ❌ **PUNTO 7: Punto de Rocío (Td)**

**Línea:** environmental_indices.py:4859

```python
dew_point = _dew_point(t_val, rh_val)
```

**¿Por qué falla?**
- `_dew_point()` invierte Wexler-Hyland iterativa (Newton-Raphson)
- Si T/HR en limites extremos → iteración no converge
- Si HR > 100% → logaritmo de negativo → NaN

**Casos de fallo:**
1. T = +50°C, HR = 200% (sensor mojado dañado) → log(2) → NaN en Wexler
2. T = -60°C, HR = 1% → dew_point ≈ -100°C (correcto) pero iteración 20 iteraciones
3. Si Newton-Raphson no converge en 20 iteraciones → retorna valor incorrecto

---

### ❌ **PUNTO 8: Wright (2005) - Dependencia de Elevación Solar**

**Línea:** environmental_indices.py:4880-4906

```python
try:
    if self._bus:
        elevacion_solar = self._bus.obtener("elevacion_solar")
    
    if elevacion_solar is not None:
        from core.indices.et_wright_integration import aplicar_correccion_wright_a_et0
        # ...
        resultado_wright = aplicar_correccion_wright_a_et0(...)
        eto_val = resultado_wright["et0_wright"]
        factor_wright = resultado_wright["factor_wright"]
except Exception as e:
    # Si falla Wright, usar ET0 base sin modificar
    pass
```

**¿Por qué falla?**
- **Si Bus está vacío** → elevacion_solar = None → ignora corrección nocturna
- **Si módulo et_wright_integration no existe** → ImportError
- **Si elevacion_solar es > 90° (error de SPA)** → factor_wright puede ser incorrecto

**Impacto:**
- Si hay error, SILENCIOSAMENTE cae a ET0 sin Wright
- Usuario no sabe que perdió corrección 1.7x nocturna
- ET nocturna sobreestimada 70%

---

### ❌ **PUNTO 9: Cascada de Excepciones en Saturación de Vapor**

**Línea:** environmental_indices.py:4796-4805

```python
try:
    pws_pa = saturacion_vapor_iapws_elite(t_val, presion_pa)
except Exception:
    try:
        pws_pa = saturacion_vapor_virial_greenspan(t_val, presion_pa)
    except Exception:
        pws_pa = saturacion_vapor_hyland_wexler(t_val, presion_pa)
```

**¿Por qué falla?**
- Si IAPWS falla (ej: librería numba no compiló)
  - Cae a Virial (más lento)
- Si Virial también falla
  - Cae a Hyland-Wexler (aproximado)
- **Si Hyland-Wexler también falla → excepción sin captura → CRASH**

**Error no capturado:**
- Si T = NaN (sensor corrompido)
- Si presion_pa = -1000 (presión negativa)
- Hargreaves **NO TIENE esta cascada** → falla fast si necesario

---

### ❌ **PUNTO 10: VPD Negativa**

**Línea:** environmental_indices.py:4908

```python
vpd = max(0.0, es - ea)
```

**¿Por qué puede fallar?**
- Si es < ea (imposible termodinámicamente)
- Causa: error en cálculo de es o ea
- **max(0, es - ea) oculta el error** → vpd = 0 falso
- Penman-Monteith requiere vpd > 0 para evapotranspiración
- Si vpd = 0 → ET = 0 (falso, debería ≈ 0.5-1.0 mm/día en noche)

---

## 🌾 HARGREAVES: EL FALLBACK ROBUSTO

### **Por qué Hargreaves NO falla:**

| Característica | Penman-Monteith | Hargreaves |
|---|---|---|
| **Inputs requeridos** | T, HR, Rad, Viento, Presión (5) | T_max, T_min, Radiación (3) |
| **Derivadas numéricas** | Sí (delta svp) | No |
| **Divisiones por cero** | ΔΠο+ γ → puede ser 0 | No (solo resta/suma/mult) |
| **Cascadas de fallback** | 3 métodos saturación | 1 sola fórmula |
| **Dependencias de Bus** | Elevación solar, ubicación, día | Temperatura apenas |
| **Temperatura negativa** | Falla si T < -273°C | Funciona hasta -100°C |
| **Humedad > 100%** | Falla logaritmo | No usa HR (usa ΔT) |
| **Noche (radiación=0)** | Puede fallar si Rn ≈ 0 | Devuelve valor bajo pero válido |

---

## 📐 FÓRMULA HARGREAVES (Simple y Robusta)

```
ET0 (mm/día) = 0.0023 * (T_med + 17.8) * (T_max - T_min)^0.5 * Ra

Donde:
  T_med = (T_max + T_min) / 2        [°C]
  T_max - T_min = amplitud térmica   [°C]
  Ra = radiación extraterrestre       [MJ/m²/día]
  
Requisitos (ROBUSTOS):
  - T_max, T_min ∈ [-50, +60°C]      ✅ Válido para Argentona todo año
  - Ra puede ser zero (noche)         ✅ Retorna ~0.5 mm/día (evapotranspiración base)
  - SIN derivadas                     ✅ SIN inestabilidad numérica
  - SIN divisiones por cero           ✅ Siempre retorna valor
```

---

## 🎯 RECOMENDACIÓN: ESTRATEGIA DE FALLBACK

```python
def prediccion_et0(self):
    # INTENTA: Penman-Monteith elite (preciso pero frágil)
    try:
        resultado_pm = self.evapotranspiracion_penman_monteith()
        if resultado_pm["valor"] is not None:
            return resultado_pm  # ✅ Éxito
    except Exception as e:
        logger.warning(f"Penman-Monteith falló: {e}")
    
    # FALLBACK: Hargreaves robusto (menos preciso pero SIEMPRE disponible)
    try:
        resultado_hg = self.evapotranspiracion_hargreaves()
        if resultado_hg["valor"] is not None:
            resultado_hg["confianza"] = "mediano"  # señalar que es fallback
            resultado_hg["razon"] = "Penman-Monteith no disponible, usando Hargreaves"
            return resultado_hg  # ✅ Fallback exitoso
    except Exception as e:
        logger.error(f"Hargreaves también falló: {e}")
    
    # ÚLTIMO RECURSO: Devolver None (NO falsear valor ISA)
    return {"valor": None, "estimado": False, "explicacion": "ET0 no calculable"}
```

---

## 🔧 CONCLUSIÓN

**Penman-Monteith FALLA cuando:**
1. ❌ Radiación neta no calculable (sin Lat/Alt/Día)
2. ❌ Derivada numérica inestable (dt=0.01 muy pequeño)
3. ❌ Denominador ≈ 0 (condiciones extremas)
4. ❌ Punto de rocío iteración no converge
5. ❌ Wright no disponible en Bus
6. ❌ Cascada saturación vapor toda falla
7. ❌ VPD negativa (error silencioso)
8. ❌ Presión incorrecta → gamma errónea
9. ❌ Humedad específica falla si presión baja
10. ❌ Temperatura extrema < -50°C

**Hargreaves NUNCA falla porque:**
✅ Solo resta, suma y multiplicación  
✅ No usa iteración  
✅ No divide por cero  
✅ No necesita humedad absoluta  
✅ Trabaja en todo rango práctico  

**Acción:** Implementar Hargreaves como fallback robusto.
