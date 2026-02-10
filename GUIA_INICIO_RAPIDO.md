# 🚀 GUÍA DE INICIO RÁPIDO - MeteoSerV3 Dashboard

## 📋 Pre-requisitos

- Python 3.10 o superior
- Visual Studio Code (opcional pero recomendado)
- Gateway Ecowitt con sensores WH65 + WH31
- Conexión de red local

---

## ⚙️ Instalación en 5 Pasos

### 1️⃣ Clonar/Descargar Workspace
```bash
cd c:\Users\kioko\Desktop\MeteoSerV3
```

### 2️⃣ Instalar Dependencias
```bash
pip install -r requirements.txt
```
*(Si no existe requirements.txt, instalar: `fastapi uvicorn ecuaciones datetime json`)*

### 3️⃣ Configurar Gateway Ecowitt
En la aplicación Ecowitt (Breeze):
1. Settings → Custom Server
2. Copiar la **IP local** de la máquina donde corre MeteoSerV3
3. Puerto: **8080**
4. Ruta: **/ecowitt**
5. Protocolo: **HTTP**

### 4️⃣ Iniciar el Servidor
```bash
python arrancar_meteoser.py
```

Debería ver:
```
✓ Sistema inicializado
✓ main_asgi listening on port 8080
✓ Monitor activo
```

### 5️⃣ Abrir Dashboard
Navegador: **http://localhost:8080/api/v1/fusion/dashboard**

---

## 📊 Panel Principal

El dashboard muestra **3 tarjetas** en tiempo real:

```
┌─ ☀️ EXTERIOR ─────────┐  ┌─ 🌳 WH31 ──────────┐  ┌─ 🏠 INTERIOR ──────┐
│ Temperatura: 19.2°C  │  │ Temperatura: 17.7°C│  │ Temperatura: 17.7°C│
│ Humedad: 68%         │  │ Humedad: 67%       │  │ Humedad: 68%       │
│ [Sensor WH65]        │  │ [Sensor WH31]      │  │ [HP2550A]          │
└──────────────────────┘  └────────────────────┘  └────────────────────┘

       FUSIÓN ADAPTATIVA
    Temperatura: 17.96°C
    Humedad: 68.2%
    Contexto: Confort ✅
```

---

## 🔗 API Endpoints Principales

### 1. Dashboard HTML (Visual)
```
GET http://localhost:8080/api/v1/fusion/dashboard
```
Respuesta: Página HTML con interfaz interactiva

---

### 2. Dashboard JSON (Datos)
```
GET http://localhost:8080/api/v1/fusion/dashboard-data
```

**Ejemplo de respuesta:**
```json
{
  "timestamp": "2026-02-10T19:14:09.589426",
  "wh65": {
    "temp": 18.78,
    "hum": 70.0
  },
  "wh31": {
    "temp": 17.61,
    "hum": 67.0
  },
  "interior": {
    "temp": 17.72,
    "hum": 68.0
  },
  "fusion": {
    "temp": 17.96,
    "hum": 68.2
  },
  "ponderaciones": {
    "temperatura": {"wh65": 0.3, "wh31": 0.7},
    "humedad": {"wh65": 0.4, "wh31": 0.6}
  },
  "anomalia": null,
  "alertas": [],
  "metadata": {
    "timestamp_captura": "2026-02-10T19:14:09.589439",
    "actualizacion_segundos_atras": 0
  }
}
```

---

### 3. Diagnóstico de Sensores
```
GET http://localhost:8080/diagnostico/sensores-primarios
```
Ver estado en tiempo real de:
- Última captura por sensor
- Errores detectados
- Recomendaciones

---

## 🔍 Verificar que Todo Funciona

### Opción 1: Desde el Navegador
1. Abrir http://localhost:8080/api/v1/fusion/dashboard
2. Si ve las 3 tarjetas → ✅ Funcionando

### Opción 2: Desde PowerShell
```powershell
curl "http://localhost:8080/api/v1/fusion/dashboard-data" | ConvertFrom-Json | Select-Object wh65, wh31, interior, fusion | Format-Table
```

Debería mostrar algo como:
```
wh65                       wh31                       interior                   fusion
----                       ----                       --------                   ------
@{temp=18.78; hum=70}      @{temp=17.61; hum=67}      @{temp=17.72; hum=68}      @{temp=17.96; hum=68.2}
```

---

## ⚠️ Problemas Comunes

### ❌ Dashboard muestra 0.0°C
**Causa:** Datos no están llegando del Gateway Ecowitt

**Solución:**
1. Verificar Gateway Ecowitt está conectado a Wi-Fi
2. Revisar IP de servidor en settings de Ecowitt
3. Verificar firewall permite puerto 8080
4. Ver logs: http://localhost:8080/diagnostico/sensores-primarios

### ❌ JSON devuelve valores null
**Causa:** A veces pasan 5-10 segundos antes del primer dato

**Solución:**
- Esperar 10 segundos después de iniciar servidor
- Revisar que Gateway está enviando datos (check logs)

### ❌ No puedo acceder a http://localhost:8080
**Causa:** Puerto 8080 está en uso por otro programa

**Solución:**
```powershell
# Encontrar qué usa puerto 8080
netstat -ano | findstr ":8080"

# Liberar puerto (si es python anterior)
taskkill /F /IM python.exe
```

---

## 🎨 Customización

### Cambiar ponderaciones
Archivo: `core/sensors/ml_ponderaciones_adaptativas.py`

Buscar `PONDERACIONES_CONTEXTOS` y modificar números (deben sumar 1.0 cada grupo)

### Cambiar nombres de sensores
Archivo: `routers/fusion_endpoints.py` línea ~280

Buscar `"nombre": "Temperatura al Sol"` y cambiar texto

### Cambiar formato de actualización
Archivo: `routers/fusion_endpoints.py` - Sección JavaScript `updateData()`

Modificar `setInterval(updateData, 2000)` - el 2000 es milisegundos

---

## 📈 Monitoreo Avanzado

### Ver todas las mediciones
```powershell
curl "http://localhost:8080/api/v1/fusion/dashboard-data" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Ver diagnóstico completo
```powershell
curl "http://localhost:8080/diagnostico/sensores-primarios" | ConvertFrom-Json | Format-List
```

---

## 🔐 Seguridad (Opcional)

### Agregar autenticación API
*(Tarea futura si es necesario)*

```python
# En main_asgi.py, agregar después de @app.post("/ecowitt"):
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.post("/ecowitt")
async def ecowitt_secure(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    # Validar usuario/contraseña
    ...
```

---

## 📞 Soporte

**Archivo de logs:**
- `c:\Users\kioko\Desktop\MeteoSerV3\logs\meteoser.log`

**Estado del sistema:**
- http://localhost:8080/diagnostico/sensores-primarios

**Reiniciar servidor:**
```powershell
taskkill /F /IM python.exe
python arrancar_meteoser.py
```

---

## 🎯 Próximos Pasos

1. **Configuración inicial completa** ✅
2. **Verificación en tiempo real** → http://localhost:8080/api/v1/fusion/dashboard
3. **Integración con otras aplicaciones** → Usar endpoint JSON
4. **Análisis histórico** → Próxima fase (guardar datos en DB)
5. **Alertas automáticas** → Próxima fase (correo, SMS)

---

**¿Listo para empezar?** 🚀
1. Conecta Gateway Ecowitt
2. Inicia servidor: `python arrancar_meteoser.py`
3. Abre dashboard: http://localhost:8080/api/v1/fusion/dashboard
4. ¡Disfruta datos en tiempo real! 📊

