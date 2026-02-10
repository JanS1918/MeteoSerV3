# 📚 ÍNDICE DE DOCUMENTACIÓN - Restauración de Ubicación y Astronomía

## 🎯 PUNTO DE PARTIDA

**Tarea del usuario:** "Revisar qué se perdió de ubicación/arco solar/astronomía en main_asgi.py (rama backup/ojo_20260202_102049)"

**Resultado:** 6 documentos de análisis + pseudocódigo + checklist

---

## 📖 DOCUMENTOS GENERADOS

### 1️⃣ **RESUMEN_UBICACION_ASTRONOMIA_PERDIDAS.md** (6.6 KB)
**Para:** Ejecutivos, decisión rápida
- ¿Qué pasó? (síntesis)
- ¿Por qué importa? (impacto)
- ¿Qué falta? (datos perdidos)
- Estimado de trabajo
- Próximos pasos

**Leer si:** Necesitas entender el panorama general en 5 minutos

---

### 2️⃣ **ANALISIS_PERDIDA_UBICACION_V26.md** (13.8 KB)
**Para:** Ingenieros, análisis técnico profundo
- Lista de funciones perdidas (10)
- Lógica de cada una (pseudocódigo detallado)
- Dónde se llamaban en flujo
- Importancia para Vector #26
- Archivos de apoyo necesarios

**Leer si:** Necesitas entender CADA FUNCIÓN que se perdió

---

### 3️⃣ **PSEUDOCODIGO_RESTAURACION_UBICACION.md** (17.1 KB)
**Para:** Programadores, implementación
- 9 funciones con pseudocódigo completo
- Casos de uso para cada función
- Flujo de datos (diagrama)
- Funciones auxiliares
- Integración en contexto

**Leer si:** Vas a codificar la restauración

---

### 4️⃣ **MAPEO_DEPENDENCIAS_MOTORES.md** (12.2 KB)
**Para:** Arquitectos, validación
- Por cada motor (6 total):
  - Qué necesita
  - Estado actual
  - Síntomas de fallo
  - Líneas en backup
- Matriz de impacto
- Recomendación de restauración

**Leer si:** Necesitas saber cómo cada motor se ve afectado

---

### 5️⃣ **CHECKLIST_RESTAURACION_UBICACION.md** (14.4 KB)
**Para:** Project managers, ejecución
- Tarea 1-8 (cada una con subtareas)
- Estado actual vs. esperado
- Criterios de paso para validación
- Matriz de tareas (prioridad + estimado)
- Commit messages sugeridos
- PR template

**Leer si:** Vas a gestionar la restauración (sprints, tracking)

---

### 6️⃣ **ACTUALIZACION_HALLAZGOS_UBICACION.md** (8.4 KB)
**Para:** Ingenieros, búsquedas en codebase
- Ubicación actual de funciones (¿dónde migraron?)
- Qué está en `core/arcos_solares.py` (actual)
- Qué está en `app/ui/viewmodel.py` (actual)
- Qué REALMENTE falta
- Acciones correctivas

**Leer si:** Verificaste el codebase y necesitas actualizar análisis

---

### 7️⃣ **ANALISIS_FINAL_UBICACION.md** (Este documento)
**Para:** Todos, resumen ejecutivo
- Situación resumida (tabla)
- Lo que realmente falta (crítica/media)
- Checklist mínimo (5 pasos)
- Estado de motores
- Estimado final: 3 horas

**Leer si:** Necesitas decisión rápida sobre si hacerlo/cómo hacerlo

---

## 🗂️ FLUJO DE LECTURA RECOMENDADO

### Escenario A: "Necesito entender qué pasó" (15 min)
1. Leer: `RESUMEN_UBICACION_ASTRONOMIA_PERDIDAS.md`
2. Ver: Tabla de "¿QUÉ PASÓ?" en `ANALISIS_FINAL_UBICACION.md`

### Escenario B: "Necesito saber si es crítico" (30 min)
1. Leer: `RESUMEN_UBICACION_ASTRONOMIA_PERDIDAS.md`
2. Leer: `MAPEO_DEPENDENCIAS_MOTORES.md` (secciones de motores críticos)
3. Ver: Checklist en `ANALISIS_FINAL_UBICACION.md`

### Escenario C: "Voy a implementar la restauración" (1-2 horas)
1. Leer: `ANALISIS_PERDIDA_UBICACION_V26.md` (entender qué se perdió)
2. Leer: `PSEUDOCODIGO_RESTAURACION_UBICACION.md` (ver pseudocódigo)
3. Leer: `CHECKLIST_RESTAURACION_UBICACION.md` (pasos exactos)
4. Leer: `ACTUALIZACION_HALLAZGOS_UBICACION.md` (verificar en codebase)
5. Ejecutar tareas del checklist

### Escenario D: "Soy project manager" (45 min)
1. Leer: `RESUMEN_UBICACION_ASTRONOMIA_PERDIDAS.md`
2. Leer: `CHECKLIST_RESTAURACION_UBICACION.md` (matriz de tareas)
3. Asignar: Tarea 1-3 a ingenieros hoy
4. Plannear: Sprint de implementación

---

## 🔍 BÚSQUEDA RÁPIDA

### "¿Qué función X se perdió?"
→ Ir a: `ANALISIS_PERDIDA_UBICACION_V26.md` → Buscar nombre de función

