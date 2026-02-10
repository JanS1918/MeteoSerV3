# 📍 REFERENCIAS RÁPIDAS: UBICACIONES EXACTAS

Use este documento para localizar rápidamente cada cambio implementado.

---

## 📄 main_asgi.py

### Import 1: Importes de Seguridad
**Ubicación**: Línea ~237-243
**Buscar**: `from core.security import (`
**Verificar**: 5 validadores importados
```python
from core.security import (
    MeteorologicalDomainValidator,
    SpecificationCompletenessValidator,
    PrecisionValidator,
    WhitelistEnforcer,
    SecurityOptimizationOrchestrator
)
```

### Instancia 1: Domain Validator
**Ubicación**: Línea ~247
**Buscar**: `app_instance.state.domain_validator =`
```python
app_instance.state.domain_validator = MeteorologicalDomainValidator()
```

### Instancia 2: Completeness Validator
**Ubicación**: Línea ~248
**Buscar**: `app_instance.state.completeness_validator =`
```python
app_instance.state.completeness_validator = SpecificationCompletenessValidator()
```

### Instancia 3: Precision Validator
**Ubicación**: Línea ~249
**Buscar**: `app_instance.state.precision_validator =`
```python
app_instance.state.precision_validator = PrecisionValidator()
```

### Instancia 4: Whitelist Enforcer
**Ubicación**: Línea ~250
**Buscar**: `app_instance.state.whitelist_enforcer =`
```python
app_instance.state.whitelist_enforcer = WhitelistEnforcer(".")
```

### Instancia 5: Security Orchestrator
**Ubicación**: Línea ~251
**Buscar**: `app_instance.state.security_orchestrator =`
```python
app_instance.state.security_orchestrator = SecurityOptimizationOrchestrator()
```

### Task 1: Security Optimization Loop
**Ubicación**: Línea ~256
**Buscar**: `asyncio.create_task(_security_optimization_loop())`
```python
asyncio.create_task(_security_optimization_loop())
```

### Función: _security_optimization_loop
**Ubicación**: Línea ~217-235
**Buscar**: `async def _security_optimization_loop():`
```python
async def _security_optimization_loop():
    """Ciclos de optimización de seguridad (cada 10 minutos) - auto-mejora de defensas"""
    while True:
        try:
            orchestrator = getattr(app_instance.state, "security_orchestrator", None)
            if orchestrator:
                result = orchestrator.execute_security_cycle()
                if result:
                    logger.info(
                        f"🛡️ Ciclo seguridad #{result.get('cycle_num')}: "
                        f"{result.get('vulnerabilities_discovered', 0)} gaps descubiertos, "
                        f"{result.get('security_duels_won', 0)} mejoras integradas, "
                        f"Seguridad actual: {result.get('current_security_score', 0):.1f}%"
                    )
        except Exception as e:
            logger.error(f"Error en security_optimization_loop: {e}")
        await asyncio.sleep(600)  # Cada 10 minutos
```

---

## 📄 core/monitoring/automated_duel_engine.py

### Ubicación: Función `duelo`
**Buscar**: `def duelo(`
**Línea aprox**: 96

### Validaciones de Seguridad: INICIO
**Ubicación**: Línea ~130 (después de logs iniciales)
**Buscar**: `# 🎯 VALIDACIONES DE SEGURIDAD`
```python
# 🎯 VALIDACIONES DE SEGURIDAD (antes de ejecutar/medir)
try:
    from core.security import (
        MeteorologicalDomainValidator,
        SpecificationCompletenessValidator,
        PrecisionValidator
    )
```

### Validación 1: MeteorologicalDomainValidator
**Ubicación**: Línea ~145
**Buscar**: `domain_validator = MeteorologicalDomainValidator()`
```python
domain_validator = MeteorologicalDomainValidator()
is_valid_domain, msg_domain = domain_validator.validate(
    parametro,
    getattr(externa, 'source_library', 'unknown'),
    getattr(externa, 'source_function', 'unknown')
)
if not is_valid_domain:
    logger.warning(f"🚫 Externa RECHAZADA (dominio): {msg_domain}")
    return DuelResult(
        timestamp=datetime.now(timezone.utc).timestamp(),
        parametro=parametro,
        interna_id=interna_id,
        externa_id=externa_id,
        externa_nombre=externa_nombre,
        duracion_segundos=time.time() - inicio,
        ganadora="internal",
        score_ganadora=100.0,
        score_perdedora=0.0,
        margen_victoria=100.0,
        detalles={"razon": "external_domain_invalid", "mensaje": msg_domain}
    )
```

### Validación 2: SpecificationCompletenessValidator
**Ubicación**: Línea ~165
**Buscar**: `spec_validator = SpecificationCompletenessValidator()`
```python
spec_validator = SpecificationCompletenessValidator()
is_valid_spec, errors_spec = spec_validator.validate(
    parametro,
    spec_dict,
    externa
)
if not is_valid_spec:
    logger.warning(f"🚫 Externa RECHAZADA (especificación incompleta): {errors_spec}")
    return DuelResult(
        timestamp=datetime.now(timezone.utc).timestamp(),
        parametro=parametro,
        interna_id=interna_id,
        externa_id=externa_id,
        externa_nombre=externa_nombre,
        duracion_segundos=time.time() - inicio,
        ganadora="internal",
        score_ganadora=100.0,
        score_perdedora=0.0,
        margen_victoria=100.0,
        detalles={"razon": "external_spec_incomplete", "errores": errors_spec}
    )
```

