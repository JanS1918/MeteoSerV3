# Limpieza segura del árbol

- `archive/demo/`: demo no operativo movido para no incluirlo en el despliegue principal.
- `archive/tests/`: tests placeholder y bytes compilados movidos para evitar ruido en `pytest`.
- `archive/disabled_bats/`: lanzadores peligrosos deshabilitados. Mantenemos la evidencia por si se necesita restaurarlos.
- `archive/logs/`: copias de los logs actuales para auditoría antes de truncarlos.

Cada carpeta está ignorada en `.gitignore` y puede purgarse manualmente cuando ya no haga falta. Para restaurar algo, basta copiar el fichero de `archive/` de nuevo al lugar original y eliminar la entrada correspondiente del archivo.