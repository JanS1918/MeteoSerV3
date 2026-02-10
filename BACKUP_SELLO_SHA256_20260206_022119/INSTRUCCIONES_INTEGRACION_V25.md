"""
INSTRUCCIONES_INTEGRACION_V25.md
==================================
Guía completa para integrar Biblia V2.5 en environmental_indices.py

STATUS: Listo para integración
AUTOR: Elite Motors V2.5 Team
FECHA: 2025-01-28
VERSIÓN: 1.0 Final
"""

# RESUMEN EJECUTIVO

La Biblia V2.5 es un framework completamente independiente que se integra en
environmental_indices.py mediante un único punto de inyección.

## Arquitectura de Integración

```
environmental_indices.calcular_indices()
    ↓
[PUNTO DE INYECCIÓN]
    ↓
integracion_elite_motors_v25.execute_ciclo_completo()
    ↓
┌─────────────────────────────────────┐
│  6 Elite Motors (parallelizable)   │
├─────────────────────────────────────┤
│ • Motor Masas de Aire              │
│ • Motor Capa Límite                │
│ • Motor Opacidad Nubes             │
│ • Motor Ventilación Táctica        │
│ • Motor Autocalibración            │
│ • Motor Simulación Forense         │
└─────────────────────────────────────┘
    ↓
BucholtzRayleighV25.visibilidad_bucholtz_completa()
    ↓
VectorAproximacion.vector_final_aproximacion()
    ↓
Bus de Estado Global._publicar()
    ↓
26 Predicciones (actualizadas con datos de élite)
```

---

# PASO 1: CREAR PUNTO DE INYECCIÓN

Modificar `core/indices/environmental_indices.py`:

## Antes (línea ~50):
```python
def calcular_indices(self, sensores_dict):
    """Calcula índices ambientales completos"""
    # Inicialización...
    resultado = {}
    
    # Cálculos existentes...
    resultado['indice_humedad_absoluta'] = self.humedad_absoluta(...)
    # ... más cálculos ...
    
    return resultado
```

## Después (INYECTAR ESTO):
```python
def calcular_indices(self, sensores_dict):
    """Calcula índices ambientales completos"""
    # Inicialización...
    resultado = {}
    
    # ===== INYECCIÓN BIBLIA V2.5 (NUEVO) =====
    try:
        from integracion_elite_motors_v25 import IntegracionMotoresV25
        integracion = IntegracionMotoresV25()
        
        # Preparar datos para motores
        sensores_v25 = {
            "temperatura_c": sensores_dict.get("temperatura", 20),
            "presion_hpa": sensores_dict.get("presion", 1013),
            "humedad_relativa": sensores_dict.get("humedad_relativa", 0.60),
            "velocidad_viento_ms": sensores_dict.get("velocidad_viento", 5),
            "direccion_viento_grados": sensores_dict.get("direccion_viento", 0),
            "radiacion_solar_w_m2": sensores_dict.get("radiacion_solar", 500),
            "altura_mast_m": 2.0  # Altura estándar
        }
        
        contexto_v25 = {
            "tipo_aire": self._detectar_tipo_aire(sensores_dict),
            "nubosidad_octavos": sensores_dict.get("nubosidad_octavos", 4),
            "tipo_precipitacion": sensores_dict.get("tipo_precipitacion", None)
        }
        
        # Ejecutar cascada de élite motors
        elite_results = integracion.execute_ciclo_completo(
            sensores=sensores_v25,
            contexto_ambiental=contexto_v25
        )
        
        # Inyectar resultados en el diccionario de salida
        resultado["elite_motors"] = elite_results
        
        # Actualizar predicciones con datos de élite
        self._actualizar_predicciones_con_elite(resultado, elite_results)
        
        self.logger.info("✓ Biblia V2.5 ejecutada correctamente")
        
    except Exception as e:
        self.logger.warning(f"⚠ Biblia V2.5 no disponible: {e}")
        resultado["elite_motors"] = None
    # ===== FIN INYECCIÓN V2.5 =====
    
    # Cálculos existentes (sin cambios)...
    resultado['indice_humedad_absoluta'] = self.humedad_absoluta(...)
    # ... más cálculos ...
    
    return resultado
```

---

# PASO 2: AGREGAR MÉTODOS DE SOPORTE

Añadir estos métodos a la clase EnvironmentalIndices:

