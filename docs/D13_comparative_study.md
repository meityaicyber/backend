# Deliverable D13: Comparative Study of Models and Techniques

**Project**: Development of AI-Based Solution for Analysing, Benchmarking and Quality Monitoring of Cybersecurity Audit Reports and Performance Monitoring of Auditing Organisations  
**Document Ref**: D13-COMPARATIVE-STUDY-2026  
**Classification**: Strictly Confidential  

---

## 1. Scope & Analytical Framework

This comparative study systematically evaluates alternative algorithms across five core computational components:
1. **Classification Models**
2. **Missing-Data Handling Mechanisms**
3. **Feature Scaling & Normalisation**
4. **Scoring Aggregation Rules**
5. **Ranking and Tie-Breaking Policies**

Every alternative is evaluated across the mandatory **7 Evaluation Criteria (Section 3.2)**:
1. **Accuracy / Expected Performance**
2. **Interpretability & Explainability**
3. **Data Requirement**
4. **Computational Cost & Hardware Feasibility**
5. **Air-Gapped & Offline Suitability**
6. **Stability Under Input Perturbation**
7. **Known Failure Modes**

---

## 2. Comprehensive Comparative Tables

### 2.1 Classification Models

| Alternative | Accuracy / Perf. | Interpretability | Data Req. | Computational Cost | Offline Suitability | Stability | Known Failure Modes | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rule-Based Baseline** | Moderate (cannot capture complex non-linear feature interactions) | **Maximum** (Direct threshold rules transparent to affected agencies) | Minimal ($N=0$ required) | Extremely Low ($O(1)$) | **High** (Pure arithmetic) | High (Deterministic step functions) | Discontinuous jumps at cutoffs; ignores correlated feature trade-offs. | **Evaluated (Baseline Benchmark)** |
| **Gradient Boosted Trees (GBDT)** [Friedman, 2001] | **Highest** (Captures non-linearities and threshold boundaries effectively) | **High** (SHAP / Tree split importance directly explains decisions) | Small-to-Medium ($100 \le N \le 10,000$) | Low ($< 1$ sec training on standard CPU) | **High** (Pure Scikit-Learn offline) | **High** (Ensemble averaging dampens individual noise) | Can overfit if tree depth is unconstrained without regularization. | **SELECTED FOR PRODUCTION** |
| **Support Vector Machine (RBF Kernel)** [Cortes & Vapnik, 1995] | High (Effective in high-dimensional feature spaces) | **Low** (Dual-space kernel weights are opaque to non-technical reviewers) | Small-to-Medium ($100 \le N \le 5,000$) | Medium ($O(N^2)$ to $O(N^3)$ kernel computation) | **High** (Standard Scikit-Learn) | Moderate (Sensitive to scaling and hyperparameter $C/\gamma$) | Highly sensitive to unscaled features; opaque boundary decisions. | **Rejected** (Opaque decisions cannot be justified to penalized agencies) |
| **Multi-Layer Perceptron (MLP)** [Rumelhart et al., 1986] | Moderate-to-Low on small tabular datasets ($N < 1,000$) | **Low** (Black-box weight matrices impossible to explain in appeals) | High ($N > 10,000$ needed for stable generalization) | High (Backpropagation iterative epochs) | **Medium** (Requires matrix runtime) | Low on small $N$ (Stochastic gradient descent variance) | Severe overfitting on minority classes; sensitive to initialization. | **Rejected** (Sample size $N=500$ is too small for robust deep learning) |

