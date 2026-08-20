| Bandit | LOW | ai_pipeline/main.py:178 | Standard pseudo-random generators are not suitable for security/cryptographic purposes. | TBD |
| Bandit | LOW | backend/app/dependencies.py:35 | Possible hardcoded password: 'access' | TBD |
| Bandit | LOW | backend/app/services/auth_service.py:74 | Possible hardcoded password: 'bearer' | TBD |
| Bandit | LOW | backend/app/services/auth_service.py:149 | Possible hardcoded password: 'bearer' | TBD |
| Bandit | LOW | backend/app/utils/pdf_converter.py:10 | Consider possible security implications associated with the subprocess module. | TBD |
| Bandit | LOW | backend/app/utils/pdf_converter.py:50 | Starting a process with a partial executable path | TBD |
| Bandit | LOW | backend/app/utils/pdf_converter.py:50 | subprocess call - check for execution of untrusted input. | TBD |
| Trivy | MEDIUM | ai_pipeline/requirements.txt (python-multipart) | CVE-2026-40347 | TBD |
| Trivy | LOW | ai_pipeline/requirements.txt (python-multipart) | CVE-2026-53537 | TBD |
| Trivy | LOW | ai_pipeline/requirements.txt (python-multipart) | CVE-2026-53538 | TBD |
| Trivy | LOW | ai_pipeline/requirements.txt (python-multipart) | CVE-2026-53540 | TBD |
| Trivy | MEDIUM | backend/requirements.txt (PyPDF2) | CVE-2023-36464 | TBD |
| Trivy | MEDIUM | backend/requirements.txt (cryptography) | CVE-2026-69248 | TBD |
| Trivy | LOW | backend/requirements.txt (cryptography) | CVE-2024-12797 | TBD |
| Trivy | LOW | backend/requirements.txt (cryptography) | CVE-2026-34073 | TBD |
| Trivy | MEDIUM | backend/requirements.txt (python-jose) | CVE-2024-33664 | TBD |
| Trivy | MEDIUM | backend/requirements.txt (python-multipart) | CVE-2026-40347 | TBD |
| Trivy | LOW | backend/requirements.txt (python-multipart) | CVE-2026-53537 | TBD |
| Trivy | LOW | backend/requirements.txt (python-multipart) | CVE-2026-53538 | TBD |
| Trivy | LOW | backend/requirements.txt (python-multipart) | CVE-2026-53540 | TBD |
| Trivy | MEDIUM | frontend/package-lock.json (react-router) | CVE-2026-53666 | TBD |
| Trivy | MEDIUM | frontend/package-lock.json (react-router) | CVE-2026-53669 | TBD |
| Trivy | MEDIUM | frontend/package-lock.json (react-router-dom) | CVE-2026-53668 | TBD |
| Trivy | MEDIUM | backend/requirements.txt (PyJWT) | CVE-2026-48522 | TBD |
| Trivy | MEDIUM | backend/requirements.txt (PyJWT) | CVE-2026-48523 | TBD |
| Trivy | MEDIUM | backend/requirements.txt (PyJWT) | CVE-2026-48525 | TBD |
| Trivy | LOW | backend/requirements.txt (PyJWT) | CVE-2026-48524 | TBD |
| Bandit | LOW | objective4/test.py:1 | Consider possible security implications associated with pickle module. | TBD |
| Bandit | MEDIUM | objective4/test.py:1 | Pickle and modules that wrap it can be unsafe when used to deserialize untrusted data, possible security issue. | TBD |
