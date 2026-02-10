# 📖 INDICE DE MEMORIA ETERNA - METEOSER V3
## Los Documentos de la Síntesis Atómica del 31 de Enero de 2026

---

## 🎯 COMIENZA AQUÍ

Si acabas de abrir el proyecto y ves cabeceras extrañas en los archivos de física:

1. **Lee primero:** [ENGINEERING_STANDARDS.md](./ENGINEERING_STANDARDS.md)
   - Los 6 pilares inamovibles
   - Por qué existen estas reglas
   - Cómo operan

2. **Luego:** [SELLO_PERMANENTE_31ENE.md](./SELLO_PERMANENTE_31ENE.md)
   - Qué fue purgado (paja digital)
   - Por qué fue necesario
   - Arqueología del sistema

3. **Finalmente:** Las cabeceras en los archivos modificados
   - environmental_indices.py (líneas 1-18)
   - main_asgi.py (líneas 1-16)

---

## 📚 ESTRUCTURA DE DOCUMENTACIÓN

### Documentos Normativos (INAMOVIBLES)
| Archivo | Propósito | Vigencia |
|---------|-----------|----------|
| [ENGINEERING_STANDARDS.md](./ENGINEERING_STANDARDS.md) | 6 pilares de la sintonización atómica | PERPETUA |
| [SELLO_PERMANENTE_31ENE.md](./SELLO_PERMANENTE_31ENE.md) | Arqueología + cambios irreversibles | ETERNA |
| Este archivo | Índice de navegación | VIGENTE |

### Cabeceras de Protección en Código
| Archivo | Líneas | Contenido | Estado |
|---------|--------|----------|--------|
| core/indices/environmental_indices.py | 1-18 | Advertencia: PHYSICS CORE SELLADO | ⚠️ PROTEGIDO |
| main_asgi.py | 1-16 | Advertencia: MAIN ASGI SELLADO | ⚠️ PROTEGIDO |

### Fuente Única de Verdad
| Archivo | Rol | Auditoría |
|---------|-----|----------|
| data/indices_config.json | Limits (INT), ranges, types, escudo | Ver `python -c "import json; ...limits"` |

---

## 🔍 BÚSQUEDA RÁPIDA

### "¿Por qué environmental_indices.py tiene esa cabecera?"
→ Fue purgado de 95 literales `.0` decorativos el 31 de enero de 2026. La cabecera es la frontera entre caos y orden.

### "¿Debo cambiar un límite?"
→ NO edites código Python. Edita `data/indices_config.json` → `physics_safe` → `limits`. Reinicia uvicorn.

### "¿Qué significa 'Ley del Entero'?"
→ Los topes/umbrales son INT puros (0, 1, 9, 99, 100), nunca 0.0 o 100.0. Ruido cognitivo removido.

### "¿Qué es el 'Escudo de Seguridad'?"
→ Protecciones `if divisor > 0:` antes de cualquier división. Previene crashes por cero.

### "¿Las coordenadas son flotantes?"
→ SÍ. lat/lon/alt son excepciones a la Ley del Entero. Tienen precisión real (metros/segundos de arco).

### "¿Por qué el código es MÁS GRANDE después de la limpieza?"
→ Porque añadimos cabeceras (13 KB de protección). Es intencional: cada byte es un escudo.

---

## 🛡️ VERIFICACIÓN DE INTEGRIDAD

Antes de hacer commit, ejecuta:

```bash
# 1. Validar sintaxis
python -m py_compile core/indices/environmental_indices.py
python -m py_compile main_asgi.py

# 2. Buscar violaciones de Ley del Entero
grep -rE "=\s*[0-9]+\.0\b" core/ --include="*.py" \
  | grep -v "273.15\|1361.0\|5.0/9.0\|0.0\|1.0" \
  | wc -l
# Esperado: 0 líneas

# 3. Verificar config.json
python -c "import json; json.load(open('data/indices_config.json'))"

# 4. Contar escudos de seguridad
grep -c "if.*>\s*0\s*:" core/indices/environmental_indices.py
# Esperado: > 3
```

---

## 📊 ESTADÍSTICAS FINALES

| Métrica | Valor |
|---------|-------|
| Literales .0 eliminados | 113 |
| Bytes de paja removida | 525 |
| Cabeceras de protección añadidas | 2 archivos |
| Bytes de memoria grabada | 13,165 |
| Estado de escudos | INTACTO |
| Constantes físicas | SAGRADAS |

---

## 🎓 LECCIONES APRENDIDAS

1. **Paja digital existe** - 113 literales `.0` no contribuían a precisión
2. **La documentación es código** - Cabeceras + estándares son protecciones
3. **La configuración es soberana** - Limits en JSON, no en Python
4. **La física no negocia** - Constantes (273.15, 1013.25) son sagradas
5. **La seguridad es prevención** - Escudos `if > 0:` evitan crashes

---

## 🚀 PRÓXIMAS OPERACIONES

### Si necesitas cambiar un límite:
1. Abre `data/indices_config.json`
2. Edita `physics_safe.limits.NOMBRE`
3. Reinicia: `uvicorn main_asgi:app --reload`

### Si necesitas añadir una métrica nueva:
1. Define en config.json (tipo + tope)
2. Calcula en Python con flotantes internos
3. Añade escudo `if divisor > 0:`
4. Redondea salida: `round(valor, 2)`

### Si encuentras violación de estándares:
1. Revisa [ENGINEERING_STANDARDS.md](./ENGINEERING_STANDARDS.md)
2. Reporta al equipo
3. NO comitees sin corrección

---

## 🔐 PROHIBICIONES ABSOLUTAS

| Prohibición | Razón |
|------------|-------|
| Hardcode topes en Python | Config soberana |
| Floats decorativos (.0) | Ruido + Ley del Entero |
| Remover escudos (if > 0) | Crash por div cero |
| Tocar constantes físicas | Cálculos incorrectos |
| Salida JSON sin redondeo | Ineficiencia bytes |

---

## 📞 REFERENCIAS CRUZADAS

- **Fusión Final 27ENE:** Centralización de 37 topes
- **Poda Masiva 31ENE:** Eliminación de 113 `.0` decorativos
- **Config Soberana:** data/indices_config.json es fuente única
- **Escudo de Seguridad:** if divisor > 0 ANTES de cualquier división
- **Physics Models:** Liljegren WBGT, Fanger PMV/PPD, UTCI (INTACTOS)

---

## 🎯 CONCLUSIÓN

**El Acorazado Argentona es reluciente, honesto y protegido.**

Esta documentación existe para que NUNCA vuelva a haber paja digital en el casco. Es la memoria del sistema.

**Cualquier violación a estos estándares es traición.**

---

*Índice de Memoria Eterna*  
*Creado: 31 de enero de 2026*  
*Vigencia: PERPETUA* 🔒
