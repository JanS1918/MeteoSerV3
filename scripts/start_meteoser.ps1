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
$env:METEOSER_OFFICIAL_START='1'
$env:METEOSER_REQUIRE_OFFICIAL='1'
$env:METEOSER_OFFICIAL_CALLER='start_meteoser.ps1'
Set-Location -Path "C:\Users\kioko\Desktop\MeteoSerV3"
"Starting MeteoSer (uvicorn) in background..."
$launcher = "C:\Users\kioko\Desktop\MeteoSerV3\arrancar_meteoser.py"
Start-Process -FilePath "C:\Users\kioko\Desktop\MeteoSerV3\.venv\Scripts\python.exe" -ArgumentList $launcher -WindowStyle Hidden -WorkingDirectory "C:\Users\kioko\Desktop\MeteoSerV3"
Write-Host "MeteoSer started (background)."
