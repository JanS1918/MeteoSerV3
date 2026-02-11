Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$nssm = Join-Path $PSScriptRoot 'nssm\nssm-2.24\win64\nssm.exe'
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo '.venv\Scripts\python.exe'
$script = Join-Path $repo 'arrancar_meteoser.py'
$logs = Join-Path $repo 'logs'

Write-Host "Usando NSSM: $nssm"
Write-Host "Python: $python"
Write-Host "Script: $script"

if (-not (Test-Path $nssm)) { Write-Error "No se encontró nssm.exe en $nssm"; exit 1 }
if (-not (Test-Path $python)) { Write-Error "No se encontró python.exe en $python"; exit 1 }
if (-not (Test-Path $script)) { Write-Error "No se encontró $script"; exit 1 }

New-Item -Path $logs -ItemType Directory -Force | Out-Null

& $nssm install MeteoSer $python $script
& $nssm set MeteoSer AppDirectory $repo
& $nssm set MeteoSer AppStdout (Join-Path $logs 'servicio_out.log')
& $nssm set MeteoSer AppStderr (Join-Path $logs 'servicio_err.log')
& $nssm set MeteoSer Start SERVICE_AUTO_START

Write-Host "Intentando iniciar servicio MeteoSer..."
try { Start-Service MeteoSer -ErrorAction Stop; Write-Host 'Servicio iniciado.' } catch { Write-Host "Start-Service falló: $_. Exception.Message" }

Write-Host "Estado del servicio (sc query):"
sc.exe query MeteoSer | Write-Host

Write-Host 'Instalación NSSM completada.'
