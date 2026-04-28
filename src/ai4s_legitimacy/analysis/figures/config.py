from __future__ import annotations

import json
from calendar import monthrange
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

from ai4s_legitimacy.config.formal_baseline import ACTIVE_FIGURE_DIR, paper_scope_view
from ai4s_legitimacy.config.research_scope import (
    RESEARCH_WINDOW_END,
    RESEARCH_WINDOW_START,
    build_half_year_windows,
    render_half_year_case_sql,
)

HALF_YEAR_WINDOWS = build_half_year_windows()
FORMAL_HALFYEAR_LABELS = tuple(label for label, _, _ in HALF_YEAR_WINDOWS)
FIGURE_DIR = ACTIVE_FIGURE_DIR

SUBJECT_ORDER = [
    "Engineering & Technology",
    "Arts & Humanities",
    "Life Sciences & Medicine",
    "Natural Sciences",
    "Social Sciences & Management",
    "uncertain",
]
WORKFLOW_ORDER = [
    "文献检索与综述",
    "选题与问题定义",
    "编码/建模/统计分析",
    "研究设计与实验/方案制定",
    "论文写作/投稿/审稿回复",
    "数据获取与预处理",
    "学术交流与科研管理",
    "uncertain",
]
SUBJECT_DISPLAY = {
    "Engineering & Technology": "工程技术",
    "Arts & Humanities": "艺术人文",
    "Life Sciences & Medicine": "生命医学",
    "Natural Sciences": "自然科学",
    "Social Sciences & Management": "社科管理",
    "uncertain": "未确定",
}
ATTITUDE_ORDER = ["中性经验帖", "积极但保留", "积极采用", "批判/担忧", "明确拒绝"]
ATTITUDE_COLORS = {
    "中性经验帖": "#6C7A89",
    "积极但保留": "#C89B3C",
    "积极采用": "#2F7F6F",
    "批判/担忧": "#C05A5A",
    "明确拒绝": "#7E4A65",
    "其他": "#B8BFC7",
}
RISK_PRIORITY = ["detection", "hallucination", "ethics", "privacy", "bias"]
RISK_COLORS = {
    "detection": "#8C4A5B",
    "hallucination": "#D17B49",
    "ethics": "#7A8F63",
    "privacy": "#6E7FA8",
    "bias": "#9A6FB0",
    "其他": "#B8BFC7",
}
TOOL_PALETTE = ["#355070", "#6D597A", "#B56576", "#E56B6F", "#EAAC8B", "#A7B0BE"]


def normalize_date_only(value: str | None) -> str:
    if not value:
        return ""
    normalized = str(value).strip().replace("/", "-")
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        pass
    candidate = normalized[:10]
    if len(candidate) == 10:
        try:
            datetime.strptime(candidate, "%Y-%m-%d")
            return candidate
        except ValueError:
            return ""
    return ""


def resolve_coverage_end_date(
    coverage_end_date: str | None,
    *,
    fallback: str = RESEARCH_WINDOW_END,
) -> str:
    normalized = normalize_date_only(coverage_end_date)
    fallback_date = normalize_date_only(fallback)
    if not normalized:
        return fallback_date
    if fallback_date and normalized > fallback_date:
        return fallback_date
    return normalized


def resolve_paper_scope_coverage_end_date(connection) -> str:
    row = connection.execute(
        f"""
        SELECT MAX(coverage_date) AS coverage_end_date
        FROM (
            SELECT post_date AS coverage_date
            FROM {paper_scope_view("posts")}
            WHERE post_date IS NOT NULL AND post_date != ''

            UNION ALL

            SELECT c.comment_date AS coverage_date
            FROM {paper_scope_view("comments")} c
            JOIN {paper_scope_view("posts")} p ON p.post_id = c.post_id
            WHERE c.comment_date IS NOT NULL
              AND c.comment_date != ''

            UNION ALL

            SELECT post_date AS coverage_date
            FROM posts
            WHERE post_date IS NOT NULL AND post_date != ''

            UNION ALL

            SELECT comment_date AS coverage_date
            FROM comments
            WHERE comment_date IS NOT NULL
              AND comment_date != ''
        )
        """
    ).fetchone()
    raw_value = ""
    if row is not None:
        raw_value = row["coverage_end_date"] if hasattr(row, "keys") else row[0]
    return resolve_coverage_end_date(str(raw_value or ""))


def format_month_window_text(
    start_date: str = RESEARCH_WINDOW_START,
    end_date: str = RESEARCH_WINDOW_END,
) -> str:
    start = normalize_date_only(start_date)
    end = normalize_date_only(end_date)
    if not start or not end:
        return ""
    return f"`{start[:7]}` 至 `{end[:7]}`"


def halfyear_bounds(label: str) -> tuple[str, str]:
    normalized = str(label or "").strip()
    if (
        len(normalized) != 6
        or normalized[4] != "H"
        or not normalized[:4].isdigit()
        or normalized[5] not in "12"
    ):
        return "", ""
    year, half = int(normalized[:4]), int(normalized[5])
    start_month, end_month = (1, 6) if half == 1 else (7, 12)
    return (
        date(year, start_month, 1).isoformat(),
        date(year, end_month, monthrange(year, end_month)[1]).isoformat(),
    )


def halfyear_display(label: str, as_of: str) -> str:
    start, end = halfyear_bounds(label)
    if not start:
        return label
    if start <= as_of <= end and as_of < end:
        return f"{label}(部分)"
    return label


