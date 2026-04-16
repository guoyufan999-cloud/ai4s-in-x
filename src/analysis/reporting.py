from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.analysis.figures.config import resolve_paper_scope_coverage_end_date
from src.config.settings import RESEARCH_DB_PATH, RESEARCH_DB_SUMMARY_PATH
from src.utils.db import connect_sqlite_readonly


def _rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _summarize_scope_counts(connection) -> dict[str, int]:
    return {
        str(row["scope_name"]): int(row["row_count"] or 0)
        for row in connection.execute(
            "SELECT scope_name, row_count FROM vw_scope_counts ORDER BY scope_name"
        ).fetchall()
    }


def _summarize_paper_quality_v4_cross_tabs(connection) -> dict[str, Any]:
    workflow_legitimacy = _rows_to_dicts(
        connection.execute(
            "SELECT workflow_stage, legitimacy_stance, post_count "
            "FROM vw_paper_quality_v4_workflow_legitimacy_cross "
            "ORDER BY workflow_stage, legitimacy_stance"
        ).fetchall()
    )
    subject_workflow = _rows_to_dicts(
        connection.execute(
            "SELECT subject_label, workflow_stage, post_count "
            "FROM vw_paper_quality_v4_subject_workflow_cross "
            "ORDER BY post_count DESC, subject_label, workflow_stage"
        ).fetchall()
    )
    subject_legitimacy = _rows_to_dicts(
        connection.execute(
            "SELECT subject_label, legitimacy_stance, post_count "
            "FROM vw_paper_quality_v4_subject_legitimacy_cross "
            "ORDER BY post_count DESC, subject_label, legitimacy_stance"
        ).fetchall()
    )
    boundary_negotiation = _rows_to_dicts(
        connection.execute(
            "SELECT boundary_negotiation_code, coded_count "
            "FROM vw_paper_quality_v4_boundary_negotiation_summary "
            "ORDER BY coded_count DESC, boundary_negotiation_code"
        ).fetchall()
    )
    comment_legitimacy_basis = _rows_to_dicts(
        connection.execute(
            "SELECT legitimacy_basis, comment_count "
            "FROM vw_paper_quality_v4_comment_legitimacy_basis_distribution "
            "ORDER BY comment_count DESC, legitimacy_basis"
        ).fetchall()
    )
    halfyear_workflow = _rows_to_dicts(
        connection.execute(
            "SELECT half_year, workflow_stage, post_count "
            "FROM vw_paper_quality_v4_halfyear_workflow "
            "ORDER BY half_year, workflow_stage"
        ).fetchall()
    )
    halfyear_subject = _rows_to_dicts(
        connection.execute(
            "SELECT half_year, subject_label, post_count "
            "FROM vw_paper_quality_v4_halfyear_subject "
            "ORDER BY half_year, subject_label"
        ).fetchall()
    )
    return {
        "workflow_legitimacy": workflow_legitimacy,
        "subject_workflow": subject_workflow,
        "subject_legitimacy": subject_legitimacy,
        "boundary_negotiation": boundary_negotiation,
        "comment_legitimacy_basis": comment_legitimacy_basis,
        "halfyear_workflow": halfyear_workflow,
        "halfyear_subject": halfyear_subject,
    }


