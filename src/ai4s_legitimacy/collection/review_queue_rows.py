from __future__ import annotations

from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.formal_baseline import REBASELINE_SUGGESTIONS_DIR

from ._review_db import coalesce_mapping_value, load_reviewed_payloads
from .review_queue_io import REVIEW_PHASES, _load_suggestion_index


def _stable_post_row(post: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "post",
        "record_id": post["post_id"],
        "post_id": post["post_id"],
        "post_date": post.get("post_date"),
        "legacy_crawl_status": post.get("legacy_crawl_status"),
        "keyword_query": post.get("keyword_query"),
        "title": post.get("title"),
        "content_text": post.get("content_text"),
        "sample_status": post.get("sample_status"),
        "historical_sample_status": post.get("sample_status"),
        "decision_reason": post.get("decision_reason"),
        "actor_type": post.get("actor_type"),
        "historical_actor_type": post.get("actor_type"),
        "qs_broad_subject": post.get("qs_broad_subject"),
        "workflow_domain": post.get("workflow_domain"),
        "workflow_stage": post.get("workflow_stage"),
        "primary_legitimacy_stance": post.get("primary_legitimacy_stance"),
        "primary_legitimacy_code": post.get("primary_legitimacy_code"),
        "has_legitimacy_evaluation": post.get("has_legitimacy_evaluation"),
        "boundary_discussion": post.get("boundary_discussion"),
        "primary_boundary_type": post.get("primary_boundary_type"),
        "uncertainty_note": post.get("uncertainty_note"),
        "ai_tools_json": post.get("ai_tools_json"),
        "risk_themes_json": post.get("risk_themes_json"),
        "benefit_themes_json": post.get("benefit_themes_json"),
        "notes": post.get("notes"),
    }


def _stable_comment_row(comment: dict[str, Any], post: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "comment",
        "record_id": comment["comment_id"],
        "comment_id": comment["comment_id"],
        "post_id": comment.get("post_id"),
        "comment_date": comment.get("comment_date"),
        "comment_text": comment.get("comment_text"),
        "stance": comment.get("stance"),
        "legitimacy_basis": comment.get("legitimacy_basis"),
        "workflow_domain": comment.get("workflow_domain"),
        "workflow_stage": comment.get("workflow_stage"),
        "primary_legitimacy_code": comment.get("primary_legitimacy_code"),
        "has_legitimacy_evaluation": comment.get("has_legitimacy_evaluation"),
        "boundary_discussion": comment.get("boundary_discussion"),
        "primary_boundary_type": comment.get("primary_boundary_type"),
        "uncertainty_note": comment.get("uncertainty_note"),
        "benefit_themes_json": comment.get("benefit_themes_json"),
        "is_reply": comment.get("is_reply"),
        "post_sample_status": post.get("sample_status"),
        "post_actor_type": post.get("actor_type"),
        "post_workflow_domain": post.get("workflow_domain"),
        "post_workflow_stage": post.get("workflow_stage"),
        "post_title": post.get("title"),
        "post_text": post.get("content_text"),
    }


def _priority_bucket(
    row: dict[str, Any],
    *,
    suggestion: dict[str, Any] | None,
) -> str:
    current_status = str(row.get("sample_status") or "").strip()
    current_actor = str(row.get("actor_type") or "").strip()
    suggested_status = str(suggestion.get("sample_status") or "").strip() if suggestion else ""
    if current_status == "review_needed":
        return "current_review_needed"
    if suggested_status and suggested_status != current_status:
        return "deepseek_conflict"
    if current_status == "true" and current_actor == "tool_vendor_or_promotional":
        return "historical_true_vendor"
    return "remaining_posts"


def _build_post_rows(
    connection,
    *,
    phase: str,
    suggestions_dir: Path = REBASELINE_SUGGESTIONS_DIR,
) -> list[dict[str, Any]]:
    suggestion_index = _load_suggestion_index(suggestions_dir)
    rescreen_index = load_reviewed_payloads(
        connection,
        review_phase="rescreen_posts",
        record_type="post",
    )
    rows: list[dict[str, Any]] = []
    for post in connection.execute("SELECT * FROM posts ORDER BY post_date, post_id").fetchall():
        payload = _stable_post_row(dict(post))
        payload["historical_rescreen"] = rescreen_index.get(str(post["post_id"]))
        if phase == "post_review_v2":
            suggestion = suggestion_index.get(str(post["post_id"]))
            payload["deepseek_suggestion"] = suggestion
            payload["priority_bucket"] = _priority_bucket(payload, suggestion=suggestion)
            if suggestion:
                payload["deepseek_suggested_sample_status"] = suggestion.get("sample_status")
                payload["deepseek_suggested_actor_type"] = suggestion.get("actor_type")
                payload["deepseek_suggested_reason"] = suggestion.get("ai_review_reason")
                payload["deepseek_suggested_confidence"] = suggestion.get("ai_confidence")
        rows.append(payload)
    return rows


def _build_comment_rows(connection, *, phase: str) -> list[dict[str, Any]]:
    included_post_ids: set[str] | None = None
    if phase == "comment_review_v2":
        reviewed_post_payloads = load_reviewed_payloads(
            connection,
            review_phase="post_review_v2",
            record_type="post",
        )
        included_post_ids = {
            post_id
            for post_id, payload in reviewed_post_payloads.items()
            if str(
                coalesce_mapping_value(
                    payload,
                    "inclusion_decision",
                    "是否纳入",
                    default="",
                )
            ).strip()
            == "纳入"
        }
        if not included_post_ids:
            return []
    posts = {
        str(row["post_id"]): dict(row)
        for row in connection.execute("SELECT * FROM posts").fetchall()
    }
    rows: list[dict[str, Any]] = []
    for comment in connection.execute(
        "SELECT * FROM comments ORDER BY comment_date, comment_id"
    ).fetchall():
        post = posts.get(str(comment["post_id"]))
        if post is None:
            continue
        if included_post_ids is not None:
            if str(comment["post_id"]) not in included_post_ids:
                continue
        elif str(post.get("sample_status") or "").strip() != "true":
            continue
        payload = _stable_comment_row(dict(comment), post)
        if phase == "comment_review_v2":
            payload["historical_rescreen"] = {
                "post_sample_status": post.get("sample_status"),
                "post_actor_type": post.get("actor_type"),
            }
        rows.append(payload)
    return rows


def _rows_for_phase(
    connection,
    *,
    phase: str,
    suggestions_dir: Path = REBASELINE_SUGGESTIONS_DIR,
) -> list[dict[str, Any]]:
    if phase in {"rescreen_posts", "post_review", "post_review_v2"}:
        return _build_post_rows(
            connection,
            phase=phase,
            suggestions_dir=suggestions_dir,
        )
    if phase in {"comment_review", "comment_review_v2"}:
        return _build_comment_rows(connection, phase=phase)
    valid_phases = ", ".join(REVIEW_PHASES)
    raise ValueError(f"Unknown review phase: {phase}. Expected one of: {valid_phases}")
