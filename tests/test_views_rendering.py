from __future__ import annotations

import ai4s_legitimacy.config.research_scope as research_scope
from ai4s_legitimacy.analysis.figures.config import (
    format_halfyear_sequence_text,
    format_month_window_text,
    format_quarter_sequence_text,
)
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import VIEWS_PATH, VIEWS_TEMPLATE_PATH


def _normalize_sql(text: str) -> str:
    return "\n".join(
        line.rstrip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("--")
    ).strip()


def test_rendered_views_sql_matches_checked_in_artifact() -> None:
    assert _normalize_sql(render_views_sql()) == _normalize_sql(
        VIEWS_PATH.read_text(encoding="utf-8")
    )


def test_render_views_sql_tracks_custom_research_window() -> None:
    rendered = render_views_sql(start_date="2023-07-01", end_date="2024-06-30")
    assert "BETWEEN '2023-07-01' AND '2024-06-30'" in rendered
    assert "THEN '2023H2'" in rendered
    assert "THEN '2024H1'" in rendered
    assert "THEN '2026H1'" not in rendered


def test_rendered_views_sql_no_longer_exposes_placeholder_coding_views() -> None:
    rendered = render_views_sql()
    checked_in = VIEWS_PATH.read_text(encoding="utf-8")

    assert "vw_paper_quality_v4_ai_practice_distribution" not in rendered
    assert "vw_paper_quality_v4_workflow_ai_practice_cross" not in rendered
    assert "vw_paper_quality_v4_legitimacy_dimension_distribution" not in rendered
    assert "vw_paper_quality_v4_ai_practice_distribution" not in checked_in
    assert "vw_paper_quality_v4_workflow_ai_practice_cross" not in checked_in
    assert "vw_paper_quality_v4_legitimacy_dimension_distribution" not in checked_in


def test_view_path_constants_come_from_shared_settings() -> None:
    assert research_scope.VIEWS_TEMPLATE_PATH == VIEWS_TEMPLATE_PATH
    assert research_scope.VIEWS_PATH == VIEWS_PATH


def test_figure_window_helpers_follow_custom_research_window() -> None:
    assert (
        format_month_window_text(start_date="2023-07-01", end_date="2024-06-30")
        == "`2023-07` 至 `2024-06`"
    )
    assert (
        format_halfyear_sequence_text(
            start_date="2023-07-01",
            end_date="2024-06-30",
            coverage_end_date="2024-05-15",
        )
        == "`2023H2 -> 2024H1(部分)`"
    )
    assert (
        format_quarter_sequence_text(
            start_date="2023-07-01",
            end_date="2024-06-30",
            coverage_end_date="2024-05-15",
        )
        == "`2023Q3 -> 2023Q4 -> 2024Q1 -> 2024Q2(部分)`"
    )
