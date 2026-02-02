# LIMITES_FISICOS_SELLADOS.md

## MAPA DE CLAMPS Y FALLBACKS — Quantum_Diamond_Universal_v1.1_FINAL
## ⚛️ SOBERANÍA DE CÁLCULO: Clamps SOLO en Salida Final

Este documento lista todos los límites físicos (clamps), topes, protecciones y fallbacks implementados en el código de MeteoSer V3, con justificación científica y visibilidad para auditoría total.

**FILOSOFÍA DE EXTINCIÓN (31 Enero 2026):**
- **Motores internos (IAPWS-95, Virial, Ciddor, Monin-Obukhov)**: Cálculo con precisión infinita, SIN clamps intermedios.
- **Capa de salida (sanitizar_json)**: Aquí se aplican los 10 Clamps de Extinción con rango total de la física.
- **Objetivo**: Evitar propagación de error. Precisión de reloj atómico dentro de tanque acorazado.

---

### 🛡️ CLAMPS DE EXTINCIÓN (Valores INT Puros)

| Parámetro | Rango/Valor | Justificación |
|-----------|-------------|---------------|
| **Temperatura** | ±99°C | Rango máximo observable en superficie terrestre |
| **Presión** | 799-1099 hPa | Desde centro ciclón más profundo a anticiclón más extremo |
| **Humedad Relativa** | 0-100% | Vacío absoluto a saturación total |
| **UTCI** | ±99°C | Límite de supervivencia humana con ropa |
| **WBGT** | 0-49°C | Índice de estrés térmico (49°C = peligro extremo) |
| **UV** | 0-49 | Índice UV (49 = nivel extremo jamás registrado) |
| **Viento** | 0-399 km/h | Desde calma hasta récord mundial F5 |
| **CO₂** | 199-9999 ppm | Desde aire limpio a ambiente peligroso |
| **Zeta (ζ)** | ±49 | Estabilidad atmosférica extrema (Businger-Dyer extendido) |
| **ΔT** | ±499 K | Diferencia térmica máxima observable |

---

### 1. Psicrometría y Vapor (Hyland-Wexler, Virial, IAPWS)
- **Temperatura interna**: SIN clamp en motores. Protección solo contra valores no físicos (NaN, Inf).
- **Humedad interna**: SIN clamp en cálculos. Se valida coherencia física (0≤HR≤100 solo en salida).
- **Presión de Saturación**: Cascada de degradación: IAPWS-95 → Virial-Greenspan → Hyland-Wexler → ISA (con log WARNING + flag "ALERTA_FALLO_SENSOR").
  - _Justificación_: Cada fallback reduce precisión pero mantiene coherencia física.
- **Divisiones protegidas**: Todas las divisiones están protegidas por `if abs(denominador) < 1e-12: return None` o similar.
  - _Justificación_: Evita crash por divisores nulos o log(0), pero NO limita el rango de cálculo.

### 2. Dinámica de Fluidos (Monin-Obukhov, Richardson, Ley Logarítmica)
- **Estabilidad ζ (zeta) interna**: Se calcula sin límite. Solo se clampea a ±49 en salida JSON.
  - _Justificación anterior (±9)_: Límite de convergencia Businger-Dyer clásico.
  - _Justificación nueva (±49)_: Permitir observación de atmósferas extremas (inversiones polares, superconvección tropical).
- **Velocidad de fricción u***: SIN clamp interno. Protección solo contra valores no físicos.
- **Viento**: SIN clamp interno. Rango 0-399 km/h solo en salida.

### 3. Modelo GAB (Sorción de Paredes)
- **Parámetros**: Validación física estricta: a ∈ (0.01, 2.0), b ∈ (0.01, 1.0), c ∈ (0.01, 2.0).
  - _Justificación_: Fuera de estos rangos, la isoterma GAB no es físicamente válida (esta validación es científica, no un clamp).
