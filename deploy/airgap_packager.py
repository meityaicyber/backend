"""Air-Gapped Packager and Integrity Manifest Generator.

Computes cryptographic SHA-256 checksums for all source files, configurations, datasets,
and tests, producing an immutable manifest for air-gapped custody transfer.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent


def hash_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    hasher.update(file_path.read_bytes())
    return hasher.hexdigest()


def build_airgap_manifest(output_path: Path = ROOT_DIR / "deploy" / "airgap_manifest.json") -> dict[str, Any]:
    """Generate air-gapped integrity manifest."""
    tracked_directories = ["config", "data", "src", "deploy", "tests", "docs"]
    manifest_entries: list[dict[str, Any]] = []

    for dir_name in tracked_directories:
        d_path = ROOT_DIR / dir_name
        if not d_path.exists():
            continue
        for f in sorted(d_path.rglob("*")):
            if f.is_file() and not f.name.endswith(".pyc") and "__pycache__" not in str(f) and f.name != "airgap_manifest.json":
                rel_path = f.relative_to(ROOT_DIR).as_posix()
                manifest_entries.append({
                    "path": rel_path,
                    "sha256": hash_file(f),
                    "size_bytes": f.stat().st_size,
                })

    # Include root files
    for root_file in ["README.md", "requirements.txt", "config.json"]:
        rf_path = ROOT_DIR / root_file
        if rf_path.exists():
            manifest_entries.append({
                "path": root_file,
                "sha256": hash_file(rf_path),
                "size_bytes": rf_path.stat().st_size,
            })

    payload = {
        "manifest_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(manifest_entries),
        "target_environment": "Air-Gapped Secure Enclave",
        "verification_method": "SHA-256 Digest",
        "entries": manifest_entries,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    res = build_airgap_manifest()
    print(f"Air-gapped manifest generated: {res['total_files']} files hashed.")