def _summarize_paper_quality_v4(
    connection,
    *,
    scope_counts: dict[str, int],
    coverage_end_date: str,
) -> dict[str, Any]:
    monthly_posts = _rows_to_dicts(
        connection.execute(
            """
            SELECT period_month, workflow_stage, post_count
            FROM vw_paper_quality_v4_posts_by_month_workflow
            ORDER BY period_month, workflow_stage
            """
        ).fetchall()
    )
    subject_distribution = _rows_to_dicts(
        connection.execute(
            """
            SELECT subject_label, post_count
            FROM vw_paper_quality_v4_subject_distribution
            ORDER BY post_count DESC, subject_label
            """
        ).fetchall()
    )
    workflow_distribution = _rows_to_dicts(
        connection.execute(
            """
            SELECT workflow_stage, post_count
            FROM vw_paper_quality_v4_workflow_distribution
            ORDER BY post_count DESC, workflow_stage
            """
        ).fetchall()
    )
    comment_stance_distribution = _rows_to_dicts(
        connection.execute(
            """
            SELECT stance AS label, COUNT(*) AS comment_count
            FROM vw_comments_paper_scope_quality_v4
            GROUP BY stance
            ORDER BY comment_count DESC, label
            """
        ).fetchall()
    )
    comment_stance_by_month = _rows_to_dicts(
        connection.execute(
            """
            SELECT period_month, stance, comment_count
            FROM vw_paper_quality_v4_comments_by_month_stance
            ORDER BY period_month, stance
            """
        ).fetchall()
    )
    cross_tabs = _summarize_paper_quality_v4_cross_tabs(connection)
    return {
        "scope_counts": scope_counts,
        "formal_posts": int(scope_counts.get("paper_quality_v4_posts", 0)),
        "formal_comments": int(scope_counts.get("paper_quality_v4_comments", 0)),
        "coverage_end_date": coverage_end_date,
        "monthly_posts_by_workflow": monthly_posts,
        "subject_distribution": subject_distribution,
        "workflow_distribution": workflow_distribution,
        "comment_stance_distribution": comment_stance_distribution,
        "comment_stance_by_month": comment_stance_by_month,
        "cross_tabs": cross_tabs,
    }


def _summarize_research_db(
    connection,
    *,
    scope_counts: dict[str, int],
) -> dict[str, Any]:
    posts = int(connection.execute("SELECT COUNT(*) AS c FROM posts").fetchone()["c"])
    comments = int(connection.execute("SELECT COUNT(*) AS c FROM comments").fetchone()["c"])
    code_rows = int(connection.execute("SELECT COUNT(*) AS c FROM codes").fetchone()["c"])
    codebook_rows = int(connection.execute("SELECT COUNT(*) AS c FROM codebook").fetchone()["c"])
    sample_status_rows = {
        str(row["sample_status"]): int(row["count"] or 0)
        for row in connection.execute(
            "SELECT sample_status, COUNT(*) AS count FROM posts GROUP BY sample_status ORDER BY sample_status"
        ).fetchall()
    }
    return {
        "posts": posts,
        "comments": comments,
        "codes": code_rows,
        "codebook_rows": codebook_rows,
        "sample_status": sample_status_rows,
        "scope_counts": scope_counts,
    }


def summarize_scope_counts(db_path: Path = RESEARCH_DB_PATH) -> dict[str, int]:
    with connect_sqlite_readonly(db_path) as connection:
        return _summarize_scope_counts(connection)


def summarize_paper_quality_v4_cross_tabs(db_path: Path = RESEARCH_DB_PATH) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        return _summarize_paper_quality_v4_cross_tabs(connection)


def summarize_paper_quality_v4(db_path: Path = RESEARCH_DB_PATH) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        scope_counts = _summarize_scope_counts(connection)
        return _summarize_paper_quality_v4(
            connection,
            scope_counts=scope_counts,
            coverage_end_date=resolve_paper_scope_coverage_end_date(connection),
        )


def summarize_research_db(db_path: Path = RESEARCH_DB_PATH) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        scope_counts = _summarize_scope_counts(connection)
        return _summarize_research_db(connection, scope_counts=scope_counts)


def build_summary_payload(db_path: Path = RESEARCH_DB_PATH) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        scope_counts = _summarize_scope_counts(connection)
        coverage_end_date = resolve_paper_scope_coverage_end_date(connection)
        return {
            "research_db": _summarize_research_db(connection, scope_counts=scope_counts),
            "paper_quality_v4": _summarize_paper_quality_v4(
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
