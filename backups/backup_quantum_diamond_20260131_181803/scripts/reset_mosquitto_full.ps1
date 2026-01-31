# reset_mosquitto_full.ps1
$ErrorActionPreference = 'Stop'
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$mosq = 'C:\mosquitto'
$backup = "${mosq}_bak_$timestamp"
$nssm = Join-Path $PSScriptRoot 'tools\nssm\nssm-2.24\win64\nssm.exe'
$mosquitto_bin = 'C:\Program Files\Mosquitto\mosquitto.exe'
$mosquitto_passwd = 'C:\Program Files\Mosquitto\mosquitto_passwd.exe'

Write-Output "=== Inicio reset_mosquitto_full ($timestamp) ==="

# Stop and remove NSSM services if present
if (Test-Path $nssm) {
    try { & $nssm stop MeteoSerMosquitto 2>&1 | Write-Output } catch { Write-Output "nssm stop error: $_" }
    try { & $nssm stop MeteoSerBackend 2>&1 | Write-Output } catch { }
    Start-Sleep -Seconds 1
    try { & $nssm remove MeteoSerMosquitto confirm 2>&1 | Write-Output } catch { Write-Output "nssm remove may fail if not present: $_" }
    try { & $nssm remove MeteoSerBackend confirm 2>&1 | Write-Output } catch { }
} else {
    Write-Output "nssm not found at $nssm"
}

# Stop Windows mosquitto service if exists
try {
    $svc = Get-Service -Name mosquitto -ErrorAction SilentlyContinue
    if ($svc) { Stop-Service -Name mosquitto -Force -ErrorAction SilentlyContinue; Write-Output 'Stopped native mosquitto service' }
} catch { Write-Output "Stop-Service mosquitto error: $_" }

# Backup current installation if exists
if (Test-Path $mosq) {
    Write-Output "Backing up existing $mosq to $backup"
    try { Rename-Item -Path $mosq -NewName (Split-Path $backup -Leaf) -Force; Write-Output 'Backup rename complete' } catch { Write-Output "Rename error: $_" }
}

# Recreate directories
New-Item -ItemType Directory -Path $mosq -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $mosq 'conf') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $mosq 'data') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $mosq 'log') -Force | Out-Null

# Copy certs from repo if present
$repoCerts = Join-Path $PSScriptRoot 'tools\certs'
if (Test-Path $repoCerts) {
    Write-Output 'Copying certificates from repo tools/certs'
    Copy-Item -Path (Join-Path $repoCerts '*') -Destination (Join-Path $mosq 'conf\certs') -Recurse -Force -ErrorAction SilentlyContinue
} else { Write-Output 'No repo certs found; ensure you have TLS certs in C:\mosquitto\conf\certs' }

# Create minimal mosquitto.conf
$conf = @"
# MeteoSer minimal mosquitto.conf
listener 1883 127.0.0.1
listener 8883
protocol mqtt
persistence true
persistence_location C:/mosquitto/data/
log_dest file C:/mosquitto/log/mosquitto.log
allow_anonymous false
password_file C:/mosquitto/conf/passwordfile
# TLS
cafile C:/mosquitto/conf/certs/ca.crt
certfile C:/mosquitto/conf/certs/server.crt
keyfile C:/mosquitto/conf/certs/server.key
"@

$confPath = Join-Path $mosq 'conf\mosquitto.conf'
$conf | Out-File -FilePath $confPath -Encoding ascii

# Ensure permissions
& 'C:\Windows\System32\icacls.exe' $mosq /grant 'NT AUTHORITY\SYSTEM:(OI)(CI)F' /grant 'BUILTIN\Administradores:(OI)(CI)F' /grant 'BUILTIN\Usuarios:(OI)(CI)M' /T | Out-Null

# Create passwordfile using generated_password.txt if present
$pwdSource = Join-Path $PSScriptRoot 'C:\mosquitto\conf\generated_password.txt'
$repoPwd = Join-Path $PSScriptRoot 'tools\generated_password.txt'
$pwdTxt = $null
if (Test-Path $pwdSource) { $pwdTxt = Get-Content $pwdSource -ErrorAction SilentlyContinue } elseif (Test-Path $repoPwd) { $pwdTxt = Get-Content $repoPwd -ErrorAction SilentlyContinue }
if ($pwdTxt) {
    $pw = $pwdTxt.Trim()
    $pwfile = Join-Path $mosq 'conf\passwordfile'
    if (Test-Path $mosquitto_passwd) {
        & $mosquitto_passwd -b $pwfile meteoser $pw | Out-Null
        Write-Output 'Created passwordfile with mosquitto_passwd'
    } else {
        # fallback: create basic passwordfile using mosquitto_passwd format is complex; write warning
        Write-Output 'mosquitto_passwd not found; please create passwordfile manually or install mosquitto tools'
    }
} else {
    Write-Output 'No generated_password.txt found; create passwordfile manually at C:\mosquitto\conf\passwordfile'
}

# Install service via NSSM
if (Test-Path $nssm) {
    try { & $nssm install MeteoSerMosquitto "$mosquitto_bin" "-c $confPath" 2>&1 | Write-Output } catch { Write-Output "nssm install error: $_" }
    # configure stdout/stderr
    try { & $nssm set MeteoSerMosquitto AppStdout "C:/mosquitto/log/mosquitto_stdout.log" } catch {}
    try { & $nssm set MeteoSerMosquitto AppStderr "C:/mosquitto/log/mosquitto_stderr.log" } catch {}
    try { & $nssm set MeteoSerMosquitto AppRotateFiles 1 } catch {}
    Start-Sleep -Seconds 1
    try { & $nssm start MeteoSerMosquitto 2>&1 | Write-Output } catch { Write-Output "nssm start error: $_" }
} else { Write-Output 'nssm not available; please register service manually' }

Start-Sleep -Seconds 2
Write-Output '=== Comprobación final ==='
Get-Service -Name MeteoSerMosquitto -ErrorAction SilentlyContinue | Format-List
Test-NetConnection -ComputerName localhost -Port 1883 | Format-List
Test-NetConnection -ComputerName localhost -Port 8883 | Format-List

Write-Output "=== reset_mosquitto_full finalizado ==="
