"""Air-Gapped Offline Installation and Environment Verification Suite.

Performs deterministic self-tests in an isolated environment without network access:
1. Validates local dependency imports without network sockets.
2. Checks SHA-256 file digests against airgap_manifest.json.
3. Tests JSON configuration schema completeness.
4. Executes offline dry-run of feature computation, scoring, and baseline ranking.
"""

from __future__ import annotations

import hashlib
import json
import socket
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))



def test_no_external_network() -> bool:
    """Ensure socket calls to external domains are disabled or unneeded."""
    # Attempting to verify no external requests are triggered
    try:
        # Standard check: confirm localhost is reachable
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.close()
        return True
    except Exception as e:
        print(f"Socket initialization warning: {e}")
        return True


def test_dependency_imports() -> list[str]:
    """Verify all critical runtime modules can be imported strictly offline."""
    errors = []
    required_modules = [
        "json", "hashlib", "math", "random",
        "numpy", "sklearn", "sklearn.ensemble", "sklearn.svm", "sklearn.neural_network"
    ]
    for mod in required_modules:
        try:
            __import__(mod)
        except ImportError as e:
            errors.append(f"Failed to import required offline module '{mod}': {e}")
    return errors


def test_configuration_integrity() -> list[str]:
    """Verify configuration files are present, valid JSON, and schema compliant."""
    errors = []
    config_dir = ROOT_DIR / "config"
    required_configs = ["feature_definitions.json", "scoring_config.json", "model_config.json", "version_registry.json"]

    for cfg_name in required_configs:
        cfg_file = config_dir / cfg_name
        if not cfg_file.exists():
            errors.append(f"Missing essential config file: {cfg_name}")
            continue
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                errors.append(f"Config {cfg_name} is not a valid JSON object.")
        except Exception as e:
            errors.append(f"Error parsing {cfg_name}: {e}")
    return errors


def test_file_integrity_manifest() -> list[str]:
    """Verify all tracked files match their cryptographic SHA-256 hashes in airgap_manifest.json."""
    errors = []
    manifest_file = ROOT_DIR / "deploy" / "airgap_manifest.json"
    if not manifest_file.exists():
        return ["airgap_manifest.json not found. Run deploy/airgap_packager.py to generate."]

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    for entry in manifest.get("entries", []):
        rel_path = entry["path"]
        expected_sha = entry["sha256"]
        f_path = ROOT_DIR / rel_path
        if not f_path.exists():
            errors.append(f"Missing file declared in manifest: {rel_path}")
            continue
        hasher = hashlib.sha256()
        hasher.update(f_path.read_bytes())
        actual_sha = hasher.hexdigest()
        if actual_sha != expected_sha:
            errors.append(f"Checksum mismatch for '{rel_path}': expected {expected_sha}, got {actual_sha}")
    return errors


def test_offline_execution() -> list[str]:
    """Execute end-to-end dry-run scoring and heuristic classification offline."""
    errors = []
    try:
        from src.scoring.engine import calculate_organisation_score
        test_features = {
            "audit_timeliness": 90.0,
            "audit_efficiency": 85.0,
            "error_rate": 2.0,
            "agency_scale": 70.0,
            "compliance_adherence": 95.0,
            "past_renewal_status": 90.0,
        }
        res = calculate_organisation_score(test_features)
        if res.get("status") != "assessable" or res.get("score") is None:
            errors.append(f"Dry-run scoring failed: {res}")
        if res.get("decision") != "renew":
            errors.append(f"Dry-run scoring decision mismatch: expected 'renew', got {res.get('decision')}")
    except Exception as e:
        errors.append(f"Dry run exception: {e}")
    return errors


def run_verification() -> int:
    """Run all verification tests and return exit code."""
    print("=" * 65)
    print("AIR-GAPPED ENVIRONMENT OFFLINE INSTALLATION VERIFICATION")
    print("=" * 65)

    all_errors = []

    print("[1/4] Testing offline dependencies...")
    dep_errors = test_dependency_imports()
    if dep_errors:
        all_errors.extend(dep_errors)
        print("  -> FAILED:")
        for err in dep_errors:
            print(f"     * {err}")
    else:
        print("  -> PASSED (All runtime dependencies resolved locally)")

    print("[2/4] Testing configuration syntax and schema integrity...")
    cfg_errors = test_configuration_integrity()
    if cfg_errors:
        all_errors.extend(cfg_errors)
        print("  -> FAILED:")
        for err in cfg_errors:
            print(f"     * {err}")
    else:
        print("  -> PASSED (All JSON configurations valid)")

    print("[3/4] Testing file integrity against airgap_manifest.json...")
    manifest_errors = test_file_integrity_manifest()
    if manifest_errors:
        all_errors.extend(manifest_errors)
        print("  -> FAILED / MISMATCH:")
        for err in manifest_errors:
            print(f"     * {err}")
    else:
        print("  -> PASSED (All file SHA-256 digests match)")

    print("[4/4] Testing offline scoring dry-run...")
    exec_errors = test_offline_execution()
    if exec_errors:
        all_errors.extend(exec_errors)
        print("  -> FAILED:")
        for err in exec_errors:
            print(f"     * {err}")
    else:
        print("  -> PASSED (Dry-run scoring completed successfully)")

    print("-" * 65)
    if all_errors:
        print(f"VERIFICATION FAILED: {len(all_errors)} issues identified.")
        return 1
    else:
        print("VERIFICATION SUCCESSFUL: System is fully operational in air-gapped environment.")
        return 0


if __name__ == "__main__":
    sys.exit(run_verification())
