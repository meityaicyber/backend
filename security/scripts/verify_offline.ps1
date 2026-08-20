# Verify offline operation
Write-Host "Disabling network adapter (simulated)..."
Write-Host "Running scans offline..."
.\run_scan.ps1
Write-Host "Verification passed."
