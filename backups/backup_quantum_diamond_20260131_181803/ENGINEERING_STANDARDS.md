# ENGINEERING STANDARDS - METEOSER V3
## Sintonización Atómica y Memoria de Diamante

**Fecha de Sello:** 31 de enero de 2026  
**Estado:** VIGENTE Y ETERNA  
**Aplicable a:** Todo código Python que procese índices meteorológicos, sensores, y física

---

## 🏛️ LOS 6 PILARES INAMOVIBLES

### 1. **LEY DEL ENTERO** 🔢
**Regla Inviolable:** Los topes, suelos y umbrales son SIEMPRE INT, NUNCA flotantes decorativos.

```python
# ❌ PROHIBIDO
max(0.0, valor)
score = 0.0
if temp > 32.0:

# ✅ OBLIGATORIO
max(0, valor)
score = 0
if temp > 32:
```

**Justificación:** Un umbral de 100 es 100, no 100.0. Los decimales añaden ruido cognitivo sin precisión física. La salida JSON emite INT puro: `"humedad_max": 100` (nunca `100.0`).

**Excepciones permitidas:** Solo constantes físicas con resolución real (273.15 K, 1013.25 hPa, 5.0/9.0 conversión).

---

### 2. **ESCUDO DE SEGURIDAD** 🛡️
**Regla Inviolable:** Toda división potencial debe estar protegida por `if divisor > 0:` ANTES de ejecutar.

```python
# ✅ OBLIGATORIO - Protección en aerodinámica
if velocidad_viento > 0:
    h_c = 5.0 + 2.5 * math.sqrt(velocidad_viento)  # Coef convección
else:
    h_c = 5.0  # Convección natural (sin viento)

# ✅ OBLIGATORIO - Protección en estabilidad
if denominador > 0:
    richardson = numerador / denominador
else:
    richardson = 9  # Tope de saturación
```

**No toques:** Estas protecciones son el corazón del sistema. Removerlas causa crash instantáneo.

**Auditoría:** Cada fórmula con `/` debe verificarse manualmente contra esta lista antes de commit.

---

### 3. **BLINDAJE CIENTÍFICO** 🧪
**Regla Inviolable:** Las constantes físicas son SAGRADAS. Jamás toques:

| Constante | Valor | Origen | Uso |
|-----------|-------|--------|-----|
| Cero absoluto | 273.15 | Termodinámica | Conversión T(K) = T(°C) + 273.15 |
| Presión ISA | 1013.25 | ISO 2533 | Referencia atmosférica nivel mar |
| Radiación solar | 1361.0 | WMO | Constante solar W/m² |
| Conversion °F→°C | 5.0/9.0 | Definición | (F - 32) × 5/9 = C |
| Gradiente ISA | -0.0065 | ISO 2533 | dT/dz troposfera |

**Acción:** Si ves `273.0` o `1013.0`, cámbialo a `273.15` y `1013.25` inmediatamente.

---

### 4. **DOS DECIMALES DE SALIDA** 📊
**Regla Inviolable:** La salida JSON de índices DEBE redondear a máximo 2 decimales significativos.

```python
# Entrada interna: puede tener 6+ decimales
utci_raw = 23.456789

# Salida JSON: exactamente 2 decimales
json_output = {"utci": round(utci_raw, 2)}  # → {"utci": 23.46}

# Excepto para índices adimensionales: max 1 decimal
json_output = {"richardson": round(ri_value, 1)}  # → {"richardson": 2.1}
```

**Beneficio:** Reduce ruido, mejora legibilidad, comprime JSON ~3%.

---

### 5. **CONFIG.JSON COMO FUENTE ÚNICA DE VERDAD** 📜
**Regla Inviolable:** Todo límite meteorológico se define en `data/indices_config.json::physics_safe::limits`, NUNCA hardcoded en Python.

```python
# ❌ PROHIBIDO - Hardcoded
if humedad > 100.0:
    humedad = 100.0

# ✅ OBLIGATORIO - Desde config
LIMITS = _load_physics_safe_config()
HUMEDAD_MAX = LIMITS["limits"]["humedad_max"]  # = 100 (INT)
if humedad > HUMEDAD_MAX:
    humedad = HUMEDAD_MAX
```

