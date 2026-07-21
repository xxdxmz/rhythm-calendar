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

try {
    if (-not (Test-Path -LiteralPath $python)) {
        throw "Python environment not found: $python"
    }
    if (-not $git) {
        throw 'Git executable not found'
    }

    Write-UpdateLog 'Starting anonymous Arcaea collection'
    Push-Location $projectRoot
    try {
        & $python -m backend.export_static --output $snapshot
        if ($LASTEXITCODE -ne 0) { throw "Collector exited with $LASTEXITCODE" }

        $payload = Get-Content -LiteralPath $snapshot -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $payload.dynamics -or $payload.dynamics.Count -eq 0) {
            throw 'Collector produced an empty snapshot'
        }
        Write-UpdateLog "Collected $($payload.dynamics.Count) dynamics"

        if ($NoPush) {
            Write-UpdateLog 'NoPush requested; skipping GitHub upload'
            exit 0
        }

        & $git add -- 'frontend/public/data/snapshot.json'
        & $git diff --cached --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-UpdateLog 'Snapshot unchanged; nothing to upload'
            exit 0
        }
        & $git commit -m "Update Arcaea dynamics $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        if ($LASTEXITCODE -ne 0) { throw "Git commit exited with $LASTEXITCODE" }
        & $git push origin main
        if ($LASTEXITCODE -ne 0) { throw "Git push exited with $LASTEXITCODE" }
        Write-UpdateLog 'Snapshot uploaded successfully'
    }
    finally {
        Pop-Location
    }
}
catch {
    Write-UpdateLog "FAILED: $($_.Exception.Message)"
    exit 1
}
