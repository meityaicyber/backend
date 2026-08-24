import os
import json
import subprocess
import shutil
import hashlib
import pytest
import sys
from src.utils.json_utils import load_json, save_json

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert result.returncode == 0, f"Command failed: {cmd}\nOutput: {result.stderr}"
    return result.stdout

@pytest.fixture(scope="session")
def setup_test_env(tmp_path_factory):
    # Tests operate in a temporary isolated copy
    basetemp = tmp_path_factory.mktemp("perfmon")
    # Copy source to basetemp
    for item in ["config", "data", "src", "deploy", "vendor", "requirements.txt"]:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.copytree(item, basetemp / item)
            else:
                shutil.copy2(item, basetemp / item)
                
    python_exec = sys.executable
    return basetemp, python_exec

def test_1_fresh_clone(setup_test_env):
    # Since we are in the temp dir, we will run the pipeline directly
    basetemp, python_exec = setup_test_env
    cmd = f"{python_exec} -m src.run_pipeline --config config/generator_config.json --dataset data/sample_dataset.json --output output"
    run_cmd(f"cd {basetemp} && {cmd}")
    
    assert os.path.exists(basetemp / "output" / "scoring" / "organisation_scores.json")

def test_2_offline_install(setup_test_env):
    basetemp, python_exec = setup_test_env
    # Just run the verification script which simulates offline validation
    cmd = f"{python_exec} deploy/verify_install.py"
    output = run_cmd(f"cd {basetemp} && {cmd}")
    assert "ALL VERIFICATIONS PASSED" in output

def test_3_feature_coverage(setup_test_env):
    basetemp, _ = setup_test_env
    schema = load_json(basetemp / "config" / "feature_schema.json")
    expected_features = ["audit_timeliness", "audit_efficiency", "error_rate", "agency_scale", "compliance_adherence", "past_renewal_status"]
    for f in expected_features:
        assert f in schema["features"]
        assert "range" in schema["features"][f] or "components" in schema["features"][f]
        assert "missing_rule" in schema["features"][f]

def test_4_determinism(setup_test_env):
    basetemp, python_exec = setup_test_env
    
    def run_and_hash():
        cmd = f"{python_exec} -m src.dataset_generator -n 10 --output data/det_dataset.json --seed 42"
        run_cmd(f"cd {basetemp} && {cmd}")
        with open(basetemp / "data" / "det_dataset.json", "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
            
    hash1 = run_and_hash()
    hash2 = run_and_hash()
    hash3 = run_and_hash()
    assert hash1 == hash2 == hash3

def test_5_config_independence(setup_test_env):
    basetemp, python_exec = setup_test_env
    # Run once to get baseline scores
    cmd = f"{python_exec} -m src.pipeline.score --config-scoring config/scoring_config.json --config-schema config/feature_schema.json --models-meta output/models/models_metadata.json --dataset data/sample_dataset.json --output output/score_1"
    run_cmd(f"cd {basetemp} && {cmd}")
    
    scores1 = load_json(basetemp / "output" / "score_1" / "organisation_scores.json")
    
    # Modify config
    config = load_json(basetemp / "config" / "scoring_config.json")
    config["scoring_rule"]["weights"]["audit_timeliness"] = 0.50
    config["scoring_rule"]["weights"]["compliance_adherence"] = 0.0
    save_json(config, basetemp / "config" / "scoring_config.json")
    
    # Run again
    cmd = f"{python_exec} -m src.pipeline.score --config-scoring config/scoring_config.json --config-schema config/feature_schema.json --models-meta output/models/models_metadata.json --dataset data/sample_dataset.json --output output/score_2"
    run_cmd(f"cd {basetemp} && {cmd}")
    
    scores2 = load_json(basetemp / "output" / "score_2" / "organisation_scores.json")
    
    # Verify scores changed without code changes
    diff = sum(1 for s1, s2 in zip(scores1, scores2) if s1["performance_score"] != s2["performance_score"])
    assert diff > 0, "Scores did not change after config mutation"
    
def test_6_irregular_input(setup_test_env):
    basetemp, python_exec = setup_test_env
    scores = load_json(basetemp / "output" / "scoring" / "organisation_scores.json")
    
    has_not_assessable = False
    for s in scores:
        if s["assessment_status"] == "not_assessable":
            has_not_assessable = True
            assert len(s["missing_features"]) > 2
    
    assert has_not_assessable, "Generator did not produce unassessable data or scorer failed to catch it"

def test_7_versioning(setup_test_env):
    basetemp, python_exec = setup_test_env
    cmd = f"{python_exec} -m src.versioning.cli create --change 'test bump' --approver 'test' --component 'scoring_config' --file config/scoring_config.json --new-version '2.0.0'"
    run_cmd(f"cd {basetemp} && {cmd}")
    
    registry = load_json(basetemp / "config" / "version_registry.json")
    assert registry["current_versions"]["scoring_config"] == "2.0.0"
    assert os.path.exists(basetemp / "config" / "archive" / "scoring_config_v1.0.0.json")

def test_8_model_comparison(setup_test_env):
    basetemp, _ = setup_test_env
    summary = load_json(basetemp / "output" / "evaluation" / "comparison_summary.json")
    assert "baseline" in summary
    assert "gradient_boosting" in summary
    assert "svm" in summary
    assert "neural_network" in summary
