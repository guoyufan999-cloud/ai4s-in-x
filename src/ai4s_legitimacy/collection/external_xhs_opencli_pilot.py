from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.external_xhs_coding import (
    CODER_VERSION as CODER_VERSION,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    TASK_BATCH_ID as TASK_BATCH_ID,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_basis_codes as _choose_basis_codes,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_boundary_codes as _choose_boundary_codes,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_boundary_mode_codes as _choose_boundary_mode_codes,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_legitimacy as _choose_legitimacy,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_workflow_codes as _choose_workflow_codes,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _collect_evidence as _collect_evidence,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _confidence as _confidence,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _decision_for_page as _decision_for_page,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _discursive_mode as _discursive_mode,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _format_decision_reason as _format_decision_reason,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _looks_like_generic_tool_roundup as _looks_like_generic_tool_roundup,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _make_claim_units as _make_claim_units,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _practice_status as _practice_status,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _review_points as _review_points,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _speaker_position as _speaker_position,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _target_practice_summary as _target_practice_summary,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _theme_summary as _theme_summary,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    encode_page as encode_page,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    DEFAULT_END_DATE as DEFAULT_END_DATE,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    OPENCLI_TIMEOUT_SECONDS as OPENCLI_TIMEOUT_SECONDS,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    DoctorStatus as DoctorStatus,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    PagePayload as PagePayload,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    PilotQuery as PilotQuery,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    SearchCandidate as SearchCandidate,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _build_ssl_context as _build_ssl_context,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _canonical_url as _canonical_url,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _contains_any as _contains_any,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _dedupe_url_key as _dedupe_url_key,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_date as _extract_date,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_html_title as _extract_html_title,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_json_like_field as _extract_json_like_field,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_meta as _extract_meta,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_note_id as _extract_note_id,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_structured_note_fields as _extract_structured_note_fields,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_xhs_body_text as _extract_xhs_body_text,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _fetch_public_note_direct as _fetch_public_note_direct,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _load_existing_post_urls as _load_existing_post_urls,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _normalize_date as _normalize_date,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _normalize_space as _normalize_space,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _normalize_timestamp as _normalize_timestamp,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _parse_doctor_output as _parse_doctor_output,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _parse_search_author_and_date as _parse_search_author_and_date,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _run_opencli as _run_opencli,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _search_with_bing as _search_with_bing,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _search_with_opencli as _search_with_opencli,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _sentence_for_keywords as _sentence_for_keywords,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _sha1 as _sha1,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _split_sentences as _split_sentences,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _strip_html as _strip_html,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _unescape_xhs_text as _unescape_xhs_text,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    build_fixed_queries as build_fixed_queries,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    check_opencli_prerequisite as check_opencli_prerequisite,
)
from ai4s_legitimacy.config.settings import LEGACY_QUERY_TEMPLATE, OUTPUTS_DIR, RESEARCH_DB_PATH

DEFAULT_OUTPUT_PATH = OUTPUTS_DIR / "tables" / "external_xhs_ai4s_2025plus_pilot100.jsonl"
DEFAULT_SUMMARY_PATH = (
    OUTPUTS_DIR / "reports" / "review_v2" / "external_xhs_ai4s_2025plus_pilot100.summary.json"
)
DEFAULT_START_DATE = date(2025, 1, 1)
DEFAULT_MAX_CODED = 100
DEFAULT_MIN_INCLUDED = 50
DEFAULT_MAX_VERIFIED = 140
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_PER_QUERY_CAP = 6
DEFAULT_PER_AUTHOR_CAP = 2


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _decision_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "included": sum(1 for row in rows if row.get("decision") == "纳入"),
        "review_needed": sum(1 for row in rows if row.get("decision") == "待复核"),
        "excluded": sum(1 for row in rows if row.get("decision") == "剔除"),
    }


def _read_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _artifact_classification(*, output_preserved: bool, new_row_count: int) -> dict[str, Any]:
    if output_preserved and new_row_count == 0:
        return {
            "status": "diagnostic_failed_run_preserved_output",
            "formal_evidence_chain": False,
            "quality_v5_formal_scope": False,
            "reason": (
                "This run harvested no new rows and preserved an existing non-empty JSONL; "
                "keep it for diagnostics only, not paper_scope_quality_v5 evidence."
            ),
        }
    return {
        "status": "external_pilot_exploratory",
        "formal_evidence_chain": False,
        "quality_v5_formal_scope": False,
        "reason": (
            "External XHS pilot outputs are exploratory review_v2 artifacts and are not part "
            "of the quality_v5 post-only formal evidence chain."
        ),
    }


