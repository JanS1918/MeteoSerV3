"""
QUICK REFERENCE - Framework Universal de Aprendizaje
═══════════════════════════════════════════════════════════════════════════════════
Para integración rápida (5 minutos por módulo)

Autor: V50.5 (Feb 10, 2026)
"""

# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 1: IMPORTAR EN MÓDULO DE ÍNDICE
# ═══════════════════════════════════════════════════════════════════════════════════

"""
En core/indices/environmental_indices.py (al principio):

from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje
from core.indices.contexto_solar import obtener_contexto_solar
from datetime import timezone  # si no está
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 2: ENVOLVER FUNCIÓN CON APRENDIZAJE
# ═══════════════════════════════════════════════════════════════════════════════════

"""
PATRÓN UNIVERSAL - 3 pasos:

def mi_indice_con_aprendizaje(..., presion=None, timestamp=None):
    '''Versión con aprendizaje automático'''
    
    # Defaults
    if timestamp is None:
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc)
    if presion is None:
        presion = 1013.25
    
    coordinador = obtener_coordinador_aprendizaje()
    
    # PASO 1: MARCAR INICIO
    pred_id = coordinador.marcar_inicio_calculo(
        tipo_indice="mi_indice",  # ← cambiar
        contexto={
            "hora": timestamp.hour,
            "mes": timestamp.month,
            "temperatura": kwargs.get("temperatura", None),
            # Agregar cualquier variable importante para el índice
        },
        metadata={"modelo": "MiModelo_v1.0"}
    )
    
    # PASO 2: EJECUTAR CÁLCULO (sin cambios)
    resultado = ... mi cálculo normal ...
    
    # PASO 3: MARCAR FIN (automáticamente aplica aprendizaje)
    resultado_final = coordinador.marcar_fin_calculo(
        prediccion_id=pred_id,
        valor_predicho=resultado,
        confianza=85  # Tu confianza típica (0-100)
    )
    
    return resultado_final

¡ESO ES TODO! Ya aprendiendo automáticamente.
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# REFERENCIAS RÁPIDAS POR ÍNDICE
# ═══════════════════════════════════════════════════════════════════════════════════

# WBGT (environmental_indices.py)
"""
Contexto importante:
├─ "hora" (hora del día, 0-23)
├─ "elevacion_solar" (qué tan alto está el sol)
├─ "estado_solar" (noche/día/twilight)
├─ "temperatura_aire"
├─ "humedad"
└─ "radiacion_ghi"

Confianza típica: 85%
Feedback: Diario (registrar temperatura globo real)
"""

# ET0 (environmental_indices.py)
"""
Contexto importante:
├─ "hora"
├─ "mes" (estación)
├─ "temperatura"
├─ "humedad"
├─ "viento"
├─ "radiacion"
└─ "tipo_suelo" (si disponible)

Confianza típica: 78%
Feedback: Semanal (balance hídrico: lluvia + riego - escorrentía)
"""

# T_MIN (deardorff_force_restore.py)
"""
Contexto importante:
├─ "mes"
├─ "temperatura_actual"
├─ "nubosidad_pct"
├─ "humedad_nocturna"
├─ "viento_nocturno"
└─ "inversion_termica"

Confianza típica: 72%
Feedback: Diario (registrar T_min real al día siguiente)
"""

# RADIACIÓN (ya integrada)
"""
Contexto importante:
├─ "hora"
├─ "elevacion_solar"
├─ "estado_solar"
├─ "mes"
└─ "modelo" (REST2, etc.)

Confianza típica: 80%
Feedback: Horaria (si hay piranómetro real)
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 3: PROCESAR FEEDBACK (crear función en mismo archivo)
# ═══════════════════════════════════════════════════════════════════════════════════

"""
def procesar_feedback_mi_indice():
    '''Ejecutar periódicamente (diario/semanal según índice)'''
    
    coordinador = obtener_coordinador_aprendizaje()
    
    try:
        # Obtener valor real observado
        valor_real = ... obtener de sensor o cálculo ...
        
        # Registrar
        coordinador.registrar_realidad(
            tipo_indice="mi_indice",
            observacion=valor_real,
            contexto={"hora": ..., "mes": ...},
            timestamp=datetime.now(timezone.utc)
        )
        
        logger.info(f"[FEEDBACK] {tipo} real: {valor_real}")
    
    except Exception as e:
        logger.warning(f"Error feedback: {e}")
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 4: ARRANCAR CICLO AUTOMÁTICO
# ═══════════════════════════════════════════════════════════════════════════════════

