# 📁 GUÍA RÁPIDA DE ARCHIVOS - QUÉ ES QUÉ

## ⭐ ARCHIVOS PRINCIPALES (LOS QUE IMPORTAN)

### Para Arrancar MeteoSer
```
arrancar_meteoser.py       ⭐⭐⭐ - USAR ESTE para arrancar
main_asgi.py               ⭐⭐⭐ - Servidor principal (YA MODIFICADO con IA)
```

### Sistema de IA
```
ai_controller.py           ⭐⭐⭐ - Controlador de IA
ai_endpoints.py            ⭐⭐⭐ - Endpoints /ai/*

core/ai/                   ⭐⭐⭐ - 8 módulos de IA
├── orchestrator.py        - Coordinador central
├── knowledge.py           - Persistencia
├── contracts.py           - Parser de contratos
├── codegen.py             - Generación de código
├── autoheal.py            - Autocuración
├── updater.py             - Updates
├── dialog.py              - Diálogo
└── explainer.py           - Explicabilidad
```

### Contratos de Sensores
```
contracts/                 ⭐⭐ - Poner contratos JSON aquí
└── bme280_sensor.json     - Ejemplo completo
```

### Tests
```
tests/ai/                  ⭐⭐ - 27 tests del sistema de IA
```

---

## 📖 DOCUMENTACIÓN (QUÉ LEER)

### Lee PRIMERO (orden recomendado)
```
LEEME_AHORA.md             ⭐⭐⭐ - QUÉ HACER AHORA (este archivo resume TODO)
INICIO_RAPIDO.md           ⭐⭐⭐ - Cómo arrancar y usar
INTEGRACION_FINAL_LIMPIA.md ⭐⭐ - Qué se modificó
```

### Lee DESPUÉS (referencia)
```
DOCUMENTACION_COMPLETA_IA.md ⭐⭐ - Guía completa del sistema de IA
RESUMEN_IMPLEMENTACION_IA.md ⭐   - Resumen técnico
HOJA_RUTA_IA_METEOSER.md     ⭐   - Roadmap de desarrollo
```

---

## 🗑️ ARCHIVOS QUE PUEDES IGNORAR

### Documentación Antigua/Redundante
```
INSTRUCCIONES_INTEGRACION_IA.py  ⚠️ - YA INTEGRADO, solo referencia
AUDITORIA_*.md                   ℹ️ - Históricos
IMPLEMENTACION_*.md              ℹ️ - Históricos
BIBLIA_*.md                      ℹ️ - Históricos
VALIDACION_*.py                  ℹ️ - Ya ejecutado
```

### Backups
```
backups/                         ℹ️ - Backups automáticos
backup_*.py                      ℹ️ - Backups de código
```

### Archivos de Sistema
```
__pycache__/                     ℹ️ - Cache de Python
.pytest_cache/                   ℹ️ - Cache de tests
logs/                            ℹ️ - Logs del sistema
data/                            ℹ️ - Datos persistentes
```

---

## 🎯 RESUMEN ULTRA-RÁPIDO

### Para Arrancar:
```powershell
python arrancar_meteoser.py
```

### Para Configurar IA:
```powershell
$env:OPENROUTER_API_KEY = "tu_key"
```

### Para Verificar:
```powershell
Invoke-RestMethod http://localhost:8080/ai/status
```

### Para Aprender:
```
1. Lee: LEEME_AHORA.md
2. Lee: INICIO_RAPIDO.md
3. Prueba: http://localhost:8080/docs
```

---

## 📂 ESTRUCTURA SIMPLIFICADA

```
MeteoSerV3/
│
├── 🚀 ARRANQUE
│   ├── arrancar_meteoser.py ⭐ <- USA ESTE
│   └── main_asgi.py ⭐ <- YA MODIFICADO
│
├── 🤖 IA (NUEVO)
│   ├── ai_controller.py ⭐
│   ├── ai_endpoints.py ⭐
│   └── core/ai/ ⭐ (8 módulos)
│
├── 📋 CONTRATOS
│   └── contracts/ ⭐ <- PON SENSORES AQUÍ
│
├── 📖 DOCS IMPORTANTES
│   ├── LEEME_AHORA.md ⭐⭐⭐
│   ├── INICIO_RAPIDO.md ⭐⭐⭐
│   └── INTEGRACION_FINAL_LIMPIA.md ⭐⭐
│
├── 📚 DOCS REFERENCIA
│   └── DOCUMENTACION_COMPLETA_IA.md ⭐
│
├── 🧪 TESTS
│   └── tests/ai/ ⭐
│
└── ℹ️ IGNORAR
    ├── backups/
    ├── logs/
    ├── __pycache__/
    └── AUDITORIA_*.md (históricos)
```

---

## 🎯 LO MÁS IMPORTANTE

### 3 Archivos Críticos
1. **arrancar_meteoser.py** - Para iniciar
2. **main_asgi.py** - Servidor (YA modificado, NO tocar)
3. **LEEME_AHORA.md** - Qué hacer ahora

### 2 Carpetas Críticas
1. **core/ai/** - Sistema de IA (8 módulos)
2. **contracts/** - Contratos de sensores

### 1 Comando para Arrancar
```powershell
python arrancar_meteoser.py
```

---

## ✅ CHECKLIST RÁPIDO

Antes de arrancar, verifica:
- [ ] Estás en la carpeta MeteoSerV3
- [ ] Entorno virtual activado (`.venv`)
- [ ] (Opcional) API key configurada
- [ ] Puerto 8080 libre

Luego:
```powershell
python arrancar_meteoser.py
```

---

**Todo lo demás es documentación de referencia o histórico.**

**Empieza aquí: LEEME_AHORA.md** ⭐⭐⭐
