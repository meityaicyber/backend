# Tool Selection Document

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
