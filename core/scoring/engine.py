from __future__ import annotations

from typing import Any


def decision_for_score(score: float, thresholds: dict[str, float], tolerance: float) -> dict[str, Any]:
    if score >= thresholds["renew"]:
        decision = "renew"
        boundary = thresholds["renew"] - tolerance <= score <= thresholds["renew"] + tolerance
    elif score >= thresholds["review"]:
        decision = "review"
        boundary = thresholds["review"] - tolerance <= score <= thresholds["review"] + tolerance
    else:
        decision = "do_not_renew"
        boundary = score >= thresholds["review"] - tolerance
    nearest = min(abs(score - threshold) for threshold in thresholds.values())
    return {"decision": decision, "boundary_status": "boundary_case" if boundary else "clear", "distance_to_boundary": round(nearest, 2)}


def calculate_score(features: dict[str, float | None], config: dict[str, Any]) -> dict[str, Any]:
    weights = config["weights"]
    assessable = {key: value for key, value in features.items() if value is not None and key in weights}
    if not assessable:
        return {"score": None, "status": "not_assessable", "reason": "no assessable features"}
    total_weight = sum(weights[key] for key in assessable)
    score = sum(float(assessable[key]) * weights[key] for key in assessable) / total_weight
    result = {"score": round(score, 2), "status": "assessable", "assessable_features": list(assessable), "excluded_features": [key for key in weights if key not in assessable]}
    result.update(decision_for_score(score, config["thresholds"], config["boundary_tolerance"]))
    return result
