from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from ai4s_legitimacy.analysis.figures.config import (
    ATTITUDE_COLORS,
    FIGURE_DIR,
    RISK_COLORS,
    RESEARCH_WINDOW_START,
    resolve_paper_scope_coverage_end_date,
)
from ai4s_legitimacy.analysis.figures.queries import load_submission_figure_data
from ai4s_legitimacy.config.settings import RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

from ._render_primitives import (
    render_dual_line_counts,
    render_heatmap,
    render_posts_trend,
    render_stacked_share_chart,
)
from ._render_runtime import configure_matplotlib


def _load_figure_datasets(
    *,
    db_path: Path,
    coverage_end_date: str | None,
    immutable: bool,
) -> tuple[str, dict[str, dict[str, Any]]]:
    with connect_sqlite_readonly(db_path, immutable=immutable) as connection:
        resolved_coverage_end_date = (
            coverage_end_date or resolve_paper_scope_coverage_end_date(connection)
        )
        datasets = load_submission_figure_data(
            connection,
            coverage_end_date=resolved_coverage_end_date,
        )
    return resolved_coverage_end_date, datasets


def _append_rendered_slug(
    generated: list[str],
    *,
    slug: str,
    dataset: Mapping[str, Any] | None,
    render: Callable[[Mapping[str, Any]], None],
) -> None:
    if dataset is None:
        return
    render(dataset)
    generated.append(slug)


def _render_generated_figures(
    plt: Any,
    np: Any,
    *,
    figure_dir: Path,
    datasets: dict[str, dict[str, Any]],
) -> list[str]:
    generated: list[str] = []

    _append_rendered_slug(
        generated,
        slug="posts_trend",
        dataset=datasets.get("posts_trend"),
        render=lambda dataset: render_posts_trend(
            plt,
            figure_dir=figure_dir,
            dataset=dataset,
        ),
    )
    _append_rendered_slug(
        generated,
        slug="posts_by_period",
        dataset=datasets.get("posts_by_period"),
        render=lambda dataset: render_dual_line_counts(
            plt,
            figure_dir=figure_dir,
            slug="posts_by_period",
            title="半年度帖子与评论规模",
            labels=dataset["display_labels"],
            post_values=dataset["post_values"],
            comment_values=dataset["comment_values"],
            figure_size=(8.8, 4.8),
        ),
    )
    _append_rendered_slug(
        generated,
        slug="posts_by_quarter",
        dataset=datasets.get("posts_by_quarter"),
        render=lambda dataset: render_dual_line_counts(
            plt,
            figure_dir=figure_dir,
            slug="posts_by_quarter",
            title="季度帖子与评论规模",
            labels=dataset["display_labels"],
            post_values=dataset["post_values"],
            comment_values=dataset["comment_values"],
            figure_size=(10.0, 4.8),
            rotation=25,
        ),
    )
    _append_rendered_slug(
        generated,
        slug="posts_heatmap",
        dataset=datasets.get("posts_heatmap"),
        render=lambda dataset: render_heatmap(
            plt,
            np,
            figure_dir=figure_dir,
            dataset=dataset,
        ),
    )
    _append_rendered_slug(
        generated,
        slug="comments_attitude",
        dataset=datasets.get("comments_attitude"),
        render=lambda dataset: render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="comments_attitude",
            title="半年度评论态度结构",
            labels=dataset["display_labels"],
            categories=dataset["categories"],
            matrix=dataset["matrix"],
            color_lookup=ATTITUDE_COLORS,
            default_color=ATTITUDE_COLORS["其他"],
            figure_size=(8.8, 4.8),
        ),
    )
    _append_rendered_slug(
        generated,
        slug="tools_by_period",
        dataset=datasets.get("tools_by_period"),
        render=lambda dataset: render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="tools_by_period",
            title="半年度 AI 工具构成",
            labels=dataset["display_labels"],
            categories=dataset["categories"],
            matrix=dataset["matrix"],
            color_lookup=dataset["palette"],
            default_color="#A7B0BE",
            figure_size=(8.8, 4.8),
        ),
    )
    _append_rendered_slug(
        generated,
        slug="tools_by_quarter",
        dataset=datasets.get("tools_by_quarter"),
        render=lambda dataset: render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="tools_by_quarter",
            title="季度 AI 工具构成",
            labels=dataset["display_labels"],
            categories=dataset["categories"],
            matrix=dataset["matrix"],
            color_lookup=dataset["palette"],
            default_color="#A7B0BE",
            figure_size=(10.0, 4.8),
            rotation=25,
        ),
    )
    _append_rendered_slug(
        generated,
        slug="risk_themes_by_period",
        dataset=datasets.get("risk_themes_by_period"),
        render=lambda dataset: render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="risk_themes_by_period",
            title="半年度风险主题构成",
            labels=dataset["display_labels"],
            categories=dataset["categories"],
            matrix=dataset["matrix"],
            color_lookup=RISK_COLORS,
            default_color=RISK_COLORS["其他"],
            figure_size=(8.8, 4.8),
        ),
    )
    _append_rendered_slug(
        generated,
        slug="risk_themes_by_quarter",
        dataset=datasets.get("risk_themes_by_quarter"),
        render=lambda dataset: render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="risk_themes_by_quarter",
            title="季度风险主题构成",
            labels=dataset["display_labels"],
            categories=dataset["categories"],
            matrix=dataset["matrix"],
            color_lookup=RISK_COLORS,
            default_color=RISK_COLORS["其他"],
            figure_size=(10.0, 4.8),
            rotation=25,
        ),
    )
    return generated


def generate_submission_figures(
    db_path: Path = RESEARCH_DB_PATH,
    figure_dir: Path = FIGURE_DIR,
    coverage_end_date: str | None = None,
    immutable: bool = False,
) -> dict[str, Any]:
    plt, np = configure_matplotlib()
    figure_dir.mkdir(parents=True, exist_ok=True)
    resolved_coverage_end_date, datasets = _load_figure_datasets(
        db_path=db_path,
        coverage_end_date=coverage_end_date,
        immutable=immutable,
    )
    generated = _render_generated_figures(
        plt,
        np,
        figure_dir=figure_dir,
        datasets=datasets,
    )
    return {
        "status": "ok",
        "figure_dir": str(figure_dir),
        "figure_count": len(generated),
        "generated_slugs": generated,
        "coverage_end_date": resolved_coverage_end_date,
        "research_window_start": RESEARCH_WINDOW_START,
    }
