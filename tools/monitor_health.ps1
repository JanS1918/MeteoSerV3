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

$healthUrl = "$BaseUrl/estado"
try {
    $state = Invoke-RestMethod -Uri $healthUrl -UseBasicParsing -TimeoutSec 10
    $sensorCount = 0
    if ($state.sensores) { $sensorCount = ($state.sensores | Measure-Object).Count }
    Show-Panel "[OK] API responde" "Status: $sensorCount sensores listados."
} catch {
    Show-Panel "[ERROR] /estado" $_.Exception.Message
    exit 2
}

$stdoutPath = Join-Path (Get-Location) 'logs\service_stdout.log'
if (-not (Test-Path $stdoutPath)) {
    Show-Panel "Logs" "No existe $stdoutPath"
    exit 0
}

try {
    $recentLines = Get-Content -Path $stdoutPath -Encoding UTF8 -Tail $LinesToCheck -ErrorAction SilentlyContinue
} catch {
    $recentLines = @()
}
$pattern = 'HTTP/1\.1"\s+(5\d\d)'
$errors = $recentLines | Select-String -Pattern $pattern
if ($errors) {
    Show-Panel "[ALERTA] $($errors.Count) respuestas 5xx en las últimas $LinesToCheck líneas" "Último: $($errors[-1].Line)"
    exit 3
} else {
    Show-Panel "No se detectaron 5xx recientes" "Revisadas $LinesToCheck líneas de logs."
}

if (Test-Path (Join-Path (Get-Location) 'logs\service_stderr.log')) {
    $stderrLines = Get-Content -Path (Join-Path (Get-Location) 'logs\service_stderr.log') -Tail 30 -ErrorAction SilentlyContinue
    if ($stderrLines) {
        Show-Panel "service_stderr.log (últimas líneas)" "$(($stderrLines -join "`n"))"
    }
}