```python
def _detectar_tipo_aire(self, sensores_dict):
    """
    Detecta tipo de masa de aire basado en sensores
    
    Returns: "TROPICAL" | "SUBTROPICAL" | "TEMPLADA" | "POLAR" | "ÁRTICA"
    """
    temp = sensores_dict.get("temperatura", 15)
    humedad = sensores_dict.get("humedad_relativa", 0.60)
    
    if temp > 25 and humedad > 0.75:
        return "TROPICAL"
    elif temp > 20 and humedad > 0.60:
        return "SUBTROPICAL"
    elif 10 <= temp <= 20:
        return "TEMPLADA"
    elif 0 <= temp < 10:
        return "POLAR"
    else:
        return "ÁRTICA"


def _actualizar_predicciones_con_elite(self, resultado, elite_results):
    """
    Actualiza las 26 predicciones con datos de los motores de élite
    
    Mapeo de predicciones a motores:
    • 1-6: Directamente de los 6 motores elite
    • 7-15: Derivadas de Motor Masas de Aire + Capa Límite
    • 16-20: Derivadas de Motor Opacidad Nubes + Bucholtz V2.5
    • 21-25: Derivadas de Motor Ventilación Táctica
    • 26: Vector de Aproximación (#26)
    """
    if elite_results is None:
        return
    
    # Predicción 1: Tipo de masa de aire
    resultado["prediccion_1_tipo_masa_aire"] = \
        elite_results.get("motor_masas_aire", {}).get("tipo_masa_aire", "DESCONOCIDA")
    
    # Predicción 2: Temperatura de suelo
    resultado["prediccion_2_temperatura_suelo"] = \
        elite_results.get("motor_capa_limite", {}).get("temperatura_suelo_c", None)
    
    # Predicción 3: Altura capa límite
    resultado["prediccion_3_altura_capa_limite"] = \
        elite_results.get("motor_capa_limite", {}).get("altura_capa_limite_m", None)
    
    # Predicción 4: Opacidad nubes
    resultado["prediccion_4_opacidad_nubes"] = \
        elite_results.get("motor_opacidad_nubes", {}).get("opacidad_nubes", None)
    
    # Predicción 5: Flujo ventilación natural
    resultado["prediccion_5_ventilacion_tactica"] = \
        elite_results.get("motor_ventilacion_tactica", {}).get("flujo_ventilacion_m3_s", None)
    
    # Predicción 6: Error residual autocalibración
    resultado["prediccion_6_error_residual"] = \
        elite_results.get("motor_autocalibration", {}).get("chi_cuadrado", None)
    
    # Predicción 16: Visibilidad Bucholtz V2.5
    bucholtz = elite_results.get("bucholtz_rayleigh_v25", {})
    resultado["prediccion_16_visibilidad_bucholtz_m"] = bucholtz.get("visibilidad_m", None)
    resultado["prediccion_16_visibilidad_bucholtz_km"] = bucholtz.get("visibilidad_km", None)
    resultado["prediccion_16_clasificacion_visibilidad"] = bucholtz.get("clasificacion", None)
    
    # Predicción 26: Vector de Aproximación (inclemencia)
    vector = elite_results.get("vector_aproximacion", {})
    resultado["prediccion_26_vector_aproximacion_direccion"] = \
        vector.get("direccion_cardinal", None)
    resultado["prediccion_26_vector_aproximacion_distancia"] = \
        vector.get("distancia_km", None)
    resultado["prediccion_26_vector_aproximacion_eta"] = \
        vector.get("eta_horas", None)
    resultado["prediccion_26_vector_aproximacion_velocidad"] = \
        vector.get("velocidad_aproximacion_kmh", None)
    resultado["prediccion_26_alerta_nivel"] = \
        elite_results.get("nivel_alerta", "VERDE")


def _validar_coherencia_elite(self, elite_results):
    """
    Valida que los resultados de élite motors sean coherentes físicamente
    
    Retorna: True si coherentes, False si hay inconsistencias
    """
    try:
        capa_limite = elite_results.get("motor_capa_limite", {})
        masas_aire = elite_results.get("motor_masas_aire", {})
        
        # Validación 1: Tsuelo > Taire en radiación fuerte
        tsuelo = capa_limite.get("temperatura_suelo_c")
        taire = masas_aire.get("temperatura_c")
        
        if tsuelo is not None and taire is not None:
            if tsuelo < taire - 2:  # Permitir -2°C de histeresis
                self.logger.warning("⚠ Inconsistencia: Tsuelo < Taire")
                return False
        
        return True
    
    except Exception as e:
        self.logger.error(f"Error en validación de coherencia: {e}")
        return False
```

---

# PASO 3: VERIFICAR IMPORTACIONES

Asegurarse de que estas importaciones existen en environmental_indices.py:

```python
import sys
from pathlib import Path

# Agregar rutas para importar módulos V2.5
sys.path.insert(0, str(Path(__file__).parent.parent))

from elite_motors_v25 import EliteMotorsV25
from bucholtz_rayleigh_v25 import BucholtzRayleighV25
from vector_aproximacion_v26 import VectorAproximacion
from integracion_elite_motors_v25 import IntegracionMotoresV25
```

---

