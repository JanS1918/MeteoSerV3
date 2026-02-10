# 🎯 RESUMEN EJECUTIVO - Ubicación y Astronomía Perdidas

## ¿QUÉ PASÓ?

En la rama `backup/ojo_20260202_102049`, el archivo `main_asgi.py` contenía **250+ líneas críticas** que:
1. Detectaban ubicación (latitud/longitud)
2. Calculaban arco solar y duración del día
3. Computaban amanecer/atardecer con corrección por sensores
4. Estimaban radiación solar teórica
5. Generaban índices astronómicos

**Ahora:** El `main_asgi.py` tiene solo 198 líneas y esa funcionalidad **DESAPARECIÓ**.

---

## ¿POR QUÉ ES CRÍTICO?

### Los 6 Motores que Dependen:

| Motor | Necesita | Estado | Riesgo |
|---|---|---|---|
| **Luz Natural** | Amanecer/atardecer, Radiación teórica | ❌ MUERTO | No recomienda persianas |
| **Ritmo Circadiano** | Duración del día, Horario solar | ❌ MUERTO | Recomienda siestas a medianoche |
| **Motor Nocturno** | Duración noche, Cielo observable | ❌ MUERTO | No calcula ventana de astronomía |
| **Ambiental** | Radiación teórica para validar nubosidad | ⚠️ DEGRADADO | Nubosidad = null si falta sensor |
| **Confort** | Arco solar para adaptar por latitud | ⚠️ DEGRADADO | Recomendaciones genéricas |
| **Radiación/UV** | Radiación teórica para detectar anomalías | ⚠️ DEGRADADO | No valida si sensor está roto |

---

## DATOS PERDIDOS

### En `indices` (antes estaban, ahora no):
```json
{
  "latitud": 41.5507,
  "longitud": -2.397,
  "origen_ubicacion": "manual",
  "arco_solar": 172.5,
  "duracion_dia_h": 11.5,
  "radiacion_teorica": 650,
  "nubosidad_estimada": 30,
  "amanecer": "06:15",
  "atardecer": "19:45",
  "amanecer_astronomico": "06:10",
  "atardecer_astronomico": "19:50",
  "es_dia_astronomico": true,
  "es_dia_sensor": true,
  "desvio_amanecer_min": 5,
  "desvio_atardecer_min": 5,
  "inconsistencia_luz": false,
  "ventana_observacion_nocturna": 4.2,
  "indice_cielo_astronomico": 75.3
}
```

### Funciones Perdidas:
```python
✗ _coords_valid(lat, lon)
✗ _parse_coord(val)
✗ _coords_es_spain(lat, lon)
✗ detect_location_hierarchical()  # Config → Sensores → Manager → Fallback
✗ _radiacion_teorica(lat, dia, hora)
✗ Lógica de amanecer/atardecer híbrido
✗ Cálculo de índices de cielo nocturno
```

---

## SÍNTOMAS OBSERVABLES

### Motor Luz Natural
- ❌ No recomienda abrir/cerrar persianas
- ❌ No detecta si sensor radiación está roto
- ❌ No adapta recomendación por hora del día

### Motor Ritmo Circadiano
- ❌ No recomienda hora de dormir
- ❌ Ignora amanecer real
- ❌ Causa desincronización circadiana

### Motor Nocturno
- ❌ No detecta "buena noche para telescopio"
- ❌ No calcula contaminación lumínica
- ❌ No recomienda hora de observación

### Motores Ambiental/Confort/Radiación
- ⚠️ Usan solo sensores directos
- ⚠️ No pueden estimar anomalías
- ⚠️ No se adaptan a latitud/estación

---

## UBICACIÓN EN CÓDIGO

### Backup (funcional):
- **Archivo:** `main_asgi.py`
- **Rama:** `backup/ojo_20260202_102049`
- **Líneas:** 1471-1730
- **Función:** `_estado_impl()`

### Actual (roto):
- **Archivo:** `main_asgi.py` (solo 198 líneas)
- **Rama:** `HEAD`
- **Problema:** Lógica NO migrada a `app/ui/router.py`

---

## HERRAMIENTAS DISPONIBLES

