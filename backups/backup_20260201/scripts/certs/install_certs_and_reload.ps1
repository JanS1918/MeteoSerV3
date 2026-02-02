# Copia los certificados de scripts/certs a C:\mosquitto\conf\certs, fija ACLs y reinicia Mosquitto (NSSM)
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Error "Ejecuta este script en PowerShell como Administrador."
  exit 1
}

$src = Join-Path $PSScriptRoot 'certs'
$dst = 'C:\mosquitto\conf\certs'
New-Item -Path $dst -ItemType Directory -Force | Out-Null

Get-ChildItem -Path $src -Filter *.crt -File | ForEach-Object { Copy-Item -Path $_.FullName -Destination $dst -Force }
Get-ChildItem -Path $src -Filter *.key -File | ForEach-Object { Copy-Item -Path $_.FullName -Destination $dst -Force }

& 'C:\Windows\System32\icacls.exe' $dst /grant 'NT AUTHORITY\SYSTEM:(OI)(CI)F' /grant 'BUILTIN\Administradores:(OI)(CI)F' /grant 'BUILTIN\Usuarios:(OI)(CI)M' /T

Write-Output "Certificados copiados a $dst"

# Actualizar mosquitto.conf (asegurar que apunta a los archivos correctos)
$conf = 'C:\mosquitto\conf\mosquitto.conf'
if (Test-Path $conf) {
  (Get-Content $conf) | ForEach-Object {
    $_ -replace '^(\s*cafile\s+).*', "cafile C:/mosquitto/conf/certs/ca.crt" -replace '^(\s*certfile\s+).*', "certfile C:/mosquitto/conf/certs/server.crt" -replace '^(\s*keyfile\s+).*', "keyfile C:/mosquitto/conf/certs/server.key"
  } | Set-Content $conf
  Write-Output "mosquitto.conf actualizado (cafile/certfile/keyfile)."
} else { Write-Output "mosquitto.conf no encontrado en $conf" }

# Reiniciar NSSM service
& '.\tools\nssm\nssm-2.24\win64\nssm.exe' restart MeteoSerMosquitto
Start-Sleep -Seconds 2
Get-Service -Name MeteoSerMosquitto | Format-List

Write-Output "Hecho. Revisa logs en C:\mosquitto\log"
