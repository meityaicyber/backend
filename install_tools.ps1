$ErrorActionPreference = "Stop"
$binDir = "C:\SECUREGATEWAY\bin"
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir | Out-Null }

$offlineCache = "Z:\offline-security-tools-cache" # Shared network drive or USB path for air-gapped env

Write-Host "Extracting Gitleaks (Betterleaks) from offline cache..."
Expand-Archive -Path "$offlineCache\gitleaks_8.18.2_windows_x64.zip" -DestinationPath "$binDir" -Force

Write-Host "Extracting Trivy from offline cache..."
Expand-Archive -Path "$offlineCache\trivy_0.74.0_windows-64bit.zip" -DestinationPath "$binDir\trivy" -Force
Move-Item -Path "$binDir\trivy\trivy.exe" -Destination "$binDir\trivy.exe" -Force
Remove-Item "$binDir\trivy" -Recurse -Force

Write-Host "Extracting Grype from offline cache..."
Expand-Archive -Path "$offlineCache\grype_0.77.3_windows_amd64.zip" -DestinationPath "$binDir" -Force

Write-Host "Extracting Syft from offline cache..."
Expand-Archive -Path "$offlineCache\syft_1.3.0_windows_amd64.zip" -DestinationPath "$binDir" -Force

Write-Host "All tools installed locally in $binDir from offline cache!"
