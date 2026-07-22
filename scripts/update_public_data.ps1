param(
    [switch]$NoPush
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$gitCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\MinGit\cmd\git.exe'),
    (Join-Path $env:ProgramFiles 'Git\cmd\git.exe')
)
$git = $gitCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$snapshot = Join-Path $projectRoot 'frontend\public\data\snapshot.json'
$logs = Join-Path $projectRoot 'data\logs'
$log = Join-Path $logs 'local-updater.log'

New-Item -ItemType Directory -Force -Path $logs | Out-Null

function Write-UpdateLog([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Add-Content -LiteralPath $log -Value $line -Encoding UTF8
    Write-Output $line
}

function Wait-WithProgress([int]$Seconds, [string]$Reason) {
    for ($remaining = $Seconds; $remaining -gt 0; $remaining--) {
        $elapsed = $Seconds - $remaining
        $percent = if ($Seconds -gt 0) { [int](100 * $elapsed / $Seconds) } else { 100 }
        Write-Progress `
            -Activity 'Rhythm Calendar data update' `
            -Status "$Reason - $remaining seconds remaining" `
            -PercentComplete $percent
        Start-Sleep -Seconds 1
    }
    Write-Progress -Activity 'Rhythm Calendar data update' -Completed
}

function Invoke-GitPush([int]$TimeoutSeconds = 45) {
    # Git writes normal progress to stderr. Temporarily keep native stderr from
    # becoming a terminating PowerShell error and judge success by ExitCode.
    # Revocation lookup is disabled only for this command because that Windows
    # endpoint is blocked on the current network; certificate validation stays on.
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = @(& $git `
            -c http.schannelCheckRevoke=false `
            -c http.version=HTTP/1.1 `
            -c http.lowSpeedLimit=1 `
            -c "http.lowSpeedTime=$TimeoutSeconds" `
            push origin main 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    return [pscustomobject]@{ ExitCode = $exitCode; Output = ($output -join "`n") }
}

function Push-GitHubWithRetry {
    $delays = @(0, 30, 120)
    for ($attempt = 0; $attempt -lt $delays.Count; $attempt++) {
        if ($delays[$attempt] -gt 0) {
            Write-UpdateLog "Waiting $($delays[$attempt]) seconds before push retry"
            Wait-WithProgress $delays[$attempt] "Waiting for GitHub upload attempt $($attempt + 1)"
        }
        $pushResult = Invoke-GitPush
        $pushExitCode = $pushResult.ExitCode
        foreach ($line in @($pushResult.Output -split "`r?`n")) {
            if ($line) { Write-UpdateLog "git: $line" }
        }
        if ($pushExitCode -eq 0) {
            Write-UpdateLog "GitHub push succeeded on attempt $($attempt + 1)"
            return
        }
        Write-UpdateLog "GitHub push attempt $($attempt + 1) failed with exit code $pushExitCode"
    }
    throw 'GitHub push failed after 3 attempts; the local commit is preserved for the next run'
}

try {
    if (-not (Test-Path -LiteralPath $python)) {
        throw "Python environment not found: $python"
    }
    if (-not $git) {
        throw 'Git executable not found'
    }

    Write-Progress -Activity 'Rhythm Calendar data update' -Status 'Preparing environment' -PercentComplete 2
    Write-UpdateLog 'Starting anonymous music-game account collection'
    Push-Location $projectRoot
    try {
        $env:GCM_INTERACTIVE = 'Never'
        $ahead = & $git rev-list --count '@{upstream}..HEAD'
        if ($LASTEXITCODE -eq 0 -and [int]$ahead -gt 0) {
            Write-Progress -Activity 'Rhythm Calendar data update' -Status 'Uploading pending local commits' -PercentComplete 8
            Write-UpdateLog "Found $ahead pending local commit(s); uploading them first"
            Push-GitHubWithRetry
        }

        Write-Progress -Activity 'Rhythm Calendar data update' -Status 'Collecting 14 Bilibili accounts' -PercentComplete 15
        & $python -m backend.export_static --output $snapshot --fallback $snapshot
        if ($LASTEXITCODE -ne 0) { throw "Collector exited with $LASTEXITCODE" }

        $payload = Get-Content -LiteralPath $snapshot -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $payload.dynamics -or $payload.dynamics.Count -eq 0) {
            throw 'Collector produced an empty snapshot'
        }
        Write-UpdateLog "Collected $($payload.dynamics.Count) dynamics"
        Write-Progress -Activity 'Rhythm Calendar data update' -Status 'Snapshot generated' -PercentComplete 75

        if ($NoPush) {
            Write-UpdateLog 'NoPush requested; skipping GitHub upload'
            Write-Progress -Activity 'Rhythm Calendar data update' -Completed
            exit 0
        }

        & $git add -- 'frontend/public/data/snapshot.json'
        & $git diff --cached --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-UpdateLog 'Snapshot unchanged; nothing to upload'
            Write-Progress -Activity 'Rhythm Calendar data update' -Completed
            exit 0
        }
        & $git commit -m "Update music game dynamics $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        if ($LASTEXITCODE -ne 0) { throw "Git commit exited with $LASTEXITCODE" }
        Write-Progress -Activity 'Rhythm Calendar data update' -Status 'Uploading to GitHub' -PercentComplete 88
        Push-GitHubWithRetry
        Write-UpdateLog 'Snapshot uploaded successfully'
        Write-Progress -Activity 'Rhythm Calendar data update' -Status 'Update completed' -PercentComplete 100
        Write-Progress -Activity 'Rhythm Calendar data update' -Completed
    }
    finally {
        Pop-Location
    }
}
catch {
    Write-Progress -Activity 'Rhythm Calendar data update' -Completed
    Write-UpdateLog "FAILED: $($_.Exception.Message)"
    exit 1
}