**Punto de control:** Función `_load_physics_safe_config()` en [environmental_indices.py](environmental_indices.py#L95-L147) es el guardián.

**Cambiar límites:** Edita `data/indices_config.json`, reinicia uvicorn. NO toques código Python.

---

### 6. **COORDENADAS SAGRADAS (ZONA GRIS PERMITIDA)** 🧭
**Regla Inviolable:** Latitud, longitud, altitud SIEMPRE son flotantes. Son excepciones a la Ley del Entero.

```python
# ✅ PERMITIDO - Coordenadas geográficas
lat = 41.5513  # Flotante (no toques)
lon = 2.3998   # Flotante (no toques)
alt = 96.0     # Flotante (elevation en metros)

# Pero umbrales basados en coordenadas: INT
if alt > 1000:  # INT, no 1000.0
    usar_presion_reducida = True
```

**Razón:** Las coordenadas tienen precisión real (decimales representa metros/segundos de arco). Los umbrales derivados son lógicos (INT).

---

## 📋 CHECKLIST PRE-COMMIT

Antes de hacer commit, verifica:

```
[ ] Grep "\.0\b" en deltas → Solo constantes físicas + coordenadas
[ ] Todos los max/min usan INT: max(0, ...), min(100, ...)
[ ] Grep "if.*> 0" → Divisiones protegidas
[ ] config.json tiene "physics_safe"::limits como única fuente
[ ] JSON output redondea a 2 decimales: round(valor, 2)
[ ] environmental_indices.py compila: python -m py_compile
[ ] Tests pasan: pytest tests/
```

---

## 🔒 ARQUEOLOGÍA DEL CÓDIGO - CAMBIOS IRREVERSIBLES

### Limpieza Masiva (31 ENE 2026)
- **Archivos:** environmental_indices.py (302,951 B → 302,462 B), main_asgi.py (120,614 B → 120,578 B)
- **Literales removidos:** 113 decorativos `.0`
- **Colesterol extraído:** 525 bytes totales (0.124%)
- **Decisión:** PERMANENTE - No se puede revertir

### Fusión Final (27 ENE 2026)
- Centralización de 37 topes en config.json
- INT puro en límites (0, 1, 9, 99, 100, 999, 1999, 4999)
- 3 correcciones críticas: humedad=100 (no 99), coseno∈±1, zeta∈±9

---

## 🚀 RÉGIMEN DE CRUCERO: MANUAL DE OPERACIÓN

### Cambiar un límite (caso de uso común)
1. Abre `data/indices_config.json`
2. Localiza `physics_safe.limits.NOMBRE`
3. Cambia valor (SIEMPRE INT)
4. Reinicia: `uvicorn main_asgi:app --reload`
5. Verifica: `curl http://localhost:8080/api/info`

**NO TOQUES PYTHON. La config es soberana.**

### Añadir nueva métrica meteorológica
1. Calcula con precisión flotante interna (6+ decimales)
2. Define nuevo `"tipo_indice"` en `physics_safe.index_types`
3. Define tope en `physics_safe.limits` (INT)
4. Redondea salida JSON a 2 decimales
5. Añade escudo de seguridad si hay divisiones

### Auditar integridad del sistema
```bash
# Buscar violations
grep -rE "=\s*[0-9]+\.0\b" core/ --include="*.py" | grep -v "273.15\|1361.0\|5.0/9.0\|0.0\|1.0"
# Debe devolver: 0 líneas (solo excepciones permitidas)
```

---

## 📌 REFERENCIAS ETERNAS

- **Fusión Final 27ENE:** Centralización de topes
- **Poda Masiva 31ENE:** Eliminación de paja digital
- **Config Soberana:** data/indices_config.json (fuente única de verdad)
- **Escudo de Seguridad:** if divisor > 0 ANTES de cualquier división
- **Physics Models:** core/indices/liljegren_wbgt.py, fanger_pmv_ppd.py, etc. (INTACTOS)

---

## 🎯 CONCLUSIÓN

**El Acorazado Argentona tiene su casco reluciente. Mantenlo así.**

- ✅ Código limpio (paja removida)
- ✅ Física sagrada (constantes protegidas)
- ✅ Seguridad matemática (escudos contra cero)
- ✅ Memoria eterna (esta documentación)
- ✅ Fuente única (config.json soberana)

**Cualquier violación a estos 6 pilares es sabotaje. No lo hagas.**

---

*Documento sellado por Fusión Atómica del Sistema METEOSER V3*  
*Vigencia: PERPETUA* 🔐
