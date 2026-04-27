from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.formal_baseline import (
    ACTIVE_FORMAL_SCOPE_COMMENTS_KEY,
    ACTIVE_FORMAL_SCOPE_POSTS_KEY,
    ACTIVE_FORMAL_SUMMARY_KEY,
    paper_quality_view,
    paper_scope_view,
)


PAPER_QUALITY_V4_DISTRIBUTION_QUERIES: dict[str, str] = {
    "monthly_posts_by_workflow": f"""
        SELECT period_month, workflow_stage, post_count
        FROM {paper_quality_view("posts_by_month_workflow")}
        ORDER BY period_month, workflow_stage
    """,
    "subject_distribution": f"""
        SELECT subject_label, post_count
        FROM {paper_quality_view("subject_distribution")}
        ORDER BY post_count DESC, subject_label
    """,
    "workflow_distribution": f"""
        SELECT workflow_stage, post_count
        FROM {paper_quality_view("workflow_distribution")}
        ORDER BY post_count DESC, workflow_stage
    """,
    "comment_stance_distribution": f"""
        SELECT stance AS label, COUNT(*) AS comment_count
        FROM {paper_scope_view("comments")}
        GROUP BY stance
        ORDER BY comment_count DESC, label
    """,
    "comment_stance_by_month": f"""
        SELECT period_month, stance, comment_count
        FROM {paper_quality_view("comments_by_month_stance")}
        ORDER BY period_month, stance
    """,
}

PAPER_QUALITY_V4_CROSS_TAB_QUERIES: dict[str, str] = {
    "workflow_legitimacy": f"""
        SELECT workflow_stage, legitimacy_stance, post_count
        FROM {paper_quality_view("workflow_legitimacy_cross")}
        ORDER BY workflow_stage, legitimacy_stance
    """,
    "subject_workflow": f"""
        SELECT subject_label, workflow_stage, post_count
        FROM {paper_quality_view("subject_workflow_cross")}
        ORDER BY post_count DESC, subject_label, workflow_stage
    """,
    "subject_legitimacy": f"""
        SELECT subject_label, legitimacy_stance, post_count
        FROM {paper_quality_view("subject_legitimacy_cross")}
        ORDER BY post_count DESC, subject_label, legitimacy_stance
    """,
    "boundary_negotiation": f"""
        SELECT boundary_negotiation_code, coded_count
        FROM {paper_quality_view("boundary_negotiation_summary")}
        ORDER BY coded_count DESC, boundary_negotiation_code
    """,
    "comment_legitimacy_basis": f"""
        SELECT legitimacy_basis, comment_count
        FROM {paper_quality_view("comment_legitimacy_basis_distribution")}
        ORDER BY comment_count DESC, legitimacy_basis
    """,
    "halfyear_workflow": f"""
        SELECT half_year, workflow_stage, post_count
        FROM {paper_quality_view("halfyear_workflow")}
        ORDER BY half_year, workflow_stage
    """,
    "halfyear_subject": f"""
        SELECT half_year, subject_label, post_count
        FROM {paper_quality_view("halfyear_subject")}
        ORDER BY half_year, subject_label
    """,
}

RESEARCH_DB_COUNT_QUERIES: dict[str, str] = {
    "posts": "SELECT COUNT(*) AS c FROM posts",
    "comments": "SELECT COUNT(*) AS c FROM comments",
    "codes": "SELECT COUNT(*) AS c FROM codes",
    "codebook_rows": "SELECT COUNT(*) AS c FROM codebook",
}


