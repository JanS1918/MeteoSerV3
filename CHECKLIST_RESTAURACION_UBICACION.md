# ✅ CHECKLIST DE RESTAURACIÓN - Ubicación y Astronomía

## 📋 ESTADO ACTUAL vs. ESPERADO

### Estado Actual (main_asgi.py)
```
main_asgi.py: 198 líneas
└─ Solo recibe datos Ecowitt
└─ Los transforma a unidades SI
└─ Actualiza sensores del SystemManager
└─ Delega TODO a app/ui/router.py

Resultado: 6 motores sin contexto de ubicación/astronomía
```

### Estado Esperado (Backup ojo_20260202_102049)
```
main_asgi.py: 3398 líneas (~17× más)
└─ Detecta ubicación (Config → Sensores → Manager → Fallback)
└─ Calcula arco solar
└─ Calcula amanecer/atardecer híbrido
└─ Calcula radiación teórica
└─ Estima nubosidad
└─ Índices astronómicos de cielo nocturno
└─ TODO se inyecta en contexto para 40+ motores

Resultado: 6 motores funcionan correctamente
```

---

## 🎯 TAREAS DE RESTAURACIÓN

### TAREA 1: Extraer funciones del backup ✓ COMPLETADO
- [x] Acceder a rama backup/ojo_20260202_102049
- [x] Extraer líneas 1471-1730 de main_asgi.py
- [x] Identificar funciones clave
- [x] Documentar pseudocódigo

**Archivo generado:** `PSEUDOCODIGO_RESTAURACION_UBICACION.md`

---

### TAREA 2: Verificar si funciones existen en codebase

#### 2.1 Buscar `_radiacion_teorica` ⏳ PENDIENTE
```bash
cd c:\Users\kioko\Desktop\MeteoSerV3
grep -r "radiacion_teorica" core/ app/ --include="*.py"
grep -r "_radiacion_teorica" . --include="*.py"
```

**Acción:** Ejecutar búsqueda y documentar resultado

#### 2.2 Buscar `_coords_valid` ⏳ PENDIENTE
```bash
grep -r "coords_valid" . --include="*.py"
grep -r "_coords_valid" . --include="*.py"
```

**Acción:** Ejecutar búsqueda y documentar resultado

#### 2.3 Buscar lógica de ubicación ⏳ PENDIENTE
```bash
grep -r "origen_ubicacion" . --include="*.py"
grep -r "latitud" core/ --include="*.py" | head -20
```

**Acción:** Verificar si se migró a `app/ui/router.py`

#### 2.4 Verificar herramientas externas ✓ COMPLETADO
```
✓ tools/arco_solar.py EXISTE
✓ tools/amanecer_atardecer.py EXISTE
```

---

### TAREA 3: Identificar dónde debería estar la lógica

#### 3.1 Revisar `app/ui/router.py` ⏳ PENDIENTE
```bash
wc -l app/ui/router.py
grep -n "amanecer\|atardecer\|arco_solar\|radiacion_teorica" app/ui/router.py
grep -n "ubicacion\|latitud\|longitud" app/ui/router.py
```

**Preguntas:**
- ¿Tiene lógica de ubicación?
- ¿Calcula índices astronómicos?
- ¿Es el lugar donde se pasó la lógica?

**Acción:** Leer archivo completo y analizar

#### 3.2 Revisar `core/system/system_manager.py` ⏳ PENDIENTE
```bash
grep -n "set_manual_coordinates\|obtener_coordenadas" core/system/system_manager.py
grep -n "latitud\|longitud" core/system/system_manager.py
```

**Preguntas:**
- ¿Tiene métodos de geocodificación?
- ¿Gestiona ubicación internamente?

**Acción:** Leer sección de ubicación

#### 3.3 Revisar `core/indices/environmental_indices.py` ⏳ PENDIENTE
```bash
grep -n "arco_solar\|radiacion_teorica\|amanecer" core/indices/environmental_indices.py
grep -n "_calcular_ventana_observacion_nocturna" core/indices/environmental_indices.py
```

**Preguntas:**
- ¿Dónde se calculan índices astronómicos ahora?
- ¿Tiene las funciones helper que se importaban?

**Acción:** Leer archivo y documentar

---

### TAREA 4: Crear módulo centralizado de ubicación ⏳ PENDIENTE