- **Actividad de agua (aw)**: SIN clamp en cálculo. Coherencia HR/100 validada en salida.
- **División protegida**: Si el denominador de la isoterma es <1e-12, retorna 0.0.

### 4. Astronomía (NREL SPA, Ciddor)
- **Refracción**: Cálculo completo sin clamps. No se calcula solo si elevación < -2° (criterio físico, no clamp numérico).
- **Corrección de Ciddor**: SIN clamp interno. Se calcula para cualquier elevación físicamente observable.
- **ΔT (Deriva Atómica)**: SIN clamp. Validación física: debe ser positivo (ley termodinámica).

### 5. UTCI y Sensación Térmica
- **Temperatura interna**: SIN clamp en polinomio UTCI. El polinomio Fiala diverge fuera del rango de entrenamiento, pero se calcula igual.
- **Viento interno**: SIN clamp en cálculo de resistencia térmica.
- **Salida final**: UTCI clampeado a ±99°C solo en JSON.
  - _Justificación_: Rango de supervivencia humana extendido.

### 6. Fallbacks y Cascadas Universales
- **Cascada de degradación**: Si una fórmula de élite falla, el sistema degrada automáticamente a versiones más estables (ej: Shuttleworth-Wallace → Penman-Monteith → Thornthwaite).
  - _Justificación_: Mantener robustez y continuidad operativa.
- **ISA Fallback**: Si falla el barómetro, se usa atmósfera estándar (1013.25 hPa) y se activa flag **"status": "ALERTA_FALLO_SENSOR"**.

### 7. Visibilidad en Logs
- **Todos los clamps críticos y fallbacks** generan un registro DEBUG/INFO en `logs/physics_extremos.log`.
  - _Justificación_: Auditoría total. Si un dato toca un clamp de salida, queda registrado para trazabilidad.

---

### 📊 RESUMEN DE CLAMPS (Tabla Completa)

```
PARÁMETRO          | CLAMP SALIDA    | MOTOR INTERNO      | JUSTIFICACIÓN
-------------------+-----------------+--------------------+----------------------------------
Temperatura        | ±99°C           | SIN clamp          | Rango físico terrestre extremo
Presión            | 799-1099 hPa    | SIN clamp          | Desde ciclón profundo a anticiclón
Humedad            | 0-100%          | SIN clamp          | Definición física de saturación
UTCI               | ±99°C           | SIN clamp          | Supervivencia humana extendida
WBGT               | 0-49°C          | SIN clamp          | Estrés térmico extremo
UV                 | 0-49            | SIN clamp          | Récord UV jamás medido
Viento             | 0-399 km/h      | SIN clamp          | Récord F5 tornado + margen
CO₂                | 199-9999 ppm    | SIN clamp          | Aire limpio a peligro extremo
Zeta (ζ)           | ±49             | SIN clamp          | Estabilidad atmosférica extrema
ΔT                 | ±499 K          | SIN clamp          | Diferencia térmica máxima
```

---

**Sello Final:**
Este mapa de límites es la última pieza del Manifiesto Universal. Aquí termina la física y comienza la protección del código. Cada clamp, tope y fallback está documentado, justificado y es auditable.

**Si el mundo se acaba, lo verás en tu :8080.**

_Actualizado: 31 de enero de 2026 — CLAMPS DE EXTINCIÓN implementados_

---

**Para más detalles, consulte los módulos:**
- core/indices/environmental_indices.py (sanitizar_json: clamps de salida)
- core/indices/advanced_physics_models.py (motores sin clamps)
- core/indices/atmospheric_profiler.py (motores sin clamps)
- core/indices/gab_sorption.py (validación científica)
- core/indices/utci_polynomial.py (cálculo sin clamps)
- core/indices/astronomia_recursiva.py (cálculo sin clamps)
- core/context/fallback_universal.py (cascadas de degradación)
- data/indices_config.json (configuración de clamps)

**Motor:** Quantum_Diamond_Universal_v1.1_FINAL
**Filosofía:** ⚛️ Precisión de reloj atómico dentro de tanque acorazado