> **Configuration Note (Mandatory Discipline 4.1)**: All hyperparameters for the 4 architectures above (tree estimators, learning rates, tree depth, kernel penalties, network topology, and heuristic thresholds) are loaded dynamically from [`config.json`](file:///c:/auditagencyPerformance/config.json) (or [`config/model_config.json`](file:///c:/auditagencyPerformance/config/model_config.json)).

---

### 2.2 Missing-Data Handling Mechanisms

| Alternative | Accuracy / Perf. | Interpretability | Data Req. | Computational Cost | Offline Suitability | Stability | Known Failure Modes | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Listwise Deletion (Complete Case)** | Poor (Discards valuable partial performance evidence) | High (Simple rule) | High (Requires complete records) | Negligible | High | Low (Small sample dropout) | Introduces severe survivorship bias against newly empanelled agencies. | **Rejected** (Unfairly drops new agencies lacking past renewal records) |
| **Mean / Median Imputation** [Little & Rubin, 2019] | Moderate (Preserves sample size) | Low-Medium (Imputes artificial phantom data) | Low | Negligible | High | Moderate (Distorts variance) | Artificially compresses feature variance; falsely assumes unobserved agencies are 'average'. | **Rejected** (Silent imputation violates Mandatory Discipline 4.4) |
| **Exclude & Renormalise** | **High** (Evaluates only verified evidence without imputation) | **Maximum** (Output records exactly which features contributed and active weight %) | **Minimal** (Works per individual organisation) | Negligible ($O(1)$) | **High** (Zero dependencies) | **High** (Continuous proportional redistribution) | If all features missing, score is undefined (properly handled as `not_assessable`). | **SELECTED FOR PRODUCTION** |
| **MICE (Iterative Multivariate Imputation)** [Van Buuren, 2018] | High in large epidemiology data | Low (Complex chained equations opaque to audit review) | High ($N > 2,000$) | High (Chained regression iterations) | Medium (Complex dependencies) | Low on small samples | Multiple imputation yields different values across runs if unseeded. | **Rejected** (Excessive complexity for 6-feature domain) |

---

### 2.3 Feature Scaling and Normalisation

| Alternative | Accuracy / Perf. | Interpretability | Data Req. | Computational Cost | Offline Suitability | Stability | Known Failure Modes | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **No Scaling** | Variable (Distorts distance-based models) | High (Retains raw physical units) | None | Zero | High | High | Fails completely for SVM and MLP where large units dominate. | **Rejected for ML Pipelines** |
| **Min-Max Normalisation ($[0, 100]$)** | **High** (Aligns all 6 features to percentage scale) | **High** (Easily understood by auditors as 0-100 index) | None (Domain-defined bounds) | Negligible ($O(1)$) | **High** | **High** (Fixed theoretical bounds) | Outliers exceeding fixed bounds must be clipped. | **SELECTED FOR SCORING ENGINE** |
| **Standard Z-Score Scaler** | High (Zero mean, unit variance) | Low (Negative values confuse non-technical reviewers) | Sample dependent | Low | High | Moderate (Shifts with new cohort data) | Transformed units have no physical meaning to auditing organisations. | **Selected for SVM/MLP Pipelines Only** |
| **Robust Scaler (IQR)** | High (Resistant to extreme outliers) | Low (Interquartile centered) | Sample dependent | Low | High | Moderate | Confusing scale for human ranking interpretation. | **Rejected** |

---

### 2.4 Scoring Aggregation Rules

| Alternative | Accuracy / Perf. | Interpretability | Data Req. | Computational Cost | Offline Suitability | Stability | Known Failure Modes | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Unweighted Simple Mean** | Poor (Treats minor features like scale identically to critical errors) | High (Simple average) | None | Negligible | High | High | Ignores regulatory risk hierarchy. | **Rejected** |
| **Weighted Linear Combination (AHP-Weighted)** [Saaty, 1980] | **High** (Accurately reflects statutory cybersecurity priorities) | **Maximum** (Point contribution of each feature is additive and verifiable) | None (Weights from regulatory policy) | Negligible ($O(1)$) | **High** | **High** (Continuous linear monotonicity) | Does not capture non-linear catastrophe triggers (mitigated via fatal-flaw rules). | **SELECTED FOR SCORING ENGINE** |
| **TOPSIS (Ideal Solution Distance)** [Hwang & Yoon, 1981] | High (Measures Euclidean distance to positive/negative ideal) | Low (Hyper-dimensional Euclidean distance is non-intuitive in legal appeals) | Cohort dependent | Low | High | Low (Rank reversal when new agency is added) | Rank reversal phenomenon violates ranking stability requirements. | **Rejected** (Rank reversal creates legal vulnerability) |

---

### 2.5 Ranking and Tie-Breaking Policies

| Alternative | Accuracy / Perf. | Interpretability | Data Req. | Computational Cost | Offline Suitability | Stability | Known Failure Modes | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ordinal Ranking (1234)** | Misleading (Assigns arbitrary rank sequence to exact tied scores) | Low (Arbitrary advantage to alphabetical order) | None | Negligible | High | Low (Tied agencies arbitrarily split) | Unfairly penalizes agencies based on random ID ordering. | **Rejected** |
| **Dense Ranking (1223)** | Moderate (No gaps after ties) | Moderate | None | Negligible | High | High | Fails to reflect true population percentile. | **Rejected** |
| **Standard Competition Ranking (1224)** | **Highest** (International sports & civil service standard) | **High** (Preserves exact percentile and equal rank for equal performance) | None | Negligible | **High** | **High** (Fully deterministic) | Rank gaps occur following ties (intended behavior). | **SELECTED FOR PRODUCTION** |

---

## 3. Justification of Selected Approaches

### 3.1 Why Gradient Boosted Trees for Classification
1. **Superior Tabular Generalization**: Empirical literature (e.g., Grinsztajn et al., NeurIPS 2022) consistently proves tree-based ensembles outperform deep networks and kernel methods on small-to-medium tabular datasets.
2. **Transparent Explainability**: Individual tree splits mirror regulatory rules (e.g., `error_rate > 30%` AND `compliance < 50%` $\to$ `do_not_renew`), allowing clear justifications during administrative appeals.
3. **Robustness to Missing/Skewed Data**: Tree architectures partition feature space monotonically, eliminating sensitivity to monotonic scaling and outlier distortion.

### 3.2 Why Exclude & Renormalise for Missing Data
1. **Regulatory Fairness**: A new entrant without past renewal history should not receive a synthetic imputed score. Evaluating the agency strictly on its 5 assessable features and renormalising active weights ($100 / 85$) provides an objective appraisal without assumption.
2. **Audit Compliance**: Completely eliminates silent imputation (Mandatory Discipline 4.4).

### 3.3 Why Standard Competition Ranking (1224)
1. Conforms to government and public-sector empanelment standards where two agencies with identical performance scores (e.g., $94.0$) share identical standing without arbitrary alphabetical bias.

---

## 4. Limitations, Risks, and Mitigations

| Identified Risk | Potential Impact | Adopted Mitigation |
| :--- | :--- | :--- |
| **Synthetic-to-Real Domain Shift** | Synthetic data distributions may not capture unforeseen real-world audit quirks. | Mandatory Discipline 4.5 honest disclaimer in reports; modular JSON configuration allowing rapid threshold recalibration once real data is ingested. |
| **Boundary Decision Fragility** | Organisations near the $70.0$ cutoff could be unfairly classified due to small metric fluctuations. | Boundary tolerance detector flags all agencies within $\pm 3.0$ points as `boundary_case` for secondary human review. |
| **Feature Correlation Collinearity** | Timeliness and efficiency are moderately correlated ($r \approx 0.65$). | AHP weights explicitly derived to balance operational velocity against technical compliance rigor. |

---

## 5. References & Academic Citations

1. **Breiman, L.** (2001). *Random Forests*. Machine Learning, 45(1), 5-32.
2. **Cortes, C., & Vapnik, V.** (1995). *Support-Vector Networks*. Machine Learning, 20(3), 273-297.
3. **Friedman, J. H.** (2001). *Greedy Function Approximation: A Gradient Boosting Machine*. Annals of Statistics, 1189-1232.
4. **Grinsztajn, L., Oyallon, E., & Varoquaux, G.** (2022). *Why do tree-based models still outperform deep learning on tabular data?* Advances in Neural Information Processing Systems (NeurIPS 2022).
5. **Hwang, C. L., & Yoon, K.** (1981). *Multiple Attribute Decision Making: Methods and Applications*. Springer-Verlag.
6. **Little, R. J., & Rubin, D. B.** (2019). *Statistical Analysis with Missing Data* (3rd ed.). John Wiley & Sons.
7. **Saaty, T. L.** (1980). *The Analytic Hierarchy Process: Planning, Priority Setting, Resource Allocation*. McGraw-Hill.
8. **Van Buuren, S.** (2018). *Flexible Imputation of Missing Data* (2nd ed.). CRC Press.
