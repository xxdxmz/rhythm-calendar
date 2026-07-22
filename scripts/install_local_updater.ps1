$ErrorActionPreference = 'Stop'
$updateScript = Join-Path $PSScriptRoot 'update_public_data.ps1'
$taskName = 'Rhythm Calendar - Update Arcaea Data'
$powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

if (-not (Test-Path -LiteralPath $updateScript)) {
    throw "Updater script not found: $updateScript"
}

$action = New-ScheduledTaskAction `
    -Execute $powershell `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$updateScript`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddHours(6) `
    -RepetitionInterval (New-TimeSpan -Hours 6)
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -WakeToRun `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description 'Anonymous Arcaea collection and static JSON upload every six hours.' `
    -Force | Out-Null

Write-Output "Installed scheduled task: $taskName"
Write-Output "First run: $($trigger.StartBoundary)"
