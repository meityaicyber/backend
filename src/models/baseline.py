"""Rule-Based Threshold Heuristic Baseline Classifier.

Implements a deterministic statistical heuristic classifier as a classical baseline
to benchmark machine learning models against.
"""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin


class RuleBaselineClassifier(BaseEstimator, ClassifierMixin):
    """Rule-based baseline classifier applying linear heuristic thresholds."""

    def __init__(
        self,
        renew_cutoff: float = 70.0,
        review_cutoff: float = 50.0,
        weights: list[float] | None = None,
    ) -> None:
        self.renew_cutoff = renew_cutoff
        self.review_cutoff = review_cutoff
        # Default weights for the 6 features: timeliness, efficiency, error_rate, scale, compliance, renewal_history
        self.weights = weights if weights is not None else [0.20, 0.15, 0.20, 0.10, 0.20, 0.15]
        self.classes_ = np.array(["do_not_renew", "renew", "review"])

    def fit(self, X: np.ndarray, y: np.ndarray | None = None) -> RuleBaselineClassifier:
        """Fit method (stateless heuristic, validates input dimensions)."""
        X = np.asarray(X)
        if len(self.weights) != X.shape[1]:
            raise ValueError(f"Expected {len(self.weights)} feature weights, got {X.shape[1]}")
        return self

    def _compute_heuristic_score(self, x: np.ndarray) -> float:
        """Calculate weighted score with error rate inversion and missing data adjustment."""
        w = np.array(self.weights)
        valid_mask = ~np.isnan(x)
        if not np.any(valid_mask):
            return 50.0  # Neutral fallback

        x_adj = x.copy()
        # Invert error_rate (index 2)
        if valid_mask[2]:
            x_adj[2] = max(0.0, 100.0 - x_adj[2])

        w_valid = w[valid_mask]
        x_valid = x_adj[valid_mask]
        total_w = np.sum(w_valid)
        if total_w == 0:
            return 50.0
        return float(np.sum(x_valid * w_valid) / total_w)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict renewal decision for each sample."""
        X = np.asarray(X)
        preds = []
        for row in X:
            score = self._compute_heuristic_score(row)
            if score >= self.renew_cutoff:
                preds.append("renew")
            elif score >= self.review_cutoff:
                preds.append("review")
            else:
                preds.append("do_not_renew")
        return np.array(preds)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Compute pseudo-probabilities based on distance to decision thresholds."""
        X = np.asarray(X)
        probas = []
        # Class order: ["do_not_renew", "renew", "review"]
        for row in X:
            score = self._compute_heuristic_score(row)
            if score >= self.renew_cutoff:
                probas.append([0.05, 0.85, 0.10])
            elif score >= self.review_cutoff:
                probas.append([0.15, 0.20, 0.65])
            else:
                probas.append([0.80, 0.05, 0.15])
        return np.array(probas)
