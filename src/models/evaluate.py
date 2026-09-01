"""Evaluation Harness for Renewal Classification Models.

Computes comprehensive classification metrics (accuracy, precision, recall, F1-score,
macro-F1, confusion matrix, per-class breakdown) and outputs directly to structured JSON.
"""

from __future__ import annotations

from typing import Any
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score


class ModelEvaluator:
    """Standardized evaluation harness producing JSON-compliant metric payloads."""

    TARGET_CLASSES = ["renew", "review", "do_not_renew"]

    @classmethod
    def evaluate(
        cls,
        y_true: list[str] | np.ndarray,
        y_pred: list[str] | np.ndarray,
        model_name: str,
        cv_scores: list[float] | None = None,
        target_classes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Compute all required classification performance metrics."""
        classes = target_classes or cls.TARGET_CLASSES
        y_t = np.asarray(y_true)
        y_p = np.asarray(y_pred)

        acc = float(accuracy_score(y_t, y_p))
        macro_prec = float(precision_score(y_t, y_p, average="macro", zero_division=0))
        macro_rec = float(recall_score(y_t, y_p, average="macro", zero_division=0))
        macro_f1 = float(f1_score(y_t, y_p, average="macro", zero_division=0))
        weighted_f1 = float(f1_score(y_t, y_p, average="weighted", zero_division=0))

        # Per-class breakdown
        per_class: dict[str, dict[str, float | int]] = {}
        for c in classes:
            mask_true = (y_t == c)
            mask_pred = (y_p == c)
            tp = int(np.sum(mask_true & mask_pred))
            fp = int(np.sum((~mask_true) & mask_pred))
            fn = int(np.sum(mask_true & (~mask_pred)))
            support = int(np.sum(mask_true))

            prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

            per_class[c] = {
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "support": support,
            }

        # Confusion matrix
        cm_raw = confusion_matrix(y_t, y_p, labels=classes)
        cm_dict = {
            "labels": classes,
            "matrix": cm_raw.tolist(),
            "breakdown": {
                actual: {
                    pred: int(cm_raw[i, j])
                    for j, pred in enumerate(classes)
                }
                for i, actual in enumerate(classes)
            }
        }

        result: dict[str, Any] = {
            "model_name": model_name,
            "sample_size": len(y_t),
            "metrics": {
                "accuracy": round(acc, 4),
                "macro_precision": round(macro_prec, 4),
                "macro_recall": round(macro_rec, 4),
                "macro_f1": round(macro_f1, 4),
                "weighted_f1": round(weighted_f1, 4),
            },
            "per_class_breakdown": per_class,
            "confusion_matrix": cm_dict,
        }

        if cv_scores:
            result["cross_validation"] = {
                "fold_scores": [round(s, 4) for s in cv_scores],
                "mean_f1_macro": round(float(np.mean(cv_scores)), 4),
                "std_f1_macro": round(float(np.std(cv_scores)), 4),
            }

        return result
