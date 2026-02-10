# 🤖 Sistema de IA MeteoSer - Documentación Completa

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)





























































































































































































































































































































































































































































**Estado**: ✅ PRODUCCIÓN - SIN CHAPUZAS**Puerto**: 8080 ⚠️ (NO 8000)  **Fecha**: 3 de Febrero de 2026  **Versión**: 1.0.0 (Integración Completa)  ---- 📋 Panel superior: http://localhost:8080/api/panel/superior- 🤖 Estado de IA: http://localhost:8080/ai/status- 📊 Estado del sistema: http://localhost:8080/estado- 🌐 Documentación API: http://localhost:8080/docs**Accesos rápidos:**MeteoSer V3 + IA está completamente configurado e integrado.## 🎉 ¡LISTO!---- [ ] Documentación consultada- [ ] Sistema responde en `http://localhost:8080/`- [ ] Logs revisados (`logs/meteoser.log`)- [ ] API key configurada (si se usa IA)- [ ] Puerto 8080 libre- [ ] Dependencias instaladas (`pip install -r requirements.txt`)- [ ] Entorno virtual activado (`.venv`)Antes de reportar problemas, verificar:## ✅ CHECKLIST DE VERIFICACIÓN---```netstat -ano | findstr LISTENING# Ver puertos en usoGet-Process python | Stop-Process -Force# Matar todos los procesos Python (reset completo)Get-Process python# Ver procesos Python activos```powershell### Comandos Útiles```Invoke-RestMethod http://localhost:8080/ai/status# Estado detalladoInvoke-RestMethod http://localhost:8080/health# Health check```powershell### Verificación de Salud- **Startup log**: `startup_log.txt`- **Backend log**: `meteoser_backend.log`- **Main log**: `logs/meteoser.log`### Logs## 📞 SOPORTE Y AYUDA---Las funciones básicas siguen funcionando al 100%.- Respuestas a preguntas complejas en diálogo- Generación de código avanzadaEl sistema usa templates locales como fallback. Si no tienes API key, funcionará pero sin:### Reducir Uso de LLM3. **Limitar historial** en knowledge manager (ya configurado a 1000 max)2. **Ajustar health check interval** en orchestrator si es necesario   ```   $env:METEOSER_BLE_ENABLED = "0"   $env:METEOSER_MQTT_ENABLED = "0"   ```powershell1. **Deshabilitar módulos opcionales** (si no se usan):### Optimizar Arranque## ⚡ TIPS DE RENDIMIENTO---   ```   Invoke-RestMethod http://localhost:8080/ai/contracts   ```powershell4. Verificar:3. Genera driver y lo integra2. El sistema lo detecta automáticamente1. Crear contrato en `contracts/nuevo_sensor.json`### 4. Integrar Sensor Nuevo```Invoke-RestMethod http://localhost:8080/ai/history# Ver historial de fixes aplicadosInvoke-RestMethod -Uri http://localhost:8080/ai/autoheal/scan -Method Post# Disparar escaneo de problemas```powershell### 3. Autocuración de Errores```Invoke-RestMethod -Uri http://localhost:8080/ai/dialog -Method Post -Body $query -ContentType "application/json"} | ConvertTo-Json    message = "¿Y la sensación térmica?"    session_id = $resp.session_id$query = @{ # Continuar conversación con mismo session_id$resp = Invoke-RestMethod -Uri http://localhost:8080/ai/dialog -Method Post -Body $session -ContentType "application/json"$session = @{ message = "Hola, ¿cómo está el tiempo?" } | ConvertTo-Json# Crear sesión y preguntar```powershell### 2. Conversación con IA```Invoke-RestMethod http://localhost:8080/api/panel/superior# Ver panel superior (temperatura, humedad, etc.)Invoke-RestMethod http://localhost:8080/estado# Ver estado actual```powershell### 1. Monitoreo Meteorológico Básico## 🎯 CASOS DE USO COMUNES---- **HOJA_RUTA_IA_METEOSER.md**: Roadmap de desarrollo (6 fases)- **RESUMEN_IMPLEMENTACION_IA.md**: Resumen ejecutivo de implementación- **DOCUMENTACION_COMPLETA_IA.md**: Guía exhaustiva del sistema de IA## 📖 DOCUMENTACIÓN COMPLETA---```└── docs/                    # Documentación├── tests/                   # Tests unitarios├── data/                    # Persistencia de IA├── contracts/               # ⭐ Contratos de sensores (JSON)││   └── system/              # Bus, discovery, etc.│   ├── sensors/             # Sensores virtuales│   ├── indices/             # Índices meteorológicos│   ││   │   └── explainer.py     # Explicabilidad│   │   ├── dialog.py        # Diálogo conversacional│   │   ├── updater.py       # Actualizaciones│   │   ├── autoheal.py      # Autocuración│   │   ├── codegen.py       # Generación de código│   │   ├── contracts.py     # Parser de contratos│   │   ├── knowledge.py     # Gestor de conocimiento│   │   ├── orchestrator.py  # Coordinador central│   ├── ai/                   # ⭐ Módulos de IA (8 módulos)├── core/                     # Core del sistema│├── ai_endpoints.py           # Endpoints de IA├── ai_controller.py          # Controlador de IA├── arrancar_meteoser.py      # ⭐ Script de arranque recomendado├── main_asgi.py              # ⭐ Servidor principal (PUERTO 8080)MeteoSerV3/```## 📚 ESTRUCTURA DEL PROYECTO---   ```   Get-Content logs/meteoser.log -Tail 100   ```powershell3. **Ver logs de error:**   ```   pip install -r requirements.txt   ```powershell2. **Verificar dependencias:**   ```   .\.venv\Scripts\Activate.ps1   ```powershell1. **Verificar entorno virtual activo:**### Sistema No Inicia```# Reiniciar MeteoSer$env:OPENROUTER_API_KEY = "tu_key_aqui"# Si está vacía, configurar:$env:OPENROUTER_API_KEY# Verificar API key configurada```powershell### IA No Responde```python arrancar_meteoser.py# O usar el script de arranque (lo hace automáticamente)taskkill /F /PID [numero_pid]# Anotar el PID y ejecutar:netstat -ano | findstr :8080# Liberar puerto manualmente```powershell### Puerto 8080 Ocupado## 🛠️ SOLUCIÓN DE PROBLEMAS---```Invoke-RestMethod http://localhost:8080/admin/omnipotencia/dispositivos# Dispositivos detectados por Omnipotencia```powershell### Verificar Hardware Detectado```Get-Content logs/meteoser.log -Tail 50 -Wait# Logs en tiempo real```powershell### Ver Logs```Invoke-RestMethod http://localhost:8080/ai/metrics | ConvertTo-Json -Depth 10# Métricas del orchestratorInvoke-RestMethod http://localhost:8080/ai/status | ConvertTo-Json -Depth 10# Estado de IAInvoke-RestMethod http://localhost:8080/estado | ConvertTo-Json -Depth 10# Estado general```powershell### Ver Estado Completo## 🔍 MONITOREO Y DEBUG---Ver ejemplo completo en: `contracts/bme280_sensor.json`5. ✅ Integra el sensor en MeteoSer4. ✅ Ejecuta tests de validación3. ✅ Genera el driver Python automáticamente2. ✅ Valida el contrato1. ✅ Escanea `contracts/` periódicamenteEl sistema de IA:### 2. El Sistema Lo Detecta Automáticamente```}  }    "temperatura": "mi_sensor_temp"  "bus_keys": {    },    "address": "0x48"    "type": "i2c",  "protocol": {    ],    }      "range": [-40, 85]      "unit": "celsius",      "type": "float",      "name": "temperatura",    {  "fields": [    "description": "Descripción del sensor",  "version": "1.0.0",  "type": "sensor",  "name": "Mi Sensor Personalizado",  "id": "mi_sensor",{```jsonCrear archivo en `contracts/mi_sensor.json`:### 1. Crear Contrato JSON## 📋 AÑADIR NUEVOS SENSORES---```Invoke-RestMethod -Uri http://localhost:8080/ai/contracts```powershell**4. Ver Contratos de Sensores:**```    -ContentType "application/json"    -Body $body `    -Method Post `Invoke-RestMethod -Uri http://localhost:8080/ai/generate `} | ConvertTo-Json    prompt = "crear función para leer sensor I2C BME280"$body = @{```powershell**3. Generar Código:**```    -ContentType "application/json"    -Body $body `    -Method Post `Invoke-RestMethod -Uri http://localhost:8080/ai/explain `} | ConvertTo-Json    query = "qué es el UTCI"$body = @{```powershell**2. Explicar un Concepto:**```    -ContentType "application/json"    -Body $body `    -Method Post `Invoke-RestMethod -Uri http://localhost:8080/ai/dialog `} | ConvertTo-Json    message = "¿Cuál es la temperatura actual?"$body = @{# PowerShell```powershell**1. Preguntar al Sistema:**### Ejemplos Prácticos| GET | `/ai/history` | Historial de cambios || GET | `/ai/metrics` | Métricas del orchestrator || POST | `/ai/autoheal/scan` | Escaneo de autocuración || POST | `/ai/generate` | Generar código || GET | `/ai/contracts` | Listar contratos de sensores || POST | `/ai/explain` | Explicar conceptos || POST | `/ai/dialog` | Conversación con IA || GET | `/ai/status` | Estado de todos los subsistemas ||--------|----------|-------------|| Método | Endpoint | Descripción |### Endpoints Disponibles## 🤖 USAR EL SISTEMA DE IA---```curl http://localhost:8080/ai/status# Estado del sistema de IAcurl http://localhost:8080/estado# Estado del sistemahttp://localhost:8080/docs# Ver documentación interactivacurl http://localhost:8080/# Test básico```powershell### Verificar que Funciona```python -m uvicorn main_asgi:app --host 0.0.0.0 --port 8080```powershell### Método 2: Uvicorn Directo- ✅ Inicia uvicorn con configuración óptima- ✅ Configura PYTHONPATH correctamente- ✅ Libera el puerto 8080 automáticamenteEste script:```python arrancar_meteoser.py```powershell### Método 1: Script de Arranque (RECOMENDADO)## 🚀 ARRANCAR METEOSER---```pip install -r requirements.txt# Instalar/actualizar dependencias.\.venv\Scripts\Activate.ps1# Activar entorno virtual```powershell### 2. Instalar Dependencias4. Copiar y configurar la variable de entorno3. Crear API key en el dashboard2. Registrarse (gratuito)1. Ir a https://openrouter.ai/**Obtener API Key de OpenRouter:**```$env:METEOSER_MQTT_TLS = "1"$env:METEOSER_MQTT_PORT = "8883"$env:METEOSER_MQTT_HOST = "127.0.0.1"# Opcional: Configuración MQTT$env:OPENROUTER_API_KEY = "tu_api_key_aqui"# API Key para el sistema de IA (OpenRouter)```powershell### 1. Variables de Entorno Requeridas## 🔧 CONFIGURACIÓN INICIAL---- ✅ **Evolution Engine**: Auto-mejora continua- ✅ **API REST**: Endpoints completos en puerto **8080**- ✅ **Sistema de IA**: Autocuración, diálogo, generación de código- ✅ **Omnipotencia V1.5**: Radar universal USB/BLE/WiFi- ✅ **Discovery Engine**: Auto-detección de hardware (MQTT, BLE, Serial, mDNS)- ✅ **Core MeteoSer**: Sensores, índices, motores de cálculo### 🎯 Características Activas3. [Módulos Implementados](#módulos-implementados)
4. [Instalación y Configuración](#instalación-y-configuración)
5. [Integración con MeteoSer](#integración-con-meteoser)
6. [Uso Práctico](#uso-práctico)
7. [Contratos de Componentes](#contratos-de-componentes)
8. [API Endpoints](#api-endpoints)
9. [Ejemplos Avanzados](#ejemplos-avanzados)
10. [Troubleshooting](#troubleshooting)

---

## 📖 Descripción General

El Sistema de IA de MeteoSer es una arquitectura modular y autónoma que proporciona:

- **Autocuración**: Detecta y repara errores automáticamente
- **Auto-integración de sensores**: Lee contratos JSON/YAML y genera drivers
- **Generación de código**: Usa LLM externo (OpenRouter) para crear código funcional
- **Actualizaciones autónomas**: Descarga, valida y aplica updates con rollback
- **Diálogo inteligente**: Interfaz conversacional específica de MeteoSer
- **Explicabilidad total**: Explica cualquier concepto, fórmula o valor del sistema

**¿Qué NO es este sistema?**
- ❌ No es una IA generalista
- ❌ No tiene conocimientos externos al dominio meteorológico
- ✅ Es una IA especializada en gestionar y expandir MeteoSer

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    AI ORCHESTRATOR                      │
│          (Coordinador central, loop async)              │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─► Knowledge Manager (Contratos, arquitectura, historial)
       ├─► Contract Parser (JSON/YAML → drivers)
       ├─► Code Generator (LLM → código funcional)
       ├─► Auto-Heal Engine (Detección y corrección de errores)
       ├─► Updater Engine (Updates autónomos con rollback)
       ├─► Dialog Manager (NLU + LLM conversacional)
       └─► Explainer (Explicaciones en lenguaje natural)
                │
                └─► Bus (Sistema existente de MeteoSer)
```

### Principios de Diseño

1. **Modularidad**: Cada subsistema es independiente
2. **Persistencia**: Todo se guarda en JSON (data/, contracts/)
3. **Graceful Degradation**: Si el LLM falla, usa templates locales
4. **Safety First**: Backup automático antes de cambios destructivos
5. **Rollback Capability**: Cualquier update puede revertirse

---

## 🧩 Módulos Implementados

### 1. **orchestrator.py** (270 líneas)

Coordinador central asíncrono.

**Funcionalidades:**
- Loop asíncrono no bloqueante
- Cola de tareas con prioridades (1-10)
- Health checks cada 30 segundos
- Métricas de ejecución (tareas completadas/fallidas, uptime)
- Integración con Bus de MeteoSer

**Uso:**
```python
from core.ai import get_orchestrator

orch = get_orchestrator()

# Programar tarea
task_id = orch.schedule_task(
    name="Mi Tarea",
    callback=lambda: print("Ejecutando"),
    priority=5
)

# Iniciar
await orch.start()

# Métricas
metrics = orch.get_metrics()
```

---

### 2. **knowledge.py** (320 líneas)

Gestor centralizado de conocimiento.

**Funcionalidades:**
- Gestión de contratos de componentes
- Arquitectura del sistema (módulos, dependencias)
- Historial de cambios (max 1000 entradas, auto-prune)
- Reglas y políticas
- Búsqueda full-text
- Persistencia JSON
- Import/export

**Estructura de archivos:**
```
data/
├── contracts.json      # Contratos registrados
├── architecture.json   # Arquitectura del sistema
├── history.json        # Historial de cambios
└── rules.json          # Reglas y políticas
```

**Uso:**
```python
from core.ai import KnowledgeManager

km = KnowledgeManager(knowledge_dir="data")

# Registrar contrato
km.register_contract({
    "id": "bme280",
    "name": "BME280 Sensor",
    "type": "sensor",
    "version": "1.0.0"
})

# Buscar
results = km.search("temperature")

# Historial
history = km.get_history(limit=10)
```

---

### 3. **contracts.py** (200 líneas)

Parser y validador de contratos.

**Funcionalidades:**
- Carga JSON/YAML
- Validación de esquema (id, name, type, version obligatorios)
- Tipos válidos: sensor, actuator, service, component
- Generación de scaffolds (driver + test)
- Escaneo de directorios
- Extracción de metadata

**Formato de contrato:**
```json
{
  "id": "sensor_id",
  "name": "Nombre del Sensor",
  "type": "sensor",
  "version": "1.0.0",
  "fields": [...],
  "protocol": {...},
  "bus_keys": {...}
}
```

**Uso:**
```python
from core.ai import ContractParser

parser = ContractParser(contracts_dir="contracts")

# Validar
is_valid, errors = parser.validate_contract(contract)

# Generar driver
driver_code = parser.generate_driver_scaffold(contract)

# Escanear directorio
contracts = parser.scan_contracts_dir("contracts")
```

---

### 4. **codegen.py** (260 líneas)

Generador de código usando LLM externo.

**Funcionalidades:**
- Integración con OpenRouter API
- Modelo: openai/gpt-3.5-turbo (configurable)
- Validación sintáctica (AST)
- Ejecución de tests (pytest)
- Template fallback si LLM falla
- Corrección automática de errores
- Historial de generaciones

**Configuración:**
```bash
# Variable de entorno
export OPENROUTER_API_KEY="tu_api_key_aqui"
```

**Uso:**
```python
from core.ai import CodeGenerator

codegen = CodeGenerator()

# Generar código
code = codegen.generate_code(
    prompt="Crear función para leer sensor I2C",
    context={"protocol": "i2c", "address": "0x76"}
)

# Validar sintaxis
is_valid, error = codegen.validate_syntax(code)

# Ejecutar tests
passed, output = codegen.run_tests("test_file.py")
```

---

### 5. **autoheal.py** (280 líneas)

Motor de auto-curación.

**Funcionalidades:**
- Escaneo de logs (ERROR, CRITICAL, Exception)
- Detección de anomalías estadísticas (3σ)
- Catálogo de fixes predefinidos:
  - `import_error`: Instala paquetes Python faltantes
  - `permission_error`: Corrige permisos de archivos
  - `connection_timeout`: Reintentos con backoff exponencial
  - `file_not_found`: Crea archivos/directorios faltantes
  - `memory_error`: Limpia cachés
- Fixes personalizables
- Historial de reparaciones

**Uso:**
```python
from core.ai import AutoHealEngine

heal = AutoHealEngine()

# Escanear logs
issues = heal.scan_logs("logs")

# Aplicar fix
success = heal.apply_fix("import_error", error_data)

# Añadir fix personalizado
heal.add_custom_fix(
    "custom_error",
    r"error pattern",
    lambda data: print("Fix aplicado")
)
```

---

### 6. **updater.py** (270 líneas)

Motor de actualizaciones autónomas.

**Funcionalidades:**
- Descarga de updates desde URLs
- Validación SHA256
- Backup automático pre-update
- Aplicación de updates (ZIP)
- Rollback si falla
- Dry-run para testing
- Actualización de paquetes Python
- Historial de updates

**Uso:**
```python
from core.ai import UpdaterEngine

updater = UpdaterEngine()

# Descargar update
path = updater.download_update(
    "https://example.com/update.zip"
)

# Validar checksum
is_valid = updater.validate_update(path, expected_checksum)

# Aplicar (con backup automático)
success = updater.apply_update(path)

# Rollback si es necesario
updater.rollback()
```

---

### 7. **dialog.py** (350 líneas)

Gestor de diálogo conversacional.

**Funcionalidades:**
- NLU específico de MeteoSer (sensores, motores, índices)
- Clasificación de intenciones (greeting, ask_sensor, ask_status, etc.)
- Contexto de sesión persistente
- Integración con Bus para consultas en tiempo real
- Fallback a LLM externo para preguntas complejas
- Handlers extensibles

**Intenciones soportadas:**
- `greeting`: Saludos
- `ask_sensor`: Consultas sobre sensores
- `ask_status`: Estado del sistema
- `ask_motor`: Motores y cálculos
- `ask_explanation`: Solicitudes de explicación
- `ask_history`: Historial de eventos
- `ask_contract`: Información de contratos
- `system_command`: Comandos de control
- `fallback`: LLM externo para todo lo demás

**Uso:**
```python
from core.ai import DialogManager

dialog = DialogManager(bus=bus)

# Crear sesión
session_id = dialog.create_session()

# Procesar mensaje
response = dialog.process_message(
    session_id,
    "¿Cuál es la temperatura actual?"
)

# Respuesta incluye: text, intent, confidence
```

---

### 8. **explainer.py** (330 líneas)

Sistema de explicabilidad.

**Funcionalidades:**
- Explicaciones predefinidas (temperatura, UTCI, dewpoint, etc.)
- Búsqueda en knowledge manager
- Consulta de valores del Bus con contexto
- Explicación de fórmulas paso a paso
- Explicación de motores
- Fallback a LLM externo

**Uso:**
```python
from core.ai import Explainer

explainer = Explainer()

# Explicar concepto
explanation = explainer.explain("qué es el UTCI", bus=bus)

# Explicar fórmula
formula_exp = explainer.explain_formula(
    "dewpoint",
    {"T": 25.0, "RH": 60.0}
)

# Explicar motor
motor_exp = explainer.explain_motor("motor_utci", bus=bus)
```

---

## ⚙️ Instalación y Configuración

### Requisitos

```bash
# Python 3.8+
python --version

# Paquetes necesarios
pip install requests pyyaml pytest
```

### Configuración de API Key

El sistema usa OpenRouter para generación de código y diálogo avanzado.

```bash
# Crear variable de entorno (Windows)
set OPENROUTER_API_KEY=tu_api_key_aqui

# Linux/Mac
export OPENROUTER_API_KEY=tu_api_key_aqui

# Persistente en Windows
setx OPENROUTER_API_KEY "tu_api_key_aqui"
```

**Obtener API key:**
1. Ir a https://openrouter.ai/
2. Registrarse (gratis)
3. Crear API key
4. Copiar y configurar

---

## 🔗 Integración con MeteoSer

### Paso 1: Añadir imports en main_asgi.py

```python
from ai_controller import initialize_ai_controller, get_ai_controller
from ai_endpoints import router as ai_router
```

### Paso 2: Inicializar en startup

```python
@app.on_event("startup")
async def startup_event():
    global ai_controller
    
    # Obtener Bus (ajustar según tu implementación)
    bus = get_bus_instance()
    
    # Inicializar AI
    ai_controller = initialize_ai_controller(
        bus=bus,
        config_dir="data",
        contracts_dir="contracts"
    )
    
    await ai_controller.initialize()
    
    logger.info("🤖 Sistema de IA inicializado")
```

### Paso 3: Registrar endpoints

```python
# Registrar router de IA
app.include_router(ai_router)
```

### Paso 4: Apagar en shutdown

```python
@app.on_event("shutdown")
async def shutdown_event():
    ai_controller = get_ai_controller()
    
    if ai_controller:
        await ai_controller.shutdown()
```

Ver archivo `INSTRUCCIONES_INTEGRACION_IA.py` para ejemplo completo.

---

## 📚 Uso Práctico

### Ejemplo 1: Auto-integrar sensor desde contrato

```python
# 1. Crear contrato JSON en contracts/mi_sensor.json
{
  "id": "mi_sensor",
  "name": "Mi Sensor Custom",
  "type": "sensor",
  "version": "1.0.0",
  "fields": [{"name": "value", "type": "float", "unit": "celsius"}],
  "protocol": {"type": "i2c", "address": "0x48"}
}

# 2. Sistema de IA lo detecta automáticamente
# 3. Genera driver y test
# 4. Valida sintaxis
# 5. Ejecuta tests
# 6. Si OK, integra en MeteoSer
```

### Ejemplo 2: Conversación con IA

```bash
# Usuario: "¿Cuál es la temperatura actual?"
# IA busca en Bus → responde con valores

# Usuario: "Explica qué es el UTCI"
# IA consulta catálogo → respuesta detallada

# Usuario: "¿Cómo funciona el motor de radiación?"
# IA busca en arquitectura + LLM → explicación técnica
```

### Ejemplo 3: Auto-curación de error

```
1. Sistema detecta: ImportError: No module named 'requests'
2. AutoHeal identifica error tipo 'import_error'
3. Aplica fix: pip install requests
4. Reinicia componente afectado
5. Registra en historial
```

---

## 📄 Contratos de Componentes

Los contratos son archivos JSON/YAML que describen completamente un componente.

### Esquema de Contrato

```json
{
  "id": "string (requerido)",
  "name": "string (requerido)",
  "type": "sensor|actuator|service|component (requerido)",
  "version": "string (requerido)",
  "description": "string (opcional)",
  
  "fields": [
    {
      "name": "string",
      "type": "float|int|string|bool",
      "unit": "string",
      "range": [min, max],
      "precision": float
    }
  ],
  
  "protocol": {
    "type": "i2c|spi|uart|http|mqtt",
    "address": "string",
    "registers": {}
  },
  
  "bus_keys": {
    "field_name": "bus_key_name"
  },
  
  "dependencies": {
    "python_packages": [],
    "system_packages": []
  }
}
```

### Ejemplo Real: BME280

Ver `contracts/bme280_sensor.json` para ejemplo completo.

---

## 🌐 API Endpoints

Una vez integrado, estos endpoints están disponibles:

### GET /ai/status
Estado de todos los subsistemas.

```bash
curl http://localhost:8080/ai/status
```

Respuesta:
```json
{
  "initialized": true,
  "subsystems": {
    "orchestrator": {"running": true, "tasks_pending": 0},
    "knowledge": {"contracts": 5},
    "dialog": {"sessions_active": 2}
  }
}
```

### POST /ai/dialog
Diálogo conversacional.

```bash
curl -X POST http://localhost:8080/ai/dialog \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Cuál es la temperatura?"}'
```

### POST /ai/explain
Explicar conceptos.

```bash
curl -X POST http://localhost:8080/ai/explain \
  -H "Content-Type: application/json" \
  -d '{"query": "qué es el UTCI"}'
```

### GET /ai/contracts
Listar todos los contratos.

```bash
curl http://localhost:8080/ai/contracts
```

### POST /ai/generate
Generar código.

```bash
curl -X POST http://localhost:8080/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "función para leer I2C"}'
```

Ver `ai_endpoints.py` para todos los endpoints disponibles.

---

## 🔧 Ejemplos Avanzados

### Añadir handler de diálogo personalizado

```python
def mi_handler(context, nlu, text):
    return "Respuesta personalizada"

dialog.register_intent_handler("mi_intencion", mi_handler)
```

### Añadir fix de auto-curación personalizado

```python
def mi_fix(error_data):
    # Lógica de reparación
    return True

autoheal.add_custom_fix(
    "mi_error",
    r"patron regex del error",
    mi_fix
)
```

### Añadir explicación personalizada

```python
explainer.add_explanation(
    "mi_concepto",
    "Explicación detallada de mi concepto"
)
```

---

## 🐛 Troubleshooting

### Problema: LLM no responde

**Causa**: API key no configurada o inválida.

**Solución**:
```bash
# Verificar variable de entorno
echo %OPENROUTER_API_KEY%  # Windows
echo $OPENROUTER_API_KEY   # Linux/Mac

# Si está vacía, configurar
set OPENROUTER_API_KEY=tu_key_aqui
```

### Problema: Orchestrator no inicia

**Causa**: Loop asyncio ya ejecutándose.

**Solución**:
```python
# Usar create_task en lugar de await directamente
asyncio.create_task(orchestrator.start())
```

### Problema: Contratos no se detectan

**Causa**: Directorio incorrecto o permisos.

**Solución**:
```bash
# Verificar que exista
ls contracts/

# Verificar permisos (Linux)
chmod -R 755 contracts/
```

### Problema: Auto-heal no detecta errores

**Causa**: Logs vacíos o formato no reconocido.

**Solución**:
```python
# Verificar logs
heal.scan_logs("logs")

# Añadir patrón personalizado si necesario
```

---

## 📊 Métricas y Monitoreo

### Ver estado completo

```python
ai_controller = get_ai_controller()
status = ai_controller.get_status()
```

### Métricas del orchestrator

```python
metrics = orchestrator.get_metrics()
# tasks_completed, tasks_failed, uptime
```

### Historial de cambios

```python
history = knowledge.get_history(limit=100)
```

---

## 🚀 Próximos Pasos

1. **Crear más contratos**: Añade todos tus sensores en `contracts/`
2. **Personalizar handlers**: Añade lógica específica de tu dominio
3. **Monitorear**: Usa `/ai/metrics` para ver rendimiento
4. **Iterar**: El sistema aprende y mejora con uso

---

## 📞 Soporte

Para cualquier duda:
1. Ver logs en `logs/`
2. Consultar historial: `GET /ai/history`
3. Ver estado: `GET /ai/status`

---

**Versión**: 1.0.0  
**Fecha**: Febrero 2025  
**Sistema**: MeteoSer IA  
**Estado**: Producción ✅
