import argparse
import os
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from src.utils.json_utils import load_json, save_json
from src.experiments import extract_features_and_labels
from sklearn.model_selection import train_test_split

def evaluate_models(dataset_path, prep_config_path, models_dir, output_dir):
    dataset = load_json(dataset_path)
    prep_config = load_json(prep_config_path)
    models_metadata = load_json(os.path.join(models_dir, "models_metadata.json"))
    
    X, y = extract_features_and_labels(dataset)
    test_size = prep_config["preprocessing"]["train_test_split"]["test_size"]
    random_state = prep_config["preprocessing"]["train_test_split"]["random_state"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    os.makedirs(output_dir, exist_ok=True)
    
    summary = {}
    
    for name, meta in models_metadata.items():
        pipe = joblib.load(meta["artifact_path"])
        preds = pipe.predict(X_test)
        
        acc = accuracy_score(y_test, preds)
        macro_f1 = f1_score(y_test, preds, average="macro")
        
        # Per class metrics
        classes = [0, 1]
        cm = confusion_matrix(y_test, preds, labels=classes)
        per_class = {}
        for cls in classes:
            per_class[str(cls)] = {
                "precision": float(precision_score(y_test, preds, labels=[cls], average="macro", zero_division=0)),
                "recall": float(recall_score(y_test, preds, labels=[cls], average="macro", zero_division=0)),
                "f1": float(f1_score(y_test, preds, labels=[cls], average="macro", zero_division=0))
            }
            
        metrics = {
            "accuracy": float(acc),
            "macro_f1": float(macro_f1),
            "precision_macro": float(precision_score(y_test, preds, average="macro", zero_division=0)),
            "recall_macro": float(recall_score(y_test, preds, average="macro", zero_division=0)),
            "confusion_matrix": cm.tolist()
        }
        
        result = {
            "model": name,
            "metadata": {
                "dataset_size": len(y),
                "test_size": len(y_test),
                "split_random_state": random_state,
                "model_version": meta["version"]
            },
            "metrics": metrics,
            "per_class": per_class
        }
        
        save_json(result, os.path.join(output_dir, f"{name}_results.json"))
        summary[name] = {"macro_f1": float(macro_f1), "accuracy": float(acc)}
        
    save_json(summary, os.path.join(output_dir, "comparison_summary.json"))
    print("Evaluation complete.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-prep", default="config/preprocessing_config.json")
    parser.add_argument("--dataset", default="data/sample_dataset.json")
    parser.add_argument("--models", default="output/models")
    parser.add_argument("--output", default="output/evaluation")
    args = parser.parse_args()
    
    evaluate_models(args.dataset, args.config_prep, args.models, args.output)

if __name__ == "__main__":
    main()
