import argparse
import os
import uuid
import joblib
import numpy as np

from src.utils.json_utils import load_json, save_json

def extract_single_row_features(f):
    timeliness = f["audit_timeliness"]
    efficiency = f["audit_efficiency"]
    error = f["error_rate"]
    team_size = f["agency_scale"]["team_size"] if f["agency_scale"] is not None else None
    years = f["agency_scale"]["years_experience"] if f["agency_scale"] is not None else None
    comp = f["compliance_adherence"]
    ren = f["past_renewal_status"]
    
    return [
        timeliness if timeliness is not None else np.nan,
        efficiency if efficiency is not None else np.nan,
        error if error is not None else np.nan,
        team_size if team_size is not None else np.nan,
        years if years is not None else np.nan,
        comp if comp is not None else np.nan,
        ren if ren is not None else np.nan
    ]

def evaluate_performance(dataset_path, scoring_config_path, model_metadata_path, schema_path, output_dir):
    dataset = load_json(dataset_path)
    scoring_config = load_json(scoring_config_path)
    schema = load_json(schema_path)
    models_meta = load_json(model_metadata_path)
    
    # We use gradient_boosting for renewal prediction
    model_name = "gradient_boosting"
    pipe = joblib.load(models_meta[model_name]["artifact_path"])
    import hashlib
    run_hash = hashlib.sha256(f"{dataset_path}_{scoring_config['version']}_{schema['version']}".encode()).hexdigest()
    run_id = f"run_{run_hash[:8]}"
    
    weights = scoring_config["scoring_rule"]["weights"]
    norms = scoring_config["scoring_rule"]["feature_normalisation"]
    missing_policy = scoring_config["scoring_rule"]["missing_feature_policy"]
    boundary_settings = scoring_config["classification_boundary"]
    
    results = []
    
    for row in dataset["data"]:
        org_id = row["organisation_id"]
        f = row["features"]
        
        # 1. Scoring
        missing_count = 0
        missing_keys = []
        valid_weights = {}
        norm_vals = {}
        
        # Calculate normalized values
        if f["audit_timeliness"] is not None:
            norm_vals["audit_timeliness"] = f["audit_timeliness"]
        else:
            missing_count += 1
            missing_keys.append("audit_timeliness")
            
        if f["audit_efficiency"] is not None:
            norm_vals["audit_efficiency"] = max(0, (365 - f["audit_efficiency"]) / 365.0 * 100)
        else:
            missing_count += 1
            missing_keys.append("audit_efficiency")
            
        if f["error_rate"] is not None:
            norm_vals["error_rate"] = max(0, 100 - (f["error_rate"] / 50.0 * 100))
        else:
            missing_count += 1
            missing_keys.append("error_rate")
            
        if f["agency_scale"] is not None:
            norm_vals["agency_scale"] = 0.5 * min(f["agency_scale"]["team_size"]/100*100, 100) + 0.5 * min(f["agency_scale"]["years_experience"]/20*100, 100)
        else:
            missing_count += 1
            missing_keys.append("agency_scale")
            
        if f["compliance_adherence"] is not None:
            norm_vals["compliance_adherence"] = f["compliance_adherence"]
        else:
            missing_count += 1
            missing_keys.append("compliance_adherence")
            
        if f["past_renewal_status"] is not None:
            norm_vals["past_renewal_status"] = f["past_renewal_status"] * 100
        else:
            missing_count += 1
            missing_keys.append("past_renewal_status")
            
        assessment_status = "assessable"
        score = None
        
        if missing_count > missing_policy["max_missing_allowed"]:
            assessment_status = missing_policy["fallback"]
            score = 0.0 # Will be sorted at bottom, but noted as unassessable
        else:
            # Renormalize weights
            total_valid_weight = sum([weights[k] for k in norm_vals.keys()])
            score = 0.0
            for k, val in norm_vals.items():
                w = weights[k] / total_valid_weight
                score += val * w
                
        # 2. Prediction
        X_row = np.array([extract_single_row_features(f)])
        prob = pipe.predict_proba(X_row)[0][1]
        
        predicted_class = "renewed" if prob >= boundary_settings["decision_threshold"] else "not_renewed"
        b_status = boundary_settings["boundary_status_labels"]["normal"]
        if abs(prob - boundary_settings["decision_threshold"]) <= boundary_settings["epsilon"]:
            b_status = boundary_settings["boundary_status_labels"]["close_to_boundary"]
            
        out_row = {
            "organisation_id": org_id,
            "performance_score": round(score, 2) if score is not None else None,
            "assessment_status": assessment_status,
            "missing_features": missing_keys,
            "renewal_prediction": {
                "class": predicted_class,
                "probability": round(float(prob), 4),
                "boundary_status": b_status
            },
            "raw_features": f, # for tie breaking
            "provenance": {
                "feature_schema_version": schema["version"],
                "scoring_config_version": scoring_config["version"],
                "model_version": f"{model_name}_{models_meta[model_name]['version']}",
                "run_id": run_id
            }
        }
        results.append(out_row)
        
    # 3. Ranking
    # Sort by score DESC, then compliance DESC, then timeliness DESC, then org_id ASC (for determinism)
    def sort_key(x):
        s = x["performance_score"] if x["performance_score"] is not None else -1.0
        c = x["raw_features"]["compliance_adherence"] if x["raw_features"]["compliance_adherence"] is not None else -1.0
        t = x["raw_features"]["audit_timeliness"] if x["raw_features"]["audit_timeliness"] is not None else -1.0
        return (-s, -c, -t, x["organisation_id"])
        
    results.sort(key=sort_key)
    
    # Assign ranks
    current_rank = 1
    for i, r in enumerate(results):
        if i > 0:
            prev = results[i-1]
            if sort_key(r)[:-1] != sort_key(prev)[:-1]:
                current_rank = i + 1
        r["rank"] = current_rank if r["assessment_status"] == "assessable" else None
        
    # Clean up raw_features from final output
    for r in results:
        del r["raw_features"]
        
    os.makedirs(output_dir, exist_ok=True)
    save_json(results, os.path.join(output_dir, "organisation_scores.json"))
    
    ranking_summary = {
        "metadata": {
            "total_organisations": len(results),
            "assessable_organisations": sum(1 for r in results if r["assessment_status"] == "assessable"),
            "provenance": results[0]["provenance"] if len(results) > 0 else {}
        },
        "top_10": results[:10],
        "bottom_10": results[-10:]
    }
    save_json(ranking_summary, os.path.join(output_dir, "ranking_summary.json"))
    print(f"Scored {len(results)} organisations.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-scoring", default="config/scoring_config.json")
    parser.add_argument("--config-schema", default="config/feature_schema.json")
    parser.add_argument("--models-meta", default="output/models/models_metadata.json")
    parser.add_argument("--dataset", default="data/sample_dataset.json")
    parser.add_argument("--output", default="output/scoring")
    args = parser.parse_args()
    
    evaluate_performance(args.dataset, args.config_scoring, args.models_meta, args.config_schema, args.output)

if __name__ == "__main__":
    main()
