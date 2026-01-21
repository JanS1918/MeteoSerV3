$ErrorActionPreference = 'Stop'

$svcName = 'MeteoSerBackend'
$repoRoot = 'C:\Users\kioko\Desktop\MeteoSerV3'
$logDir = Join-Path $repoRoot 'logs'
$logPath = Join-Path $logDir 'watchdog.log'

if (-not (Test-Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory -Force | Out-Null
}

function Write-Log([string]$msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $logPath -Value $line
}

try {
    $svc = Get-CimInstance Win32_Service -Filter "Name='$svcName'"
    if (-not $svc) {
        Write-Log "[WARN] Servicio $svcName no encontrado."
        exit 0
    }

    if ($svc.State -ne 'Running') {
        Write-Log "[INFO] Servicio $svcName en estado $($svc.State). Iniciando..."
        Start-Service $svcName
        Start-Sleep -Seconds 3
        $svc = Get-CimInstance Win32_Service -Filter "Name='$svcName'"
    }

    $keepPid = $svc.ProcessId
    if ($keepPid -and $keepPid -gt 0) {
        $procs = Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -and ($_.CommandLine -match 'main_asgi|uvicorn') -and ($_.CommandLine -match [regex]::Escape($repoRoot))
        }
        foreach ($p in $procs) {
            if ($p.ProcessId -ne $keepPid) {
                Write-Log "[WARN] Proceso duplicado detectado PID=$($p.ProcessId). Finalizando."
                try { Stop-Process -Id $p.ProcessId -Force } catch { }
            }
        }
    } else {
        Write-Log "[WARN] Servicio $svcName sin PID activo."
    }
}
catch {
    Write-Log "[ERROR] Watchdog fallo: $($_.Exception.Message)"
}
