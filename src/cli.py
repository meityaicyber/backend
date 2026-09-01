"""Master CLI Orchestrator for Auditing Agency Performance Monitoring.

Provides single-command execution for data generation, model evaluation, scoring,
ranking, provenance tracing, and offline verification.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from data.generator import AgencyDataGenerator
from src.models.pipeline import ModelPipeline
from src.scoring.ranking import RankingEngine, compute_config_hash
from src.versioning.registry import VersionRegistry


def run_all(seed: int = 42, samples: int = 500) -> None:
    """Execute complete end-to-end performance monitoring pipeline."""
    print("=" * 70)
    print("FIELDLINE AUDITING AGENCY PERFORMANCE MONITORING & RANKING MODULE")
    print("Clean-Room Build - Execution Pipeline")
    print("=" * 70)

    # 1. Generate Synthetic Population
    print(f"\n[1/4] Generating synthetic population ({samples} organisations, seed={seed})...")
    generator = AgencyDataGenerator(seed=seed)
    gen_result = generator.generate(
        n_samples=samples,
        irregularity_rate=0.15,
        output_path="data/synthetic_auditing_agencies.json",
    )
    print(f"  -> Generated {gen_result['sample_count']} organisations.")
    print(f"  -> Irregular records injected: {gen_result['irregular_sample_count']}")
    print(f"  -> Class Distribution: {gen_result['class_distribution']}")

    # 2. Train and Evaluate Models
    print("\n[2/4] Executing classification pipeline (Baseline, GBDT, SVM, MLP)...")
    pipeline = ModelPipeline()
    eval_results = pipeline.run_pipeline(
        dataset_path="data/synthetic_auditing_agencies.json",
        output_dir="output",
    )
    print(f"  -> Evaluated on {eval_results['sample_counts']['test']} holdout test samples.")
    for m_id, m_data in eval_results["models"].items():
        met = m_data["metrics"]
        cv = m_data.get("cross_validation", {})
        print(f"     * {m_id:<18} | Test Acc: {met['accuracy']:.4f} | Macro-F1: {met['macro_f1']:.4f} | CV F1: {cv.get('mean_f1_macro', 0.0):.4f}")

    # 3. Score and Rank Agencies
    print("\n[3/4] Running continuous scoring, boundary detection, and ranking...")
    dataset = json.loads(Path("data/synthetic_auditing_agencies.json").read_text(encoding="utf-8"))
    ranking_engine = RankingEngine()
    per_org_scores, ranking_output = ranking_engine.process_and_rank_dataset(dataset, output_dir="output")
    summary = ranking_output["summary"]
    print(f"  -> Total organisations ranked: {len(ranking_output['rankings'])}")
    print(f"  -> Average Score: {summary['average_score']}")
    print(f"  -> Decision Breakdown: Renew={summary['renew_count']}, Review={summary['review_count']}, Do Not Renew={summary['do_not_renew_count']}")
    print(f"  -> Boundary Cases Flagged: {summary['boundary_case_count']}")

    # 4. Top 5 Leaderboard Preview
    print("\n[4/4] Top 5 Ranked Auditing Organisations:")
    for item in ranking_output["rankings"][:5]:
        b_flag = f" [BOUNDARY: +/-{item['distance_to_nearest_boundary']}]" if item["boundary_status"] == "boundary_case" else ""
        print(f"  Rank #{item['rank']:<2} | {item['organisation_id']} | {item['organisation_name']:<35} | Score: {item['score']:>5.2f} | {item['decision'].upper()}{b_flag}")

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION COMPLETE - All outputs saved to /output/ and /data/")
    print("=" * 70)


def trace_organisation(org_id: str) -> None:
    """Trace complete provenance and feature values for an organisation."""
    scores_path = Path("output/sample_organisation_scores.json")
    if not scores_path.exists():
        print(f"Error: {scores_path} not found. Please run the pipeline first.")
        sys.exit(1)

    data = json.loads(scores_path.read_text(encoding="utf-8"))
    records = data.get("records", [])
    record = next((r for r in records if r["organisation_id"] == org_id), None)

    if not record:
        print(f"Organisation '{org_id}' not found in latest scoring run.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"PROVENANCE & FEATURE TRACE: {org_id}")
    print("=" * 60)
    print(f"Organisation Name : {record.get('organisation_name')}")
    print(f"Reporting Period  : {record.get('reporting_period')}")
    print(f"Computed Score    : {record['score_result'].get('score')}")
    print(f"Decision Status   : {record['score_result'].get('decision')}")
    print(f"Boundary Status   : {record['score_result'].get('boundary_status')}")
    print("\nRaw Feature Inputs:")
    for k, v in record.get("raw_features", {}).items():
        print(f"  - {k:<25}: {v}")

    print("\nFeature Contributions to Final Score:")
    for k, v in record["score_result"].get("feature_contributions", {}).items():
        print(f"  - {k:<25}: {v:>5.2f} points")

    print("\nAudit Provenance Lineage:")
    for k, v in record.get("provenance", {}).items():
        print(f"  - {k:<25}: {v}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditing Agency Performance Monitoring Module Master CLI")
    parser.add_argument("--all", action="store_true", help="Run full pipeline end-to-end")
    parser.add_argument("--generate-data", action="store_true", help="Generate synthetic dataset only")
    parser.add_argument("--train-eval", action="store_true", help="Train and evaluate all models")
    parser.add_argument("--score-rank", action="store_true", help="Score and rank organisations")
    parser.add_argument("--trace-org", type=str, help="Trace score lineage and provenance for organisation ID")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--samples", type=int, default=500, help="Number of organisations to generate")
    args = parser.parse_args()

    if args.trace_org:
        trace_organisation(args.trace_org)
    elif args.generate_data:
        generator = AgencyDataGenerator(seed=args.seed)
        generator.generate(n_samples=args.samples, output_path="data/synthetic_auditing_agencies.json")
    elif args.train_eval:
        pipeline = ModelPipeline()
        pipeline.run_pipeline()
    elif args.score_rank:
        dataset = json.loads(Path("data/synthetic_auditing_agencies.json").read_text(encoding="utf-8"))
        ranking_engine = RankingEngine()
        ranking_engine.process_and_rank_dataset(dataset)
    else:
        # Default behavior: run all
        run_all(seed=args.seed, samples=args.samples)


if __name__ == "__main__":
    main()
