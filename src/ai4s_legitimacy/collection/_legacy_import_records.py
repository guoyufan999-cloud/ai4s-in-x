from __future__ import annotations

import sqlite3
from typing import Any

from ai4s_legitimacy.cleaning.normalization import (
    hash_identifier,
    join_unique,
    mask_name,
    normalize_date,
    normalize_text,
)
from ai4s_legitimacy.coding.codebook_seed import (
    LEGACY_WORKFLOW_TO_STAGE_CODE,
    legacy_workflow_to_domain_code,
)
from ai4s_legitimacy.config.settings import PLATFORM_CODE

from ._legacy_import_contracts import (
    LegacyLookups,
    PreparedCommentInsert,
    PreparedPostInsert,
)


def _normalize_sample_status(value: str | None) -> str:
    sample_status = normalize_text(value)
    return sample_status if sample_status in {"true", "false", "review_needed"} else "review_needed"


def _build_post_notes(
    row: sqlite3.Row,
    label: sqlite3.Row | None,
) -> str | None:
    return join_unique(
        [
            f"legacy_decided_by={normalize_text(label['decided_by'])}" if label else None,
            f"legacy_review_override={int(label['review_override'])}" if label else None,
            f"legacy_note_type={normalize_text(row['note_type'])}"
            if normalize_text(row["note_type"])
            else None,
            f"legacy_media_count={int(row['media_count'])}",
        ],
        separator="; ",
    )


def _build_post_insert_values(
    row: sqlite3.Row,
    label: sqlite3.Row | None,
    *,
    batch_id: int,
    lookups: LegacyLookups,
    preserve_legacy_labels: bool,
) -> tuple[tuple[Any, ...], str | None, str | None]:
    note_id = str(row["note_id"])
    author_id = normalize_text(row["author_id"])
    author_name = lookups.author_name_map.get(author_id or "", "")
    legacy_workflow = normalize_text(label["workflow_primary"]) if label and preserve_legacy_labels else ""
    workflow_domain = legacy_workflow_to_domain_code(legacy_workflow)
    # Keep legacy stage labels in historical fields; v2 active coding lives elsewhere.
    workflow_stage = legacy_workflow or None
    primary_legitimacy_stance = (
        normalize_text(label["attitude_polarity"]) if label and preserve_legacy_labels else None
    )
    values = (
        note_id,
        PLATFORM_CODE,
        note_id,
        normalize_text(row["crawl_status"]) or "unknown",
        normalize_text(row["canonical_url"]) or normalize_text(row["source_url"]),
        hash_identifier(author_id or normalize_text(row["canonical_url"])),
        mask_name(author_name),
        normalize_date(row["publish_time"]),
        normalize_date(row["updated_at"]) or normalize_date(row["created_at"]),
        normalize_text(row["title"]),
        normalize_text(row["full_text"]),
        lookups.like_map.get(note_id),
        lookups.comment_count_map.get(note_id),
        None,
        lookups.query_map.get(note_id),
        1,
        (
            _normalize_sample_status(label["sample_status"] if label else "review_needed")
            if preserve_legacy_labels
            else "review_needed"
        ),
        None,
        normalize_text(label["actor_type"]) if label and preserve_legacy_labels else None,
        normalize_text(label["qs_broad_subject"]) if label and preserve_legacy_labels else None,
        workflow_domain,
        workflow_stage,
        primary_legitimacy_stance,
        0,
        None,
        0,
        None,
        None,
        label["risk_themes_json"] if label and preserve_legacy_labels else "[]",
        label["ai_tools_json"] if label and preserve_legacy_labels else "[]",
        label["benefit_themes_json"] if label and preserve_legacy_labels else "[]",
        batch_id,
        _build_post_notes(row, label),
    )
    return values, workflow_domain, legacy_workflow or None


