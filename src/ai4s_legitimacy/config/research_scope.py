from __future__ import annotations

from pathlib import Path
from string import Template

from ai4s_legitimacy.config.settings import VIEWS_PATH, VIEWS_TEMPLATE_PATH

RESEARCH_WINDOW_START = "2024-01-01"
RESEARCH_WINDOW_END = "2026-06-30"

RESEARCH_SCOPE_SAMPLE_STATUSES = ("true", "review_needed")
PAPER_SCOPE_REQUIRED_CRAWL_STATUS = "crawled"
PAPER_SCOPE_EXCLUDED_ACTOR_TYPES = ("tool_vendor_or_promotional",)


def sql_string_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def build_half_year_windows(
    start_date: str = RESEARCH_WINDOW_START,
    end_date: str = RESEARCH_WINDOW_END,
) -> tuple[tuple[str, str, str], ...]:
    windows: list[tuple[str, str, str]] = []
    start_year = int(start_date[:4])
    end_year = int(end_date[:4])
    for year in range(start_year, end_year + 1):
        for label_suffix, window_start, window_end in (
            ("H1", f"{year}-01-01", f"{year}-06-30"),
            ("H2", f"{year}-07-01", f"{year}-12-31"),
        ):
            if window_end < start_date or window_start > end_date:
                continue
            windows.append(
                (
                    f"{year}{label_suffix}",
                    max(window_start, start_date),
                    min(window_end, end_date),
                )
            )
    return tuple(windows)


def render_half_year_case_sql(
    column: str,
    start_date: str = RESEARCH_WINDOW_START,
    end_date: str = RESEARCH_WINDOW_END,
) -> str:
    lines = ["    CASE"]
    for label, window_start, window_end in build_half_year_windows(start_date, end_date):
        lines.append(
            f"        WHEN {column} BETWEEN '{window_start}' AND '{window_end}' THEN '{label}'"
        )
    lines.append("    END")
    return "\n".join(lines)


def render_views_sql(
    start_date: str = RESEARCH_WINDOW_START,
    end_date: str = RESEARCH_WINDOW_END,
) -> str:
    template = Template(VIEWS_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.substitute(
        research_window_start=start_date,
        research_window_end=end_date,
        research_scope_status_values=sql_string_list(RESEARCH_SCOPE_SAMPLE_STATUSES),
        paper_scope_crawl_status=PAPER_SCOPE_REQUIRED_CRAWL_STATUS,
        paper_scope_excluded_actor_values=sql_string_list(
            PAPER_SCOPE_EXCLUDED_ACTOR_TYPES
        ),
        halfyear_case_post_date=render_half_year_case_sql(
            "post_date",
            start_date=start_date,
            end_date=end_date,
        ),
    )


def write_rendered_views_sql(
    output_path: Path = VIEWS_PATH,
    start_date: str = RESEARCH_WINDOW_START,
    end_date: str = RESEARCH_WINDOW_END,
) -> Path:
    output_path.write_text(
        render_views_sql(start_date=start_date, end_date=end_date),
        encoding="utf-8",
    )
    return output_path
