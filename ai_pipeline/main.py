"""
AI Pipeline Service
-------------------
Standalone FastAPI microservice that receives a report file,
runs a dummy AI analysis pipeline, and returns structured JSON results.
"""

import asyncio
import hashlib
import random
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Pipeline Service",
    description="Dummy AI analysis pipeline for cyber-audit reports",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _generate_dummy_results(report_id: str, file_bytes: bytes, filename: str) -> dict:
    """Return the exact JSON structure provided by the user with zero additional information."""
    return {
        "_meta": {
            "pipeline_version": "",
            "source_file": "",
            "extraction_timestamp": "",
            "llm_model": "",
            "extraction_mode": "",
            "tables_extracted": 0,
            "images_extracted": 0
        },
        "metadata": {
            "document_title": "",
            "document_id": "",
            "document_version": "",
            "document_classification": "",
            "organization_audited": "",
            "auditing_organization": "",
            "audit_type": "",
            "report_type": "",
            "release_date": "",
            "prepared_by": "",
            "reviewed_by": "",
            "approved_by": "",
            "released_by": "",
            "standards_referenced": [""]
        },
        "scope": {
            "description": "",
            "assets_tested": [
                {
                    "sr_no": "",
                    "asset_name": "",
                    "asset_type": "",
                    "url": None,
                    "internal_ip": "",
                    "public_ip": "",
                    "location": "",
                    "criticality": "",
                    "version": None,
                    "other_details": ""
                }
            ],
            "testing_period": {
                "start_date": "",
                "end_date": ""
            },
            "assumptions": ""
        },
        "audit_team": [
            {
                "name": "",
                "designation": "",
                "organization": "",
                "email": "",
                "certifications": "",
                "listed_on_certin": ""
            }
        ],
        "tools_used": [
            {
                "name": "",
                "version": "",
                "license_type": "",
                "description": ""
            }
        ],
        "methodology": "",
        "executive_summary": {
            "summary_text": "",
            "total_vulnerabilities": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "informational_count": 0,
            "summary_findings": [
                {
                    "sr_no": "",
                    "vulnerability_title": "",
                    "severity": "",
                    "affected_asset": "",
                    "status": "",
                    "new_or_repeat": ""
                }
            ]
        },
        "vulnerabilities": [
            {
                "report id": "",
                "id": "",
                "vulnerability_title": "",
                "category": "",
                "severity": "",
                "cvss_score": None,
                "cve_ids": [""],
                "cwe_ids": [""],
                "affected_assets": [""],
                "status": "",
                "detailed_observation": "",
                "description": "",
                "impact": "",
                "recommendation": "",
                "proof_of_concept": "",
                "reproduction_steps": None,
                "reference": "",
                "new_or_repeat": "",
                "revalidation_status": None,
                "additional meta": "jsonb"
            }
        ],
        "risk_rating_criteria": {
            "critical": "",
            "high": "",
            "medium": "",
            "low": "",
            "informational": None
        },
        "appendices": {
            "acronyms": None,
            "site_structure": None,
            "risk_assessment_matrix": [
                {
                    "impact": "",
                    "likelihood": "",
                    "risk_severity": ""
                }
            ],
            "disclaimer": None
        }
    }


@app.post("/run")
async def run_pipeline(
    report_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Run the AI analysis pipeline on the uploaded report file.
    Returns structured JSON with analysis results.
    """
    file_bytes = await file.read()
    filename = file.filename or "unknown"

    # Simulate AI processing time (2-3 seconds)
    await asyncio.sleep(random.uniform(2.0, 3.0))

    results = _generate_dummy_results(report_id, file_bytes, filename)
    #write your ai logic

    return results


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-pipeline"}
