# Test de envío por Telegram para MeteoSer
$bot = [System.Environment]::GetEnvironmentVariable('TELEGRAM_BOT_TOKEN')
$chat = [System.Environment]::GetEnvironmentVariable('TELEGRAM_CHAT_ID')
if (-not $bot -or -not $chat) {
    if (-not $bot) { Write-Host "TELEGRAM_BOT_TOKEN: UNSET" }
    if (-not $chat) { Write-Host "TELEGRAM_CHAT_ID: UNSET" }
    Write-Host "Variables faltantes; define TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID y vuelve a ejecutar."
    exit 1
}
try {
    $uri = "https://api.telegram.org/bot$bot/sendMessage"
    $body = @{ chat_id = $chat; text = '[MeteoSer] Prueba rápida: este mensaje confirma que las alertas por Telegram funcionan.' }
    Invoke-RestMethod -Uri $uri -Method Post -Body $body -TimeoutSec 10 | Out-Null
    Write-Host 'TELEGRAM: Mensaje enviado correctamente.'
} catch {
    Write-Host "TELEGRAM: Falló envío: $($_.Exception.Message)" -ForegroundColor Yellow
}
