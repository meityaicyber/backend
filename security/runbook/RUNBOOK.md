# Security Scanning Runbook

This runbook explains how to install the offline security tools, run the scans, and handle gate failures.

## 1. Offline Installation

All security tools are packaged and designed to run entirely offline without querying cloud services.

1.  **Clone the Repository:** Ensure you have the latest code from the project's internal Git server.
2.  **Run the Initialization Script:**
    From the root of the repository, execute the setup script:
    ```powershell
    .\init-security.ps1
    ```
    This single script automatically:
    * Creates the Python virtual environment.
    * Installs SAST tools natively using the local offline packages cache.
    * Extracts the SCA and Secret scanning binaries (Trivy, Betterleaks) into the `bin/` directory.
    * Installs the pre-push hook directly into `.git/hooks/pre-push`.

3.  **Database Updates (Trivy and Offline Tools):**
    Ensure you have copied the latest Trivy vulnerability database to your local cache according to the offline DB update procedure. To skip online updates during scanning, ensure `--skip-db-update` is present in the Trivy command inside `security/gate/config.json`.

## Offline Advisory Database Process

**On Internet-Connected Machine:**
1. Download vulnerability database (e.g. Trivy DB: `oras pull ghcr.io/aquasecurity/trivy-db:2`).
2. Verify source and checksum where available.
3. Record database version and download date.
4. Transfer using approved offline mechanism (e.g. secure USB).

**On Air-Gapped Machine:**
1. Import database.
2. Verify checksum and database version.
3. Run scan using local database.
4. Record database snapshot date.

**Database Update Procedure (Frequency & Responsibility):**
*   **Update frequency:** Weekly.
*   **Responsible person/team:** Security Lead.
*   **Failed-update procedure:** Rollback to the previous database version and investigate transfer logs.


## 2. Running the Full Scan

The security gate is wired directly into Git. You do not need to run a complex sequence of commands.

**To run the scan, simply attempt to push your code:**
```bash
git push origin your-feature-branch
```

**To run the scan manually (without pushing):**
```bash
python security/gate/security_gate.py
```

## 3. Reading the Output

When the scan runs, it executes Bandit, ESLint, Trivy, Grype, and Betterleaks concurrently.

*   **Reports:** Raw JSON reports are generated in the `security/reports/` directory.
*   **Terminal Output:** The orchestrator parses the JSON and outputs a summary to your terminal.
*   **Risk Register:** Any Low/Medium findings are silently appended to `security/risk-and-limitation-register.md`.

## 4. Handling Gate Failures

If a tool finds a **CRITICAL** or **HIGH** severity issue, the orchestrator will abort your `git push` and display a failure message like this:

```text
[FAIL] Bandit HIGH: backend/api.py:45 - Use of hardcoded SQL query
...
Total Unresolved CRITICAL/HIGH findings: 1
❌ FAILED
```

**How to resolve the failure:**

You have two options to unblock your branch:

**Option A: Fix the Code (Preferred)**
1.  Open the file and line number indicated in the output.
2.  Fix the vulnerability (e.g., use parameterized queries instead of hardcoded SQL strings).
3.  Commit your change and run `git push` again.

**Option B: Mark as False Positive (If applicable)**
If you are absolutely certain the finding is a false positive or an accepted risk for this specific air-gapped environment:
1.  Open `security/false-positives.md`.
2.  Copy the exact string pattern provided by the failure output in your terminal.
3.  Paste it into the file and **you must append a written justification**. 
    *Example:* `backend/api.py:45:bandit | Bandit | Query is safely sanitized via internal library | Jane Doe | 2026-08-20`
4.  Commit `security/false-positives.md` and push again. The gate will now pass.
