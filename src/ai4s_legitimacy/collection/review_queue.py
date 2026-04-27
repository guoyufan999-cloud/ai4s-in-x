from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.formal_baseline import (
    REBASELINE_REVIEW_QUEUE_DIR,
    REBASELINE_STAGING_DB_PATH,
    REBASELINE_SUGGESTIONS_DIR,
)
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

from ._canonical_review import canonicalize_review_row
from ._review_db import coalesce_mapping_value, load_reviewed_payloads


REVIEW_PHASES = (
    "rescreen_posts",
    "post_review",
    "post_review_v2",
    "comment_review",
    "comment_review_v2",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _latest_suggestion_file(
    suggestions_dir: Path = REBASELINE_SUGGESTIONS_DIR,
) -> Path | None:
    if not suggestions_dir.exists():
        return None
    candidates = [
        path
        for path in suggestions_dir.rglob("*.full_draft.jsonl")
        if "/shards/" not in str(path)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, str(path)))[-1]


def _load_suggestion_index(
    suggestions_dir: Path = REBASELINE_SUGGESTIONS_DIR,
) -> dict[str, dict[str, Any]]:
    suggestion_file = _latest_suggestion_file(suggestions_dir)
    if suggestion_file is None:
        return {}
    index: dict[str, dict[str, Any]] = {}
    for row in _load_jsonl(suggestion_file):
        post_id = str(row.get("post_id") or row.get("record_id") or "").strip()
        if post_id:
            index[post_id] = row
    return index


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


def _default_output_path(phase: str) -> Path:
    return REBASELINE_REVIEW_QUEUE_DIR / f"{phase}.jsonl"


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export JSONL review queues from the quality_v5 rebaseline staging DB."
    )
    parser.add_argument("--db", type=Path, default=REBASELINE_STAGING_DB_PATH)
    parser.add_argument("--phase", choices=sorted(REVIEW_PHASES), required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--suggestions-dir", type=Path, default=REBASELINE_SUGGESTIONS_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(
        export_review_queue(
            db_path=args.db,
            phase=args.phase,
            output_path=args.output,
            limit=args.limit,
            suggestions_dir=args.suggestions_dir,
        )
    )


if __name__ == "__main__":
    main()
