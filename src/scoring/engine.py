"""Continuous Performance Scoring and Boundary Evaluation Engine.

Computes multi-criteria performance scores strictly from versioned configuration files,
handles missing or irregular features with transparent non-assessable logging,
and flags decision boundary edge cases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ScoringEngine:
    """Configuration-driven scoring engine implementing weighted linear combination and boundary tracking."""

    def __init__(self, scoring_config: dict[str, Any] | str | Path = "config/scoring_config.json") -> None:
        if isinstance(scoring_config, (str, Path)):
            self.config = json.loads(Path(scoring_config).read_text(encoding="utf-8"))
        else:
            self.config = scoring_config

        self.version = self.config.get("version", "1.0.0")
        self.weights = self.config.get("weights", {})
        self.thresholds = self.config.get("thresholds", {"renew": 70.0, "review": 50.0})
        self.boundary_tolerance = float(self.config.get("boundary_tolerance", 3.0))
        self.missing_policy = self.config.get("missing_data_policy", "exclude_and_renormalise")
        self.error_rate_inversion = self.config.get("error_rate_inversion", {"enabled": True, "formula": "100.0 - error_rate"})

    def evaluate_decision_and_boundary(self, score: float) -> dict[str, Any]:
        """Classify score into decision tier and detect boundary proximity."""
        renew_th = self.thresholds["renew"]
        review_th = self.thresholds["review"]

        if score >= renew_th:
            decision = "renew"
        elif score >= review_th:
            decision = "review"
        else:
            decision = "do_not_renew"

        dist_renew = abs(score - renew_th)
        dist_review = abs(score - review_th)
        nearest_threshold_name = "renew" if dist_renew <= dist_review else "review"
        min_distance = min(dist_renew, dist_review)

        is_boundary = min_distance <= self.boundary_tolerance
        boundary_info: dict[str, Any] = {
            "decision": decision,
            "boundary_status": "boundary_case" if is_boundary else "clear",
            "distance_to_nearest_boundary": round(min_distance, 2),
            "nearest_boundary_threshold": nearest_threshold_name,
        }

        if is_boundary:
            boundary_info["boundary_annotation"] = (
                f"Score {score:.2f} is within +/-{self.boundary_tolerance:.1f} of '{nearest_threshold_name}' threshold "
                f"({self.thresholds[nearest_threshold_name]:.1f}). Subject to supervisory secondary review."
            )

        return boundary_info

    def score_organisation(self, features: dict[str, float | None]) -> dict[str, Any]:
        """Compute objective continuous performance score from raw feature dict."""
        assessable_features: dict[str, float] = {}
        non_assessable_features: list[dict[str, str]] = []
        feature_contributions: dict[str, float] = {}

        for feat_id, raw_val in features.items():
            if feat_id not in self.weights:
                continue

            if raw_val is None:
                non_assessable_features.append({
                    "feature_id": feat_id,
                    "reason": "Missing or non-assessable feature value",
                })
                continue

            # Directional inversion for error rate
            val = float(raw_val)
            if feat_id == "error_rate" and self.error_rate_inversion.get("enabled", True):
                eff_val = max(0.0, 100.0 - val)
            else:
                eff_val = val

            assessable_features[feat_id] = eff_val

        if not assessable_features:
            return {
                "score": None,
                "status": "not_assessable",
                "reason": "Zero assessable features available for scoring.",
                "assessable_features": [],
                "non_assessable_features": non_assessable_features,
                "decision": "undetermined",
                "boundary_status": "not_applicable",
            }

        # Weighted combination with renormalisation
        active_weight_sum = sum(self.weights[k] for k in assessable_features)
        if active_weight_sum <= 0:
            return {
                "score": None,
                "status": "not_assessable",
                "reason": "Total active weight is zero.",
                "assessable_features": list(assessable_features.keys()),
                "non_assessable_features": non_assessable_features,
            }

        weighted_sum = sum(assessable_features[k] * self.weights[k] for k in assessable_features)
        final_score = round(weighted_sum / active_weight_sum, 2)

        for k in assessable_features:
            contrib = (assessable_features[k] * self.weights[k]) / active_weight_sum
            feature_contributions[k] = round(contrib, 2)

        decision_data = self.evaluate_decision_and_boundary(final_score)

        return {
            "score": final_score,
            "status": "assessable",
            "active_weight_percentage": round((active_weight_sum / sum(self.weights.values())) * 100, 1),
            "feature_contributions": feature_contributions,
            "assessable_features": list(assessable_features.keys()),
            "non_assessable_features": non_assessable_features,
            **decision_data,
        }


def calculate_organisation_score(
    features: dict[str, float | None],
    config_path: str | Path = "config/scoring_config.json",
) -> dict[str, Any]:
    """Helper functional API to compute organisation score."""
    engine = ScoringEngine(config_path)
    return engine.score_organisation(features)
