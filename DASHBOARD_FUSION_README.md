# 📊 Dashboard de Fusión Adaptativa WH65 + WH31

## 🎯 Descripción General

Sistema de monitoreo en tiempo real que **fusiona datos de 3 sensores de temperatura y humedad** mediante un algoritmo adaptativo. Cada cambio en los datos se refleja automáticamente en el dashboard sin necesidad de recargar.

---

## 📍 Ubicación de Sensores

| Nombre | Sensor | Ubicación | Propósito |
|--------|--------|-----------|----------|
| **Exterior** | WH65 | Expuesto al sol directo | Medir temperatura máxima exterior |
| **WH31** | WH31 | Sombreado (referencia) | Medir temperatura real sin radiación solar |
| **Interior** | HP2550A | Estación interior | Medir ambiente protegido |

---

## 🔗 Endpoints Disponibles

### Dashboard Visual (HTML)
```
GET http://localhost:8080/api/v1/fusion/dashboard
```
Interfaz interactiva con actualización en tiempo real. Muestra:
- 3 tarjetas de sensores (Exterior, WH31, Interior)
- Fusión adaptativa (media ponderada)
- Gráficos de evolución
- Alertas y anomalías

### API JSON
```
GET http://localhost:8080/api/v1/fusion/dashboard-data
```

**Respuesta:**
```json
{
  "timestamp": "2026-02-10T19:14:09.589426",
  "wh65": {"temp": 18.78, "hum": 70.0},
  "wh31": {"temp": 17.61, "hum": 67.0},
  "interior": {"temp": 17.72, "hum": 68.0},
  "fusion": {
    "temp": 17.96,
    "hum": 68.2,
    "contexto": "confort"
  },
  "ponderaciones": {
    "temperatura": {"wh65": 0.3, "wh31": 0.7},
    "humedad": {"wh65": 0.4, "wh31": 0.6}
  },
  "anomalia": null,
  "alertas": [],
  "metadata": {
    "wh65": {
      "nombre": "Temperatura al Sol",
      "ubicacion": "Exterior Expuesto",
      "sensor": "WH65"
    },
    "wh31": {
      "nombre": "Temperatura en Sombra",
      "ubicacion": "Exterior Sombreado",
      "sensor": "WH31"
    },
    "interior": {
      "nombre": "Temperatura Interior",
      "ubicacion": "Estación HP2550A",
      "sensor": "HP2550A"
    },
    "timestamp_captura": "2026-02-10T19:14:09.589439",
    "actualizacion_segundos_atras": 0
  }
}
```

---

## 🔧 Arquitectura Técnica

### Flujo de Datos

```
Ecowitt Gateway
        ↓
   /ecowitt (POST)
        ↓
Fortalecimiento (multi-alias)
   - tempf, temp_f, temp, tempout, exttemp...
   - humidity, humidityout, outhumidity...
   - temp1f, temp1f, temp1c, temp_ch1...
        ↓
SystemManager.sensores (global)
   - "temperatura" → WH65 en °C
   - "humedad" → WH65 en %
   - "temperatura_wh31" → WH31 en °C
   - "humedad_wh31" → WH31 en %
   - "temperatura_interior" → Interior en °C
   - "humedad_interior" → Interior en %
        ↓
Dashboard JSON Endpoint
        ↓
Aplicaciones (Dashboard HTML, APIs, etc.)
```

### Módulos Involucrados

1. **core/integration/fortalecimiento_captura.py**
   - Captura garantizada con 69 aliases de sensores
   - Conversiones automáticas (F→C, inHg→hPa, mph→m/s)
   - Fallback a últimos valores válidos
   - Validación de rangos

2. **routers/fusion_endpoints.py**
   - Dashboard HTML interactivo
   - Endpoint JSON con metadata
   - Gráficos de evolución
   - Cálculo de ponderaciones

3. **routers/diagnostico_datos_primarios.py**
   - Monitoreo de ingestas en tiempo real
   - Recomendaciones automáticas
   - Panel visual de diagnóstico

4. **core/sensors/ml_ponderaciones_adaptativas.py**
   - Optimización de pesos dinámicamente
   - Hill climbing con Pearson correlation
   - Préximo: entrenamiento con datos históricos

---

## 📊 Ponderaciones (Fusión)

El sistema calcula una **temperatura y humedad fusionada** ponderando los sensores según su fiabilidad:

### Contexto "Confort" (por defecto)

**Temperatura:**
- WH65 (Exterior): 30% de peso
- WH31 (Sombreado): 70% de peso (referencia)

**Humedad:**
- WH65 (Exterior): 40% de peso
- WH31 (Sombreado): 60% de peso

**Fórmula:**
```
temp_fusionada = (temp_WH65 × 0.3) + (temp_WH31 × 0.7)
hum_fusionada = (hum_WH65 × 0.4) + (hum_WH31 × 0.6)
```

### Por qué WH31 tiene más peso
WH31 está en sombra (sin radiación solar) → representa mejor la temperatura real del ambiente sin sesgos de radiación.

---

## ⚠️ Anomalías y Alertas

### Anomalías Detectadas
- **Diferencia extrema de temperatura** (>15°C entre sensores)
- **Diferencia extrema de humedad** (>40% entre sensores)

### Alertas Generadas
- **Microclima detectado** (Δ T > 3°C)
  - Indica zona con mucha variación térmica

---

## 🔄 Actualización en Tiempo Real

El dashboard se **actualiza automáticamente cada 2 segundos** mediante JavaScript:

```javascript
async function updateData() {
    const response = await fetch('/api/v1/fusion/dashboard-data');
    const data = await response.json();
    // Actualizar elementos HTML con datos nuevos
}
setInterval(updateData, 2000);
```

Si el servidor no responde, los datos permanecen en pantalla pero se marca como "desactualizado".

---

## 🛠️ Mantenimiento

### Registros de Error
- Los errores secundarios (astronomía, viento) no afectan la captura de datos
- La fusión y dashboard funcionan independientemente
- Panel de diagnóstico: `http://localhost:8080/diagnostico/sensores-primarios`

### Validación de Datos
Cada dato es validado en múltiples capas:
1. **Recepción**: Rango físico (temp -50 a 130°F, hum 0-100%)
2. **Conversión**: Precisión de unidades
3. **Persistencia**: Fallback a último valor válido
4. **Fusión**: Validación de ponderaciones

---

## 📈 Próximas Mejoras

- [ ] ML adaptativo con entrenamiento continuo
- [ ] Historial de 24h con gráficos avanzados
- [ ] Alertas por correo/SMS
- [ ] Comparativa con predicciones meteorológicas
- [ ] Exportar datos a CSV/JSON

---

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| Dashboard muestra 0.0°C | Verificar `/diagnostico/sensores-primarios` |
| Datos no se actualizan | Reiniciar servidor: `taskkill /F /IM python.exe` |
| JSON vacío | Esperar 5 segundos a que llegue primer dato de Ecowitt |
| Metadata no aparece en HTML | Es normal, está en JSON pero no se muestra en interfaz |

---

## 📝 Notas Técnicas

- **Sistema operativo**: Windows
- **Python**: 3.10+
- **Framework**: FastAPI + Uvicorn
- **Base de datos**: En memoria (sensores dict)
- **Persistencia**: JSON en /data/

---

Última actualización: 2026-02-10
