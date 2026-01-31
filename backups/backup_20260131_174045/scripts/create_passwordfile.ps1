$ErrorActionPreference='Stop'
$confDir = 'C:\mosquitto\conf'
if (-not (Test-Path $confDir)) { New-Item -ItemType Directory -Path $confDir -Force | Out-Null }
# Generate a random 24-char password (base64 of 18 bytes)
$bytes = New-Object byte[] 18
[System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
$pw = [Convert]::ToBase64String($bytes)
$pwFile = Join-Path $confDir 'generated_password.txt'
Set-Content -Path $pwFile -Value $pw -Encoding ascii
Write-Output "Wrote generated password to $pwFile"

$mosquitto_passwd = 'C:\Program Files\Mosquitto\mosquitto_passwd.exe'
$pwfile = Join-Path $confDir 'passwordfile'
if (Test-Path $mosquitto_passwd) {
    & "$mosquitto_passwd" -b $pwfile meteoser $pw 2>&1 | Write-Output
    Write-Output "Created passwordfile at $pwfile"
} else {
    Write-Output "mosquitto_passwd not found at $mosquitto_passwd. Attempting to create simple passwordfile entry."
    # Create bcrypt style? We'll fallback to adding plain text (mosquitto won't accept plain text). Notify user.
    Add-Content -Path $pwfile -Value "# Passwordfile must be created with mosquitto_passwd; mosquitto_passwd.exe not found."
}

# Ensure permissions on conf and log
& 'C:\Windows\System32\icacls.exe' 'C:\mosquitto' /grant 'NT AUTHORITY\SYSTEM:(OI)(CI)F' /grant 'BUILTIN\Administradores:(OI)(CI)F' /grant 'BUILTIN\Usuarios:(OI)(CI)M' /T | Out-Null

# Restart service via NSSM if available
$nssm = 'C:\Users\kioko\Desktop\MeteoSerV3\tools\nssm\nssm-2.24\win64\nssm.exe'
if (Test-Path $nssm) {
    try { & $nssm restart MeteoSerMosquitto 2>&1 | Write-Output } catch { Write-Output "nssm restart error: $_" }
    Start-Sleep -Seconds 2
    Get-Service -Name MeteoSerMosquitto | Format-List | Write-Output
} else { Write-Output 'NSSM not found; start Mosquitto manually to test.' }

Write-Output "Generated password: $pw (also saved to $pwFile)"
Read-Host 'Pulsa Enter para cerrar esta ventana'