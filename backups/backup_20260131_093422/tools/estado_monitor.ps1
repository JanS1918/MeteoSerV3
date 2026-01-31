param(
    [string]$Url = 'http://127.0.0.1:8080/estado',
    [int]$IntervalSeconds = 60,
    [int]$TimeoutSeconds = 10,
    [string]$LogFile = "$PSScriptRoot\estado_monitor.log",
    [switch]$Once
)

function Write-Log {
    param([string]$Line)
    $Line | Out-File -FilePath $LogFile -Append -Encoding utf8
}

Write-Host "[$(Get-Date -Format o)] estado_monitor iniciado contra $Url"

while ($true) {
    $timestamp = Get-Date -Format o
    try {
        $response = Invoke-RestMethod -Uri $Url -TimeoutSec $TimeoutSeconds
        $summary = if ($response.recomendacion) {
            $response.recomendacion.estado -replace '\s{2,}', ' '
        } else {
            'sin recomendacion'
        }
        $message = "$timestamp OK | recom: $summary"
        Write-Host $message
        Write-Log $message
    } catch {
        $message = "$timestamp ERROR | $_"
        Write-Host $message -ForegroundColor Red
        Write-Log $message
    }

    if ($Once) {
        break
    }

    Start-Sleep -Seconds $IntervalSeconds
}
