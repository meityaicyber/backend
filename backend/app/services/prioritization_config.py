PRIORITY_CONFIG = {
    "version": "1",
    "weights": {"urgency": 0.35, "impact": 0.50, "resource": 0.15},
    "thresholds": {"CRITICAL": 80, "HIGH": 60, "MEDIUM": 40, "LOW": 20},
    "severity_scores": {"CRITICAL": 100, "HIGH": 80, "MEDIUM": 50, "LOW": 20, "INFORMATIONAL": 0},
    "impact_weights": {
        "base_severity": 0.40,
        "exploitability": 0.20,
        "asset_criticality": 0.15,
        "affected_assets": 0.10,
        "data_sensitivity": 0.10,
        "agency_risk": 0.05,
    },
    "urgency_weights": {"deadline": 0.60, "age": 0.40},
    "sla_target_days": {"CRITICAL": 15, "HIGH": 30, "MEDIUM": 60, "LOW": 90, "INFORMATIONAL": 120},
    "deadline_bands": [(7, 85), (30, 65), (90, 40)],
    "effort_scores": {"LOW": 80, "MEDIUM": 50, "HIGH": 20},
    "status_multipliers": {
        "OPEN": 1.0,
        "IN_PROGRESS": 0.8,
        "ACCEPTED": 0.0,
        "RISK_ACCEPTED": 0.0,
        "CLOSED": 0.0
    },
    "critical_floor_level": "HIGH",
    "resources": {
        "security_team": 2,
        "development_team": 4,
        "infrastructure_team": 2
    },
}

def validate_config(config):
    # Validate weights sum to 1
    w_sum = sum(config["weights"].values())
    if abs(w_sum - 1.0) > 0.001:
        raise ValueError(f"Primary weights must sum to 1, got {w_sum}")
    
    # Validate thresholds are descending
    prev = 101
    for k, v in config["thresholds"].items():
        if v >= prev:
            raise ValueError("Thresholds must be strictly descending")
        prev = v

validate_config(PRIORITY_CONFIG)
