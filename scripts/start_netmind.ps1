# NetMind: start the database, backend and dashboard, then open the browser.
$root = Split-Path -Parent $PSScriptRoot
$activate = Join-Path $root 'venv\Scripts\Activate.ps1'

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Docker is not running. Start Docker Desktop, wait for "Engine running", then run this script again.'
    exit 1
}
docker start netmind-db | Out-Null
Write-Host 'Database container started. Waiting 8 seconds for PostgreSQL...'
Start-Sleep -Seconds 8

foreach ($port in 8000, 5173) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Start-Process powershell -ArgumentList '-NoExit', '-Command',
    "cd '$root\backend'; & '$activate'; uvicorn app.main:app"
Start-Process powershell -ArgumentList '-NoExit', '-Command',
    "cd '$root\frontend'; npm run dev"

Write-Host 'Waiting for the backend (the first start loads the models and can take a minute)...'
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        Invoke-RestMethod http://127.0.0.1:8000/health -TimeoutSec 2 | Out-Null
        $ready = $true
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}

if ($ready) {
    Write-Host 'Backend is up. Opening the dashboard.'
    Start-Process 'http://localhost:5173'
} else {
    Write-Host 'The backend did not answer within 2 minutes. Look at its window for the error.'
}

