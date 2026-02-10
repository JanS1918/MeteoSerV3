# 📋 FALLBACKS ISA DEL SISTEMA METEOSER V3
**Estado**: ✅ ACTUALIZADO 09/02/2026 13:13  
**Versión**: 1.0.0  
**Auditoría**: Completa

---

## ⚠️ REGLA DE ORO: FALLBACKS SIN DESINFORMACIÓN

El sistema MateoSer utiliza fallbacks ISA (Atmósfera Estándar Internacional) **ÚNICAMENTE** como último recurso. Cada fallback registra un WARNING en los logs.

**CRÍTICO**: No usar valores ISA para sensores que NO están conectados → Usar `None` en su lugar.

---

## 📊 TABLA MAESTRA DE FALLBACKS

| Índice | Sensor/Variable | Fallback | Ubicación | Razón | Comentario |
|--------|-----------------|----------|-----------|-------|-----------|
| **1** | **CO2** | ~~400 ppm~~ → `None` | `bus_expander.py` líneas 2786, 3301 | Sin sensor conectado | ✅ CORREGIDO 09/02 (ahora muestra "Sin sensor") |
| **2** | Temperatura | 15.0°C (ISA) | `bus_expander.py` múltiples | Sensor faltante | Última opción si input fallido |
| **3** | Humedad | 50.0% (ISA) | `bus_expander.py` múltiples | Sensor faltante | No es dato real |
| **4** | Presión | 1013.25 hPa (ISA) | `environmental_indices.py` | Barómetro averiado | ⚠️ Crítico: la fórmula Deardorff requiere presión real |
| **5** | Radiación Solar | 0.0 W/m² | Sistema | Sin sensor | Asume noche/nublado |
| **6** | Velocidad Viento | 0.0 m/s | `bus_expander.py` | Anemómetro averiado | Asume calma chicha |
| **7** | Punto Rocío | Desde T+HR | `environmental_indices.py` | Sensor faltante | Derivado (no es fallback directo) |
| **8** | Radiación Neta | Calculada | `environmental_indices.py` | No disponible | Usa algoritmo Kneizyk |
| **9** | Evapotranspiración ET0 | FAO-56 Penman | `environmental_indices.py` | Sensor faltante | Fallback científico respaldado |
| **10** | Densidad Aire | CIPM 2007 | `physics_engine_2026.py` | No disponible | Calculada desde T, P, HR |
| **11** | Altitud | ESTACION.ALTITUD | `constants.py` | No disponible | Argentona = 100m (SRTM) |
| **12** | Latitud/Longitud | ESTACION.LAT/LON | `constants.py` | GPS sin señal | Argentona: 41.55327°N, 2.39684°E |
| **13** | Temperatura Suelo | = Temperatura aire | `bus_expander.py` | Sensor faltante | Aproximación grosera |
| **14** | Humedad Interior | 50% | `bus_expander.py` | Sin sensor | Neutral (no es real) |
| **15** | Temperatura Interior | 20°C | `bus_expander.py` | Sin sensor | Asume confort estándar |

---

## 🔴 FALLBACKS CRÍTICOS (NO USAR)

### ❌ CO2 = 400 ppm (ISA)
- **Problema**: Si no tienes sensor, mostrar 400 ppm es desinformante
- **Solución**: Mostrar `None` o "Sin sensor"
- **Implementado**: ✅ `bus_expander.py` actualizado 09/02/2026

### ❌ Presión = 1013.25 hPa (ISA)
- **Problema**: El sistema Deardorff/Liljegren REQUIERE presión real
- **Riesgo**: Cálculos de WBGT completamente errados
- **Solución**: 
  ```python
  if presion is None:
      logger.error("REQUIERE BARÓMETRO REAL - No usar ISA")
      presion = None  # Retornar error, no valor
  ```

### ❌ Temperatura = 15°C (ISA)
- **Problema**: Afecta todos los cálculos termales
- **Riesgo**: Errores en confort, ET0, radiación neta
- **Solución**: Requiere sensor

---

## 🟡 FALLBACKS SIN RIESGO CRÍTICO

### Viento = 0 m/s
- Asume calma
- Provoca subestimación de enfriamiento
- Aceptable para diagnóstico temporal

### Radiación = 0 W/m²
- Asume noche/nublado
- Bajo impacto (ET0 igualmente bajo)
- Aceptable

### Densidad aire (CIPM 2007)
- Derivada de T, P, HR → No es fallback
- Precisión ±0.2%
- ✅ Completamente aceptable

---

## 🟢 FALLBACKS ROBUSTOS

