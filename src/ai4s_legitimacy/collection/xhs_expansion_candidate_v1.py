from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.external_xhs_coding import encode_page
from ai4s_legitimacy.collection.external_xhs_runtime import (
    DEFAULT_END_DATE,
    DoctorStatus,
    PagePayload,
    SearchCandidate,
    _canonical_url,
    _dedupe_url_key,
    _extract_note_id,
    _fetch_public_note_direct,
    _load_existing_post_urls,
    _run_opencli,
    _search_with_bing,
    _search_with_opencli,
    _sha1,
    build_fixed_queries,
    check_opencli_prerequisite,
)
from ai4s_legitimacy.config.formal_baseline import ACTIVE_FORMAL_STAGE
from ai4s_legitimacy.config.settings import INTERIM_DIR, OUTPUTS_DIR, RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

TASK_BATCH_ID = "xhs_expansion_candidate_v1"
CODER_VERSION = "codex_xhs_expansion_candidate_v1"
PHASE = "xhs_expansion_candidate_v1"

DEFAULT_OUTPUT_DIR = OUTPUTS_DIR / "tables" / PHASE
DEFAULT_POST_OUTPUT_PATH = DEFAULT_OUTPUT_DIR / "posts.jsonl"
DEFAULT_COMMENT_OUTPUT_PATH = DEFAULT_OUTPUT_DIR / "comments.jsonl"
DEFAULT_SUMMARY_PATH = OUTPUTS_DIR / "reports" / "review_v2" / f"{PHASE}.summary.json"
DEFAULT_REVIEW_QUEUE_DIR = INTERIM_DIR / PHASE / "review_queues"
DEFAULT_BATCH_SIZE = 100
DEFAULT_REVIEWER = "guoyufan"
DEFAULT_START_DATE = date(2024, 1, 1)
DEFAULT_MAX_CODED = 500
DEFAULT_MAX_VERIFIED = 700
DEFAULT_SEARCH_LIMIT = 30
DEFAULT_PER_QUERY_CAP = 20
DEFAULT_PER_AUTHOR_CAP = 3
DEFAULT_MAX_COMMENT_PROBES = 25
COMMENT_MODE_BROWSER_SESSION = "browser-session"
COMMENT_MODE_OFF = "off"
PUBLIC_PAGE_CHROME_MARKERS = (
    "创作中心 业务合作 发现 直播 发布 通知",
    "window.__INITIAL_STATE__",
    "window.__SSR__",
    "沪ICP备",
    "营业执照",
)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _artifact_classification() -> dict[str, Any]:
    return {
        "status": "xhs_expansion_candidate_v1",
        "formal_evidence_chain": False,
        "quality_v5_formal_scope": False,
        "reason": (
            "xhs_expansion_candidate_v1 outputs are exploratory artifacts. They are not imported into "
            "quality_v5 post-only formal results."
        ),
    }


