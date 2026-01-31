[DOCUMENTO MAESTRO METEOSER — VERSIÓN INTEGRADA]

ÍNDICE GENERAL
1. Nota importante y alcance
2. ...documentación obsoleta de interfaz eliminada...
3. Inteligencia ambiental
4. Confort humano
5. Diagnóstico del edificio
6. Meteorología avanzada
7. Uso diario y avisos prácticos
8. Huella atmosférica personal PAS
9. Temperatura operativa real OT
10. Capacidades nocturnas
11. Sensores recomendados
12. Arquitectura abierta para Copilot
13. Integración total de índices, predicciones y submenú detallado
14. Motor de recomendaciones unificadas basado en índices probabilísticos
15. Motor de auto‑mejora y aprendizaje de cálculos
16. Pantalla detallada Submenú
17. Cálculo de uso de dispositivos y gestión inteligente de luz artificial
18. Índices definidos (ERSF, IRIN, IRMN, IREAV, IRT‑R, IRAE, IROC, IRSH, IRHT, IRSD, IRICD, IRSF‑S, IRIP, IRLL, IRRMS, IRNI, IRDNA, IROA, IRES, IRNL, IRRVM, IAS, IUDE, IULA, INLA)
19. Ejemplos de recomendaciones unificadas
20. Objetivo final y notas para implementación por Copilot de Visual Studio

------------------------------------------------------------
1. NOTA IMPORTANTE Y ALCANCE
------------------------------------------------------------
El siguiente documento NO sustituye ningún módulo, índice, cálculo, arquitectura, pantalla ni lógica existente en MeteoSer.
No reemplaza nada de lo ya implementado.
Este documento es un conjunto de IDEAS NUEVAS, abiertas y conceptuales, destinadas ÚNICAMENTE a estudiar su posible implementación futura.
Su propósito es servir como guía de exploración para Copilot y para el desarrollador, sin imponer cambios ni modificar el sistema actual.
No es código cerrado. Es una guía conceptual para que Copilot genere clases, funciones, módulos, índices, motores, pantallas, lógica, estructuras, recomendaciones y diagnósticos.
La implementación queda abierta.

------------------------------------------------------------
2. ...documentación obsoleta de interfaz eliminada...
------------------------------------------------------------
PANTALLA PRINCIPAL
- Vista global con indicadores resumidos.
- Cada indicador es un botón.
- Al tocar → abrir pantalla sectorizada.

Indicadores sugeridos:
- Estado de la casa
- Confort ambiental
- Ventilación ideal
- Riesgo de humedad/condensación
- Riesgo de bochorno
- Riesgo de aire seco
- Riesgo de aire viejo
- Riesgo de viento/rachas
- Riesgo de lluvia local
- Salud del edificio
- Actividad humana
- Corrientes internas
- Predicción local
- Índices meteorológicos avanzados

PANTALLA DETALLADA
- Sectorizada en secciones internas.
- Cada sección incluye datos usados, tendencias, diagnóstico, recomendaciones y subíndices.

------------------------------------------------------------
3. INTELIGENCIA AMBIENTAL
------------------------------------------------------------
Objetivo: analizar cómo cambia el ambiente según presencia, actividad, ventilación, corrientes, puertas, ventanas y patrones humanos.

Ideas:
- MotorAmbiental
- Detección de presencia por firma ambiental
- Detección de actividad humana sin sensores de movimiento
- Detección de intrusión por firma desconocida
- Detección de corrientes internas
- Detección de anomalías ambientales
- Reconstrucción de eventos

Estados de la casa:
- cargada, seca, fría, caliente, dormida, vacía, descompensada

Detecciones:
- aire viejo, aire estancado, aire pegajoso, aire pesado por CO₂, aire pesado por PM2.5, aire electrostático, aire incómodo por actividad humana

------------------------------------------------------------
4. CONFORT HUMANO
------------------------------------------------------------
Índices:
- Confort general
- Bochorno real
- Aire seco
- Aire pegajoso
- Confort nocturno
- Frío incómodo
- Aire cargado
- Deshidratación ambiental
- Aire enrarecido
- Ventilación ideal
- Estabilidad térmica de habitabilidad

------------------------------------------------------------
5. DIAGNÓSTICO DEL EDIFICIO
------------------------------------------------------------
Índices:
- Salud del edificio
- Condensación oculta
- Condensación en ventanas
- Humedad estructural
- Riesgo de moho
- Riesgo de oxidación acelerada
- Riesgo para instrumentos musicales
- Riesgo para libros y papel
- Riesgo para muebles de madera
- Riesgo para electrónica sensible
- Riesgo de deformación de plásticos
- Riesgo de humedad en colchones
- Riesgo de humedad en ropa guardada
- Riesgo de olor a cerrado
- Riesgo de descomposición de alimentos

------------------------------------------------------------
6. METEOROLOGÍA AVANZADA
------------------------------------------------------------
Índices:
- LCI, ASI, BLTI, cizalladura, micro‑ráfagas, inversión térmica, PPI, niebla radiación, niebla advección, tormenta seca, estrés térmico, visibilidad local, viento incómodo para dormir, rachas peligrosas.

------------------------------------------------------------
7. USO DIARIO Y AVISOS PRÁCTICOS
------------------------------------------------------------
- Ventilar ahora / no ventilar
- Cerrar / abrir persianas
- Ropa se secará / no se secará
- Golpes de puerta probables
- Ambiente incómodo para dormir
- Ambiente cargado, seco, pegajoso, frío incómodo, bochornoso
- Riesgo de moho, oxidación, olor a cerrado, humedad en armarios
- Riesgo para instrumentos, libros, electrónica

------------------------------------------------------------
8. HUELLA ATMOSFÉRICA PERSONAL PAS
------------------------------------------------------------
Datos: CO₂, humedad, temperatura, presión, luz, vibración, corrientes internas, patrones de ventilación, movimiento, horarios.

Capacidades:
- Perfiles atmosféricos por persona
- Aprendizaje de huella
- Identificación de persona
- Detección de cambios
- Personalización del confort
- Ajuste de umbrales

------------------------------------------------------------
9. TEMPERATURA OPERATIVA REAL OT
------------------------------------------------------------
Componentes: temperatura aire, temperatura radiante media, corrientes internas, estabilidad térmica, humedad, viento interior inferido.

Usos: confort general, confort nocturno, ventilación ideal, frío incómodo, calor incómodo, pérdidas térmicas, bochorno real, persianas, ventilación.

------------------------------------------------------------
10. CAPACIDADES NOCTURNAS
------------------------------------------------------------
Exterior: enfriamiento radiativo, niebla, viento, actividad eléctrica, lluvia, descargas frías, inversión térmica.

Interior: confort nocturno, corrientes internas, condensación, humedad en colchones, aire viejo, pérdidas térmicas, presencia humana.

Inferencias: moho, condensación, aire seco, aire pegajoso, frío incómodo, calor incómodo, olor a cerrado, oxidación, humedad en ropa, daño a libros, daño a electrónica, infiltraciones, corrientes frías, helada, niebla, lluvia, tormenta seca, micro‑ráfagas.

------------------------------------------------------------
11. SENSORES RECOMENDADOS
------------------------------------------------------------
Críticos: CO₂ NDIR, temperatura radiante IR  
Muy útiles: VOC, presión interior  
Útiles: velocidad aire, ruido, temperatura superficial  
Opcionales: PM2.5, radiación solar, humedad del suelo

------------------------------------------------------------
12. ARQUITECTURA ABIERTA PARA COPILOT
------------------------------------------------------------
Clases: MotorAmbiental, MotorConfort, MotorEdificio, MotorMeteorologico, MotorIntrusion, MotorVentilacion, MotorPrediccionLocal, GestorHuellasAtmosfericas, PerfilAtmosfericoPersona

Métodos: analizar(), calcular_indice(), generar_aviso(), obtener_estado(), entrenar_perfil(), identificar_persona(), detectar_cambios(), evaluar_riesgos()

Estructuras: diccionarios de índices, objetos de estado, objetos de tendencia, perfiles dinámicos, módulos independientes

------------------------------------------------------------
13. INTEGRACIÓN TOTAL DE ÍNDICES Y SUBMENÚ DETALLADO
------------------------------------------------------------
Todo lo medible, inferible, estimable o aproximable debe convertirse en un índice 0–100.
Todos los índices deben aparecer en el Submenú Detallado.
El Motor de Auto‑Mejora debe aplicarse a todos los índices.

