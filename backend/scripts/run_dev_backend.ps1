$ErrorActionPreference = 'Stop'

$backendRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $backendRoot 'venv\Scripts\python.exe'
$logDirectory = Join-Path $backendRoot '.runtime-logs\request-timing'
$timingLog = Join-Path $logDirectory 'requests.log'

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'The project virtual environment Python executable was not found.'
}

$persistentLoggingReady = $true
$probePath = Join-Path $logDirectory ('.write-check-' + [guid]::NewGuid().ToString('N'))
try {
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    [System.IO.File]::WriteAllText($probePath, '')
    $stream = [System.IO.File]::Open(
        $timingLog,
        [System.IO.FileMode]::OpenOrCreate,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::ReadWrite
    )
    $stream.Dispose()
}
catch {
    $persistentLoggingReady = $false
    Write-Warning ('Persistent timing log is unavailable ({0}); console logging will remain enabled.' -f $_.Exception.GetType().Name)
}
finally {
    if (Test-Path -LiteralPath $probePath -PathType Leaf) {
        try {
            Remove-Item -LiteralPath $probePath -Force
        }
        catch {
            $persistentLoggingReady = $false
            Write-Warning ('Log-directory write check cleanup failed ({0}); console logging will remain enabled.' -f $_.Exception.GetType().Name)
        }
    }
}

$arguments = @(
    '-m', 'uvicorn', 'app.main:app',
    '--reload', '--reload-dir', 'app',
    '--host', '127.0.0.1', '--port', '8000',
    '--log-level', 'info'
)
if ($persistentLoggingReady) {
    $arguments += @('--log-config', 'logging.json')
}

Push-Location $backendRoot
try {
    & $python @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
