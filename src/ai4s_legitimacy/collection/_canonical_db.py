from __future__ import annotations

from typing import Any

from ai4s_legitimacy.collection.canonical_schema import (
    WORKFLOW_STAGE_LABELS,
    apply_claim_units_to_row,
    code_label,
    decision_to_sample_status,
    validate_canonical_row,
)

from ._review_db import json_dumps, table_columns

POST_CANONICAL_COLUMNS = {
    "task_batch_id": "TEXT",
    "coder_version": "TEXT",
    "language": "TEXT",
    "thread_id": "TEXT",
    "parent_post_id": "TEXT",
    "reply_to_post_id": "TEXT",
    "quoted_post_id": "TEXT",
    "context_available": "TEXT NOT NULL DEFAULT '否'",
    "context_used": "TEXT NOT NULL DEFAULT 'none'",
    "decision": "TEXT NOT NULL DEFAULT '待复核'",
    "decision_reason_json": "TEXT NOT NULL DEFAULT '[]'",
    "theme_summary": "TEXT",
    "target_practice_summary": "TEXT",
    "evidence_master_json": "TEXT NOT NULL DEFAULT '[]'",
    "discursive_mode": "TEXT",
    "practice_status": "TEXT",
    "speaker_position_claimed": "TEXT",
    "boundary_present": "TEXT NOT NULL DEFAULT '否'",
    "interaction_event_present": "TEXT NOT NULL DEFAULT '不适用'",
    "interaction_role": "TEXT",
    "interaction_target_claim_summary": "TEXT",
    "interaction_event_codes_json": "TEXT NOT NULL DEFAULT '[]'",
    "interaction_event_basis_codes_json": "TEXT NOT NULL DEFAULT '[]'",
    "interaction_outcome": "TEXT",
    "mechanism_eligible": "TEXT NOT NULL DEFAULT '否'",
    "mechanism_notes_json": "TEXT NOT NULL DEFAULT '[]'",
    "comparison_keys_json": "TEXT NOT NULL DEFAULT '[]'",
    "api_assistance_used": "TEXT NOT NULL DEFAULT '否'",
    "api_assistance_purpose_json": "TEXT NOT NULL DEFAULT '[]'",
    "api_assistance_confidence": "TEXT NOT NULL DEFAULT '无'",
    "api_assistance_note": "TEXT",
    "notes_multi_label": "TEXT NOT NULL DEFAULT '否'",
    "notes_ambiguity": "TEXT NOT NULL DEFAULT '否'",
    "notes_confidence": "TEXT NOT NULL DEFAULT '中'",
    "notes_review_points_json": "TEXT NOT NULL DEFAULT '[]'",
    "notes_dedup_group": "TEXT",
    "review_status": "TEXT NOT NULL DEFAULT 'unreviewed'",
}

COMMENT_CANONICAL_COLUMNS = POST_CANONICAL_COLUMNS | {
    "platform": "TEXT",
    "post_url": "TEXT",
}