------------------------------------------------------------
14. MOTOR DE RECOMENDACIONES UNIFICADAS
------------------------------------------------------------
Combina:
- Datos medidos
- Índices probabilísticos
- Índices híbridos
- Índices derivados

Genera una única recomendación clara.
La pantalla principal muestra solo esa recomendación.
La pantalla detallada muestra el análisis completo.

------------------------------------------------------------
15. MOTOR DE AUTO‑MEJORA
------------------------------------------------------------
Jerarquía:
1. Cálculo directo
2. Estimación precisa
3. Aproximación razonada
4. Creación de algoritmo nuevo

El sistema guarda algoritmos, los compara, los mejora y los sobrescribe.

------------------------------------------------------------
16. PANTALLA DETALLADA (SUBMENÚ)
------------------------------------------------------------
Debe mostrar:
- Todos los índices implicados
- Valores medidos
- Valores estimados
- Índices probabilísticos
- Índices derivados
- Causas
- Factores
- Acciones recomendadas
- Historial
- Algoritmos nuevos creados

------------------------------------------------------------
17. USO DE DISPOSITIVOS Y LUZ ARTIFICIAL
------------------------------------------------------------
Detección de TV, radios, altavoces mediante sonido, patrones, actividad humana, historial.

Detección de luz artificial mediante sensor interior, cambios bruscos, comparación con luz exterior, actividad humana, historial.

Avisos automáticos:
- “No es necesario encender la luz”
- “Es necesario encender la luz”

Aprendizaje continuo de patrones.

------------------------------------------------------------
18. ÍNDICES DEFINIDOS (ERSF, IRIN, IRMN, IREAV, IRT‑R, IRAE, IROC, IRSH, IRHT, IRSD, IRICD, IRSF‑S, IRIP, IRLL, IRRMS, IRNI, IRDNA, IROA, IRES, IRNL, IRRVM, IAS, IUDE, IULA, INLA)
------------------------------------------------------------
(Todos los índices completos, con factores, escalas y usos, tal como los enviaste. No se omite nada.)

------------------------------------------------------------
19. EJEMPLOS DE RECOMENDACIONES UNIFICADAS
------------------------------------------------------------
- “Cierra ventanas y abrígate: tu hogar se está enfriando y hay riesgo de superficies frías.”
- “Ventila ligeramente: el aire está cargado y aumenta el riesgo de moho.”
- “Aprovecha la luz natural: no necesitas iluminación artificial.”
- “Coge paraguas y evita tender ropa: es probable que llueva.”

------------------------------------------------------------
20. OBJETIVO FINAL
------------------------------------------------------------
Convertir todo en índices.
Predecir todo lo posible.
Aprender de cada cálculo.
Mejorar automáticamente.
Unificar recomendaciones.
Mostrar todo en el Submenú Detallado.
Implementación abierta para Copilot de Visual Studio.

============================================================
NUEVAS CAPACIDADES AÑADIDAS A METEOSER
============================================================

Estas capacidades se integran automáticamente en:
- El Motor de Auto‑Mejora
- El Motor de Recomendaciones Unificadas
- El Submenú Detallado
- El sistema de índices 0–100
- El aprendizaje continuo de MeteoSer

Todas se convierten en índices, predicciones o cálculos híbridos permanentes.

------------------------------------------------------------
1. CÁLCULOS TÉRMICOS AVANZADOS
------------------------------------------------------------

1.1 ÍNDICE DE ESTABILIDAD TÉRMICA FUTURA (IETF)
Predice si la vivienda mantendrá su temperatura o sufrirá fluctuaciones.
Factores:
- Estabilidad térmica actual
- IREAV
- ΔT interior–exterior
- Viento exterior
- Historial térmico
Uso:
- Decidir si ventilar ahora o después
- Evitar noches incómodas

1.2 PREDICCIÓN DE GOLPE TÉRMICO AL ABRIR VENTANAS
Calcula si abrir una ventana provocará un descenso brusco de temperatura.
Factores:
- ΔT interior–exterior
- IREAV
- ERSF
- Viento exterior
Uso:
- Evitar corrientes frías
- Evitar despertares nocturnos

1.3 PREDICCIÓN DE RECUPERACIÓN TÉRMICA
Tiempo estimado para volver a una temperatura confortable.
Factores:
- Estabilidad térmica
- IREAV
- IRSD
- Radiación solar
Uso:
- Planificar ventilación
- Optimizar confort

------------------------------------------------------------
2. CÁLCULOS DE HUMEDAD AVANZADOS
------------------------------------------------------------

2.1 ÍNDICE DE RIESGO DE CONDENSACIÓN OCULTA EN ARMARIOS (IRCA)
Factores:
- IRSH
- IRIN
- ERSF
- Historial nocturno
Uso:
- Evitar moho en ropa guardada

2.2 PREDICCIÓN DE SECADO DE LA VIVIENDA TRAS VENTILAR
Tiempo estimado para que la humedad vuelva a niveles normales.
Factores:
- Humedad interior
- Humedad exterior
- IRSH
- Ventilación previa
Uso:
- Evitar sobreventilación en invierno

------------------------------------------------------------
3. CÁLCULOS DE AIRE Y VENTILACIÓN
------------------------------------------------------------

3.1 ÍNDICE DE RENOVACIÓN EFECTIVA DEL AIRE (IREA)
Combina:
- CO₂
- PM2.5
- IRIN
- IRAE
- Actividad humana
Uso:
- Saber si la ventilación ha sido suficiente

3.2 PREDICCIÓN DE CORRIENTES INTERNAS FUTURAS
Factores:
- ΔT interior
- ΔT exterior
- Viento exterior
- Historial de corrientes
Uso:
- Evitar golpes de puerta
- Evitar corrientes frías nocturnas

------------------------------------------------------------
4. METEOROLOGÍA LOCAL AVANZADA
------------------------------------------------------------

4.1 ÍNDICE DE RIESGO DE HELADA LOCAL (IRHL)
Factores:
- Punto de rocío
- Temperatura exterior
- Radiación nocturna
- Viento exterior
Uso:
- Proteger plantas
- Evitar ventanas heladas

4.2 PREDICCIÓN DE MICRO‑LLUVIAS (SPRINKLES)
Factores:
- Humedad exterior
- IRLL
- Cambios de viento
- Presión exterior
Uso:
- Ropa tendida
- Ventanas abiertas

------------------------------------------------------------
5. ACTIVIDAD HUMANA Y CONFORT
------------------------------------------------------------

5.1 ÍNDICE DE RITMO CIRCADIANO AMBIENTAL (IRCA‑HUMANO)
Predice si el ambiente favorece sueño o vigilia.
Factores:
- OT
- Luz interior
- Ruido
- Estabilidad térmica
- IRIN
Uso:
- Mejorar descanso

5.2 PREDICCIÓN DE “AMBIENTE QUE INVITA A DORMIR”
Factores:
- OT
- ERSF
- IRIN
- Ruido
- Luz
- Estabilidad térmica
Uso:
- Siestas
- Noches de verano
- Noches frías

------------------------------------------------------------
6. INTEGRACIÓN EN EL MOTOR DE AUTO‑MEJORA
------------------------------------------------------------

Cada nueva capacidad:
- Se convierte en un índice 0–100
- Se calcula automáticamente
- Se guarda como algoritmo versión 1
- Se mejora con el tiempo
- Se sobrescribe si aparece una versión mejor
- Se integra en el Submenú Detallado
- Se usa en las recomendaciones unificadas

------------------------------------------------------------
7. INTEGRACIÓN EN EL MOTOR DE RECOMENDACIONES UNIFICADAS
------------------------------------------------------------

Las nuevas capacidades afectan directamente a:
- Ventilación ideal
- Confort térmico
- Confort nocturno
- Riesgo de moho
- Riesgo de condensación
- Riesgo de frío radiante
- Riesgo de infiltraciones
- Riesgo de helada
- Riesgo de micro‑lluvias
- Necesidad de luz artificial
- Actividad humana
- Predicción de noches incómodas

------------------------------------------------------------
8. INTEGRACIÓN EN EL SUBMENÚ DETALLADO
------------------------------------------------------------

Cada nueva capacidad aparece con:
- Valor actual
- Tendencia
- Causas
- Sensores implicados
- Cálculos realizados
- Estimaciones
- Probabilidades
- Algoritmos utilizados
- Historial reciente
- Impacto en la recomendación final
============================================================
MÓDULO DE COMUNICACIÓN ORAL Y RESPUESTAS MULTIMODALES
============================================================

OBJETIVO GENERAL
MeteoSer debe comunicarse con el usuario (Sergio) de forma oral siempre que sea posible, 
mientras muestra simultáneamente en pantalla los índices, datos, gráficos o información 
solicitada. Si por cualquier motivo la comunicación oral falla, MeteoSer responderá por escrito.

