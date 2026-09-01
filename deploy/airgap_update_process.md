# Air-Gapped Deployment & Controlled Update Protocol (SOP)

**Classification**: Strictly Confidential  
**System**: Auditing Agency Performance Monitoring & Ranking Module  
**Scope**: Air-Gapped High-Security Enclave Deployment and Schema/Code Updates  

---

## 1. Overview & Operational Constraints

The Auditing Agency Performance Monitoring and Ranking Module is designed for zero-trust, completely isolated (air-gapped) environments with no external network interfaces, cloud APIs, or external telemetry.

All operations—including synthetic data generation, machine learning classification, continuous scoring, tie-broken ranking, and configuration version updates—are executed entirely on-premise using pre-verified local dependencies and pure JSON file formats.

---

## 2. 5-Stage Controlled Air-Gap Update Process

```
+-----------------------------------------------------------------------------------+
| Stage 1: Development, Testing & Release Approval (Connected Staging)               |
|  - Automated test suite execution (Acceptance Tests 1-8)                          |
|  - Formal approval logging with Change Request ID                                 |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Stage 2: Packaging & Cryptographic Manifest Generation                            |
|  - Execute deploy/airgap_packager.py to compute SHA-256 digests                  |
|  - Bundle source, configs, wheels, and manifest into single signed archive        |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Stage 3: Security Screening & Chain-of-Custody Ingestion                          |
|  - Two-person integrity verification (Dual Custody)                               |
|  - Multi-engine antivirus and static malware scanning                             |
|  - Write-once optical / vetted encrypted hardware transfer media                  |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Stage 4: Enclave Extraction & Pre-Activation Verification                         |
|  - Extract package into target isolation workspace                                |
|  - Execute deploy/verify_offline_install.py (integrity and dry-run check)         |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Stage 5: Version Registration & Operational Execution                             |
|  - Register new schema version in config/version_registry.json                    |
|  - Retain immutable historical score snapshots                                    |
|  - Run python -m src.cli --all for updated empanelment ranking                   |
+-----------------------------------------------------------------------------------+
```

---

## 3. Step-by-Step Execution Guide

### Step 3.1: Staging Preparation & Checksum Manifest Generation
On the staging development machine, run the automated test suite and generate the cryptographic manifest:
```powershell
# 1. Run all acceptance tests
python -m pytest tests/test_acceptance.py -v

# 2. Build air-gapped cryptographic manifest
python deploy/airgap_packager.py
```

### Step 3.2: Air-Gapped Media Transfer
1. Transfer the zipped archive `PerformanceMonitoring_<Assignee>_<Date>.zip` to a hardware-encrypted, approved USB device.
2. Verify SHA-256 hash at both transfer boundaries:
   ```powershell
   Get-FileHash -Algorithm SHA256 PerformanceMonitoring_*.zip
   ```
3. Complete the physical Chain-of-Custody logbook recording:
   - Date & Time
   - Transferring Engineer Name & Signature
   - Escort Security Officer Name & Signature
   - SHA-256 Checksum Verification
   - Physical Media Serial Number

### Step 3.3: Ingestion & Offline Installation Verification
Inside the air-gapped secure facility:
1. Extract the bundle to the designated application directory (`C:\auditagencyPerformance`).
2. Run the offline verification test:
   ```powershell
   python deploy/verify_offline_install.py
   ```
   **Expected Outcome**: Verification passes with code 0:
   - Dependencies imported offline: **PASSED**
   - Configuration integrity: **PASSED**
   - SHA-256 manifest check: **PASSED**
   - Scoring engine dry-run: **PASSED**

### Step 3.4: Applying Schema / Scoring Updates
To alter a feature weight or scoring rule without touching code:
1. Modify the target JSON configuration (e.g., `config/scoring_config.json`).
2. Register the change using `src.versioning.registry`:
   ```python
   from src.versioning.registry import VersionRegistry
   reg = VersionRegistry()
   reg.register_version(
       new_version="1.1.0",
       author="Chief Compliance Officer",
       approval_id="EMP-AUTH-2026-09-02",
       description="Updated error_rate weight to 25% following annual audit policy review.",
       changes=["Adjusted error_rate weight from 20 to 25", "Recalibrated boundary tolerance to 2.5"]
   )
   ```
3. Re-run scoring and ranking:
   ```powershell
   python -m src.cli --score-rank
   ```
4. Prior run results in `output/` remain archived and attributable to `1.0.0`.

---

## 4. Rollback and Disaster Recovery

In the event of an anomaly or failed offline verification:
1. Revert to the prior known-good version recorded in `config/version_registry.json`.
2. Historical output scores and ranking JSONs carry their own version and config hashes, preventing data corruption or state loss.
