Param(
    [string]$LogRotateScript = "$PSScriptRoot\logrotate.ps1",
    [string]$HealthScript = "$PSScriptRoot\monitor_health.ps1",
    [string]$WatchdogScript = "$PSScriptRoot\official_watchdog.ps1",
    [string]$LogRotateTaskName = "MeteoSer LogRotate",
    [string]$HealthTaskName = "MeteoSer Health Monitor",
    [string]$WatchdogTaskName = "MeteoSer Official Watchdog",
    [string]$LogRotateTime = "02:00"
)

$logRotatePath = (Resolve-Path $LogRotateScript).Path
$healthPath = (Resolve-Path $HealthScript).Path
$watchdogPath = (Resolve-Path $WatchdogScript).Path

$logAction = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-NoProfile -WindowStyle Hidden -File `"$logRotatePath`""
$logTrigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::ParseExact($LogRotateTime,'HH:mm',$null))

$healthAction = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-NoProfile -WindowStyle Hidden -File `"$healthPath`""
$startAt = (Get-Date).AddMinutes(1)
$healthTrigger = New-ScheduledTaskTrigger -Once -At $startAt -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)

$watchdogAction = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-NoProfile -WindowStyle Hidden -File `"$watchdogPath`""
$watchdogStart = (Get-Date).AddMinutes(2)
$watchdogTrigger = New-ScheduledTaskTrigger -Once -At $watchdogStart -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)

Register-ScheduledTask -TaskName $LogRotateTaskName -Action $logAction -Trigger $logTrigger -RunLevel Highest -Force | Out-Null
Register-ScheduledTask -TaskName $HealthTaskName -Action $healthAction -Trigger $healthTrigger -RunLevel Highest -Force | Out-Null
Register-ScheduledTask -TaskName $WatchdogTaskName -Action $watchdogAction -Trigger $watchdogTrigger -RunLevel Highest -Force | Out-Null

Write-Output "[OK] Tasks registered: $LogRotateTaskName, $HealthTaskName, $WatchdogTaskName"