### Validación 3: PrecisionValidator
**Ubicación**: Línea ~185
**Buscar**: `precision_validator = PrecisionValidator()`
```python
precision_validator = PrecisionValidator()
required_precision = precision_validator.get_precision_for_parameter(parametro)
if required_precision is not None:
    logger.info(f"✅ {parametro} requiere precisión ±{required_precision}")
```

### Validaciones de Seguridad: FIN
**Ubicación**: Línea ~192 (aproximado)
**Buscar**: `except Exception as e:`
```python
except Exception as e:
    logger.warning(f"⚠️ Validadores de seguridad no disponibles: {e}")
    # Continuar sin validadores (fallback)
```

### Código Original Continúa
**Ubicación**: Línea ~194+
**Descripción**: Después del except, continúa el código original de duelo (sin cambios)

---

## 📄 core/security/__init__.py

**Ubicación**: `core/security/__init__.py`
**Contenido**: Exporta los 5 validadores

```python
from .meteorological_domain_validator import MeteorologicalDomainValidator
from .specification_completeness_validator import SpecificationCompletenessValidator
from .precision_validator import PrecisionValidator
from .whitelist_enforcer import WhitelistEnforcer
from .security_optimization_orchestrator import SecurityOptimizationOrchestrator

__all__ = [
    'MeteorologicalDomainValidator',
    'SpecificationCompletenessValidator',
    'PrecisionValidator',
    'WhitelistEnforcer',
    'SecurityOptimizationOrchestrator'
]
```

---

## 📊 RESUMEN DE CAMBIOS

| Archivo | Tipo | Líneas | Cambio |
|---------|------|--------|--------|
| main_asgi.py | Añadir | 217-235 | Función _security_optimization_loop |
| main_asgi.py | Añadir | 237-243 | Importes de core.security |
| main_asgi.py | Añadir | 247-251 | Instanciación de 5 validadores |
| main_asgi.py | Añadir | 256 | Task para security loop |
| automated_duel_engine.py | Añadir | 130-193 | Validaciones en función duelo |
| core/security/__init__.py | Crear | 22 | Exportes de validadores |
| core/security/meteorological_domain_validator.py | Crear | 380 | Validador de dominio |
| core/security/specification_completeness_validator.py | Crear | 290 | Validador de especificación |
| core/security/precision_validator.py | Crear | 250 | Validador de precisión |
| core/security/whitelist_enforcer.py | Crear | 240 | Protector de parámetros sagrados |
| core/security/security_optimization_orchestrator.py | Crear | 330 | Orquestador de ciclos |

**TOTAL DE CAMBIOS**: 11 archivos modificados/creados, 1,579 líneas

---

## 🔍 BÚSQUEDAS RÁPIDAS

### Encontrar all los validadores instantiados:
```bash
grep "app_instance.state.*validator" main_asgi.py
# Resultado: 5 líneas
```

### Encontrar imports de seguridad:
```bash
grep -n "from core.security import" main_asgi.py
# Resultado: 1 línea (237)
```

### Encontrar validaciones en duelo:
```bash
grep -n "domain_validator\|spec_validator\|precision_validator" core/monitoring/automated_duel_engine.py
# Resultado: 3 líneas
```

### Encontrar loop automático:
```bash
grep -n "_security_optimization_loop" main_asgi.py
# Resultado: 2 líneas (definición + task)
```

### Encontrar scipy.special bloqueada:
```bash
grep -n "scipy.special" core/security/meteorological_domain_validator.py
# Resultado: múltiples líneas
```

---

## 🚀 VALIDACIÓN DE INTEGRACIÓN

### Comando 1: Verificar Sintaxis
```bash
python -m py_compile main_asgi.py core/monitoring/automated_duel_engine.py core/security/*.py
# No debe mostrar errores
```

### Comando 2: Verificar Importes
```bash
python -c "from core.security import *; print('✅ Todos los validadores importan OK')"
```

### Comando 3: Verificar Instanciación
```bash
python -c "
from main_asgi import app
attrs = ['domain_validator', 'completeness_validator', 'precision_validator', 'whitelist_enforcer', 'security_orchestrator']
for attr in attrs:
    assert hasattr(app.state, attr), f'Falta {attr}'
print('✅ Todos los validadores instanciados OK')
"
```

### Comando 4: Ejecutar Tests
```bash
python test_validadores_rapido.py
# Debe mostrar: ✅ TODOS LOS TESTS PASARON CORRECTAMENTE
```

---

## 📋 CHECKLIST DE UBICACIÓN

- [ ] main_asgi.py línea ~237-243: Importes
- [ ] main_asgi.py línea ~247-251: Instanciaciones
- [ ] main_asgi.py línea ~256: Task
- [ ] main_asgi.py línea ~217-235: Función loop
- [ ] automated_duel_engine.py línea ~130-193: Validaciones
- [ ] core/security/: 6 archivos creados
- [ ] core/security/__init__.py: Exportes

Si todas las ubicaciones están correctas → **✅ IMPLEMENTACIÓN COMPLETA**

---

**Documento de Referencias - Enero 27, 2025**
**Sistema: MeteoSerV3 - Máxima Seguridad**
