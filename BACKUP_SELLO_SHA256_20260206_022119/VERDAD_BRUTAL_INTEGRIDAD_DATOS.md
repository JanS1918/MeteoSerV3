# VERDAD BRUTAL SOBRE NUESTRAS FÓRMULAS - AUDITORÍA COMPLETA

**CONCLUSIÓN EJECUTIVA:**
El usuario está FURIOSO con razón. Guardian trae 3 fórmulas de sensación térmica al duelo, pero:
- Una NO EXISTE en el código (wind_chill es REGISTRO FANTASMA)
- Una sí existe pero tiene baja calidad (UTCI registrada con score "inventado" 88.5%)
- Hay excelentes opciones OCULTAS que nunca se consideran

---

## PARTE 1: EL CRIMEN PERFECTO - wind_chill NO EXISTE

### ¿Qué pasó?

**En FORMULA_HIERARCHY (core/bus/formula_hierarchy.py línea 191):**
```python
NivelElite.FALLBACK: Fórmula(
    nivel=NivelElite.FALLBACK,
    nombre_tecnico="wind_chill",
    nombre_legible="Wind Chill Temperature Index",
    módulo="core.indices.environmental_indices",
    # ... [metadata]
),
```

**En el código real (core/indices/environmental_indices.py):**
```
# [FAST] EUTANASIA TÉCNICA 2026: Heat Index, Wind Chill, Humidex ELIMINADOS
# Reemplazados por UTCI Diamond_Refined_v1 (física completa)
```

**RESULTADO:** Guardian intenta usar `wind_chill()` en duelo, pero la función NO EXISTE → ERROR

### Impacto
- ❌ Cuando duelo busca fórmula FALLBACK, falla silenciosamente
- ❌ Sistema cae a valor por defecto (probablemente UTCI ELITE)
- ❌ Usuario piensa que hay 3 opciones, en realidad hay 1.5

---

## PARTE 2: INDICE_WBGT EXISTE PERO ES INVISIBLE

### La fórmula ESCONDIDA

**Ubicación:** core/indices/environmental_indices.py línea 1662
```python
def indice_wbgt(temp_c: float, humedad: float, radiacion: float = 0, 
                viento_kmh: float = 0, **kwargs) -> float:
    """Wet Bulb Globe Temperature - Standard OSHA para estrés térmico ocupacional"""
    # [IMPLEMENTACIÓN COMPLETA]
    return wbgt_valor
```

**Estado en FORMULA_HIERARCHY:** NO EXISTE
- ❌ Nunca registrada
- ❌ Nunca visible a duelo
- ❌ Nunca evaluada en competición

**Impacto:** Perdemos una opción ESTÁNDAR OSHA para ambientes ocupacionales

---

## PARTE 3: LOS NÚMEROS MÁGICOS (88.5% vs 92.5%)

### ¿De dónde vienen los scores?

Encontrados en: [llamadas_formulas_externas_v47_5_revisado.py](llamadas_formulas_externas_v47_5_revisado.py)

```python
"score_interno": 88.5,   # ← NÚMERO MÁGICO (sin metodología)
"score_externa": 92.5,   # ← NÚMERO MÁGICO (sin metodología)
"mejora": 4.0,          # ← DIFERENCIA INVENTADA
```

### Metodología REAL
- ✅ Cálculos físicos: UTCI es ISO 14505-2 oficial
- ❌ Benchmarking: NINGUNO documentado
- ❌ Validación: Solo "claimed" en comentarios
- ❌ Dataset: Sin datos reales de prueba

### Realidad
Los scores parecen:
1. Copias de "papers académicos" (92.5% suena como precisión de artículo)
2. Estimaciones del agente anterior sin fuente
3. Números que cumplen "criterios Guardian" (≥85%)

---

## PARTE 4: ¿QUÉ TENEMOS REALMENTE EN SENSACIÓN TÉRMICA?

