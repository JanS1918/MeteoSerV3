---
title: "GUÍA DE FUSIÓN ADAPTATIVA WH65 + WH31"
date: "2026-02-10"
version: "1.0"
author: "MeteoSer V3.0"
---

# 🔗 GUÍA DE FUSIÓN ADAPTATIVA: WH65 + WH31

## 📋 Resumen

El sistema ahora es capaz de combinar inteligentemente los datos de dos sensores exterior:
- **WH65**: Zona soleada, despejada, bien ventilada (referencia oficial)
- **WH31**: Zona sombría, húmeda, protegida (microclima local)

Ambos sensores participan siempre en los cálculos mediante una **media ponderada adaptativa** que se ajusta según el contexto y tipo de índice/predicción.

---

## 🎯 Contextos soportados

### 1. **'confort'** - Confort humano
- **Ponderación T**: WH65: 0.3 | WH31: 0.7
- **Ponderación H**: WH65: 0.4 | WH31: 0.6
- **Uso**: WBGT, THI, UTCI, índices de confort
- **Lógica**: Prioriza zona sombría (más representativa para confort)

### 2. **'lluvia'** - Predicción de lluvia
- **Ponderación T**: WH65: 0.7 | WH31: 0.3
- **Ponderación H**: WH65: 0.65 | WH31: 0.35
- **Uso**: Predicción de lluvia, tormentas, humedad meteorológica
- **Lógica**: Prioriza zona expuesta (más fiel a condiciones abiertas)

### 3. **'alerta'** - Alertas y validación
- **Ponderación T**: WH65: 0.5 | WH31: 0.5
- **Ponderación H**: WH65: 0.5 | WH31: 0.5
- **Uso**: Alertas cruzadas, validación de anomalías
- **Lógica**: Balance perfecto para detectar inconsistencias

### 4. **'microclima'** - Análisis de microclimas
- **Ponderación T**: WH65: 0.5 | WH31: 0.5
- **Ponderación H**: WH65: 0.5 | WH31: 0.5
- **Uso**: Detectar diferencias locales, zonas frías/cálidas
- **Lógica**: Estudia cómo varían las condiciones en tu parcela

### 5. **'rocio_niebla'** - Rocío, niebla, condensación
- **Ponderación T**: WH65: 0.4 | WH31: 0.6
- **Ponderación H**: WH65: 0.35 | WH31: 0.65
- **Uso**: Predicción de rocío, niebla, riesgo de moho
- **Lógica**: Prioriza zona húmeda (más propensa a estos fenómenos)

### 6. **'confort_expuesto'** - Confort en zona soleada
- **Ponderación T**: WH65: 0.7 | WH31: 0.3
- **Ponderación H**: WH65: 0.6 | WH31: 0.4
- **Uso**: Confort para personas en zona soleada
- **Lógica**: Prioriza zona soleada para condiciones realistas de exposición

### 7. **'prediccion_general'** - Predicción general (DEFAULT)
- **Ponderación T**: WH65: 0.6 | WH31: 0.4
- **Ponderación H**: WH65: 0.55 | WH31: 0.45
- **Uso**: Predicciones generales, si no hay contexto específico
- **Lógica**: Ligeramente ponderado hacia WH65 (sensor principal)

### 8. **'validacion'** - Validación de sensores
- **Ponderación T**: WH65: 0.5 | WH31: 0.5
- **Ponderación H**: WH65: 0.5 | WH31: 0.5
- **Uso**: Comparar sensores, detectar fallos
- **Lógica**: Simetría perfecta para validación

---

## 🚀 Cómo usar la fusión en código

### Ejemplo 1: Media simple
```python
from core.sensors.adaptive_sensor_fusion import media_adaptativa

# Obtener datos del sistema
temp_wh65 = system.sensores['temperatura']  # 25.0°C
hum_wh65 = system.sensores['humedad']       # 60%
temp_wh31 = system.sensores['temperatura_wh31']  # 22.0°C
hum_wh31 = system.sensores['humedad_wh31']       # 75%

# Calcular media para confort humano
fusion = media_adaptativa(temp_wh65, hum_wh65, temp_wh31, hum_wh31, 'confort')

# Usar valores fusionados
temp_para_confort = fusion.temperatura_media  # 22.9°C
hum_para_confort = fusion.humedad_media       # 69%

# Ver detalles
print(f"Temperatura: {fusion.temperatura_media:.1f}°C (Anomalía: {fusion.anomalia})")
print(f"Contexto: {fusion.contexto}")
print(f"Pesos: WH65={fusion.peso_wh65_temp}, WH31={fusion.peso_wh31_temp}")
```

