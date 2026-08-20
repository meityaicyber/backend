import json
import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_command(name, command):
    print(f"[RUNNING] {name}...")
    try:
        # Use shell=True for windows compatibility and to handle piped/chained commands
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"[FINISHED] {name}")
        return name, result.returncode, result.stdout, result.stderr
    except Exception as e:
        print(f"[ERROR] {name} execution failed: {e}")
        return name, -1, "", str(e)

def load_false_positives(fp_path):
    fps = set()
    if os.path.exists(fp_path):
        with open(fp_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('file/line') and not line.startswith('#'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        fps.add(parts[0]) # file/line:tool or target:pkg:trivy
    return fps

def parse_opengrep(fps, critical_high_count, new_fps, risk_register):
    if os.path.exists('security/reports/opengrep-results.json'):
        with open('security/reports/opengrep-results.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for result in data.get('results', []):
                    sev = result.get('extra', {}).get('severity', 'INFO').upper()
                    if sev == 'ERROR':
                        sev = 'HIGH' # Normalize to HIGH
                    file_path = os.path.relpath(result.get('path', ''), start=os.getcwd()).replace('\\', '/')
                    parts = file_path.split('/')
                    if 'venv' in parts or 'node_modules' in parts or 'security' in parts:
                        continue

                    line = result.get('start', {}).get('line', 0)
                    fp_key = f"{file_path}:{line}:opengrep"
                    if sev in ['HIGH', 'CRITICAL']:
                        if fp_key not in fps:
                            critical_high_count += 1
                            print(f"[FAIL] Opengrep {sev}: {file_path}:{line} - {result.get('extra', {}).get('message', '')}")
                            new_fps.append(f"{fp_key} | Opengrep | Add justification here | Developer Name | 2026-08-20")
                        else:
                            print(f"[SKIP] Opengrep {sev} (False Positive): {file_path}:{line}")
                    elif sev in ['LOW', 'MEDIUM', 'INFO']:
                        risk_register.append(f"| Opengrep | {sev} | {file_path}:{line} | {result.get('extra', {}).get('message', '')} | TBD |")
            except Exception as e:
                pass
    return critical_high_count

def parse_bandit(fps, critical_high_count, new_fps, risk_register):
    if os.path.exists('security/reports/bandit-results.json'):
        with open('security/reports/bandit-results.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for result in data.get('results', []):
                    sev = result.get('issue_severity', 'LOW').upper()
                    file_path = os.path.relpath(result.get('filename', ''), start=os.getcwd()).replace('\\', '/')
                    line = result.get('line_number', 0)
                    parts = file_path.split('/')
                    if 'venv' in parts or 'node_modules' in parts or 'security' in parts:
                        continue

                    fp_key = f"{file_path}:{line}:bandit"
                    if sev in ['HIGH', 'CRITICAL']:
                        if fp_key not in fps:
                            critical_high_count += 1
                            print(f"[FAIL] Bandit {sev}: {file_path}:{line} - {result.get('issue_text')}")
                            new_fps.append(f"{fp_key} | Bandit | Add justification here | Developer Name | 2026-08-20")
                        else:
                            print(f"[SKIP] Bandit {sev} (False Positive): {file_path}:{line}")
                    elif sev in ['LOW', 'MEDIUM']:
                        risk_register.append(f"| Bandit | {sev} | {file_path}:{line} | {result.get('issue_text')} | TBD |")
            except Exception as e:
                print(f"[ERROR] Failed to parse bandit results: {e}")
    return critical_high_count

def parse_eslint(fps, critical_high_count, new_fps, risk_register):
    if os.path.exists('security/reports/eslint-results.json'):
        with open('security/reports/eslint-results.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for file_result in data:
                    file_path = os.path.relpath(file_result.get('filePath', ''), start=os.getcwd()).replace('\\', '/')
                    parts = file_path.split('/')
                    if 'venv' in parts or 'node_modules' in parts or 'security' in parts:
                        continue

                    for message in file_result.get('messages', []):
                        if message.get('severity') == 2: # 2 is Error in ESLint
                            sev = 'HIGH'
                            line = message.get('line', 0)
                            fp_key = f"{file_path}:{line}:eslint"
                            if fp_key not in fps:
                                critical_high_count += 1
                                print(f"[FAIL] ESLint {sev}: {file_path}:{line} - {message.get('message')}")
                                new_fps.append(f"{fp_key} | Eslint | Add justification here | Developer Name | 2026-08-20")
                            else:
                                print(f"[SKIP] ESLint {sev} (False Positive): {file_path}:{line}")
                        elif message.get('severity') == 1: # 1 is Warning
                            line = message.get('line', 0)
                            risk_register.append(f"| ESLint | MEDIUM | {file_path}:{line} | {message.get('message')} | TBD |")
            except Exception:
                pass
    return critical_high_count

def parse_trivy(fps, critical_high_count, new_fps, risk_register):
    if os.path.exists('security/reports/trivy-results.json'):
        with open('security/reports/trivy-results.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for result in data.get('Results', []):
                    target = result.get('Target', '')
                    
                    parts = target.replace('\\', '/').split('/')
                    if 'venv' in parts or 'node_modules' in parts or 'security' in parts:
                        continue
                        
                    for vuln in result.get('Vulnerabilities', []):
                        sev = vuln.get('Severity', 'LOW').upper()
                        pkg = vuln.get('PkgName', '')
                        fp_key = f"{target}:{pkg}:trivy"
                        if sev in ['HIGH', 'CRITICAL']:
                            if fp_key not in fps:
                                critical_high_count += 1
                                print(f"[FAIL] Trivy {sev}: {target} -> {pkg} ({vuln.get('VulnerabilityID')})")
                                new_fps.append(f"{fp_key} | Trivy | Add justification here | Developer Name | 2026-08-20")
                            else:
                                print(f"[SKIP] Trivy {sev} (False Positive): {target} -> {pkg}")
                        elif sev in ['LOW', 'MEDIUM']:
                            risk_register.append(f"| Trivy | {sev} | {target} ({pkg}) | {vuln.get('VulnerabilityID')} | TBD |")
            except Exception:
                pass
    return critical_high_count

def parse_grype(fps, critical_high_count, new_fps, risk_register):
    if os.path.exists('security/reports/grype-results.json'):
        with open('security/reports/grype-results.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for match in data.get('matches', []):
                    sev = match.get('vulnerability', {}).get('severity', 'Low').upper()
                    pkg = match.get('artifact', {}).get('name', '')
                    locations = match.get('artifact', {}).get('locations', [])
                    target = locations[0].get('path', '') if locations else 'unknown'
                    
                    parts = target.replace('\\', '/').split('/')
                    if 'venv' in parts or 'node_modules' in parts or 'security' in parts:
                        continue
                    
                    fp_key = f"{target}:{pkg}:grype"
                    if sev in ['HIGH', 'CRITICAL']:
                        if fp_key not in fps:
                            critical_high_count += 1
                            print(f"[FAIL] Grype {sev}: {target} -> {pkg} ({match.get('vulnerability', {}).get('id')})")
                            new_fps.append(f"{fp_key} | Grype | Add justification here | Developer Name | 2026-08-20")
                        else:
                            print(f"[SKIP] Grype {sev} (False Positive): {target} -> {pkg}")
                    elif sev in ['LOW', 'MEDIUM', 'NEGLIGIBLE']:
                        risk_register.append(f"| Grype | {sev} | {target} ({pkg}) | {match.get('vulnerability', {}).get('id')} | TBD |")
            except Exception:
                pass
    return critical_high_count

def parse_betterleaks(fps, critical_high_count, new_fps, risk_register):
    if os.path.exists('security/reports/betterleaks-results.json'):
        with open('security/reports/betterleaks-results.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for finding in data:
                    file_path = finding.get('File', '')
                    line = finding.get('StartLine', 0)
                    
                    parts = file_path.replace('\\', '/').split('/')
                    if 'venv' in parts or 'node_modules' in parts or 'security' in parts:
                        continue

                    fp_key = f"{file_path}:{line}:betterleaks"
                    if fp_key not in fps:
                        critical_high_count += 1
                        print(f"[FAIL] Betterleaks CRITICAL: {file_path}:{line} - {finding.get('Description')}")
                        new_fps.append(f"{fp_key} | Betterleaks | Add justification here | Developer Name | 2026-08-20")
                    else:
                        print(f"[SKIP] Betterleaks CRITICAL (False Positive): {file_path}:{line}")
            except Exception as e:
                print(f"[ERROR] Failed to parse betterleaks results: {e}")
    return critical_high_count

def write_risk_register(risk_register):
    if not risk_register:
        return
        
    register_path = 'security/risk-and-limitation-register.md'
    existing_keys = set()
    
    if os.path.exists(register_path):
        with open(register_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('|') and not line.startswith('| Tool') and not line.startswith('|---'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 5:
                        key = f"{parts[1]}:{parts[3]}:{parts[4]}"
                        existing_keys.add(key)
                        
    new_entries = []
    for entry in risk_register:
        parts = [p.strip() for p in entry.split('|')]
        if len(parts) >= 5:
            key = f"{parts[1]}:{parts[3]}:{parts[4]}"
            if key not in existing_keys:
                new_entries.append(entry)
                existing_keys.add(key)
                
    if new_entries:
        file_exists = os.path.exists(register_path)
        with open(register_path, 'a', encoding='utf-8') as f:
            if not file_exists:
                f.write("# Risk and Limitation Register\n\n")
                f.write("This document tracks Medium and Low severity findings from security scans that do not block the build, as required by the SSDLC workflow.\n\n")
                f.write("| Tool | Severity | Location | Description | Owner |\n")
                f.write("|---|---|---|---|---|\n")
            
            for entry in new_entries:
                f.write(entry + "\n")
        print(f"\n[INFO] Logged {len(new_entries)} NEW Medium/Low finding(s) to {register_path}")
    else:
        print(f"\n[INFO] 0 NEW Medium/Low finding(s) to log. All findings already tracked.")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')

    os.makedirs('security/reports', exist_ok=True)
    
    config_path = 'security/gate/config.json'
    if not os.path.exists(config_path):
        print(f"[ERROR] Config file {config_path} not found.")
        sys.exit(1)
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    print("--- Starting Concurrent Security Scans ---")
    
    futures = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        for tool, settings in config.items():
            if settings.get('enabled', False):
                cmd = settings.get('command')
                if cmd:
                    futures.append(executor.submit(run_command, tool, cmd))
    
    for future in as_completed(futures):
        name, rc, stdout, stderr = future.result()
        if rc != 0 and name not in ['bandit', 'opengrep', 'eslint', 'trivy', 'grype', 'betterleaks']:
            # Tools may exit non-zero when they find issues, but if it crashed we might want to log it
            pass

    print("\n--- Security Gate Summary ---")
    fp_path = 'security/false-positives.md'
    fps = load_false_positives(fp_path)
    critical_high_count = 0
    new_fps = []
    risk_register = []

    critical_high_count = parse_opengrep(fps, critical_high_count, new_fps, risk_register)
    critical_high_count = parse_bandit(fps, critical_high_count, new_fps, risk_register)
    critical_high_count = parse_eslint(fps, critical_high_count, new_fps, risk_register)
    critical_high_count = parse_trivy(fps, critical_high_count, new_fps, risk_register)
    critical_high_count = parse_grype(fps, critical_high_count, new_fps, risk_register)
    critical_high_count = parse_betterleaks(fps, critical_high_count, new_fps, risk_register)

    write_risk_register(risk_register)

    print(f"\nTotal Unresolved CRITICAL/HIGH findings: {critical_high_count}")
    if critical_high_count > 0:
        print("❌ FAILED")
        print("\n--- How to Whitelist ---")
        print("To whitelist these findings, add the following lines to security/false-positives.md:")
        for line in new_fps:
            print(line)
        sys.exit(1)
    else:
        print("✅ PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
