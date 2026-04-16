from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

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


def _save_figure(fig: Any, base_path: Path) -> dict[str, str]:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = base_path.with_suffix(".png")
    svg_path = base_path.with_suffix(".svg")
    fig.savefig(png_path, dpi=240, bbox_inches="tight")
    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    return {"png_path": str(png_path), "vector_path": str(svg_path)}


def _remove_top_right_spines(ax: Any) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def _configure_matplotlib() -> tuple[Any, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import font_manager

    from ai4s_legitimacy.analysis.figures.config import configure_style

    configure_style(matplotlib, font_manager)
    return plt, np


def _render_posts_trend(
    plt: Any,
    *,
    figure_dir: Path,
    dataset: Mapping[str, Any],
) -> None:
    month_order = list(dataset["month_order"])
    monthly_values = list(dataset["monthly_values"])
    smoothed_values = list(dataset["smoothed_values"])
    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    x_values = list(range(len(month_order)))
    ax.plot(
        x_values,
        monthly_values,
        color="#355070",
        linewidth=2.3,
        marker="o",
        markersize=3.6,
        label="正式帖子数",
    )
    ax.plot(
        x_values,
        smoothed_values,
        color="#B56576",
        linewidth=1.8,
        linestyle="--",
        label="3个月滚动均值",
    )
    ticks = [
        index
        for index in range(len(month_order))
        if index % 2 == 0 or index == len(month_order) - 1
    ]
    ax.set_xticks(ticks)
    ax.set_xticklabels(
        [month_order[index] for index in ticks],
        rotation=45,
        ha="right",
    )
    ax.set_ylabel("帖子数")
    ax.set_title("月度正式帖子趋势")
    ax.grid(axis="y", linestyle="--")
    ax.legend(frameon=False, loc="upper left")
    _remove_top_right_spines(ax)
    ax.set_xlim(-0.3, len(month_order) - 0.7)
    _save_figure(fig, figure_dir / "posts_trend")
    plt.close(fig)


def _render_dual_line_counts(
    plt: Any,
    *,
    figure_dir: Path,
    slug: str,
    title: str,
    labels: Sequence[str],
    post_values: Sequence[int],
    comment_values: Sequence[int],
    figure_size: tuple[float, float],
    rotation: int = 0,
) -> None:
    fig, ax = plt.subplots(figsize=figure_size)
    x_values = list(range(len(labels)))
    ax.plot(x_values, post_values, color="#355070", linewidth=2.2, marker="o", label="帖子数")
    ax.plot(
        x_values,
        comment_values,
        color="#C06C54",
        linewidth=2.2,
        marker="s",
        label="评论数",
    )
    ax.set_xticks(x_values)
    if rotation:
        ax.set_xticklabels(labels, rotation=rotation, ha="right")
    else:
        ax.set_xticklabels(labels)
    ax.set_ylabel("数量")
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--")
    ax.legend(frameon=False, loc="upper left")
    _remove_top_right_spines(ax)
    _save_figure(fig, figure_dir / slug)
    plt.close(fig)


def _render_heatmap(
    plt: Any,
    np: Any,
    *,
    figure_dir: Path,
    dataset: Mapping[str, Any],
) -> None:
    matrix = np.array(dataset["matrix"], dtype=float)
    row_labels = list(dataset["row_labels"])
    labels = list(dataset["display_labels"])
    figure_height = max(6.0, min(12.0, 0.42 * len(row_labels) + 2.8))
    fig, ax = plt.subplots(figsize=(9.4, figure_height))
    image = ax.imshow(matrix, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=8)
    ax.set_title("时间—学科—流程高频组合热力图")
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = int(matrix[row_index, column_index])
            if value > 0:
                ax.text(
                    column_index,
                    row_index,
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="#15324B",
                )
    fig.colorbar(image, ax=ax, label="帖子数")
    _save_figure(fig, figure_dir / "posts_heatmap")
    plt.close(fig)


def _render_stacked_share_chart(
    plt: Any,
    np: Any,
    *,
    figure_dir: Path,
    slug: str,
    title: str,
    labels: Sequence[str],
    categories: Sequence[str],
    matrix: Sequence[Sequence[float]],
    color_lookup: Mapping[str, str],
    default_color: str,
    figure_size: tuple[float, float],
    rotation: int = 0,
) -> None:
    fig, ax = plt.subplots(figsize=figure_size)
    x_values = list(range(len(labels)))
    bottom = np.zeros(len(labels))
    for index, category in enumerate(categories):
        values = np.array(matrix[index], dtype=float)
        ax.bar(
            x_values,
            values,
            bottom=bottom,
            color=color_lookup.get(category, default_color),
            width=0.72,
            label=category,
        )
        bottom += values
    ax.set_xticks(x_values)
    if rotation:
        ax.set_xticklabels(labels, rotation=rotation, ha="right")
    else:
        ax.set_xticklabels(labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("占比（%）")
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--")
    ax.legend(frameon=False, ncol=3, loc="upper left")
    _remove_top_right_spines(ax)
    _save_figure(fig, figure_dir / slug)
    plt.close(fig)


def generate_submission_figures(
    db_path: Path = RESEARCH_DB_PATH,
    figure_dir: Path = FIGURE_DIR,
    coverage_end_date: str | None = None,
) -> dict[str, Any]:
    plt, np = _configure_matplotlib()
    figure_dir.mkdir(parents=True, exist_ok=True)

    generated: list[str] = []
    with connect_sqlite_readonly(db_path) as connection:
        resolved_coverage_end_date = (
            coverage_end_date or resolve_paper_scope_coverage_end_date(connection)
        )
        datasets = load_submission_figure_data(
            connection,
            coverage_end_date=resolved_coverage_end_date,
        )

    posts_trend = datasets.get("posts_trend")
    if posts_trend:
        _render_posts_trend(plt, figure_dir=figure_dir, dataset=posts_trend)
        generated.append("posts_trend")

    posts_by_period = datasets.get("posts_by_period")
    if posts_by_period:
        _render_dual_line_counts(
            plt,
            figure_dir=figure_dir,
            slug="posts_by_period",
            title="半年度帖子与评论规模",
            labels=posts_by_period["display_labels"],
            post_values=posts_by_period["post_values"],
            comment_values=posts_by_period["comment_values"],
            figure_size=(8.8, 4.8),
        )
        generated.append("posts_by_period")

    posts_by_quarter = datasets.get("posts_by_quarter")
    if posts_by_quarter:
        _render_dual_line_counts(
            plt,
            figure_dir=figure_dir,
            slug="posts_by_quarter",
            title="季度帖子与评论规模",
            labels=posts_by_quarter["display_labels"],
            post_values=posts_by_quarter["post_values"],
            comment_values=posts_by_quarter["comment_values"],
            figure_size=(10.0, 4.8),
            rotation=25,
        )
        generated.append("posts_by_quarter")

    posts_heatmap = datasets.get("posts_heatmap")
    if posts_heatmap:
        _render_heatmap(plt, np, figure_dir=figure_dir, dataset=posts_heatmap)
        generated.append("posts_heatmap")

    comments_attitude = datasets.get("comments_attitude")
    if comments_attitude:
        _render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="comments_attitude",
            title="半年度评论态度结构",
            labels=comments_attitude["display_labels"],
            categories=comments_attitude["categories"],
            matrix=comments_attitude["matrix"],
            color_lookup=ATTITUDE_COLORS,
            default_color=ATTITUDE_COLORS["其他"],
            figure_size=(8.8, 4.8),
        )
        generated.append("comments_attitude")

    tools_by_period = datasets.get("tools_by_period")
    if tools_by_period:
        _render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="tools_by_period",
            title="半年度 AI 工具构成",
            labels=tools_by_period["display_labels"],
            categories=tools_by_period["categories"],
            matrix=tools_by_period["matrix"],
            color_lookup=tools_by_period["palette"],
            default_color="#A7B0BE",
            figure_size=(8.8, 4.8),
        )
        generated.append("tools_by_period")

    tools_by_quarter = datasets.get("tools_by_quarter")
    if tools_by_quarter:
        _render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="tools_by_quarter",
            title="季度 AI 工具构成",
            labels=tools_by_quarter["display_labels"],
            categories=tools_by_quarter["categories"],
            matrix=tools_by_quarter["matrix"],
            color_lookup=tools_by_quarter["palette"],
            default_color="#A7B0BE",
            figure_size=(10.0, 4.8),
            rotation=25,
        )
        generated.append("tools_by_quarter")

    risk_by_period = datasets.get("risk_themes_by_period")
    if risk_by_period:
        _render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="risk_themes_by_period",
            title="半年度风险主题构成",
            labels=risk_by_period["display_labels"],
            categories=risk_by_period["categories"],
            matrix=risk_by_period["matrix"],
            color_lookup=RISK_COLORS,
            default_color=RISK_COLORS["其他"],
            figure_size=(8.8, 4.8),
        )
        generated.append("risk_themes_by_period")

    risk_by_quarter = datasets.get("risk_themes_by_quarter")
    if risk_by_quarter:
        _render_stacked_share_chart(
            plt,
            np,
            figure_dir=figure_dir,
            slug="risk_themes_by_quarter",
            title="季度风险主题构成",
            labels=risk_by_quarter["display_labels"],
            categories=risk_by_quarter["categories"],
            matrix=risk_by_quarter["matrix"],
            color_lookup=RISK_COLORS,
            default_color=RISK_COLORS["其他"],
            figure_size=(10.0, 4.8),
            rotation=25,
        )
        generated.append("risk_themes_by_quarter")

    return {
        "status": "ok",
        "figure_dir": str(figure_dir),
        "figure_count": len(generated),
        "generated_slugs": generated,
        "coverage_end_date": resolved_coverage_end_date,
        "research_window_start": RESEARCH_WINDOW_START,
    }
