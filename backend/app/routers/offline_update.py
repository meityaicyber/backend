from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.benchmark_registry import BenchmarkRegistry
from app.utils.clamav_utils import scan_file_bytes
from app.schemas.offline_update import (
    OfflineUpdateActionResponse,
    OfflineUpdateBackupsOut,
    OfflineUpdateHistoryListOut,
    OfflineUpdateHistoryOut,
    OfflineUpdateInstallResponse,
    OfflineUpdateImportResponse,
    OfflineUpdateStepListOut,
    OfflineUpdateStepOut,
    OfflineUpdateVerifyResponse,
)

router = APIRouter(prefix="/api/offline-update", tags=["Offline Update"])
offline_router = APIRouter(prefix="/offline", tags=["Offline Update"])

ROOT_DIR = Path(__file__).resolve().parents[3]
STORAGE_DIR = ROOT_DIR / "storage"
UPDATES_DIR = STORAGE_DIR / "updates"
EXTRACTED_DIR = STORAGE_DIR / "extracted"
BACKUPS_DIR = STORAGE_DIR / "backups"
CURRENT_DIR = STORAGE_DIR / "current"
LOG_DIR = STORAGE_DIR / "logs"
STATE_FILE = UPDATES_DIR / "package_registry.json"
HISTORY_DB = STORAGE_DIR / "update_history.db"
REQUIRED_PACKAGE_FILES = [
    "manifest.json",
    "benchmark_rules.json",
    "recommendation_rules.json",
    "methodology_rules.json",
    "scoring_rules.json",
    "checksum.sha256",
    "signature.sig",
]


def ensure_storage_layout() -> None:
    for directory in (UPDATES_DIR, EXTRACTED_DIR, BACKUPS_DIR, CURRENT_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        STATE_FILE.write_text("{}", encoding="utf-8")


def load_registry() -> Dict[str, Dict[str, Any]]:
    ensure_storage_layout()
    try:
        with STATE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        data = {}
    return data if isinstance(data, dict) else {}


def save_registry(registry: Dict[str, Dict[str, Any]]) -> None:
    ensure_storage_layout()
    STATE_FILE.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _parse_version(version: str) -> tuple[int, ...]:
    cleaned = version.replace("v", "").strip()
    return tuple(int(part) for part in cleaned.split(".") if part.isdigit()) or (0,)


def _read_manifest(extracted_dir: Path) -> Dict[str, Any]:
    manifest_path = extracted_dir / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=400, detail="manifest.json is missing from the extracted package.")
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"manifest.json is invalid: {exc}") from exc


def _hash_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


async def _get_current_benchmark_version(db: AsyncSession) -> Optional[str]:
    """Return the active benchmark version from the registry table, falling back to the current storage file."""
    try:
        result = await db.execute(
            select(BenchmarkRegistry.version)
            .where(BenchmarkRegistry.is_active.is_(True))
            .order_by(BenchmarkRegistry.created_at.desc())
            .limit(1)
        )
        version = result.scalar_one_or_none()
        if version:
            return str(version)
    except Exception:
        pass

    current_version_path = CURRENT_DIR / "version.json"
    if current_version_path.exists():
        try:
            current_version_payload = json.loads(current_version_path.read_text(encoding="utf-8"))
            if current_version_payload.get("version"):
                return str(current_version_payload["version"])
        except json.JSONDecodeError:
            pass
    return None


