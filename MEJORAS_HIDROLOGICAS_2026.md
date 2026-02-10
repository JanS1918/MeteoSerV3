# Mejoras Hidrológicas MeteoSerV3 - Febrero 2026
## Infiltración, Escorrentía, SPI (Sin Hardware Adicional)

**Fecha:** 9 de febrero de 2026  
**Modificaciones:** `core/indices/hidrology_indices.py` (nuevo) + `core/indices/environmental_indices.py`  
**Objetivo:** Calcular balance hídrico sin WH51 (sensor de humedad del suelo)

---

## 1. ¿POR QUÉ ESTAS FÓRMULAS?

### WH51 da humedad DIRECTA
- Solo dice: "suelo tiene X% de agua"
- NO dice cuánta agua entra, cuánta sale, ni cuál es el riesgo de sequía real

### Infiltración + Escorrentía COMPLEMENTAN:
- **Infiltración**: cuánta lluvia realmente empapar el suelo
- **Escorrentía**: cuánta lluvia corre por la superficie (no entra)
- Juntas = **balance hídrico real** sin depender de WH51

### SPI = "SEQUÍA VERDADERA"
- WH51: solo humedad **instantánea**
- SPI: precipitación acumulada vs histórico → revela sequías **profundas**
  - -2.0: 1 año sin lluvia (catastrófico)
  - -1.0 a -1.5: sequía moderada (riego urgente)
  - +1.0: lluvia buena
  - +2.0: inundación eventual

---

## 2. IMPLEMENTACIÓN: INFILTRACIÓN + ESCORRENTÍA

### Modelo: Green-Ampt Simplificado

```python
f(t) = Ks * (1 + S*θ_s / F_acumulada)
```

Donde:
- **Ks**: Conductividad saturada (mm/h)
  - Arenoso: 25 mm/h (drena rápido)
  - Franco: 6 mm/h (equilibrado)
  - Arcilloso: 0.3 mm/h (retiene agua)
  
- **S**: Absorción capilar (mm)
- **θ_s**: Porosidad total (%)

### ¿Cómo estima tipo de suelo sin sensor WH51?

```
HR > 75% + T-trend negativa  → ARCILLOSO (retiene, drena lentamente)
HR 40-75%                     → FRANCO (normal)
HR < 40%                      → ARENOSO (seco, drena rápido)
```

### Resultado publicado al Bus:

```
infiltracion_mm_h: 6.5          # Verde: agua entra al suelo
escorrentia_mm_h: 2.3           # Rojo: agua que se pierde en superfice
coef_escorrentia: 0.42          # Depende: pendiente + tipo_suelo + saturación
tipo_suelo_estimado: franco     # Inference
```

### ¿Qué hace con esto?

**Agronomía:**
- Si escorrentía > 30%: baja eficiencia de riego
- Si infiltración < 1 mm/h: suelo endurecido

**Gestión de agua:**
- Escorrentía alta = riesgo de erosión
- Escorrentía baja = buena absorción

---

## 3. SPI: SEQUÍA ESTANDARIZADA (3, 6, 12 MESES)

### Fórmula

```
SPI = (P_acumulado - media_histórica) / desv_estándar
```

### Ejemplo práctico

```
Histórico 12 meses: [75, 80, 60, 55, 90, 70, ...]  (mm/mes)

Media = 70 mm/mes
Desv = 15 mm/mes

Mes actual: 40 mm

SPI-12 = (40 - 70) / 15 = -2.0  ← EXTREMADAMENTE SECO
         (alertan sequía severa)
```

### Ventajas sobre "HR baja":

| Métrica | HR baja | SPI bajo |
|---------|---------|----------|
| Mide | Humedad instantánea | Tendencia 3/6/12 meses |
| Contexto | Hoy está seco | Llevamos meses sin lluvia |
| Error | Falsos positivos con rocío | Ninguno (estadístico) |

### Resultado publicado (3 ventanas):

```
spi_3m: -1.3              # Últimos 3 meses: SECO
categoria_spi_3m: Seco
spi_6m: -0.8              # Últimos 6 meses: Normal-Seco
categoria_spi_6m: Normal
spi_12m: +0.2             # Año completo: Normal
categoria_spi_12m: Normal
```

