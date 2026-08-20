# Remediation Record

**Date:** 2026-08-20

This document tracks the remediation of Critical and High findings identified during the first full security scan.

## Remediated Findings (Fixed in Code)

| Finding ID | Tool | Severity | Location | Description | Fix Implemented |
| :--- | :--- | :--- | :--- | :--- | :--- |
| SCA-1 | Trivy | HIGH | `backend/requirements.txt` | CVEs in `cryptography==43.0.1` | Upgraded `cryptography` to version `44.0.0`. |
| SCA-2 | Trivy | CRITICAL | `backend/requirements.txt` | Multiple unresolved CVEs in abandoned `python-jose==3.3.0` | Replaced `python-jose` entirely with the modern `PyJWT==2.10.1` library for secure JWT handling. |
| SCA-3 | Trivy | HIGH | `backend/requirements.txt`, `ai_pipeline/requirements.txt` | Resource exhaustion in `python-multipart==0.0.12` | Upgraded `python-multipart` to `0.0.20` across all python environment requirements. |

## Suppressed Findings (False Positives)

All suppressed findings are formally documented in `security/false-positives.md` with explicit justification. Silent suppression is forbidden.

| Finding Category | Tool | Severity | Location | Justification |
| :--- | :--- | :--- | :--- | :--- |
| SAST | ESLint | HIGH | `frontend/dist/assets/*` | Scanned compiled/minified code that triggered strict-mode alerts. Added `dist/` to `.eslintignore`. Exiting findings formally accepted in `false-positives.md`. |
| Secrets | Betterleaks | CRITICAL | `.env`, `.env.example` | Mock database credentials meant strictly for local development setup. No real production credentials exposed. Credentials in `.env` verified as non-production mock values; no rotation required. Production credentials are injected via environment variables at deployment time and were never committed to the repository. |
| Secrets | Betterleaks | CRITICAL | `bin/README.md` | Documentation examples for security tooling CLI commands. Not actual project secrets. Verified as non-production mock values; no rotation required. |

## Medium/Low Findings

All 26 Medium/Low severity findings (primarily Trivy informational alerts on indirect dependencies) have been appended to `security/risk-and-limitation-register.md`. They are tracked as technical debt but do not block the build per the SSDLC workflow.
