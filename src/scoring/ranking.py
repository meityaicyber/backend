"""Ranking and Provenance Engine for Empanelled Auditing Organisations.

Computes deterministic ordered rankings across organisations based on continuous performance scores,
implements configurable tie-breaking policies, and attaches complete provenance metadata.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.scoring.engine import ScoringEngine


def compute_config_hash(config_dir: str | Path = "config") -> str:
    """Compute SHA-256 hash over all configuration files."""
    c_dir = Path(config_dir)
    json_files = sorted(c_dir.glob("*.json"))
    hasher = hashlib.sha256()
    for jf in json_files:
        hasher.update(jf.read_bytes())
    return hasher.hexdigest()[:16]


class RankingEngine:
    """Configuration-driven ranking and provenance module."""

    def __init__(
        self,
        scoring_config_path: str | Path = "config/scoring_config.json",
        model_config_path: str | Path = "config/model_config.json",
    ) -> None:
        self.scoring_config_path = Path(scoring_config_path)
        m_path = Path(model_config_path)
        if not m_path.exists() and Path("config.json").exists():
            m_path = Path("config.json")
        self.model_config_path = m_path
        self.scoring_config = json.loads(self.scoring_config_path.read_text(encoding="utf-8"))
        self.model_config = json.loads(self.model_config_path.read_text(encoding="utf-8"))
        self.scoring_engine = ScoringEngine(self.scoring_config)
        self.tie_policy = self.scoring_config.get("tie_policy", "standard_competition")

    def process_and_rank_dataset(
        self,
        dataset: dict[str, Any],
        output_dir: str | Path = "output",
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Score all organisations in dataset, assign ranks, and save JSON outputs."""
        config_hash = compute_config_hash(self.scoring_config_path.parent)
        scoring_version = self.scoring_config.get("version", "1.0.0")
        model_version = self.model_config.get("version", "1.0.0")
        selected_model = self.model_config.get("selected_model", "gradient_boosting")
        timestamp = datetime.now(timezone.utc).isoformat()

        scored_organisations: list[dict[str, Any]] = []

        for org in dataset.get("organisations", []):
            org_id = org["organisation_id"]
            org_name = org.get("organisation_name", org_id)
            raw_features = org.get("features", {})
            reporting_period = org.get("reporting_period", "2025-2026_ANNUAL")

            score_res = self.scoring_engine.score_organisation(raw_features)

            record = {
                "organisation_id": org_id,
                "organisation_name": org_name,
                "reporting_period": reporting_period,
                "score_result": score_res,
                "raw_features": raw_features,
                "provenance": {
                    "scoring_config_version": scoring_version,
                    "model_config_version": model_version,
                    "selected_model": selected_model,
                    "configuration_sha256": config_hash,
                    "computation_timestamp": timestamp,
                },
            }
            scored_organisations.append(record)

        # Separate assessable from non-assessable
        assessable_list = [
            item for item in scored_organisations
            if item["score_result"]["status"] == "assessable" and item["score_result"]["score"] is not None
        ]
        non_assessable_list = [
            item for item in scored_organisations
            if item["score_result"]["status"] != "assessable" or item["score_result"]["score"] is None
        ]

        # Sort assessable by score descending, then organisation_id ascending
        assessable_list.sort(
            key=lambda x: (-x["score_result"]["score"], x["organisation_id"])
        )

        # Apply tie policy
        ranked_items: list[dict[str, Any]] = []
        if self.tie_policy == "standard_competition":
            # 1224 ranking
            current_rank = 1
            for idx, item in enumerate(assessable_list):
                if idx > 0 and item["score_result"]["score"] < assessable_list[idx - 1]["score_result"]["score"]:
                    current_rank = idx + 1
                ranked_items.append({
                    "rank": current_rank,
                    **item,
                })
        elif self.tie_policy == "dense":
            # 1223 ranking
            current_rank = 1
            for idx, item in enumerate(assessable_list):
                if idx > 0 and item["score_result"]["score"] < assessable_list[idx - 1]["score_result"]["score"]:
                    current_rank += 1
                ranked_items.append({
                    "rank": current_rank,
                    **item,
                })
        else:
            # Ordinal (1234)
            for idx, item in enumerate(assessable_list):
                ranked_items.append({
                    "rank": idx + 1,
                    **item,
                })

        # Non-assessable items get rank None
        for item in non_assessable_list:
            ranked_items.append({
                "rank": None,
                **item,
            })

        # Build Per-Organisation Scores Payload (D9)
        per_org_payload = {
            "version": scoring_version,
            "generated_at": timestamp,
            "config_hash": config_hash,
            "total_organisations": len(scored_organisations),
            "assessable_count": len(assessable_list),
            "non_assessable_count": len(non_assessable_list),
            "records": scored_organisations,
        }

        # Build Aggregate Ranking Payload (D9)
        ranking_summary = {
            "renew_count": sum(1 for x in assessable_list if x["score_result"]["decision"] == "renew"),
            "review_count": sum(1 for x in assessable_list if x["score_result"]["decision"] == "review"),
            "do_not_renew_count": sum(1 for x in assessable_list if x["score_result"]["decision"] == "do_not_renew"),
            "boundary_case_count": sum(1 for x in assessable_list if x["score_result"]["boundary_status"] == "boundary_case"),
            "average_score": round(sum(x["score_result"]["score"] for x in assessable_list) / len(assessable_list), 2) if assessable_list else None,
        }

        aggregate_ranking_payload = {
            "ranking_version": scoring_version,
            "generated_at": timestamp,
            "config_hash": config_hash,
            "tie_policy": self.tie_policy,
            "summary": ranking_summary,
            "rankings": [
                {
                    "rank": item["rank"],
                    "organisation_id": item["organisation_id"],
                    "organisation_name": item["organisation_name"],
                    "score": item["score_result"]["score"],
                    "decision": item["score_result"]["decision"],
                    "boundary_status": item["score_result"]["boundary_status"],
                    "distance_to_nearest_boundary": item["score_result"].get("distance_to_nearest_boundary"),
                    "nearest_boundary_threshold": item["score_result"].get("nearest_boundary_threshold"),
                    "boundary_annotation": item["score_result"].get("boundary_annotation"),
                    "non_assessable_features": item["score_result"].get("non_assessable_features", []),
                    "provenance": item["provenance"],
                }
                for item in ranked_items
            ],
        }

        if output_dir is not None:
            out_d = Path(output_dir)
            out_d.mkdir(parents=True, exist_ok=True)
            (out_d / "sample_organisation_scores.json").write_text(
                json.dumps(per_org_payload, indent=2), encoding="utf-8"
            )
            (out_d / "sample_rankings.json").write_text(
                json.dumps(aggregate_ranking_payload, indent=2), encoding="utf-8"
            )

        return per_org_payload, aggregate_ranking_payload


def rank_organisation_scores(
    dataset_path: str | Path = "data/synthetic_auditing_agencies.json",
    output_dir: str | Path = "output",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Functional API to rank organisations from dataset file."""
    dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    engine = RankingEngine()
    return engine.process_and_rank_dataset(dataset, output_dir=output_dir)


def main() -> None:
    _, ranking_payload = rank_organisation_scores()
    print("Scoring and Ranking Output Generated:")
    print(f" - Total Ranked: {len(ranking_payload['rankings'])}")
    print(f" - Summary: {ranking_payload['summary']}")
    print(f" - Top 3:")
    for r in ranking_payload["rankings"][:3]:
        print(f"   Rank #{r['rank']}: {r['organisation_name']} - Score: {r['score']} [{r['decision']}]")


if __name__ == "__main__":
    main()