### ET0 (Penman-Monteith FAO-56)
- Fórmula científica respaldada por FAO
- Precisión ±5-10%
- ✅ Mejor que desechar datos

### Punto Rocío (Magnus modificado)
- Derivado de T + HR
- Precisión ±0.5°C
- ✅ No es fallback, es derivado

### Evapotranspiración Real (ETr)
- Ajustada por estrés hídrico
- Usa Kc de cultivo estándar
- ✅ Aceptable para agricultura

---

## 📍 UBICACIÓN DE CODE: DÓNDE ESTÁN LOS FALLBACKS

### `core/system/bus_expander.py`
```python
# Línea 2786: CO2 en calidad aire
co2 = self.system.data.get("co2", None)  # ✅ Ahora None, no 400

# Línea 3301: CO2 en confort interior  
co2 = self.system.data.get("co2", None)  # ✅ Mismo cambio

# Otras variables:
temp_exterior = self.system.data.get("temperatura", 15.0)  # ISA
humedad = self.system.data.get("humedad", 50.0)  # ISA
presion = self.system.data.get("presion_barometrica", 101325.0)  # ISA (⚠️)
```

### `core/indices/environmental_indices.py`
```python
# Línea 910-960: _get_isa_default() - función maestra de fallbacks
def _get_isa_default(path: str) -> Optional[float]:
    """
    ⚛️ LEY DE PUREZA FÍSICA 2026:
    - Estos valores son FALLBACKS DE EMERGENCIA
    - Se emite WARNING cada vez que se usan
    """
    cfg = _load_physics_safe_config()
    defaults = cfg.get("isa_defaults", {})
    # ... retorna valores del config, logs WARNING
```

### `core/system/constants.py`
```python
class ESTACION:
    LATITUD = 41.553267  # Argentona
    LONGITUD = 2.396845
    ALTITUD = 100  # SRTM
```

### `core/indices/physics_engine_2026.py`
```python
# Densidad aire CIPM 2007 - ✅ Completamente derivada, no fallback
densidad = densidad_aire_cipm_2007(T_K, presion_Pa, HR_fraccion)
```

---

## 🔍 CÓMO VERIFICAR SI SE USAN FALLBACKS

### Ver Logs
```bash
grep -i "fallback\|ISA\|SIN_SENSOR" logs/meteoser.log
```

### En Bus (en vivo)
```python
# Leer valores del bus
valor_co2 = bus.leer("co2_nivel")  # None si sin sensor
categoria_co2 = bus.leer("co2_categoria")  # "Sin sensor" si no disponible
```

### En API
```bash
curl http://localhost:8080/api/panel/central
# Buscar "co2_nivel": null en JSON
```

---

## 🛠️ CÓMO CAMBIAR UN FALLBACK

### Ejemplo: Cambiar fallback de CO2
1. **Ubicar**:
   ```bash
   grep -n "co2.*400" core/system/bus_expander.py
   ```

2. **Editar**:
   ```python
   # ANTES:
   co2 = self.system.data.get("co2", 400.0)
   
   # DESPUÉS:
   co2 = self.system.data.get("co2", None)
   
   # LUEGO manejar None:
   if co2 is not None:
       self.bus.publicar("co2_nivel", co2, "ppm")
   else:
       self.bus.publicar("co2_nivel", None, "ppm")
   ```

3. **Verificar**:
   ```bash
   python -m pytest tests/test_bus_expander.py::test_co2_sin_sensor
   ```

---

## 📝 RESUMEN DE CAMBIOS 09/02/2026

| Cambio | Antes | Después | Razón |
|--------|-------|---------|-------|
| **CO2 fallback** | 400 ppm (ISA) | `None` | Evitar desinformación |
| **CO2 en calidad aire** | Publicaba siempre | Condición `if co2` | No engañar |
| **CO2 en confort interior** | Publicaba siempre | Condición `if co2` | Score neutral si sin sensor |
| **CO2 en ventilación** | Usaba 400 para cálculo | Solo usa HR si `None` | Lógica correcta |
| **Logs CO2** | Mostraba valor ISA | Muestra "SIN_SENSOR" | Claridad |

---

## ⚡ CHECKLIST: ANTES DE USAR FALLBACKS

- [ ] ¿El sensor falta o está averiado?
- [ ] ¿Es crítico para el cálculo?
  - YES → Retornar `None` o error
  - NO → Usar fallback + WARNING
- [ ] ¿He testeado con valores reales?
- [ ] ¿Los logs muestran que se usó fallback?
- [ ] ¿El usuario sabe que es un estimado?

---

**Documento generado automáticamente**  
**Mantener actualizado con cada cambio en fallbacks**
