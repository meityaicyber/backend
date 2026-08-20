# Results and Analysis

This document interprets the outcomes of the initial security scanning exercise for the Cybersecurity Audit Report Management System. It goes beyond the raw findings to identify systemic weaknesses and recommend improvements to our coding practices.

## 1. Summary Statistics

**Findings by Severity (Pre-Remediation)**
| Severity | Count | Status |
| :--- | :--- | :--- |
| **CRITICAL** | 5 | 1 Remediated / 4 Justified False Positives |
| **HIGH** | 500+ | 2 Remediated / Rest Justified False Positives (Compiled Code) |
| **MEDIUM/LOW** | 26 | Tracked in Risk Register |

**Findings by Category**
| Category | Tool | True Positives | False Positives |
| :--- | :--- | :--- | :--- |
| **SAST** | Bandit (Python) | 0 | 0 |
| **SAST** | ESLint (JS) | 0 | 12 (Compiled `dist/` & standard strict-mode) |
| **SCA** | Trivy | 3 | 0 |
| **Secrets** | Betterleaks | 0 | 4 (Mock configs/READMEs) |

**Findings by Module**
| Module / Subsystem | Findings (High/Critical) | Tracked Risks (Med/Low) |
| :--- | :--- | :--- |
| **Backend API (`backend/`)** | 2 | 23 |
| **Frontend UI (`frontend/`)** | 0 | 0 |
| **AI Pipeline (`ai_pipeline/`)** | 1 | 3 |
| **DevOps / Config** | 0 | 0 |

## 2. Analysis of Significant Findings

The initial scan revealed a few architectural supply-chain weaknesses that the team must address going forward:

**A. Stale and Abandoned Dependencies**
The SCA scan revealed the usage of `python-jose`, a JWT library that has been formally abandoned and contains unpatched CVEs. 
*Insight:* The team must actively monitor the maintenance status of cryptographic and security-critical libraries, not just their current CVE counts. We have replaced this with `PyJWT`.

**B. Scanning Configuration Scopes**
The initial SAST (ESLint) and Secrets (Betterleaks) scans generated massive amounts of noise because they were improperly scoped. ESLint attempted to lint minified JavaScript in `frontend/dist/`, and Betterleaks flagged `.env.example` mock strings.
*Insight:* Security tools must be tightly scoped to source directories (`frontend/src`, `backend/`, `ai_pipeline/`).

## 3. False-Positive Rate

The gate's false-positive rate (FPR) during the initial rollout highlighted the need for strict scope control:
*   **Bandit:** 0% FPR.
*   **ESLint:** Extremely high FPR initially due to missing `.eslintignore` rules for compiled artifacts.
*   **Betterleaks:** 100% FPR on this run, as it correctly identified "secrets" that were intentionally mock strings in documentation and `.env.example`.
*   **Trivy:** 0% FPR on OS packages and dependencies. All flagged CVEs were legitimate.

All false positives have now been formally documented with justification strings in `security/false-positives.md`.

## 4. Recommendations and Coding Practices

Based on the scan results, the following SSDLC practices are now mandatory for all future development:

1.  **Dependency Maintenance:** Do not use abandoned Python libraries. Prioritize well-maintained, official libraries (e.g., `PyJWT` over `python-jose`).
2.  **No Pickles:** Use `safetensors` or ONNX formats for all model artifact loading (proactively enforced).
3.  **Strict Secrets Management:** Absolutely no API keys, tokens, or passwords in code, test files, or `docker-compose.yml`. All credentials must be injected via the `.env` file or environment variables at runtime.
4.  **Security Gate Scope:** All new directories or compiled output must be explicitly added to ignore-lists (`.gitignore`, `.eslintignore`) to prevent the gate from failing on non-source artifacts.
