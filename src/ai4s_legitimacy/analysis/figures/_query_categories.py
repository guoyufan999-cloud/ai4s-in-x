from __future__ import annotations

import sqlite3
from collections import defaultdict
from typing import Any

from ai4s_legitimacy.analysis.figures.config import (
    ATTITUDE_ORDER,
    RISK_PRIORITY,
    SUBJECT_DISPLAY,
    SUBJECT_ORDER,
    TOOL_PALETTE,
    WORKFLOW_ORDER,
    infer_quarter,
    parse_json_list,
    share_matrix,
)
from ai4s_legitimacy.config.formal_baseline import ACTIVE_FORMAL_STAGE, paper_scope_view

from ._query_context import PeriodContext


def _ordered_present_categories(
    present_categories: set[str],
    preferred_order: list[str],
) -> list[str]:
    return [
        category for category in preferred_order if category in present_categories
    ] + sorted(
        category
        for category in present_categories
        if category not in preferred_order
    )


def _accumulate_json_category_counts(
    rows: list[sqlite3.Row],
    *,
    json_field: str,
) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, int]], dict[str, int]]:
    by_period: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_quarter: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    totals: dict[str, int] = defaultdict(int)
    for row in rows:
        period_label = str(row["period_label"] or "unknown")
        quarter_label = infer_quarter(str(row["post_date"] or ""))
        for category in parse_json_list(row[json_field]):
            by_period[period_label][category] += 1
            if quarter_label != "unknown":
                by_quarter[quarter_label][category] += 1
            totals[category] += 1
    return by_period, by_quarter, totals


def _top_categories(
    totals: dict[str, int],
    *,
    limit: int = 5,
) -> list[str]:
    return [
        category
        for category, _ in sorted(
            totals.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]
    ]


def _priority_categories(
    totals: dict[str, int],
    *,
    preferred_order: list[str],
) -> list[str]:
    categories = [category for category in preferred_order if category in totals]
    categories.extend(
        category
        for category, _ in sorted(
            totals.items(),
            key=lambda item: (-item[1], item[0]),
        )
        if category not in categories
    )
    return categories


def _collapse_categories_with_other(
    categories: list[str],
    *,
    totals: dict[str, int],
    limit: int = 5,
) -> list[str]:
    if len(categories) <= limit:
        return categories
    kept_categories = categories[:limit]
    return kept_categories + (
        ["其他"] if any(category not in kept_categories for category in totals) else []
    )


def _aggregate_category_counts(
    raw_counts: dict[str, dict[str, int]],
    *,
    categories: list[str],
) -> dict[str, dict[str, int]]:
    aggregated_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    kept_categories = set(categories) - {"其他"}
    has_other_bucket = "其他" in categories
    for period_label, period_counts in raw_counts.items():
        for category, row_count in period_counts.items():
            target_category = category
            if category not in kept_categories and has_other_bucket:
                target_category = "其他"
            aggregated_counts[period_label][target_category] += row_count
    return aggregated_counts


def _build_share_dataset(
    *,
    raw_counts: dict[str, dict[str, int]],
    order: list[str],
    display_labels: list[str],
    categories: list[str],
    palette: dict[str, str] | None = None,
) -> dict[str, Any]:
    dataset = {
        "categories": categories,
        "display_labels": display_labels,
        "matrix": share_matrix(
            _aggregate_category_counts(raw_counts, categories=categories),
            order,
            categories,
        ),
    }
    if palette is not None:
        dataset["palette"] = palette
    return dataset


def build_posts_heatmap_dataset(
    connection: sqlite3.Connection,
    *,
    context: PeriodContext,
    stage: str = ACTIVE_FORMAL_STAGE,
) -> dict[str, Any] | None:
    heatmap_rows = connection.execute(
        f"SELECT {context.halfyear_case_post} AS period_label, "
        "COALESCE(qs_broad_subject, 'uncertain') AS subject_label, "
        "COALESCE(workflow_stage, 'uncertain') AS workflow_stage, "
        "COUNT(*) AS row_count "
        f"FROM {paper_scope_view('posts', stage)} "
        "WHERE post_date IS NOT NULL "
        "GROUP BY period_label, subject_label, workflow_stage"
    ).fetchall()
    combination_counts: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    combination_totals: dict[tuple[str, str], int] = defaultdict(int)
    for row in heatmap_rows:
        subject_label = str(row["subject_label"])
        workflow_stage = str(row["workflow_stage"])
        period_label = str(row["period_label"] or "")
        combination_counts[(subject_label, workflow_stage)][period_label] += int(
            row["row_count"]
        )
        combination_totals[(subject_label, workflow_stage)] += int(row["row_count"])

    if not combination_totals:
        return None

    subject_rank = {label: index for index, label in enumerate(SUBJECT_ORDER)}
    workflow_rank = {label: index for index, label in enumerate(WORKFLOW_ORDER)}
    selected = sorted(
        combination_totals.items(),
        key=lambda item: (
            -item[1],
            subject_rank.get(item[0][0], 99),
            workflow_rank.get(item[0][1], 99),
        ),
    )[:24]
    ordered = sorted(
        [item[0] for item in selected],
        key=lambda item: (
            subject_rank.get(item[0], 99),
            workflow_rank.get(item[1], 99),
        ),
    )

    matrix: list[list[int]] = []
    row_labels: list[str] = []
    for subject_label, workflow_stage in ordered:
        row_labels.append(
            f"{SUBJECT_DISPLAY.get(subject_label, subject_label)}｜"
            f"{workflow_stage if workflow_stage != 'uncertain' else '未确定'}"
        )
        matrix.append(
            [
                combination_counts.get((subject_label, workflow_stage), {}).get(
                    period_label,
                    0,
                )
                for period_label in context.halfyear_order
            ]
        )

    return {
        "display_labels": context.halfyear_display_labels,
        "matrix": matrix,
        "row_labels": row_labels,
    }


