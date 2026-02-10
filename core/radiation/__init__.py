"""
MÓDULO CORE.RADIATION - Arquitectura Radiativa Robusta

Componentes:
1. clasificador_contexto_radiativo: Decisión de aprendizaje
2. estrategias_aprendizaje: Correctivo + Diagnóstico separados
3. publicador_radiacion_robusto: Jerarquía de confianza
4. controlador_radiacion_robusto: Orquestador central

Uso típico:
  from core.radiation.controlador_radiacion_robusto import ControladorRadiacionRobusto
  
  controlador = ControladorRadiacionRobusto(
      clasificador=clasificador,
      aprendizaje_correctivo=aprendizaje_correctivo,
      aprendizaje_diagnostico=aprendizaje_diagnostico,
      publicador=publicador,
      validador_cruzado=validador
  )
  
  resultado = controlador.procesar_ciclo_radiacion(...)

Fecha: Feb 10, 2026
"""
