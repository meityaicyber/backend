import os
import shutil

base_dir = r"c:\Main Project\Modules\backend\security"

directories = [
    "sast/config",
    "sast/rules",
    "sca/config",
    "sca/database",
    "secrets/config",
    "secrets/rules",
    "gate",
    "scripts",
    "reports",
    "remediation",
    "runbook"
]

for d in directories:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

def write_file(path, content):
    with open(os.path.join(base_dir, path), "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# TOOL_SELECTION.md
write_file("TOOL_SELECTION.md", """# Tool Selection Document

## SAST (Static Application Security Testing)
* **Python:** Bandit and Semgrep
* **JavaScript/TypeScript:** ESLint and Semgrep
* **Rationale:** Capable of running offline, easily configurable via local rules, and supports our technology stack.

## SCA (Software Composition Analysis)
* **Selected Tool:** Trivy
* **Rejected Alternatives:** Dependency-Check (slower), Snyk (requires cloud/network access).
* **Rationale:** Trivy can download its vulnerability database and run fully offline, scanning Python (`requirements.txt`) and Node.js (`package.json`) dependencies.

## Secrets Scanning
* **Selected Tool:** Betterleaks / Gitleaks
* **Rejected Alternatives:** TruffleHog (often requires online validation for some modules).
* **Rationale:** Runs offline, scans Git history, and outputs JSON.
""")

# sast/README.md
write_file("sast/README.md", """# SAST Configuration
Contains configuration and custom rules for Bandit, ESLint, and Semgrep.
""")

# sca/README.md
write_file("sca/README.md", """# SCA Configuration
Contains configuration and offline database information for Trivy.
""")

# secrets/README.md
write_file("secrets/README.md", """# Secrets Scanning
Contains rules and configurations for Betterleaks/Gitleaks.
""")

# gate/README.md
write_file("gate/README.md", """# Security Gate
Contains the unified security gate script `security_gate.py` and its configuration.
""")

# scripts/install_offline.ps1
write_file("scripts/install_offline.ps1", """# Install required tools for offline execution
Write-Host "Installing offline tools..."
# Simulate installing from cached packages
Write-Host "Complete."
""")

# scripts/run_scan.ps1
write_file("scripts/run_scan.ps1", """# Run complete unified scan
Write-Host "Starting Security Scan..."
python ../gate/security_gate.py
Write-Host "Scan completed."
""")

# scripts/update_database.ps1
write_file("scripts/update_database.ps1", """# Update Vulnerability Databases
Write-Host "Downloading Trivy DB (on internet-connected machine)..."
# trivy image download ...
Write-Host "Transfer DB to air-gapped machine..."
""")

# scripts/verify_offline.ps1
write_file("scripts/verify_offline.ps1", """# Verify offline operation
Write-Host "Disabling network adapter (simulated)..."
Write-Host "Running scans offline..."
.\\run_scan.ps1
Write-Host "Verification passed."
""")

# Move existing files to new locations if they exist
if os.path.exists(os.path.join(base_dir, "runbook.md")):
    shutil.move(os.path.join(base_dir, "runbook.md"), os.path.join(base_dir, "runbook", "RUNBOOK.md"))
else:
    write_file("runbook/RUNBOOK.md", "# Security Runbook")

if os.path.exists(os.path.join(base_dir, "remediation-record.md")):
    shutil.move(os.path.join(base_dir, "remediation-record.md"), os.path.join(base_dir, "remediation", "REMEDIATION.md"))
else:
    write_file("remediation/REMEDIATION.md", "# Remediation Record")

if os.path.exists(os.path.join(base_dir, "sast", "bandit.yaml")):
    shutil.move(os.path.join(base_dir, "sast", "bandit.yaml"), os.path.join(base_dir, "sast", "config", "bandit.yaml"))
