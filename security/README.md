# Security Scanning Gate

This directory contains the configuration, orchestrator, and outputs for the automated Code Security Scanning Setup (SAST, SCA, and Secrets) as required by the SSDLC workflow.

## Structure
* `gate/`
  * `security_gate.py`: The Python orchestrator script that runs all scanners concurrently, parses results, and enforces the security gate.
  * `config.json`: The configuration file enabling/disabling tools and defining their CLI commands.
* `sast/`
  * `bandit.yaml`: Custom rule profile for the Bandit SAST scanner.
* `reports/`: The output directory where tools drop their JSON scan results.
* `false-positives.md`: The whitelist file. Any Critical/High findings must be listed here with a written justification to bypass the gate.
* `risk-and-limitation-register.md`: Automatically generated log of all Low/Medium severity findings that do not block the build but must be tracked.

## Usage
The security gate is triggered automatically on `git push` via a git hook (`.git/hooks/pre-push`). 
To run it manually:
```bash
python security/gate/security_gate.py
```
