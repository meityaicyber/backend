"""Unit tests for Scoring and Ranking Engine."""

from __future__ import annotations

from src.scoring.engine import ScoringEngine, calculate_organisation_score
from src.scoring.ranking import RankingEngine


def test_score_renormalises_missing_features() -> None:
    custom_config = {
        "version": "1.0.0",
        "weights": {"audit_timeliness": 20.0, "audit_efficiency": 80.0},
        "thresholds": {"renew": 70.0, "review": 50.0},
        "boundary_tolerance": 3.0,
        "missing_data_policy": "exclude_and_renormalise",
    }
    engine = ScoringEngine(custom_config)
    result = engine.score_organisation({"audit_timeliness": 90.0, "audit_efficiency": None})
    assert result["score"] == 90.0
    assert result["status"] == "assessable"
    assert len(result["non_assessable_features"]) == 1


def test_boundary_is_explicit() -> None:
    custom_config = {
        "version": "1.0.0",
        "weights": {"audit_timeliness": 100.0},
        "thresholds": {"renew": 70.0, "review": 50.0},
        "boundary_tolerance": 3.0,
        "missing_data_policy": "exclude_and_renormalise",
    }
    engine = ScoringEngine(custom_config)
    result = engine.score_organisation({"audit_timeliness": 71.5})
    assert result["boundary_status"] == "boundary_case"
    assert result["distance_to_nearest_boundary"] == 1.5
    assert "boundary_annotation" in result


def test_error_rate_inversion() -> None:
    custom_config = {
        "version": "1.0.0",
        "weights": {"error_rate": 100.0},
        "thresholds": {"renew": 70.0, "review": 50.0},
        "boundary_tolerance": 3.0,
        "error_rate_inversion": {"enabled": True, "formula": "100.0 - error_rate"},
    }
    engine = ScoringEngine(custom_config)
    # 5% error rate should yield a quality score of 95.0
    result = engine.score_organisation({"error_rate": 5.0})
    assert result["score"] == 95.0
    assert result["decision"] == "renew"


def test_ranking_tie_breaks() -> None:
    dataset = {
        "organisations": [
            {"organisation_id": "ORG_A", "organisation_name": "Agency A", "features": {"audit_timeliness": 90.0, "audit_efficiency": 90.0, "error_rate": 0.0, "agency_scale": 90.0, "compliance_adherence": 90.0, "past_renewal_status": 90.0}},
            {"organisation_id": "ORG_B", "organisation_name": "Agency B", "features": {"audit_timeliness": 90.0, "audit_efficiency": 90.0, "error_rate": 0.0, "agency_scale": 90.0, "compliance_adherence": 90.0, "past_renewal_status": 90.0}},
            {"organisation_id": "ORG_C", "organisation_name": "Agency C", "features": {"audit_timeliness": 80.0, "audit_efficiency": 80.0, "error_rate": 0.0, "agency_scale": 80.0, "compliance_adherence": 80.0, "past_renewal_status": 80.0}},
        ]
    }
    engine = RankingEngine()
    _, ranking_payload = engine.process_and_rank_dataset(dataset, output_dir=None)
    rankings = ranking_payload["rankings"]
    # In standard competition ranking: ORG_A and ORG_B tie at rank 1, ORG_C gets rank 3
    assert rankings[0]["rank"] == 1
    assert rankings[1]["rank"] == 1
    assert rankings[2]["rank"] == 3
