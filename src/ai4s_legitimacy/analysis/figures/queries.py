from __future__ import annotations

import sqlite3
from typing import Any

from ._query_categories import (
    build_comments_attitude_dataset,
    build_posts_heatmap_dataset,
    build_risk_theme_datasets,
    build_tools_datasets,
)
from ._query_context import resolve_period_context
from ._query_counts import build_post_count_datasets, build_posts_trend_dataset

__all__ = ["load_submission_figure_data"]


def load_submission_figure_data(
    connection: sqlite3.Connection,
    *,
    coverage_end_date: str | None = None,
) -> dict[str, dict[str, Any]]:
    context = resolve_period_context(coverage_end_date)
    datasets: dict[str, dict[str, Any]] = {}

    dataset = build_posts_trend_dataset(connection)
    if dataset:
        datasets["posts_trend"] = dataset

    datasets.update(build_post_count_datasets(connection, context=context))

    dataset = build_posts_heatmap_dataset(connection, context=context)
    if dataset:
        datasets["posts_heatmap"] = dataset

    dataset = build_comments_attitude_dataset(connection, context=context)
    if dataset:
        datasets["comments_attitude"] = dataset

    datasets.update(build_tools_datasets(connection, context=context))
    datasets.update(build_risk_theme_datasets(connection, context=context))
    return datasets
