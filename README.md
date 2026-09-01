# Auditing Agency Performance Monitoring & Ranking Module

**Project**: Development of AI-Based Solution for Analysing, Benchmarking and Quality Monitoring of Cybersecurity Audit Reports and Performance Monitoring of Auditing Organisations  
**Task Ref**: TASK ASSIGNMENT-2  
**Classification**: Strictly Confidential  
**Submission Deadline**: 2 September 2026  

---

## 1. Executive Summary

This clean-room software module provides an automated, objective, and reproducible framework for monitoring, scoring, ranking, and evaluating the empanelment renewal status of cybersecurity auditing organisations.

### Key Architectural Disciplines:
* **Zero External Dependencies / Air-Gapped Ready (Mandatory Disciplines 2.8, 4.3)**: 100% self-contained, fully operable offline without internet connectivity.
* **Strict JSON-Only Constraint (Requirement 2.9)**: Exclusively uses standard JSON for all datasets, configurations, evaluation results, version histories, and outputs (zero YAML, CSV, XML, or database dependencies).
* **Configuration-Driven (Mandatory Discipline 4.1)**: Every feature definition, formula, weight, decision boundary, and missing data policy resides in `/config/` JSON files with full mathematical derivations.
* **Complete Provenance & Lineage (Requirement 2.6)**: Every computed score and rank carries cryptographic SHA-256 digests and version tags tracing back to underlying feature inputs.
* **Graceful Degradation (Mandatory Discipline 4.4)**: Handles missing features, sparse operating histories, and extreme outliers without runtime failure or silent imputation.
* **Deterministic Execution (Mandatory Discipline 4.2)**: Fixed seeds (`seed=42`) guarantee byte-identical outputs across repeated runs.

---

## 2. Deliverables Index (D1 to D13)

