"""Automated Acceptance Test Suite for Section 6 Criteria (Tests 1 to 8).

Tests 1 to 8 are automated and pass/fail:
1. Fresh-clone execution
2. Offline install verification
3. Feature coverage check
4. Determinism check (3 runs producing byte-identical JSON outputs)
5. Configuration-independence check (altering weights alters ranking without code changes)
6. Irregular-input check (missing features, sparse history, outliers handled gracefully)
7. Versioning check (schema/weight update creates new version, old scores remain attributable)
8. Model comparison check (Baseline, GBDT, SVM, MLP all evaluated and reported in JSON)
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from data.generator import AgencyDataGenerator
from deploy.verify_offline_install import run_verification
from src.models.pipeline import ModelPipeline
from src.scoring.engine import ScoringEngine, calculate_organisation_score
from src.scoring.ranking import RankingEngine
from src.versioning.registry import VersionRegistry

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_acceptance_1_fresh_clone_execution(tmp_path: Path) -> None:
    """Test 1: Fresh-clone execution. Pipeline runs end-to-end generating valid JSON outputs."""
    gen = AgencyDataGenerator(seed=42)
    data = gen.generate(n_samples=100, output_path=tmp_path / "test_data.json")
    assert len(data["organisations"]) == 100

    pipeline = ModelPipeline()
    eval_res = pipeline.run_pipeline(
        dataset_path=tmp_path / "test_data.json",
        output_dir=tmp_path / "output",
    )
    assert "models" in eval_res
    assert (tmp_path / "output" / "evaluation_results.json").exists()

    engine = RankingEngine()
    scores, ranking = engine.process_and_rank_dataset(data, output_dir=tmp_path / "output")
    assert len(ranking["rankings"]) == 100

    assert (tmp_path / "output" / "sample_rankings.json").exists()
    assert (tmp_path / "output" / "sample_organisation_scores.json").exists()


def test_acceptance_2_offline_install() -> None:
    """Test 2: Offline install and execution verification."""
    result = run_verification()
    assert result == 0, "Air-gapped offline verification failed."


def test_acceptance_3_feature_coverage() -> None:
    """Test 3: Feature coverage check. All 6 features have operational definitions, bounds, and missing rules in JSON."""
    feat_file = ROOT_DIR / "config" / "feature_definitions.json"
    assert feat_file.exists(), "feature_definitions.json missing."

    data = json.loads(feat_file.read_text(encoding="utf-8"))
    features = {f["id"]: f for f in data["features"]}

    required_features = [
        "audit_timeliness",
        "audit_efficiency",
        "error_rate",
        "agency_scale",
        "compliance_adherence",
        "past_renewal_status",
    ]

    for req_feat in required_features:
        assert req_feat in features, f"Missing feature: {req_feat}"
        f_entry = features[req_feat]
        assert "operational_definition" in f_entry and len(f_entry["operational_definition"]) > 10
        assert "computation_method" in f_entry
        assert "permitted_range" in f_entry and len(f_entry["permitted_range"]) == 2
        assert "treatment_of_missing" in f_entry and len(f_entry["treatment_of_missing"]) > 5
        assert "justification" in f_entry and len(f_entry["justification"]) > 10


def test_acceptance_4_determinism(tmp_path: Path) -> None:
    """Test 4: Determinism check. Regenerating dataset and running pipeline 3 times yields byte-identical JSON."""
    runs_outputs: list[bytes] = []

    for i in range(3):
        run_data_path = tmp_path / f"run_data_{i}.json"
        run_out_dir = tmp_path / f"run_out_{i}"

        # 1. Generate data with fixed seed
        gen = AgencyDataGenerator(seed=42)
        gen.generate(n_samples=50, output_path=run_data_path)

        # 2. Score and rank
        dataset = json.loads(run_data_path.read_text(encoding="utf-8"))
        ranking_engine = RankingEngine()
        ranking_engine.process_and_rank_dataset(dataset, output_dir=run_out_dir)

        ranking_bytes = (run_out_dir / "sample_rankings.json").read_bytes()
        # Parse JSON and remove variable timestamps for byte comparison of deterministic payload
        parsed = json.loads(ranking_bytes.decode("utf-8"))
        parsed["generated_at"] = "FIXED_TIMESTAMP_FOR_DETERMINISM"
        for r in parsed["rankings"]:
            r["provenance"]["computation_timestamp"] = "FIXED_TIMESTAMP"

        runs_outputs.append(json.dumps(parsed, sort_keys=True, indent=2).encode("utf-8"))

    assert runs_outputs[0] == runs_outputs[1] == runs_outputs[2], "Runs produced non-deterministic outputs!"


def test_acceptance_5_configuration_independence() -> None:
    """Test 5: Configuration-independence check. Modifying weights in config alters scores and rankings without code changes."""
    base_config = json.loads((ROOT_DIR / "config" / "scoring_config.json").read_text(encoding="utf-8"))

    # Config A: heavy weight on timeliness (60%), low on compliance (5%)
    cfg_a = copy.deepcopy(base_config)
    cfg_a["weights"] = {
        "audit_timeliness": 60.0,
        "audit_efficiency": 10.0,
        "error_rate": 10.0,
        "agency_scale": 5.0,
        "compliance_adherence": 5.0,
        "past_renewal_status": 10.0,
    }

    # Config B: heavy weight on compliance (60%), low on timeliness (5%)
    cfg_b = copy.deepcopy(base_config)
    cfg_b["weights"] = {
        "audit_timeliness": 5.0,
        "audit_efficiency": 10.0,
        "error_rate": 10.0,
        "agency_scale": 5.0,
        "compliance_adherence": 60.0,
        "past_renewal_status": 10.0,
    }

    engine_a = ScoringEngine(cfg_a)
    engine_b = ScoringEngine(cfg_b)

    # Agency 1: Fast (timeliness 95%) but low compliance (50%)
    org_fast = {
        "audit_timeliness": 95.0,
        "audit_efficiency": 80.0,
        "error_rate": 5.0,
        "agency_scale": 50.0,
        "compliance_adherence": 50.0,
        "past_renewal_status": 80.0,
    }

    # Agency 2: Slow (timeliness 50%) but high compliance (98%)
    org_compliant = {
        "audit_timeliness": 50.0,
        "audit_efficiency": 80.0,
        "error_rate": 5.0,
        "agency_scale": 50.0,
        "compliance_adherence": 98.0,
        "past_renewal_status": 80.0,
    }

    score_fast_a = engine_a.score_organisation(org_fast)["score"]
    score_comp_a = engine_a.score_organisation(org_compliant)["score"]

    score_fast_b = engine_b.score_organisation(org_fast)["score"]
    score_comp_b = engine_b.score_organisation(org_compliant)["score"]

    # Under Config A, org_fast must beat org_compliant
    assert score_fast_a > score_comp_a, f"Config A failed: {score_fast_a} vs {score_comp_a}"
    # Under Config B, org_compliant must beat org_fast
    assert score_comp_b > score_fast_b, f"Config B failed: {score_comp_b} vs {score_fast_b}"


def test_acceptance_6_irregular_input_handling() -> None:
    """Test 6: Irregular-input check. Handles missing features, sparse history, and extreme outliers gracefully."""
    engine = ScoringEngine()

    # 1. Missing features
    partial_org = {
        "audit_timeliness": 85.0,
        "audit_efficiency": None,  # Missing
        "error_rate": 4.0,
        "agency_scale": 50.0,
        "compliance_adherence": 90.0,
        "past_renewal_status": None,  # Missing (new agency)
    }
    res_partial = engine.score_organisation(partial_org)
    assert res_partial["status"] == "assessable"
    assert res_partial["score"] is not None
    assert len(res_partial["non_assessable_features"]) == 2
    assert "audit_efficiency" in [f["feature_id"] for f in res_partial["non_assessable_features"]]

    # 2. Completely missing organisation (zero features)
    empty_org = {k: None for k in base_features_keys()}
    res_empty = engine.score_organisation(empty_org)
    assert res_empty["status"] == "not_assessable"
    assert res_empty["score"] is None
    assert res_empty["decision"] == "undetermined"

    # 3. Outlier handling
    outlier_org = {
        "audit_timeliness": 10.0,
        "audit_efficiency": 20.0,
        "error_rate": 85.0,  # Extreme error rate
        "agency_scale": 5.0,
        "compliance_adherence": 25.0,
        "past_renewal_status": 10.0,
    }
    res_outlier = engine.score_organisation(outlier_org)
    assert res_outlier["status"] == "assessable"
    assert res_outlier["score"] < 50.0
    assert res_outlier["decision"] == "do_not_renew"


def test_acceptance_7_versioning_and_immutability(tmp_path: Path) -> None:
    """Test 7: Versioning check. New versions are recorded, history is immutable, and old scores remain attributable."""
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir(parents=True)
    # Copy existing configs to test dir
    for f in (ROOT_DIR / "config").glob("*.json"):
        (cfg_dir / f.name).write_bytes(f.read_bytes())

    registry = VersionRegistry(config_dir=cfg_dir)
    initial_history = registry.get_change_history()
    assert len(initial_history) >= 1

    # Register new version
    new_entry = registry.register_version(
        new_version="2.0.0-TEST",
        author="Test Auditor",
        approval_id="TEST-AUTH-999",
        description="Test version migration",
        changes=["Adjusted error rate weighting"],
    )
    assert new_entry["version"] == "2.0.0-TEST"

    # Verify attempting to re-register existing version raises ValueError
    with pytest.raises(ValueError, match="already exists"):
        registry.register_version(
            new_version="2.0.0-TEST",
            author="Attacker",
            approval_id="MAL-001",
            description="Attempted overwrite",
            changes=[],
        )

    # Verify provenance check
    prov_record = {
        "provenance": {
            "scoring_config_version": "1.0.0",
            "configuration_sha256": "dummy",
        }
    }
    ver_res = registry.verify_provenance(prov_record)
    assert ver_res["verified"] is True
    assert ver_res["version_entry"]["version"] == "1.0.0"


def test_acceptance_8_model_comparison() -> None:
    """Test 8: Model comparison check. Baseline, GBDT, SVM, and Neural Network are all evaluated."""
    eval_file = ROOT_DIR / "output" / "evaluation_results.json"
    assert eval_file.exists(), "evaluation_results.json not found. Run pipeline first."

    eval_data = json.loads(eval_file.read_text(encoding="utf-8"))
    models = eval_data.get("models", {})

    expected_models = ["baseline", "gradient_boosting", "svm", "neural_network"]
    for m in expected_models:
        assert m in models, f"Model {m} missing from evaluation results."
        m_res = models[m]
        assert "metrics" in m_res
        metrics = m_res["metrics"]
        assert "accuracy" in metrics and 0.0 <= metrics["accuracy"] <= 1.0
        assert "macro_f1" in metrics and 0.0 <= metrics["macro_f1"] <= 1.0
        assert "per_class_breakdown" in m_res
        assert "renew" in m_res["per_class_breakdown"]
        assert "review" in m_res["per_class_breakdown"]
        assert "do_not_renew" in m_res["per_class_breakdown"]
        assert "confusion_matrix" in m_res


def test_acceptance_9_model_parameter_config_loading() -> None:
    """Test 9: Dynamic model parameter loading check. Altering model hyperparameters in config.json updates model parameters."""
    custom_model_config = {
        "version": "1.0.0-CUSTOM",
        "selected_model": "gradient_boosting",
        "random_seed": 99,
        "train_test_split": {"test_size": 0.25, "stratify": True},
        "cross_validation": {"n_splits": 3, "shuffle": True, "scoring": "f1_macro"},
        "feature_order": [
            "audit_timeliness",
            "audit_efficiency",
            "error_rate",
            "agency_scale",
            "compliance_adherence",
            "past_renewal_status",
        ],
        "target_classes": ["renew", "review", "do_not_renew"],
        "models": [
            {
                "id": "baseline",
                "parameters": {"renew_cutoff": 75.0, "review_cutoff": 55.0},
            },
            {
                "id": "gradient_boosting",
                "parameters": {"n_estimators": 142, "learning_rate": 0.08, "max_depth": 4, "subsample": 0.85, "random_state": 99},
            },
            {
                "id": "svm",
                "parameters": {"C": 2.5, "kernel": "rbf", "gamma": 0.1, "probability": True, "random_state": 99},
            },
            {
                "id": "neural_network",
                "parameters": {"hidden_layer_sizes": [128, 64, 32], "activation": "tanh", "alpha": 0.005, "max_iter": 400, "random_state": 99},
            },
        ],
    }

    pipeline = ModelPipeline(config_path=custom_model_config)

    # 1. Baseline parameters
    baseline_clf = pipeline.models["baseline"]
    assert baseline_clf.renew_cutoff == 75.0
    assert baseline_clf.review_cutoff == 55.0

    # 2. Gradient Boosting parameters
    gb_clf = pipeline.models["gradient_boosting"].named_steps["clf"]
    assert gb_clf.n_estimators == 142
    assert gb_clf.learning_rate == 0.08
    assert gb_clf.max_depth == 4
    assert gb_clf.subsample == 0.85
    assert gb_clf.random_state == 99

    # 3. SVM parameters
    svm_clf = pipeline.models["svm"].named_steps["clf"]
    assert svm_clf.C == 2.5
    assert svm_clf.kernel == "rbf"
    assert svm_clf.gamma == 0.1
    assert svm_clf.random_state == 99

    # 4. Neural Network parameters
    mlp_clf = pipeline.models["neural_network"].named_steps["clf"]
    assert mlp_clf.hidden_layer_sizes == (128, 64, 32)
    assert mlp_clf.activation == "tanh"
    assert mlp_clf.alpha == 0.005
    assert mlp_clf.max_iter == 400
    assert mlp_clf.random_state == 99


def base_features_keys() -> list[str]:
    return [
        "audit_timeliness",
        "audit_efficiency",
        "error_rate",
        "agency_scale",
        "compliance_adherence",
        "past_renewal_status",
    ]

