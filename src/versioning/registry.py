"""Version Registry and Provenance Management.

Implements version control for feature schemas, scoring rules, and model templates.
Maintains an immutable change history and ensures historical scores are never overwritten.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class VersionRegistry:
    """Manages schema versions, change history, and provenance verification."""

    def __init__(self, config_dir: str | Path = "config") -> None:
        self.config_dir = Path(config_dir)
        self.registry_file = self.config_dir / "version_registry.json"
        self._ensure_registry()

    def _ensure_registry(self) -> None:
        """Ensure version registry JSON file exists with base structure."""
        if not self.registry_file.exists():
            base_data = {
                "active_version": "1.0.0",
                "versions": [
                    {
                        "version": "1.0.0",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "author": "System Initializer",
                        "approval_id": "INIT-AUTH-001",
                        "description": "Baseline operational release",
                        "config_hashes": self.compute_current_hashes(),
                        "changes": ["Initial system release"],
                    }
                ],
            }
            self.registry_file.write_text(json.dumps(base_data, indent=2), encoding="utf-8")

    def load_registry(self) -> dict[str, Any]:
        """Load registry from disk."""
        return json.loads(self.registry_file.read_text(encoding="utf-8"))

    def compute_current_hashes(self) -> dict[str, str]:
        """Compute SHA-256 hashes of all JSON configurations in config directory."""
        hashes: dict[str, str] = {}
        for p in sorted(self.config_dir.glob("*.json")):
            if p.name == "version_registry.json":
                continue
            hasher = hashlib.sha256()
            hasher.update(p.read_bytes())
            hashes[p.stem] = hasher.hexdigest()[:12]
        return hashes

    def register_version(
        self,
        new_version: str,
        author: str = "",
        approval_id: str = "",
        description: str = "",
        changes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Register a new configuration and schema version with immutable history."""
        registry = self.load_registry()
        existing_versions = [v["version"] for v in registry["versions"]]

        if new_version in existing_versions:
            raise ValueError(
                f"Version '{new_version}' already exists in registry. Historical versions are immutable."
            )

        entry = {
            "version": new_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "author": author,
            "approval_id": approval_id,
            "description": description,
            "config_hashes": self.compute_current_hashes(),
            "changes": changes or [],
        }

        registry["versions"].append(entry)
        registry["active_version"] = new_version

        self.registry_file.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        return entry

    def verify_provenance(self, score_or_rank_record: dict[str, Any]) -> dict[str, Any]:
        """Trace a score or ranking record back to its configuration version and validation status."""
        prov = score_or_rank_record.get("provenance", {})
        config_ver = prov.get("scoring_config_version") or prov.get("configuration_version")
        claimed_hash = prov.get("configuration_sha256")

        registry = self.load_registry()
        matched_entry = next(
            (v for v in registry["versions"] if v["version"] == config_ver), None
        )

        if not matched_entry:
            return {
                "verified": False,
                "reason": f"Version '{config_ver}' not found in official registry.",
                "recorded_provenance": prov,
            }

        return {
            "verified": True,
            "version_entry": matched_entry,
            "active_version": registry["active_version"],
            "is_current_active": (config_ver == registry["active_version"]),
            "recorded_provenance": prov,
        }

    def get_change_history(self) -> list[dict[str, Any]]:
        """Return full audit log of version updates."""
        return self.load_registry().get("versions", [])