### "¿Cómo codifico X?"
→ Ir a: `PSEUDOCODIGO_RESTAURACION_UBICACION.md` → Buscar "FUNCIÓN" + número

### "¿Cómo afecta a motor Y?"
→ Ir a: `MAPEO_DEPENDENCIAS_MOTORES.md` → Buscar nombre del motor

### "¿Qué pasos debo seguir?"
→ Ir a: `CHECKLIST_RESTAURACION_UBICACION.md` → TAREA 1-8

### "¿Realmente falta o está migrado?"
→ Ir a: `ACTUALIZACION_HALLAZGOS_UBICACION.md` → Tabla de "ESTADO ACTUAL VS. ESPERADO"

---

## 📊 MATRIZ DE UBICACIÓN DE TÓPICOS

| Tópico | RESUMEN | ANÁLISIS | PSEUDO | MAPEO | CHECKLIST | ACTUALIZACIÓN |
|--------|---------|----------|-------|-------|-----------|---------------|
| Qué se perdió | ✅ | ✅ | - | ✅ | - | ✅ |
| Cómo codificarlo | - | - | ✅ | - | ✅ | - |
| Impacto en motores | ✅ | - | - | ✅ | - | - |
| Plan de acción | ✅ | - | - | - | ✅ | - |
| Pseudocódigo | - | ✅ | ✅ | - | - | - |
| Estado actual codebase | - | - | - | - | - | ✅ |
| Estimado tiempo | ✅ | - | - | - | ✅ | - |
| Tests | - | - | - | - | ✅ | - |

---

## 🎯 DECISIÓN: ¿HACER O NO HACER?

### Criterios Críticos para SÍ:
- ❌ Motor Luz Natural completamente roto
- ❌ Motor Ritmo Circadiano completamente roto
- ❌ Motor Nocturno sin índices astronómicos
- 🔴 Física Vector #26 sin validación de radiación

### Criterio de Viabilidad:
- ✅ Funciones solo parcialmente migradas (recuperables)
- ✅ Pseudocódigo disponible
- ✅ Estimado solo 3 horas de trabajo
- ✅ Herramientas externas aún funcionan

### Recomendación:
**✅ HACER INMEDIATAMENTE**

---

## 📞 SOPORTE

### Si necesitas...

**Entender qué está en backup:**
```bash
git show backup/ojo_20260202_102049:main_asgi.py | sed -n '1471,1730p' > /tmp/funcs.txt
# Comparar con: ANALISIS_PERDIDA_UBICACION_V26.md
```

**Ver funciones en codebase actual:**
```bash
grep -r "radiacion_teorica\|ventana_observacion" core/ app/
# Comparar con: ACTUALIZACION_HALLAZGOS_UBICACION.md
```

**Validar tareas completadas:**
```bash
# Seguir: CHECKLIST_RESTAURACION_UBICACION.md
# Ejecutar cada tarea y marcar como ✅
```

---

## 📋 CHECKLIST RÁPIDO

- [ ] Decidir: ¿Hacer la restauración?
- [ ] Leer: Documento(s) relevantes para tu rol
- [ ] Verificar: Búsquedas en codebase (si ingeniería)
- [ ] Planificar: Tareas con estimados (si PM)
- [ ] Ejecutar: Pasos del checklist (si dev)
- [ ] Validar: Criterios de paso (si QA)

---

## 📈 IMPACTO ESTIMADO

### Antes (ahora):
- Motor Luz Natural: ❌ Inoperante
- Motor Ritmo Circadiano: ❌ Inoperante
- Motor Nocturno: ⚠️ Degradado
- Física Vector #26: ⚠️ Sin validación

### Después (con restauración):
- Motor Luz Natural: ✅ Funcional
- Motor Ritmo Circadiano: ✅ Funcional
- Motor Nocturno: ✅ Funcional
- Física Vector #26: ✅ Validada

**Ganancia:** 3 motores restaurados, física correcta

---

## 🔗 REFERENCIAS EXTERNAS

### Backup donde estaba la lógica:
- **Rama:** `backup/ojo_20260202_102049`
- **Archivo:** `main_asgi.py`
- **Líneas:** 1471-1730

### Archivos del sistema:
- `core/arcos_solares.py` → Lógica actual (parcial)
- `app/ui/viewmodel.py` → Integración (parcial)
- `tools/arco_solar.py` → Función externa (funciona)
- `tools/amanecer_atardecer.py` → Función externa (funciona)

---

## 🚀 ¿LISTO PARA EMPEZAR?

### Si eres **Decisor**:
→ Lee `RESUMEN_UBICACION_ASTRONOMIA_PERDIDAS.md` (6 min) → Aprobar/Rechazar

### Si eres **Gestor**:
→ Lee `CHECKLIST_RESTAURACION_UBICACION.md` (15 min) → Crear tareas

### Si eres **Ingeniero**:
→ Lee `PSEUDOCODIGO_RESTAURACION_UBICACION.md` (30 min) → Codificar

### Si eres **Revisor**:
→ Lee `MAPEO_DEPENDENCIAS_MOTORES.md` (20 min) → Validar impacto

---

**Generado:** 2 Feb 2026  
**Estado:** ANÁLISIS COMPLETO, PRONTO PARA ACCIÓN  
**Documentos:** 7 archivos (83.2 KB total)  
**Cobertura:** 100% de funciones perdidas identificadas

*Para comenzar: Abre el archivo relevante según tu rol (arriba) →*