**Interpretación:**
- Últimos 3 meses: lluvia escasa
- Pero año en general: normal
- → No es sequía crónica, es patrón estacional

---

## 4. ARCHIVOS MODIFICADOS

### Nuevo: `core/indices/hidrology_indices.py` (195 líneas)

**Clases:**
- `InfiltracionEscorrentia`: Cálculos Green-Ampt
- `SPICalculator`: Índice Estandarizado Precipitación

**Funciones envolventes:**
```python
calcular_infiltracion_escorrentia(lluvia_24h, lluvia_rate, HR, T, pendiente)
calcular_spi_batch(historico_lluvia, windows=[3,6,12])
```

### Modificado: `core/indices/environmental_indices.py`

**Línea 1:** Agregar import
```python
from core.indices.hidrology_indices import (
    calcular_infiltracion_escorrentia,
    calcular_spi_batch,
    SPICalculator
)
```

**Línea 6328 (después de sequía_suelo):**
- Agregar cálculo de infiltración/escorrentía
- Agregar cálculo de SPI con histórico

---

## 5. REQUISITOS DE DATOS

### Para Infiltración + Escorrentía:
✅ Disponibles (sensors estándar):
- Lluvia 24h: `lluvia_24h` (mm)
- Lluvia actual: `lluvia_rate` (mm/h)
- Humedad: `humedad` (%)
- Temperatura: `temperatura` (°C)

### Para SPI:
⚠️ REQUIERE histórico `data/historico_lluvia.json`:
```json
{
  "2026-02-01": 15.3,
  "2026-02-02": 0.0,
  "2026-02-03": 8.5,
  ...
}
```

**¿Sin archivo?** No se calcula SPI (debug log, sin error)

---

## 6. PARÁMETROS PERSONALIZABLES

### En `hidrology_indices.py`:

```python
SOIL_PARAMS = {
    "arenoso": {
        "Ks": 25.0,        # mm/h (cambiar si suelo específico)
        "S": 110.0,        
        "theta_s": 0.43,   
    },
    ...
}
```

### Al llamar:
```python
calcular_infiltracion_escorrentia(
    ...,
    pendiente_terreno_pct=5.0  # Personalizar para tu ubicación
)
```

---

## 7. PUBLICACIÓN AL BUS

Todos los índices se publican en el Bus global:

```
infiltracion_mm_h         → 6.45 mm/h
escorrentia_mm_h          → 2.15 mm/h
coef_escorrentia          → 0.42 (0-1)
tipo_suelo_estimado       → franco
spi_3m                    → -1.3
categoria_spi_3m          → Seco
spi_6m                    → -0.8
categoria_spi_6m          → Normal
spi_12m                   → +0.2
categoria_spi_12m         → Normal
```

Acceso desde otros módulos:
```python
from core.bus.bus_capas_informacion import obtener_bus
bus = obtener_bus()
infiltr = bus.obtener_valor("infiltracion_mm_h")
spi_tres = bus.obtener_valor("spi_3m")
```

---

## 8. VALIDACIÓN REALIZADA

✅ Sintaxis Python correcta (py_compile)
✅ Importes correctos
✅ Divisiones protegidas (if x > 0:)
✅ Valores dentro de rangos físicos (0-100%)

---

## 9. PRÓXIMAS MEJORAS (OPCIONAL)

1. **Persistencia histórico SPI**: Guardar a BD en lugar de JSON
2. **Predicción infiltración**: Usar ML con ET0 + tendencia
3. **Mapa de humedad suelo**: Interpolación espacial si múltiples ubicaciones
4. **Alerta de erosión**: Cuando escorrentía > 40% durante lluvia fuerte

---

## 10. REFERENCIAS CIENTÍFICAS

- Green-Ampt (1911): "Studies on Soil Physics"
- FAO Penman-Monteith (Allen et al., 1998)
- SPI (McKee et al., 1993): "The relationship of drought frequency and duration to time scales"
- USDA Soil Conservation Service: Modelos de infiltración

---

**Desarrollado:** MeteoSerV3 V3.8+  
**Autor:** IA MeteoSer  
**Licencia:** Soberanía de datos