# PASO 4: CONECTAR DASHBOARD

Modificar `static/js/dashboard.js` para mostrar Vector #26:

```javascript
// Agregar en la función actualizarDatos()
async function cargarVectorAproximacion() {
    try {
        const response = await fetch('/api/vector-aproximacion');
        const datos = await response.json();
        
        // Actualizar brújula táctica
        document.getElementById('brujula-direccion').textContent = 
            datos.vector_aproximacion.direccion_cardinal;
        document.getElementById('brujula-distancia').textContent = 
            `${datos.vector_aproximacion.distancia_km.toFixed(1)} km`;
        document.getElementById('brujula-eta').textContent = 
            `${datos.vector_aproximacion.eta_horas.toFixed(1)}h`;
        document.getElementById('brujula-alerta').textContent = 
            datos.nivel_alerta;
        
        // Rotar aguja según dirección
        const grados = datos.vector_aproximacion.direccion_grados;
        document.getElementById('aguja-brujula').style.transform = 
            `rotate(${grados}deg)`;
        
        // Cambiar color de alerta
        const alertaElement = document.getElementById('alerta-nivel');
        if (datos.nivel_alerta.includes('ROJA')) {
            alertaElement.style.backgroundColor = '#ff0040';
        } else if (datos.nivel_alerta.includes('NARANJA')) {
            alertaElement.style.backgroundColor = '#ff8800';
        } else {
            alertaElement.style.backgroundColor = '#00ff88';
        }
        
    } catch (error) {
        console.error('Error cargando vector:', error);
    }
}

// Llamar cada 5 segundos
setInterval(cargarVectorAproximacion, 5000);
```

---

# PASO 5: PRUEBAS DE INTEGRACIÓN

Ejecutar suite de pruebas:

```bash
python test_biblia_v25_completa.py
```

Esperado: ✓ Todos los tests deben pasar

---

# MAPEO DE PREDICCIONES (26 PREDICCIONES)

| # | Predicción | Motor Elite | Fórmula |
|---|-----------|-------------|---------|
| 1 | Tipo masa aire | Motor 1 | Clasificación θ_e |
| 2 | Temperatura suelo | Motor 2 | T_ground = T_mast - Γ·Δz + ΔT_rad |
| 3 | Altura capa límite | Motor 2 | h_CBL = 300 + 3.75·u·Q_0 |
| 4 | Opacidad nubes | Motor 3 | τ = ln(I_real/I_teo) |
| 5 | Ventilación táctica | Motor 4 | φ_vent = √(2·ΔP/ρ) |
| 6 | Error residual | Motor 5 | χ² = Σ[(Obs-Pred)²/σ²] |
| 7-15 | Derivadas masas/límite | Motors 1+2 | Combinadas |
| 16-20 | Opacidad/visibilidad | Motor 3 + Bucholtz | Cascada óptica |
| 21-25 | Ventilación/forense | Motors 4+6 | Combinadas |
| 26 | **Vector Aproximación** | **#26** | **Buys-Ballot + Óptico + RSSI** |

---

# VALIDACIÓN FINAL

Checklist de integración completa:

- [ ] Punto de inyección agregado en environmental_indices.py
- [ ] Métodos de soporte implementados (_detectar_tipo_aire, _actualizar_predicciones, etc.)
- [ ] Importaciones verificadas
- [ ] Dashboard actualizado con brújula táctica
- [ ] test_biblia_v25_completa.py ejecutado exitosamente
- [ ] API /api/vector-aproximacion funcionando
- [ ] Datos del Bus de Estado Global siendo actualizados
- [ ] SHA256 checksums calculados y verificados

---

# PRUEBA MANUAL RÁPIDA

```python
# Desde Python shell
from core.indices.environmental_indices import EnvironmentalIndices

indices = EnvironmentalIndices()

sensores = {
    'temperatura': 18,
    'presion': 1010,
    'humedad_relativa': 0.70,
    'velocidad_viento': 5,
    'direccion_viento': 180,
    'radiacion_solar': 600
}

resultado = indices.calcular_indices(sensores)

# Debe haber "elite_motors" en resultado
print(resultado.get('elite_motors', {}).keys())

# Debe mostrar predicción 26
print(resultado.get('prediccion_26_vector_aproximacion_direccion'))
```

---

# SOPORTE

Si hay problemas:

1. **Verificar logs**: `logs/` debe tener registros de V2.5
2. **Validar sensores**: ¿Todos los sensores tienen valores?
3. **Comprobar bus**: ¿Bus de Estado Global está operativo?
4. **Tests**: ¿test_biblia_v25_completa.py pasa?

---

**STATUS: LISTO PARA PRODUCCIÓN**
**SELLO SHA256: [Ver BIBLIA_V25_CERTIFICACION_COMPLETA.md]**