### Ejemplo 2: Funciones de conveniencia
```python
from core.sensors.adaptive_sensor_fusion import (
    obtener_temperatura_adaptativa,
    obtener_humedad_adaptativa,
    detectar_anomalia
)

# Obtener solo temperatura adaptativa para lluvia
temp = obtener_temperatura_adaptativa(25.0, 22.0, contexto='lluvia')

# Obtener solo humedad adaptativa para rocío
hum = obtener_humedad_adaptativa(60, 75, contexto='rocio_niebla')

# Detectar anomalía
hay_anomalia, razon = detectar_anomalia(25.0, 60, 10.0, 85)  # Diferencia >10°C
if hay_anomalia:
    print(f"⚠️ ALERTA: {razon}")
```

### Ejemplo 3: Integración en índice existente
```python
def calcular_wbgt_adaptativo(system):
    """Calcular WBGT usando fusión adaptativa."""
    from core.sensors.adaptive_sensor_fusion import media_adaptativa
    
    # Obtener sensores
    temp_wh65 = system.sensores.get('temperatura', 25.0)
    hum_wh65 = system.sensores.get('humedad', 60.0)
    temp_wh31 = system.sensores.get('temperatura_wh31', 25.0)
    hum_wh31 = system.sensores.get('humedad_wh31', 60.0)
    
    # Fusionar con contexto 'confort'
    fusion = media_adaptativa(temp_wh65, hum_wh65, temp_wh31, hum_wh31, 'confort')
    
    # Usar temperatura y humedad fusionadas
    temp = fusion.temperatura_media
    hum = fusion.humedad_media
    
    # Calcular WBGT con valores fusionados
    # ... código existe de WBGT ...
    
    return {
        'wbgt': wbgt_valor,
        'temperatura_fusionada': temp,
        'humedad_fusionada': hum,
        'pesos_aplicados': {
            'temp': {'wh65': fusion.peso_wh65_temp, 'wh31': fusion.peso_wh31_temp},
            'hum': {'wh65': fusion.peso_wh65_hum, 'wh31': fusion.peso_wh31_hum},
        }
    }
```

---

## ⚠️ Detección de anomalías

La fusión detecta automáticamente si hay diferencias extremas:

- **Diferencia temperatura > 15°C**: ALERTA
- **Diferencia humedad > 40%**: ALERTA

Cuando detecta anomalía, el sistema:
1. Lanza un warning en logs
2. Usa ponderación equilibrada 50/50 en lugar de la contextual
3. Marca la decisión como anómala en DecisionFusion

**Ejemplo:**
```
[ALERTA ANOMALIA] Diferencia temperatura extrema: 18.5°C (WH65=25°C, WH31=6.5°C)
[FUSION] Por anomalía, usando ponderación 50/50
```

---

## 📊 Estructura DecisionFusion

Cada fusión retorna un objeto con esta información:

```python
@dataclass
class DecisionFusion:
    temperatura_media: float          # T fusionada (°C)
    humedad_media: float              # H fusionada (%)
    peso_wh65_temp: float             # Peso WH65 para T (0.0-1.0)
    peso_wh31_temp: float             # Peso WH31 para T (0.0-1.0)
    peso_wh65_hum: float              # Peso WH65 para H (0.0-1.0)
    peso_wh31_hum: float              # Peso WH31 para H (0.0-1.0)
    contexto: str                     # 'confort', 'lluvia', etc.
    anomalia: bool                    # ¿Hay diferencia extrema?
    razon_anomalia: Optional[str]     # Descripción de anomalía
    razon_fusion: str                 # Por qué se eligió esta ponderación
```

---

## 🔧 Personalización

### Cambiar umbral de anomalía
```python
from core.sensors.adaptive_sensor_fusion import UMBRALES_ANOMALIA

# Aumentar tolerancia a diferencias de temperatura
UMBRALES_ANOMALIA['temperatura_delta_max'] = 20.0  # en lugar de 15.0°C
```

### Añadir nuevo contexto
```python
from core.sensors.adaptive_sensor_fusion import PONDERACIONES

PONDERACIONES['mi_contexto'] = {
    'temperatura': {'wh65': 0.4, 'wh31': 0.6},
    'humedad': {'wh65': 0.3, 'wh31': 0.7},
    'razon': 'Mi descripción personalizada',
}

# Usar
from core.sensors.adaptive_sensor_fusion import media_adaptativa
fusion = media_adaptativa(25.0, 60, 22.0, 75, contexto='mi_contexto')
```

---

## 📈 Próximos pasos

1. ✅ Módulo de fusión creado
2. ⏳ Integración en índices meteorológicos (WBGT, THI, UTCI)
3. ⏳ Integración en predicción de lluvia
4. ⏳ Dashboard para visualizar diferencias WH65/WH31
5. ⏳ Alertas automáticas por microclima

---

## 📞 Soporte

- Logs: Ver `[FUSION]` en output del sistema
- Debugging: Usar `fusion.to_dict()` para convertir a diccionario
- Validación: Usar `detectar_anomalia()` para chequeos rápidos

---

**Última actualización:** 2026-02-10  
**Versión módulo:** 1.0  
**Estado:** Producción
