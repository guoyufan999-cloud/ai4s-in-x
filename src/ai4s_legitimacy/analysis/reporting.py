from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai4s_legitimacy.analysis.figures.config import resolve_paper_scope_coverage_end_date
from ai4s_legitimacy.config.settings import RESEARCH_DB_PATH, RESEARCH_DB_SUMMARY_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly


PAPER_QUALITY_V4_DISTRIBUTION_QUERIES: dict[str, str] = {
    "monthly_posts_by_workflow": """
        SELECT period_month, workflow_stage, post_count
        FROM vw_paper_quality_v4_posts_by_month_workflow
        ORDER BY period_month, workflow_stage
    """,
    "subject_distribution": """
        SELECT subject_label, post_count
        FROM vw_paper_quality_v4_subject_distribution
        ORDER BY post_count DESC, subject_label
    """,
    "workflow_distribution": """
        SELECT workflow_stage, post_count
        FROM vw_paper_quality_v4_workflow_distribution
        ORDER BY post_count DESC, workflow_stage
    """,
    "comment_stance_distribution": """
        SELECT stance AS label, COUNT(*) AS comment_count
        FROM vw_comments_paper_scope_quality_v4
        GROUP BY stance
        ORDER BY comment_count DESC, label
    """,
    "comment_stance_by_month": """
        SELECT period_month, stance, comment_count
        FROM vw_paper_quality_v4_comments_by_month_stance
        ORDER BY period_month, stance
    """,
}

PAPER_QUALITY_V4_CROSS_TAB_QUERIES: dict[str, str] = {
    "workflow_legitimacy": """
        SELECT workflow_stage, legitimacy_stance, post_count
        FROM vw_paper_quality_v4_workflow_legitimacy_cross
        ORDER BY workflow_stage, legitimacy_stance
    """,
    "subject_workflow": """
        SELECT subject_label, workflow_stage, post_count
        FROM vw_paper_quality_v4_subject_workflow_cross
        ORDER BY post_count DESC, subject_label, workflow_stage
    """,
    "subject_legitimacy": """
        SELECT subject_label, legitimacy_stance, post_count
        FROM vw_paper_quality_v4_subject_legitimacy_cross
        ORDER BY post_count DESC, subject_label, legitimacy_stance
    """,
    "boundary_negotiation": """
        SELECT boundary_negotiation_code, coded_count
        FROM vw_paper_quality_v4_boundary_negotiation_summary
        ORDER BY coded_count DESC, boundary_negotiation_code
    """,
    "comment_legitimacy_basis": """
        SELECT legitimacy_basis, comment_count
        FROM vw_paper_quality_v4_comment_legitimacy_basis_distribution
        ORDER BY comment_count DESC, legitimacy_basis
    """,
    "halfyear_workflow": """
        SELECT half_year, workflow_stage, post_count
        FROM vw_paper_quality_v4_halfyear_workflow
        ORDER BY half_year, workflow_stage
    """,
    "halfyear_subject": """
        SELECT half_year, subject_label, post_count
        FROM vw_paper_quality_v4_halfyear_subject
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
        "formal_posts": int(scope_counts.get("paper_quality_v4_posts", 0)),
        "formal_comments": int(scope_counts.get("paper_quality_v4_comments", 0)),
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


def _resolve_summary_context(connection) -> tuple[dict[str, int], str]:
    scope_counts = _summarize_scope_counts(connection)
    return scope_counts, resolve_paper_scope_coverage_end_date(connection)


def _build_summary_payload_from_connection(connection) -> dict[str, Any]:
    scope_counts, coverage_end_date = _resolve_summary_context(connection)
    return {
        "research_db": _summarize_research_db(connection, scope_counts=scope_counts),
        "paper_quality_v4": _summarize_paper_quality_v4(
            connection,
            scope_counts=scope_counts,
            coverage_end_date=coverage_end_date,
        ),
    }


def summarize_scope_counts(db_path: Path = RESEARCH_DB_PATH) -> dict[str, int]:
    with connect_sqlite_readonly(db_path) as connection:
        return _summarize_scope_counts(connection)


def summarize_paper_quality_v4_cross_tabs(db_path: Path = RESEARCH_DB_PATH) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        return _summarize_paper_quality_v4_cross_tabs(connection)


def summarize_paper_quality_v4(db_path: Path = RESEARCH_DB_PATH) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        scope_counts, coverage_end_date = _resolve_summary_context(connection)
        return _summarize_paper_quality_v4(
            connection,
            scope_counts=scope_counts,
            coverage_end_date=coverage_end_date,
        )


def summarize_research_db(db_path: Path = RESEARCH_DB_PATH) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        scope_counts = _summarize_scope_counts(connection)
        return _summarize_research_db(connection, scope_counts=scope_counts)


def build_summary_payload(db_path: Path = RESEARCH_DB_PATH) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        return _build_summary_payload_from_connection(connection)


def write_summary_payload(payload: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def export_summary_json(
    db_path: Path = RESEARCH_DB_PATH,
    output_path: Path | None = None,
) -> Path:
    output = output_path or RESEARCH_DB_SUMMARY_PATH
    return write_summary_payload(build_summary_payload(db_path=db_path), output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export research DB summary JSON.")
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--output", type=Path, default=RESEARCH_DB_SUMMARY_PATH)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(export_summary_json(db_path=args.db, output_path=args.output))


if __name__ == "__main__":
    main()
