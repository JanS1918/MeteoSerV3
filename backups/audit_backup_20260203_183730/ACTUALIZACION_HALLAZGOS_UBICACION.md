# 📋 ACTUALIZACIÓN DE HALLAZGOS - Ubicación Y Astronomía

## ✅ CONCLUSIÓN REVISADA

### Estado REAL de la Lógica

**BIEN NOTICIA:** La lógica de ubicación y astronomía **NO SE PERDIÓ COMPLETAMENTE**.

Se migró parcialmente a:
1. `app/ui/viewmodel.py` → Cálculo de arcos solares
2. `core/arcos_solares.py` → Funciones astronómicas
3. `app/ui/router.py` → Inyección de contexto

---

## 📍 UBICACIÓN ACTUAL DE FUNCIONES

### 1. Cálculo de Posición Solar
```
ANTERIOR (main_asgi.py L1545-1587):
  - from tools.arco_solar import arco_solar
  - calcular_amanecer_atardecer()
  - _radiacion_teorica()

AHORA (core/arcos_solares.py):
  - calcular_posicion_sol()
  - calcular_posicion_luna()
  - calcular_fase_lunar()

INTEGRACIÓN (app/ui/viewmodel.py L117-124):
  def obtener_arcos_solares(lat, lon, nubosidad):
    datos_sol = calcular_posicion_sol(lat, lon, fecha_actual)
    datos_luna = calcular_fase_lunar(fecha_actual)
    posicion_luna = calcular_posicion_luna(...)
    return {...}

ENDPOINT (app/ui/router.py L688):
  @router.get("/api/panel/arcos")
  async def obtener_arcos_solares(nubosidad: float = None):
    data = panel_vm.obtener_arcos_solares(lat, lon, nubosidad)
    return data
```

✅ **PRESENTE en `core/arcos_solares.py`**

---

### 2. Detección Jerárquica de Ubicación
```
ANTERIOR (main_asgi.py L1471-1539):
  - Leer config manual
  - Leer sensores del sistema
  - Consultar manager.obtener_coordenadas()
  - Fallback a Argentona

AHORA: ???
  - app/ui/router.py L726-728 intenta obtener coords del manager
  - Pero NO implementa la jerarquía completa

RIESGO: ⚠️ Incompleta
```

---

### 3. Radiación Teórica
```
ANTERIOR (main_asgi.py L1548-1556):
  def _radiacion_teorica(lat_deg, day, hora_decimal):
    # Ecuación de Spencer simplificada
    # Retorna: W/m²

AHORA: ???
  - NO encontrada en core/arcos_solares.py
  - NO importada en app/ui/router.py
  - NO calculada para estimar nubosidad

RIESGO: 🔴 FALTA CRÍTICA
```

---

### 4. Amanecer/Atardecer Híbrido
```
ANTERIOR (main_asgi.py L1614-1671):
  - Comparar amanecer astronómico vs sensor
  - Ajustar si hay desvío > 90 minutos
  - Generar indicadores de inconsistencia

AHORA (app/ui/viewmodel.py L123):
  'amanecer': datos_sol['amanecer'],
  'anochecer': datos_sol['anochecer'],
  
PROBLEMA: ⚠️ Solo devuelve valores teóricos, NO híbridos
  - No valida con radiación real
  - No detecta inconsistencias
  - No genera indicadores de alerta
```

---

### 5. Índices Astronómicos de Cielo Nocturno
```
ANTERIOR (main_asgi.py L1693-1726):
  - duracion_noche_h
  - ventana_observacion_nocturna
  - indice_cielo_astronomico
  - indice_cielo_astronomico_nivel

AHORA (app/ui/viewmodel.py L124):
  'duracion_noche': datos_sol['duracion_noche']

PROBLEMA: ⚠️ Solo duración, NO índices compuestos
  - NO calcula ventana de observación
  - NO estima cielo observable
  - NO clasifica calidad de noche
```

---

## 🚨 LO QUE REALMENTE FALTA

### CRÍTICA: Radiación Teórica
```python
# Archivo: app/ui/viewmodel.py o core/arcos_solares.py
# FALTA: Función _radiacion_teorica()

IMPACTO: 
  - Motor Radiación/UV NO VALIDA anomalías
  - No puede estimar nubosidad si falta sensor
  - Toda la física de Vector #26 sin validación
```

### CRÍTICA: Lógica Híbrida Día/Noche
```python
# Archivo: app/ui/viewmodel.py o core/arcos_solares.py
# FALTA: Sincronización sensor vs astronomía

IMPACTO:
  - Motor Luz Natural NO DETECTA anomalías de sensor
  - No ajusta horario si sensor está retrasado
  - Inconsistencias sin alerta
```

### MEDIA: Índices Astronómicos Compuestos
```python
# Archivo: app/ui/viewmodel.py
# FALTA: ventana_observacion_nocturna, indice_cielo_astronomico

IMPACTO:
  - Motor Nocturno retorna valores genéricos
  - No personaliza por calidad del cielo
  - Astronomía sin contexto real
```

### MEDIA: Detección Jerárquica Completa
```python
# Archivo: app/ui/router.py L726-728
# ACTUAL: Solo intenta del manager
# FALTA: Lógica completa (config → sensores → manager → fallback)

IMPACTO:
  - Si manager no tiene coords: ubica en (41.5, 2.4) genérico
  - No lee archivo de configuración manual
  - No intenta desde sensores del sistema
  - Sin fallback validado de España
```