"""
En arrancar_meteoser.py o main.py (al inicio):

from core.learning.ciclo_aprendizaje import iniciar_ciclo_aprendizaje

# Es importante iniciar DESPUÉS que logging esté configurado
logging.basicConfig(...)

# Iniciar ciclo en background (no bloquea)
iniciar_ciclo_aprendizaje(en_background=True)

logger.info("Sistema de aprendizaje iniciado")
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# INTEGRACIÓN EN ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════════

"""
En routers/fusion_endpoints.py:

@router.get("/indice/mi_indice")
async def obtener_mi_indice(params...):
    try:
        # Llamar a versión con aprendizaje (retorna YA CORREGIDA)
        valor = calcular_mi_indice_con_aprendizaje(
            param1=...,
            param2=...,
            presion_hpa=obtener_presion_actual(),
            timestamp_actual=datetime.now(timezone.utc)
        )
        
        # Obtener estado de aprendizaje (opcional, para debug)
        coordinador = obtener_coordinador_aprendizaje()
        estado = coordinador.obtener_estado_indice("mi_indice")
        
        return {
            "valor": round(valor, 1),
            "unidad": "°C",  # Cambiar según índice
            "aprendizaje": {
                "activo": estado["aprendiendo"] if estado else False,
                "confiabilidad": estado["confiabilidad_pct"] if estado else None,
                "muestras": estado["muestras"] if estado else 0
            }
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# MONITOREO RÁPIDO
# ═══════════════════════════════════════════════════════════════════════════════════

"""
En cualquier punto (ej: shell de admin):

from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje

coordinador = obtener_coordinador_aprendizaje()

# Ver reporte completo
reporte = coordinador.obtener_reporte_aprendizaje()
print(f"Total predicciones: {reporte['total_predicciones_registradas']}")
print(f"Total observaciones: {reporte['total_observaciones_registradas']}")
print(f"Tasa matching: {reporte['tasa_matching_pct']:.1f}%")

for tipo, modelo in reporte['modelos_aprendidos'].items():
    print(f"{tipo}: error={modelo['error_medio']}%, conf={modelo['confiabilidad']}%, muestras={modelo['muestras']}")

# Ver estado de un índice específico
estado = coordinador.obtener_estado_indice("wbgt")
if estado:
    print(f"WBGT: {estado['muestras']} muestras, {estado['confiabilidad_pct']}% confiable")
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# CHECKLIST MÍNIMO
# ═══════════════════════════════════════════════════════════════════════════════════

"""
□ Paso 1: Imports añadidos al módulo
□ Paso 2: Función con aprendizaje creada (pattern universal)
□ Paso 3: procesar_feedback_* creada
□ Paso 4: Ciclo iniciado en arranque
□ Paso 5: Endpoints para obtener el índice
□ Test: python -c "from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje; print('✓')"
□ Test: Llamar endpoint y verificar que retorna valor
□ Test: Verificar logs muestran "[APRENDIZAJE]" messages
□ Dejar corriendo 1-2 días para acumular observaciones
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# TROUBLESHOOTING RÁPIDO
# ═══════════════════════════════════════════════════════════════════════════════════

"""
P: "ModuleNotFoundError: No module named 'coordinador_aprendizaje'"
R: Asegúrate que existe: core/learning/coordinador_aprendizaje.py
   Verifica: ls core/learning/

P: "No hay '[APRENDIZAJE]' en logs"
R: Verificar que ciclo_aprendizaje.iniciar_ciclo_aprendizaje() fue llamado
   Verificar logging level (no esté en ERROR)
   Revisar logs: tail -f logs/meteoser.log | grep APRENDIZAJE

P: "Confiabilidad siempre 0%"
R: Número muestras insuficiente (<50)
   Verificar que registrar_realidad() está siendo llamado
   Mirar: coordinador.obtener_reporte_aprendizaje()['total_observaciones_registradas']

P: "Error anterior 5% pero sigue igual"
R: Muestras < 100 → corrección no confiable aún
   Muestras 100-500 → corrección emergiendo
   Muestras 500+ → corrección confiable
   Esperar más días

P: "Valores ahora son PEOR que antes"
R: Muy pocas muestras (feedback early con datos malos)
   Solución: "data/ajustes_aprendizaje_universal.json" borrar y dejar que reentries
   O: Esperar 100+ observaciones REALES antes de confiar
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# ARCHIVOS AFECTADOS POR INTEGRACIÓN (RESUMEN)
# ═══════════════════════════════════════════════════════════════════════════════════

"""
CREACIONES (ya hechas):
  ✅ core/learning/framework_aprendizaje_universal.py
  ✅ core/learning/coordinador_aprendizaje.py
  ✅ core/learning/ciclo_aprendizaje.py
  ✅ GUIA_INTEGRACION_APRENDIZAJE_UNIVERSAL.md
  ✅ EJEMPLO_INTEGRACION_WBGT_ET0.py
  ✅ ARQUITECTURA_APRENDIZAJE_UNIVERSAL_V50.5.md
  ✅ ENTREGA_FRAMEWORK_APRENDIZAJE_UNIVERSAL.txt
  ✅ QUICK_REFERENCE_INTEGRACION.py (este)

MODIFICACIONES (pendientes):
  □ core/indices/environmental_indices.py
    - Añadir imports (3 líneas)
    - Crear calcular_wbgt_con_aprendizaje() (copia + 20 líneas)
    - Crear calcular_et0_con_aprendizaje() (copia + 20 líneas)
    - Opcional: crear procesar_feedback_wbgt() y procesar_feedback_et0()

  □ core/indices/deardorff_force_restore.py (después)
    - Crear calcular_temperatura_minima_con_aprendizaje() (+20 líneas)

  □ arrancar_meteoser.py O main.py (1 línea)
    - Añadir: iniciar_ciclo_aprendizaje()

  □ routers/fusion_endpoints.py (actualizar endpoints)
    - Usar calcular_*_con_aprendizaje() en lugar de versión antigua
    - Mostrar estado aprendizaje en respuesta (opcional)


ARCHIVOS QUE NO CAMBIAN:
  - core/indices/radiacion_hibrida.py (ya integrada)
  - core/sensores/* (opcionales, después)
  - core/bus_estado_global.py (usa el sistema)
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# TEMPOS TÍPICOS
# ═══════════════════════════════════════════════════════════════════════════════════

"""
INTEGRACIÓN:
  WBGT: 15 minutos (copy-paste + 3 cambios)
  ET0: 15 minutos
  T_min: 15 minutos
  Ciclo arranque: 2 minutos
  Total: 45 minutos para 3 índices + ciclo

APRENDIZAJE (antes de confiable):
  Primeras 50 muestras: 1-2 días (confianza 40-50%)
  Muestras 100: 2-4 días (confianza 60%)
  Muestras 500: 1-2 semanas (confianza 80%)
  Muestras 1000+: 1+ mes (confianza 90%+)
  Patrón estacional: 1-2 años

MEJORA OBSERVABLE:
  Después 500 obs: reducción error ~30-40%
  Después 2000 obs: reducción error ~60-70%
  Después 10000 obs: sistema comparable a modelos profesionales
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# UNA LÍNEA COMPLICADA EXPLICADA
# ═══════════════════════════════════════════════════════════════════════════════════

"""
Este es el ÚNICO patrón que necesitas:

    valor_final = coordinador.marcar_fin_calculo(pred_id, valor, confianza)

¿Qué hace?
  1. Registra predicción en histórico JSONL
  2. Busca factores aprendidos para el contexto
  3. Aplica corrección automáticamente
  4. Retorna valor MEJORADO
  5. Todo en < 1 ms (NO suma latencia)

Ejemplo:
  valor_sin_aprender = 28.5°C
  valor_con_aprender = 29.3°C (28.5 * 1.028)
  
  Usuario obtiene 29.3°C ← MEJOR PREDICCIÓN
  Sin cambios de código, AUTOMÁTICAMENTE.
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# COMANDOS DE TESTING ÚTILES
# ═══════════════════════════════════════════════════════════════════════════════════

"""
# Verificar que módulos existen y se importan
python -c "from core.learning.framework_aprendizaje_universal import obtener_framework_aprendizaje; print('✓ Framework')"
python -c "from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje; print('✓ Coordinador')"
python -c "from core.learning.ciclo_aprendizaje import iniciar_ciclo_aprendizaje; print('✓ Ciclo')"

# Registrar predicción y observación manual (test)
python << 'EOF'
from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje
import random

coordinador = obtener_coordinador_aprendizaje()

# Registrar 10 predicciones de prueba
for i in range(10):
    pred_id = coordinador.marcar_inicio_calculo("test_indice", contexto={"hora": 14})
    valor = 20.0 + random.gauss(0, 0.5)
    coordinador.marcar_fin_calculo(pred_id, valor, confianza=85)
    coordinador.registrar_realidad("test_indice", 20.0 + random.gauss(0, 0.5))

reporte = coordinador.obtener_reporte_aprendizaje()
print(f"Total predicciones: {reporte['total_predicciones_registradas']}")
print(f"Total observaciones: {reporte['total_observaciones_registradas']}")
EOF

# Ver histórico de los últimos 5 eventos
tail -5 data/historico_predicciones_universal.jsonl | python -m json.tool

# Ver modelos aprendidos actuales
python -m json.tool data/ajustes_aprendizaje_universal.json
"""


print(__doc__)
