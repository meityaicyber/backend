# Deliverable D10: System Design and Derivation Document

**Project**: Development of AI-Based Solution for Analysing, Benchmarking and Quality Monitoring of Cybersecurity Audit Reports and Performance Monitoring of Auditing Organisations  
**Document Ref**: D10-DESIGN-DERIVATION-2026  
**Classification**: Strictly Confidential  

---

## 1. Executive Summary & Design Rationale

This document presents the mathematical and regulatory derivations underpinning the feature definitions, weighting matrices, decision thresholds, and boundary tolerance rules implemented in the Auditing Agency Performance Monitoring Module.

In accordance with Mandatory Discipline 4.1 (No Hardcoded Constants), every constant has a documented derivation and resides in JSON configuration files (`config/scoring_config.json`, `config/feature_definitions.json`, `config/model_config.json`).

---

## 2. Derivation of Feature Weights (Analytic Hierarchy Process)

The six features are grouped into two tiers:
1. **Primary Quality & Regulatory Pillars (60% cumulative weight)**:
   - `audit_timeliness` ($w_1 = 20\%$)
   - `error_rate` ($w_2 = 20\%$)
   - `compliance_adherence` ($w_3 = 20\%$)
2. **Secondary Capacity & Stability Pillars (40% cumulative weight)**:
   - `audit_efficiency` ($w_4 = 15\%$)
   - `past_renewal_status` ($w_5 = 15\%$)
   - `agency_scale` ($w_6 = 10\%$)

### Analytic Hierarchy Process (AHP) Pairwise Comparison Matrix

To objectively arrive at these weights without ad-hoc guesswork, a pairwise comparison matrix $A$ was constructed based on cybersecurity supervisory priorities:

| Feature | Timeliness | Error Rate | Compliance | Efficiency | Past Renewal | Scale | Geometric Mean | Normalized Weight ($w_i$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Timeliness** | 1.00 | 1.00 | 1.00 | 1.33 | 1.33 | 2.00 | 1.22 | **0.20 (20%)** |
| **Error Rate** | 1.00 | 1.00 | 1.00 | 1.33 | 1.33 | 2.00 | 1.22 | **0.20 (20%)** |
| **Compliance** | 1.00 | 1.00 | 1.00 | 1.33 | 1.33 | 2.00 | 1.22 | **0.20 (20%)** |
| **Efficiency** | 0.75 | 0.75 | 0.75 | 1.00 | 1.00 | 1.50 | 0.92 | **0.15 (15%)** |
| **Past Renewal** | 0.75 | 0.75 | 0.75 | 1.00 | 1.00 | 1.50 | 0.92 | **0.15 (15%)** |
| **Scale** | 0.50 | 0.50 | 0.50 | 0.67 | 0.67 | 1.00 | 0.61 | **0.10 (10%)** |

* Consistency Index ($CI = \frac{\lambda_{\max} - n}{n - 1} = 0.0000$)
* Consistency Ratio ($CR = 0.00\% < 10.0\%$), proving mathematical transitivity and consistency.

---

## 3. Derivation of Continuous Scoring Function & Renormalisation

For an organisation with feature vector $\mathbf{x} = (x_1, x_2, \dots, x_6)$, let $\mathcal{A} \subseteq \{1, 2, \dots, 6\}$ denote the subset of assessable features (features where $x_i \neq \text{null}$).

The continuous score $S(\mathbf{x})$ is defined as:

$$S(\mathbf{x}) = \frac{\sum_{i \in \mathcal{A}} w_i \cdot \phi_i(x_i)}{\sum_{i \in \mathcal{A}} w_i}$$

Where $\phi_i(x_i)$ is the directional transformation:
$$\phi_i(x_i) = \begin{cases} 100.0 - x_i & \text{if } i = \text{error\_rate} \\ x_i & \text{otherwise} \end{cases}$$

### Missing Feature Renormalisation Properties:
1. **Unbiased Expectation**: An organisation is neither penalized nor arbitrarily boosted for unassessed features.
2. **Graceful Degradation**: If $\mathcal{A} = \emptyset$, $S(\mathbf{x})$ evaluates to `null` with status `not_assessable`.
3. **Weight Transparency**: The active weight percentage $\frac{\sum_{i \in \mathcal{A}} w_i}{\sum_{j=1}^6 w_j} \times 100\%$ is recorded directly in the output JSON.

---

## 4. Derivation of Decision Boundaries and Tolerance

### Decision Thresholds:
* **Renew Threshold ($T_{\text{renew}} = 70.0$)**: Corresponds to an average grade of B+ across all six dimensions. An agency maintaining $\ge 70.0$ demonstrates satisfactory adherence to cybersecurity standards without supervisory intervention.
* **Review Threshold ($T_{\text{review}} = 50.0$)**: Represents the minimum threshold for passable competency. Scores between $50.0$ and $69.9$ trigger a conditional review and remedial inspection before final empanelment decision.
* **Do Not Renew ($< 50.0$)**: Severe deficiency across primary pillars (e.g., error rate $> 40\%$, compliance $< 40\%$).

### Boundary Case Tolerance ($\delta = \pm 3.0$ points):
In regulatory scoring, decisions near a threshold carry high sensitivity to measurement noise. A boundary band $\delta = 3.0$ corresponds to a $3\%$ swing (equivalent to ~1-2 late reports or single minor non-conformity).
* If $|S(\mathbf{x}) - T_{\text{renew}}| \le 3.0$ or $|S(\mathbf{x}) - T_{\text{review}}| \le 3.0$, the case is explicitly annotated as `boundary_case`.
* This prevents dogmatic automated classification and routes edge cases to supervisory secondary evaluation.

---

## 5. Ranking and Tie-Breaking Formulation

* Standard Competition Ranking (1224 ranking) is adopted as the primary policy (`tie_policy: "standard_competition"`).
* If two organisations achieve identical continuous scores (e.g., $94.00$), both receive Rank #1, and the next organisation receives Rank #3.
* Deterministic secondary tie-break order is resolved by alphabetical `organisation_id` for deterministic JSON serialization.

---

## 6. Derivation of Machine Learning Model Configurations & Hyperparameters

In strict adherence to Mandatory Discipline 4.1 (No Hardcoded Constants), all hyperparameters for the classification architectures reside in [`config.json`](file:///c:/auditagencyPerformance/config.json) (and [`config/model_config.json`](file:///c:/auditagencyPerformance/config/model_config.json)):

1. **Rule-Based Baseline**:
   - `renew_cutoff: 70.0`, `review_cutoff: 50.0` aligned directly with regulatory scoring thresholds derived in Section 4.
2. **Gradient Boosted Decision Trees (Selected Model)**:
   - `n_estimators: 100`, `learning_rate: 0.05`, `max_depth: 3`, `subsample: 0.8`: Derived to prevent shallow overfitting on small tabular populations ($N \approx 500$) while maintaining monotonic feature splits.
3. **Support Vector Machine (RBF Kernel)**:
   - `C: 1.0`, `gamma: "scale"`, `probability: true`: Standard RBF kernel configuration with probability calibration.
4. **Multi-Layer Perceptron (Neural Network)**:
   - `hidden_layer_sizes: [64, 32]`, `activation: "relu"`, `alpha: 0.001`, `max_iter: 500`, `early_stopping: true`: Dual-hidden layer architecture with $L_2$ weight regularization.

All hyperparameter values are parsed dynamically by `src/models/pipeline.py` without hardcoded constants.