def quarter_bounds(label: str) -> tuple[str, str]:
    normalized = str(label or "").strip()
    if (
        len(normalized) != 6
        or normalized[4] != "Q"
        or not normalized[:4].isdigit()
        or normalized[5] not in "1234"
    ):
        return "", ""
    year, quarter = int(normalized[:4]), int(normalized[5])
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2
    return (
        date(year, start_month, 1).isoformat(),
        date(year, end_month, monthrange(year, end_month)[1]).isoformat(),
    )


def quarter_display(label: str, as_of: str) -> str:
    start, end = quarter_bounds(label)
    if not start:
        return label
    if start <= as_of <= end and as_of < end:
        return f"{label}(部分)"
    return label


def formal_quarter_labels(
    start_date: str = RESEARCH_WINDOW_START,
    end_date: str = RESEARCH_WINDOW_END,
) -> list[str]:
    start = normalize_date_only(start_date)
    end = normalize_date_only(end_date)
    if not start or not end:
        return []
    labels: list[str] = []
    for year in range(int(start[:4]), int(end[:4]) + 1):
        for quarter in (1, 2, 3, 4):
            label = f"{year}Q{quarter}"
            quarter_start, quarter_end = quarter_bounds(label)
            if not quarter_start or quarter_end < start or quarter_start > end:
                continue
            labels.append(label)
    return labels


def format_halfyear_sequence_text(
    start_date: str = RESEARCH_WINDOW_START,
    end_date: str = RESEARCH_WINDOW_END,
    *,
    coverage_end_date: str | None = None,
) -> str:
    resolved_coverage_end_date = resolve_coverage_end_date(
        coverage_end_date,
        fallback=end_date,
    )
    labels = [
        halfyear_display(label, resolved_coverage_end_date)
        for label, _, _ in build_half_year_windows(start_date, end_date)
    ]
    return f"`{' -> '.join(labels)}`" if labels else ""


def format_quarter_sequence_text(
    start_date: str = RESEARCH_WINDOW_START,
    end_date: str = RESEARCH_WINDOW_END,
    *,
    coverage_end_date: str | None = None,
) -> str:
    resolved_coverage_end_date = resolve_coverage_end_date(
        coverage_end_date,
        fallback=end_date,
    )
    labels = [
        quarter_display(label, resolved_coverage_end_date)
        for label in formal_quarter_labels(start_date, end_date)
    ]
    return f"`{' -> '.join(labels)}`" if labels else ""


def infer_quarter(date_str: str) -> str:
    normalized = normalize_date_only(date_str)
    if not normalized:
        return "unknown"
    return f"{normalized[:4]}Q{(int(normalized[5:7]) - 1) // 3 + 1}"


def month_sequence(start_date: str, end_date: str) -> list[str]:
    start = normalize_date_only(start_date)
    end = normalize_date_only(end_date)
    if not start or not end:
        return []
    current = date(int(start[:4]), int(start[5:7]), 1)
    limit = date(int(end[:4]), int(end[5:7]), 1)
    months: list[str] = []
    while current <= limit:
        months.append(current.strftime("%Y-%m"))
        current = date(
            current.year + (1 if current.month == 12 else 0),
            1 if current.month == 12 else current.month + 1,
            1,
        )
    return months


def rolling_mean(values: Sequence[float], window: int = 3) -> list[float]:
    size = max(int(window), 1)
    smoothed: list[float] = []
    for index in range(len(values)):
        subset = values[max(0, index - size + 1) : index + 1]
        smoothed.append(sum(subset) / len(subset))
    return smoothed


def share_matrix(
    counts: Mapping[str, Mapping[str, int]],
    period_order: Sequence[str],
    categories: Sequence[str],
) -> list[list[float]]:
    matrix: list[list[float]] = []
    for category in categories:
        row: list[float] = []
        for period in period_order:
            period_counts = dict(counts.get(period) or {})
            total = float(sum(int(value) for value in period_counts.values()))
            row.append(
                float(period_counts.get(category, 0)) / total * 100.0 if total > 0 else 0.0
            )
        matrix.append(row)
    return matrix


def parse_json_list(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(payload, list):
            return [str(item).strip() for item in payload if str(item).strip()]
    return []


def configure_style(matplotlib: Any, font_manager: Any) -> list[str]:
    candidates = [
        "Noto Serif CJK SC",
        "Noto Sans CJK SC",
        "Noto Sans CJK JP",
        "Noto Serif CJK JP",
        "Microsoft YaHei",
        "SimHei",
        "WenQuanYi Zen Hei",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    available = {font.name for font in font_manager.fontManager.ttflist}
    chosen = [font for font in candidates if font in available]
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.sans-serif"] = chosen or candidates
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["figure.facecolor"] = "white"
    matplotlib.rcParams["savefig.facecolor"] = "white"
    matplotlib.rcParams["axes.facecolor"] = "white"
    matplotlib.rcParams["axes.edgecolor"] = "#5A6570"
    matplotlib.rcParams["axes.linewidth"] = 0.8
    matplotlib.rcParams["axes.titlesize"] = 13
    matplotlib.rcParams["axes.labelsize"] = 11
    matplotlib.rcParams["xtick.labelsize"] = 9
    matplotlib.rcParams["ytick.labelsize"] = 9
    matplotlib.rcParams["legend.fontsize"] = 9
    matplotlib.rcParams["grid.color"] = "#D6DADF"
    matplotlib.rcParams["grid.linewidth"] = 0.8
    matplotlib.rcParams["grid.alpha"] = 0.7
    return chosen or candidates


def halfyear_case_sql(column: str) -> str:
    return render_half_year_case_sql(
        column,
        start_date=RESEARCH_WINDOW_START,
        end_date=RESEARCH_WINDOW_END,
    )
