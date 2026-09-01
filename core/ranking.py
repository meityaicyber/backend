from __future__ import annotations

from typing import Any


def rank_scores(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(scores, key=lambda item: (-item["score"], item["organisation_id"]))
    return [{**item, "rank": index + 1} for index, item in enumerate(ordered)]