#### 4.1 Crear archivo
```bash
mkdir -p core/location
touch core/location/__init__.py
touch core/location/location_module.py
```

#### 4.2 Implementar funciones (ver PSEUDOCODIGO_RESTAURACION_UBICACION.md)

```python
# core/location/location_module.py

import datetime
import math
import pathlib
from typing import Optional, Tuple, Dict

# Función 1: Validación
def coords_valid(lat, lon) -> bool:
    """Validar que lat/lon estén en rango válido"""
    # ... (Pseudocódigo en documento)

# Función 2: Parseo
def parse_coord(val) -> Optional[float]:
    """Convertir múltiples formatos de coordenadas"""
    # ... (Pseudocódigo en documento)

# Función 3: Validación España
def coords_es_spain(lat, lon) -> bool:
    """Validar que coordenadas sean de España"""
    # ... (Pseudocódigo en documento)

# Función 4: Detección jerárquica
def detect_location(system, config_path: str) -> Dict:
    """
    Detectar ubicación en orden: Config → Sensores → Manager → Fallback
    Retorna: {"lat": float, "lon": float, "origen": str}
    """
    # ... (Pseudocódigo en documento)

# Función 5: Radiación teórica
def radiacion_teorica(lat_deg: float, dia_año: int, hora_decimal: float) -> float:
    """Calcular radiación solar teórica en W/m²"""
    # ... (Pseudocódigo en documento)

# Función 6: Helpers
def hhmm_a_minutos(hhmm: str) -> Optional[int]:
    """Convertir "06:15" a minutos"""
    # ... (Pseudocódigo en documento)

def minutos_a_hhmm(total_min: int) -> str:
    """Convertir minutos a "06:15" """
    # ... (Pseudocódigo en documento)
```

**Acción:** Copiar pseudocódigo y adaptar a código real

#### 4.3 Crear tests
```bash
touch tests/test_location_module.py
```

```python
# tests/test_location_module.py

from core.location.location_module import *

def test_coords_valid():
    assert coords_valid(41.5507, -2.397) == True  # Argentona
    assert coords_valid(91, 0) == False           # Fuera de rango
    assert coords_valid(None, 0) == False

def test_parse_coord():
    assert parse_coord("41.5507N") == 41.5507
    assert parse_coord("2.397W") == -2.397
    assert parse_coord("41,5507") == 41.5507

def test_coords_es_spain():
    assert coords_es_spain(41.5507, -2.397) == True  # Argentona
    assert coords_es_spain(51, 0) == False           # Londres

def test_radiacion_teorica():
    # A mediodía en Argentona el 2 de Feb
    rad = radiacion_teorica(41.5507, 33, 12.0)
    assert 500 < rad < 800  # Debe ser razonable para mediodía
```

**Acción:** Crear tests para validar

---

### TAREA 5: Integrar en `app/ui/router.py` ⏳ PENDIENTE

#### 5.1 Identificar función principal
```python
# En app/ui/router.py, buscar donde se calcula respuesta de /api/panel/superior
# (Probablemente sea _estado_impl() o equivalente)
```

#### 5.2 Inyectar lógica de ubicación
```python
# Antes de los motores, añadir:

from core.location.location_module import detect_location, radiacion_teorica

# En _estado_impl():
    ubicacion = detect_location(system, CONFIG_PATH)
    indices["latitud"] = ubicacion["lat"]
    indices["longitud"] = ubicacion["lon"]
    indices["origen_ubicacion"] = ubicacion["origen"]
    
    # Calcular arco solar
    from tools.arco_solar import arco_solar
    hoy = datetime.datetime.now().timetuple().tm_yday
    arco = arco_solar(ubicacion["lat"], hoy)
    indices["arco_solar"] = {"valor": round(arco, 2), "estimado": ubicacion["origen"] != "manual"}
    indices["duracion_dia_h"] = {"valor": round(arco / 15.0, 2), "estimado": ubicacion["origen"] != "manual"}
    
    # ... resto de cálculos
```

**Acción:** Modificar router.py

#### 5.3 Verificar que motor obtiene contexto
```python
# En cada motor, verificar:
contexto = {
    "sensores": {...},
    "indices": {
        "latitud": 41.5507,        # ← DEBE EXISTIR
        "longitud": -2.397,        # ← DEBE EXISTIR
        "origen_ubicacion": "manual",  # ← DEBE EXISTIR
        "arco_solar": 172.5,       # ← DEBE EXISTIR
        "amanecer": "06:15",       # ← DEBE EXISTIR
        ...
    }
}
```