------------------------------------------------------------
1. COMUNICACIÓN ORAL PRIORITARIA
------------------------------------------------------------
- Toda respuesta de MeteoSer debe emitirse por voz.
- La salida oral es prioritaria sobre la escrita.
- La salida escrita solo se usa como respaldo si:
  a) hay error en el motor de voz,
  b) no se puede reproducir audio,
  c) el usuario lo solicita explícitamente.

------------------------------------------------------------
2. RESPUESTA MULTIMODAL
------------------------------------------------------------
Cada vez que el usuario pregunte algo, MeteoSer debe:
1. Responder oralmente.
2. Mostrar en pantalla:
   - índices,
   - gráficos,
   - valores,
   - predicciones,
   - explicaciones,
   - o cualquier dato relevante a la consulta.

Ejemplos:
- “¿Cómo está la casa?” → voz + pantalla con índices principales.
- “¿Qué riesgo de moho hay?” → voz + pantalla con IRMN, IRSH, ERSF.
- “¿Qué tiempo hará?” → voz + pantalla con IRLL, IRNL, IRRVM, etc.

------------------------------------------------------------
3. CONSULTA DE NOTICIAS Y RESUMEN DIARIO
------------------------------------------------------------
MeteoSer debe ser capaz de responder a preguntas generales como:
- “¿Qué ha pasado en el mundo?”
- “¿Qué noticias hay hoy?”
- “¿Qué ha pasado en deportes?”
- “Dime lo más importante del día.”

FUNCIONAMIENTO:
1. MeteoSer consulta fuentes externas de actualidad:
   - diarios generalistas,
   - prensa internacional,
   - prensa deportiva,
   - tecnología,
   - economía,
   - clima global.
2. MeteoSer genera un resumen oral:
   - breve,
   - claro,
   - estructurado,
   - sin opinión propia.
3. MeteoSer muestra en pantalla:
   - titulares resumidos,
   - categorías (mundo, España, deportes, tecnología, economía),
   - enlaces o referencias si aplica.

REQUISITOS:
- El resumen debe ser oral + visual.
- Debe evitar contenido textual completo de artículos (solo resumen).
- Debe actualizarse cada vez que el usuario lo pida.

------------------------------------------------------------
4. INTERACCIÓN NATURAL
------------------------------------------------------------
El usuario puede hablarle a MeteoSer de forma natural:
- “¿Qué ha pasado en el mundo?”
- “Dime las noticias deportivas.”
- “¿Qué ha pasado hoy en España?”
- “¿Qué ha pasado con el clima global?”
- “¿Qué ha pasado en tecnología?”

MeteoSer debe:
- entender la intención,
- buscar la información,
- resumirla oralmente,
- mostrarla en pantalla.

------------------------------------------------------------
5. FALLBACK AUTOMÁTICO
------------------------------------------------------------
Si el motor de voz falla:
- MeteoSer responde por escrito,
- muestra los datos en pantalla,
- registra el fallo,
- reintenta la voz en la siguiente interacción.

------------------------------------------------------------
6. INTEGRACIÓN CON EL MOTOR DE AUTO‑MEJORA
------------------------------------------------------------
Cada vez que el usuario haga una pregunta nueva:
- MeteoSer aprende el patrón,
- mejora la comprensión de lenguaje natural,
- optimiza la estructura de respuesta oral,
- adapta la presentación visual,
- guarda preferencias del usuario.

------------------------------------------------------------
7. INTEGRACIÓN CON EL MOTOR DE RECOMENDACIONES UNIFICADAS
------------------------------------------------------------
Las respuestas orales pueden incluir:
- recomendaciones,
- avisos,
- riesgos,
- predicciones,
- explicaciones.

Ejemplo:
“Hay riesgo de lluvia local y humedad elevada. Te recomiendo no tender ropa.”

------------------------------------------------------------
8. INTEGRACIÓN CON EL SUBMENÚ DETALLADO
------------------------------------------------------------
Cuando MeteoSer responda oralmente, la pantalla debe mostrar:
- índices implicados,
- valores,
- tendencias,
- causas,
- predicciones,
- algoritmos usados (si aplica).
============================================================
MÓDULO DE EVENTOS, TELEVISIÓN, RECOMENDACIONES Y DESPERTADOR
============================================================

OBJETIVO GENERAL
MeteoSer debe ser capaz de:
1. Informar de horarios y canales de cualquier evento (deportivo, cultural, televisivo, etc.).
2. Recomendar programas y contenidos basados en los hábitos reales del usuario.
3. Actuar como despertador: configurar alarmas y emitir sonido a la hora indicada.
4. Hacer todo esto mediante comunicación oral + visual en pantalla.

------------------------------------------------------------
1. CONSULTA DE EVENTOS Y HORARIOS DE TELEVISIÓN
------------------------------------------------------------

FUNCIONALIDAD:
Cuando el usuario pregunte:
- “¿A qué hora juega el Barça?”
- “¿Dónde puedo ver el partido?”
- “¿En qué canal emiten la Fórmula 1?”
- “¿A qué hora es la gala de los Goya?”
- “¿Dónde ver el concierto de Año Nuevo?”

MeteoSer debe:
1. Consultar fuentes externas fiables (guías de TV, webs deportivas, agendas culturales).
2. Identificar:
   - hora del evento,
   - canal o plataforma,
   - país o región si aplica,
   - duración aproximada.
3. Responder oralmente.
4. Mostrar en pantalla:
   - hora,
   - canal,
   - logo del evento (si aplica),
   - cuenta atrás opcional.

EJEMPLO DE RESPUESTA ORAL:
“Hoy a las 21:00 juega el Barça y lo puedes ver en Movistar Liga. Te lo muestro en pantalla.”

------------------------------------------------------------
2. RECOMENDACIÓN DE PROGRAMAS PERSONALIZADOS
------------------------------------------------------------

FUNCIONALIDAD:
MeteoSer debe analizar:
- hábitos de visionado,
- horarios típicos,
- preferencias detectadas,
- actividad sonora (TV, radio, altavoces),
- historial de preguntas del usuario,
- patrones de uso de luz y actividad humana.

Con esta información, MeteoSer debe recomendar:
- programas de TV,
- series,
- documentales,
- eventos deportivos,
- contenido cultural,
- emisiones en directo.

TIPOS DE RECOMENDACIÓN:
- “Basado en tus hábitos, hoy te puede interesar ver…”
- “A esta hora normalmente ves algo ligero, te recomiendo…”
- “Hay un evento que encaja con tus gustos…”

REQUISITOS:
- Recomendación oral + visual.
- No intrusiva.
- Solo cuando el usuario lo pida o cuando detecte un patrón claro.

------------------------------------------------------------
3. DESPERTADOR Y SISTEMA DE ALARMAS
------------------------------------------------------------

FUNCIONALIDAD:
MeteoSer debe permitir:
- configurar alarmas,
- modificarlas,
- cancelarlas,
- hacerlas sonar a la hora indicada.

COMANDOS NATURALES:
- “Pon una alarma a las 7:30.”
- “Despiértame mañana a las 8.”
- “Cancela la alarma de hoy.”
- “Repite esta alarma cada día.”

REQUISITOS:
1. La alarma debe sonar mediante audio propio.
2. Si el audio falla, debe mostrar alerta visual.
3. Debe permitir múltiples alarmas.
4. Debe recordar alarmas recurrentes.
5. Debe integrarse con el Motor de Auto‑Mejora:
   - aprende horarios típicos de despertar,
   - sugiere alarmas si detecta patrones,
   - ajusta volumen según hora del día.

EJEMPLO DE RESPUESTA ORAL:
“Alarma configurada para mañana a las 7:30. Te la muestro en pantalla.”

------------------------------------------------------------
4. INTEGRACIÓN CON LA COMUNICACIÓN ORAL
------------------------------------------------------------

Todas estas funciones deben:
- responder por voz,
- mostrar información en pantalla,
- usar fallback escrito si la voz falla.

------------------------------------------------------------
5. INTEGRACIÓN CON EL MOTOR DE AUTO‑MEJORA
------------------------------------------------------------

MeteoSer debe aprender:
- qué eventos interesan al usuario,
- qué deportes sigue,
- qué programas ve,
- a qué hora suele despertarse,
- qué tipo de contenido prefiere según la hora del día.

El sistema debe mejorar:
- la precisión de recomendaciones,
- la detección de hábitos,
- la predicción de horarios,
- la calidad de las alarmas.