def _load_query_template_metadata() -> dict[str, Any]:
    if not LEGACY_QUERY_TEMPLATE.exists():
        return {}
    try:
        payload = json.loads(LEGACY_QUERY_TEMPLATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload.get("metadata", {})


def run_external_xhs_pilot(
    *,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    db_path: Path = RESEARCH_DB_PATH,
    max_coded: int = DEFAULT_MAX_CODED,
    min_included: int = DEFAULT_MIN_INCLUDED,
    max_verified: int = DEFAULT_MAX_VERIFIED,
    search_limit: int = DEFAULT_SEARCH_LIMIT,
    per_query_cap: int = DEFAULT_PER_QUERY_CAP,
    per_author_cap: int = DEFAULT_PER_AUTHOR_CAP,
    start_date: date = DEFAULT_START_DATE,
    end_date: date = DEFAULT_END_DATE,
    max_queries: int | None = None,
) -> tuple[Path, Path]:
    doctor_status = check_opencli_prerequisite()
    query_template_metadata = _load_query_template_metadata()
    queries = build_fixed_queries()
    if max_queries is not None:
        queries = queries[: max(0, int(max_queries))]
    existing_urls = _load_existing_post_urls(db_path)

    provider_name = "opencli_xiaohongshu" if doctor_status.extension_connected else "bing_fallback"
    candidates_seen: set[str] = set()
    title_hash_seen: set[str] = set()
    author_counts: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    query_stats: list[dict[str, Any]] = []
    verified_count = 0
    included_count = 0

    for query in queries:
        if len(rows) >= max_coded and included_count >= min_included:
            break
        if verified_count >= max_verified:
            break

        if doctor_status.extension_connected:
            try:
                search_results = _search_with_opencli(query, limit=search_limit)
            except Exception as exc:  # pragma: no cover - runtime integration branch
                search_results = []
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
        else:
            try:
                search_results = _search_with_bing(query, limit=search_limit)
            except Exception as exc:
                search_results = []
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
            if retained_this_query >= per_query_cap:
                break
            if len(rows) >= max_coded and included_count >= min_included:
                break
            if verified_count >= max_verified:
                break
            fetch_url = _canonical_url(candidate.url)
            dedupe_key = _dedupe_url_key(fetch_url)
            if not fetch_url or dedupe_key in existing_urls or dedupe_key in candidates_seen:
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

            row = encode_page(page=page, candidate=candidate, end_date=end_date)
            rows.append(row)
            candidates_seen.add(dedupe_key)
            title_hash_seen.add(title_hash)
            verified_count += 1
            verified_this_query += 1
            retained_this_query += 1
            if row["decision"] == "纳入":
                included_count += 1
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

    rows.sort(key=lambda item: (item["created_at"] or "9999-99-99", item["post_id"]))
    output_preserved = False
    output_rows = rows
    if rows or not output_path.exists() or output_path.stat().st_size == 0:
        _write_jsonl(output_path, rows)
    else:
        output_preserved = True
        output_rows = _read_jsonl_rows(output_path)
    output_row_count = len(output_rows)
    row_decision_counts = _decision_counts(rows)
    output_decision_counts = _decision_counts(output_rows)

    summary = {
        "task_batch_id": TASK_BATCH_ID,
        "coder_version": CODER_VERSION,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "opencli_doctor": {
            "daemon_running": doctor_status.daemon_running,
            "extension_connected": doctor_status.extension_connected,
            "connectivity_ok": doctor_status.connectivity_ok,
            "raw_output": doctor_status.raw_output,
        },
        "provider_used": provider_name,
        "fallback_used": not doctor_status.extension_connected,
        "query_template_metadata": query_template_metadata,
        "query_count": len(queries),
        "max_coded_target": max_coded,
        "min_included_target": min_included,
        "max_verified_limit": max_verified,
        "row_count": len(rows),
        "output_row_count": output_row_count,
        "included_count": included_count,
        "review_needed_count": row_decision_counts["review_needed"],
        "excluded_count": row_decision_counts["excluded"],
        "output_included_count": output_decision_counts["included"],
        "output_review_needed_count": output_decision_counts["review_needed"],
        "output_excluded_count": output_decision_counts["excluded"],
        "query_stats": query_stats,
        "limitations": (
            [
                "OpenCLI Browser Bridge was not connected; the run fell back to Bing discovery plus direct public-note fetch.",
            ]
            if not doctor_status.extension_connected
            else []
        ),
        "artifact_classification": _artifact_classification(
            output_preserved=output_preserved,
            new_row_count=len(rows),
        ),
        "output_preserved": output_preserved,
        "output_path": str(output_path),
    }
    if output_preserved:
        summary["preserved_existing_row_count"] = output_row_count
        summary["preserved_existing_decision_counts"] = output_decision_counts
        summary["limitations"].append(
            "No rows were harvested in this run; existing non-empty JSONL output was preserved."
        )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path, summary_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Harvest and code a strict JSONL pilot corpus for external Xiaohongshu AI4S posts."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--max-coded", type=int, default=DEFAULT_MAX_CODED)
    parser.add_argument("--min-included", type=int, default=DEFAULT_MIN_INCLUDED)
    parser.add_argument("--max-verified", type=int, default=DEFAULT_MAX_VERIFIED)
    parser.add_argument("--search-limit", type=int, default=DEFAULT_SEARCH_LIMIT)
    parser.add_argument("--per-query-cap", type=int, default=DEFAULT_PER_QUERY_CAP)
    parser.add_argument("--per-author-cap", type=int, default=DEFAULT_PER_AUTHOR_CAP)
    parser.add_argument("--start-date", type=str, default=str(DEFAULT_START_DATE))
    parser.add_argument("--end-date", type=str, default=str(DEFAULT_END_DATE))
    parser.add_argument("--max-queries", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    output_path, summary_path = run_external_xhs_pilot(
        output_path=args.output,
        summary_path=args.summary,
        db_path=args.db,
        max_coded=args.max_coded,
        min_included=args.min_included,
        max_verified=args.max_verified,
        search_limit=args.search_limit,
        per_query_cap=args.per_query_cap,
        per_author_cap=args.per_author_cap,
        start_date=start_date,
        end_date=end_date,
        max_queries=args.max_queries,
    )
    print(output_path)
    print(summary_path, file=sys.stderr)


if __name__ == "__main__":
    main()