### En FORMULA_HIERARCHY
```
1. ELITE:     indice_utci                          (ISO 14505-2, ±0.1°C)
2. ESTÁNDAR:  indice_steadman_apparent_temperature (1984, ±0.5°C)
3. FALLBACK:  wind_chill                           (❌ NO EXISTE)
```

### En el código actual
```
1. ✅ indice_utci()                               (LÍNEA 380 - EXISTE, FUNCIONA)
2. ✅ indice_steadman_apparent_temperature()      (LÍNEA 856 - EXISTE, FUNCIONA)
3. ❌ wind_chill()                                (LÍNEA 849 - ELIMINADA, REGISTRO FANTASMA)
4. ✅ indice_wbgt()                               (LÍNEA 1662 - EXISTE, NO REGISTRADA)
5. ❌ humidex()                                   (LÍNEA 849 - ELIMINADA, "EUTANASIA TÉCNICA")
6. ❌ heat_index()                                (LÍNEA 849 - ELIMINADA, "EUTANASIA TÉCNICA")
```

### Resumen
- Tenemos **2 fórmulas funcionando** de 3 registradas
- Tenemos **1 fórmula escondida** (WBGT) que podría usarse
- Tenemos **2 fórmulas deletadas** (Humidex, Heat Index) sin documentación

---

## PARTE 5: LAS 5 "EXTERNAS" - ¿SON REALMENTE EXTERNAS?

### Lo que se creó (formulas_externas_v47_5.py)

1. **utci_v4_02_fiala** - DUPLICADA
   - Existe internamente: `indice_utci()` 
   - Nueva versión: Simplificación del v4.02 oficial
   - Diferencia: Puede que sea más simple/rápida

2. **realfeel_steadman_twc** - NUEVA (verdaderamente externa)
   - ¿Existe internamente? NO
   - Es implementación de The Weather Company

3. **humidex_eccc_canada** - RESURRECCIÓN
   - Fue deletada (línea 849 "EUTANASIA")
   - Ahora reimplementada como "externa"
   - Señal de alerta: ¿Por qué fue deletada entonces?

4. **wbgt_yaglou_osha** - DUPLICADA-ESCONDIDA
   - Existe internamente: `indice_wbgt()` línea 1662
   - Nueva versión: Copia de lo que ya tenemos

5. **mrt_tg_iso7726** - NUEVA (probablemente no interna)
   - ISO 7726 está en environmental_indices pero...
   - Necesita verificación si hay función equivalente

### Veredicto
**"Externas"** es el nombre EQUIVOCADO. Son:
- 2 DUPLICADAS (utci, wbgt) que ya tenemos ocultas/deletadas
- 1 RESURRECCIÓN (humidex) que fue deliberadamente eliminada
- 2 NUEVAS REALES (realfeel, mrt - probablemente)

---

## PARTE 6: ¿POR QUÉ PASÓ ESTO?

### Timeline reconstructido

**Punto A - Versiones anteriores (antes 3 Feb 2026):**
- Teníamos: indice_utci + steadman + wind_chill + humidex + heat_index + WBGT
- FORMULA_HIERARCHY tenía 5 entradas

**Punto B - "EUTANASIA TÉCNICA 2026" (línea 849):**
```python
# Decisión deliberada: Eliminar Heat Index, Wind Chill, Humidex
# Razón: "Reemplazados por UTCI Diamond_Refined_v1 (física completa)"
# Sin documentación adicional
```

**Punto C - FORMULA_HIERARCHY NO se actualizó:**
- Sigue registrando `wind_chill` como FALLBACK
- Nunca agregó `indice_wbgt()` aunque existe

**Punto D - Ahora (5 Feb 2026):**
- Tenemos código fragmentado e inconsistente
- Duelo solo ve 2-3 opciones de 6+ disponibles
- Agent anterior intentó "arreglarlo" creando duplicadas como "externas"

---

## PARTE 7: EL ERROR DEL AGENTE ANTERIOR