**Acción:** Verificar en cada motor crítico

---

### TAREA 6: Validar funcionamiento ⏳ PENDIENTE

#### 6.1 Prueba unitaria del módulo
```bash
cd c:\Users\kioko\Desktop\MeteoSerV3
python -m pytest tests/test_location_module.py -v
```

**Criterio de paso:** Todos los tests verdes

#### 6.2 Prueba de integración
```bash
# Arrancar servidor
python -m uvicorn main_asgi:app --host 0.0.0.0 --port 8080

# En otra terminal:
curl http://localhost:8080/api/panel/superior | jq '.indices | {latitud, longitud, origen_ubicacion, arco_solar, amanecer, atardecer}'

# Debe devolver:
# {
#   "latitud": 41.5507,
#   "longitud": -2.397,
#   "origen_ubicacion": "manual",
#   "arco_solar": 172.5,
#   "amanecer": "06:15",
#   "atardecer": "19:45"
# }
```

**Criterio de paso:** JSON válido con ubicación + astronomía

#### 6.3 Verificar que motores funcionan
```bash
# Probar Motor Luz Natural
curl http://localhost:8080/api/panel/superior | jq '.luz_natural'

# Debe contener recomendaciones, no vacío:
# { "recomendacion": "...", "valor": X, "explicacion": "..." }

# Probar Motor Ritmo Circadiano
curl http://localhost:8080/api/panel/superior | jq '.ritmo_circadiano'

# Debe contener recomendaciones de sueño, no vacío
```

**Criterio de paso:** Motores retornan datos, no {}

---

### TAREA 7: Documentar en Git ⏳ PENDIENTE

#### 7.1 Crear rama de trabajo
```bash
git checkout -b feature/restaurar-ubicacion-astronomia
```

#### 7.2 Commit 1: Módulo de ubicación
```bash
git add core/location/
git commit -m "feat: Módulo de ubicación y astronomía

- Función detect_location(): Detección jerárquica de coords
- Función radiacion_teorica(): Cálculo de radiación solar
- Función coords_valid(), parse_coord(): Validadores
- Funciones helper: hhmm_a_minutos(), minutos_a_hhmm()
- Tests unitarios en tests/test_location_module.py

Referencia: backup/ojo_20260202_102049 (líneas 1471-1730)"
```

#### 7.3 Commit 2: Integración en router
```bash
git add app/ui/router.py
git commit -m "feat: Integración de ubicación en respuesta de panel

- Detección de ubicación en _estado_impl()
- Cálculo de arco solar y duración del día
- Cálculo de amanecer/atardecer híbrido
- Índices astronómicos en respuesta JSON
- Contexto con ubicación para 40+ motores

Fixes: Motor Luz Natural, Motor Ritmo Circadiano, Motor Nocturno"
```

#### 7.4 Commit 3: Documentación
```bash
git add ANALISIS_PERDIDA_UBICACION_V26.md
git add PSEUDOCODIGO_RESTAURACION_UBICACION.md
git add MAPEO_DEPENDENCIAS_MOTORES.md
git commit -m "docs: Análisis de funciones perdidas en main_asgi.py

- ANALISIS_PERDIDA_UBICACION_V26.md: Qué se perdió y por qué es importante
- PSEUDOCODIGO_RESTAURACION_UBICACION.md: Lógica de cada función
- MAPEO_DEPENDENCIAS_MOTORES.md: Cómo afecta a los 6 motores

Referencia: backup/ojo_20260202_102049"
```

#### 7.5 Crear Pull Request
```
Título: Restaurar ubicación y astronomía en main_asgi.py

Descripción:
Esta PR restaura las funciones de ubicación, arco solar y astronomía que fueron removidas en una refactorización anterior.

## Cambios
- Módulo core/location/ con lógica de geocodificación
- Integración en app/ui/router.py
- Tests unitarios
- Documentación de cambios

## Impacto
- Restaura funcionalidad de 3 motores críticos (Luz Natural, Ritmo Circadiano, Nocturno)
- Mejora degradación de 3 motores más (Ambiental, Confort, Radiación/UV)
- Restablece física Vector #26 para cálculos de radiación

## Testing
- Tests unitarios: PASS
- Integración: PASS
- Motor Luz Natural: Funciona ✓
- Motor Ritmo Circadiano: Funciona ✓
- Motor Nocturno: Funciona ✓

Closes: (Crear issue si existe o dejar en blanco)
```

