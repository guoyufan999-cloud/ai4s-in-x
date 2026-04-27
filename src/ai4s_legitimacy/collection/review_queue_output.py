from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.formal_baseline import (
    REBASELINE_STAGING_DB_PATH,
    REBASELINE_SUGGESTIONS_DIR,
)
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

from ._canonical_review import canonicalize_review_row
from .review_queue_io import REVIEW_PHASES, _default_output_path
from .review_queue_rows import _rows_for_phase


def _empty_queue_row_for_phase(phase: str, row: dict[str, Any]) -> dict[str, Any]:
    canonical = canonicalize_review_row(
        dict(row) | {"review_phase": phase, "review_status": "unreviewed"},
        base_row=row,
        review_phase=phase,
    )
    canonical["review_status"] = "unreviewed"
    if phase == "rescreen_posts":
        canonical["workflow_dimension"] = {
            "primary_dimension": [],
            "secondary_stage": [],
            "evidence": [],
        }
        canonical["legitimacy_evaluation"] = {
            "direction": [],
            "basis": [],
            "evidence": [],
        }
        canonical["boundary_expression"] = {
            "present": "否",
            "boundary_content_codes": [],
            "boundary_expression_mode_codes": [],
            "evidence": [],
        }
        canonical["interaction_level"] = {
            "event_present": "不适用" if canonical["context_used"] == "none" else "无法判断",
            "interaction_role": "unclear",
            "target_claim_summary": "",
            "event_codes": [],
            "event_basis_codes": [],
            "event_outcome": "",
            "evidence": [],
        }
        canonical["claim_units"] = []
        canonical["evidence_master"] = []
        canonical["notes"]["multi_label"] = "否"

    for field, value in row.items():
        if field in canonical or value is None:
            continue
        canonical[field] = value
    return canonical


def export_review_queue(
    *,
    db_path: Path = REBASELINE_STAGING_DB_PATH,
    phase: str,
    output_path: Path | None = None,
    limit: int | None = None,
    suggestions_dir: Path = REBASELINE_SUGGESTIONS_DIR,
) -> Path:
    if phase not in REVIEW_PHASES:
        valid_phases = ", ".join(REVIEW_PHASES)
        raise ValueError(f"Unknown review phase: {phase}. Expected one of: {valid_phases}")

    with connect_sqlite_readonly(db_path) as connection:
        rows = _rows_for_phase(
            connection,
            phase=phase,
            suggestions_dir=suggestions_dir,
        )
    if limit is not None:
        rows = rows[: int(limit)]

    output = output_path or _default_output_path(phase)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = _empty_queue_row_for_phase(phase, {"review_phase": phase} | row)
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return output
