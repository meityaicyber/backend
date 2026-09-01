"""Synthetic Dataset Generator for Auditing Agency Performance Monitoring.

Produces reproducible, configurable synthetic populations of cybersecurity auditing
organisations with the six required features, ground truth renewal labels,
and deliberate realistic irregularities (missing values, sparse history, outliers).
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any


class AgencyDataGenerator:
    """Configurable and reproducible synthetic dataset generator for auditing organisations."""

    AGENCY_PREFIXES = [
        "CyberShield", "Apex", "Vanguard", "Sentinel", "CertiAudit",
        "SecureMatrix", "QuantumSec", "TrustLayer", "DefendPoint", "Ironclad",
        "Aegis", "CyberPulse", "Nexus", "Beacon", "Fortress", "Valence",
        "CipherGuard", "IntegritySec", "Pinnacle", "Spectra"
    ]
    AGENCY_SUFFIXES = [
        "Auditing Partners", "Cyber Risk Group", "Assurance Labs",
        "Security Systems", "Compliance Bureau", "Advisory Services",
        "Cybernetics", "Assessment Corp", "Solutions", "Inspect Group"
    ]

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = random.Random(seed)

    def _generate_organisation_name(self, index: int) -> str:
        prefix = self.rng.choice(self.AGENCY_PREFIXES)
        suffix = self.rng.choice(self.AGENCY_SUFFIXES)
        return f"{prefix} {suffix} #{index + 1:03d}"

    def generate(
        self,
        n_samples: int = 500,
        irregularity_rate: float = 0.15,
        output_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Generate a complete synthetic dataset of auditing organisations."""
        self.rng = random.Random(self.seed)
        organisations: list[dict[str, Any]] = []
        irregular_count = 0

        for i in range(n_samples):
            org_id = f"AUDIT_ORG_{i + 1:04d}"
            org_name = self._generate_organisation_name(i)
            is_irregular = self.rng.random() < irregularity_rate
            irregularity_type = None

            # Base latent competence (0.0 to 1.0)
            latent_quality = self.rng.betavariate(3.5, 2.0)

            # 1. Audit Timeliness: Beta distribution correlated with quality
            timeliness_raw = min(100.0, max(0.0, self.rng.gauss(latent_quality * 90 + 5, 12)))

            # 2. Audit Efficiency: Benchmark is 45 days. Average duration between 25 and 80 days
            avg_duration_days = max(15.0, self.rng.gauss(80 - latent_quality * 45, 12))
            efficiency_raw = min(100.0, max(0.0, (45.0 / avg_duration_days) * 100.0))

            # 3. Error Rate: Discrepancy % (lower is better)
            error_rate_raw = min(100.0, max(0.0, self.rng.gauss((1.0 - latent_quality) * 28 + 2, 7.5)))

            # 4. Agency Scale: Team size and years experience
            certified_auditors = max(3, int(self.rng.lognormvariate(2.8, 0.6)))
            years_experience = max(1, min(30, int(self.rng.gauss(latent_quality * 12 + 4, 4))))
            agency_scale_raw = min(100.0, (certified_auditors / 50.0) * 60.0 + (years_experience / 20.0) * 40.0)

            # 5. Compliance Adherence: Pass rate on mandatory supervisory controls (%)
            compliance_adherence_raw = min(100.0, max(15.0, self.rng.gauss(latent_quality * 45 + 52, 10)))

            # 6. Past Renewal Status: Successful renewal track record (%)
            renewal_attempts = max(0, int(years_experience / 3))
            if renewal_attempts == 0:
                past_renewal_raw = None  # New entrant
            else:
                success_ratio = min(1.0, max(0.0, latent_quality + self.rng.gauss(0, 0.1)))
                past_renewal_raw = round(success_ratio * 100.0, 1)

            # Feature dictionary with initial clean values
            features: dict[str, float | None] = {
                "audit_timeliness": round(timeliness_raw, 1),
                "audit_efficiency": round(efficiency_raw, 1),
                "error_rate": round(error_rate_raw, 1),
                "agency_scale": round(agency_scale_raw, 1),
                "compliance_adherence": round(compliance_adherence_raw, 1),
                "past_renewal_status": past_renewal_raw,
            }

            reporting_period = "2025-2026_ANNUAL"

            # Inject realistic irregularities
            if is_irregular:
                irregular_count += 1
                irr_choice = self.rng.choice([
                    "missing_past_renewal",
                    "missing_efficiency_unreported",
                    "missing_compliance_audit_pending",
                    "sparse_operating_history",
                    "outlying_extreme_errors",
                    "inconsistent_quarterly_period"
                ])
                irregularity_type = irr_choice

                if irr_choice == "missing_past_renewal":
                    features["past_renewal_status"] = None
                elif irr_choice == "missing_efficiency_unreported":
                    features["audit_efficiency"] = None
                elif irr_choice == "missing_compliance_audit_pending":
                    features["compliance_adherence"] = None
                elif irr_choice == "sparse_operating_history":
                    features["agency_scale"] = 4.5
                    features["past_renewal_status"] = None
                    years_experience = 1
                    certified_auditors = 2
                elif irr_choice == "outlying_extreme_errors":
                    features["error_rate"] = 68.5
                    features["audit_timeliness"] = 22.0
                elif irr_choice == "inconsistent_quarterly_period":
                    reporting_period = "2026_Q2_INTERIM_ONLY"

            # Derive Ground Truth Label
            # Renewal decision rule based on realistic regulatory criteria:
            # Latent weighted performance
            eff_term = features["audit_efficiency"] if features["audit_efficiency"] is not None else 60.0
            time_term = features["audit_timeliness"] if features["audit_timeliness"] is not None else 65.0
            err_term = features["error_rate"] if features["error_rate"] is not None else 15.0
            scale_term = features["agency_scale"] if features["agency_scale"] is not None else 40.0
            comp_term = features["compliance_adherence"] if features["compliance_adherence"] is not None else 70.0
            renew_term = features["past_renewal_status"] if features["past_renewal_status"] is not None else 75.0

            composite_score = (
                0.20 * time_term
                + 0.15 * eff_term
                + 0.20 * (100.0 - err_term)
                + 0.10 * scale_term
                + 0.20 * comp_term
                + 0.15 * renew_term
            )

            # Critical disqualification checks
            fatal_flaw = (
                (features["compliance_adherence"] is not None and features["compliance_adherence"] < 40.0)
                or (features["error_rate"] is not None and features["error_rate"] > 40.0)
                or composite_score < 50.0
            )

            if fatal_flaw:
                label = "do_not_renew"
            elif composite_score >= 68.0:
                label = "renew"
            else:
                label = "review"

            organisations.append({
                "organisation_id": org_id,
                "organisation_name": org_name,
                "reporting_period": reporting_period,
                "is_irregular": is_irregular,
                "irregularity_type": irregularity_type,
                "raw_metrics": {
                    "certified_auditors": certified_auditors,
                    "years_experience": years_experience,
                    "avg_duration_days": round(avg_duration_days, 1),
                },
                "features": features,
                "renewal_outcome": label,
            })

        # Calculate class distribution
        dist: dict[str, int] = {}
        for org in organisations:
            l = org["renewal_outcome"]
            dist[l] = dist.get(l, 0) + 1

        payload = {
            "dataset_version": "1.0.0",
            "format": "JSON",
            "seed": self.seed,
            "sample_count": n_samples,
            "irregular_sample_count": irregular_count,
            "irregularity_percentage": round((irregular_count / n_samples) * 100, 2),
            "class_distribution": dist,
            "organisations": organisations,
        }

        if output_path:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic auditing agency performance data.")
    parser.add_argument("--samples", type=int, default=500, help="Number of organisations to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--irregularity-rate", type=float, default=0.15, help="Proportion of irregular records")
    parser.add_argument("--output", type=str, default="data/synthetic_auditing_agencies.json", help="Output JSON path")
    args = parser.parse_args()

    generator = AgencyDataGenerator(seed=args.seed)
    result = generator.generate(
        n_samples=args.samples,
        irregularity_rate=args.irregularity_rate,
        output_path=args.output,
    )
    print(f"Generated {result['sample_count']} organisations ({result['irregular_sample_count']} irregular).")
    print(f"Distribution: {result['class_distribution']}")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
