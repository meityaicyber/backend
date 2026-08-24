import argparse
import os
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler, StandardScaler, MinMaxScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.neural_network import MLPClassifier
from sklearn.dummy import DummyClassifier
import numpy as np

from src.utils.json_utils import load_json, save_json
from src.experiments import extract_features_and_labels

def get_scaler(name):
    if name == "robust_scaler": return RobustScaler()
    if name == "standard_scaler": return StandardScaler()
    return MinMaxScaler()

def get_imputer(name):
    if name == "mean_imputation": return SimpleImputer(strategy="mean")
    if name == "constant_imputation": return SimpleImputer(strategy="constant", fill_value=-1)
    return SimpleImputer(strategy="median")

def train_models(dataset_path, prep_config_path, model_config_path, output_dir):
    dataset = load_json(dataset_path)
    prep_config = load_json(prep_config_path)
    model_config = load_json(model_config_path)
    
    X, y = extract_features_and_labels(dataset)
    
    test_size = prep_config["preprocessing"]["train_test_split"]["test_size"]
    random_state = prep_config["preprocessing"]["train_test_split"]["random_state"]
    folds = prep_config["preprocessing"]["cross_validation"]["folds"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    os.makedirs(output_dir, exist_ok=True)
    
    imputer = get_imputer(prep_config["preprocessing"]["missing_data_strategy"])
    scaler = get_scaler(prep_config["preprocessing"]["scaling_method"])
    
    models_to_train = {
        "baseline": DummyClassifier(strategy=model_config["models"]["baseline"]["strategy"]),
        "gradient_boosting": GradientBoostingClassifier(random_state=model_config["models"]["gradient_boosting"]["random_state"]),
        "svm": CalibratedClassifierCV(SVC(random_state=model_config["models"]["svm"]["random_state"])),
        "neural_network": MLPClassifier(random_state=model_config["models"]["neural_network"]["random_state"], max_iter=model_config["models"]["neural_network"]["max_iter"])
    }
    
    trained_metadata = {}
    
    for name, model in models_to_train.items():
        pipe = Pipeline([
            ("imputer", imputer),
            ("scaler", scaler),
            ("model", model)
        ])
        
        param_grid = {}
        if name in model_config["models"] and "search_space" in model_config["models"][name]:
            space = model_config["models"][name]["search_space"]
            for k, v in space.items():
                if name == "svm":
                    param_grid[f"model__estimator__{k}"] = v
                else:
                    param_grid[f"model__{k}"] = v
        
        if param_grid:
            search = GridSearchCV(pipe, param_grid, cv=folds, n_jobs=-1, scoring="f1_macro")
            search.fit(X_train, y_train)
            best_pipe = search.best_estimator_
            best_params = search.best_params_
        else:
            best_pipe = pipe.fit(X_train, y_train)
            best_params = {}
            
        model_filename = os.path.join(output_dir, f"{name}.joblib")
        joblib.dump(best_pipe, model_filename)
        
        trained_metadata[name] = {
            "version": "1.0.0",
            "hyperparameters": best_params,
            "artifact_path": model_filename
        }
        
    save_json(trained_metadata, os.path.join(output_dir, "models_metadata.json"))
    print("Training complete.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-prep", default="config/preprocessing_config.json")
    parser.add_argument("--config-model", default="config/model_config.json")
    parser.add_argument("--dataset", default="data/sample_dataset.json")
    parser.add_argument("--output", default="output/models")
    args = parser.parse_args()
    
    train_models(args.dataset, args.config_prep, args.config_model, args.output)

if __name__ == "__main__":
    main()