def _strip_public_page_chrome(text: str) -> str:
    cleaned = str(text or "").strip()
    for marker in PUBLIC_PAGE_CHROME_MARKERS:
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].strip()
    for suffix in (" - 小红书", "_小红书"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
    return cleaned


def _prepare_candidate_page(page: PagePayload) -> PagePayload:
    page.source_text = _strip_public_page_chrome(page.source_text)
    page.raw_excerpt = _strip_public_page_chrome(page.raw_excerpt)
    return page


def _formal_guard_counts(db_path: Path) -> dict[str, int]:
    if not db_path.exists():
        return {
            f"paper_{ACTIVE_FORMAL_STAGE}_posts": 0,
            f"paper_{ACTIVE_FORMAL_STAGE}_comments": 0,
        }
    try:
        with connect_sqlite_readonly(db_path) as connection:
            return {
                str(row["scope_name"]): int(row["row_count"] or 0)
                for row in connection.execute(
                    """
                    SELECT scope_name, row_count
                    FROM vw_scope_counts
                    WHERE scope_name IN (?, ?)
                    ORDER BY scope_name
                    """,
                    (
                        f"paper_{ACTIVE_FORMAL_STAGE}_posts",
                        f"paper_{ACTIVE_FORMAL_STAGE}_comments",
                    ),
                ).fetchall()
            }
    except Exception:
        return {
            f"paper_{ACTIVE_FORMAL_STAGE}_posts": 0,
            f"paper_{ACTIVE_FORMAL_STAGE}_comments": 0,
        }


def _load_existing_post_keys(db_path: Path) -> set[str]:
    keys = set(_load_existing_post_urls(db_path))
    if not db_path.exists():
        return keys
    with connect_sqlite_readonly(db_path) as connection:
        for row in connection.execute(
            """
            SELECT post_id, legacy_note_id, post_url
            FROM posts
            """
        ).fetchall():
            post_id = str(row["post_id"] or "").strip()
            legacy_note_id = str(row["legacy_note_id"] or "").strip()
            post_url = str(row["post_url"] or "").strip()
            if post_id:
                keys.add(f"xiaohongshu:{post_id}")
            if legacy_note_id:
                keys.add(f"xiaohongshu:{legacy_note_id}")
            if post_url:
                keys.add(_dedupe_url_key(post_url))
    return keys


def _post_key(row: dict[str, Any]) -> str:
    url = str(row.get("post_url") or row.get("url") or "").strip()
    post_id = str(row.get("post_id") or row.get("record_id") or "").strip()
    if url:
        return _dedupe_url_key(url)
    if post_id:
        return f"xiaohongshu:{post_id}"
    return ""


def _comment_status_row(
    *,
    page: PagePayload,
    candidate: SearchCandidate,
    status: str,
    source_strategy: str,
    note: str = "",
) -> dict[str, Any]:
    parent_post_id = page.note_id or _extract_note_id(page.url)
    return {
        "record_type": "comment_fetch_status",
        "comment_id": f"{parent_post_id}:comment_fetch:{status}",
        "comment_text": "",
        "parent_post_id": parent_post_id,
        "parent_post_url": page.url,
        "parent_query_name": candidate.query_name,
        "parent_query_text": candidate.query_text,
        "comment_fetch_status": status,
        "source_strategy": source_strategy,
        "formal_result_scope": False,
        "review_status": "unreviewed",
        "note": note,
    }


def _iter_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _iter_dicts(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_dicts(item)


def _comment_text_from_dict(row: dict[str, Any]) -> str:
    for key in ("comment_text", "commentText", "content", "text", "desc"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _comment_id_from_dict(row: dict[str, Any], *, parent_post_id: str, index: int) -> str:
    for key in ("comment_id", "commentId", "id"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return f"{parent_post_id}:comment:{index:04d}"


def _parse_comment_sidecar_rows(
    payload: Any,
    *,
    page: PagePayload,
    candidate: SearchCandidate,
    source_strategy: str,
) -> list[dict[str, Any]]:
    parent_post_id = page.note_id or _extract_note_id(page.url)
    rows: list[dict[str, Any]] = []
    seen_texts: set[str] = set()
    for item in _iter_dicts(payload):
        text = _comment_text_from_dict(item)
        if not text or text in seen_texts:
            continue
        keys = {str(key).lower() for key in item}
        looks_like_comment = any("comment" in key for key in keys) or bool(
            {"nickname", "user", "user_id", "userid", "like_count"} & keys
        )
        if not looks_like_comment:
            continue
        seen_texts.add(text)
        rows.append(
            {
                "record_type": "comment",
                "comment_id": _comment_id_from_dict(
                    item,
                    parent_post_id=parent_post_id,
                    index=len(rows) + 1,
                ),
                "comment_text": text,
                "parent_post_id": parent_post_id,
                "parent_post_url": page.url,
                "parent_query_name": candidate.query_name,
                "parent_query_text": candidate.query_text,
                "comment_fetch_status": "ok",
                "source_strategy": source_strategy,
                "formal_result_scope": False,
                "review_status": "unreviewed",
                "raw_comment_payload": item,
            }
        )
    return rows


def _fetch_comments_with_browser_session(
    *,
    page: PagePayload,
    candidate: SearchCandidate,
    doctor_status: DoctorStatus,
) -> list[dict[str, Any]]:
    source_strategy = "opencli_browser_session_probe"
    if not doctor_status.extension_connected:
        return [
            _comment_status_row(
                page=page,
                candidate=candidate,
                status="browser_session_unavailable",
                source_strategy=source_strategy,
                note="OpenCLI browser extension is not connected.",
            )
        ]
    note_id = page.note_id or _extract_note_id(page.url)
    if not note_id:
        return [
            _comment_status_row(
                page=page,
                candidate=candidate,
                status="missing_note_id",
                source_strategy=source_strategy,
            )
        ]
    process = _run_opencli("xiaohongshu", "creator-note-detail", note_id, "-f", "json")
    if process.returncode != 0:
        return [
            _comment_status_row(
                page=page,
                candidate=candidate,
                status="comment_fetch_failed",
                source_strategy=source_strategy,
                note=(process.stderr or process.stdout or "").strip()[:500],
            )
        ]
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError:
        return [
            _comment_status_row(
                page=page,
                candidate=candidate,
                status="comment_fetch_invalid_json",
                source_strategy=source_strategy,
            )
        ]
    rows = _parse_comment_sidecar_rows(
        payload,
        page=page,
        candidate=candidate,
        source_strategy=source_strategy,
    )
    if rows:
        return rows
    return [
        _comment_status_row(
            page=page,
            candidate=candidate,
            status="no_stable_comment_source",
            source_strategy=source_strategy,
            note=(
                "The available OpenCLI Xiaohongshu commands did not expose stable public "
                "comment text for this note."
            ),
        )
    ]


def _fetch_comment_sidecar(
    *,
    page: PagePayload,
    candidate: SearchCandidate,
    doctor_status: DoctorStatus,
    comment_mode: str,
    probe_allowed: bool,
) -> list[dict[str, Any]]:
    if comment_mode == COMMENT_MODE_OFF:
        return [
            _comment_status_row(
                page=page,
                candidate=candidate,
                status="comment_fetch_disabled",
                source_strategy="disabled",
            )
        ]
    if not probe_allowed:
        return [
            _comment_status_row(
                page=page,
                candidate=candidate,
                status="comment_fetch_deferred_after_probe_limit",
                source_strategy="browser_session_probe_limited",
                note="Browser-session comment probing was deferred after the configured probe limit.",
            )
        ]
    return _fetch_comments_with_browser_session(
        page=page,
        candidate=candidate,
        doctor_status=doctor_status,
    )


def _decorate_post_row(
    row: dict[str, Any],
    *,
    comment_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses = Counter(str(item.get("comment_fetch_status") or "unknown") for item in comment_rows)
    decorated = dict(row)
    decorated["task_batch_id"] = TASK_BATCH_ID
    decorated["coder_version"] = CODER_VERSION
    decorated["source_phase"] = PHASE
    decorated["formal_result_scope"] = False
    decorated["artifact_classification"] = _artifact_classification()
    decorated["comment_sidecar_summary"] = {
        "sidecar_rows": len(comment_rows),
        "comment_rows": sum(1 for item in comment_rows if item.get("record_type") == "comment"),
        "status_counts": dict(statuses),
    }
    return decorated


def _run_id(batch_index: int) -> str:
    return f"{PHASE}_batch_{batch_index:02d}"


def _review_template_row(
    row: dict[str, Any],
    *,
    batch_index: int,
    reviewer: str,
) -> dict[str, Any]:
    template = dict(row)
    template.update(
        {
            "run_id": _run_id(batch_index),
            "review_phase": PHASE,
            "review_status": "unreviewed",
            "reviewer": reviewer,
            "review_date": "",
            "formal_result_scope": False,
            "post_expansion_reviewer_notes": [],
        }
    )
    return template


def _write_review_queue(
    *,
    rows: list[dict[str, Any]],
    queue_dir: Path,
    batch_size: int,
    reviewer: str,
) -> dict[str, Any]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_path = queue_dir / f"{PHASE}.jsonl"
    _write_jsonl(queue_path, rows)
    batch_count = math.ceil(len(rows) / batch_size) if rows else 0
    batches: list[dict[str, Any]] = []
    for batch_index in range(batch_count):
        chunk = rows[batch_index * batch_size : (batch_index + 1) * batch_size]
        batch_rows = [
            _review_template_row(row, batch_index=batch_index, reviewer=reviewer)
            for row in chunk
        ]
        batch_path = queue_dir / f"{PHASE}.batch_{batch_index:02d}.review_template.jsonl"
        _write_jsonl(batch_path, batch_rows)
        batches.append(
            {
                "batch_index": batch_index,
                "run_id": _run_id(batch_index),
                "row_count": len(batch_rows),
                "review_template_path": str(batch_path),
            }
        )
    return {
        "queue_path": str(queue_path),
        "batch_size": batch_size,
        "batch_count": batch_count,
        "batches": batches,
    }


def _decision_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "included": sum(1 for row in rows if row.get("decision") == "纳入"),
        "review_needed": sum(1 for row in rows if row.get("decision") == "待复核"),
        "excluded": sum(1 for row in rows if row.get("decision") == "剔除"),
    }


def _comment_status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("comment_fetch_status") or "unknown") for row in rows))


def run_xhs_expansion_candidate_v1(
    *,
    post_output_path: Path = DEFAULT_POST_OUTPUT_PATH,
    comment_output_path: Path = DEFAULT_COMMENT_OUTPUT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    review_queue_dir: Path = DEFAULT_REVIEW_QUEUE_DIR,
    db_path: Path = RESEARCH_DB_PATH,
    max_coded: int = DEFAULT_MAX_CODED,
    max_verified: int = DEFAULT_MAX_VERIFIED,
    search_limit: int = DEFAULT_SEARCH_LIMIT,
    per_query_cap: int = DEFAULT_PER_QUERY_CAP,
    per_author_cap: int = DEFAULT_PER_AUTHOR_CAP,
    start_date: date = DEFAULT_START_DATE,
    end_date: date = DEFAULT_END_DATE,
    max_queries: int | None = None,
    comment_mode: str = COMMENT_MODE_BROWSER_SESSION,
    max_comment_probes: int = DEFAULT_MAX_COMMENT_PROBES,
    batch_size: int = DEFAULT_BATCH_SIZE,
    reviewer: str = DEFAULT_REVIEWER,
) -> tuple[Path, Path, Path]:
    if max_coded <= 0:
        raise ValueError("max_coded must be positive")
    if max_verified <= 0:
        raise ValueError("max_verified must be positive")
    if max_comment_probes < 0:
        raise ValueError("max_comment_probes must be non-negative")
    if comment_mode not in {COMMENT_MODE_BROWSER_SESSION, COMMENT_MODE_OFF}:
        raise ValueError("comment_mode must be browser-session or off")

    doctor_status = check_opencli_prerequisite()
    queries = build_fixed_queries()
    if max_queries is not None:
        queries = queries[: max(0, int(max_queries))]

    existing_keys = _load_existing_post_keys(db_path)
    candidates_seen: set[str] = set()
    title_hash_seen: set[str] = set()
    author_counts: dict[str, int] = {}
    post_rows: list[dict[str, Any]] = []
    comment_rows: list[dict[str, Any]] = []
    query_stats: list[dict[str, Any]] = []
    verified_count = 0
    comment_probe_count = 0

    provider_name = "opencli_xiaohongshu" if doctor_status.extension_connected else "bing_fallback"
    for query in queries:
        if len(post_rows) >= max_coded or verified_count >= max_verified:
            break
        try:
            search_results = (
                _search_with_opencli(query, limit=search_limit)
                if doctor_status.extension_connected
                else _search_with_bing(query, limit=search_limit)
            )
        except Exception as exc:
            query_stats.append(
                {
                    "query": query.query,
                    "query_name": query.name,
                    "category": query.category,
                    "search_provider": provider_name,
                    "status": "search_failed",
                    "error": str(exc),
                }
            )
            continue

        retained_this_query = 0
        verified_this_query = 0
        for candidate in search_results:
            if (
                retained_this_query >= per_query_cap
                or len(post_rows) >= max_coded
                or verified_count >= max_verified
            ):
                break
            fetch_url = _canonical_url(candidate.url)
            dedupe_key = _dedupe_url_key(fetch_url)
            if not fetch_url or dedupe_key in existing_keys or dedupe_key in candidates_seen:
                continue
            author_key = _sha1(candidate.author) if candidate.author else ""
            if author_key and author_counts.get(author_key, 0) >= per_author_cap:
                continue

            try:
                page = _fetch_public_note_direct(fetch_url)
            except Exception:
                page = None
            if page is None:
                continue
            page = _prepare_candidate_page(page)
            if (not page.title or page.title.startswith("小红书_")) and candidate.title:
                page.title = candidate.title
            if not page.author_handle and candidate.author:
                page.author_handle = candidate.author
            if not page.created_at and candidate.result_date:
                page.created_at = candidate.result_date
            if page.created_at:
                try:
                    created_date = datetime.strptime(page.created_at, "%Y-%m-%d").date()
                    if created_date < start_date or created_date > end_date:
                        continue
                except ValueError:
                    pass
            title_hash = _sha1(f"{page.title}\n{page.source_text[:200]}")
            if title_hash in title_hash_seen:
                continue

            probe_allowed = (
                comment_mode == COMMENT_MODE_BROWSER_SESSION
                and comment_probe_count < max_comment_probes
            )
            sidecar_rows = _fetch_comment_sidecar(
                page=page,
                candidate=candidate,
                doctor_status=doctor_status,
                comment_mode=comment_mode,
                probe_allowed=probe_allowed,
            )
            if probe_allowed:
                comment_probe_count += 1
            row = _decorate_post_row(
                encode_page(page=page, candidate=candidate, end_date=end_date),
                comment_rows=sidecar_rows,
            )
            post_rows.append(row)
            comment_rows.extend(sidecar_rows)
            candidates_seen.add(dedupe_key)
            title_hash_seen.add(title_hash)
            verified_count += 1
            verified_this_query += 1
            retained_this_query += 1
            if author_key:
                author_counts[author_key] = author_counts.get(author_key, 0) + 1

        query_stats.append(
            {
                "query": query.query,
                "query_name": query.name,
                "category": query.category,
                "search_provider": provider_name,
                "search_hits": len(search_results),
                "verified_kept": verified_this_query,
            }
        )

    post_rows.sort(key=lambda item: (item.get("created_at") or "9999-99-99", item["post_id"]))
    _write_jsonl(post_output_path, post_rows)
    _write_jsonl(comment_output_path, comment_rows)
    review_queue = _write_review_queue(
        rows=post_rows,
        queue_dir=review_queue_dir,
        batch_size=batch_size,
        reviewer=reviewer,
    )
    formal_guard_counts = _formal_guard_counts(db_path)
    summary = {
        "task_batch_id": TASK_BATCH_ID,
        "coder_version": CODER_VERSION,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "provider_used": provider_name,
        "comment_mode": comment_mode,
        "opencli_doctor": {
            "daemon_running": doctor_status.daemon_running,
            "extension_connected": doctor_status.extension_connected,
            "connectivity_ok": doctor_status.connectivity_ok,
            "raw_output": doctor_status.raw_output,
        },
        "query_count": len(queries),
        "max_coded_target": max_coded,
        "max_verified_limit": max_verified,
        "max_comment_probes": max_comment_probes,
        "comment_probe_count": comment_probe_count,
        "post_row_count": len(post_rows),
        "comment_sidecar_row_count": len(comment_rows),
        "comment_fetch_status_counts": _comment_status_counts(comment_rows),
        "post_decision_counts": _decision_counts(post_rows),
        "query_stats": query_stats,
        "formal_baseline_guard_counts": formal_guard_counts,
        "artifact_status": PHASE,
        "artifact_classification": _artifact_classification(),
        "quality_v5_formal_scope": False,
        "formal_result_scope": False,
        "post_output_path": str(post_output_path),
        "comment_output_path": str(comment_output_path),
        "review_queue": review_queue,
        "limitations": [
            "xhs_expansion_candidate_v1 artifacts are exploratory and require manual review before any formal use.",
            "Comment sidecar rows are contextual capture attempts, not comment_review_v2 formal results.",
        ],
    }
    if comment_rows and set(summary["comment_fetch_status_counts"]) == {"no_stable_comment_source"}:
        summary["limitations"].append(
            "The browser-session probe did not expose stable comment text; status rows were retained."
        )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return post_output_path, comment_output_path, summary_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Harvest xhs_expansion_candidate_v1 rows with comment sidecar."
    )
    parser.add_argument("--posts-output", type=Path, default=DEFAULT_POST_OUTPUT_PATH)
    parser.add_argument("--comments-output", type=Path, default=DEFAULT_COMMENT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--review-queue-dir", type=Path, default=DEFAULT_REVIEW_QUEUE_DIR)
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--max-coded", type=int, default=DEFAULT_MAX_CODED)
    parser.add_argument("--max-verified", type=int, default=DEFAULT_MAX_VERIFIED)
    parser.add_argument("--search-limit", type=int, default=DEFAULT_SEARCH_LIMIT)
    parser.add_argument("--per-query-cap", type=int, default=DEFAULT_PER_QUERY_CAP)
    parser.add_argument("--per-author-cap", type=int, default=DEFAULT_PER_AUTHOR_CAP)
    parser.add_argument("--start-date", type=str, default=str(DEFAULT_START_DATE))
    parser.add_argument("--end-date", type=str, default=str(DEFAULT_END_DATE))
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument(
        "--comment-mode",
        choices=[COMMENT_MODE_BROWSER_SESSION, COMMENT_MODE_OFF],
        default=COMMENT_MODE_BROWSER_SESSION,
    )
    parser.add_argument("--max-comment-probes", type=int, default=DEFAULT_MAX_COMMENT_PROBES)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    post_output_path, comment_output_path, summary_path = run_xhs_expansion_candidate_v1(
        post_output_path=args.posts_output,
        comment_output_path=args.comments_output,
        summary_path=args.summary,
        review_queue_dir=args.review_queue_dir,
        db_path=args.db,
        max_coded=args.max_coded,
        max_verified=args.max_verified,
        search_limit=args.search_limit,
        per_query_cap=args.per_query_cap,
        per_author_cap=args.per_author_cap,
        start_date=start_date,
        end_date=end_date,
        max_queries=args.max_queries,
        comment_mode=args.comment_mode,
        max_comment_probes=args.max_comment_probes,
        batch_size=args.batch_size,
        reviewer=args.reviewer,
    )
    print(post_output_path)
    print(comment_output_path)
    print(summary_path, file=sys.stderr)


__all__ = [
    "COMMENT_MODE_BROWSER_SESSION",
    "COMMENT_MODE_OFF",
    "DEFAULT_MAX_CODED",
    "PHASE",
    "run_xhs_expansion_candidate_v1",
    "main",
]


if __name__ == "__main__":
    main()
