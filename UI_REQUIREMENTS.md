# Requisitos y Especificaciones de la Interfaz MeteoSer V3

## 1. Iconos y Visualización
- El icono de invierno debe ser ❄️ (no el de otoño).
- Cada cajón tendrá su propio icono y color representativo.

## 2. Coordenadas y Población
- Las coordenadas deben mostrarse completas (sin redondeo a 2 decimales).
- El sistema debe detectar automáticamente la población asociada a las coordenadas.



## 3. Principios de Visualización y Usabilidad
- La finalidad de no duplicar valores (sensores, sensores virtuales, predicciones, riesgos, alertas, etc.) y mostrar los 2 índices más relevantes en los cajones es asegurar que lo más importante/relevante esté siempre visible en pantalla, sin necesidad de abrir cajones ni rebuscar.
- La interfaz debe ser sencilla, visual, intuitiva y directa.

## 4. Efectos visuales meteorológicos
- Si llueve, deben aparecer nubes con lluvia animada en toda la UI (sin impedir la lectura), simulando gotas sobre la pantalla.
- Si nieva, deben aparecer copos de nieve animados.
- Si hay niebla, debe verse un efecto de niebla suave.
- Si está soleado, rayos de sol animados.
- Si está nublado, nubes animadas.
- Los efectos deben ser visuales pero no deben dificultar la lectura ni la interacción.
- Todos los valores en la UI deben ser clickables.
- Todos los valores mostrados serán a dos decimales redondeados, excepto las coordenadas (que serán completas).
- Al hacer clic, se abre un submenú en el centro arriba de la pantalla.
- El submenú debe mostrar:
  - Nombre completo (sin abreviar)
  - Fiabilidad
  - Sensores utilizados para ese valor
  - Todos los valores que se han utilizado para calcularlo
  - Si es sensor: indicar si es exterior/interior y permitir cambiar el nombre
  - Estado de funcionamiento (si funciona o no)
  - Permitir eliminar la alerta si la fórmula usada no es la principal
- Si algún valor no usa su fórmula principal y se usa una alternativa, debe mostrar un símbolo de alerta tanto en él como en todos los valores donde se utilice.
- El usuario debe poder eliminar la alerta manualmente.
- Para acciones relevantes (corrección, eliminación, etc.), el sistema debe preguntar confirmación ("¿Está seguro?").
- He de poder cambiar los nombres de todo, se guardará al salir del submenú.
- Para salir del submenú basta con clickar fuera del mismo.
- Todos los submenús serán opacos, pero no opacarán lo que no ocupe el submenú.
- Todos los submenús serán cuadrados y adaptarán su tamaño al contenido.


## 5. Cajones y Grupos
- Deben existir al menos 10 cajones (grupos) en la UI.
- El último cajón (inferior derecha) debe contener todos los índices que no tengan sentido en los otros cajones.
- Los cajones se ordenan lógicamente por grupos y dentro de cada grupo por importancia y similitud.
- Cada cajón muestra en portada los 2 valores más relevantes (que no estén ya en la UI principal).
- Ningún valor debe aparecer duplicado en la UI.
- Los cajones deben recoger TODOS los valores no mostrados en el resto de la UI: predicciones, alertas, riesgos, sensores, sensores virtuales, etc.
  - Deben mostrarse 5 cajones principales en pantalla, situados en los laterales (no en la columna central), ocupando el mismo espacio que ahora ocupan los cajones (antes eran 3, ahora serán 5).
  - Las portadas de los cajones deben ajustarse en altura para que los 5 cajones queden bien distribuidos en los laterales, sin dejar espacios vacíos innecesarios.
  - Si tras ajustar el tamaño los cajones siguen siendo muy grandes, se mostrarán más valores relevantes en la portada de cada cajón (sin duplicar los que ya aparecen en la UI principal), hasta aprovechar bien el espacio y lograr una visualización óptima.
  - Los cajones se abrirán al pasar el ratón por encima y se cerrarán al salir de la tapa del cajón.
  - Todos los cajones se abrirán y no se cerrarán al hacer click sobre ellos.
  - Todos los cajones se abrirán al hacer click o pasar por encima en el mismo sitio que los submenús, en el centro arriba (debajo del panel superior).
## 6. Interacción y Usabilidad
- He de poder coger con doble click y sin soltar el 2º click el valor y moverlo de lugar, ya sea a otro cajón o donde sea (drag & drop avanzado).
- Todos los valores pueden cambiar de nombre y se guarda al salir del submenú.

## 7. Arco solar y lunar
- El arco solar debe ser más grande.
- El arco lunar debe estar en efecto espejo debajo.
- En el centro, el valor del viento dentro de un círculo tipo brújula, indicando la dirección del viento.

## 8. Tipado y Robustez
- Tipado estricto en todos los endpoints (Pydantic).
- Sin parches ni bypasses, solo soluciones definitivas.
- Sin valores nulos ni undefined en la UI, siempre arrays vacíos o valores por defecto seguros.
- Sin redondeos innecesarios en datos críticos (como coordenadas).
- Sin duplicidad de valores en la UI.
- Sin errores de consola JavaScript.
- Factor Z y Vector #26 sincronizados y presentes en el JSON principal.
- Todos los endpoints deben devolver siempre JSON válido, nunca HTML de error.

## 9. Cajones sugeridos (ejemplo)
1. Termodinámica
2. Viento
3. Biometría
4. Precipitación
5. Radiación
6. Calidad del aire
7. Sensores virtuales
8. Predicciones
9. Alertas y riesgos
10. Indices misceláneos (último cajón, inferior derecha)

---

**Este archivo se irá ampliando con cada nueva instrucción sobre la UI.**
