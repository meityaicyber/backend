$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "  Initializing Local Offline Security Gate"
Write-Host "=========================================="

# 1. Setup Python Virtual Environment & Bandit
Write-Host "`n[1/4] Setting up Python Virtual Environment..."
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "Created new venv."
} else {
    Write-Host "venv already exists."
}
Write-Host "Installing SAST tools (Bandit, Semgrep) from offline cache..."
.\venv\Scripts\python.exe -m pip install --no-index --find-links="Z:\offline-security-tools-cache" bandit semgrep

# 2. Setup Node.js & ESLint
Write-Host "`n[2/4] Verifying Node.js and installing ESLint..."
if (Get-Command "npm" -ErrorAction SilentlyContinue) {
    npm install -g eslint
} else {
    Write-Host "WARNING: npm not found! Please install Node.js to use ESLint." -ForegroundColor Yellow
}

# 3. Download Offline Binary Scanners (Trivy, Grype, Betterleaks)
Write-Host "`n[3/4] Downloading Offline Binary Scanners..."
if (Test-Path "install_tools.ps1") {
    powershell -File install_tools.ps1
} else {
    Write-Host "WARNING: install_tools.ps1 not found!" -ForegroundColor Red
}

# 4. Install Git Pre-Push Hook
Write-Host "`n[4/4] Installing Git Pre-Push Hook..."
if (Test-Path "security/gate/pre-push") {
    if (-not (Test-Path ".git/hooks")) {
        New-Item -ItemType Directory -Path ".git/hooks" | Out-Null
    }
    Copy-Item "security/gate/pre-push" -Destination ".git/hooks/pre-push" -Force
    Write-Host "Successfully installed pre-push hook into .git/hooks/"
} else {
    Write-Host "WARNING: security/gate/pre-push not found! Hook not installed." -ForegroundColor Red
}

Write-Host "`n=========================================="
Write-Host "✅ Security Setup Complete!"
Write-Host "You can test the gate by running: py security/gate/security_gate.py"
Write-Host "=========================================="
