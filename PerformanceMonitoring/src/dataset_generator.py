import argparse
import random
import uuid
import hashlib
from src.utils.json_utils import load_json, save_json

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

def generate_dataset(generator_config, feature_schema, label_rule, seed, count):
    random.seed(seed)
    
    population = []
    
    settings = generator_config["generator_settings"]
    f_settings = settings["features"]
    rates = settings["irregularity_rates"]
    
    class_counts = {0: 0, 1: 0}
    irregularity_counts = {"missing_feature": 0, "sparse_history": 0, "outliers": 0}
    
    for i in range(count):
        org_id = f"ORG_{i:05d}"
        
        # Generate base features
        timeliness = clamp(random.gauss(f_settings["audit_timeliness"]["mean"], f_settings["audit_timeliness"]["std"]), 0, 100)
        efficiency = clamp(random.gauss(f_settings["audit_efficiency"]["mean"], f_settings["audit_efficiency"]["std"]), 1, 365)
        error_rate = clamp(random.gauss(f_settings["error_rate"]["mean"], f_settings["error_rate"]["std"]), 0, 50)
        
        team_size = int(clamp(random.gauss(f_settings["agency_scale"]["team_size"]["mean"], f_settings["agency_scale"]["team_size"]["std"]), 1, 1000))
        years_exp = clamp(random.gauss(f_settings["agency_scale"]["years_experience"]["mean"], f_settings["agency_scale"]["years_experience"]["std"]), 0, 50)
        
        compliance = clamp(random.gauss(f_settings["compliance_adherence"]["mean"], f_settings["compliance_adherence"]["std"]), 0, 100)
        renewal_hist = clamp(random.gauss(f_settings["past_renewal_status"]["mean"], f_settings["past_renewal_status"]["std"]), 0, 1)
        
        features = {
            "audit_timeliness": round(timeliness, 2),
            "audit_efficiency": round(efficiency, 2),
            "error_rate": round(error_rate, 2),
            "agency_scale": {
                "team_size": team_size,
                "years_experience": round(years_exp, 1)
            },
            "compliance_adherence": round(compliance, 2),
            "past_renewal_status": round(renewal_hist, 2)
        }
        
        # Apply label rule (before irregularity to have the true latent label)
        lw = label_rule["synthetic_label_generation"]["latent_formula_weights"]
        latent_score = (
            lw["audit_timeliness"] * (features["audit_timeliness"] / 100.0) +
            lw["audit_efficiency"] * (max(0, 365 - features["audit_efficiency"]) / 365.0) +
            lw["error_rate"] * (max(0, 50 - features["error_rate"]) / 50.0) +
            lw["agency_scale"] * (0.5 * min(team_size/100, 1.0) + 0.5 * min(years_exp/20, 1.0)) +
            lw["compliance_adherence"] * (features["compliance_adherence"] / 100.0) +
            lw["past_renewal_status"] * features["past_renewal_status"]
        )
        
        threshold = label_rule["synthetic_label_generation"]["latent_score_threshold"]
        outcome = 1 if latent_score >= threshold else 0
        
        # Noise
        if random.random() < label_rule["synthetic_label_generation"]["noise_injection"]["probability"]:
            outcome = 1 - outcome
            
        class_counts[outcome] += 1
        
        # Inject irregularities
        if random.random() < rates["missing_feature"]:
            missing_k = random.choice(["audit_timeliness", "audit_efficiency", "error_rate", "compliance_adherence", "past_renewal_status"])
            features[missing_k] = None
            irregularity_counts["missing_feature"] += 1
            
        if random.random() < rates["sparse_history"]:
            # Set to a value that triggers the sparse history rule, or simulate it. We'll simulate by making it None as per the schema missing rule
            features["past_renewal_status"] = None
            irregularity_counts["sparse_history"] += 1
            
        if random.random() < rates["outliers"]:
            outlier_k = random.choice(["audit_efficiency", "error_rate", "audit_timeliness"])
            if outlier_k == "audit_efficiency":
                features[outlier_k] = 1000.0
            elif outlier_k == "error_rate":
                features[outlier_k] = 200.0
            elif outlier_k == "audit_timeliness":
                features[outlier_k] = -10.0
            irregularity_counts["outliers"] += 1
            
        org = {
            "organisation_id": org_id,
            "features": features,
            "renewal_outcome": outcome
        }
        population.append(org)
        
    metadata = {
        "seed": seed,
        "requested_count": count,
        "generated_count": len(population),
        "generator_config_version": generator_config["version"],
        "feature_schema_version": feature_schema["version"],
        "label_rule_version": label_rule["version"],
        "class_counts": class_counts,
        "irregularity_counts": irregularity_counts
    }
    
    return {"metadata": metadata, "data": population}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/generator_config.json")
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", "--count", type=int)
    parser.add_argument("--output", default="data/sample_dataset.json")
    args = parser.parse_args()
    
    generator_config = load_json(args.config)
    feature_schema = load_json("config/feature_schema.json")
    label_rule = load_json("config/label_rule.json")
    
    seed = args.seed if args.seed is not None else generator_config["generator_settings"]["default_seed"]
    count = args.count if args.count is not None else generator_config["generator_settings"]["population_size"]
    
    dataset = generate_dataset(generator_config, feature_schema, label_rule, seed, count)
    save_json(dataset, args.output)
    print(f"Dataset generated with {count} records at {args.output}")

if __name__ == "__main__":
    main()
