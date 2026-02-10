# 🎯 GUÍA DE USO - OPTIMIZACIONES IMPLEMENTADAS

## 1️⃣ MÓDULO DE UBICACIÓN/ASTRONOMÍA

### Importar
```python
from core.location import (
    detect_location,
    arco_solar,
    radiacion_teorica,
    coords_valid,
    parse_coord,
)
```

### Detectar ubicación
```python
# Desde SystemManager o SystemCore
coords = detect_location(system)
print(f"Ubicación: {coords['lat']}, {coords['lon']}")
print(f"Origen: {coords['origen']}")  # "manual", "sensor", "manager", "fallback"
```

### Calcular arco solar
```python
from datetime import datetime

hoy = datetime.now().timetuple().tm_yday
arco = arco_solar(lat=41.5507, day_of_year=hoy)
duracion_dia = arco / 15.0  # Convertir a horas

print(f"Arco solar: {arco:.1f}°")
print(f"Duración del día: {duracion_dia:.1f} horas")
```

### Calcular radiación teórica
```python
hora_decimal = 12.5  # 12:30
rad = radiacion_teorica(
    lat_deg=41.5507,
    day_of_year=hoy,
    hora_decimal=hora_decimal
)

print(f"Radiación a las 12:30: {rad:.1f} W/m²")
```

### Validar coordenadas
```python
if coords_valid(41.5507, -2.3968):
    print("Coordenadas válidas")

if coords_es_spain(41.5507, -2.3968):
    print("Está en España")

# Parsear múltiples formatos
lat = parse_coord("41.5507N")    # → 41.5507
lon = parse_coord("2.3968W")     # → -2.3968
```

---

## 2️⃣ EJECUTAR AUDITORÍAS MANUALMENTE

### Auditoría de Redundancia
```bash
python scripts/auditar_redundancia.py
```

Verifica que **cada variable en el Bus tiene UN SOLO productor** (No hay redundancia).

### Generar Mapa de Dependencias
```bash
python scripts/generar_mapa_dependencias.py
```

Crea:
- `docs/MAPA_DEPENDENCIAS_V20.json` (estructura completa)
- `docs/MAPA_DEPENDENCIAS_V20.md` (visualización)

### Ejecutar TODAS las Auditorías
```bash
python scripts/run_all_audits.py
```

Ejecuta en orden:
1. Auditoría de redundancia
2. Mapa de dependencias
3. Auto-auditoría del sistema
4. Registro en histórico

---

## 3️⃣ TESTS

### Ejecutar todos los tests de ubicación
```bash
pytest tests/test_location_module.py -v
```

Resultado esperado:
```
============================= 26 passed in 0.26s ==============================
```

### Ejecutar tests específicos
```bash
# Solo tests de validación
pytest tests/test_location_module.py::TestCoordsValidation -v

# Solo tests de cálculos
pytest tests/test_location_module.py::TestArcoSolar -v

# Solo smoke tests
pytest tests/test_location_module.py::test_smoke_import -v
```

### Con cobertura
```bash
pytest tests/test_location_module.py --cov=core.location --cov-report=html
```

---

## 4️⃣ CI/CD AUTOMÁTICO

### Triggers
El pipeline CI.yml se ejecuta automáticamente:

- ✅ En cada `git push` a main/develop
- ✅ En cada pull request
- ✅ Diariamente a las 6 AM UTC

### Ver resultados en GitHub
```
https://github.com/tu-usuario/MeteoSerV3/actions
```

### Steps ejecutados
1. Setup Python
2. Install dependencies
3. Lint (flake8)
4. Format check (black)
5. Unit tests (pytest)
6. **Audit redundancy** ← Nuevo
7. **Dependency map** ← Nuevo
8. **System audit** ← Nuevo
9. **Location validation** ← Nuevo
10. **Formula validation** ← Nuevo
11. Upload coverage artifacts
12. Upload audit reports
13. Print summary

### Descargar reportes
En GitHub Actions, la pestaña "Artifacts":
- `coverage-report-py3.11` - Cobertura de tests
- `audit-reports-py3.11` - Reportes de auditoría

---

## 5️⃣ STRUCTURE DE CARPETAS

```
core/location/                          ← Nuevo módulo
├── __init__.py                         # Exports
└── location_module.py                  # Implementación

scripts/
├── auditar_redundancia.py              # Verificación redundancia
├── generar_mapa_dependencias.py        # Exportar grafo
├── run_all_audits.py                   # ← Nuevo orquestador
└── ...otros scripts

tests/
├── test_location_module.py             # ← Nuevos 26 tests
└── ...otros tests

.github/workflows/
└── ci.yml                              # ← Actualizado (15 pasos)
```

---

## 6️⃣ INTEGRACIÓN CON MOTORES

Los 6 motores que dependen de ubicación/astronomía:

```python
from core.location import detect_location, arco_solar

class MotorLuzNatural:
    def calcular(self, system):
        coords = detect_location(system)
        arco = arco_solar(coords['lat'], dia_año)
        # Usar arco para cálculos...
```

Similar para:
- **MotorRitmoCircadiano**
- **MotorNocturno**
- **MotorAmbiental**
- **MotorConfort**
- **MotorRadiacionUV**

---

## 7️⃣ TROUBLESHOOTING

### "ImportError: No module named 'core.location'"
```bash
# Asegúrate de estar en el directorio raíz del proyecto
pwd
# Debería mostrar: .../MeteoSerV3

# Verifica que existe
ls core/location/
```

### "tools.amanecer_atardecer not available"
Es un warning, no error. El módulo `calcular_anejo_astronomico()` tiene fallback.

### Tests fallan por pytest no encontrado
```bash
pip install pytest pytest-cov
```

### Workflow CI no se ejecuta
```
1. Ve a .github/workflows/ci.yml
2. Verifica que existe y tiene sintaxis YAML correcta
3. Haz push a main o develop
4. Revisa GitHub Actions
```

---

## 8️⃣ VERSIONADO

**Versión actual:** 1.0  
**Fecha:** 9 de febrero de 2026

Cambios futuros:
- [ ] Integrar ideas_master con SystemCore
- [ ] Vectorizar microphysics
- [ ] Detector automático de imports circulares

---

## 📚 REFERENCIAS

Documentación completa:
- [OPTIMIZACIONES_IMPLEMENTADAS_20260209.md](OPTIMIZACIONES_IMPLEMENTADAS_20260209.md) - Resumen ejecutivo
- [core/location/location_module.py](core/location/location_module.py) - Código fuente
- [tests/test_location_module.py](tests/test_location_module.py) - Tests
- [.github/workflows/ci.yml](.github/workflows/ci.yml) - Pipeline CI/CD

---

**¿Preguntas?** Revisa los docstrings en el código:
```python
python -c "from core.location import detect_location; help(detect_location)"
```
