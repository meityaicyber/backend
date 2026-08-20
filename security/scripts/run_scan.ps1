# Run complete unified scan
Write-Host "Starting Security Scan..."
$ProjectRoot = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $ProjectRoot
.\venv\Scripts\python.exe security\gate\security_gate.py
Write-Host "Scan completed."
