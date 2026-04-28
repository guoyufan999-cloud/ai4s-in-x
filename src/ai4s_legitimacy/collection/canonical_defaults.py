from __future__ import annotations

from typing import Any

from .canonical_constants import RECORD_ID_FIELD, RECORD_TYPE_VALUES


def empty_workflow_dimension() -> dict[str, Any]:
    return {
        "primary_dimension": [],
        "secondary_stage": [],
        "evidence": [],
    }


def empty_legitimacy_evaluation() -> dict[str, Any]:
    return {
        "direction": [],
        "basis": [],
        "evidence": [],
    }


def empty_boundary_expression() -> dict[str, Any]:
    return {
        "present": "否",
        "boundary_content_codes": [],
        "boundary_expression_mode_codes": [],
        "evidence": [],
    }


def empty_interaction_level() -> dict[str, Any]:
    return {
        "event_present": "不适用",
        "interaction_role": "unclear",
        "target_claim_summary": "",
        "event_codes": [],
        "event_basis_codes": [],
        "event_outcome": "",
        "evidence": [],
    }


def empty_mechanism_memo() -> dict[str, Any]:
    return {
        "eligible_for_mechanism_analysis": "否",
        "candidate_pattern_notes": [],
        "comparison_keys": [],
    }


def empty_api_assistance() -> dict[str, Any]:
    return {
        "used": "否",
        "purpose": [],
        "api_confidence": "无",
        "adoption_note": "",
    }


def empty_notes(record_id: str) -> dict[str, Any]:
    return {
        "multi_label": "否",
        "ambiguity": "否",
        "confidence": "中",
        "review_points": [],
        "dedup_group": record_id,
    }


def build_empty_canonical_row(
    record_type: str,
    record_id: str,
    *,
    platform: str = "xiaohongshu",
) -> dict[str, Any]:
    if record_type not in RECORD_TYPE_VALUES:
        raise ValueError(f"Unsupported record_type: {record_type}")
    id_field = RECORD_ID_FIELD[record_type]
    row = {
        "post_id": "",
        "task_batch_id": "",
        "coder_version": "",
        "platform": platform,
        "post_url": "",
        "author_id": "",
        "created_at": "",
        "language": "",
        "thread_id": "",
        "parent_post_id": "",
        "reply_to_post_id": "",
        "quoted_post_id": "",
        "context_available": "否",
        "context_used": "none",
        "source_text": "",
        "context_text": "",
        "decision": "待复核",
        "decision_reason": [],
        "theme_summary": "",
        "target_practice_summary": "",
        "evidence_master": [],
        "discursive_mode": "",
        "practice_status": "",
        "speaker_position_claimed": "",
        "workflow_dimension": empty_workflow_dimension(),
        "legitimacy_evaluation": empty_legitimacy_evaluation(),
        "boundary_expression": empty_boundary_expression(),
        "interaction_level": empty_interaction_level(),
        "claim_units": [],
        "mechanism_memo": empty_mechanism_memo(),
        "api_assistance": empty_api_assistance(),
        "notes": empty_notes(record_id),
        "review_status": "unreviewed",
        "record_type": record_type,
        "record_id": record_id,
    }
    row[id_field] = record_id
    return row


def canonical_record_identity(row: dict[str, Any]) -> tuple[str, str]:
    record_type = str(row.get("record_type") or "").strip()
    if record_type not in RECORD_TYPE_VALUES:
        record_type = "comment" if str(row.get("comment_id") or "").strip() else "post"
    record_id = str(row.get("record_id") or "").strip()
    if not record_id:
        record_id = str(row.get(RECORD_ID_FIELD[record_type]) or "").strip()
    if not record_id:
        raise ValueError("Canonical row missing record_id")
    return record_type, record_id
