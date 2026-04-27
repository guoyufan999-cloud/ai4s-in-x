from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .canonical_schema import decision_to_sample_status


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def build_delta_report(post_records: list[dict[str, Any]]) -> dict[str, Any]:
    changes: dict[str, list[dict[str, Any]]] = {
        "old_true_to_new_false": [],
        "old_false_to_new_true": [],
        "old_review_needed_to_new_true": [],
    }
    decision_counts = {"纳入": 0, "剔除": 0, "待复核": 0}
    claim_unit_distribution: dict[str, int] = {}
    for row in post_records:
        decision = str(row["decision"])
        old_status = str(row.get("historical_sample_status") or "")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        claim_units = row.get("claim_units") or []
        claim_unit_distribution[str(len(claim_units))] = claim_unit_distribution.get(
            str(len(claim_units)),
            0,
        ) + 1
        entry = {
            "post_id": row["post_id"],
            "title": row.get("theme_summary") or row.get("title"),
            "old_status": old_status,
            "new_status": decision_to_sample_status(decision),
            "reason": " | ".join(row.get("decision_reason") or []),
        }
        if old_status == "true" and decision == "剔除":
            changes["old_true_to_new_false"].append(entry)
        elif old_status == "false" and decision == "纳入":
            changes["old_false_to_new_true"].append(entry)
        elif old_status == "review_needed" and decision == "纳入":
            changes["old_review_needed_to_new_true"].append(entry)
    return {
        "decision_counts": decision_counts,
        "claim_unit_distribution": claim_unit_distribution,
        "key_changes": changes,
    }