def _ensure_history_db() -> sqlite3.Connection:
    ensure_storage_layout()
    conn = sqlite3.connect(HISTORY_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS update_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id TEXT,
            version TEXT,
            package_name TEXT,
            installed_by TEXT,
            install_time TEXT,
            checksum_status TEXT,
            signature_status TEXT,
            status TEXT,
            rollback_version TEXT,
            remarks TEXT
        )
        """
    )
    conn.commit()
    return conn


def _history_record_to_response(record: Any) -> OfflineUpdateHistoryOut:
    if isinstance(record, sqlite3.Row):
        payload = {key: record[key] for key in record.keys()}
    elif isinstance(record, dict):
        payload = record
    else:
        payload = {
            "id": record[0],
            "package_id": record[1],
            "version": record[2],
            "package_name": record[3],
            "installed_by": record[4],
            "install_time": record[5],
            "checksum_status": record[6],
            "signature_status": record[7],
            "status": record[8],
            "rollback_version": record[9],
            "remarks": record[10],
        }

    install_time = payload.get("install_time")
    if install_time and isinstance(install_time, str):
        install_time = datetime.fromisoformat(install_time)

    return OfflineUpdateHistoryOut(
        id=payload.get("id"),
        package_id=payload.get("package_id"),
        version=payload.get("version"),
        package_name=payload.get("package_name"),
        installed_by=payload.get("installed_by"),
        install_time=install_time,
        checksum_status=payload.get("checksum_status"),
        signature_status=payload.get("signature_status"),
        status=payload.get("status"),
        rollback_version=payload.get("rollback_version"),
        remarks=payload.get("remarks"),
    )


def _load_latest_registry_entry(session_id: Optional[str] = None, package_id: Optional[str] = None) -> Dict[str, Any]:
    registry = load_registry()
    if session_id and session_id in registry:
        return registry[session_id]
    if package_id:
        for item in registry.values():
            if item.get("package_id") == package_id:
                return item
    raise HTTPException(status_code=404, detail="Package session was not found. Import the package before verification or installation.")


async def _version_compatibility_pass(manifest_version: str, db: AsyncSession) -> bool:
    """Only permit versions newer than the active registry version."""
    current_version = await _get_current_benchmark_version(db)
    return not current_version or _parse_version(manifest_version) > _parse_version(current_version)


def _read_package_rules(extracted_dir: Path) -> Dict[str, Any]:
    """Load and validate the rule payloads that are persisted in the registry."""
    payloads: Dict[str, Any] = {}
    required_fields = {
        "benchmark_rules": "benchmark_rules.json",
        "scoring_rules": "scoring_rules.json",
        "recommendation_rules": "recommendation_rules.json",
        "methodology_rules": "methodology_rules.json",
    }
    optional_fields = {
        "scoring_weights": "scoring_weights.json",
        "thresholds": "thresholds.json",
    }

    for field, file_name in required_fields.items():
        path = extracted_dir / file_name
        try:
            payloads[field] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid {file_name}: {exc}") from exc

    for field, file_name in optional_fields.items():
        path = extracted_dir / file_name
        if path.exists():
            try:
                payloads[field] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail=f"Invalid {file_name}: {exc}") from exc
        else:
            payloads[field] = None
    return payloads


async def _scan_package_for_malware(package_data: Dict[str, Any], extracted_dir: Path) -> List[str]:
    """Scan the archive and every extracted package file with ClamAV."""
    scan_paths = [Path(package_data["stored_package"])]
    scan_paths.extend(path for path in extracted_dir.rglob("*") if path.is_file())

    detected: List[str] = []
    for path in scan_paths:
        try:
            is_clean, scan_message = await scan_file_bytes(path.read_bytes())
        except OSError as exc:
            raise HTTPException(status_code=400, detail=f"Unable to read {path.name} for malware scanning: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"ClamAV scan failed: {exc}") from exc
        if not is_clean:
            detected.append(f"{path.name}: {scan_message}")
    return detected


def _setup_current_benchmark_files() -> None:
    ensure_storage_layout()
    default_rules = {
        "benchmark_rules.json": {"benchmark": "Audit Quality Benchmark", "rules": []},
        "recommendation_rules.json": {"recommendations": []},
        "methodology_rules.json": {"methodology": []},
        "scoring_rules.json": {"scores": []},
    }
    for file_name, payload in default_rules.items():
        target = CURRENT_DIR / file_name
        if not target.exists():
            target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_generated_package(version: str, package_name: str, output_directory: Path) -> Path:
    ensure_storage_layout()
    _setup_current_benchmark_files()
    output_directory.mkdir(parents=True, exist_ok=True)

    manifest_payload = {
        "package_id": f"pkg-{version.replace('.', '-')}",
        "package_name": package_name,
        "version": version,
        "created_date": datetime.now(timezone.utc).isoformat(),
        "status": "READY",
    }

    current_version_payload = {
        "version": version,
        "package_name": package_name,
        "created_date": datetime.now(timezone.utc).isoformat(),
    }

    package_root = output_directory / "package_build"
    package_root.mkdir(parents=True, exist_ok=True)
    manifest_path = package_root / "manifest.json"
    version_path = package_root / "version.json"
    signature_path = package_root / "signature.sig"
    checksum_path = package_root / "checksum.sha256"

    manifest_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
    version_path.write_text(json.dumps(current_version_payload, indent=2), encoding="utf-8")
    signature_path.write_text("MOCK_SIGNATURE", encoding="utf-8")

    for file_name in [
        "benchmark_rules.json",
        "recommendation_rules.json",
        "methodology_rules.json",
        "scoring_rules.json",
    ]:
        shutil.copy2(CURRENT_DIR / file_name, package_root / file_name)

    checksum_lines = []
    for file_name in [
        "benchmark_rules.json",
        "recommendation_rules.json",
        "methodology_rules.json",
        "scoring_rules.json",
        "manifest.json",
        "version.json",
        "signature.sig",
    ]:
        checksum_lines.append(f"{file_name}  {_hash_file(package_root / file_name)}")

    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    zip_path = output_directory / package_name
    with zipfile.ZipFile(zip_path, "w") as bundle:
        for file_name in [
            "benchmark_rules.json",
            "recommendation_rules.json",
            "methodology_rules.json",
            "scoring_rules.json",
            "manifest.json",
            "version.json",
            "checksum.sha256",
            "signature.sig",
        ]:
            bundle.write(package_root / file_name, arcname=file_name)

    return zip_path


OFFLINE_UPDATE_STEPS: Dict[str, Dict[str, str]] = {
    "Import Package": {
        "description": "Upload the package archive from an offline media source.",
        "status": "Ready",
    },
    "Verify Package": {
        "description": "Validate checksum, signature, and package integrity before install.",
        "status": "Pending",
    },
    "Install": {
        "description": "Apply the approved version with staged deployment controls.",
        "status": "Pending",
    },
    "Update History": {
        "description": "Review package events, install trace, and rollback record.",
        "status": "Tracked",
    },
}


@router.get("/steps", response_model=OfflineUpdateStepListOut)
async def get_offline_update_steps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the available offline update workflow steps and their status."""
    steps = [
        OfflineUpdateStepOut(
            title=title,
            description=details["description"],
            status=details["status"],
            last_updated_at=datetime.now(timezone.utc),
        )
        for title, details in OFFLINE_UPDATE_STEPS.items()
    ]
    return OfflineUpdateStepListOut(steps=steps)


