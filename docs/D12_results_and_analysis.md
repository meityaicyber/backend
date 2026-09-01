# Deliverable D12: Results and Performance Analysis

**Project**: Development of AI-Based Solution for Analysing, Benchmarking and Quality Monitoring of Cybersecurity Audit Reports and Performance Monitoring of Auditing Organisations  
**Document Ref**: D12-RESULTS-ANALYSIS-2026  
**Classification**: Strictly Confidential  

---

## 1. Mandatory Statement of Limits & Proof-of-Concept Status

> [!CAUTION]
> **DISCLAIMER OF SYNTHETIC VALIDATION (Mandatory Discipline 4.5)**:
> The empirical results, model accuracies, and rankings presented in this report were generated exclusively using a synthetic population of 500 auditing organisations produced by an algorithmic generator (`data/generator.py`), against renewal outcome labels derived from a synthetic decision rule.
>
> While the generator incorporates realistic irregularities (missing features, sparse operating histories, skewed distributions, and extreme outliers), these results constitute a **Proof of Concept (PoC)** demonstrating algorithmic correctness, pipeline determinism, and air-gapped readiness. They do **not** constitute an empirically validated operational performance-monitoring system for production regulatory deployment.

---

## 2. Experimental Setup & Population Characteristics

* **Total Organisations ($N$)**: 500
* **Irregular Records Injected**: 77 ($15.4\%$)
* **Class Distribution**:
  * `renew`: 317 organisations ($63.4\%$)
  * `review`: 159 organisations ($31.8\%$)
  * `do_not_renew`: 24 organisations ($4.8\%$)
* **Train / Test Split**: 400 train ($80\%$) / 100 test ($20\%$), stratified by class (configured in `config.json`).
* **Cross-Validation**: 5-Fold Stratified Cross-Validation on training split.
* **Random Seed**: Fixed at `42` for 100% byte-level reproducibility (configured in `config.json`).
* **Model Configurations**: All 4 model hyperparameters loaded dynamically from `config.json` / `config/model_config.json`.

---

## 3. Model Benchmark Comparison

The four classification architectures were evaluated on identical holdout test sets and 5-fold cross validation.

| Model Architecture | Test Accuracy | Test Macro-F1 | 5-Fold CV Mean Macro-F1 | 5-Fold CV Std | Offline Suitability | Interpretability |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Rule-Based Baseline** | **0.9700** | **0.8991** | 0.8482 | $\pm 0.0456$ | High | Maximum (Exact rules) |
| **Gradient Boosted Trees (Selected)** | 0.8900 | 0.7570 | **0.9286** | $\pm 0.0293$ | High | High (Feature importance) |
| **Support Vector Machine (RBF)** | 0.9500 | 0.8263 | 0.9024 | $\pm 0.0678$ | High | Low (Black-box kernel) |
| **Neural Network (MLP)** | 0.9000 | 0.6019 | 0.7907 | $\pm 0.1155$ | Medium | Low (Dense weights) |

### Key Observations:
1. **Cross-Validation Superiority of Gradient Boosting**: Gradient Boosted Trees achieved the highest cross-validation stability ($0.9286 \pm 0.0293$), demonstrating robust generalization across folds and resilience against irregular feature patterns.
2. **Support Vector Machine Performance**: SVM demonstrated strong test accuracy ($0.9500$), but showed higher variance across cross-validation folds ($0.9024 \pm 0.0678$).
3. **Neural Network Limitations on Small Datasets**: The Multi-Layer Perceptron struggled on the minority class (`do_not_renew`, 24 total samples), resulting in lower macro-F1 ($0.6019$), underscoring that deep learning architectures are suboptimal for tabular datasets with $< 10,000$ records.

---

## 4. Boundary Case and Edge-Case Analysis

Out of 500 organisations evaluated by the scoring engine:
* **Renewed ($\ge 70.0$)**: 296 ($59.2\%$)
* **Under Review ($50.0 \le S < 70.0$)**: 189 ($37.8\%$)
* **Do Not Renew ($< 50.0$)**: 15 ($3.0\%$)
* **Flagged Boundary Cases**: **94 organisations** ($18.8\%$)

### Why Boundary Flagging is Crucial:
Rather than asserting artificial certainty near decision thresholds, the module explicitly flagged 94 organisations whose continuous score fell within $\pm 3.0$ points of the 70.0 or 50.0 thresholds. These organisations are automatically tagged with `boundary_annotation` alerting regulatory reviewers to conduct an expedited qualitative review.

---

## 5. Feature Importance & Contribution Insights

Feature importance analysis extracted from the selected Gradient Boosting model reveals:
1. **Compliance Adherence ($26.4\%$)**: The strongest single predictor of renewal outcome.
2. **Error Rate ($24.1\%$)**: Material errors in audit reports heavily penalized non-renewals.
3. **Audit Timeliness ($21.8\%$)**: Milestone punctuality separated the top-quartile agencies.
4. **Audit Efficiency ($13.2\%$)** & **Past Renewal ($9.8\%$)**: Provided secondary differentiation.
5. **Agency Scale ($4.7\%$)**: Minimum baseline necessary, but team size alone does not guarantee renewal without quality execution.
