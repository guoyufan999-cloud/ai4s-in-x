from __future__ import annotations

from pathlib import Path
from typing import Any

from ._canonical_review import canonicalize_review_row
from ._review_db import load_reviewed_payloads
from .canonical_schema import validate_canonical_row
from .review_queue import _load_suggestion_index
from .review_v2_artifact_bootstrap import json_list


def canonical_record_from_source(
    *,
    record_type: str,
    base_row: dict[str, Any],
    review_phase: str,
    reviewed_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    if reviewed_payload:
        try:
            canonical = validate_canonical_row(reviewed_payload)
        except ValueError:
            canonical = canonicalize_review_row(
                reviewed_payload,
                base_row=base_row,
                review_phase=review_phase,
            )
        if canonical.get("review_status") == "unreviewed":
            canonical["review_status"] = "reviewed"
        return validate_canonical_row(canonical)

    seed = dict(base_row)
    seed.update(
        {
            "record_type": record_type,
            "record_id": str(
                base_row["post_id"] if record_type == "post" else base_row["comment_id"]
            ),
            "review_phase": f"{review_phase}_bootstrap",
            "review_status": str(base_row.get("review_status") or "unreviewed"),
        }
    )
    if str(base_row.get("decision") or "").strip():
        seed["decision"] = str(base_row.get("decision") or "").strip()
    if base_row.get("decision_reason_json") not in (None, ""):
        seed["decision_reason"] = json_list(base_row.get("decision_reason_json"))
    canonical = canonicalize_review_row(
        seed,
        base_row=base_row,
        review_phase=f"{review_phase}_bootstrap",
    )
    return validate_canonical_row(canonical)


def build_post_records(connection, suggestions_dir: Path) -> list[dict[str, Any]]:
    reviewed_payloads = load_reviewed_payloads(
        connection,
        review_phase="post_review_v2",
        record_type="post",
    )
    rescreen_payloads = load_reviewed_payloads(
        connection,
        review_phase="rescreen_posts",
        record_type="post",
    )
    suggestion_index = _load_suggestion_index(suggestions_dir)
    records: list[dict[str, Any]] = []
    for row in connection.execute("SELECT * FROM posts ORDER BY post_date, post_id").fetchall():
        post = dict(row)
        post_id = str(post["post_id"])
        canonical = canonical_record_from_source(
            record_type="post",
            base_row=post,
            review_phase="post_review_v2",
            reviewed_payload=reviewed_payloads.get(post_id),
        )
        canonical["historical_sample_status"] = str(post.get("sample_status") or "")
        if post.get("post_date") not in (None, ""):
            canonical["post_date"] = post.get("post_date")
        if post.get("title") not in (None, ""):
            canonical["title"] = post.get("title")
        if post_id in rescreen_payloads:
            canonical["historical_rescreen"] = rescreen_payloads[post_id]
        if post_id in suggestion_index:
            canonical["deepseek_suggestion"] = suggestion_index[post_id]
        records.append(canonical)
    return records


def build_comment_records(
    connection,
    *,
    included_post_ids: set[str],
) -> list[dict[str, Any]]:
    reviewed_payloads = load_reviewed_payloads(
        connection,
        review_phase="comment_review_v2",
        record_type="comment",
    )
    records: list[dict[str, Any]] = []
    for row in connection.execute("SELECT * FROM comments ORDER BY comment_date, comment_id").fetchall():
        comment = dict(row)
        post_id = str(comment["post_id"])
        if post_id not in included_post_ids:
            continue
        comment_id = str(comment["comment_id"])
        canonical = canonical_record_from_source(
            record_type="reply" if str(comment.get("is_reply") or "") in {"1", "true"} else "comment",
            base_row=comment,
            review_phase="comment_review_v2",
            reviewed_payload=reviewed_payloads.get(comment_id),
        )
        canonical["comment_id"] = comment_id
        canonical["post_id"] = post_id
        if comment.get("comment_date") not in (None, ""):
            canonical["comment_date"] = comment.get("comment_date")
        records.append(canonical)
    return records
