"""FastAPI Backend for Auditing Agency Performance Monitoring and Ranking Module.

Exposes REST APIs for dashboard summaries, configuration inspection, real-time scoring,
evaluation benchmarks, provenance tracing, version registry, and interactive simulation.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from data.generator import AgencyDataGenerator
from src.feature_extractor import extract_features, is_raw_organisation
from src.models.pipeline import ModelPipeline
from src.scoring.engine import ScoringEngine
from src.scoring.ranking import RankingEngine, compute_config_hash
from src.versioning.registry import VersionRegistry

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
OUTPUT_DIR = ROOT_DIR / "output"
DATA_DIR = ROOT_DIR / "data"
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

app = FastAPI(
    title="Auditing Agency Performance Monitoring & Ranking API",
    description="Offline-ready AI-based performance monitoring and empanelment ranking system.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/")
def root():
    if (FRONTEND_DIST / "index.html").exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    return {
        "service": "Auditing Agency Performance Monitoring and Ranking API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "/api/health",
            "dashboard": "/api/dashboard",
            "ranking": "/api/ranking",
            "active_config": "/api/config/active",
            "evaluation_benchmarks": "/api/evaluation",
            "dataset": "/api/dataset",
            "version_history": "/api/config/history",
        },
    }


class ScoreRequest(BaseModel):
    organisation_id: str = "CUSTOM_AGENCY_SIM"
    features: dict[str, float | None]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agency-performance-monitoring-api", "version": "1.0.0"}


@app.get("/api/config/active")
def active_config() -> dict[str, Any]:
    registry = VersionRegistry(CONFIG_DIR)
    reg_data = registry.load_registry()
    return {
        "active_version": reg_data.get("active_version", "1.0.0"),
        "config_hash": compute_config_hash(CONFIG_DIR),
        "features": load_json_file(CONFIG_DIR / "feature_definitions.json"),
        "scoring": load_json_file(CONFIG_DIR / "scoring_config.json"),
        "models": load_json_file(CONFIG_DIR / "model_config.json"),
    }


@app.get("/api/config/features")
def features() -> dict[str, Any]:
    return load_json_file(CONFIG_DIR / "feature_definitions.json")


@app.get("/api/config/scoring")
def scoring_config() -> dict[str, Any]:
    return load_json_file(CONFIG_DIR / "scoring_config.json")


@app.get("/api/config/models")
def models_config() -> dict[str, Any]:
    return load_json_file(CONFIG_DIR / "model_config.json")


@app.get("/api/config/history")
def version_history() -> dict[str, Any]:
    registry = VersionRegistry(CONFIG_DIR)
    return {"versions": registry.get_change_history(), "active_version": registry.load_registry().get("active_version", "1.0.0")}


@app.post("/api/config/update-package")
def update_config_package(payload: dict[str, Any]) -> dict[str, Any]:
    """Update system configuration from a JSON package and register a new version."""
    version_str = payload.get("version", "").strip()
    if not version_str:
        raise HTTPException(status_code=400, detail="Version string is required (e.g. '1.1.0').")

    new_version = version_str
    registry = VersionRegistry(CONFIG_DIR)
    reg_data = registry.load_registry()
    existing = [v["version"] for v in reg_data.get("versions", [])]
    if new_version in existing:
        raise HTTPException(
            status_code=400,
            detail=f"Version '{new_version}' already exists in registry. Historical versions are immutable.",
        )

    updated_files = []
    if "scoring_config" in payload and payload["scoring_config"]:
        (CONFIG_DIR / "scoring_config.json").write_text(
            json.dumps(payload["scoring_config"], indent=2), encoding="utf-8"
        )
        updated_files.append("scoring_config.json")

    if "feature_definitions" in payload and payload["feature_definitions"]:
        (CONFIG_DIR / "feature_definitions.json").write_text(
            json.dumps(payload["feature_definitions"], indent=2), encoding="utf-8"
        )
        updated_files.append("feature_definitions.json")

    if "model_config" in payload and payload["model_config"]:
        (CONFIG_DIR / "model_config.json").write_text(
            json.dumps(payload["model_config"], indent=2), encoding="utf-8"
        )
        updated_files.append("model_config.json")

    entry = registry.register_version(
        new_version=new_version,
        description=payload.get("description") or "Configuration update package applied",
        changes=payload.get("changes") or [f"Updated config files: {', '.join(updated_files)}"],
    )

    return {
        "status": "success",
        "message": f"Configuration package v{new_version} applied and registered successfully.",
        "active_version": new_version,
        "updated_files": updated_files,
        "version_entry": entry,
    }


@app.post("/api/config/upload-package")
async def upload_config_package(
    file: UploadFile = File(...),
    version: str = Form(...),
    description: str = Form(""),
    changes: str = Form(""),
) -> dict[str, Any]:
    """Upload a ZIP file or JSON file package containing config files and register version."""
    if not version or not version.strip():
        raise HTTPException(status_code=400, detail="Version string is required (e.g. '1.1.0').")

    new_version = version.strip()
    registry = VersionRegistry(CONFIG_DIR)
    reg_data = registry.load_registry()
    existing = [v["version"] for v in reg_data.get("versions", [])]
    if new_version in existing:
        raise HTTPException(
            status_code=400,
            detail=f"Version '{new_version}' already exists in registry. Historical versions are immutable.",
        )

    contents = await file.read()
    updated_files: list[str] = []

    # Check if ZIP
    if file.filename and file.filename.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(contents)) as z:
                for filename in z.namelist():
                    basename = Path(filename).name
                    if basename in ["scoring_config.json", "feature_definitions.json", "model_config.json"]:
                        target = CONFIG_DIR / basename
                        target.write_bytes(z.read(filename))
                        updated_files.append(basename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract ZIP package: {str(e)}")
    elif file.filename and file.filename.endswith(".json"):
        try:
            parsed = json.loads(contents.decode("utf-8"))
            if "scoring_config" in parsed or "feature_definitions" in parsed or "model_config" in parsed:
                if "scoring_config" in parsed:
                    (CONFIG_DIR / "scoring_config.json").write_text(json.dumps(parsed["scoring_config"], indent=2), encoding="utf-8")
                    updated_files.append("scoring_config.json")
                if "feature_definitions" in parsed:
                    (CONFIG_DIR / "feature_definitions.json").write_text(json.dumps(parsed["feature_definitions"], indent=2), encoding="utf-8")
                    updated_files.append("feature_definitions.json")
                if "model_config" in parsed:
                    (CONFIG_DIR / "model_config.json").write_text(json.dumps(parsed["model_config"], indent=2), encoding="utf-8")
                    updated_files.append("model_config.json")
            else:
                # Single config file matching name
                basename = Path(file.filename).name
                if basename in ["scoring_config.json", "feature_definitions.json", "model_config.json"]:
                    (CONFIG_DIR / basename).write_text(json.dumps(parsed, indent=2), encoding="utf-8")
                    updated_files.append(basename)
                else:
                    raise HTTPException(status_code=400, detail=f"Unrecognized configuration file name '{basename}'.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse JSON configuration file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Uploaded file must be a .zip archive or .json configuration file.")

    if not updated_files:
        raise HTTPException(status_code=400, detail="Package contained no recognizable configuration files (expected scoring_config.json, feature_definitions.json, or model_config.json).")

    change_list = [c.strip() for c in changes.split("\n") if c.strip()] if changes else [f"Imported from package: {', '.join(updated_files)}"]

    entry = registry.register_version(
        new_version=new_version,
        description=description or f"Imported package from {file.filename}",
        changes=change_list,
    )

    return {
        "status": "success",
        "message": f"Configuration package '{file.filename}' successfully deployed as v{new_version}.",
        "active_version": new_version,
        "updated_files": updated_files,
        "version_entry": entry,
    }


@app.get("/api/dashboard")
def dashboard_metrics() -> dict[str, Any]:
    ranking_data = load_json_file(OUTPUT_DIR / "sample_rankings.json")
    eval_data = load_json_file(OUTPUT_DIR / "evaluation_results.json")
    scoring_cfg = load_json_file(CONFIG_DIR / "scoring_config.json")

    summary = ranking_data.get("summary", {})
    rankings = ranking_data.get("rankings", [])

    total_orgs = len(rankings)
    renew_count = summary.get("renew_count", 0)
    review_count = summary.get("review_count", 0)
    do_not_renew_count = summary.get("do_not_renew_count", 0)
    boundary_count = summary.get("boundary_case_count", 0)
    avg_score = summary.get("average_score", 0.0)

    renew_pct = round((renew_count / total_orgs * 100), 1) if total_orgs > 0 else 0.0

    return {
        "total_organisations": total_orgs,
        "average_score": avg_score,
        "renewal_percentage": renew_pct,
        "at_risk_count": do_not_renew_count,
        "boundary_count": boundary_count,
        "model_selected": "Gradient Boosted Trees (GBDT)",
        "configuration_version": scoring_cfg.get("version", "1.0.0"),
        "latest_run": f"RUN-20260824-{compute_config_hash(CONFIG_DIR)[:6].upper()}",
        "distribution": [
            {"label": "Renew (>= 70)", "value": renew_count, "color": "#10b981"},
            {"label": "Review (50-69)", "value": review_count, "color": "#f59e0b"},
            {"label": "Do not renew (< 50)", "value": do_not_renew_count, "color": "#ef4444"},
        ],
        "top_organisations": rankings[:10],
        "model_evaluation_summary": eval_data.get("models", {}),
    }


@app.get("/api/ranking")
def get_rankings(
    page: int = 1,
    limit: int = 25,
    decision: str | None = None,
    boundary_only: bool = False,
    search: str | None = None,
) -> dict[str, Any]:
    ranking_data = load_json_file(OUTPUT_DIR / "sample_rankings.json")
    all_rankings = ranking_data.get("rankings", [])

    if decision and decision != "all":
        all_rankings = [r for r in all_rankings if r.get("decision") == decision]

    if boundary_only:
        all_rankings = [r for r in all_rankings if r.get("boundary_status") == "boundary_case"]

    if search:
        s_lower = search.lower().strip()
        all_rankings = [
            r for r in all_rankings
            if s_lower in r.get("organisation_name", "").lower() or s_lower in r.get("organisation_id", "").lower()
        ]

    total = len(all_rankings)
    start_idx = (page - 1) * limit
    paginated = all_rankings[start_idx : start_idx + limit]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": max(1, (total + limit - 1) // limit),
        "summary": ranking_data.get("summary", {}),
        "items": paginated,
        "configuration_version": ranking_data.get("ranking_version", "1.0.0"),
    }


@app.get("/api/organisations/sample-template")
def get_sample_agency_template() -> dict[str, Any]:
    """Returns sample agency JSON templates for data ingestion testing.

    Two input formats are supported by the ingest endpoints:
    - **raw** : Operational records (audits, auditors, compliance_assessments,
      renewal_history).  Features are auto-derived server-side.
    - **pre-computed** : Feature values already calculated by the caller.
    """
    return {
        # ----------------------------------------------------------------
        # Format A: Raw operational data (features derived automatically)
        # ----------------------------------------------------------------
        "raw_format_sample": {
            "organisations": [
                {
                    "organisation_id": "AGENCY_001",
                    "organisation_name": "Sample Audit Agency 001",
                    "audits": [
                        {
                            "audit_id": "AUD_001",
                            "scheduled_start_date": "2026-01-05",
                            "actual_start_date": "2026-01-06",
                            "contractual_milestone_date": "2026-01-20",
                            "report_submission_date": "2026-01-18",
                            "report_status": "submitted",
                            "report_findings": [
                                {"finding_id": "F001", "review_status": "accepted"},
                                {"finding_id": "F002", "review_status": "discrepancy"}
                            ]
                        },
                        {
                            "audit_id": "AUD_002",
                            "scheduled_start_date": "2026-02-01",
                            "actual_start_date": "2026-02-01",
                            "contractual_milestone_date": "2026-02-15",
                            "report_submission_date": "2026-02-17",
                            "report_status": "submitted",
                            "report_findings": [
                                {"finding_id": "F003", "review_status": "accepted"}
                            ]
                        }
                    ],
                    "auditors": [
                        {"auditor_id": "EMP_001", "certified": True, "experience_start_date": "2018-06-01"},
                        {"auditor_id": "EMP_002", "certified": True, "experience_start_date": "2020-04-15"},
                        {"auditor_id": "EMP_003", "certified": False, "experience_start_date": "2021-07-10"}
                    ],
                    "compliance_assessments": [
                        {
                            "assessment_date": "2026-06-15",
                            "controls": [
                                {"control_id": "CTRL-001", "applicable": True, "result": "pass"},
                                {"control_id": "CTRL-002", "applicable": True, "result": "pass"},
                                {"control_id": "CTRL-003", "applicable": True, "result": "fail"},
                                {"control_id": "CTRL-004", "applicable": False, "result": None}
                            ]
                        }
                    ],
                    "renewal_history": [
                        {"renewal_date": "2024-06-01", "decision": "renewed", "sanction": False},
                        {"renewal_date": "2025-06-01", "decision": "renewed", "sanction": False},
                        {"renewal_date": "2026-06-01", "decision": "renewed", "sanction": False}
                    ]
                }
            ]
        },
        # ----------------------------------------------------------------
        # Format B: Pre-computed feature values (legacy / direct entry)
        # ----------------------------------------------------------------
        "single_agency": {
            "organisation_id": "AUDIT_ORG_CUSTOM_001",
            "organisation_name": "Apex Cyber Assurance Ltd",
            "reporting_period": "2025-2026_ANNUAL",
            "features": {
                "audit_timeliness": 88.5,
                "audit_efficiency": 94.0,
                "error_rate": 3.8,
                "agency_scale": 82.0,
                "compliance_adherence": 96.5,
                "past_renewal_status": 91.0
            }
        },
        "precomputed_format_sample": {
            "organisation_id": "AUDIT_ORG_CUSTOM_001",
            "organisation_name": "Apex Cyber Assurance Ltd",
            "reporting_period": "2025-2026_ANNUAL",
            "features": {
                "audit_timeliness": 88.5,
                "audit_efficiency": 94.0,
                "error_rate": 3.8,
                "agency_scale": 82.0,
                "compliance_adherence": 96.5,
                "past_renewal_status": 91.0
            }
        },
        "feature_derivation_reference": {
            "audit_timeliness": "(submitted audits with report_submission_date <= contractual_milestone_date) / total_submitted * 100",
            "audit_efficiency": "clamp((45 / avg_days_actual_start_to_submission) * 100, 0, 100)",
            "error_rate": "(submitted audits with any finding.review_status=='discrepancy') / total_submitted * 100",
            "agency_scale": "min(100, (certified_auditors/50)*60 + (years_since_earliest_experience_start/20)*40)",
            "compliance_adherence": "(applicable controls with result=='pass') / total_applicable * 100 [latest assessment]",
            "past_renewal_status": "(renewals with decision=='renewed' AND sanction==False) / total_renewals * 100"
        }
    }


class IngestAgencyPayload(BaseModel):
    organisation_id: str
    organisation_name: str | None = None
    reporting_period: str | None = "2025-2026_ANNUAL"
    features: dict[str, float | None]
    raw_metrics: dict[str, Any] | None = None


@app.post("/api/organisations/ingest-and-rank")
def ingest_and_rank_agency(payload: dict[str, Any]) -> dict[str, Any]:
    """Ingest one or multiple auditing agencies from JSON, score, trace provenance, and recalculate global rankings.

    Accepts **two input formats** transparently:

    **Format A – Raw operational data** (features derived automatically):
    Post the exact agency JSON produced by audit management systems, containing
    ``audits``, ``auditors``, ``compliance_assessments``, and ``renewal_history``.
    The server computes all six features server-side.

    **Format B – Pre-computed features** (legacy):
    Post a dict with a ``features`` key containing the six pre-computed feature values.

    Both formats can be wrapped in ``{"organisations": [...]}`` for batch ingestion.
    """
    # Normalize input: could be single agency dict or { "organisations": [...] } or list of dicts
    incoming_orgs: list[dict[str, Any]] = []
    if "organisations" in payload and isinstance(payload["organisations"], list):
        incoming_orgs = payload["organisations"]
    elif "organisation_id" in payload and "features" in payload:
        incoming_orgs = [payload]
    elif isinstance(payload, list):
        incoming_orgs = payload
    elif "features" in payload:
        # Minimal single agency
        incoming_orgs = [{
            "organisation_id": payload.get("organisation_id", "AUDIT_ORG_INGESTED"),
            "organisation_name": payload.get("organisation_name", "Ingested Auditing Agency"),
            "reporting_period": payload.get("reporting_period", "2025-2026_ANNUAL"),
            "features": payload.get("features", {}),
            "raw_metrics": payload.get("raw_metrics", {}),
        }]
    else:
        # If payload itself is a mapping of feature names to values
        feat_defs = load_json_file(CONFIG_DIR / "feature_definitions.json").get("features", [])
        known_feat_ids = {f["id"] for f in feat_defs}
        if any(k in known_feat_ids for k in payload.keys()):
            incoming_orgs = [{
                "organisation_id": "AUDIT_ORG_INGESTED",
                "organisation_name": "Ingested Auditing Agency",
                "reporting_period": "2025-2026_ANNUAL",
                "features": {k: v for k, v in payload.items() if k in known_feat_ids},
            }]
        else:
            raise HTTPException(status_code=400, detail="Invalid agency data format. Must include 'features', raw data sections (audits/auditors/etc.), or 'organisation_id'.")

    if not incoming_orgs:
        raise HTTPException(status_code=400, detail="No valid organisation records found in payload.")

    # Load active dataset
    dataset_path = DATA_DIR / "synthetic_auditing_agencies.json"
    dataset = load_json_file(dataset_path)
    if not dataset or "organisations" not in dataset:
        # Initialize standard dataset if missing
        generator = AgencyDataGenerator(seed=42)
        generator.generate(n_samples=500, output_path=dataset_path)
        dataset = load_json_file(dataset_path)

    existing_orgs = dataset.get("organisations", [])
    existing_map = {o["organisation_id"]: idx for idx, o in enumerate(existing_orgs)}

    # Merge incoming orgs — auto-extract features from raw input when needed
    primary_target_id = incoming_orgs[0].get("organisation_id", "AUDIT_ORG_INGESTED")
    for org in incoming_orgs:
        oid = org.get("organisation_id", f"AUDIT_ORG_{len(existing_orgs) + 1:04d}")
        org["organisation_id"] = oid
        if "organisation_name" not in org or not org["organisation_name"]:
            org["organisation_name"] = f"Agency {oid}"
        if "reporting_period" not in org or not org["reporting_period"]:
            org["reporting_period"] = "2025-2026_ANNUAL"

        # Auto-derive features from raw operational data if not pre-computed
        if is_raw_organisation(org) and "features" not in org:
            derived = extract_features(org)
            org["features"] = derived
            org["feature_extraction"] = "auto_derived_from_raw_data"
        elif is_raw_organisation(org) and "features" in org:
            # Raw data present alongside features — re-derive to ensure consistency
            derived = extract_features(org)
            org["features"] = derived
            org["feature_extraction"] = "re_derived_from_raw_data"
        else:
            org.setdefault("feature_extraction", "pre_computed")

        if oid in existing_map:
            # Update existing
            existing_orgs[existing_map[oid]] = org
        else:
            # Add new
            existing_orgs.insert(0, org)
            existing_map[oid] = 0

    dataset["organisations"] = existing_orgs
    dataset["sample_count"] = len(existing_orgs)
    dataset_path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")

    # Run ranking engine on updated dataset
    ranking_engine = RankingEngine(
        scoring_config_path=CONFIG_DIR / "scoring_config.json",
        model_config_path=CONFIG_DIR / "model_config.json",
    )
    per_org_scores, ranking_output = ranking_engine.process_and_rank_dataset(dataset, output_dir=OUTPUT_DIR)

    # Find the target organisation's ranking & trace
    target_rank_item = next((r for r in ranking_output["rankings"] if r["organisation_id"] == primary_target_id), None)
    target_score_item = next((r for r in per_org_scores["records"] if r["organisation_id"] == primary_target_id), None)

    if not target_score_item:
        raise HTTPException(status_code=500, detail="Failed to locate scored record in recalculated dataset.")

    # Build detailed feature breakdown
    scoring_cfg = load_json_file(CONFIG_DIR / "scoring_config.json")
    feat_defs = load_json_file(CONFIG_DIR / "feature_definitions.json").get("features", [])
    feat_names = {f["id"]: f.get("name", f["id"]) for f in feat_defs}
    weights = scoring_cfg.get("weights", {})
    score_res = target_score_item["score_result"]
    raw_feats = target_score_item["raw_features"]
    contributions = score_res.get("feature_contributions", {})

    breakdown = []
    for fid, fweight in weights.items():
        raw_val = raw_feats.get(fid)
        is_missing = raw_val is None
        is_inverted = fid == "error_rate" and scoring_cfg.get("error_rate_inversion", {}).get("enabled", True)
        eff_val = max(0.0, 100.0 - float(raw_val)) if (not is_missing and is_inverted) else raw_val

        breakdown.append({
            "feature_id": fid,
            "feature_name": feat_names.get(fid, fid.replace("_", " ").title()),
            "raw_value": raw_val,
            "is_inverted": is_inverted,
            "effective_value": round(eff_val, 2) if eff_val is not None else None,
            "weight_pct": fweight,
            "point_contribution": contributions.get(fid, 0.0),
            "status": "not_assessable" if is_missing else "assessed",
        })

    return {
        "status": "success",
        "message": f"Successfully processed '{primary_target_id}' and updated global rankings.",
        "primary_organisation_id": primary_target_id,
        "organisation_name": target_score_item.get("organisation_name"),
        "reporting_period": target_score_item.get("reporting_period"),
        "rank": target_rank_item.get("rank") if target_rank_item else None,
        "total_organisations": len(ranking_output["rankings"]),
        "score_result": score_res,
        "provenance": target_score_item["provenance"],
        "feature_breakdown": breakdown,
        "raw_features": raw_feats,
        "ranking_summary": ranking_output["summary"],
        "all_ingested_count": len(incoming_orgs),
        "feature_extraction_mode": target_score_item.get("feature_extraction", "pre_computed"),
    }


@app.post("/api/organisations/ingest-raw")
def ingest_raw_agency(payload: dict[str, Any]) -> dict[str, Any]:
    """Ingest raw agency operational data, derive features, score, and return ranked result.

    This endpoint is identical to ``POST /api/organisations/ingest-and-rank`` but is
    purpose-named for clarity when submitting raw audit management JSON (containing
    ``audits``, ``auditors``, ``compliance_assessments``, ``renewal_history``).

    Accepts either a single organisation dict or ``{"organisations": [...]}``.  Features
    are always derived automatically from the raw data; any pre-existing ``features``
    key is overwritten to ensure derivation consistency.
    """
    # Normalise to list
    orgs: list[dict[str, Any]] = []
    if "organisations" in payload and isinstance(payload["organisations"], list):
        orgs = payload["organisations"]
    elif "organisation_id" in payload:
        orgs = [payload]
    else:
        raise HTTPException(
            status_code=400,
            detail="Payload must include 'organisation_id' or wrap records in {\"organisations\": [...]}",
        )

    if not orgs:
        raise HTTPException(status_code=400, detail="No organisation records found in payload.")

    extracted_results: list[dict[str, Any]] = []
    for org in orgs:
        oid = org.get("organisation_id", "AGENCY_RAW")
        org_name = org.get("organisation_name", f"Agency {oid}")
        derived_features = extract_features(org)
        scoring_cfg = load_json_file(CONFIG_DIR / "scoring_config.json")
        engine = ScoringEngine(scoring_cfg)
        score_result = engine.score_organisation(derived_features)
        extracted_results.append({
            "organisation_id": oid,
            "organisation_name": org_name,
            "derived_features": derived_features,
            "score_result": score_result,
            "feature_derivation_formulas": {
                "audit_timeliness": "(on_time_submitted / total_submitted) * 100",
                "audit_efficiency": "clamp((45 / avg_days_start_to_submission) * 100, 0, 100)",
                "error_rate": "(submitted_with_discrepancy_finding / total_submitted) * 100",
                "agency_scale": "min(100, (certified_auditors/50)*60 + (years_experience/20)*40)",
                "compliance_adherence": "(applicable_passed / total_applicable) * 100 [latest assessment]",
                "past_renewal_status": "(renewed_without_sanction / total_renewals) * 100",
            },
        })

    return {
        "status": "success",
        "count": len(extracted_results),
        "results": extracted_results,
    }


@app.get("/api/organisations/{org_id}")
def get_organisation_trace(org_id: str) -> dict[str, Any]:
    scores_data = load_json_file(OUTPUT_DIR / "sample_organisation_scores.json")
    records = scores_data.get("records", [])
    record = next((r for r in records if r["organisation_id"] == org_id), None)

    if not record:
        raise HTTPException(status_code=404, detail=f"Organisation '{org_id}' not found.")

    return record


@app.get("/api/evaluation")
def get_evaluation_benchmarks() -> dict[str, Any]:
    eval_data = load_json_file(OUTPUT_DIR / "evaluation_results.json")
    if not eval_data:
        raise HTTPException(status_code=404, detail="Evaluation results not yet generated. Run pipeline.")
    return eval_data


@app.get("/api/dataset")
def get_dataset_summary() -> dict[str, Any]:
    data = load_json_file(DATA_DIR / "synthetic_auditing_agencies.json")
    if not data:
        raise HTTPException(status_code=404, detail="Dataset not found. Run generator.")
    return {
        "dataset_version": data.get("dataset_version", "1.0.0"),
        "seed": data.get("seed", 42),
        "sample_count": data.get("sample_count", 0),
        "irregular_sample_count": data.get("irregular_sample_count", 0),
        "irregularity_percentage": data.get("irregularity_percentage", 0.0),
        "class_distribution": data.get("class_distribution", {}),
        "sample_records": data.get("organisations", [])[:15],
    }


@app.post("/api/scoring/run")
def run_live_scoring(request: ScoreRequest) -> dict[str, Any]:
    scoring_cfg = load_json_file(CONFIG_DIR / "scoring_config.json")
    engine = ScoringEngine(scoring_cfg)
    result = engine.score_organisation(request.features)
    return {
        "organisation_id": request.organisation_id,
        "result": result,
        "configuration_version": scoring_cfg.get("version", "1.0.0"),
        "configuration_sha256": compute_config_hash(CONFIG_DIR),
    }


@app.post("/api/pipeline/run")
def trigger_pipeline_run() -> dict[str, Any]:
    """Re-run pipeline and refresh scoring and rankings."""
    generator = AgencyDataGenerator(seed=42)
    gen_result = generator.generate(n_samples=500, output_path=DATA_DIR / "synthetic_auditing_agencies.json")

    pipeline = ModelPipeline()
    eval_result = pipeline.run_pipeline(dataset_path=DATA_DIR / "synthetic_auditing_agencies.json", output_dir=OUTPUT_DIR)

    dataset = load_json_file(DATA_DIR / "synthetic_auditing_agencies.json")
    ranking_engine = RankingEngine()
    per_org_scores, ranking_output = ranking_engine.process_and_rank_dataset(dataset, output_dir=OUTPUT_DIR)

    return {
        "status": "success",
        "sample_count": gen_result["sample_count"],
        "ranked_count": len(ranking_output["rankings"]),
        "summary": ranking_output["summary"],
    }