**Acción:** Crear PR y solicitar review

---

### TAREA 8: Monitoreo post-restauración ⏳ PENDIENTE

#### 8.1 Verificar logs de arranque
```bash
python -m uvicorn main_asgi:app --reload 2>&1 | grep -i "ubicacion\|location\|arco\|amanecer"

# Debe mostrar logs indicando:
# - Ubicación detectada: Argentona (41.5507, -2.397) [manual]
# - Arco solar: 172.5° (11.5 horas)
# - Amanecer: 06:15 / Atardecer: 19:45
```

**Acción:** Añadir logging en detect_location()

#### 8.2 Revisar respuesta JSON
```python
# Script para validar estructura
import requests
import json

resp = requests.get("http://localhost:8080/api/panel/superior")
data = resp.json()

# Validaciones
assert "indices" in data, "Falta 'indices'"
assert data["indices"].get("latitud"), "Falta latitud"
assert data["indices"].get("longitud"), "Falta longitud"
assert data["indices"].get("origen_ubicacion"), "Falta origen"
assert data["indices"].get("arco_solar"), "Falta arco_solar"
assert data["indices"].get("amanecer"), "Falta amanecer"
assert data["indices"].get("atardecer"), "Falta atardecer"

# Validar que motores tienen datos
assert data.get("luz_natural"), "Motor Luz Natural vacío"
assert data.get("ritmo_circadiano"), "Motor Ritmo Circadiano vacío"
assert data.get("nocturno"), "Motor Nocturno vacío"

print("✓ Todas las validaciones pasaron")
```

**Acción:** Ejecutar script de validación

#### 8.3 Comparar con backup
```bash
# Verificar que estructura coincide con backup
git show backup/ojo_20260202_102049:main_asgi.py | grep -A5 "indices\[\"latitud\"\]"

# Debe devolver mismo formato en respuesta actual
curl http://localhost:8080/api/panel/superior | jq '.indices.latitud'
```

**Acción:** Validar compatibilidad con backup

---

## 📊 RESUMEN DE TAREAS

| # | Tarea | Estado | Prioridad | Estimado |
|---|-------|--------|-----------|----------|
| 1 | Extraer funciones del backup | ✅ HECHO | P0 | - |
| 2 | Verificar si funciones existen | ⏳ TODO | P0 | 30 min |
| 3 | Identificar dónde va la lógica | ⏳ TODO | P0 | 1 h |
| 4 | Crear módulo centralizado | ⏳ TODO | P1 | 2 h |
| 5 | Integrar en router | ⏳ TODO | P1 | 1 h |
| 6 | Validar funcionamiento | ⏳ TODO | P1 | 1 h |
| 7 | Documentar en Git | ⏳ TODO | P2 | 30 min |
| 8 | Monitoreo post-restauración | ⏳ TODO | P2 | 1 h |

**Total estimado:** 8 horas de trabajo

---

## 🚀 PRÓXIMOS PASOS

1. **Hoy:**
   - [ ] Ejecutar búsquedas (Tarea 2)
   - [ ] Revisar app/ui/router.py (Tarea 3.1)

2. **Mañana:**
   - [ ] Crear módulo core/location/ (Tarea 4)
   - [ ] Crear tests (Tarea 4.3)

3. **Pasado:**
   - [ ] Integrar en router (Tarea 5)
   - [ ] Validar (Tarea 6)

4. **Final:**
   - [ ] Git + PR (Tarea 7)
   - [ ] Monitoreo (Tarea 8)

---

## 📞 NOTAS

- **Rama de referencia:** `backup/ojo_20260202_102049`
- **Líneas críticas:** 1471-1730 (ubicación + astronomía)
- **Documentación generada:**
  - `ANALISIS_PERDIDA_UBICACION_V26.md` ← Qué y por qué
  - `PSEUDOCODIGO_RESTAURACION_UBICACION.md` ← Cómo
  - `MAPEO_DEPENDENCIAS_MOTORES.md` ← Dónde se usa
  - `CHECKLIST_RESTAURACION_UBICACION.md` ← Este archivo

---

*Generado: 2 Feb 2026*
*Estado: ANÁLISIS COMPLETO, LISTO PARA IMPLEMENTACIÓN*
