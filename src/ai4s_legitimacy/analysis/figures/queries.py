from __future__ import annotations

from collections import defaultdict
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


def load_submission_figure_data(
    connection,
    *,
    coverage_end_date: str | None = None,
) -> dict[str, dict[str, Any]]:
    resolved_coverage_end_date = resolve_coverage_end_date(
        coverage_end_date,
        fallback=RESEARCH_WINDOW_END,
    )
    halfyear_order = list(FORMAL_HALFYEAR_LABELS)
    halfyear_display_labels = [
        halfyear_display(label, resolved_coverage_end_date) for label in halfyear_order
    ]
    quarter_labels = formal_quarter_labels()
    quarter_display_labels = [
        quarter_display(label, resolved_coverage_end_date) for label in quarter_labels
    ]
    halfyear_case_post = halfyear_case_sql("post_date")
    halfyear_case_comment = halfyear_case_sql("COALESCE(c.comment_date, p.post_date)")
    datasets: dict[str, dict[str, Any]] = {}

    rows = connection.execute(
        "SELECT substr(post_date, 1, 7) AS period_month, COUNT(*) AS row_count "
        "FROM vw_posts_paper_scope_quality_v4 "
        "WHERE post_date IS NOT NULL AND post_date != '' "
        "GROUP BY period_month ORDER BY period_month"
    ).fetchall()
    month_order = month_sequence(RESEARCH_WINDOW_START, RESEARCH_WINDOW_END)
    month_counts = {str(row["period_month"]): int(row["row_count"]) for row in rows}
    monthly_values = [month_counts.get(month, 0) for month in month_order]
    if month_order:
        datasets["posts_trend"] = {
            "month_order": month_order,
            "monthly_values": monthly_values,
            "smoothed_values": rolling_mean(monthly_values, 3),
        }

    post_rows = connection.execute(
        f"SELECT {halfyear_case_post} AS period_label, COUNT(*) AS row_count "
        "FROM vw_posts_paper_scope_quality_v4 "
        "WHERE post_date IS NOT NULL "
        "GROUP BY period_label HAVING period_label IS NOT NULL"
    ).fetchall()
    comment_rows = connection.execute(
        f"SELECT {halfyear_case_comment} AS period_label, COUNT(*) AS row_count "
        "FROM vw_comments_paper_scope_quality_v4 c "
        "JOIN vw_posts_paper_scope_quality_v4 p ON p.post_id = c.post_id "
        "GROUP BY period_label HAVING period_label IS NOT NULL"
    ).fetchall()
    post_counts = {str(row["period_label"]): int(row["row_count"]) for row in post_rows}
    comment_counts = {
        str(row["period_label"]): int(row["row_count"]) for row in comment_rows
    }
    post_values = [post_counts.get(label, 0) for label in halfyear_order]
    comment_values = [comment_counts.get(label, 0) for label in halfyear_order]
    if any(post_values) or any(comment_values):
        datasets["posts_by_period"] = {
            "labels": halfyear_order,
            "display_labels": halfyear_display_labels,
            "post_values": post_values,
            "comment_values": comment_values,
        }

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
    quarter_post_values = [quarter_post_counts.get(label, 0) for label in quarter_labels]
    quarter_comment_values = [
        quarter_comment_counts.get(label, 0) for label in quarter_labels
    ]
    if any(quarter_post_values) or any(quarter_comment_values):
        datasets["posts_by_quarter"] = {
            "labels": quarter_labels,
            "display_labels": quarter_display_labels,
            "post_values": quarter_post_values,
            "comment_values": quarter_comment_values,
        }

    heatmap_rows = connection.execute(
        f"SELECT {halfyear_case_post} AS period_label, "
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
    if combination_totals:
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
                        period_label, 0
                    )
                    for period_label in halfyear_order
                ]
            )
        datasets["posts_heatmap"] = {
            "display_labels": halfyear_display_labels,
            "matrix": matrix,
            "row_labels": row_labels,
        }

    attitude_rows = connection.execute(
        f"SELECT {halfyear_case_comment} AS period_label, "
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
    ] + sorted(attitude for attitude in present_attitudes if attitude not in ATTITUDE_ORDER)
    if ordered_attitudes:
        datasets["comments_attitude"] = {
            "categories": ordered_attitudes,
            "display_labels": halfyear_display_labels,
            "matrix": share_matrix(attitude_counts, halfyear_order, ordered_attitudes),
        }

    tool_rows = connection.execute(
        f"SELECT {halfyear_case_post} AS period_label, post_date, ai_tools_json "
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
    top_tools = [
        item[0] for item in sorted(total_tools.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]
    tool_categories = list(top_tools) + (
        ["其他"] if any(name not in top_tools for name in total_tools) else []
    )
    if total_tools:
        aggregated_halfyear_tools: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for period_label in halfyear_order:
            for tool_name, row_count in tools_by_period.get(period_label, {}).items():
                aggregated_halfyear_tools[period_label][
                    tool_name if tool_name in top_tools else "其他"
                ] += row_count
        datasets["tools_by_period"] = {
            "categories": tool_categories,
            "display_labels": halfyear_display_labels,
            "matrix": share_matrix(
                aggregated_halfyear_tools,
                halfyear_order,
                tool_categories,
            ),
            "palette": {
                tool_name: TOOL_PALETTE[index % len(TOOL_PALETTE)]
                for index, tool_name in enumerate(top_tools)
            }
            | {"其他": "#A7B0BE"},
        }

        aggregated_quarter_tools: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for period_label in quarter_labels:
            for tool_name, row_count in tools_by_quarter.get(period_label, {}).items():
                aggregated_quarter_tools[period_label][
                    tool_name if tool_name in top_tools else "其他"
                ] += row_count
        datasets["tools_by_quarter"] = {
            "categories": tool_categories,
            "display_labels": quarter_display_labels,
            "matrix": share_matrix(
                aggregated_quarter_tools,
                quarter_labels,
                tool_categories,
            ),
            "palette": {
                tool_name: TOOL_PALETTE[index % len(TOOL_PALETTE)]
                for index, tool_name in enumerate(top_tools)
            }
            | {"其他": "#A7B0BE"},
        }

    risk_rows = connection.execute(
        f"SELECT {halfyear_case_post} AS period_label, post_date, risk_themes_json "
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
    if total_risks:
        aggregated_halfyear_risks: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for period_label in halfyear_order:
            for risk_name, row_count in risks_by_period.get(period_label, {}).items():
                aggregated_halfyear_risks[period_label][
                    risk_name if risk_name in ordered_risks else "其他"
                ] += row_count
        datasets["risk_themes_by_period"] = {
            "categories": ordered_risks,
            "display_labels": halfyear_display_labels,
            "matrix": share_matrix(
                aggregated_halfyear_risks,
                halfyear_order,
                ordered_risks,
            ),
        }

        aggregated_quarter_risks: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for period_label in quarter_labels:
            for risk_name, row_count in risks_by_quarter.get(period_label, {}).items():
                aggregated_quarter_risks[period_label][
                    risk_name if risk_name in ordered_risks else "其他"
                ] += row_count
        datasets["risk_themes_by_quarter"] = {
            "categories": ordered_risks,
            "display_labels": quarter_display_labels,
            "matrix": share_matrix(
                aggregated_quarter_risks,
                quarter_labels,
                ordered_risks,
            ),
        }

    return datasets
