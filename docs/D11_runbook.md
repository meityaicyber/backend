# Deliverable D11: Operational Runbook

**Project**: Development of AI-Based Solution for Analysing, Benchmarking and Quality Monitoring of Cybersecurity Audit Reports and Performance Monitoring of Auditing Organisations  
**Document Ref**: D11-RUNBOOK-2026  
**Classification**: Strictly Confidential  

---

## 1. System Requirements & Environment

* **Operating System**: Windows 10/11, Windows Server 2019/2022, or Linux (RHEL 8+, Ubuntu 20.04+)
* **Python Runtime**: Python 3.10 or 3.11
* **Core Libraries**: `scikit-learn`, `numpy`, `pytest`, `fastapi`, `uvicorn` (all offline vendored)
* **Storage Requirement**: < 150 MB

---

## 2. Installation & Fresh-Clone Setup

### Step 2.1: Fresh-Clone Installation
```powershell
# In terminal:
cd c:\auditagencyPerformance

# Install dependencies from local wheels / cache:
python -m pip install -r requirements.txt
```

### Step 2.2: Air-Gapped Offline Verification
Confirm that all dependencies, configurations, and test runners operate without internet access:
```powershell
python deploy/verify_offline_install.py
```
**Expected Output**:
```
AIR-GAPPED ENVIRONMENT OFFLINE INSTALLATION VERIFICATION
[1/4] Testing offline dependencies... -> PASSED
[2/4] Testing configuration syntax and schema integrity... -> PASSED
[3/4] Testing file integrity against airgap_manifest.json... -> PASSED
[4/4] Testing offline scoring dry-run... -> PASSED
VERIFICATION SUCCESSFUL: System is fully operational in air-gapped environment.
```

---

## 3. End-to-End Execution Commands

### Single-Command Full Execution (Section 6 Test 1)
To run the entire pipeline (synthetic dataset generation, 4-model evaluation, scoring, ranking, and output generation) in a single command:
```powershell
python -m src.cli --all
```

### Granular Pipeline Step Execution
```powershell
# 1. Regenerate synthetic population with custom seed/samples:
python data/generator.py --samples 500 --seed 42 --output data/synthetic_auditing_agencies.json

# 2. Run model training, cross-validation, and holdout evaluation:
python -m src.models.pipeline

# 3. Compute continuous scores and generate ranking outputs:
python -m src.scoring.ranking

# 4. Trace the provenance and feature contribution of an individual organisation:
python -m src.cli --trace-org AUDIT_ORG_0179
```

---

---

## 4. Automated Acceptance Testing

Run the automated test suite implementing Acceptance Tests 1 to 9:
```powershell
python -m pytest tests/ -v
```

---

## 5. Customizing Model Parameters (`config.json`)

All model parameters and hyperparameters are loaded dynamically from [`config.json`](file:///c:/auditagencyPerformance/config.json) (or [`config/model_config.json`](file:///c:/auditagencyPerformance/config/model_config.json)). Operators can adjust any parameter before executing the pipeline:

```json
{
  "selected_model": "gradient_boosting",
  "train_test_split": {"test_size": 0.20, "stratify": true},
  "cross_validation": {"n_splits": 5, "shuffle": true, "scoring": "f1_macro"},
  "models": [
    {
      "id": "gradient_boosting",
      "parameters": {
        "n_estimators": 150,
        "learning_rate": 0.04,
        "max_depth": 4,
        "subsample": 0.85
      }
    }
  ]
}
```

To re-run evaluation with modified parameters:
```powershell
python -m src.models.pipeline
```

---

## 6. Interpreting Output JSON Files

All results are strictly formatted as standard JSON in `/output/`:

### 1. `output/sample_rankings.json`
* **`rankings`**: Ordered list of all organisations with rank, final continuous score, decision tier (`renew`, `review`, `do_not_renew`), and boundary status.
* **`boundary_status`**: Annotated as `"boundary_case"` if the score is within $\pm 3.0$ points of a decision boundary, alerting reviewers to conduct a secondary check.

### 2. `output/sample_organisation_scores.json`
* **`records`**: Per-organisation breakdown containing raw feature values, computed score, and point contributions from each feature.
* **`provenance`**: Lineage including exact `scoring_config_version`, `model_config_version`, `selected_model`, and `configuration_sha256`.

### 3. `output/evaluation_results.json`
* Benchmark comparison of all four classification models (Baseline, Gradient Boosting, SVM, MLP) with Accuracy, Macro-F1, Per-Class Precision/Recall/F1, and Confusion Matrices.

