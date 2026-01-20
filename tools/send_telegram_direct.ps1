param([string]$Token)
if (-not $Token) { Write-Host 'MISSING_TOKEN'; exit 1 }
try {
    $r = Invoke-RestMethod -Uri "https://api.telegram.org/bot$Token/getUpdates" -Method Get -TimeoutSec 10
} catch {
    Write-Host "GETUPDATES_FAILED: $($_.Exception.Message)"
    exit 1
}
if ($r.ok -and $r.result -and $r.result.Count -gt 0) {
    $chat = $null
    foreach ($u in $r.result) {
        if ($u.message) { $chat = $u.message.chat.id; break }
        if ($u.callback_query) { $chat = $u.callback_query.message.chat.id; break }
    }
    if (-not $chat) { Write-Host 'NO_CHAT_IN_UPDATES'; exit 1 }
    try {
        Invoke-RestMethod -Uri "https://api.telegram.org/bot$Token/sendMessage" -Method Post -Body @{ chat_id = $chat; text = '[MeteoSer] Prueba automática desde MeteoSer' } -TimeoutSec 10 | Out-Null
        Write-Host "SENT_TO:$chat"
    } catch {
        Write-Host "SEND_FAILED: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host 'NO_UPDATES'
    exit 1
}