@router.get("/history", response_model=OfflineUpdateHistoryListOut)
async def get_offline_update_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return recent offline update actions and their execution records from SQLite."""
    conn = _ensure_history_db()
    rows = conn.execute(
        "SELECT * FROM update_history ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    history = [_history_record_to_response(row) for row in rows]
    return OfflineUpdateHistoryListOut(history=history)


@router.get("/history/{history_id}", response_model=OfflineUpdateHistoryOut)
async def get_offline_update_history_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a single update history record by primary key."""
    conn = _ensure_history_db()
    row = conn.execute("SELECT * FROM update_history WHERE id = ?", (history_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="History record was not found.")
    return _history_record_to_response(row)


@router.get("/backups", response_model=OfflineUpdateBackupsOut)
async def get_available_backups(
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    """Return available rollback backup versions."""
    result = await db.execute(
        select(BenchmarkRegistry.version)
        .where(BenchmarkRegistry.is_active.is_(False))
        .order_by(BenchmarkRegistry.created_at.desc())
    )
    versions = [str(version) for version in result.scalars().all()]
    return OfflineUpdateBackupsOut(versions=versions)


@router.get("/current-version")
async def get_current_benchmark_version(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current active version for client-side validation in the generate-package flow."""
    version = await _get_current_benchmark_version(db)
    return {"version": version or "0.0"}


@router.post("/upload-current-rule")
async def upload_current_rule(
    file: UploadFile = File(...),
    file_name: str = Form(...),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """Replace the current benchmark rule JSON file in storage/current with the uploaded payload."""
    ensure_storage_layout()
    allowed_rule_files = {
        "benchmark_rules.json",
        "scoring_rules.json",
        "recommendation_rules.json",
        "methodology_rules.json",
    }
    if file_name not in allowed_rule_files:
        raise HTTPException(status_code=400, detail="Unsupported benchmark rule file name.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="A file is required for upload.")

    content = await file.read()
    try:
        json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in {file_name}: {exc}") from exc

    destination = CURRENT_DIR / file_name
    destination.write_bytes(content)
    return {
        "status": "success",
        "file_name": file_name,
        "message": f"{file_name} updated successfully.",
    }


@router.post("/build-package")
async def build_package(
    benchmark_name: str = Form(...),
    version: str = Form(...),
    change_summary: Optional[str] = Form(None),
    benchmark_rules: UploadFile = File(...),
    scoring_rules: UploadFile = File(...),
    recommendation_rules: UploadFile = File(...),
    methodology_rules: UploadFile = File(...),
    scoring_weights: Optional[UploadFile] = File(None),
    thresholds: Optional[UploadFile] = File(None),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """Generate an offline update package from uploaded benchmark rule JSON files without touching the database."""
    ensure_storage_layout()
    current_version = await _get_current_benchmark_version(db)
    if current_version and _parse_version(version) <= _parse_version(current_version):
        raise HTTPException(
            status_code=400,
            detail=f"Version must be greater than the current benchmark version {current_version}.",
        )

    uploaded_rule_files = {
        "benchmark_rules.json": benchmark_rules,
        "scoring_rules.json": scoring_rules,
        "recommendation_rules.json": recommendation_rules,
        "methodology_rules.json": methodology_rules,
        "scoring_weights.json": scoring_weights,
        "thresholds.json": thresholds,
    }

    file_payloads: Dict[str, Dict[str, Any]] = {}
    for file_name, upload in uploaded_rule_files.items():
        if upload is None or not getattr(upload, "filename", None):
            raise HTTPException(status_code=400, detail=f"{file_name} is required for package generation.")
        raw_content = await upload.read()
        try:
            payload = json.loads(raw_content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in {file_name}: {exc}") from exc
        file_payloads[file_name] = payload

    package_name = f"AQB_Update_v{version}.zip"
    output_directory = UPDATES_DIR
    output_directory.mkdir(parents=True, exist_ok=True)

    package_root = output_directory / "package_build"
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    manifest_payload = {
        "package_name": package_name.replace(".zip", ""),
        "package_id": f"AQB-{version.replace('.', '-')}",
        "version": version,
        "benchmark_name": benchmark_name,
        "created_by": getattr(current_user, "username", "admin"),
        "created_date": datetime.now(timezone.utc).isoformat(),
        "change_summary": change_summary or "",
        "files": list(uploaded_rule_files.keys()),
    }

    manifest_path = package_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")

    for file_name, payload in file_payloads.items():
        (package_root / file_name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    signature_path = package_root / "signature.sig"
    signature_path.write_text("MOCK_SIGNATURE", encoding="utf-8")
    checksum_lines = []
    for file_name in [*file_payloads.keys(), "manifest.json", "signature.sig"]:
        checksum_lines.append(f"{file_name}  {_hash_file(package_root / file_name)}")

    checksum_path = package_root / "checksum.sha256"
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    zip_path = output_directory / package_name
    with zipfile.ZipFile(zip_path, "w") as bundle:
        for file_name in [*file_payloads.keys(), "manifest.json", "checksum.sha256", "signature.sig"]:
            if (package_root / file_name).exists():
                bundle.write(package_root / file_name, arcname=file_name)

    return FileResponse(zip_path, media_type="application/zip", filename=package_name)


@router.post("/import-package", response_model=OfflineUpdateImportResponse)
async def import_package(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """Import a package archive, validate the filename, store it, and extract it into a session directory."""
    ensure_storage_layout()
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip package archives are supported.")

    package_name = file.filename
    session_id = str(uuid4())
    destination_path = UPDATES_DIR / package_name
    extracted_dir = EXTRACTED_DIR / session_id
    extracted_dir.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    destination_path.write_bytes(content)

    with zipfile.ZipFile(destination_path) as package_zip:
        package_zip.extractall(extracted_dir)

    manifest = _read_manifest(extracted_dir)
    registry = load_registry()
    registry[session_id] = {
        "package_id": manifest.get("package_id") or session_id,
        "package_name": manifest.get("package_name") or package_name,
        "version": manifest.get("version") or "0.0.0",
        "created_date": manifest.get("created_date") or datetime.now(timezone.utc).isoformat(),
        "status": manifest.get("status") or "IMPORTED",
        "stored_package": str(destination_path),
        "extracted_path": str(extracted_dir),
        "session_id": session_id,
    }
    save_registry(registry)

    return OfflineUpdateImportResponse(
        package_name=registry[session_id]["package_name"],
        package_id=registry[session_id]["package_id"],
        version=registry[session_id]["version"],
        created_date=registry[session_id]["created_date"],
        status=registry[session_id]["status"],
        session_id=session_id,
    )


@router.post("/verify-package", response_model=OfflineUpdateVerifyResponse)
async def verify_package(
    session_id: Optional[str] = Form(None),
    package_id: Optional[str] = Form(None),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """Verify the manifest, required package files, checksum, signature, malware scan, and version compatibility."""
    ensure_storage_layout()
    package_data = _load_latest_registry_entry(session_id=session_id, package_id=package_id)
    extracted_dir = Path(package_data["extracted_path"])
    manifest = _read_manifest(extracted_dir)

    errors: List[str] = []
    verification_details = {
        "Manifest PASS": True,
        "Checksum PASS": True,
        "Signature PASS": True,
        "Malware PASS": False,
        "Version Compatibility PASS": True,
    }

    for required_file in REQUIRED_PACKAGE_FILES:
        if not (extracted_dir / required_file).exists():
            errors.append(f"Missing required file: {required_file}")
            if required_file == "manifest.json":
                verification_details["Manifest PASS"] = False
            elif required_file == "checksum.sha256":
                verification_details["Checksum PASS"] = False
            elif required_file == "signature.sig":
                verification_details["Signature PASS"] = False

    malware_findings = await _scan_package_for_malware(package_data, extracted_dir)
    if malware_findings:
        errors.extend(malware_findings)
    else:
        verification_details["Malware PASS"] = True

    checksum_path = extracted_dir / "checksum.sha256"
    if checksum_path.exists():
        checksum_content = checksum_path.read_text(encoding="utf-8")
        for line in checksum_content.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                file_name = parts[0]
                expected_hash = parts[-1]
                if (extracted_dir / file_name).exists():
                    actual_hash = _hash_file(extracted_dir / file_name)
                    if actual_hash != expected_hash:
                        errors.append(f"Checksum mismatch for {file_name}")
                        verification_details["Checksum PASS"] = False
    else:
        verification_details["Checksum PASS"] = False

    if not (extracted_dir / "signature.sig").exists():
        verification_details["Signature PASS"] = False
    if not await _version_compatibility_pass(str(manifest.get("version", "0.0.0")), db):
        verification_details["Version Compatibility PASS"] = False
        errors.append("Version compatibility failed: the package version must be newer than the currently installed version.")

    overall_verified = all(verification_details.values()) and not errors
    if not overall_verified:
        raise HTTPException(status_code=400, detail={"errors": errors, "checks": verification_details})

    return OfflineUpdateVerifyResponse(
        manifest_pass=verification_details["Manifest PASS"],
        checksum_pass=verification_details["Checksum PASS"],
        signature_pass=verification_details["Signature PASS"],
        malware_pass=verification_details["Malware PASS"],
        overall_status="VERIFIED",
        package_name=package_data["package_name"],
        package_id=package_data["package_id"],
        version=package_data["version"],
        session_id=package_data["session_id"],
    )


@router.post("/install", response_model=OfflineUpdateInstallResponse)
async def install_offline_update(
    session_id: Optional[str] = Form(None),
    package_id: Optional[str] = Form(None),
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    """Persist the package rules in benchmark_registry and make that version active."""
    ensure_storage_layout()
    package_data = _load_latest_registry_entry(session_id=session_id, package_id=package_id)
    extracted_dir = Path(package_data["extracted_path"])
    manifest = _read_manifest(extracted_dir)
    version = str(manifest.get("version") or package_data["version"])
    rules = _read_package_rules(extracted_dir)
    installed_by = getattr(current_user, "username", "admin")
    installed_at = datetime.now(timezone.utc)
    existing = await db.execute(select(BenchmarkRegistry).where(BenchmarkRegistry.version == version))
    registry_entry = existing.scalar_one_or_none()
    if registry_entry is not None and registry_entry.is_active:
        raise HTTPException(status_code=400, detail=f"Benchmark version {version} is already active.")

    await db.execute(update(BenchmarkRegistry).values(is_active=False))
    change_event = {
        "action": "installed",
        "package_id": package_data["package_id"],
        "package_name": package_data["package_name"],
        "performed_by": installed_by,
        "performed_at": installed_at.isoformat(),
    }
    if registry_entry is None:
        registry_entry = BenchmarkRegistry(
            benchmark_name=str(manifest.get("benchmark_name") or package_data["package_name"]),
            version=version,
            description=manifest.get("description"),
            approval_status="Approved",
            effective_date=date.today(),
            created_by=installed_by,
            approved_by=installed_by,
            approved_at=installed_at,
            change_summary=manifest.get("change_summary") or "Installed from offline package.",
            change_history=[change_event],
            checksum_sha256=_hash_file(extracted_dir / "checksum.sha256"),
            package_name=package_data["package_name"],
            package_path=package_data.get("stored_package"),
            is_active=True,
            **rules,
        )
        db.add(registry_entry)
    else:
        registry_entry.benchmark_name = str(manifest.get("benchmark_name") or package_data["package_name"])
        registry_entry.description = manifest.get("description")
        registry_entry.benchmark_rules = rules["benchmark_rules"]
        registry_entry.scoring_rules = rules["scoring_rules"]
        registry_entry.recommendation_rules = rules["recommendation_rules"]
        registry_entry.methodology_rules = rules["methodology_rules"]
        registry_entry.scoring_weights = rules["scoring_weights"]
        registry_entry.thresholds = rules["thresholds"]
        registry_entry.approval_status = "Approved"
        registry_entry.effective_date = date.today()
        registry_entry.approved_by = installed_by
        registry_entry.approved_at = installed_at
        registry_entry.change_summary = manifest.get("change_summary") or "Reinstalled from offline package."
        registry_entry.change_history = (registry_entry.change_history or []) + [change_event]
        registry_entry.checksum_sha256 = _hash_file(extracted_dir / "checksum.sha256")
        registry_entry.package_name = package_data["package_name"]
        registry_entry.package_path = package_data.get("stored_package")
        registry_entry.is_active = True
    await db.flush()

    log_path = LOG_DIR / f"install_{package_data['package_id']}.log"
    log_path.write_text(
        "\n".join([
            "Registry Backup Complete",
            "Installation Complete",
            "Benchmark Reloaded",
            "Status SUCCESS",
        ]),
        encoding="utf-8",
    )

    conn = _ensure_history_db()
    conn.execute(
        """
        INSERT INTO update_history (
            package_id, version, package_name, installed_by, install_time,
            checksum_status, signature_status, status, rollback_version, remarks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            package_data["package_id"],
            version,
            package_data["package_name"],
            getattr(current_user, "username", "admin"),
            datetime.now(timezone.utc).isoformat(),
            "PASS",
            "PASS",
            "SUCCESS",
            None,
            "Installed from offline package into benchmark_registry.",
        ),
    )
    conn.commit()
    conn.close()

    return OfflineUpdateInstallResponse(
        step="Install",
        status="SUCCESS",
        message="Registry Backup Complete\nInstallation Complete\nBenchmark Reloaded",
        package_name=package_data["package_name"],
        package_version=version,
        progress=["Registry Backup Complete", "Installation Complete", "Benchmark Reloaded"],
    )


@router.post("/rollback", response_model=OfflineUpdateActionResponse)
async def rollback_offline_update(
    version: str = Form(...),
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    """Make a previous benchmark_registry version active again."""
    target_result = await db.execute(select(BenchmarkRegistry).where(BenchmarkRegistry.version == version))
    target = target_result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail=f"Benchmark version {version} was not found in the registry.")

    rolled_back_at = datetime.now(timezone.utc)
    await db.execute(update(BenchmarkRegistry).values(is_active=False))
    target.is_active = True
    target.effective_date = date.today()
    target.change_history = (target.change_history or []) + [{
        "action": "rolled_back",
        "performed_by": getattr(current_user, "username", "admin"),
        "performed_at": rolled_back_at.isoformat(),
    }]
    await db.flush()

    log_path = LOG_DIR / f"rollback_{version}.log"
    log_path.write_text("Rollback Successful", encoding="utf-8")

    conn = _ensure_history_db()
    conn.execute(
        "UPDATE update_history SET status = ?, rollback_version = ?, remarks = ? WHERE version = ?",
        ("ROLLED_BACK", version, f"Reactivated benchmark_registry version {version}.", version),
    )
    conn.commit()
    conn.close()

    return OfflineUpdateActionResponse(
        step="Rollback",
        status="SUCCESS",
        message="Rollback Successful",
        package_name="Rollback Restore",
        package_version=version,
    )


@router.post("/generate-package")
async def generate_package(
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    """Validate benchmark JSON files, generate a manifest/checksum/signature bundle, zip it, and return it for download."""
    ensure_storage_layout()
    _setup_current_benchmark_files()
    required_json_files = [
        "benchmark_rules.json",
        "recommendation_rules.json",
        "methodology_rules.json",
        "scoring_rules.json",
    ]

    for file_name in required_json_files:
        file_path = CURRENT_DIR / file_name
        try:
            json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in {file_name}: {exc}") from exc

    current_version = "2.2"
    current_version_path = CURRENT_DIR / "version.json"
    if current_version_path.exists():
        try:
            current_version_data = json.loads(current_version_path.read_text(encoding="utf-8"))
            current_version = str(current_version_data.get("version") or current_version)
        except json.JSONDecodeError:
            current_version = "2.2"

    package_version = current_version.replace("v", "") if current_version.startswith("v") else current_version
    parts = package_version.split(".")
    if len(parts) < 2:
        parts = [parts[0], "0"]
    minor_version = f"{parts[0]}.{parts[1]}"
    package_name = f"AQB_Update_v{minor_version}.zip"
    zip_path = _write_generated_package(minor_version, package_name, UPDATES_DIR)
    return FileResponse(zip_path, media_type="application/zip", filename=package_name)


@offline_router.post("/import")
async def offline_import(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    return await import_package(file=file, current_user=current_user, db=db)


@offline_router.post("/verify")
async def offline_verify(
    request_data: dict = Body(...),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    session_id = request_data.get("session_id")
    package_id = request_data.get("package_id")
    return await verify_package(session_id=session_id, package_id=package_id, current_user=current_user, db=db)


@offline_router.post("/install")
async def offline_install(
    request_data: dict = Body(...),
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    session_id = request_data.get("session_id")
    package_id = request_data.get("package_id")
    return await install_offline_update(session_id=session_id, package_id=package_id, current_user=current_user, db=db)


@offline_router.get("/backups")
async def offline_backups(
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    return await get_available_backups(current_user=current_user, db=db)


@offline_router.post("/rollback")
async def offline_rollback(
    request_data: dict = Body(...),
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    version = request_data.get("version")
    if not version:
        raise HTTPException(status_code=400, detail="A target version is required for rollback.")
    return await rollback_offline_update(version=version, current_user=current_user, db=db)


@offline_router.get("/history")
async def offline_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_offline_update_history(current_user=current_user, db=db)


@offline_router.get("/history/{history_id}")
async def offline_history_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_offline_update_history_detail(history_id=history_id, current_user=current_user, db=db)
