$ErrorActionPreference = 'Stop'

$svcName = 'MeteoSerMosquitto'
$nssm = 'C:\Users\kioko\Desktop\MeteoSerV3\tools\nssm\nssm-2.24\win64\nssm.exe'
$exe = 'C:\Program Files\Mosquitto\mosquitto.exe'
$config = 'C:\mosquitto\conf\mosquitto.conf'
$logDir = 'C:\mosquitto\log'

if (-not (Test-Path $nssm)) {
    throw "NSSM no encontrado en $nssm"
}

New-Item -Path $logDir -ItemType Directory -Force | Out-Null

if (Get-Service -Name $svcName -ErrorAction SilentlyContinue) {
    & $nssm stop $svcName | Out-Null
    & $nssm remove $svcName confirm | Out-Null
}

& $nssm install $svcName $exe "-c $config" | Out-Null
& $nssm set $svcName AppDirectory 'C:\Program Files\Mosquitto' | Out-Null
& $nssm set $svcName AppStdout (Join-Path $logDir 'mosquitto_stdout.log') | Out-Null
& $nssm set $svcName AppStderr (Join-Path $logDir 'mosquitto_stderr.log') | Out-Null
& $nssm set $svcName AppRestartDelay 60000 | Out-Null
& $nssm set $svcName Start SERVICE_AUTO_START | Out-Null

Start-Service $svcName
Get-Service -Name $svcName
