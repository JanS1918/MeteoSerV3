$token = '8324459852:AAHpj-VQBQOS1HU0UULXrvyY68nTA3YrMKs'
try {
    $r = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getUpdates" -Method Get -TimeoutSec 10
    if ($r.ok -and $r.result.Count -gt 0) {
        $last = $r.result[-1]
        if ($last.message) { $id = $last.message.chat.id; Write-Host "FOUND_CHAT_ID:$id" }
        elseif ($last.callback_query) { $id = $last.callback_query.message.chat.id; Write-Host "FOUND_CHAT_ID:$id" }
        else { Write-Host "NO_CHAT_IN_LAST_UPDATE" }
    } else { Write-Host "NO_UPDATES" }
} catch {
    Write-Host "GETUPDATES_FAILED: $($_.Exception.Message)"
}