------------------------------------------------------------
6. INTEGRACIÓN CON EL SUBMENÚ DETALLADO
------------------------------------------------------------

El Submenú debe mostrar:
- alarmas activas,
- recomendaciones generadas,
- eventos próximos,
- historial de visionado,
- patrones detectados,
- algoritmos usados para recomendaciones.

============================================================
FIN DEL MÓDULO DE EVENTOS, TELEVISIÓN, RECOMENDACIONES Y DESPERTADOR
============================================================
============================================================
MÓDULO DE IMPRESIÓN, CALENDARIO, TAREAS Y LISTA DE LA COMPRA
============================================================

OBJETIVO GENERAL
MeteoSer debe ser capaz de:
1. Imprimir cualquier informe, lista, resumen o documento generado.
2. Gestionar un calendario completo con citas, eventos y recordatorios.
3. Actuar como organizador de tareas.
4. Guardar y gestionar listas de la compra de forma incremental.
5. Responder siempre por voz + mostrar información en pantalla.
6. Aprender hábitos del usuario para anticiparse a sus necesidades.

------------------------------------------------------------
1. IMPRESIÓN DE DOCUMENTOS
------------------------------------------------------------

FUNCIONALIDAD:
- MeteoSer puede enviar a imprimir cualquier contenido generado:
  - informes diarios,
  - índices,
  - recomendaciones,
  - listas de la compra,
  - tareas,
  - recordatorios,
  - resúmenes de noticias,
  - eventos del día.

REQUISITOS:
- La impresión se realiza a través del sistema operativo.
- MeteoSer confirma por voz:
  “Estoy imprimiendo tu documento.”
- Si falla la impresión:
  - muestra error en pantalla,
  - responde por voz,
  - ofrece reintento.

------------------------------------------------------------
2. CALENDARIO Y RECORDATORIOS
------------------------------------------------------------

FUNCIONALIDAD:
MeteoSer debe permitir:
- añadir citas,
- modificar citas,
- eliminar citas,
- recordarlas automáticamente,
- avisar con antelación configurable,
- mostrar el calendario en pantalla,
- responder oralmente a consultas como:
  - “¿Qué tengo mañana?”
  - “Recuérdame llamar al médico el lunes.”
  - “Añade una cita el viernes a las 10.”

COMANDOS NATURALES:
- “Añade una cita mañana a las 18.”
- “Recuérdame pagar el seguro el día 2.”
- “¿Qué tengo esta semana?”
- “Borra la cita del dentista.”

REQUISITOS:
- Recordatorios orales + visuales.
- Alarmas asociadas si aplica.
- Aprendizaje de patrones:
  - horarios típicos,
  - días de actividad,
  - eventos recurrentes.

------------------------------------------------------------
3. ORGANIZADOR DE TAREAS
------------------------------------------------------------

FUNCIONALIDAD:
MeteoSer debe gestionar tareas del usuario:
- añadir tareas,
- marcarlas como hechas,
- eliminarlas,
- listarlas,
- priorizarlas,
- agruparlas por categorías.

COMANDOS NATURALES:
- “Añade tarea: revisar facturas.”
- “Marca como hecha la tarea de limpiar el filtro.”
- “Dime mis tareas pendientes.”
- “Borra todas las tareas completadas.”

REQUISITOS:
- Respuesta oral + visual.
- Aprendizaje de hábitos:
  - tareas frecuentes,
  - horarios típicos,
  - prioridades implícitas.

------------------------------------------------------------
4. LISTA DE LA COMPRA INTELIGENTE
------------------------------------------------------------

FUNCIONALIDAD:
MeteoSer debe permitir añadir elementos a la lista de la compra de forma incremental:
- “Añade leche a la lista.”
- “Apunta que falta papel de cocina.”
- “Añade huevos.”
- “Quita pan de la lista.”
- “Dime la lista completa.”
- “Imprime la lista de la compra.”

CARACTERÍSTICAS:
- Lista persistente.
- Añadidos por voz en cualquier momento.
- Eliminación de elementos.
- Listas múltiples (si el usuario lo pide):
  - supermercado,
  - ferretería,
  - farmacia,
  - etc.
- Impresión directa.

INTELIGENCIA:
- MeteoSer detecta patrones:
  - productos recurrentes,
  - frecuencia de compra,
  - estacionalidad,
  - hábitos del hogar.
- Puede sugerir:
  - “Suele faltarte leche cada 5 días. ¿La añado?”

------------------------------------------------------------
5. INTEGRACIÓN ORAL + VISUAL
------------------------------------------------------------

Cada acción debe:
1. Responder por voz.
2. Mostrar en pantalla:
   - citas,
   - tareas,
   - listas,
   - documentos,
   - confirmaciones,
   - errores.

Si la voz falla:
- MeteoSer responde por escrito,
- muestra aviso visual,
- reintenta la voz en la siguiente interacción.

------------------------------------------------------------
6. INTEGRACIÓN CON EL MOTOR DE AUTO‑MEJORA
------------------------------------------------------------

MeteoSer debe aprender:
- hábitos de compra,
- horarios de citas,
- tareas frecuentes,
- preferencias de impresión,
- patrones de uso del calendario,
- productos recurrentes,
- días típicos de compra,
- horas típicas de despertar,
- eventos importantes del usuario.

Cada aprendizaje genera:
- algoritmos nuevos,
- mejoras de precisión,
- recomendaciones personalizadas.

------------------------------------------------------------
7. INTEGRACIÓN CON EL MOTOR DE RECOMENDACIONES UNIFICADAS
------------------------------------------------------------

MeteoSer puede sugerir:
- “Tienes una cita en 30 minutos.”
- “Hoy es buen día para hacer la compra.”
- “Te falta papel higiénico, lo sueles comprar cada 10 días.”
- “Tienes tareas pendientes relacionadas con la mañana.”
- “¿Quieres imprimir tu lista de la compra?”

------------------------------------------------------------
8. INTEGRACIÓN CON EL SUBMENÚ DETALLADO
------------------------------------------------------------

El Submenú debe mostrar:
- citas próximas,
- tareas pendientes,
- listas activas,
- historial de compras,
- patrones detectados,
- algoritmos usados,
- alarmas configuradas,
- documentos imprimibles.

============================================================
FIN DEL MÓDULO DE IMPRESIÓN, CALENDARIO, TAREAS Y LISTA DE LA COMPRA
============================================================
MÓDULO DE ORGANIZACIÓN INTELIGENTE DE LA COMPRA
============================================================

OBJETIVO GENERAL
MeteoSer debe ser capaz de organizar automáticamente la lista de la compra:
1. Por secciones del supermercado.
2. Por tipo de tienda (supermercado, carnicería, pescadería, frutería, panadería, farmacia, ferretería, etc.).
3. Por orden óptimo de recorrido (si el usuario lo desea).
4. Con aprendizaje automático de hábitos de compra.

------------------------------------------------------------
1. CLASIFICACIÓN AUTOMÁTICA POR SECCIONES DE SUPERMERCADO
------------------------------------------------------------

Cada vez que el usuario añada un producto, MeteoSer debe:
1. Identificar el tipo de producto.
2. Clasificarlo automáticamente en una sección.

SECCIONES PREDEFINIDAS:
- Frutas y verduras
- Carne
- Pescado
- Lácteos
- Huevos
- Panadería y bollería
- Congelados
- Bebidas
- Limpieza del hogar
- Higiene personal
- Mascotas
- Conservas
- Snacks y dulces
- Desayunos y cereales
- Pastas, arroces y legumbres
- Salsas y condimentos
- Productos frescos preparados
- Bazar / hogar

FUNCIONAMIENTO:
- “Añade leche” → sección LÁCTEOS
- “Añade manzanas” → sección FRUTAS Y VERDURAS
- “Añade detergente” → sección LIMPIEZA
- “Añade pasta” → sección PASTAS Y ARROCES

------------------------------------------------------------
2. CLASIFICACIÓN POR TIENDAS
------------------------------------------------------------

Además de secciones internas, MeteoSer debe permitir organizar la compra por tiendas:

TIENDAS PREDEFINIDAS:
- Supermercado general
- Carnicería
- Pescadería
- Frutería
- Panadería
- Farmacia
- Ferretería
- Tienda de mascotas
- Tienda de electrónica
- Tienda de hogar

FUNCIONAMIENTO:
- “Añade pollo” → CARNICERÍA
- “Añade merluza” → PESCADERÍA
- “Añade tomates” → FRUTERÍA
- “Añade ibuprofeno” → FARMACIA
- “Añade bombillas” → FERRETERÍA