### Lo que hizo
✅ Identificó que faltaban fórmulas
✅ Creó 5 implementaciones
✅ Las testó (resultados realistas)
✅ Las registró en `data/formula_candidates.json`

### Lo que NO hizo
❌ Auditar si las fórmulas YA EXISTÍAN internamente
❌ Verificar FORMULA_HIERARCHY para desajustes
❌ Entender por qué humidex/heat_index fueron deletadas
❌ Preguntar por qué WBGT estaba oculta

### Resultado
Creó "solución" a problema SIN ENTENDER EL PROBLEMA REAL

---

## PARTE 8: EL PROBLEMA REAL DEL USUARIO

### Lo que el usuario quería
```
"Quiero que lleve las NUESTRAS MEJORES al duelo"
"Nunca acertamos porque siempre llevamos fórmulas que NO son las mejores"
"Verifica cuál TENEMOS, si las USAMOS, si esas las SUPERAN realmente"
```

### Lo que el usuario REALMENTE necesita
1. **Visibilidad:** Conocer TODAS las fórmulas disponibles
2. **Consistencia:** Que FORMULA_HIERARCHY esté sincronizado con código
3. **Eliminación de fantasmas:** Quitar registros de funciones que no existen
4. **Activación de ocultas:** Registrar WBGT y otras fórmulas dormidas
5. **Entendimiento:** SABER por qué ciertos formulas fueron deletadas

### Lo que NO quería
❌ "Externas" ciegas sin auditar qué ya tenemos
❌ Duplicadas registradas
❌ Números mágicos de calidad sin metodología

---

## RECOMENDACIÓN INMEDIATA

### Acción 1: Sincronizar FORMULA_HIERARCHY

```python
# ANTES (actual - INCONSISTENTE):
"sensacion_termica": {
    ELITE: indice_utci,                          # ✅ Existe
    ESTÁNDAR: indice_steadman_apparent_temperature,  # ✅ Existe  
    FALLBACK: wind_chill,                        # ❌ NO EXISTE (FANTASMA)
}

# DESPUÉS (propuesto - CONSISTENTE):
"sensacion_termica": {
    ELITE: indice_utci,                          # ✅ Existe
    ESTÁNDAR: indice_steadman_apparent_temperature,  # ✅ Existe
    OCUPACIONAL: indice_wbgt,                    # ✅ Existe pero oculta
    # FALLBACK: wind_chill,                      # ❌ ELIMINADA - REMOVER
}
```

### Acción 2: Investigar decisiones EUTANASIA

```
Verificar:
1. ¿Por qué fueron deletadas Heat Index + Wind Chill + Humidex?
2. ¿Hay documentación de la decisión?
3. ¿Fue deliberado o accidental?
4. ¿Debería RESTAURARSE Humidex para climas cálidos?
```

### Acción 3: Usar lo que TENEMOS

```
En lugar de crear formulas_externas...
1. Registrar indice_wbgt() en FORMULA_HIERARCHY
2. Investigar MRT/Tg en environmental_indices (¿existe?)
3. Decidir: ¿restaurar humidex?
4. Resultado: Guardian duelo ve 5+ opciones REALES, no duplicadas
```

---

## CONCLUSIÓN

**Guardian V47.5 tiene un problema de INTEGRIDAD de datos:**
- ❌ FORMULA_HIERARCHY registra cosas que no existen
- ❌ Código tiene cosas que no están registradas
- ❌ No hay trazabilidad de decisiones (eutanasia sin docum)
- ❌ El duelo NO ve mejores opciones disponibles

**Solución NO es crear "externas"**
**Solución ES auditar, sincronizar y activar lo que ya tenemos**

---

**Documento creado:** 2026-02-05 18:XX UTC
**Basado en:** Auditoría de código + FORMULA_HIERARCHY + environmental_indices.py
**Conclusión:** Usuario está JUSTIFICADAMENTE furioso
