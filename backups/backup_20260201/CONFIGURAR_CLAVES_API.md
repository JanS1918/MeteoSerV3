# Instrucciones para configurar variables de entorno de claves API

1. Abre el Panel de Variables de Entorno de Windows:
   - Pulsa Win + S y busca "variables de entorno".
   - Haz clic en "Editar las variables de entorno del sistema".
   - En la ventana, haz clic en "Variables de entorno...".

2. En "Variables de entorno del usuario" o "del sistema":
   - Pulsa "Nueva..." para agregar cada clave:

   - Nombre: OPENWEATHER_API_KEY
     Valor: TU_CLAVE_OPENWEATHER

   - Nombre: OPENROUTER_API_KEY
     Valor: TU_CLAVE_OPENROUTER

3. Acepta y reinicia tu sistema o cierra y abre la terminal para que los cambios tengan efecto.

4. Si usas un archivo .env, crea uno así (opcional):

OPENWEATHER_API_KEY=TU_CLAVE_OPENWEATHER
OPENROUTER_API_KEY=TU_CLAVE_OPENROUTER

Luego puedes usar una librería como python-dotenv para cargarlo automáticamente.