def build_comments_attitude_dataset(
    connection: sqlite3.Connection,
    *,
    context: PeriodContext,
    stage: str = ACTIVE_FORMAL_STAGE,
) -> dict[str, Any] | None:
    attitude_rows = connection.execute(
        f"SELECT {context.halfyear_case_comment} AS period_label, "
        "COALESCE(c.stance, '其他') AS attitude_label, "
        "COUNT(*) AS row_count "
        f"FROM {paper_scope_view('comments', stage)} c "
        f"JOIN {paper_scope_view('posts', stage)} p ON p.post_id = c.post_id "
        "GROUP BY period_label, attitude_label HAVING period_label IS NOT NULL"
    ).fetchall()
    attitude_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    present_attitudes: set[str] = set()
    for row in attitude_rows:
        period_label = str(row["period_label"])
        attitude_label = str(row["attitude_label"])
        attitude_counts[period_label][attitude_label] += int(row["row_count"])
        present_attitudes.add(attitude_label)

    ordered_attitudes = _ordered_present_categories(
        present_attitudes,
        ATTITUDE_ORDER,
    )
    if not ordered_attitudes:
        return None

    return _build_share_dataset(
        raw_counts=attitude_counts,
        order=context.halfyear_order,
        display_labels=context.halfyear_display_labels,
        categories=ordered_attitudes,
    )


def build_tools_datasets(
    connection: sqlite3.Connection,
    *,
    context: PeriodContext,
    stage: str = ACTIVE_FORMAL_STAGE,
) -> dict[str, dict[str, Any]]:
    tool_rows = connection.execute(
        f"SELECT {context.halfyear_case_post} AS period_label, post_date, ai_tools_json "
        f"FROM {paper_scope_view('posts', stage)} "
        "WHERE post_date IS NOT NULL AND ai_tools_json IS NOT NULL AND ai_tools_json != '[]'"
    ).fetchall()
    tools_by_period, tools_by_quarter, total_tools = _accumulate_json_category_counts(
        tool_rows,
        json_field="ai_tools_json",
    )

    if not total_tools:
        return {}

    top_tools = _top_categories(total_tools)
    tool_categories = list(top_tools) + (
        ["其他"] if any(name not in top_tools for name in total_tools) else []
    )
    palette = {
        tool_name: TOOL_PALETTE[index % len(TOOL_PALETTE)]
        for index, tool_name in enumerate(top_tools)
    } | {"其他": "#A7B0BE"}

    return {
        "tools_by_period": _build_share_dataset(
            raw_counts=tools_by_period,
            order=context.halfyear_order,
            display_labels=context.halfyear_display_labels,
            categories=tool_categories,
            palette=palette,
        ),
        "tools_by_quarter": _build_share_dataset(
            raw_counts=tools_by_quarter,
            order=context.quarter_labels,
            display_labels=context.quarter_display_labels,
            categories=tool_categories,
            palette=palette,
        ),
    }


def build_risk_theme_datasets(
    connection: sqlite3.Connection,
    *,
    context: PeriodContext,
    stage: str = ACTIVE_FORMAL_STAGE,
) -> dict[str, dict[str, Any]]:
    risk_rows = connection.execute(
        f"SELECT {context.halfyear_case_post} AS period_label, post_date, risk_themes_json "
        f"FROM {paper_scope_view('posts', stage)} "
        "WHERE post_date IS NOT NULL AND risk_themes_json IS NOT NULL AND risk_themes_json != '[]'"
    ).fetchall()
    risks_by_period, risks_by_quarter, total_risks = _accumulate_json_category_counts(
        risk_rows,
        json_field="risk_themes_json",
    )

    if not total_risks:
        return {}

    ordered_risks = _priority_categories(
        total_risks,
        preferred_order=RISK_PRIORITY,
    )
    ordered_risks = _collapse_categories_with_other(
        ordered_risks,
        totals=total_risks,
    )

    return {
        "risk_themes_by_period": _build_share_dataset(
            raw_counts=risks_by_period,
            order=context.halfyear_order,
            display_labels=context.halfyear_display_labels,
            categories=ordered_risks,
        ),
        "risk_themes_by_quarter": _build_share_dataset(
            raw_counts=risks_by_quarter,
            order=context.quarter_labels,
            display_labels=context.quarter_display_labels,
            categories=ordered_risks,
        ),
    }
