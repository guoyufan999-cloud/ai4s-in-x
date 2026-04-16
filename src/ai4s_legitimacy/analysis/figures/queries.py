from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from ai4s_legitimacy.analysis.figures.config import (
    ATTITUDE_ORDER,
    FORMAL_HALFYEAR_LABELS,
    RISK_PRIORITY,
    RESEARCH_WINDOW_END,
    RESEARCH_WINDOW_START,
    SUBJECT_DISPLAY,
    SUBJECT_ORDER,
    TOOL_PALETTE,
    WORKFLOW_ORDER,
    formal_quarter_labels,
    halfyear_case_sql,
    halfyear_display,
    infer_quarter,
    month_sequence,
    parse_json_list,
    quarter_display,
    resolve_coverage_end_date,
    rolling_mean,
    share_matrix,
)


@dataclass(frozen=True)
class PeriodContext:
    coverage_end_date: str
    halfyear_order: list[str]
    halfyear_display_labels: list[str]
    quarter_labels: list[str]
    quarter_display_labels: list[str]
    halfyear_case_post: str
    halfyear_case_comment: str


def _count_rows_by_label(
    rows,
    *,
    label_key: str = "period_label",
    count_key: str = "row_count",
) -> dict[str, int]:
    return {
        str(row[label_key]): int(row[count_key])
        for row in rows
    }


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
    rows,
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


def _resolve_period_context(coverage_end_date: str | None) -> PeriodContext:
    resolved_coverage_end_date = resolve_coverage_end_date(
        coverage_end_date,
        fallback=RESEARCH_WINDOW_END,
    )
    halfyear_order = list(FORMAL_HALFYEAR_LABELS)
    quarter_labels = formal_quarter_labels()
    return PeriodContext(
        coverage_end_date=resolved_coverage_end_date,
        halfyear_order=halfyear_order,
        halfyear_display_labels=[
            halfyear_display(label, resolved_coverage_end_date)
            for label in halfyear_order
        ],
        quarter_labels=quarter_labels,
        quarter_display_labels=[
            quarter_display(label, resolved_coverage_end_date)
            for label in quarter_labels
        ],
        halfyear_case_post=halfyear_case_sql("post_date"),
        halfyear_case_comment=halfyear_case_sql("COALESCE(c.comment_date, p.post_date)"),
    )


def _build_posts_trend_dataset(connection) -> dict[str, Any] | None:
    rows = connection.execute(
        "SELECT substr(post_date, 1, 7) AS period_month, COUNT(*) AS row_count "
        "FROM vw_posts_paper_scope_quality_v4 "
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
    connection,
    *,
    context: PeriodContext,
) -> dict[str, Any] | None:
    post_rows = connection.execute(
        f"SELECT {context.halfyear_case_post} AS period_label, COUNT(*) AS row_count "
        "FROM vw_posts_paper_scope_quality_v4 "
        "WHERE post_date IS NOT NULL "
        "GROUP BY period_label HAVING period_label IS NOT NULL"
    ).fetchall()
    comment_rows = connection.execute(
        f"SELECT {context.halfyear_case_comment} AS period_label, COUNT(*) AS row_count "
        "FROM vw_comments_paper_scope_quality_v4 c "
        "JOIN vw_posts_paper_scope_quality_v4 p ON p.post_id = c.post_id "
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
    connection,
    *,
    context: PeriodContext,
) -> dict[str, Any] | None:
    quarter_post_rows = connection.execute(
        "SELECT "
        "(substr(post_date, 1, 4) || 'Q' || "
        "(CAST(((CAST(substr(post_date, 6, 2) AS INTEGER) - 1) / 3) AS INTEGER) + 1)) AS period_label, "
        "COUNT(*) AS row_count "
        "FROM vw_posts_paper_scope_quality_v4 "
        "WHERE post_date IS NOT NULL AND post_date != '' "
        "GROUP BY period_label ORDER BY period_label"
    ).fetchall()
    quarter_comment_rows = connection.execute(
        "SELECT "
        "(substr(COALESCE(c.comment_date, p.post_date), 1, 4) || 'Q' || "
        "(CAST(((CAST(substr(COALESCE(c.comment_date, p.post_date), 6, 2) AS INTEGER) - 1) / 3) AS INTEGER) + 1)) AS period_label, "
        "COUNT(*) AS row_count "
        "FROM vw_comments_paper_scope_quality_v4 c "
        "JOIN vw_posts_paper_scope_quality_v4 p ON p.post_id = c.post_id "
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


def _build_posts_heatmap_dataset(
    connection,
    *,
    context: PeriodContext,
) -> dict[str, Any] | None:
    heatmap_rows = connection.execute(
        f"SELECT {context.halfyear_case_post} AS period_label, "
        "COALESCE(qs_broad_subject, 'uncertain') AS subject_label, "
        "COALESCE(workflow_stage, 'uncertain') AS workflow_stage, "
        "COUNT(*) AS row_count "
        "FROM vw_posts_paper_scope_quality_v4 "
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


def _build_comments_attitude_dataset(
    connection,
    *,
    context: PeriodContext,
) -> dict[str, Any] | None:
    attitude_rows = connection.execute(
        f"SELECT {context.halfyear_case_comment} AS period_label, "
        "COALESCE(c.stance, '其他') AS attitude_label, "
        "COUNT(*) AS row_count "
        "FROM vw_comments_paper_scope_quality_v4 c "
        "JOIN vw_posts_paper_scope_quality_v4 p ON p.post_id = c.post_id "
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


def _build_tools_datasets(
    connection,
    *,
    context: PeriodContext,
) -> dict[str, dict[str, Any]]:
    tool_rows = connection.execute(
        f"SELECT {context.halfyear_case_post} AS period_label, post_date, ai_tools_json "
        "FROM vw_posts_paper_scope_quality_v4 "
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


def _build_risk_theme_datasets(
    connection,
    *,
    context: PeriodContext,
) -> dict[str, dict[str, Any]]:
    risk_rows = connection.execute(
        f"SELECT {context.halfyear_case_post} AS period_label, post_date, risk_themes_json "
        "FROM vw_posts_paper_scope_quality_v4 "
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


def _build_post_count_datasets(
    connection,
    *,
    context: PeriodContext,
) -> dict[str, dict[str, Any]]:
    datasets: dict[str, dict[str, Any]] = {}
    dataset = _build_posts_by_period_dataset(connection, context=context)
    if dataset:
        datasets["posts_by_period"] = dataset

    dataset = _build_posts_by_quarter_dataset(connection, context=context)
    if dataset:
        datasets["posts_by_quarter"] = dataset

    return datasets


def load_submission_figure_data(
    connection,
    *,
    coverage_end_date: str | None = None,
) -> dict[str, dict[str, Any]]:
    context = _resolve_period_context(coverage_end_date)
    datasets: dict[str, dict[str, Any]] = {}

    dataset = _build_posts_trend_dataset(connection)
    if dataset:
        datasets["posts_trend"] = dataset

    datasets.update(_build_post_count_datasets(connection, context=context))

    dataset = _build_posts_heatmap_dataset(connection, context=context)
    if dataset:
        datasets["posts_heatmap"] = dataset

    dataset = _build_comments_attitude_dataset(connection, context=context)
    if dataset:
        datasets["comments_attitude"] = dataset

    datasets.update(_build_tools_datasets(connection, context=context))
    datasets.update(_build_risk_theme_datasets(connection, context=context))
    return datasets