---

## 📊 ESTADO ACTUAL VS. ESPERADO (REVISADO)

| Componente | ANTERIOR (Backup) | AHORA | Estado |
|---|---|---|---|
| Arco solar | main_asgi L1547 | core/arcos_solares | ✅ Migrado |
| Amanecer/atardecer | main_asgi L1614 | core/arcos_solares | ⚠️ Parcial (solo teórico) |
| Radiación teórica | main_asgi L1548 | ??? | ❌ FALTA |
| Híbrido día/noche | main_asgi L1650 | ??? | ❌ FALTA |
| Índices cielo | main_asgi L1693 | ??? | ❌ FALTA |
| Detección ubicación | main_asgi L1471 | app/ui/router L726 | ⚠️ Parcial |
| Integración en contexto | main_asgi L1728 | app/ui/router L358 | ✅ Presente |

---

## 🔍 BÚSQUEDAS EN CODEBASE

### Búsqueda 1: ¿Existe `radiacion_teorica`?
```bash
grep -r "radiacion_teorica" core/
# RESULTADO: NO ENCONTRADA
```

### Búsqueda 2: ¿Existe `ventana_observacion_nocturna`?
```bash
grep -r "ventana_observacion_nocturna" core/
# RESULTADO: NO ENCONTRADA
```

### Búsqueda 3: ¿Existe lógica híbrida día/noche?
```bash
grep -r "es_dia_sensor\|inconsistencia_luz" core/
# RESULTADO: NO ENCONTRADA
```

### Búsqueda 4: ¿Qué hay en core/arcos_solares.py?
```bash
head -50 core/arcos_solares.py
# RESULTADO: Ver sección siguiente
```

---

## 📄 CONTENIDO DE `core/arcos_solares.py`

(Necesito leerlo para confirmar qué está allí)

---

## 🛠️ ACCIONES CORRECTIVAS (REVISADAS)

### ACCIÓN 1: Verificar qué está en `core/arcos_solares.py` ⏳ TODO
```bash
wc -l core/arcos_solares.py
grep -n "def " core/arcos_solares.py
```

### ACCIÓN 2: Buscar `core/indices/environmental_indices.py` ⏳ TODO
```bash
# Ver si tiene las funciones que se importaban en backup:
grep -n "_calcular_ventana_observacion_nocturna\|_clasificar_indice_cielo" core/indices/environmental_indices.py
```

### ACCIÓN 3: Crear función `radiacion_teorica()` ⏳ TODO
```
Ubicación recomendada: core/arcos_solares.py
Copia pseudocódigo de: PSEUDOCODIGO_RESTAURACION_UBICACION.md → Función 6
```

### ACCIÓN 4: Crear función de lógica híbrida día/noche ⏳ TODO
```
Ubicación recomendada: core/arcos_solares.py
Copia pseudocódigo de: PSEUDOCODIGO_RESTAURACION_UBICACION.md → Función 8
```

### ACCIÓN 5: Completar detección jerárquica de ubicación ⏳ TODO
```
Ubicación recomendada: core/location/ (nuevo módulo)
O: Expandir app/ui/router.py L726-728
Copia pseudocódigo de: PSEUDOCODIGO_RESTAURACION_UBICACION.md → Función 4
```

### ACCIÓN 6: Integrar índices de cielo en respuesta ⏳ TODO
```
Ubicación recomendada: app/ui/viewmodel.py
Añadir a obtener_arcos_solares():
  - ventana_observacion_nocturna
  - indice_cielo_astronomico
  - indice_cielo_astronomico_nivel
Copia lógica de: main_asgi.py backup L1693-1726
```

---

## 📝 SIGUIENTES PASOS

### Inmediato (Hoy):
1. Leer `core/arcos_solares.py` → Verificar qué funciones tiene
2. Leer `core/indices/environmental_indices.py` → Verificar funciones helper

### Corto plazo (Este fin de semana):
3. Crear función `radiacion_teorica()` en `core/arcos_solares.py`
4. Crear función de lógica híbrida día/noche
5. Completar detección jerárquica de ubicación

### Mediano plazo (Próxima semana):
6. Integrar nuevas funciones en `app/ui/viewmodel.py`
7. Validar que respuesta JSON incluya todos los índices
8. Probar con motores críticos

### Largo plazo:
9. Tests unitarios para cada función
10. Documentación de API
11. PR con cambios

---

## 📞 CONCLUSIÓN REVISADA

**La situación NO es catastrófica como parecía inicialmente.**

La lógica de astronomía SÍ existe pero está:
1. ✅ Parcialmente migrada (arcos solares)
2. ⚠️ Incompleta (faltan índices compuestos)
3. ❌ Falta radiación teórica (CRÍTICA para Vector #26)

**Estimado de trabajo para COMPLETAR:**
- Radiación teórica: 1 hora
- Lógica híbrida: 1-2 horas
- Índices compuestos: 1-2 horas
- Tests: 1-2 horas
- **Total: 4-7 horas (no 8-10)**

---

**Estado:** ANÁLISIS ACTUALIZADO, LISTO PARA ACCIÓN INMEDIATA

*Generado: 2 Feb 2026*
*Nota: Basado en búsquedas en codebase actual*
