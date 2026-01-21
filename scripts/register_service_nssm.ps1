$ErrorActionPreference = 'Stop'

$svcName = 'MeteoSerBackend'
$nssm = 'C:\Users\kioko\Desktop\MeteoSerV3\tools\nssm\nssm-2.24\win64\nssm.exe'
$python = 'C:\Users\kioko\Desktop\MeteoSerV3\.venv\Scripts\python.exe'
$work = 'C:\Users\kioko\Desktop\MeteoSerV3'
$logDir = Join-Path $work 'logs'

if (-not (Test-Path $nssm)) {
    throw "No se encontró NSSM en $nssm"
}

$pwPath = 'C:\mosquitto\conf\generated_password.txt'
$pw = ''
if (Test-Path $pwPath) { $pw = (Get-Content $pwPath -Raw).Trim() }
$envs = @(
    'METEOSER_MQTT_ENABLED=1',
    'METEOSER_MQTT_HOST=localhost',
    'METEOSER_MQTT_PORT=8883',
    'METEOSER_MQTT_TLS=1',
    'METEOSER_MQTT_TLS_CA=C:/mosquitto/conf/certs/ca.cert.pem',
    'METEOSER_MQTT_TLS_INSECURE=0',
    'METEOSER_MQTT_USER=meteoser',
    ("METEOSER_MQTT_PASS=$pw"),
    'METEOSER_DEBUG=0',
    'METEOSER_OFFICIAL_START=1',
    'METEOSER_REQUIRE_OFFICIAL=1',
    'METEOSER_OFFICIAL_SOURCE=service',
    'METEOSER_HOST=0.0.0.0',
    'METEOSER_PORT=8080'
)

if (Get-Service -Name $svcName -ErrorAction SilentlyContinue) {
    & $nssm stop $svcName | Out-Null
    $launcher = Join-Path $work 'arrancar_meteoser.py'
    & $nssm set $svcName Application $python | Out-Null
    & $nssm set $svcName AppParameters $launcher | Out-Null
} else {
    $launcher = Join-Path $work 'arrancar_meteoser.py'
    & $nssm install $svcName $python $launcher | Out-Null
}
& $nssm set $svcName AppDirectory $work | Out-Null
& $nssm set $svcName AppEnvironmentExtra ($envs -join "`r`n") | Out-Null

New-Item -Path $logDir -ItemType Directory -Force | Out-Null
& $nssm set $svcName AppStdout (Join-Path $logDir 'service_stdout.log') | Out-Null
& $nssm set $svcName AppStderr (Join-Path $logDir 'service_stderr.log') | Out-Null
& $nssm set $svcName Start SERVICE_AUTO_START | Out-Null
& $nssm set $svcName AppRestartDelay 60000 | Out-Null

Start-Service $svcName
Get-Service -Name $svcName
