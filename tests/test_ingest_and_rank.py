"""Tests for JSON Agency Data Ingestion, Lineage Tracing, and Dynamic Ranking."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
DATA_FILE = Path("data/synthetic_auditing_agencies.json")
OUTPUT_RANKINGS = Path("output/sample_rankings.json")
OUTPUT_SCORES = Path("output/sample_organisation_scores.json")


@pytest.fixture(autouse=True)
def preserve_dataset():
    original_data = DATA_FILE.read_text(encoding="utf-8") if DATA_FILE.exists() else None
    original_rankings = OUTPUT_RANKINGS.read_text(encoding="utf-8") if OUTPUT_RANKINGS.exists() else None
    original_scores = OUTPUT_SCORES.read_text(encoding="utf-8") if OUTPUT_SCORES.exists() else None
    try:
        yield
    finally:
        if original_data is not None:
            DATA_FILE.write_text(original_data, encoding="utf-8")
        if original_rankings is not None:
            OUTPUT_RANKINGS.write_text(original_rankings, encoding="utf-8")
        if original_scores is not None:
            OUTPUT_SCORES.write_text(original_scores, encoding="utf-8")



def test_sample_template_endpoint():
    response = client.get("/api/organisations/sample-template")
    assert response.status_code == 200
    data = response.json()
    assert "single_agency" in data
    assert "features" in data["single_agency"]
    assert "organisation_id" in data["single_agency"]


def test_ingest_and_rank_single_agency():
    payload = {
        "organisation_id": "TEST_AUDIT_AGENCY_999",
        "organisation_name": "Test Cyber Assurance Bureau",
        "reporting_period": "2025-2026_ANNUAL",
        "features": {
            "audit_timeliness": 98.0,
            "audit_efficiency": 95.0,
            "error_rate": 2.0,
            "agency_scale": 90.0,
            "compliance_adherence": 99.0,
            "past_renewal_status": 95.0
        }
    }

    response = client.post("/api/organisations/ingest-and-rank", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["status"] == "success"
    assert res["primary_organisation_id"] == "TEST_AUDIT_AGENCY_999"
    assert res["score_result"]["decision"] == "renew"
    assert res["score_result"]["score"] >= 90.0
    assert res["rank"] is not None
    assert "provenance" in res
    assert "configuration_sha256" in res["provenance"]
    assert len(res["feature_breakdown"]) == 6

    # Verify that ranking endpoint now contains this organisation
    rank_resp = client.get("/api/ranking?search=TEST_AUDIT_AGENCY_999")
    assert rank_resp.status_code == 200
    rank_data = rank_resp.json()
    assert rank_data["total"] >= 1
    found = any(item["organisation_id"] == "TEST_AUDIT_AGENCY_999" for item in rank_data["items"])
    assert found


def test_ingest_and_rank_boundary_case():
    payload = {
        "organisation_id": "TEST_BOUNDARY_AGENCY_001",
        "organisation_name": "Test Boundary Cyber Ltd",
        "reporting_period": "2025-2026_ANNUAL",
        "features": {
            "audit_timeliness": 71.0,
            "audit_efficiency": 70.0,
            "error_rate": 30.0,
            "agency_scale": 65.0,
            "compliance_adherence": 72.0,
            "past_renewal_status": 70.0
        }
    }

    response = client.post("/api/organisations/ingest-and-rank", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["status"] == "success"
    assert res["primary_organisation_id"] == "TEST_BOUNDARY_AGENCY_001"
    # Score should be near 70.0 (boundary case)
    assert "boundary_status" in res["score_result"]
