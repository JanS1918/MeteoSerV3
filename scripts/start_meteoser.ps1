# Start MeteoSer in background with MQTT env
$env:METEOSER_MQTT_ENABLED='1'
$env:METEOSER_MQTT_HOST='localhost'
$env:METEOSER_MQTT_PORT='8883'
$env:METEOSER_MQTT_TLS='1'
$env:METEOSER_MQTT_TLS_CA='C:\mosquitto\conf\certs\ca.cert.pem'
$env:METEOSER_MQTT_TLS_INSECURE='0'
$env:METEOSER_MQTT_USER='meteoser'
$env:METEOSER_MQTT_PASS=(Get-Content 'C:\mosquitto\conf\generated_password.txt')
$env:METEOSER_DEBUG='1'
Set-Location -Path "C:\Users\kioko\Desktop\MeteoSerV3"
"Starting MeteoSer (uvicorn) in background..."
Start-Process -FilePath "C:\Users\kioko\Desktop\MeteoSerV3\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn main_asgi:app --host 127.0.0.1 --port 8080" -WindowStyle Hidden -WorkingDirectory "C:\Users\kioko\Desktop\MeteoSerV3"
Write-Host "MeteoSer started (background)."
