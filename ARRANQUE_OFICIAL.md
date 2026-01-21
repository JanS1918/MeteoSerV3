# ARRANQUE OFICIAL DE METEOSER

Para iniciar MeteoSer de forma robusta y automática, ejecuta:

    arrancar_meteoser_autoreload.bat

Este script arranca el backend con autorecarga controlada. Cada vez que modifiques el código, el servidor se reiniciará solo y la web estará disponible tras unos segundos.

Para producción con servicio Windows (recomendado):

    scripts\register_service_nssm.ps1

Nota: el arranque directo fuera de los lanzadores oficiales queda bloqueado por seguridad.
