Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$nssm = Join-Path $PSScriptRoot 'nssm\nssm-2.24\win64\nssm.exe'
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo '.venv\Scripts\python.exe'
$script = Join-Path $repo 'arrancar_meteoser.py'
$logs = Join-Path $repo 'logs'
$svcName = 'MeteoSerBackend'

Write-Host "Usando NSSM: $nssm"
Write-Host "Python: $python"
Write-Host "Script: $script"

if (-not (Test-Path $nssm)) { Write-Error "No se encontró nssm.exe en $nssm"; exit 1 }
if (-not (Test-Path $python)) { Write-Error "No se encontró python.exe en $python"; exit 1 }
if (-not (Test-Path $script)) { Write-Error "No se encontró $script"; exit 1 }

New-Item -Path $logs -ItemType Directory -Force | Out-Null

& $nssm install $svcName $python $script
& $nssm set $svcName AppDirectory $repo
& $nssm set $svcName AppStdout (Join-Path $logs 'servicio_out.log')
& $nssm set $svcName AppStderr (Join-Path $logs 'servicio_err.log')
& $nssm set $svcName Start SERVICE_AUTO_START
& $nssm set $svcName AppRestartDelay 60000
$pwPath = 'C:\mosquitto\conf\generated_password.txt'
$pw = ''
if (Test-Path $pwPath) {
	$pw = (Get-Content $pwPath -Raw).Trim()
}
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
	'METEOSER_HOST=0.0.0.0',
	'METEOSER_PORT=8080'
)
& $nssm set $svcName AppEnvironmentExtra ($envs -join "`r`n")

Write-Host "Intentando iniciar servicio $svcName..."
try { Start-Service $svcName -ErrorAction Stop; Write-Host 'Servicio iniciado.' } catch { Write-Host "Start-Service falló: $_. Exception.Message" }

Write-Host "Estado del servicio (sc query):"
sc.exe query $svcName | Write-Host

Write-Host 'Instalación NSSM completada.'
