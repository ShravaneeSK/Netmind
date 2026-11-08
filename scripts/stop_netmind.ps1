# NetMind: stop the backend and dashboard. Add -Db to stop the database container too.
param([switch]$Db)

foreach ($port in 8000, 5173) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped the process listening on port $port"
        }
}
if ($Db) {
    docker stop netmind-db | Out-Null
    Write-Host 'Database container stopped'
}

