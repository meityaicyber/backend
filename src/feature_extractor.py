"""Config-Driven Feature Extractor for Auditing Agency Performance Monitoring.

All extraction rules — field names, filter values, benchmark constants, component
weights and normalisers — are read exclusively from
``config/feature_definitions.json`` (``raw_extraction`` block per feature).

To change a formula or threshold, edit the JSON config.  No Python changes needed.

Supported extraction strategies
---------------------------------
Strategy                        | Feature
--------------------------------|---------------------------
ratio_filter_date_compare       | audit_timeliness
benchmark_duration_index        | audit_efficiency
ratio_nested_flag               | error_rate
composite_workforce_index       | agency_scale
latest_assessment_control_pass_rate | compliance_adherence
ratio_multi_filter              | past_renewal_status
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "feature_definitions.json"


def _load_feature_config(config_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load and return the list of feature definitions from config."""
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("features", [])


# ---------------------------------------------------------------------------
# Shared date utility
# ---------------------------------------------------------------------------

def _parse_date(value: str | None) -> date | None:
    """Parse an ISO-8601 date string (YYYY-MM-DD) to a date object, or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Per-strategy extractors — all parameters come from the spec dict
# ---------------------------------------------------------------------------

def _apply_ratio_filter_date_compare(
    spec: dict[str, Any],
    data: list[dict[str, Any]],
) -> float | None:
    """Strategy: ratio_filter_date_compare (audit_timeliness).

    Filters rows by a field equality check, then counts rows where
    date_field_a <= date_field_b, divided by total passing rows.
    """
    row_filter = spec["row_filter"]
    num_spec = spec["numerator"]
    scale = float(spec.get("scale_factor", 100.0))

    # Apply row filter + require both date fields present
    date_a_field = num_spec["date_field_a"]
    date_b_field = num_spec["date_field_b"]

    eligible = [
        row for row in data
        if row.get(row_filter["field"]) == row_filter["equals"]
        and _parse_date(row.get(date_a_field)) is not None
        and _parse_date(row.get(date_b_field)) is not None
    ]

    if not eligible:
        return None

    count = sum(
        1 for row in eligible
        if _parse_date(row[date_a_field]) <= _parse_date(row[date_b_field])  # type: ignore[operator]
    )
    return round((count / len(eligible)) * scale, 1)


def _apply_benchmark_duration_index(
    spec: dict[str, Any],
    data: list[dict[str, Any]],
) -> float | None:
    """Strategy: benchmark_duration_index (audit_efficiency).

    Computes average duration between two date fields on filtered rows,
    then expresses it as a benchmark-relative index clamped to [min, max].
    """
    row_filter = spec["row_filter"]
    dur_spec = spec["duration"]
    benchmark = float(spec["benchmark_days"])
    clamp_min = float(spec.get("clamp_min", 0.0))
    clamp_max = float(spec.get("clamp_max", 100.0))
    scale = float(spec.get("scale_factor", 100.0))

    start_field = dur_spec["start_date_field"]
    end_field = dur_spec["end_date_field"]

    durations: list[float] = []
    for row in data:
        if row.get(row_filter["field"]) != row_filter["equals"]:
            continue
        start = _parse_date(row.get(start_field))
        end = _parse_date(row.get(end_field))
        if start and end and end >= start:
            durations.append(float((end - start).days))

    if not durations:
        return None

    avg_days = max(sum(durations) / len(durations), 1.0)
    raw = (benchmark / avg_days) * scale
    return round(min(clamp_max, max(clamp_min, raw)), 1)


def _apply_ratio_nested_flag(
    spec: dict[str, Any],
    data: list[dict[str, Any]],
) -> float | None:
    """Strategy: ratio_nested_flag (error_rate).

    Counts rows (passing a row filter) where ANY item in a nested array
    matches a field-value filter, divided by total passing rows.
    """
    row_filter = spec["row_filter"]
    num_spec = spec["numerator"]
    scale = float(spec.get("scale_factor", 100.0))

    nested_array = num_spec["nested_array_field"]
    nested_field = num_spec["nested_filter_field"]
    nested_value = num_spec["nested_filter_value"]

    eligible = [
        row for row in data
        if row.get(row_filter["field"]) == row_filter["equals"]
    ]

    if not eligible:
        return None

    count = sum(
        1 for row in eligible
        if any(
            item.get(nested_field) == nested_value
            for item in row.get(nested_array, [])
        )
    )
    return round((count / len(eligible)) * scale, 1)


def _apply_composite_workforce_index(
    spec: dict[str, Any],
    data: list[dict[str, Any]],
) -> float | None:
    """Strategy: composite_workforce_index (agency_scale).

    Each component specifies its aggregation type, normaliser, and weight.
    Supported component types:
      - count_where_bool_true  : count rows where field == True
      - years_since_min_date   : years from the earliest date value in date_field

    Final score = min(clamp_max, sum(min(value / normaliser, 1.0) * weight)).
    """
    if not data:
        return None

    components: list[dict[str, Any]] = spec.get("components", [])
    clamp_max = float(spec.get("clamp_max", 100.0))
    ref = date.today()
    total_score = 0.0

    for comp in components:
        comp_type = comp["type"]
        normaliser = float(comp["normaliser"])
        weight = float(comp["weight"])

        if comp_type == "count_where_bool_true":
            field = comp["field"]
            raw_value = float(sum(1 for row in data if row.get(field) is True))

        elif comp_type == "years_since_min_date":
            date_field = comp["date_field"]
            dates = [
                _parse_date(row.get(date_field))
                for row in data
                if _parse_date(row.get(date_field)) is not None
            ]
            if not dates:
                raw_value = 0.0
            else:
                earliest = min(dates)  # type: ignore[type-var]
                raw_value = max(0.0, (ref - earliest).days / 365.25)

        else:
            # Unknown component type — treat as zero contribution
            raw_value = 0.0

        total_score += min(raw_value / normaliser, 1.0) * weight

    result = min(clamp_max, total_score)
    return round(result, 1)


def _apply_latest_assessment_control_pass_rate(
    spec: dict[str, Any],
    data: list[dict[str, Any]],
) -> float | None:
    """Strategy: latest_assessment_control_pass_rate (compliance_adherence).

    Picks the assessment with the latest date, then computes
    (applicable controls with result == pass_value) / (total applicable controls).
    """
    if not data:
        return None

    sort_field = spec["assessment_sort_field"]
    controls_field = spec["controls_array_field"]
    applicable_filter = spec["applicable_filter"]
    pass_filter = spec["pass_filter"]
    scale = float(spec.get("scale_factor", 100.0))

    def _sort_key(a: dict[str, Any]) -> date:
        return _parse_date(a.get(sort_field)) or date.min

    order = spec.get("assessment_sort_order", "latest")
    sorted_assessments = sorted(data, key=_sort_key, reverse=(order == "latest"))
    latest = sorted_assessments[0]

    # Filter applicable controls
    applicable = [
        c for c in latest.get(controls_field, [])
        if c.get(applicable_filter["field"]) == applicable_filter["equals"]
    ]

    if not applicable:
        return None

    passed = sum(
        1 for c in applicable
        if c.get(pass_filter["field"]) == pass_filter["equals"]
    )
    return round((passed / len(applicable)) * scale, 1)


def _apply_ratio_multi_filter(
    spec: dict[str, Any],
    data: list[dict[str, Any]],
) -> float | None:
    """Strategy: ratio_multi_filter (past_renewal_status).

    Counts rows passing ALL conditions in numerator.filters,
    divided by total rows (denominator.type == count_all).
    """
    num_spec = spec["numerator"]
    den_spec = spec["denominator"]
    scale = float(spec.get("scale_factor", 100.0))

    if not data:
        return None

    # Denominator
    if den_spec["type"] == "count_all":
        denom = len(data)
    else:
        denom = len(data)

    if denom == 0:
        return None

    # Numerator — all filters must pass (logical AND)
    filters: list[dict[str, Any]] = num_spec.get("filters", [])
    numer = 0
    for row in data:
        if all(row.get(f["field"]) == f["equals"] for f in filters):
            numer += 1

    return round((numer / denom) * scale, 1)


# ---------------------------------------------------------------------------
# Strategy dispatcher
# ---------------------------------------------------------------------------

_STRATEGY_MAP = {
    "ratio_filter_date_compare": _apply_ratio_filter_date_compare,
    "benchmark_duration_index": _apply_benchmark_duration_index,
    "ratio_nested_flag": _apply_ratio_nested_flag,
    "composite_workforce_index": _apply_composite_workforce_index,
    "latest_assessment_control_pass_rate": _apply_latest_assessment_control_pass_rate,
    "ratio_multi_filter": _apply_ratio_multi_filter,
}


def _extract_one_feature(
    feature_def: dict[str, Any],
    organisation: dict[str, Any],
) -> float | None:
    """Extract a single feature value by reading its raw_extraction spec from config."""
    spec = feature_def.get("raw_extraction")
    if not spec:
        return None

    strategy = spec.get("strategy")
    handler = _STRATEGY_MAP.get(strategy)  # type: ignore[arg-type]
    if handler is None:
        raise ValueError(
            f"Unknown extraction strategy '{strategy}' for feature '{feature_def['id']}'. "
            f"Supported: {list(_STRATEGY_MAP.keys())}"
        )

    source_section = spec.get("source_section", "")
    section_data: list[dict[str, Any]] = organisation.get(source_section, [])

    return handler(spec, section_data)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_features(
    organisation: dict[str, Any],
    config_path: str | Path | None = None,
) -> dict[str, float | None]:
    """Derive all six scoring features from a raw organisation record.

    All extraction rules are read from ``config/feature_definitions.json``
    (``raw_extraction`` block).  To change a formula, edit the config file only.

    Parameters
    ----------
    organisation:
        A single organisation dict as per the input schema, containing keys:
        ``audits``, ``auditors``, ``compliance_assessments``, ``renewal_history``.
        All keys are optional; missing sections are treated as empty lists.
    config_path:
        Optional override path to ``feature_definitions.json``.
        Defaults to ``<project_root>/config/feature_definitions.json``.

    Returns
    -------
    dict[str, float | None]
        Feature dict keyed by the canonical feature IDs used throughout the scoring
        pipeline.  A ``None`` value means the feature is non-assessable for that
        organisation and will be excluded from scoring with renormalised weights.
    """
    feature_defs = _load_feature_config(config_path)
    return {
        feat["id"]: _extract_one_feature(feat, organisation)
        for feat in feature_defs
        if "raw_extraction" in feat
    }


def is_raw_organisation(org: dict[str, Any]) -> bool:
    """Return True if the organisation dict contains raw operational data (not pre-computed features).

    Heuristic: at least one of the raw data section keys is present.
    """
    raw_keys = {"audits", "auditors", "compliance_assessments", "renewal_history"}
    return bool(raw_keys & set(org.keys()))
