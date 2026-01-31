## Script to register a scheduled task to run `tools/backup_data.ps1` daily at 03:00
Param(
    [string]$ScriptPath = "$PSScriptRoot\backup_data.ps1",
    [string]$TaskName = "MeteoSer Backup",
    [string]$Time = "03:00"
)

$abs = (Resolve-Path $ScriptPath).Path
Write-Output "Registering scheduled task '$TaskName' -> $abs at $Time"

$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-NoProfile -WindowStyle Hidden -File `"$abs`""
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::ParseExact($Time,'HH:mm',$null))

try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -RunLevel Highest -Force
    Write-Output "[OK] Task registered: $TaskName"
} catch {
    Write-Error "[ERROR] Could not register task: $($_.Exception.Message)"
}

Write-Output "Note: Run this script from an elevated PowerShell prompt if registration fails due to permissions."
