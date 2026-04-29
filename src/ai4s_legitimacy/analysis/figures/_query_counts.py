from __future__ import annotations

import sqlite3
from typing import Any

from ai4s_legitimacy.analysis.figures.config import (
    RESEARCH_WINDOW_END,
    RESEARCH_WINDOW_START,
    month_sequence,
    rolling_mean,
)
from ai4s_legitimacy.config.formal_baseline import ACTIVE_FORMAL_STAGE, paper_scope_view

from ._query_context import PeriodContext


def _count_rows_by_label(
    rows: list[sqlite3.Row],
    *,
    label_key: str = "period_label",
    count_key: str = "row_count",
) -> dict[str, int]:
    return {str(row[label_key]): int(row[count_key]) for row in rows}


def _build_dual_count_dataset(
    *,
    order: list[str],
    display_labels: list[str],
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    first_key: str,
    second_key: str,
) -> dict[str, Any] | None:
    first_values = [first_counts.get(label, 0) for label in order]
    second_values = [second_counts.get(label, 0) for label in order]
    if not any(first_values) and not any(second_values):
        return None
    return {
        "labels": order,
        "display_labels": display_labels,
        first_key: first_values,
        second_key: second_values,
    }


def build_posts_trend_dataset(
    connection: sqlite3.Connection,
    *,
    stage: str = ACTIVE_FORMAL_STAGE,
) -> dict[str, Any] | None:
    rows = connection.execute(
        "SELECT substr(post_date, 1, 7) AS period_month, COUNT(*) AS row_count "
        f"FROM {paper_scope_view('posts', stage)} "
        "WHERE post_date IS NOT NULL AND post_date != '' "
        "GROUP BY period_month ORDER BY period_month"
    ).fetchall()
    month_order = month_sequence(RESEARCH_WINDOW_START, RESEARCH_WINDOW_END)
    if not month_order:
        return None

    month_counts = {str(row["period_month"]): int(row["row_count"]) for row in rows}
    monthly_values = [month_counts.get(month, 0) for month in month_order]
    return {
        "month_order": month_order,
        "monthly_values": monthly_values,
        "smoothed_values": rolling_mean(monthly_values, 3),
    }


def _build_posts_by_period_dataset(
    connection: sqlite3.Connection,
    *,
    context: PeriodContext,
    stage: str = ACTIVE_FORMAL_STAGE,
) -> dict[str, Any] | None:
    post_rows = connection.execute(
        f"SELECT {context.halfyear_case_post} AS period_label, COUNT(*) AS row_count "
        f"FROM {paper_scope_view('posts', stage)} "
        "WHERE post_date IS NOT NULL "
        "GROUP BY period_label HAVING period_label IS NOT NULL"
    ).fetchall()
    comment_rows = connection.execute(
        f"SELECT {context.halfyear_case_comment} AS period_label, COUNT(*) AS row_count "
        f"FROM {paper_scope_view('comments', stage)} c "
        f"JOIN {paper_scope_view('posts', stage)} p ON p.post_id = c.post_id "
        "GROUP BY period_label HAVING period_label IS NOT NULL"
    ).fetchall()
    return _build_dual_count_dataset(
        order=context.halfyear_order,
        display_labels=context.halfyear_display_labels,
        first_counts=_count_rows_by_label(post_rows),
        second_counts=_count_rows_by_label(comment_rows),
        first_key="post_values",
        second_key="comment_values",
    )


def _build_posts_by_quarter_dataset(
    connection: sqlite3.Connection,
    *,
    context: PeriodContext,
    stage: str = ACTIVE_FORMAL_STAGE,
) -> dict[str, Any] | None:
    quarter_post_rows = connection.execute(
        "SELECT "
        "(substr(post_date, 1, 4) || 'Q' || "
        "(CAST(((CAST(substr(post_date, 6, 2) AS INTEGER) - 1) / 3) AS INTEGER) + 1)) AS period_label, "
        "COUNT(*) AS row_count "
        f"FROM {paper_scope_view('posts', stage)} "
        "WHERE post_date IS NOT NULL AND post_date != '' "
        "GROUP BY period_label ORDER BY period_label"
    ).fetchall()
    quarter_comment_rows = connection.execute(
        "SELECT "
        "(substr(c.comment_date, 1, 4) || 'Q' || "
        "(CAST(((CAST(substr(c.comment_date, 6, 2) AS INTEGER) - 1) / 3) AS INTEGER) + 1)) AS period_label, "
        "COUNT(*) AS row_count "
        f"FROM {paper_scope_view('comments', stage)} c "
        f"JOIN {paper_scope_view('posts', stage)} p ON p.post_id = c.post_id "
        "GROUP BY period_label ORDER BY period_label"
    ).fetchall()
    return _build_dual_count_dataset(
        order=context.quarter_labels,
        display_labels=context.quarter_display_labels,
        first_counts=_count_rows_by_label(quarter_post_rows),
        second_counts=_count_rows_by_label(quarter_comment_rows),
        first_key="post_values",
        second_key="comment_values",
    )


def build_post_count_datasets(
    connection: sqlite3.Connection,
    *,
    context: PeriodContext,
    stage: str = ACTIVE_FORMAL_STAGE,
) -> dict[str, dict[str, Any]]:
    datasets: dict[str, dict[str, Any]] = {}

    dataset = _build_posts_by_period_dataset(connection, context=context, stage=stage)
    if dataset:
        datasets["posts_by_period"] = dataset

    dataset = _build_posts_by_quarter_dataset(connection, context=context, stage=stage)
    if dataset:
        datasets["posts_by_quarter"] = dataset

    return datasets
