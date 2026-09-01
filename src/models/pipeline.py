"""Classification Pipeline for Auditing Agency Performance Renewal Decisions.

Implements end-to-end configuration-driven training, validation, cross-validation,
and evaluation across:
1. Rule-Based Threshold Baseline
2. Gradient Boosted Decision Trees
3. Support Vector Machine (RBF Kernel)
4. Multi-Layer Perceptron (Neural Network)

All model architectures and hyperparameters are loaded dynamically from config.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from src.models.baseline import RuleBaselineClassifier
from src.models.evaluate import ModelEvaluator


def resolve_model_config(config_path: str | Path | dict[str, Any] | None = None) -> tuple[dict[str, Any], Path | None]:
    """Resolve and load model configuration from path, dict, or standard fallback locations."""
    if isinstance(config_path, dict):
        return config_path, None

    candidate_paths: list[Path] = []
    if config_path is not None:
        candidate_paths.append(Path(config_path))
    else:
        candidate_paths.extend([
            Path("config.json"),
            Path("config/model_config.json"),
            Path("config/config.json"),
        ])

    for p in candidate_paths:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            # If unified config containing "model_config" or "models"
            if "model_config" in data and isinstance(data["model_config"], dict):
                return data["model_config"], p
            return data, p

    # Default fallback minimal configuration
    default_config: dict[str, Any] = {
        "version": "1.0.0",
        "selected_model": "gradient_boosting",
        "random_seed": 42,
        "train_test_split": {"test_size": 0.20, "stratify": True},
        "cross_validation": {"n_splits": 5, "shuffle": True, "scoring": "f1_macro"},
        "feature_order": [
            "audit_timeliness",
            "audit_efficiency",
            "error_rate",
            "agency_scale",
            "compliance_adherence",
            "past_renewal_status",
        ],
        "target_classes": ["renew", "review", "do_not_renew"],
        "preprocessing": {"imputer_strategy": "median", "scale_continuous": True},
        "models": [
            {
                "id": "baseline",
                "parameters": {"renew_cutoff": 70.0, "review_cutoff": 50.0},
            },
            {
                "id": "gradient_boosting",
                "parameters": {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 3, "subsample": 0.8, "random_state": 42},
            },
            {
                "id": "svm",
                "parameters": {"C": 1.0, "kernel": "rbf", "gamma": "scale", "probability": True, "random_state": 42},
            },
            {
                "id": "neural_network",
                "parameters": {"hidden_layer_sizes": [64, 32], "activation": "relu", "alpha": 0.001, "max_iter": 500, "early_stopping": True, "random_state": 42},
            },
        ],
    }
    return default_config, None


class ModelPipeline:
    """Orchestrates model construction, training, validation, and benchmarking dynamically from config.json."""

    FEATURE_ORDER = [
        "audit_timeliness",
        "audit_efficiency",
        "error_rate",
        "agency_scale",
        "compliance_adherence",
        "past_renewal_status",
    ]

    def __init__(self, config_path: str | Path | dict[str, Any] | None = None) -> None:
        self.config, self.config_path = resolve_model_config(config_path)
        self.seed = int(self.config.get("random_seed", 42))
        self.feature_order = self.config.get("feature_order", self.FEATURE_ORDER)
        self.target_classes = self.config.get("target_classes", ["renew", "review", "do_not_renew"])
        self.preprocessing = self.config.get("preprocessing", {})
        self.imputer_strategy = self.preprocessing.get("imputer_strategy", "median")
        self.models: dict[str, Any] = {}
        self._init_models()

    def _get_model_config_entry(self, model_id: str) -> dict[str, Any]:
        """Find model specification by id from the models list in configuration."""
        for m in self.config.get("models", []):
            if m.get("id") == model_id:
                return m
        return {}

    def _init_models(self) -> None:
        """Initialize all model architectures dynamically using parameters from config.json."""
        # 1. Baseline Heuristic
        baseline_cfg = self._get_model_config_entry("baseline")
        baseline_params = dict(baseline_cfg.get("parameters", {}))
        renew_cutoff = float(baseline_params.get("renew_cutoff", 70.0))
        review_cutoff = float(baseline_params.get("review_cutoff", 50.0))
        weights = baseline_params.get("weights", None)
        self.models["baseline"] = RuleBaselineClassifier(
            renew_cutoff=renew_cutoff,
            review_cutoff=review_cutoff,
            weights=weights,
        )

        # 2. Gradient Boosting
        gb_cfg = self._get_model_config_entry("gradient_boosting")
        gb_params = dict(gb_cfg.get("parameters", {}))
        if "random_state" not in gb_params:
            gb_params["random_state"] = self.seed
        gb_imputer_strategy = gb_params.pop("imputer_strategy", self.imputer_strategy)
        self.models["gradient_boosting"] = Pipeline([
            ("imputer", SimpleImputer(strategy=gb_imputer_strategy)),
            ("clf", GradientBoostingClassifier(**gb_params)),
        ])

        # 3. Support Vector Machine (RBF)
        svm_cfg = self._get_model_config_entry("svm")
        svm_params = dict(svm_cfg.get("parameters", {}))
        if "random_state" not in svm_params:
            svm_params["random_state"] = self.seed
        svm_imputer_strategy = svm_params.pop("imputer_strategy", self.imputer_strategy)
        self.models["svm"] = Pipeline([
            ("imputer", SimpleImputer(strategy=svm_imputer_strategy)),
            ("scaler", StandardScaler()),
            ("clf", SVC(**svm_params)),
        ])

        # 4. Neural Network (MLP)
        mlp_cfg = self._get_model_config_entry("neural_network")
        mlp_params = dict(mlp_cfg.get("parameters", {}))
        if "random_state" not in mlp_params:
            mlp_params["random_state"] = self.seed
        # Convert hidden_layer_sizes list to tuple if provided as list
        if "hidden_layer_sizes" in mlp_params and isinstance(mlp_params["hidden_layer_sizes"], list):
            mlp_params["hidden_layer_sizes"] = tuple(mlp_params["hidden_layer_sizes"])
        mlp_imputer_strategy = mlp_params.pop("imputer_strategy", self.imputer_strategy)
        self.models["neural_network"] = Pipeline([
            ("imputer", SimpleImputer(strategy=mlp_imputer_strategy)),
            ("scaler", StandardScaler()),
            ("clf", MLPClassifier(**mlp_params)),
        ])

    def extract_features_and_labels(
        self, dataset: dict[str, Any]
    ) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Extract feature matrix X and label vector y from dataset JSON."""
        organisations = dataset["organisations"]
        x_rows: list[list[float | None]] = []
        y_labels: list[str] = []
        org_ids: list[str] = []

        for org in organisations:
            features = org["features"]
            row = [features.get(f) for f in self.feature_order]
            # Replace None with np.nan for numerical pipelines
            row_float = [np.nan if v is None else float(v) for v in row]
            x_rows.append(row_float)
            y_labels.append(org["renewal_outcome"])
            org_ids.append(org["organisation_id"])

        return np.array(x_rows, dtype=float), np.array(y_labels), org_ids

    def run_pipeline(
        self,
        dataset_path: str | Path = "data/synthetic_auditing_agencies.json",
        output_dir: str | Path = "output",
    ) -> dict[str, Any]:
        """Execute full training, K-fold CV, test set evaluation, and output generation."""
        dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
        X, y, _ = self.extract_features_and_labels(dataset)

        train_test_cfg = self.config.get("train_test_split", {})
        test_size = float(train_test_cfg.get("test_size", 0.20))
        _, class_counts = np.unique(y, return_counts=True)
        should_stratify = train_test_cfg.get("stratify", True) and (np.min(class_counts) >= 2)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.seed, stratify=y if should_stratify else None
        )

        cv_cfg = self.config.get("cross_validation", {})
        desired_folds = int(cv_cfg.get("n_splits", 5))
        cv_scoring = cv_cfg.get("scoring", "f1_macro")
        cv_shuffle = cv_cfg.get("shuffle", True)

        _, train_class_counts = np.unique(y_train, return_counts=True)
        min_train_count = int(np.min(train_class_counts))
        actual_folds = max(2, min(desired_folds, min_train_count))
        skf = StratifiedKFold(n_splits=actual_folds, shuffle=cv_shuffle, random_state=self.seed)

        evaluation_results: dict[str, Any] = {
            "evaluation_version": self.config.get("version", "1.0.0"),
            "random_seed": self.seed,
            "sample_counts": {
                "total": len(y),
                "train": len(y_train),
                "test": len(y_test),
            },
            "selected_model": self.config.get("selected_model", "gradient_boosting"),
            "models": {},
        }

        for model_id, model in self.models.items():
            # Cross-validation on train split
            cv_scores = cross_val_score(model, X_train, y_train, cv=skf, scoring=cv_scoring)

            # Fit on full training split
            model.fit(X_train, y_train)

            # Predict on holdout test set
            y_pred = model.predict(X_test)

            eval_payload = ModelEvaluator.evaluate(
                y_true=y_test,
                y_pred=y_pred,
                model_name=model_id,
                cv_scores=cv_scores.tolist(),
                target_classes=self.target_classes,
            )
            evaluation_results["models"][model_id] = eval_payload

        out_path = Path(output_dir) / "evaluation_results.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(evaluation_results, indent=2), encoding="utf-8")

        return evaluation_results


def main() -> None:
    pipeline = ModelPipeline()
    results = pipeline.run_pipeline()
    print("Model Evaluation Complete (All parameters loaded from config):")
    for m_id, m_data in results["models"].items():
        metrics = m_data["metrics"]
        cv = m_data.get("cross_validation", {})
        print(
            f" - {m_id:<20}: Test Acc={metrics['accuracy']:.4f}, Test Macro-F1={metrics['macro_f1']:.4f}, "
            f"CV Mean Macro-F1={cv.get('mean_f1_macro', 0.0):.4f}"
        )


if __name__ == "__main__":
    main()
