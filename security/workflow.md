# Security Gate Workflow & Architecture

This document provides a comprehensive, step-by-step breakdown of how the automated Code Security Scanning Setup operates from the moment a developer attempts to push code, all the way to the final decision.

## The End-to-End Workflow Diagram

```mermaid
graph TD
    %% Developer Action
    Start((Developer runs <br> 'git push')) --> Hook[Git pre-push hook <br> intercepts push]
    
    %% Orchestrator Initialization
    Hook --> Init[Execute security_gate.py <br> (The Orchestrator)]
    Init --> ReadConfig[Read config.json]
    
    %% Concurrent Execution (The 5 Scanners)
    ReadConfig -->|Spawns Thread 1| SAST_PY[Bandit <br> Python SAST]
    ReadConfig -->|Spawns Thread 2| SAST_JS[ESLint <br> Next.js SAST]
    ReadConfig -->|Spawns Thread 3| SAST_CUSTOM[Opengrep <br> Custom Rules]
    ReadConfig -->|Spawns Thread 4| SCA[Trivy <br> Dependency Analysis]
    ReadConfig -->|Spawns Thread 5| SECRETS[Betterleaks <br> Secrets Scanner]
    
    %% Reporting
    SAST_PY --> WriteJSON[Tools generate raw JSON <br> in security/reports/]
    SAST_JS --> WriteJSON
    SAST_CUSTOM --> WriteJSON
    SCA --> WriteJSON
    SECRETS --> WriteJSON
    
    %% Parsing & Logic
    WriteJSON --> Parse[Orchestrator parses all JSONs <br> & Normalizes Severities]
    
    Parse --> Triage{What is the <br> finding severity?}
    
    %% Low/Medium Flow
    Triage -->|Low / Medium| RiskReg[Append to <br> risk-and-limitation-register.md]
    RiskReg --> Continue1(Tracked - Does not block push)
    
    %% High/Critical Flow
    Triage -->|High / Critical| CheckFP{Is finding listed in <br> false-positives.md?}
    
    CheckFP -->|Yes - Whitelisted| Skip[Log as 'SKIP' & <br> Accept Risk]
    Skip --> Continue2(Whitelisted - Does not block push)
    
    CheckFP -->|No - Unresolved| Block[Flag as Unresolved <br> Vulnerability]
    
    %% Final Verdict
    Continue1 --> Verdict
    Continue2 --> Verdict
    Block --> Verdict{Are there any <br> Unresolved vulnerabilities?}
    
    Verdict -->|Yes| Fail[Exit Code 1 <br> Print Findings]
    Verdict -->|No| Pass[Exit Code 0 <br> Print Success]
    
    Fail --> Abort((Git Push <br> ABORTED))
    Pass --> Allow((Git Push <br> ALLOWED))
    
    style Abort fill:#ff4d4d,stroke:#333,stroke-width:2px,color:#fff
    style Allow fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
    style Start fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
```

## Step-by-Step Technical Execution

### 1. Interception (The Git Hook)
The workflow begins when a developer types `git push`. Before Git actually communicates with the remote server, it triggers the `.git/hooks/pre-push` script. This bash script changes the directory to the repository root and invokes the Python orchestrator (`security_gate.py`) using the local offline virtual environment.

### 2. Initialization & Configuration
The Python orchestrator starts by reading `security/gate/config.json`. This file dictates exactly which tools are active and defines their exact command-line arguments (including exclusion paths like `--ignore-pattern "**/dist/**"` for ESLint, and `--skip-db-update` for Trivy to enforce the air-gap rule).

### 3. Concurrent Scanning
To prevent the gate from slowing down development, the orchestrator uses a `ThreadPoolExecutor`. It spawns all 5 enabled security tools simultaneously in parallel processes. 
*   **SAST:** Evaluates the AST (Abstract Syntax Tree) of our Python and JavaScript files using local rules without executing the code.
*   **SCA:** Scans the `requirements.txt` against the locally cached Trivy vulnerability database.
*   **Secrets:** Recursively scans the file contents for regex patterns matching high-entropy secrets and credentials.

### 4. Normalized Reporting
Rather than dumping chaotic text to the terminal, every tool is forced (via `config.json` arguments) to output its findings as structured JSON files into the `security/reports/` directory.

### 5. Triaging & The Risk Register
The orchestrator reads all the JSON files, unifies their different data structures, and maps their native severities into a standard scale (CRITICAL, HIGH, MEDIUM, LOW). 
Any finding categorized as **Medium** or **Low** is instantly appended to `security/risk-and-limitation-register.md`. This satisfies the SSDLC requirement to track technical debt without actively blocking developer workflows.

### 6. The Strict Gate (False Positives)
If a finding is categorized as **Critical** or **High**, the orchestrator checks `security/false-positives.md`.
*   If the exact file, line number, and tool match an entry in the whitelist (and it includes a written justification), the gate explicitly logs it as a `[SKIP]` and forgives the error.
*   If it is *not* in the whitelist, it is marked as an unresolved vulnerability.

### 7. The Final Verdict
Once all findings are triaged:
*   If the counter for Unresolved Critical/High findings is `0`, the orchestrator exits with `Code 0`. The bash hook sees the success and permits the `git push` to upload to the server.
*   If the counter is `1` or greater, the orchestrator prints the exact location of the vulnerabilities to the terminal and exits with `Code 1`. The bash hook intercepts this failure and immediately terminates the `git push`, protecting the remote branch from vulnerable code.
