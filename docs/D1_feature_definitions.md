# Deliverable D1: Feature Definition and Operational Specification

**Project**: Development of AI-Based Solution for Analysing, Benchmarking and Quality Monitoring of Cybersecurity Audit Reports and Performance Monitoring of Auditing Organisations  
**Document Ref**: D1-FEATURE-SPEC-2026  
**Classification**: Strictly Confidential  

---

## 1. Overview & Architectural Principles

This document sets out the precise operational definitions, mathematical computation methods, permitted units and ranges, missing-data handling rules, and institutional justifications for the six core features governing empanelled cybersecurity auditing organisations.

To preserve configuration independence (Mandatory Discipline 4.1), all numerical constants, boundaries, and policies specified herein reside in `config/feature_definitions.json` and `config/scoring_config.json`.

---

## 2. Feature Definitions Specification Matrix

### Feature 1: Audit Timeliness (`audit_timeliness`)
* **Operational Definition**: The proportion of statutory and contractual cybersecurity audit milestone reports delivered to the empanelment authority on or before the contractual milestone due date within the evaluation cycle.
* **Mathematical Formulation**:
  $$\text{Audit Timeliness} = \left(\frac{N_{\text{on-time milestones}}}{N_{\text{total scheduled milestones}}}\right) \times 100$$
* **Units & Permitted Range**: Percentage ($0.0\%$ to $100.0\%$).
* **Direction**: Higher is better.
* **Treatment of Missing / Partial Data**: If $N_{\text{total scheduled milestones}} = 0$ (e.g., agency had no active audit engagements scheduled during the cycle), the feature is marked as `not_assessable`. Under the `exclude_and_renormalise` policy, its weight is redistributed proportionately across remaining assessable features without punitive default assignment.
* **Justification**: In cybersecurity compliance oversight, timely reporting is critical to ensure critical vulnerabilities (e.g., zero-day exploits, misconfigurations) are remediated within mandatory SLAs. Protracted delays leave critical national infrastructure vulnerable.

---

### Feature 2: Audit Efficiency (`audit_efficiency`)
* **Operational Definition**: An operational velocity index measuring the average calendar days taken from audit initiation (kick-off) to final report issuance, measured relative to the national benchmark standard of 45 days.
* **Mathematical Formulation**:
  $$\text{Audit Efficiency} = \text{clamp}\left(\frac{T_{\text{benchmark days}}}{\max(T_{\text{observed average days}}, 1.0)} \times 100, 0.0, 100.0\right)$$
  Where $T_{\text{benchmark days}} = 45.0$.
* **Units & Permitted Range**: Normalized Index Points ($0.0$ to $100.0$).
* **Direction**: Higher is better.
* **Treatment of Missing / Partial Data**: If no audit engagements were concluded during the evaluation window, this feature is flagged as `not_assessable` and logged in the output provenance record.
* **Justification**: Audit efficiency prevents protracted audit cycles and resource bloat while benchmarking institutional velocity against standard regulatory norms.

---

### Feature 3: Error Rate (`error_rate`)
* **Operational Definition**: The percentage of published audit reports requiring post-submission errata, technical corrections, or rejected during supervisory review due to methodological discrepancies, inaccurate vulnerability severities (e.g., CVSS score miscalculations), or missed critical findings.
* **Mathematical Formulation**:
  $$\text{Error Rate} = \left(\frac{N_{\text{discrepant reports}}}{N_{\text{total submitted reports}}}\right) \times 100$$
  In scoring aggregation, the feature is converted to a Quality Index:
  $$\text{Quality Index} = 100.0 - \text{Error Rate}$$
* **Units & Permitted Range**: Percentage ($0.0\%$ to $100.0\%$).
* **Direction**: Lower is better (inverted during scoring).
* **Treatment of Missing / Partial Data**: If $N_{\text{total submitted reports}} = 0$, marked as `not_assessable`.
* **Justification**: Report accuracy is the cornerstone of trust in cybersecurity assurance. Methodological errors and missed vulnerabilities undermine national security and regulatory integrity.

---

### Feature 4: Agency Scale (`agency_scale`)
* **Operational Definition**: A composite organizational capacity index evaluating the depth of certified cybersecurity audit personnel (CISA, CISSP, CEH, ISO 27001 Lead Auditor) and years of active operational experience in cybersecurity assurance.
* **Mathematical Formulation**:
  $$\text{Agency Scale} = \min\left(100.0, \left(\frac{N_{\text{certified auditors}}}{50.0}\right) \times 60.0 + \left(\frac{Y_{\text{operational experience}}}{20.0}\right) \times 40.0\right)$$
* **Units & Permitted Range**: Continuous Score ($0.0$ to $100.0$).
* **Direction**: Higher is better.
* **Treatment of Missing / Partial Data**: If staffing rosters or incorporation verification documents are incomplete or unverified, marked as `not_assessable`.
* **Justification**: Complex enterprise cybersecurity audits require sufficient staffing redundancy and institutional maturity to withstand staff turnover and deliver robust peer reviews.

---

### Feature 5: Compliance Adherence (`compliance_adherence`)
* **Operational Definition**: The percentage of mandatory supervisory cybersecurity auditing standards, methodologies, and quality assurance controls satisfied during regulatory oversight inspections.
* **Mathematical Formulation**:
  $$\text{Compliance Adherence} = \left(\frac{C_{\text{verified controls passed}}}{C_{\text{mandatory controls applicable}}}\right) \times 100$$
* **Units & Permitted Range**: Percentage ($0.0\%$ to $100.0\%$).
* **Direction**: Higher is better.
* **Treatment of Missing / Partial Data**: If no formal supervisory inspection occurred within the preceding 24 months, marked as `not_assessable`.
* **Justification**: Mandates adherence to established national frameworks (e.g., CERT-In empanelment standards, ISO/IEC 17020, NIST SP 800-115).

---

### Feature 6: Past Renewal Status (`past_renewal_status`)
* **Operational Definition**: The historical track record reflecting the proportion of past empanelment cycles successfully renewed without formal reprimand, sanctions, or temporary revocations.
* **Mathematical Formulation**:
  $$\text{Past Renewal Status} = \left(\frac{N_{\text{successful renewals}}}{N_{\text{total renewal attempts}}}\right) \times 100$$
* **Units & Permitted Range**: Percentage ($0.0\%$ to $100.0\%$).
* **Direction**: Higher is better.
* **Treatment of Missing / Partial Data**: For newly empanelled organisations ($N_{\text{total renewal attempts}} = 0$), this feature is recorded as `not_assessable` (new entrant status), avoiding bias against newly qualified agencies.
* **Justification**: Provides longitudinal empirical validation of an organisation's institutional integrity and sustained quality over multi-year empanelment cycles.