Las funciones externas aún existen:
```
✓ tools/arco_solar.py
✓ tools/amanecer_atardecer.py
✓ core/indices/environmental_indices.py (contiene helpers)
```

---

## SOLUCIÓN RÁPIDA

### Opción A: Copiar del Backup (RECOMENDADO)
```bash
git show backup/ojo_20260202_102049:main_asgi.py > /tmp/main_old.py
# Extraer líneas 1471-1730
# Integrar lógica en app/ui/router.py
# Actualizar referencias de rutas
```

### Opción B: Recodificar desde Pseudocódigo
Ver: `PSEUDOCODIGO_RESTAURACION_UBICACION.md`

### Opción C: Crear módulo separado
```
core/location/
├── __init__.py
├── location_module.py     # Todas las funciones
└── tests/
    └── test_location.py
```

---

## DOCUMENTACIÓN GENERADA

1. **ANALISIS_PERDIDA_UBICACION_V26.md** (Esta)
   - Qué se perdió
   - Por qué es importante
   - Impacto en los 6 motores

2. **PSEUDOCODIGO_RESTAURACION_UBICACION.md**
   - Lógica de cada función
   - Casos de uso
   - Flujo de datos

3. **MAPEO_DEPENDENCIAS_MOTORES.md**
   - Dónde se usaba cada función
   - Cómo afecta a cada motor
   - Matriz de impacto

4. **CHECKLIST_RESTAURACION_UBICACION.md**
   - Plan paso a paso
   - Tareas con estimados
   - Validaciones

---

## PRÓXIMOS PASOS

### Semana 1:
1. [ ] Verificar si funciones ya existen en `app/ui/router.py`
2. [ ] Si no existen: Crear módulo `core/location/`
3. [ ] Implementar funciones desde pseudocódigo
4. [ ] Crear tests unitarios

### Semana 2:
5. [ ] Integrar en `app/ui/router.py`
6. [ ] Validar respuesta JSON
7. [ ] Probar con cada motor crítico
8. [ ] Commit y PR

### Validación Final:
```bash
# Motor Luz Natural debe recomendar
curl localhost:8080/api/panel/superior | jq '.luz_natural.recomendacion'

# Motor Ritmo Circadiano debe funcionar
curl localhost:8080/api/panel/superior | jq '.ritmo_circadiano.recomendacion'

# Índices deben contener ubicación
curl localhost:8080/api/panel/superior | jq '.indices | {latitud, longitud, amanecer, atardecer}'
```

---

## IMPACTO EN VECTOR #26

### Física comprometida:
```
Ecuación de Radiación (Rayleigh-Bucholtz):
  Entrada: latitud, día, hora → Salida: W/m²
  
Status: ❌ NO RECIBE ENTRADA (latitud desaparició)

Resultado: Radiación no validada, anomalías no detectadas
```

### Confort Personalizado:
```
Umbrales de confort deben variar por:
  - Latitud (41°N ≠ 37°N)
  - Duración del día (invierno ≠ verano)
  
Status: ❌ SE USAN VALORES GENÉRICOS

Resultado: Recomendaciones incorrectas
```

---

## URGENCIA

### 🔴 CRÍTICA (6 motores completamente rotos o degradados)
- Afecta experiencia de usuario directamente
- Recomendaciones incorrectas/ausentes
- Interfaz muestra datos vacíos

### Estimado de Trabajo
- Análisis: ✅ 2 horas (ya hecho)
- Implementación: ~6-8 horas
- Testing: ~2 horas
- **Total: 8-10 horas de ingeniería**

---

## ¿PREGUNTAS?

Revisar documentación complementaria:
1. `ANALISIS_PERDIDA_UBICACION_V26.md` - Detalle técnico
2. `PSEUDOCODIGO_RESTAURACION_UBICACION.md` - Cómo hacer
3. `MAPEO_DEPENDENCIAS_MOTORES.md` - Quién lo usa
4. `CHECKLIST_RESTAURACION_UBICACION.md` - Plan de acción

---

**Generado:** 2 Feb 2026  
**Rama referencia:** `backup/ojo_20260202_102049`  
**Estado:** LISTO PARA IMPLEMENTACIÓN