| Ref. | Deliverable Title | Location in Package | Description |
| :--- | :--- | :--- | :--- |
| **D1** | **Feature Definition Specification** | [`config/feature_definitions.json`](file:///c:/auditagencyPerformance/config/feature_definitions.json), [`docs/D1_feature_definitions.md`](file:///c:/auditagencyPerformance/docs/D1_feature_definitions.md) | Operational definitions, ranges, units, and missing-data rules for all 6 features. |
| **D2** | **Synthetic Dataset Generator** | [`data/generator.py`](file:///c:/auditagencyPerformance/data/generator.py), [`data/synthetic_auditing_agencies.json`](file:///c:/auditagencyPerformance/data/synthetic_auditing_agencies.json) | Seeded synthetic generator producing 500 agencies with realistic irregularity injection. |
| **D3** | **Classification Pipeline** | [`src/models/pipeline.py`](file:///c:/auditagencyPerformance/src/models/pipeline.py), [`config.json`](file:///c:/auditagencyPerformance/config.json), [`config/model_config.json`](file:///c:/auditagencyPerformance/config/model_config.json) | 4 model architectures (Baseline, GBDT, SVM, MLP) dynamically loaded from config.json. |
| **D4** | **Evaluation Harness & Results** | [`output/evaluation_results.json`](file:///c:/auditagencyPerformance/output/evaluation_results.json), [`src/models/evaluate.py`](file:///c:/auditagencyPerformance/src/models/evaluate.py) | Accuracy, precision, recall, macro-F1, confusion matrices, and per-class breakdowns. |
| **D5** | **Scoring & Ranking Engine** | [`src/scoring/engine.py`](file:///c:/auditagencyPerformance/src/scoring/engine.py), [`src/scoring/ranking.py`](file:///c:/auditagencyPerformance/src/scoring/ranking.py), [`config/scoring_config.json`](file:///c:/auditagencyPerformance/config/scoring_config.json) | Continuous performance scoring, boundary case detection, and competition ranking. |
| **D6** | **Version-Controlled Schema & Registry** | [`src/versioning/registry.py`](file:///c:/auditagencyPerformance/src/versioning/registry.py), [`config/version_registry.json`](file:///c:/auditagencyPerformance/config/version_registry.json) | Immutable version registry, change history, and provenance verification. |
| **D7** | **Air-Gapped Deployment Suite** | [`deploy/verify_offline_install.py`](file:///c:/auditagencyPerformance/deploy/verify_offline_install.py), [`deploy/airgap_packager.py`](file:///c:/auditagencyPerformance/deploy/airgap_packager.py), [`deploy/airgap_update_process.md`](file:///c:/auditagencyPerformance/deploy/airgap_update_process.md) | Offline install verification, cryptographic manifest, and chain-of-custody SOP. |
| **D8** | **Automated Acceptance Test Suite** | [`tests/test_acceptance.py`](file:///c:/auditagencyPerformance/tests/test_acceptance.py), [`tests/test_scoring.py`](file:///c:/auditagencyPerformance/tests/test_scoring.py), [`tests/test_generator.py`](file:///c:/auditagencyPerformance/tests/test_generator.py) | Full automated suite implementing Section 6 Acceptance Tests 1 through 8. |
| **D9** | **Sample JSON Outputs** | [`output/sample_rankings.json`](file:///c:/auditagencyPerformance/output/sample_rankings.json), [`output/sample_organisation_scores.json`](file:///c:/auditagencyPerformance/output/sample_organisation_scores.json) | Per-organisation scores with point contributions and global ranking leaderboard. |
| **D10** | **Design & Derivation Document** | [`docs/D10_design_and_derivation.md`](file:///c:/auditagencyPerformance/docs/D10_design_and_derivation.md) | AHP weight derivations, boundary formulas, and scoring rules. |
| **D11** | **Operational Runbook** | [`docs/D11_runbook.md`](file:///c:/auditagencyPerformance/docs/D11_runbook.md) | Step-by-step fresh clone installation, execution commands, and output interpretation. |
| **D12** | **Results & Analysis Document** | [`docs/D12_results_and_analysis.md`](file:///c:/auditagencyPerformance/docs/D12_results_and_analysis.md) | Empirical analysis, boundary cases, feature importance, and proof-of-concept disclaimer. |
| **D13** | **Comparative Study of Models** | [`docs/D13_comparative_study.md`](file:///c:/auditagencyPerformance/docs/D13_comparative_study.md) | 7-criterion comparative study across 5 components with academic citations. |

---

## 3. Quick Start & Execution

### 3.1 Fresh-Clone Installation
```powershell
python -m pip install -r requirements.txt
```

### 3.2 Verify Air-Gapped Offline Readiness
```powershell
python deploy/verify_offline_install.py
```

### 3.3 Run the Complete Pipeline (Single Command)
```powershell
python -m src.cli --all
```

### 3.4 Run Automated Acceptance Tests (Section 6 Tests 1 to 8)
```powershell
python -m pytest tests/ -v
```

### 3.5 Trace Provenance for an Individual Organisation
```powershell
python -m src.cli --trace-org AUDIT_ORG_0179
```

### 3.6 Launch Interactive Monitoring API & Dashboard
```powershell
# Start FastAPI backend:
python -m uvicorn backend.main:app --port 8000
```
Interactive documentation is available at `http://localhost:8000/docs`.

### 3.7 Ingest Raw Agency Data and Score (New Raw Format)
```powershell
# POST raw operational JSON — features are auto-derived server-side:
curl -X POST http://localhost:8000/api/organisations/ingest-raw `
  -H "Content-Type: application/json" `
  --data-binary "@path/to/agency_raw.json"
```
Or submit the raw data to `/api/organisations/ingest-and-rank` — the endpoint auto-detects the format.

---

## 5. Raw Input Format & Automatic Feature Derivation

The ingest endpoints accept the **raw operational JSON** directly from audit management systems.  
All six scoring features are **derived automatically** server-side — no pre-computation required.

### 5.1 Raw Input Schema

```json
{
  "organisations": [
    {
      "organisation_id": "AGENCY_001",
      "organisation_name": "Sample Audit Agency 001",
      "audits": [
        {
          "audit_id": "AUD_001",
          "scheduled_start_date": "2026-01-05",
          "actual_start_date":    "2026-01-06",
          "contractual_milestone_date": "2026-01-20",
          "report_submission_date":     "2026-01-18",
          "report_status": "submitted",
          "report_findings": [
            { "finding_id": "F001", "review_status": "accepted" },
            { "finding_id": "F002", "review_status": "discrepancy" }
          ]
        }
      ],
      "auditors": [
        { "auditor_id": "EMP_001", "certified": true,  "experience_start_date": "2018-06-01" },
        { "auditor_id": "EMP_002", "certified": true,  "experience_start_date": "2020-04-15" },
        { "auditor_id": "EMP_003", "certified": false, "experience_start_date": "2021-07-10" }
      ],
      "compliance_assessments": [
        {
          "assessment_date": "2026-06-15",
          "controls": [
            { "control_id": "CTRL-001", "applicable": true,  "result": "pass" },
            { "control_id": "CTRL-002", "applicable": true,  "result": "pass" },
            { "control_id": "CTRL-003", "applicable": true,  "result": "fail" },
            { "control_id": "CTRL-004", "applicable": false, "result": null  }
          ]
        }
      ],
      "renewal_history": [
        { "renewal_date": "2024-06-01", "decision": "renewed", "sanction": false },
        { "renewal_date": "2025-06-01", "decision": "renewed", "sanction": false },
        { "renewal_date": "2026-06-01", "decision": "renewed", "sanction": false }
      ]
    }
  ]
}
```

### 5.2 Feature Derivation Rules

| Feature | Source Section | Formula |
| :--- | :--- | :--- |
| **Audit Timeliness** | `audits` | `(submitted audits where submission_date ≤ milestone_date) / total_submitted × 100` |
| **Audit Efficiency** | `audits` | `clamp((45 / avg_days_from_actual_start_to_submission) × 100, 0, 100)` |
| **Error Rate** | `audits → report_findings` | `(submitted audits with ≥1 finding.review_status == "discrepancy") / total_submitted × 100` |
| **Agency Scale** | `auditors` | `min(100, (certified_count/50)×60 + (years_since_earliest_start/20)×40)` |
| **Compliance Adherence** | `compliance_assessments` | `(applicable controls with result == "pass") / total_applicable × 100` (latest assessment) |
| **Past Renewal Status** | `renewal_history` | `(renewals with decision == "renewed" AND sanction == false) / total_renewals × 100` |

> **Missing data**: If a section is absent or incomplete, the corresponding feature is set to `null` and excluded from scoring with weight renormalisation (Mandatory Discipline 4.4).

### 5.3 Worked Example (AGENCY_001 from Sample)

| Feature | Raw Data | Derived Value |
| :--- | :--- | :--- |
| Audit Timeliness | 2 submitted; AUD_001 on-time, AUD_002 late | `(1/2) × 100 = 50.0` |
| Audit Efficiency | AUD_001: 12 days; AUD_002: 16 days → avg 14 days | `(45/14) × 100 = 100.0` (clamped) |
| Error Rate | AUD_001 has discrepancy (F002); AUD_002 clean | `(1/2) × 100 = 50.0` |
| Agency Scale | 2 certified; earliest start 2018-06-01 (~8.2 yrs) | `min(100, (2/50)×60 + (8.2/20)×40) = 18.8` |
| Compliance Adherence | 3 applicable; CTRL-001, CTRL-002 pass; CTRL-003 fail | `(2/3) × 100 = 66.7` |
| Past Renewal Status | 3 renewals; all renewed, no sanction | `(3/3) × 100 = 100.0` |

### 5.4 API Endpoints for Raw Input

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/organisations/ingest-raw` | `POST` | Derive features + score only (fast, no ranking recalc) |
| `/api/organisations/ingest-and-rank` | `POST` | Derive features + score + full global ranking recalc |
| `/api/organisations/sample-template` | `GET` | Returns both raw and pre-computed format examples |

---

## 6. Dynamic Model Parameter Loading from `config.json`

In accordance with **Mandatory Discipline 4.1 (No Hardcoded Constants)**, 100% of machine learning model architectures, hyperparameters, cross-validation parameters, and preprocessing steps are loaded dynamically from [`config.json`](file:///c:/auditagencyPerformance/config.json) (or [`config/model_config.json`](file:///c:/auditagencyPerformance/config/model_config.json)).

### 6.1 Model Configuration Schema (`config.json`)

```json
{
  "version": "1.0.0",
  "selected_model": "gradient_boosting",
  "random_seed": 42,
  "train_test_split": {
    "test_size": 0.20,
    "stratify": true
  },
  "cross_validation": {
    "n_splits": 5,
    "shuffle": true,
    "scoring": "f1_macro"
  },
  "feature_order": [
    "audit_timeliness",
    "audit_efficiency",
    "error_rate",
    "agency_scale",
    "compliance_adherence",
    "past_renewal_status"
  ],
  "target_classes": [
    "renew",
    "review",
    "do_not_renew"
  ],
  "preprocessing": {
    "imputer_strategy": "median",
    "scale_continuous": true
  },
  "models": [
    {
      "id": "baseline",
      "name": "Threshold Heuristic Baseline",
      "type": "heuristic",
      "parameters": {
        "renew_cutoff": 70.0,
        "review_cutoff": 50.0
      }
    },
    {
      "id": "gradient_boosting",
      "name": "Gradient Boosted Decision Trees",
      "type": "ensemble",
      "parameters": {
        "n_estimators": 100,
        "learning_rate": 0.05,
        "max_depth": 3,
        "subsample": 0.8,
        "random_state": 42
      }
    },
    {
      "id": "svm",
      "name": "Support Vector Machine (RBF Kernel)",
      "type": "kernel_machine",
      "parameters": {
        "C": 1.0,
        "kernel": "rbf",
        "gamma": "scale",
        "probability": true,
        "random_state": 42
      }
    },
    {
      "id": "neural_network",
      "name": "Multi-Layer Perceptron (MLP)",
      "type": "neural_network",
      "parameters": {
        "hidden_layer_sizes": [64, 32],
        "activation": "relu",
        "alpha": 0.001,
        "max_iter": 500,
        "early_stopping": true,
        "random_state": 42
      }
    }
  ]
}
```

### 6.2 Modifying Model Parameters
Modifying any model hyperparameter in `config.json` (such as increasing `n_estimators`, changing `learning_rate`, adjusting tree `max_depth`, tweaking neural network `hidden_layer_sizes`, or altering heuristic cutoffs) immediately takes effect across the training and evaluation harness without modifying Python source code.

---

## 7. Acceptance Testing Summary (Section 6)

| # | Test Name | Verification Command | Status |
| :-: | :--- | :--- | :-: |
| **1** | Fresh-clone execution | `python -m src.cli --all` | **PASS** |
| **2** | Offline install verification | `python deploy/verify_offline_install.py` | **PASS** |
| **3** | Feature coverage check | `python -m pytest tests/test_acceptance.py -k test_acceptance_3` | **PASS** |
| **4** | Determinism check (3 runs byte-identical) | `python -m pytest tests/test_acceptance.py -k test_acceptance_4` | **PASS** |
| **5** | Scoring config independence check | `python -m pytest tests/test_acceptance.py -k test_acceptance_5` | **PASS** |
| **6** | Irregular input check (missing/outliers) | `python -m pytest tests/test_acceptance.py -k test_acceptance_6` | **PASS** |
| **7** | Versioning & immutability check | `python -m pytest tests/test_acceptance.py -k test_acceptance_7` | **PASS** |
| **8** | Model comparison check (4 models) | `python -m pytest tests/test_acceptance.py -k test_acceptance_8` | **PASS** |
| **9** | Model parameter dynamic config check | `python -m pytest tests/test_acceptance.py -k test_acceptance_9` | **PASS** |