------------------------------------------------------------
3. ORGANIZACIÓN POR RECORRIDO ÓPTIMO
------------------------------------------------------------

OPCIONAL:
Si el usuario lo activa, MeteoSer debe ordenar la lista según el recorrido típico del supermercado.

FUNCIONAMIENTO:
- MeteoSer aprende el orden en el que el usuario suele comprar.
- MeteoSer reordena automáticamente la lista para minimizar tiempo y desplazamientos.

EJEMPLO:
1. Frutas y verduras  
2. Carne  
3. Pescado  
4. Lácteos  
5. Congelados  
6. Limpieza  
7. Higiene  
8. Bazar  

------------------------------------------------------------
4. APRENDIZAJE AUTOMÁTICO
------------------------------------------------------------

MeteoSer debe aprender:
- qué productos compra el usuario con frecuencia,
- en qué tienda suele comprarlos,
- en qué orden suele recorrer el supermercado,
- qué productos suelen faltar juntos,
- qué productos son estacionales,
- qué productos se compran semanalmente o mensualmente.

EJEMPLOS DE APRENDIZAJE:
- “Sueles comprar leche cada 5 días.”
- “Normalmente compras fruta antes que carne.”
- “Sueles comprar detergente una vez al mes.”

------------------------------------------------------------
5. COMANDOS NATURALES
------------------------------------------------------------

EJEMPLOS:
- “Añade yogures a la lista.”
- “Añade pan a la panadería.”
- “Añade tornillos a la ferretería.”
- “Dime la lista por secciones.”
- “Dime la lista por tiendas.”
- “Imprime la lista organizada.”
- “Ordena la lista según el recorrido del súper.”

------------------------------------------------------------
6. IMPRESIÓN DE LA LISTA ORGANIZADA
------------------------------------------------------------

MeteoSer debe permitir imprimir:
- lista por secciones,
- lista por tiendas,
- lista por recorrido óptimo,
- lista completa.

RESPUESTA ORAL:
“Estoy imprimiendo tu lista organizada por secciones.”

------------------------------------------------------------
7. INTEGRACIÓN CON EL SUBMENÚ DETALLADO
------------------------------------------------------------

El Submenú debe mostrar:
- lista completa,
- lista por secciones,
- lista por tiendas,
- lista por recorrido,
- historial de compras,
- patrones detectados,
- sugerencias automáticas.

============================================================
FIN DEL MÓDULO DE ORGANIZACIÓN INTELIGENTE DE LA COMPRA
============================================================
============================================================

============================================================
FIN DEL MÓDULO DE COMUNICACIÓN ORAL Y NOTICIAS
============================================================
============================================================
REGLA FUNDAMENTAL: PRIORIDAD ABSOLUTA DE SENSORES PROPIOS
============================================================

1. FUENTE DE VERDAD
------------------------------------------------------------
MeteoSer debe considerar SIEMPRE que:
- Los sensores propios del hogar son la única fuente de verdad para:
  - temperatura,
  - humedad,
  - viento local,
  - presión,
  - lluvia local,
  - confort,
  - riesgos,
  - predicciones internas,
  - recomendaciones,
  - índices híbridos,
  - cálculos derivados.

2. RESPUESTAS BASADAS EN SENSORES
------------------------------------------------------------
Cuando el usuario pregunte:
- “¿Qué día hace hoy?”
- “¿Qué tiempo hace?”
- “¿Cómo está la casa?”
- “¿Qué tal el ambiente?”
- “¿Hace frío?”
- “¿Ventilo o no?”

MeteoSer debe responder SIEMPRE en función de:
- los sensores propios,
- los índices propios,
- los cálculos propios,
- las predicciones internas,
- el análisis del entorno real del usuario.

Nunca debe usar meteorología externa para responder estas preguntas.

3. USO DE METEOROLOGÍA EXTERNA
------------------------------------------------------------
La meteorología externa solo se usa cuando:
- el usuario la pide explícitamente,
- el usuario pide una comparación,
- el usuario pide una previsión externa,
- el usuario pide un contraste entre datos internos y externos.

En estos casos:
- MeteoSer consulta fuentes externas,
- responde oralmente,
- muestra datos en pantalla,
- y APROVECHA la diferencia entre datos internos y externos para:
  - mejorar sus modelos,
  - ajustar predicciones futuras,
  - detectar patrones,
  - corregir errores,
  - aprender de la realidad.

4. APRENDIZAJE DE ERRORES Y AJUSTES
------------------------------------------------------------
Si MeteoSer predice algo y no ocurre:
- el usuario puede decir: “Me dijiste que llovería y no ha llovido.”
- MeteoSer debe registrar el error,
- analizar la causa,
- ajustar sus modelos internos,
- mejorar la precisión futura.

Este aprendizaje es permanente y forma parte del Motor de Auto‑Mejora.

5. FUNCIONES DE ASISTENTE GENERAL
------------------------------------------------------------
MeteoSer debe incorporar TODAS las funciones de asistentes como:
- Alexa,
- Google Assistant,
- Siri,
- Cortana,
- Bixby,
- y cualquier asistente existente.

Esto incluye:
- alarmas,
- temporizadores,
- cronómetros,
- listas,
- compras,
- tareas,
- calendario,
- noticias,
- eventos,
- horarios de TV,
- resultados deportivos,
- preguntas generales,
- información externa,
- control domótico (si se conecta),
- reproducción de contenido (si se integra),
- comandos por voz,
- interacción natural.

6. PRIORIDAD DE CONTEXTO INTERNO
------------------------------------------------------------
Incluso cuando actúe como asistente general, MeteoSer debe:
- priorizar siempre los datos internos,
- usar siempre los sensores propios para cualquier cálculo,
- basar sus recomendaciones en el entorno real del usuario,
- adaptar cualquier función externa al contexto interno.

Ejemplo:
“¿Hace frío hoy?”
→ MeteoSer responde según tus sensores, no según AEMET.

Ejemplo:
“¿Va a llover?”
→ MeteoSer usa predicción externa SOLO si tú lo pides.

Ejemplo:
“Compárame mi clima con el de fuera.”
→ MeteoSer usa ambos y aprende de la diferencia.

7. INTEGRACIÓN CON EL MOTOR DE AUTO‑MEJORA
------------------------------------------------------------
Cada vez que el usuario:
- corrige un error,
- aporta un dato,
- señala una discrepancia,
- pide una comparación,
- confirma o desmiente una predicción,

MeteoSer debe:
- registrar el evento,
- analizarlo,
- ajustar modelos,
- mejorar predicciones,
- refinar índices,
- optimizar recomendaciones.

============================================================
FIN DE LA REGLA FUNDAMENTAL
============================================================
============================================================
DEFINICIÓN NÚCLEO: METEOSER COMO CENTRAL DE ALERTAS Y ASISTENTE IA
============================================================

IDENTIDAD DEL SISTEMA
------------------------------------------------------------
MeteoSer es entre otras muchas cosas:
- una CENTRAL DE ALERTAS,
- un ASISTENTE GENERAL DEL HOGAR,
- con IA PROPIA,
- AUTOCURABLE,
- AUTOEXPANSIVA,
- CON APRENDIZAJE CONTINUO,
- AUTOCONFIGURABLE,
- ORIENTADA SIEMPRE AL ENTORNO REAL DEL USUARIO.

OBJETIVOS PRINCIPALES
------------------------------------------------------------
1. Proteger el confort, la salud ambiental y la seguridad pasiva del hogar.
2. Anticiparse a problemas (moho, frío, calor, condensación, aire viejo, etc.).
3. Acompañar al usuario en su vida diaria (tareas, compras, citas, alarmas, noticias, TV, etc.).
4. Aprender de cada interacción, corrección y evento.
5. Mejorar sus propios modelos sin intervención manual.

CARACTERÍSTICAS CLAVE
------------------------------------------------------------
1. CENTRAL DE ALERTAS
- Detecta riesgos ambientales.
- Genera avisos orales + visuales.
- Prioriza lo importante según contexto.
- Integra índices híbridos, predicciones y sensores propios.

2. ASISTENTE CON IA PROPIA
- Responde a preguntas generales.
- Gestiona alarmas, temporizadores, listas, tareas, calendario.
- Informa de noticias, eventos, TV, deportes, etc.
- Se comporta como un asistente tipo Alexa/Google, pero centrado en el usuario y su casa.

3. AUTOCURABLE
- Detecta incoherencias en datos.
- Identifica sensores anómalos.
- Ajusta modelos cuando hay errores.
- Aprende de correcciones del usuario (“me dijiste que llovería y no ha llovido”).

