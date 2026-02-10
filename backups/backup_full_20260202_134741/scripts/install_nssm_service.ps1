$ErrorActionPreference = 'Stop'

$svcName = 'MeteoSerBackend'
$python = 'C:\Users\kioko\Desktop\MeteoSerV3\.venv\Scripts\python.exe'
$work = 'C:\Users\kioko\Desktop\MeteoSerV3'
$logDir = Join-Path $work 'logs'

$envs = @(
    'METEOSER_MQTT_ENABLED=1',
    'METEOSER_MQTT_HOST=localhost',
    'METEOSER_MQTT_PORT=8883',
    'METEOSER_MQTT_TLS=1',
    'METEOSER_MQTT_TLS_CA=C:/mosquitto/conf/certs/ca.cert.pem',
    'METEOSER_MQTT_TLS_INSECURE=0',
    'METEOSER_MQTT_USER=meteoser',
    ('METEOSER_MQTT_PASS=' + (Get-Content 'C:\mosquitto\conf\generated_password.txt')),
    'METEOSER_DEBUG=1'
)

$tempZip = Join-Path $env:TEMP 'nssm.zip'
Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile $tempZip -UseBasicParsing
Expand-Archive -Path $tempZip -DestinationPath 'C:\nssm' -Force

$nssm = 'C:\nssm\win64\nssm.exe'
if (-not (Test-Path $nssm)) {
    throw "No se encontró NSSM en $nssm"
}

if (Get-Service -Name $svcName -ErrorAction SilentlyContinue) {
    & $nssm stop $svcName | Out-Null
    & $nssm remove $svcName confirm | Out-Null
}

& $nssm install $svcName $python "-m uvicorn main_asgi:app --host 127.0.0.1 --port 8080" | Out-Null
& $nssm set $svcName AppDirectory $work | Out-Null
& $nssm set $svcName AppEnvironmentExtra ($envs -join "`r`n") | Out-Null

New-Item -Path $logDir -ItemType Directory -Force | Out-Null
& $nssm set $svcName AppStdout (Join-Path $logDir 'service_stdout.log') | Out-Null
& $nssm set $svcName AppStderr (Join-Path $logDir 'service_stderr.log') | Out-Null
& $nssm set $svcName Start SERVICE_AUTO_START | Out-Null
& $nssm set $svcName AppRestartDelay 60000 | Out-Null

Start-Service $svcName
Get-Service -Name $svcName
