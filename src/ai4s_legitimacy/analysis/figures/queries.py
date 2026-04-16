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
    post_counts = {str(row["period_label"]): int(row["row_count"]) for row in post_rows}
    comment_counts = {
        str(row["period_label"]): int(row["row_count"]) for row in comment_rows
    }
    post_values = [post_counts.get(label, 0) for label in context.halfyear_order]
    comment_values = [comment_counts.get(label, 0) for label in context.halfyear_order]
    if not any(post_values) and not any(comment_values):
        return None
    return {
        "labels": context.halfyear_order,
        "display_labels": context.halfyear_display_labels,
        "post_values": post_values,
        "comment_values": comment_values,
    }


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
    quarter_post_counts = {
        str(row["period_label"]): int(row["row_count"]) for row in quarter_post_rows
    }
    quarter_comment_counts = {
        str(row["period_label"]): int(row["row_count"]) for row in quarter_comment_rows
    }
    quarter_post_values = [
        quarter_post_counts.get(label, 0) for label in context.quarter_labels
    ]
    quarter_comment_values = [
        quarter_comment_counts.get(label, 0) for label in context.quarter_labels
    ]
    if not any(quarter_post_values) and not any(quarter_comment_values):
        return None
    return {
        "labels": context.quarter_labels,
        "display_labels": context.quarter_display_labels,
        "post_values": quarter_post_values,
        "comment_values": quarter_comment_values,
    }


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

    ordered_attitudes = [
        attitude for attitude in ATTITUDE_ORDER if attitude in present_attitudes
    ] + sorted(
        attitude for attitude in present_attitudes if attitude not in ATTITUDE_ORDER
    )
    if not ordered_attitudes:
        return None

    return {
        "categories": ordered_attitudes,
        "display_labels": context.halfyear_display_labels,
        "matrix": share_matrix(
            attitude_counts,
            context.halfyear_order,
            ordered_attitudes,
        ),
    }


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
    tools_by_period: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tools_by_quarter: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_tools: dict[str, int] = defaultdict(int)
    for row in tool_rows:
        period_label = str(row["period_label"] or "unknown")
        quarter_label = infer_quarter(str(row["post_date"] or ""))
        for tool_name in parse_json_list(row["ai_tools_json"]):
            tools_by_period[period_label][tool_name] += 1
            if quarter_label != "unknown":
                tools_by_quarter[quarter_label][tool_name] += 1
            total_tools[tool_name] += 1

    if not total_tools:
        return {}

    top_tools = [
        item[0]
        for item in sorted(total_tools.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]
    tool_categories = list(top_tools) + (
        ["其他"] if any(name not in top_tools for name in total_tools) else []
    )
    palette = {
        tool_name: TOOL_PALETTE[index % len(TOOL_PALETTE)]
        for index, tool_name in enumerate(top_tools)
    } | {"其他": "#A7B0BE"}

    aggregated_halfyear_tools: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for period_label in context.halfyear_order:
        for tool_name, row_count in tools_by_period.get(period_label, {}).items():
            aggregated_halfyear_tools[period_label][
                tool_name if tool_name in top_tools else "其他"
            ] += row_count

    aggregated_quarter_tools: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for period_label in context.quarter_labels:
        for tool_name, row_count in tools_by_quarter.get(period_label, {}).items():
            aggregated_quarter_tools[period_label][
                tool_name if tool_name in top_tools else "其他"
            ] += row_count

    return {
        "tools_by_period": {
            "categories": tool_categories,
            "display_labels": context.halfyear_display_labels,
            "matrix": share_matrix(
                aggregated_halfyear_tools,
                context.halfyear_order,
                tool_categories,
            ),
            "palette": palette,
        },
        "tools_by_quarter": {
            "categories": tool_categories,
            "display_labels": context.quarter_display_labels,
            "matrix": share_matrix(
                aggregated_quarter_tools,
                context.quarter_labels,
                tool_categories,
            ),
            "palette": palette,
        },
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
    risks_by_period: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    risks_by_quarter: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_risks: dict[str, int] = defaultdict(int)
    for row in risk_rows:
        period_label = str(row["period_label"] or "unknown")
        quarter_label = infer_quarter(str(row["post_date"] or ""))
        for risk_name in parse_json_list(row["risk_themes_json"]):
            risks_by_period[period_label][risk_name] += 1
            if quarter_label != "unknown":
                risks_by_quarter[quarter_label][risk_name] += 1
            total_risks[risk_name] += 1

    if not total_risks:
        return {}

    ordered_risks = [risk for risk in RISK_PRIORITY if risk in total_risks]
    ordered_risks.extend(
        risk
        for risk, _ in sorted(total_risks.items(), key=lambda item: (-item[1], item[0]))
        if risk not in ordered_risks
    )
    if len(ordered_risks) > 5:
        kept_risks = ordered_risks[:5]
        ordered_risks = kept_risks + (
            ["其他"] if any(risk not in kept_risks for risk in ordered_risks) else []
        )

    aggregated_halfyear_risks: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for period_label in context.halfyear_order:
        for risk_name, row_count in risks_by_period.get(period_label, {}).items():
            aggregated_halfyear_risks[period_label][
                risk_name if risk_name in ordered_risks else "其他"
            ] += row_count

    aggregated_quarter_risks: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for period_label in context.quarter_labels:
        for risk_name, row_count in risks_by_quarter.get(period_label, {}).items():
            aggregated_quarter_risks[period_label][
                risk_name if risk_name in ordered_risks else "其他"
            ] += row_count

    return {
        "risk_themes_by_period": {
            "categories": ordered_risks,
            "display_labels": context.halfyear_display_labels,
            "matrix": share_matrix(
                aggregated_halfyear_risks,
                context.halfyear_order,
                ordered_risks,
            ),
        },
        "risk_themes_by_quarter": {
            "categories": ordered_risks,
            "display_labels": context.quarter_display_labels,
            "matrix": share_matrix(
                aggregated_quarter_risks,
                context.quarter_labels,
                ordered_risks,
            ),
        },
    }


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

    dataset = _build_posts_by_period_dataset(connection, context=context)
    if dataset:
        datasets["posts_by_period"] = dataset

    dataset = _build_posts_by_quarter_dataset(connection, context=context)
    if dataset:
        datasets["posts_by_quarter"] = dataset

    dataset = _build_posts_heatmap_dataset(connection, context=context)
    if dataset:
        datasets["posts_heatmap"] = dataset

    dataset = _build_comments_attitude_dataset(connection, context=context)
    if dataset:
        datasets["comments_attitude"] = dataset

    datasets.update(_build_tools_datasets(connection, context=context))
    datasets.update(_build_risk_theme_datasets(connection, context=context))
    return datasets