def _build_post_code_insert_values(
    *,
    note_id: str,
    row: sqlite3.Row,
    label: sqlite3.Row,
    workflow_domain: str | None,
    legacy_workflow: str | None,
) -> tuple[Any, ...]:
    return (
        note_id,
        "post",
        None,
        workflow_domain,
        LEGACY_WORKFLOW_TO_STAGE_CODE.get(legacy_workflow or ""),
        None,
        0,
        None,
        normalize_text(label["decided_by"]) or "legacy_rule",
        normalize_text(row["updated_at"]) or normalize_text(row["created_at"]) or "legacy",
        0.85 if int(label["review_override"] or 0) else 0.65,
        "Legacy post coding migrated into workflow-only baseline; legality and boundary fields remain uncoded.",
    )


def prepare_post_insert(
    row: sqlite3.Row,
    label: sqlite3.Row | None,
    *,
    batch_id: int,
    lookups: LegacyLookups,
    preserve_legacy_labels: bool = True,
) -> PreparedPostInsert:
    note_id = str(row["note_id"])
    post_values, workflow_domain, legacy_workflow = _build_post_insert_values(
        row,
        label,
        batch_id=batch_id,
        lookups=lookups,
        preserve_legacy_labels=preserve_legacy_labels,
    )
    code_values = None
    if label and preserve_legacy_labels:
        code_values = _build_post_code_insert_values(
            note_id=note_id,
            row=row,
            label=label,
            workflow_domain=workflow_domain,
            legacy_workflow=legacy_workflow,
        )
    return PreparedPostInsert(post_values=post_values, code_values=code_values)


def _build_comment_insert_values(
    row: sqlite3.Row,
    label: sqlite3.Row | None,
    *,
    batch_id: int,
    preserve_legacy_labels: bool,
) -> tuple[Any, ...]:
    legacy_workflow = normalize_text(label["workflow_primary"]) if label and preserve_legacy_labels else None
    workflow_domain = legacy_workflow_to_domain_code(legacy_workflow)
    workflow_stage = legacy_workflow or None
    controversy = normalize_text(label["controversy_type"]) if label and preserve_legacy_labels else None
    stance = normalize_text(label["attitude_polarity"]) if label and preserve_legacy_labels else None
    return (
        str(row["comment_id"]),
        str(row["note_id"]),
        normalize_text(row["parent_comment_id"]) or None,
        normalize_date(row["comment_time"]),
        normalize_text(row["comment_text"]),
        hash_identifier(
            normalize_text(row["commenter_id"]) or normalize_text(row["commenter_name"])
        ),
        stance,
        controversy,
        workflow_domain,
        workflow_stage,
        0,
        None,
        1 if controversy == "risk" else 0,
        "boundary.assistance_vs_substitution" if controversy == "risk" else None,
        None,
        label["benefit_themes_json"] if label and preserve_legacy_labels else "[]",
        1 if normalize_text(row["parent_comment_id"]) else 0,
        batch_id,
    )


def _build_comment_code_insert_values(
    row: sqlite3.Row,
    label: sqlite3.Row,
) -> tuple[Any, ...]:
    workflow_stage = normalize_text(label["workflow_primary"])
    controversy = normalize_text(label["controversy_type"])
    return (
        str(row["comment_id"]),
        "comment",
        str(row["note_id"]),
        legacy_workflow_to_domain_code(workflow_stage),
        LEGACY_WORKFLOW_TO_STAGE_CODE.get(workflow_stage),
        None,
        1 if controversy == "risk" else 0,
        "boundary.assistance_vs_substitution" if controversy == "risk" else None,
        "legacy_comment_inheritance",
        normalize_text(row["updated_at"]) or normalize_text(row["created_at"]) or "legacy",
        0.6,
        "Legacy comment coding migrated with inherited workflow and boundary flag; legality fields remain uncoded.",
    )


def prepare_comment_insert(
    row: sqlite3.Row,
    label: sqlite3.Row | None,
    *,
    batch_id: int,
    preserve_legacy_labels: bool = True,
) -> PreparedCommentInsert:
    comment_values = _build_comment_insert_values(
        row,
        label,
        batch_id=batch_id,
        preserve_legacy_labels=preserve_legacy_labels,
    )
    code_values = (
        _build_comment_code_insert_values(row, label)
        if label and preserve_legacy_labels
        else None
    )
    return PreparedCommentInsert(
        comment_values=comment_values,
        code_values=code_values,
    )
