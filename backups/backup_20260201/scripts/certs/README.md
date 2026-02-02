Instrucciones y archivos de certificados generados (CA y servidor).

Pasos para instalar (PowerShell elevado):

1. Copiar los archivos de esta carpeta a C:\mosquitto\conf\certs:
   - ca.crt
   - server.crt
   - server.key

2. Ejecutar el script `install_certs_and_reload.ps1` desde la raíz del proyecto:
   ```powershell
   Set-Location 'C:\Users\kioko\Desktop\MeteoSerV3'
   .\scripts\certs\install_certs_and_reload.ps1
   ```

3. Comprueba los logs en C:\mosquitto\log y el estado del servicio.

NOTA: Estos certificados son autofirmados para uso local y pruebas. No uses en producción.