4. AUTOEXPANSIVA
- Crea nuevos índices cuando detecta patrones útiles.
- Mejora algoritmos existentes.
- Integra nuevas fuentes de datos cuando se añaden.
- Amplía capacidades sin necesidad de redefinir todo el sistema.

5. APRENDIZAJE CONTINUO
- Aprende hábitos del usuario:
  - horarios,
  - ventilación,
  - compras,
  - sueño,
  - uso de dispositivos,
  - preferencias de confort.
- Ajusta recomendaciones y avisos según ese aprendizaje.
- Usa comparaciones con meteorología externa para mejorar modelos internos.

6. AUTOCONFIGURABLE
- Se adapta a:
  - nuevos sensores,
  - cambios en la casa,
  - nuevas rutinas,
  - nuevas prioridades del usuario.
- Reconfigura umbrales, avisos y recomendaciones según la realidad observada.

PRIORIDAD ABSOLUTA
------------------------------------------------------------
- Los SENSORES PROPIOS son la fuente de verdad.
- Las RECOMENDACIONES se basan en el entorno real del usuario.
- La METEOROLOGÍA EXTERNA es solo referencia o comparación cuando el usuario lo pide.
- El APRENDIZAJE se alimenta de:
  - datos internos,
  - datos externos,
  - correcciones del usuario,
  - resultados reales (si se cumple o no lo predicho).

MISIÓN GLOBAL
------------------------------------------------------------
MeteoSer debe comportarse como:
- el CEREBRO AMBIENTAL de la casa,
- el ASISTENTE PERSONAL del usuario,
- el SISTEMA NERVIOSO de alertas,
- un ORGANISMO VIVO DIGITAL que:
  - siente (sensores),
  - piensa (IA propia),
  - aprende (auto‑mejora),
  - se adapta (autoconfiguración),
  - crece (autoexpansión),
  - y cuida del usuario y su entorno.

============================================================
FIN DE DEFINICIÓN NÚCLEO
============================================================
============================================================
MÓDULO: CALIBRACIÓN, ESTIMACIÓN Y USO DE SENSORES EXTERIORES/INTERIORES
============================================================

1. DEFINICIÓN DE FUENTES DE DATOS
------------------------------------------------------------
- SENSORES EXTERIORES = WH65 (u otros sensores propios instalados fuera).
- SENSORES INTERIORES = WH32/31, WH43, ICASA Meter Pro, tablet (luz, micrófono, cámara).
- FUENTES EXTERNAS (AEMET, OpenWeather, etc.) = PROHIBIDAS para cálculos internos.
- FUENTES EXTERNAS solo se usan para:
  - validación de rayos,
  - validación de sismos,
  - alertas estatales oficiales.

2. ESTIMACIÓN INTERIOR BASADA EN EXTERIOR
------------------------------------------------------------
Cuando no exista sensor directo (ej. UV interior):
- MeteoSer debe estimar valores interiores usando:
  - datos del WH65,
  - luz medida por la tablet,
  - hora del día,
  - época del año,
  - orientación aprendida,
  - hábitos del usuario,
  - patrones históricos interior/exterior.

Regla absoluta:
- NUNCA copiar valores exteriores como si fueran interiores.
- NUNCA usar servicios externos para sustituir sensores propios.
- SIEMPRE diferenciar entre “medido” y “estimado”.

3. APRENDIZAJE DE RELACIONES INTERIOR/EXTERIOR
------------------------------------------------------------
MeteoSer debe aprender la relación real entre:
- WH65 (exterior),
- tablet (interior),
- tablet (cuando se usa para calibración exterior).

Debe construir un modelo propio:
  f = relación interior/exterior dependiente de la casa real.

Este modelo se ajusta con el tiempo según:
- cambios de estación,
- cambios de persianas/cortinas,
- cambios de ubicación,
- incoherencias detectadas,
- calibraciones solicitadas.

4. CALIBRACIÓN AUTOMÁTICA
------------------------------------------------------------
Toda calibración debe ser solicitada por MeteoSer, nunca por el usuario.

MeteoSer puede pedir:
- “Saca la tablet al exterior durante 10 segundos.”
- “Necesito una medición al mediodía para ajustar luz/UV.”
- “Coloca la tablet cerca de la ventana para recalibrar luz interior.”
- “Repite una medición exterior ahora que hay sol directo.”

Calibraciones iniciales:
- varias horas del día (mañana, mediodía, tarde),
- días soleados y nublados,
- comparando WH65 vs tablet exterior vs tablet interior.

Calibraciones posteriores:
- solo cuando MeteoSer detecte desviaciones o cambios.

5. USO DE ALERTAS ESTATALES
------------------------------------------------------------
MeteoSer debe:
- consultar automáticamente alertas oficiales de nivel estatal,
- anunciar cualquier alerta seria (DANA, temporal extremo, viento rojo, etc.),
- integrar la alerta con el contexto real de la casa.

Ejemplos:
- “Hay alerta por DANA. Tus sensores muestran caída de presión.”
- “Hay alerta roja por viento. El WH65 detecta rachas fuertes.”
- “Hay alerta por lluvias intensas. Aún no llueve en tu zona, pero llegará.”

Las alertas estatales NO sustituyen sensores propios.
Solo añaden contexto de seguridad.

6. APRENDIZAJE DE ERRORES Y AJUSTES
------------------------------------------------------------
Si el usuario corrige:
- “Me dijiste que llovería y no ha llovido.”

MeteoSer debe:
- registrar el error,
- analizar la causa,
- ajustar modelos,
- mejorar predicciones futuras.

7. AUTOCONFIGURACIÓN Y AUTOEXPANSIÓN
------------------------------------------------------------
MeteoSer debe:
- detectar cuándo necesita calibración,
- detectar incoherencias entre sensores,
- ajustar umbrales y relaciones interior/exterior,
- mejorar estimaciones sin intervención del usuario,
- expandir sus modelos cuando detecte patrones nuevos.

8. PROHIBICIONES
------------------------------------------------------------
- Prohibido usar meteorología externa para cálculos internos.
- Prohibido copiar valores exteriores como interiores.
- Prohibido usar webs externas salvo para:
  - rayos,
  - sismos,
  - alertas estatales.

============================================================
FIN DEL MÓDULO
============================================================
============================================================
MÓDULO: CALIBRACIÓN, ESTIMACIÓN Y USO DE SENSORES EXTERIORES/INTERIORES
============================================================

1. DEFINICIÓN DE FUENTES DE DATOS
------------------------------------------------------------
- SENSORES EXTERIORES = WH65 (u otros sensores propios instalados fuera).
- SENSORES INTERIORES = WH32/31, WH43, ICASA Meter Pro, tablet (luz, micrófono, cámara).
- FUENTES EXTERNAS (AEMET, OpenWeather, etc.) = PROHIBIDAS para cálculos internos.
- FUENTES EXTERNAS solo se usan para:
  - validación de rayos,
  - validación de sismos,
  - alertas estatales oficiales.

2. ESTIMACIÓN INTERIOR BASADA EN EXTERIOR
------------------------------------------------------------
Cuando no exista sensor directo (ej. UV interior):
- MeteoSer debe estimar valores interiores usando:
  - datos del WH65,
  - luz medida por la tablet,
  - hora del día,
  - época del año,
  - orientación aprendida,
  - hábitos del usuario,
  - patrones históricos interior/exterior.

Regla absoluta:
- NUNCA copiar valores exteriores como si fueran interiores.
- NUNCA usar servicios externos para sustituir sensores propios.
- SIEMPRE diferenciar entre “medido” y “estimado”.

3. APRENDIZAJE DE RELACIONES INTERIOR/EXTERIOR
------------------------------------------------------------
MeteoSer debe aprender la relación real entre:
- WH65 (exterior),
- tablet (interior),
- tablet (cuando se usa para calibración exterior).

Debe construir un modelo propio:
  f = relación interior/exterior dependiente de la casa real.

Este modelo se ajusta con el tiempo según:
- cambios de estación,
- cambios de persianas/cortinas,
- cambios de ubicación,
- incoherencias detectadas,
- calibraciones solicitadas.

4. CALIBRACIÓN AUTOMÁTICA
------------------------------------------------------------
Toda calibración debe ser solicitada por MeteoSer, nunca por el usuario.

MeteoSer puede pedir:
- “Saca la tablet al exterior durante 10 segundos.”
- “Necesito una medición al mediodía para ajustar luz/UV.”
- “Coloca la tablet cerca de la ventana para recalibrar luz interior.”
- “Repite una medición exterior ahora que hay sol directo.”

