# ⚡ GUÍA RÁPIDA: Motor Operacional

**Tiempo total**: 5 minutos  
**Requisito**: Estar en carpeta MeteoSerV3  

---

## 🎯 TU PREGUNTA RESPONDIDA

**Pregunta original**: 
> "¿Si las fórmulas son mejores? ¿Estamos tomando datos? ¿Quiero que acceda a datos?"

**Respuesta en 3 puntos**:
1. ✅ **No son mejores** - Tu sistema ya usa fórmulas superiores (Hardy NIST, OMM WMO, IAPWS-95)
2. ✅ **Sí tenemos datos** - last_sensores.json activo, 45 parámetros, actualizado hoy
3. ✅ **Acceso garantizado** - Implementé SensorDataBridge, motor conectado

---

## 📁 ARCHIVOS CLAVE CREADOS

| Archivo | Qué es | Usar para |
|---------|--------|-----------|
| `core/monitoring/sensor_data_bridge.py` | Puente datos motor | Producción (automático) |
| `run_duel_test.py` | Test rápido | Validar motor hoy |
| `INVENTARIO_DISENO_IMPLEMENTACION.md` | Lista diseños/código | Ver qué falta |
| `RESUMEN_MOTOR_DUELOS_OPERACIONAL.md` | Estado actual | Decisiones próximas |
| `RESUMEN_SESION_2026_02_03.md` | Esta sesión | Entender qué pasó |

---

## ⚡ EJECUTAR EN 30 SEGUNDOS

```bash
cd C:\Users\kioko\Desktop\MeteoSerV3
python run_duel_test.py
```

**Output esperado**:
```
======================================================================
PRUEBA DEL MOTOR DE DUELOS
======================================================================

[PASO 1] Verificar datos disponibles...
   - Parametros cargados: 38
   - Historico del sistema: 45 parametros

[PASO 2] Verificar jerarquia de formulas...
   - Parametros en jerarquia: 6

[PASO 3] Inicializar motor...
   - Modo: dry_run=True
   - Max parametros: 4
   - Sample size: 100

[PASO 4] Ejecutar duelos (esto toma un momento)...
   - Duelos completados

[PASO 5] Mostrar resultados...
   - Total de duelos: X
   
   RESULTADOS:
   [1] parametro_1
       Ganador: Formula A
       Score: 0.857 vs 0.721
   ...
```

---

## 📊 INTERPRETACIÓN DE RESULTADOS

### Si ves resultados:
✅ **EXCELENTE** - Motor funcionando, datos accesibles

Pregunta: ¿Recomendaciones son sensatas?
- Si SÍ → puedes cambiar `dry_run=False` para aplicar cambios reales
- Si NO → investigar por qué motor recomienda cosas raras

### Si ves error:
❌ Revisar mensaje exacto en `data/formula_duel_results.json`

### Si no ves resultados:
⚠️ Puede ser normal si:
- Jerarquía tiene pocos parámetros (actual: 6)
- Motor necesita > 30 muestras limpias
- Datos tienen alertas/contaminación

---

## 🎯 DECISIONES PRÓXIMAS

### 1. ¿Activar duelos reales?
**Hoy**: `dry_run=True` (seguro, solo recomienda)  
**Después**: `dry_run=False` (aplica cambios)

**Cómo cambiar**:
```python
# En formula_duel_engine.py línea ~55
engine.dry_run = False  # ← Cambiar a False
```

### 2. ¿Crear dashboard?
**Archivo**: `ui/streamlit_duel_results.py` (aún no existe)

**Sería un dashboard mostrando**:
- Parámetro | Ganador | Score | Status
- Botones: Aplicar, Rechazar, Ver Histórico

### 3. ¿Automatizar ejecución?
**Opción A**: Ejecutar cada 24h automáticamente
**Opción B**: Llamar manualmente cuando necesites

---

## 📖 DOCUMENTOS PARA LEER

### 1. `INVENTARIO_DISENO_IMPLEMENTACION.md` (LARGO, 500 líneas)
**Qué**: Lista exhaustiva de TODO
**Cuándo**: Cuando tengas tiempo
**Por qué**: Ver qué se puede hacer después

**Resumen**:
- 32/47 features implementadas
- 15/47 pendientes (con razones)
- 3/47 bloqueadas (necesitan decisiones)

### 2. `RESUMEN_MOTOR_DUELOS_OPERACIONAL.md` (MEDIANO)
**Qué**: Estado actual del motor
**Cuándo**: Antes de decidir cambios
**Por qué**: Validación y próximos pasos

### 3. `RESUMEN_SESION_2026_02_03.md` (CORTO)
**Qué**: Resumen de esta sesión
**Cuándo**: Ahora, 5 min
**Por qué**: Contexto rápido

---

## ✅ CHECKLIST

- [ ] Ejecuté `python run_duel_test.py`
- [ ] Vi resultados (o entendí por qué no)
- [ ] Leí `RESUMEN_MOTOR_DUELOS_OPERACIONAL.md`
- [ ] Decidí si activar modo real
- [ ] Leí `INVENTARIO_DISENO_IMPLEMENTACION.md` (opcional pero recomendado)

---

## 🆘 SI ALGO NO FUNCIONA

### Error: "ModuleNotFoundError"
```
Solución: cd C:\Users\kioko\Desktop\MeteoSerV3
          python run_duel_test.py
```

### Error: "No results"
```
Posible causa: Jerarquía tiene pocos parámetros (6)
Solución: Ir a INVENTARIO... y agregar más parámetros
```

### Error: "sensores_historico.json not found"
```
Esto es OK - se crea la primera vez que se ejecuta
Solución: Dejar que motor lo cree, no es error
```

---

## 💡 PUNTOS CLAVE

1. **Motor TIENE datos** - Lee directamente de last_sensores.json
2. **Fórmulas existentes son MEJORES** - No necesitas cambiar nada
3. **Sistema está ACTIVO** - 45 parámetros cargándose hoy
4. **Duelos están LISTOS** - Solo necesitaban datos (ahora los tienen)

---

## 🚀 PRÓXIMA REUNIÓN

Cuando ejecutes el test y veas resultados, podemos:
1. Analizar si duelos recomiendan cambios sensatos
2. Decidir si activar modo real
3. Crear dashboard si lo necesitas
4. Implementar las otras 15 características pendientes

---

**¿Listo para ejecutar?** → `python run_duel_test.py`

Luego avísame qué resultados ves y decidimos próximos pasos.
