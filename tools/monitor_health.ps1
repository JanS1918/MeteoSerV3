param(
    [string]$BaseUrl = 'http://127.0.0.1:8080',
    [int]$LinesToCheck = 40
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root\..\

function Show-Panel {
    param($title, $body)
    Write-Host "$title" -ForegroundColor Cyan
    if ($body) { Write-Host $body -ForegroundColor Gray }
}

# Telegram helper: set these env vars or edit below
$Env:TELEGRAM_BOT_TOKEN = $Env:TELEGRAM_BOT_TOKEN
$Env:TELEGRAM_CHAT_ID = $Env:TELEGRAM_CHAT_ID

function Send-Telegram {
    param($text)
    if (-not $Env:TELEGRAM_BOT_TOKEN -or -not $Env:TELEGRAM_CHAT_ID) { return }
    try {
        $uri = "https://api.telegram.org/bot$($Env:TELEGRAM_BOT_TOKEN)/sendMessage"
        $body = @{ chat_id = $Env:TELEGRAM_CHAT_ID; text = $text }
        Invoke-RestMethod -Uri $uri -Method Post -Body $body -TimeoutSec 10 | Out-Null
    } catch {
        Write-Host "[WARN] Falló envío Telegram: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Wrapper: enviar alertas por Telegram (único canal)
function Send-Alert {
    param($text)
    Send-Telegram $text
}

$healthUrl = "$BaseUrl/estado"
try {
    $state = Invoke-RestMethod -Uri $healthUrl -UseBasicParsing -TimeoutSec 10
    $sensorCount = 0
    if ($state.sensores) { $sensorCount = ($state.sensores | Measure-Object).Count }
    Show-Panel "[OK] API responde" "Status: $sensorCount sensores listados."
} catch {
    Show-Panel "[ERROR] /estado" $_.Exception.Message
    Send-Alert "[MeteoSer] ERROR /estado: $($_.Exception.Message)"
    exit 2
}

$stdoutPath = Join-Path (Get-Location) 'logs\servicio_out.log'
if (-not (Test-Path $stdoutPath)) {
    $stdoutPath = Join-Path (Get-Location) 'logs\service_stdout.log'
}
if (-not (Test-Path $stdoutPath)) {
    Show-Panel "Logs" "No existe log de stdout"
    exit 0
}

try {
    # Intento normal de lectura
    $recentLines = Get-Content -Path $stdoutPath -Encoding UTF8 -Tail $LinesToCheck -ErrorAction Stop
} catch {
    # Fallback: abrir el fichero permitiendo lectura compartida (evita errores de sharing)
    try {
        $fs = [System.IO.File]::Open($stdoutPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8)
        $all = $sr.ReadToEnd()
        $sr.Close()
        $fs.Close()
        $lines = $all -split "\r?\n"
        $recentLines = if ($lines.Length -le $LinesToCheck) { $lines } else { $lines[-$LinesToCheck..-1] }
    } catch {
        $recentLines = @()
    }
}
$pattern = 'HTTP/1\.1"\s+(5\d\d)'
$errors = $recentLines | Select-String -Pattern $pattern
if ($errors) {
    $msg = "[MeteoSer] ALERTA: $($errors.Count) respuestas 5xx en las últimas $LinesToCheck líneas. Último: $($errors[-1].Line)"
    Show-Panel "[ALERTA] $($errors.Count) respuestas 5xx en las últimas $LinesToCheck líneas" "Último: $($errors[-1].Line)"
    Send-Alert $msg
    exit 3
} else {
    Show-Panel "No se detectaron 5xx recientes" "Revisadas $LinesToCheck líneas de logs."
}

if (Test-Path (Join-Path (Get-Location) 'logs\servicio_err.log') -or Test-Path (Join-Path (Get-Location) 'logs\service_stderr.log')) {
    try {
        $stderrPath = Join-Path (Get-Location) 'logs\servicio_err.log'
        if (-not (Test-Path $stderrPath)) {
            $stderrPath = Join-Path (Get-Location) 'logs\service_stderr.log'
        }
        $stderrLines = Get-Content -Path $stderrPath -Encoding UTF8 -Tail 30 -ErrorAction Stop
    } catch {
        try {
            $fs2 = [System.IO.File]::Open($stderrPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
            $sr2 = New-Object System.IO.StreamReader($fs2, [System.Text.Encoding]::UTF8)
            $all2 = $sr2.ReadToEnd()
            $sr2.Close()
            $fs2.Close()
            $lines2 = $all2 -split "\r?\n"
            $stderrLines = if ($lines2.Length -le 30) { $lines2 } else { $lines2[-30..-1] }
        } catch {
            $stderrLines = @()
        }
    }
    if ($stderrLines) {
        Show-Panel "service_stderr.log (últimas líneas)" "$(($stderrLines -join "`n"))"
    }
}

# Alertas específicas MQTT
if (Test-Path (Join-Path (Get-Location) 'logs\servicio_err.log')) {
    try {
        $mqttLines = Get-Content -Path (Join-Path (Get-Location) 'logs\servicio_err.log') -Encoding UTF8 -Tail 200 -ErrorAction Stop
        $mqttErrors = $mqttLines | Select-String -Pattern 'MQTT (error conexi[oó]n|no disponible)'
        if ($mqttErrors) {
            $last = $mqttErrors[-1].Line
            Show-Panel "[ALERTA] MQTT" "Último: $last"
            Send-Alert "[MeteoSer] ALERTA MQTT: $last"
        }
    } catch {
        # ignore
    }
}