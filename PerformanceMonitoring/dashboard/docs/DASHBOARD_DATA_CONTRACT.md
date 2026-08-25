# Dashboard Data Contract

This document maps the dashboard UI elements to the authoritative JSON output files produced by the backend `PerformanceMonitoring` system. The dashboard is strictly read-only and relies entirely on these pre-generated artifacts.

## Overview
- **Authoritative Source File:** `output/scoring/ranking_summary.json`
- **Fields Used:**
  - `metadata.total_organisations` -> Organisation count
  - `metadata.assessable_organisations` -> Total assessed count
  - `metadata.provenance` -> For config/version/seed metadata
  - `bottom_10` / `top_10` (or derived from full dataset) -> Score extremes
- **Notes:** Full distribution can be drawn by loading `output/scoring/organisation_scores.json`.

## Ranking
- **Authoritative Source File:** `output/scoring/organisation_scores.json`
- **Fields Used:**
  - `[].rank` -> Authoritative ordering
  - `[].organisation_id` -> Org ID
  - `[].performance_score` -> Score
  - `[].renewal_prediction.class` -> Renewal Prediction
  - `[].renewal_prediction.probability` -> Probability
  - `[].renewal_prediction.boundary_status` -> Boundary Flag
  - `[].assessment_status` -> Assessability status

## Organisation Detail
- **Authoritative Source File(s):** 
  - `output/scoring/organisation_scores.json` (for ranks, scores, predictions, missing features)
  - `data/sample_dataset.json` (for raw feature values)
- **Fields Used:**
  - `[].features` (from `sample_dataset.json`)
  - `[].provenance` (from `organisation_scores.json`)
- **Notes:** Score components must be read from backend outputs.

## Model Comparison
- **Authoritative Source File:** `output/evaluation/comparison_summary.json`
- **Fields Used:**
  - `baseline`, `gradient_boosting`, `svm`, `neural_network` -> metrics paths (`accuracy`, `macro_f1`, etc.)
- **Notes:** Used to display exactly the models required without recalculation.

## Data Quality
- **Authoritative Source File(s):**
  - `output/scoring/organisation_scores.json`
  - `data/sample_dataset.json`
- **Fields Used:**
  - `missing_features` array in scores
  - `assessment_status` in scores ("not_assessable")
- **Notes:** Handles missing/outlier aggregation.

## Versions
- **Authoritative Source File:** `config/version_registry.json`
- **Fields Used:**
  - `current_versions` -> active versions
  - `history` -> array of changes (timestamp, change, approver, updated_components)
- **Notes:** Enables historical traceability.

## Acceptance Tests
- **Authoritative Source File:** `tests/.pytest_cache/...` (or a dumped test report JSON)
- **Notes:** Wait, pytest doesn't naturally output JSON unless configured. I will configure pytest to output a JSON report to `output/test_report.json` so the dashboard can consume it.

---

### Dashboard Principle
No authoritative score is recalculated. The dashboard is purely a UI presentation layer mapping over these JSON structures. Missing files will trigger explicit UI errors, not silent fallbacks.
