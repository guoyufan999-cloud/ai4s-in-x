from __future__ import annotations

from dataclasses import dataclass

from ai4s_legitimacy.analysis.figures.config import (
    FORMAL_HALFYEAR_LABELS,
    RESEARCH_WINDOW_END,
    formal_quarter_labels,
    halfyear_case_sql,
    halfyear_display,
    quarter_display,
    resolve_coverage_end_date,
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


def resolve_period_context(coverage_end_date: str | None) -> PeriodContext:
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
        halfyear_case_comment=halfyear_case_sql("c.comment_date"),
    )