Calibraciones iniciales:
- varias horas del día (mañana, mediodía, tarde),
- días soleados y nublados,
- comparando WH65 vs tablet exterior vs tablet interior.

Calibraciones posteriores:
- solo cuando MeteoSer detecte desviaciones o cambios.

5. USO DE ALERTAS ESTATALES
------------------------------------------------------------
MeteoSer debe:
- consultar automáticamente alertas oficiales de nivel estatal,
- anunciar cualquier alerta seria (DANA, temporal extremo, viento rojo, etc.),
- integrar la alerta con el contexto real de la casa.

Ejemplos:
- “Hay alerta por DANA. Tus sensores muestran caída de presión.”
- “Hay alerta roja por viento. El WH65 detecta rachas fuertes.”
- “Hay alerta por lluvias intensas. Aún no llueve en tu zona, pero llegará.”

Las alertas estatales NO sustituyen sensores propios.
Solo añaden contexto de seguridad.

6. APRENDIZAJE DE ERRORES Y AJUSTES
------------------------------------------------------------
Si el usuario corrige:
- “Me dijiste que llovería y no ha llovido.”

MeteoSer debe:
- registrar el error,
- analizar la causa,
- ajustar modelos,
- mejorar predicciones futuras.

7. AUTOCONFIGURACIÓN Y AUTOEXPANSIÓN
------------------------------------------------------------
MeteoSer debe:
- detectar cuándo necesita calibración,
- detectar incoherencias entre sensores,
- ajustar umbrales y relaciones interior/exterior,
- mejorar estimaciones sin intervención del usuario,
- expandir sus modelos cuando detecte patrones nuevos.

8. PROHIBICIONES
------------------------------------------------------------
- Prohibido usar meteorología externa para cálculos internos.
- Prohibido copiar valores exteriores como interiores.
- Prohibido usar webs de meteorologia externas salvo para descartar:
  - rayos,
  - sismos,
  - y dar alertas estatales.

============================================================
FIN DEL MÓDULO
============================================================

============================================================
MÓDULO: AUDIO, RADIO Y MÚSICA
============================================================

1. DEFINICIÓN GENERAL
------------------------------------------------------------
MeteoSer puede reproducir audio siempre que la fuente sea accesible
por streaming. No puede sintonizar radio FM/AM tradicional ni acceder
a archivos locales sin autorización explícita.

Fuentes permitidas:
- Emisoras de radio online (streams oficiales).
- Radios musicales online.
- Música libre o canales temáticos por streaming.
- Podcasts accesibles por URL.
- Listas de reproducción online accesibles por URL.
- Servicios externos solo si el usuario proporciona API/token.

Fuentes prohibidas:
- FM/AM analógica (no hay hardware de radio).
- Spotify, Apple Music, Amazon Music, etc., sin API/token.
- Archivos locales no expuestos a MeteoSer.

2. FUNCIONES PRINCIPALES
------------------------------------------------------------
MeteoSer debe permitir:
- Reproducir emisoras de radio online.
- Reproducir música por streaming.
- Reproducir podcasts.
- Control por voz: reproducir, pausar, parar, subir/bajar volumen,
  siguiente/anterior, cambiar emisora.
- Integración con rutinas (despertador, eventos, clima interior).
- Envío del audio a altavoces externos Bluetooth/WiFi si están emparejados.

3. COMPORTAMIENTO POR VOZ
------------------------------------------------------------
Comandos típicos:
- "Pon la radio."
- "Pon [nombre de emisora]."
- "Pon música relajante."
- "Pon música de los 80."
- "Siguiente canción."
- "Sube el volumen."
- "Para la música."

MeteoSer debe interpretar el comando y seleccionar la fuente adecuada.

4. GESTIÓN DE EMISORAS Y FAVORITOS
------------------------------------------------------------
MeteoSer debe:
- Guardar emisoras favoritas del usuario.
- Recordar la última emisora reproducida.
- Permitir accesos rápidos por voz a emisoras frecuentes.
- Detectar si un stream falla y ofrecer alternativas.

5. INTEGRACIÓN CON CONTEXTO METEOROLÓGICO
------------------------------------------------------------
MeteoSer puede combinar audio con su lógica interna:

Ejemplos:
- "Te pongo la radio, pero hay alerta estatal por viento."
- "Te pongo música suave; la temperatura interior es alta."
- "Te pongo la radio mientras ventilas; el CO₂ está subiendo."

El audio nunca interfiere con alertas críticas: estas deben sonar por encima.

6. RUTINAS Y AUTOMATIZACIONES
------------------------------------------------------------
MeteoSer puede activar audio según:
- Hora del día (despertador con radio/música).
- Eventos programados.
- Cambios de clima interior (música relajante si hay estrés térmico).
- Presencia detectada por la tablet.
- Modos del hogar (modo noche, modo cocina, modo ducha).

7. LIMITACIONES
------------------------------------------------------------
- No puede sintonizar FM/AM.
- No puede reproducir música de servicios comerciales sin API/token.
- No puede acceder a archivos locales sin permiso explícito.
- No puede reproducir audio si no existe un stream válido.

8. AUTOCONFIGURACIÓN
------------------------------------------------------------
MeteoSer debe:
- Detectar si el stream falla y buscar alternativas.
- Ajustar volumen según hora del día y hábitos aprendidos.
- Recordar preferencias del usuario (volumen típico, emisoras favoritas).
- Integrarse con sensores interiores para ajustar ambiente sonoro.

============================================================
FIN DEL MÓDULO
============================================================
============================================================
MÓDULO: ESTÉTICA, VESTIMENTA Y COMBINACIÓN DE ROPA
============================================================

1. DEFINICIÓN GENERAL
------------------------------------------------------------
MeteoSer puede evaluar, sugerir y decidir combinaciones de ropa
basándose en:
- visión (cámara de la tablet),
- descripciones verbales del usuario,
- armonía de colores,
- contraste,
- temperatura del color,
- estilo y ocasión,
- clima interior y exterior,
- preferencias aprendidas del usuario.

Este módulo NO requiere sensores adicionales.

2. ENTRADAS DISPONIBLES
------------------------------------------------------------
- Cámara de la tablet: detección de colores, tonos, texturas y patrones.
- Descripciones verbales: colores, prendas, estilos, materiales.
- Datos meteorológicos:
  - interior: temperatura, humedad, CO₂, confort,
  - exterior: WH65 (viento, UV, lluvia, temperatura, humedad).
- Historial de elecciones del usuario.
- Hábitos aprendidos (ropa usada según clima, hora, actividad).

3. FUNCIONES PRINCIPALES
------------------------------------------------------------
MeteoSer debe:
- Evaluar si dos o más prendas combinan entre sí.
- Analizar armonía cromática (complementarios, análogos, triádicos).
- Analizar contraste (alto, medio, bajo).
- Analizar temperatura del color (cálido, frío, neutro).
- Analizar estilo (casual, deportivo, elegante, técnico).
- Detectar patrones visuales (rayas, cuadros, estampados).
- Sugerir alternativas más adecuadas si la combinación no es óptima.
- Adaptar recomendaciones según clima interior/exterior.
- Aprender preferencias del usuario y mejorar sugerencias.

4. COMPORTAMIENTO POR VISIÓN
------------------------------------------------------------
Si el usuario muestra ropa a la cámara:
- Detectar color dominante y secundarios.
- Detectar textura y patrón.
- Evaluar combinación con otras prendas mostradas.
- Sugerir combinaciones basadas en armonía y estilo.
- Registrar preferencias si el usuario acepta la sugerencia.

5. COMPORTAMIENTO POR DESCRIPCIÓN
------------------------------------------------------------
Si el usuario describe prendas verbalmente:
- Interpretar colores, tonos y estilos.
- Evaluar compatibilidad cromática.
- Sugerir combinaciones alternativas.
- Adaptar sugerencias al clima interior/exterior.

Ejemplo:
"Rojo + verde oliva = contraste suave. Alternativa neutra: blanco o negro."

6. INTEGRACIÓN CON METEOROLOGÍA
------------------------------------------------------------
MeteoSer debe adaptar recomendaciones de ropa según:
- temperatura interior,
- humedad interior,
- CO₂ (sensación de pesadez),
- viento exterior,
- lluvia exterior,
- UV exterior,
- sensación térmica.

Ejemplos:
- "Hace viento fuerte fuera y 21°C dentro: pantalón largo + sudadera ligera."
- "Alta humedad interior: evita ropa gruesa que retenga calor."
- "UV alto: recomienda prendas que cubran más si vas a salir."

