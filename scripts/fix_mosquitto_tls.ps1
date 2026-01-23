$ErrorActionPreference = 'Stop'
$confPath = 'C:\mosquitto\conf\mosquitto.conf'
if (-not (Test-Path $confPath)) {
    Write-Error "No se encontró $confPath"
    exit 1
}

$backup = "$confPath.bak.$(Get-Date -Format 'yyyyMMddHHmmss')"
Copy-Item -Path $confPath -Destination $backup -Force

$conf = Get-Content $confPath -Raw
$conf = $conf -replace 'cafile\s+.*', 'cafile C:/mosquitto/conf/certs/ca.cert.pem'
$conf = $conf -replace 'certfile\s+.*', 'certfile C:/mosquitto/conf/certs/server.cert.pem'
$conf = $conf -replace 'keyfile\s+.*', 'keyfile C:/mosquitto/conf/certs/server.key.pem'

Set-Content -Path $confPath -Value $conf -Encoding ascii

Write-Output "Actualizado mosquitto.conf (backup: $backup)"