def ensure_canonical_schema(connection) -> None:
    _ensure_columns(connection, "posts", POST_CANONICAL_COLUMNS)
    _ensure_columns(connection, "comments", COMMENT_CANONICAL_COLUMNS)
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS claim_units (
            record_type TEXT NOT NULL,
            record_id TEXT NOT NULL,
            claim_index INTEGER NOT NULL,
            practice_unit TEXT,
            workflow_stage_codes_json TEXT NOT NULL DEFAULT '[]',
            legitimacy_codes_json TEXT NOT NULL DEFAULT '[]',
            basis_codes_json TEXT NOT NULL DEFAULT '[]',
            boundary_codes_json TEXT NOT NULL DEFAULT '[]',
            boundary_mode_codes_json TEXT NOT NULL DEFAULT '[]',
            evidence_json TEXT NOT NULL DEFAULT '[]',
            PRIMARY KEY (record_type, record_id, claim_index)
        );
        CREATE INDEX IF NOT EXISTS idx_claim_units_record
        ON claim_units(record_type, record_id);
        CREATE TABLE IF NOT EXISTS interaction_events (
            record_type TEXT NOT NULL,
            record_id TEXT NOT NULL,
            event_present TEXT NOT NULL DEFAULT '不适用',
            interaction_role TEXT,
            target_claim_summary TEXT,
            event_codes_json TEXT NOT NULL DEFAULT '[]',
            event_basis_codes_json TEXT NOT NULL DEFAULT '[]',
            event_outcome TEXT,
            evidence_json TEXT NOT NULL DEFAULT '[]',
            PRIMARY KEY (record_type, record_id)
        );
        """
    )


def _ensure_columns(connection, table_name: str, column_defs: dict[str, str]) -> None:
    existing = table_columns(connection, table_name)
    for column_name, definition in column_defs.items():
        if column_name in existing:
            continue
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def apply_canonical_row_to_db(
    connection,
    *,
    row: dict[str, Any],
) -> dict[str, Any]:
    canonical = validate_canonical_row(row)
    canonical = apply_claim_units_to_row(canonical)
    record_type = canonical["record_type"]
    record_id = canonical["record_id"]
    if record_type == "post":
        _update_record(connection, table_name="posts", key_name="post_id", key_value=record_id, row=canonical)
    else:
        _update_record(
            connection,
            table_name="comments",
            key_name="comment_id",
            key_value=record_id,
            row=canonical,
        )
    _replace_claim_units(connection, row=canonical)
    _replace_interaction_event(connection, row=canonical)
    return canonical


def _update_record(
    connection,
    *,
    table_name: str,
    key_name: str,
    key_value: str,
    row: dict[str, Any],
) -> None:
    columns = table_columns(connection, table_name)
    summary_fields = _record_summary_fields(row, table_name=table_name)
    available = [(name, value) for name, value in summary_fields.items() if name in columns]
    if not available:
        return
    set_sql = ", ".join(f"{name} = ?" for name, _ in available)
    params = [value for _, value in available] + [key_value]
    connection.execute(f"UPDATE {table_name} SET {set_sql} WHERE {key_name} = ?", params)


def _legacy_workflow_domain(stage_code: str) -> str | None:
    prefix = str(stage_code or "").split(".", 1)[0]
    return {"A1": "P", "A2": "G", "A3": "T"}.get(prefix)


def _record_summary_fields(row: dict[str, Any], *, table_name: str) -> dict[str, Any]:
    workflow_codes = row["workflow_dimension"]["secondary_stage"]
    legitimacy_codes = row["legitimacy_evaluation"]["direction"]
    basis_codes = row["legitimacy_evaluation"]["basis"]
    boundary_codes = row["boundary_expression"]["boundary_content_codes"]
    review_points = row["notes"]["review_points"]
    primary_workflow_code = workflow_codes[0] if workflow_codes else ""
    primary_legitimacy_code = legitimacy_codes[0] if legitimacy_codes else ""
    primary_boundary_code = boundary_codes[0] if boundary_codes else ""
    summary = {
        "task_batch_id": row.get("task_batch_id") or "",
        "coder_version": row.get("coder_version") or "",
        "language": row.get("language") or "",
        "thread_id": row.get("thread_id") or "",
        "parent_post_id": row.get("parent_post_id") or "",
        "reply_to_post_id": row.get("reply_to_post_id") or "",
        "quoted_post_id": row.get("quoted_post_id") or "",
        "context_available": row["context_available"],
        "context_used": row["context_used"],
        "decision": row["decision"],
        "decision_reason_json": json_dumps(row["decision_reason"]),
        "decision_reason": " | ".join(row["decision_reason"]),
        "theme_summary": row.get("theme_summary") or "",
        "target_practice_summary": row.get("target_practice_summary") or "",
        "evidence_master_json": json_dumps(row["evidence_master"]),
        "discursive_mode": row.get("discursive_mode") or "",
        "practice_status": row.get("practice_status") or "",
        "speaker_position_claimed": row.get("speaker_position_claimed") or "",
        "boundary_present": row["boundary_expression"]["present"],
        "interaction_event_present": row["interaction_level"]["event_present"],
        "interaction_role": row["interaction_level"]["interaction_role"],
        "interaction_target_claim_summary": row["interaction_level"]["target_claim_summary"],
        "interaction_event_codes_json": json_dumps(row["interaction_level"]["event_codes"]),
        "interaction_event_basis_codes_json": json_dumps(row["interaction_level"]["event_basis_codes"]),
        "interaction_outcome": row["interaction_level"]["event_outcome"],
        "mechanism_eligible": row["mechanism_memo"]["eligible_for_mechanism_analysis"],
        "mechanism_notes_json": json_dumps(row["mechanism_memo"]["candidate_pattern_notes"]),
        "comparison_keys_json": json_dumps(row["mechanism_memo"]["comparison_keys"]),
        "api_assistance_used": row["api_assistance"]["used"],
        "api_assistance_purpose_json": json_dumps(row["api_assistance"]["purpose"]),
        "api_assistance_confidence": row["api_assistance"]["api_confidence"],
        "api_assistance_note": row["api_assistance"]["adoption_note"],
        "notes_multi_label": row["notes"]["multi_label"],
        "notes_ambiguity": row["notes"]["ambiguity"],
        "notes_confidence": row["notes"]["confidence"],
        "notes_review_points_json": json_dumps(review_points),
        "notes_dedup_group": row["notes"]["dedup_group"],
        "review_status": row["review_status"],
        "sample_status": decision_to_sample_status(row["decision"]),
        "workflow_domain": _legacy_workflow_domain(primary_workflow_code),
        "workflow_stage": WORKFLOW_STAGE_LABELS.get(primary_workflow_code),
        "primary_legitimacy_stance": code_label(primary_legitimacy_code) if primary_legitimacy_code else None,
        "has_legitimacy_evaluation": 0 if primary_legitimacy_code in {"", "B0"} else 1,
        "primary_legitimacy_code": primary_legitimacy_code or None,
        "boundary_discussion": 1 if row["boundary_expression"]["present"] == "是" else 0,
        "primary_boundary_type": code_label(primary_boundary_code) if primary_boundary_code else None,
        "uncertainty_note": "；".join(review_points) if review_points else None,
    }
    actor_type = row.get("actor_type")
    if actor_type not in (None, ""):
        summary["actor_type"] = actor_type
    qs_broad_subject = row.get("qs_broad_subject")
    if qs_broad_subject not in (None, ""):
        summary["qs_broad_subject"] = qs_broad_subject
    if table_name == "comments":
        summary["platform"] = row.get("platform") or "xiaohongshu"
        summary["post_url"] = row.get("post_url") or ""
        summary["stance"] = code_label(primary_legitimacy_code) if primary_legitimacy_code else None
        summary["legitimacy_basis"] = code_label(basis_codes[0]) if basis_codes else None
        if row["record_type"] == "reply":
            summary["is_reply"] = 1
    return summary


def _replace_claim_units(connection, *, row: dict[str, Any]) -> None:
    record_type = row["record_type"]
    record_id = row["record_id"]
    connection.execute(
        "DELETE FROM claim_units WHERE record_type = ? AND record_id = ?",
        (record_type, record_id),
    )
    for index, unit in enumerate(row["claim_units"]):
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type,
                record_id,
                claim_index,
                practice_unit,
                workflow_stage_codes_json,
                legitimacy_codes_json,
                basis_codes_json,
                boundary_codes_json,
                boundary_mode_codes_json,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_type,
                record_id,
                index,
                unit.get("practice_unit") or "",
                json_dumps(unit.get("workflow_stage_codes") or []),
                json_dumps(unit.get("legitimacy_codes") or []),
                json_dumps(unit.get("basis_codes") or []),
                json_dumps(unit.get("boundary_codes") or []),
                json_dumps(unit.get("boundary_mode_codes") or []),
                json_dumps(unit.get("evidence") or []),
            ),
        )


def _replace_interaction_event(connection, *, row: dict[str, Any]) -> None:
    interaction = row["interaction_level"]
    record_type = row["record_type"]
    record_id = row["record_id"]
    connection.execute(
        """
        INSERT OR REPLACE INTO interaction_events (
            record_type,
            record_id,
            event_present,
            interaction_role,
            target_claim_summary,
            event_codes_json,
            event_basis_codes_json,
            event_outcome,
            evidence_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record_type,
            record_id,
            interaction["event_present"],
            interaction["interaction_role"],
            interaction["target_claim_summary"],
            json_dumps(interaction["event_codes"]),
            json_dumps(interaction["event_basis_codes"]),
            interaction["event_outcome"],
            json_dumps(interaction["evidence"]),
        ),
    )