def _rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _fetch_dict_rows(
    connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    return _rows_to_dicts(connection.execute(sql, params).fetchall())


def _fetch_named_query_group(
    connection,
    queries: dict[str, str],
) -> dict[str, list[dict[str, Any]]]:
    return {
        name: _fetch_dict_rows(connection, sql)
        for name, sql in queries.items()
    }


def _fetch_scalar_int(
    connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> int:
    row = connection.execute(sql, params).fetchone()
    if row is None:
        return 0
    return int(row["c"] or 0)


def _summarize_scope_counts(connection) -> dict[str, int]:
    return {
        str(row["scope_name"]): int(row["row_count"] or 0)
        for row in connection.execute(
            "SELECT scope_name, row_count FROM vw_scope_counts ORDER BY scope_name"
        ).fetchall()
    }


def _summarize_paper_quality_v4_cross_tabs(connection) -> dict[str, Any]:
    return _fetch_named_query_group(connection, PAPER_QUALITY_V4_CROSS_TAB_QUERIES)


def _summarize_paper_quality_v4_distributions(connection) -> dict[str, list[dict[str, Any]]]:
    return _fetch_named_query_group(connection, PAPER_QUALITY_V4_DISTRIBUTION_QUERIES)


def _build_paper_quality_v4_payload(
    *,
    scope_counts: dict[str, int],
    coverage_end_date: str,
    distributions: dict[str, list[dict[str, Any]]],
    cross_tabs: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    return {
        "scope_counts": scope_counts,
        "formal_posts": int(scope_counts.get(ACTIVE_FORMAL_SCOPE_POSTS_KEY, 0)),
        "formal_comments": int(scope_counts.get(ACTIVE_FORMAL_SCOPE_COMMENTS_KEY, 0)),
        "coverage_end_date": coverage_end_date,
        "monthly_posts_by_workflow": distributions["monthly_posts_by_workflow"],
        "subject_distribution": distributions["subject_distribution"],
        "workflow_distribution": distributions["workflow_distribution"],
        "comment_stance_distribution": distributions["comment_stance_distribution"],
        "comment_stance_by_month": distributions["comment_stance_by_month"],
        "cross_tabs": cross_tabs,
    }


def _summarize_paper_quality_v4(
    connection,
    *,
    scope_counts: dict[str, int],
    coverage_end_date: str,
) -> dict[str, Any]:
    distributions = _summarize_paper_quality_v4_distributions(connection)
    cross_tabs = _summarize_paper_quality_v4_cross_tabs(connection)
    return _build_paper_quality_v4_payload(
        scope_counts=scope_counts,
        coverage_end_date=coverage_end_date,
        distributions=distributions,
        cross_tabs=cross_tabs,
    )


def _summarize_research_db(
    connection,
    *,
    scope_counts: dict[str, int],
) -> dict[str, Any]:
    counts = {
        name: _fetch_scalar_int(connection, sql)
        for name, sql in RESEARCH_DB_COUNT_QUERIES.items()
    }
    sample_status_rows = {
        str(row["sample_status"]): int(row["count"] or 0)
        for row in connection.execute(
            "SELECT sample_status, COUNT(*) AS count FROM posts GROUP BY sample_status ORDER BY sample_status"
        ).fetchall()
    }
    return {
        "posts": counts["posts"],
        "comments": counts["comments"],
        "codes": counts["codes"],
        "codebook_rows": counts["codebook_rows"],
        "sample_status": sample_status_rows,
        "scope_counts": scope_counts,
    }


def _resolve_summary_context(connection, *, resolve_coverage_end_date) -> tuple[dict[str, int], str]:
    scope_counts = _summarize_scope_counts(connection)
    return scope_counts, resolve_coverage_end_date(connection)


def _build_summary_payload_from_connection(
    connection,
    *,
    resolve_coverage_end_date,
) -> dict[str, Any]:
    scope_counts, coverage_end_date = _resolve_summary_context(
        connection,
        resolve_coverage_end_date=resolve_coverage_end_date,
    )
    return {
        "research_db": _summarize_research_db(connection, scope_counts=scope_counts),
        ACTIVE_FORMAL_SUMMARY_KEY: _summarize_paper_quality_v4(
            connection,
            scope_counts=scope_counts,
            coverage_end_date=coverage_end_date,
        ),
    }


def write_summary_payload(payload: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