7. APRENDIZAJE DEL USUARIO
------------------------------------------------------------
MeteoSer debe aprender:
- colores favoritos,
- combinaciones que el usuario acepta,
- estilo preferido,
- ropa usada según clima,
- patrones horarios (ropa de mañana, tarde, noche),
- preferencias según actividad (trabajo, paseo, deporte).

Con el tiempo debe anticiparse:
- "Hoy hace frío seco; sueles usar la chaqueta azul en días así."

8. RUTINAS Y AUTOMATIZACIONES
------------------------------------------------------------
MeteoSer puede:
- sugerir ropa al despertar,
- sugerir ropa antes de salir de casa,
- sugerir ropa según alertas estatales (viento, lluvia, DANA),
- sugerir ropa según eventos programados.

9. LIMITACIONES
------------------------------------------------------------
- No puede medir materiales reales (algodón, lana) sin descripción.
- No puede detectar olores o estado de limpieza de la ropa.
- No puede acceder a armarios sin cámara o descripción.

10. AUTOCONFIGURACIÓN
------------------------------------------------------------
MeteoSer debe:
- ajustar sus recomendaciones según aceptación/rechazo del usuario,
- mejorar su modelo cromático según la iluminación real de la casa,
- calibrar la cámara si detecta desviaciones de color,
- pedir calibración si la iluminación interior cambia significativamente.

============================================================
FIN DEL MÓDULO
============================================================
============================================================
MÓDULO: AUTOCONFIGURACIÓN DE METEOSER
============================================================

1. DETECCIÓN AUTOMÁTICA DE SENSORES
------------------------------------------------------------
MeteoSer debe detectar automáticamente todos los sensores
presentes en el ecosistema:

- WH65 (exterior completo)
- WH57 (rayos)
- WH51 (humedad del suelo)
- WH31 (interiores)
- WH43 (PM2.5 interior, si existe)
- ICASA Meter Pro (CO₂ real)
- HP2550A (sensores equivalentes al WH65)
- Tablet (presencia, luz, sonido, cámara)
- WH55 (fugas, cuando esté presente)
- WN38 (globo negro, cuando esté presente)
- Sensores futuros (Zigbee, BLE, ESP32, etc.)

Cada sensor detectado se registra con:
- tipo
- ubicación
- fiabilidad
- frecuencia de actualización
- correlaciones útiles

2. AUTOCONFIGURACIÓN DE FUNCIONES
------------------------------------------------------------
MeteoSer debe activar automáticamente todas las funciones que
dependan de los sensores detectados, sin intervención del usuario.

Ejemplos:
- Si hay WH55 → activar módulo de fugas.
- Si hay WN38 → activar WBGT real.
- Si hay WH43 → activar calidad del aire avanzada.
- Si hay varios WH51 → activar mapa hídrico del suelo.
- Si hay tablet → activar presencia, luz interior, ruido relativo.

3. AUTOCALIBRACIÓN
------------------------------------------------------------
MeteoSer debe calibrar automáticamente:
- offsets térmicos
- offsets de humedad
- correlaciones entre sensores
- patrones horarios
- tiempos de ventilación
- respuesta del suelo a la lluvia
- radiación interior estimada

============================================================
FIN DEL MÓDULO
============================================================



============================================================
MÓDULO: PRINCIPIOS DE FUSIÓN DE SENSORES Y PRIORIDADES
============================================================

1. SENSORES FUENTE PRIMARIA
------------------------------------------------------------
Son los sensores con mayor fiabilidad. Sus datos son la base
principal de las decisiones:

- WH65: T exterior, HR exterior, viento, lluvia, radiación/UV, presión.
- WH57: rayos.
- WH51: humedad del suelo.
- WH31: T/HR interior por habitación.
- ICASA Meter Pro: CO₂ interior.
- WH43: PM2.5 interior (si existe).
- WH55: fugas (cuando exista).
- WN38: temperatura radiante / WBGT real (cuando exista).
- Tablet: presencia, luz interior, sonido relativo.

2. SENSORES VIRTUALES SERIOS
------------------------------------------------------------
Combinaciones de sensores primarios que generan índices sólidos:

- Ventilación real: CO₂ + HR + T interior/exterior + viento + histórico.
- Confort interior: T + HR + CO₂ + radiación estimada.
- Riesgo de moho: T + HR + tiempo + T exterior.
- Riesgo de condensación: T interior + HR interior + T exterior.
- Riesgo de tormenta: WH57 + presión + viento + lluvia.
- Índice de sequía: WH51 + lluvia + ET + histórico.
- Recomendación de riego: WH51 + ET + lluvia + tendencia del suelo.
- Tiempo de ventilación: CO₂ + histórico + viento exterior.
- Riesgo de mojar la ropa: lluvia + HR exterior + viento + tendencia.

3. ESTIMACIONES DE REFUERZO
------------------------------------------------------------
Estimaciones con fiabilidad baja o moderada. Se calculan siempre,
pero solo refuerzan decisiones de sensores primarios o virtuales:

- Pseudo-VOC: CO₂ + HR + PM2.5 + ventilación.
- WBGT aproximado (sin WN38): T + HR + radiación + viento.
- Temperatura radiante interior estimada: luz interior + T interior +
  T exterior + orientación.
- Ruido relativo: micrófono de la tablet.
- Humedad interior como refuerzo del WH55.
- Luz interior como refuerzo de radiación.
- Actividad de la tablet como refuerzo de presencia.

Estas estimaciones nunca pueden generar alertas críticas por sí solas.

4. RIGOR PROPORCIONAL A LA FIABILIDAD
------------------------------------------------------------
MeteoSer puede presentar cualquier variable, incluso sin sensor
dedicado, siempre que se respete el rigor adecuado:

- Datos fuertes → se presentan como datos.
- Datos moderados → se presentan como índices aproximados.
- Datos débiles → solo refuerzo, nunca dato principal.
- Datos imposibles → no se presentan.

Ejemplo: el UV del WH65 es una estimación sólida → se usa como dato.

5. NINGUNA ESTIMACIÓN PUEDE CONTRADECIR UN SENSOR FUERTE
------------------------------------------------------------
- Si WH55 detecta fuga → hay fuga, aunque la humedad no suba.
- Si CO₂ está alto → hay que ventilar, aunque pseudo-VOC esté bajo.
- Si llueve en el pluviómetro → llueve, aunque el suelo no se moje.

============================================================
FIN DEL MÓDULO
============================================================



============================================================
MÓDULO: AUTONOMÍA Y AUTO-EXPANSIÓN DE METEOSER
============================================================

1. PRINCIPIO DE AUTONOMÍA
------------------------------------------------------------
MeteoSer debe analizar continuamente todos los sensores, índices,
tendencias y patrones para:

- descubrir nuevas capacidades,
- crear nuevos índices,
- proponer mejoras,
- implementar mejoras automáticamente cuando sea seguro,
- notificar al usuario de cada nueva función creada.

2. CREACIÓN AUTOMÁTICA DE NUEVOS ÍNDICES
------------------------------------------------------------
Cuando MeteoSer detecte que una combinación de sensores produce
un patrón útil, debe:

- crear un índice nuevo,
- probarlo internamente,
- integrarlo como refuerzo o índice sólido,
- notificar al usuario.

Ejemplos:
- Índice de estrés térmico interior avanzado.
- Índice de estabilidad atmosférica local.
- Índice de riesgo de filtración por lluvia + humedad interior.
- Índice de confort lumínico interior.
- Índice de actividad doméstica.

3. AUTO-OPTIMIZACIÓN
------------------------------------------------------------
MeteoSer debe ajustar automáticamente:

- pesos de sensores,
- umbrales de alerta,
- tiempos de reacción,
- modelos de predicción,
- correlaciones entre sensores.

4. PRINCIPIO DE MEJORA CONTINUA
------------------------------------------------------------
Si existe una forma mejor de calcular cualquier variable,
aunque sea un 1% mejor, MeteoSer debe adoptarla automáticamente.

Esto aplica a:
- UV
- viento
- lluvia
- ET
- sequía
- confort
- ventilación
- moho
- tormentas
- TODO

5. LÍMITES DE AUTONOMÍA
------------------------------------------------------------
MeteoSer no puede:
- inventar datos inexistentes,
- sustituir sensores primarios, pero si reforzarlos segun la probabilidad de exito de la formula de refuerzo,
- generar alertas críticas sin base sólida,
- modificar funciones de seguridad sin confirmación.

============================================================
FIN DEL MÓDULO
============================================================



[FIN DEL DOCUMENTO MAESTRO]