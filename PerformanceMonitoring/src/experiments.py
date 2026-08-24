import argparse
from src.utils.json_utils import load_json, save_json
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import f1_score
import numpy as np

def extract_features_and_labels(dataset):
    X = []
    y = []
    for row in dataset["data"]:
        f = row["features"]
        # Extract features, None becomes np.nan
        timeliness = f["audit_timeliness"] if f["audit_timeliness"] is not None else np.nan
        efficiency = f["audit_efficiency"] if f["audit_efficiency"] is not None else np.nan
        error = f["error_rate"] if f["error_rate"] is not None else np.nan
        team_size = f["agency_scale"]["team_size"] if f["agency_scale"] is not None else np.nan
        years = f["agency_scale"]["years_experience"] if f["agency_scale"] is not None else np.nan
        comp = f["compliance_adherence"] if f["compliance_adherence"] is not None else np.nan
        ren = f["past_renewal_status"] if f["past_renewal_status"] is not None else np.nan
        
        X.append([timeliness, efficiency, error, team_size, years, comp, ren])
        y.append(row["renewal_outcome"])
        
    return np.array(X), np.array(y)

def run_experiments():
    dataset = load_json("data/sample_dataset.json")
    X, y = extract_features_and_labels(dataset)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    results = {}
    
    # 1. Missing Data Strategies (with a simple Logistic Regression or similar, we'll use GB)
    imputers = {
        "mean_imputation": SimpleImputer(strategy="mean"),
        "median_imputation": SimpleImputer(strategy="median"),
        "constant_imputation": SimpleImputer(strategy="constant", fill_value=-1)
    }
    
    results["missing_data_strategies"] = {}
    for name, imp in imputers.items():
        pipe = Pipeline([("imputer", imp), ("model", GradientBoostingClassifier(random_state=42))])
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        results["missing_data_strategies"][name] = {"macro_f1": round(f1_score(y_test, preds, average="macro"), 4)}
        
    # 2. Scaling Strategies (using SVM which is sensitive to scaling)
    scalers = {
        "minmax_scaler": MinMaxScaler(),
        "standard_scaler": StandardScaler(),
        "robust_scaler": RobustScaler()
    }
    results["scaling_strategies"] = {}
    for name, sc in scalers.items():
        pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", sc), ("model", SVC(random_state=42))])
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        results["scaling_strategies"][name] = {"macro_f1": round(f1_score(y_test, preds, average="macro"), 4)}
        
    # 3. Classification Models
    models = {
        "baseline": DummyClassifier(strategy="most_frequent"),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
        "svm": SVC(probability=True, random_state=42),
        "neural_network": MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500, random_state=42)
    }
    results["classification_models"] = {}
    for name, mod in models.items():
        pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", mod)])
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        results["classification_models"][name] = {"macro_f1": round(f1_score(y_test, preds, average="macro"), 4)}
        
    save_json(results, "output/experiment_results.json")
    print("Experiments completed. Results saved to output/experiment_results.json")

if __name__ == "__main__":
    run_experiments()
