<#
Auto-fix script: recrea C:\mosquitto\conf\passwordfile de forma atómica,
fija ACLs y reinicia el servicio Mosquitto gestionado por NSSM.

USO: Ejecutar en una PowerShell 64-bit con privilegios de Administrador:
  Open PowerShell (Run as Administrator) y ejecutar:
    .\scripts\auto_fix_mosquitto_password.ps1

El script intentará usar mosquitto_passwd.exe en "C:\Program Files\Mosquitto".
Si falla, el script no intentará crear hashes por su cuenta: mostrará instrucciones.
#>

$logDir = Join-Path $PSScriptRoot '..\logs' | Resolve-Path -ErrorAction SilentlyContinue
if (-not $logDir) { $logDir = Join-Path $PSScriptRoot '..\logs'; New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$time = Get-Date -Format 'yyyyMMdd_HHmmss'
$log = Join-Path $logDir "auto_fix_mosquitto_password_$time.log"

function Log { param($m) $m | Out-File -FilePath $log -Append -Encoding utf8; Write-Output $m }

Log "=== auto_fix_mosquitto_password started: $(Get-Date) ==="

# 1) comprobar elevación
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Log "ERROR: Ejecuta esta script en PowerShell como Administrador."; exit 1
}

# 2) rutas y binarios
$nssm = Join-Path $PSScriptRoot '..\tools\nssm\nssm-2.24\win64\nssm.exe' -Resolve
$mosq_passwd = 'C:\Program Files\Mosquitto\mosquitto_passwd.exe'
$confDir = 'C:\mosquitto\conf'
$pwGenerated = Join-Path $confDir 'generated_password.txt'
$pwFile = Join-Path $confDir 'passwordfile'
$pwTmp = Join-Path $confDir 'passwordfile.tmp'

Log "nssm: $nssm"
Log "mosquitto_passwd: $mosq_passwd"
Log "confDir: $confDir"

# 3) stop service & processes
try {
  & $nssm stop MeteoSerMosquitto 2>&1 | ForEach-Object { Log $_ }
} catch { Log "nssm stop error: $_" }
Get-Process -Name mosquitto -ErrorAction SilentlyContinue | ForEach-Object { Log "Stopping process $_.Id"; Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }

# 4) asegurar carpeta
New-Item -ItemType Directory -Path $confDir -Force | Out-Null

# 5) obtener o generar password
if (Test-Path $pwGenerated) {
  $pw = (Get-Content $pwGenerated -Raw).Trim()
  Log "Using existing generated_password.txt"
} else {
  $bytes = New-Object byte[] 18; [Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
  $pw = [Convert]::ToBase64String($bytes)
  $pw | Out-File -FilePath $pwGenerated -Encoding ascii
  Log "Generated and stored password to generated_password.txt"
}

# 6) crear .tmp con mosquitto_passwd
if (Test-Path $mosq_passwd) {
  try {
    if (Test-Path $pwTmp) { Remove-Item $pwTmp -Force -ErrorAction SilentlyContinue }
    & $mosq_passwd -b $pwTmp meteoser $pw 2>&1 | ForEach-Object { Log $_ }
  } catch {
    Log "mosquitto_passwd execution failed: $_"
  }
  if (-not (Test-Path $pwTmp)) {
    Log "ERROR: mosquitto_passwd no creó $pwTmp. Revisa permisos o ejecuta mosquitto_passwd manualmente."
    Log "Sugerencia: copia mosquitto_passwd.exe a 'C:\Program Files\Mosquitto' si falta o ejecuta desde CMD."
    Log "Script abortado."; exit 1
  }
} else {
  Log "ERROR: mosquitto_passwd.exe no encontrado en: $mosq_passwd"; exit 1
}

# 7) mover .tmp a passwordfile de forma atómica y ajustar ACLs
try {
  Move-Item -Path $pwTmp -Destination $pwFile -Force
  Log "Moved $pwTmp -> $pwFile"
} catch { Log "Move-Item failed: $_"; exit 1 }

& 'C:\Windows\System32\icacls.exe' $pwFile /grant 'NT AUTHORITY\SYSTEM:F' /grant 'BUILTIN\Administradores:F' /grant 'BUILTIN\Usuarios:M' 2>&1 | ForEach-Object { Log $_ }
& 'C:\Windows\System32\icacls.exe' 'C:\mosquitto' /grant 'NT AUTHORITY\SYSTEM:(OI)(CI)F' /grant 'BUILTIN\Administradores:(OI)(CI)F' /grant 'BUILTIN\Usuarios:(OI)(CI)M' /T 2>&1 | ForEach-Object { Log $_ }

# 8) iniciar servicio y comprobar
try {
  & $nssm start MeteoSerMosquitto 2>&1 | ForEach-Object { Log $_ }
} catch { Log "nssm start error: $_" }
Start-Sleep -Seconds 2
Get-Service -Name MeteoSerMosquitto | Format-List | Out-String | ForEach-Object { Log $_ }

try { Test-NetConnection -ComputerName localhost -Port 1883 | Format-List | Out-String | ForEach-Object { Log $_ } } catch { }
try { Test-NetConnection -ComputerName localhost -Port 8883 | Format-List | Out-String | ForEach-Object { Log $_ } } catch { }

if (Test-Path 'C:\mosquitto\log\mosquitto_stdout.log') { Get-Content 'C:\mosquitto\log\mosquitto_stdout.log' -Tail 200 | ForEach-Object { Log $_ } } else { Log 'stdout.log missing' }
if (Test-Path 'C:\mosquitto\log\mosquitto.log') { Get-Content 'C:\mosquitto\log\mosquitto.log' -Tail 200 | ForEach-Object { Log $_ } } else { Log 'mosquitto.log missing' }

Log "=== auto_fix_mosquitto_password finished: $(Get-Date) ==="

Write-Output "Script finished. Revisa el log: $log"
