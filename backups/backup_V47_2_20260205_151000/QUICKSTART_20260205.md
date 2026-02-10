════════════════════════════════════════════════════════════════════════════════
🚀 QUICK START - ACORAZADO DE MONTURIOL V3
════════════════════════════════════════════════════════════════════════════════

## ⚡ ARRANQUE RÁPIDO (30 segundos)

### 1. ABRIR TERMINAL EN VS CODE
```
Ctrl + ` (backtick)
```

### 2. EJECUTAR SERVIDOR
```bash
python main_asgi.py
```

### 3. ESPERAR LOGS
```
✅ Auditoría completada
🔄 Integrador Always-On: exito
   ✅ 288 eventos recuperados e integrados
✅ Sistema operativo
```

---

## ✅ VERIFICACIÓN PRE-ARRANQUE

### Opción 1: Verificación Automática
```bash
python verificar_integracion.py
```
Debería mostrar:
```
✅ Integrador importado correctamente
✅ Deardorff V46.5 FINAL importado correctamente
✅ Todas las dependencias están disponibles
```

### Opción 2: Verificación Manual
```python
# En consola Python
from core.integration.integrador_always_on import ejecutar_integrador_automatico
from core.indices.deardorff_v46_5_final_sentencia import calcular_temperatura_minima_v46_5_final
print("✅ Todo importa correctamente")
```

---

## 📊 DURANTE EL FUNCIONAMIENTO

### Ver Logs en Tiempo Real
```bash
# En terminal VS Code (el servidor ya está corriendo)
# Los logs aparecen automáticamente
```

### Ver Datos Recuperados (en otra terminal)
```bash
# Nueva terminal
ls -la data/recuperacion_gap_procesada_*.json

# Ver contenido
python -m json.tool data/recuperacion_gap_procesada_*.json | less
```

### Ver Estado del Servidor
```bash
# Nueva terminal
curl http://127.0.0.1:8080/health
```

---

## 🔧 CONFIGURACIÓN IMPORTANTE

### Variables de Entorno (Opcionales)
```bash
# Para recuperación desde Ecowitt Cloud
setx ECOWITT_API_KEY "tu_clave_aqui"
setx ECOWITT_MAC "00:11:22:33:44:55"
```

### MQTT (Configuración Predeterminada)
```
Host: 127.0.0.1
Puerto: 1883
Topics: ecowitt/#
```

---

## 🛠️ TROUBLESHOOTING

### Si el integrador NO funciona:

1. **Error: "integrador_always_on module not found"**
   ```bash
   # Verificar que el archivo existe
   ls core/integration/integrador_always_on.py
   
   # Si no existe, recrearlo desde el backup
   ```

2. **Error: "Cannot connect to MQTT"**
   ```bash
   # Normal - el sistema usa fallback a local + cloud
   # Ver logs: "⚠️ MQTT no disponible, usando fallback"
   ```

3. **Error: "No gaps detected" pero esperaba datos**
   ```bash
   # Verificar que hay archivos en data/
   ls -la data/
   
   # Si histórico está vacío, primer arranque = normal
   ```

### Ver Logs Completos:
```bash
# Los logs se guardan en logs/
ls logs/
cat logs/meteoser_latest.log | tail -100
```

---

## 📈 MONITOREO DE RECUPERACIÓN

### Dashboard de Recuperación
```bash
# Ver resumen de última recuperación
python -c "
import json
from pathlib import Path
files = list(Path('data').glob('recuperacion_gap_procesada_*.json'))
if files:
    latest = files[-1]
    with open(latest) as f:
        data = json.load(f)
    print(f'Archivo: {latest.name}')
    print(f'Eventos: {len(data)}')
    print(f'Primero: {data[0][\"timestamp\"]}')
    print(f'Último: {data[-1][\"timestamp\"]}')
else:
    print('No hay recuperaciones yet')
"
```

---

## 🎯 CONFIRMACIÓN DE ÉXITO

Cuando veas esto en los logs = **ÉXITO TOTAL:**

```
═══════════════════════════════════════════════════════════════
🚀 INICIO: MeteoSerV3 iniciando secuencia...
═══════════════════════════════════════════════════════════════

✓ Auditoría completada

🔄 INTEGRADOR ALWAYS-ON - RECUPERACIÓN AUTOMÁTICA EN ARRANQUE
═══════════════════════════════════════════════════════════════

🚨 GAP DETECTADO: 16.00 horas

✅ 288 registros recuperados
   - Locales: 240
   - MQTT: 120
   - Cloud: 288

🔄 Procesando 288 eventos...

✅ Guardado en: data/recuperacion_gap_procesada_20260205_100000.json

🔄 Integrador Always-On: exito
   ✅ 288 eventos recuperados e integrados

═══════════════════════════════════════════════════════════════

🛸 Radar Universal iniciado
📡 MQTT conectado
✅ Sistema operativo normal
```

---

## 📝 DOCUMENTACIÓN COMPLETA

Para información detallada, ver:
- `DEPLOYMENT_FINAL_20260205.md` - Documentación técnica completa
- `RESUMEN_OPERATIVO_20260205.txt` - Resumen operativo

---

## 🎯 CASO DE USO TÍPICO

### Escenario: Servidor apagado 16 horas

```
18:00 - Servidor se apaga (lluvia, corte eléctrico, etc.)
        Estación Ecowitt sigue enviando datos

10:00 - Servidor se enciende de nuevo
        
        → Integrador detecta gap automáticamente
        → Recupera 288 eventos de las 16 horas
        → Procesa como si servidor estuviera encendido
        → Guarda en histórico normal
        → Continúa operación sin interrupciones
        
✅ Sistema sin brechas de datos
```

---

════════════════════════════════════════════════════════════════════════════════

¿PREGUNTAS?

1. Ver logs: Los logs te dicen exactamente qué está pasando
2. Ver datos: `data/recuperacion_gap_procesada_*.json`
3. Ver archivo de config: `meteoser_configuracion.txt`

════════════════════════════════════════════════════════════════════════════════
