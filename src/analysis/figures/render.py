from __future__ import annotations

from pathlib import Path
from typing import Any

from src.analysis.figures.config import (
    ATTITUDE_COLORS,
    FIGURE_DIR,
    RISK_COLORS,
    RESEARCH_WINDOW_START,
    resolve_paper_scope_coverage_end_date,
)
from src.analysis.figures.queries import load_submission_figure_data
from src.config.settings import RESEARCH_DB_PATH
from src.utils.db import connect_sqlite_readonly


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


def generate_submission_figures(
    db_path: Path = RESEARCH_DB_PATH,
    figure_dir: Path = FIGURE_DIR,
    coverage_end_date: str | None = None,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import font_manager

    from src.analysis.figures.config import configure_style

    configure_style(matplotlib, font_manager)
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
        month_order = posts_trend["month_order"]
        monthly_values = posts_trend["monthly_values"]
        smoothed_values = posts_trend["smoothed_values"]
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
        generated.append("posts_trend")

    posts_by_period = datasets.get("posts_by_period")
    if posts_by_period:
        labels = posts_by_period["display_labels"]
        post_values = posts_by_period["post_values"]
        comment_values = posts_by_period["comment_values"]
        fig, ax = plt.subplots(figsize=(8.8, 4.8))
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
        ax.set_xticklabels(labels)
        ax.set_ylabel("数量")
        ax.set_title("半年度帖子与评论规模")
        ax.grid(axis="y", linestyle="--")
        ax.legend(frameon=False, loc="upper left")
        _remove_top_right_spines(ax)
        _save_figure(fig, figure_dir / "posts_by_period")
        plt.close(fig)
        generated.append("posts_by_period")

    posts_by_quarter = datasets.get("posts_by_quarter")
    if posts_by_quarter:
        labels = posts_by_quarter["display_labels"]
        post_values = posts_by_quarter["post_values"]
        comment_values = posts_by_quarter["comment_values"]
        fig, ax = plt.subplots(figsize=(10.0, 4.8))
        x_values = list(range(len(labels)))
        ax.plot(x_values, post_values, color="#355070", linewidth=2.1, marker="o", label="帖子数")
        ax.plot(
            x_values,
            comment_values,
            color="#C06C54",
            linewidth=2.1,
            marker="s",
            label="评论数",
        )
        ax.set_xticks(x_values)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_ylabel("数量")
        ax.set_title("季度帖子与评论规模")
        ax.grid(axis="y", linestyle="--")
        ax.legend(frameon=False, loc="upper left")
        _remove_top_right_spines(ax)
        _save_figure(fig, figure_dir / "posts_by_quarter")
        plt.close(fig)
        generated.append("posts_by_quarter")

    posts_heatmap = datasets.get("posts_heatmap")
    if posts_heatmap:
        matrix = np.array(posts_heatmap["matrix"], dtype=float)
        row_labels = posts_heatmap["row_labels"]
        labels = posts_heatmap["display_labels"]
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
        generated.append("posts_heatmap")

    comments_attitude = datasets.get("comments_attitude")
    if comments_attitude:
        categories = comments_attitude["categories"]
        labels = comments_attitude["display_labels"]
        matrix = comments_attitude["matrix"]
        fig, ax = plt.subplots(figsize=(8.8, 4.8))
        x_values = list(range(len(labels)))
        bottom = np.zeros(len(labels))
        for index, attitude in enumerate(categories):
            values = np.array(matrix[index], dtype=float)
            ax.bar(
                x_values,
                values,
                bottom=bottom,
                color=ATTITUDE_COLORS.get(attitude, ATTITUDE_COLORS["其他"]),
                width=0.72,
                label=attitude,
            )
            bottom += values
        ax.set_xticks(x_values)
        ax.set_xticklabels(labels)
        ax.set_ylabel("占比（%）")
        ax.set_ylim(0, 100)
        ax.set_title("半年度评论态度结构")
        ax.grid(axis="y", linestyle="--")
        ax.legend(frameon=False, ncol=3, loc="upper left")
        _remove_top_right_spines(ax)
        _save_figure(fig, figure_dir / "comments_attitude")
        plt.close(fig)
        generated.append("comments_attitude")

    tools_by_period = datasets.get("tools_by_period")
    if tools_by_period:
        categories = tools_by_period["categories"]
        labels = tools_by_period["display_labels"]
        matrix = tools_by_period["matrix"]
        palette = tools_by_period["palette"]
        fig, ax = plt.subplots(figsize=(8.8, 4.8))
        x_values = list(range(len(labels)))
        bottom = np.zeros(len(labels))
        for index, tool_name in enumerate(categories):
            values = np.array(matrix[index], dtype=float)
            ax.bar(
                x_values,
                values,
                bottom=bottom,
                color=palette.get(tool_name, "#A7B0BE"),
                width=0.72,
                label=tool_name,
            )
            bottom += values
        ax.set_xticks(x_values)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 100)
        ax.set_ylabel("占比（%）")
        ax.set_title("半年度 AI 工具构成")
        ax.grid(axis="y", linestyle="--")
        ax.legend(frameon=False, ncol=3, loc="upper left")
        _remove_top_right_spines(ax)
        _save_figure(fig, figure_dir / "tools_by_period")
        plt.close(fig)
        generated.append("tools_by_period")

    tools_by_quarter = datasets.get("tools_by_quarter")
    if tools_by_quarter:
        categories = tools_by_quarter["categories"]
        labels = tools_by_quarter["display_labels"]
        matrix = tools_by_quarter["matrix"]
        palette = tools_by_quarter["palette"]
        fig, ax = plt.subplots(figsize=(10.0, 4.8))
        x_values = list(range(len(labels)))
        bottom = np.zeros(len(labels))
        for index, tool_name in enumerate(categories):
            values = np.array(matrix[index], dtype=float)
            ax.bar(
                x_values,
                values,
                bottom=bottom,
                color=palette.get(tool_name, "#A7B0BE"),
                width=0.72,
                label=tool_name,
            )
            bottom += values
        ax.set_xticks(x_values)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_ylim(0, 100)
        ax.set_ylabel("占比（%）")
        ax.set_title("季度 AI 工具构成")
        ax.grid(axis="y", linestyle="--")
        ax.legend(frameon=False, ncol=3, loc="upper left")
        _remove_top_right_spines(ax)
        _save_figure(fig, figure_dir / "tools_by_quarter")
        plt.close(fig)
        generated.append("tools_by_quarter")

    risk_by_period = datasets.get("risk_themes_by_period")
    if risk_by_period:
        categories = risk_by_period["categories"]
        labels = risk_by_period["display_labels"]
        matrix = risk_by_period["matrix"]
        fig, ax = plt.subplots(figsize=(8.8, 4.8))
        x_values = list(range(len(labels)))
        bottom = np.zeros(len(labels))
        for index, risk_name in enumerate(categories):
            values = np.array(matrix[index], dtype=float)
            ax.bar(
                x_values,
                values,
                bottom=bottom,
                color=RISK_COLORS.get(risk_name, RISK_COLORS["其他"]),
                width=0.72,
                label=risk_name,
            )
            bottom += values
        ax.set_xticks(x_values)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 100)
        ax.set_ylabel("占比（%）")
        ax.set_title("半年度风险主题构成")
        ax.grid(axis="y", linestyle="--")
        ax.legend(frameon=False, ncol=3, loc="upper left")
        _remove_top_right_spines(ax)
        _save_figure(fig, figure_dir / "risk_themes_by_period")
        plt.close(fig)
        generated.append("risk_themes_by_period")

    risk_by_quarter = datasets.get("risk_themes_by_quarter")
    if risk_by_quarter:
        categories = risk_by_quarter["categories"]
        labels = risk_by_quarter["display_labels"]
        matrix = risk_by_quarter["matrix"]
        fig, ax = plt.subplots(figsize=(10.0, 4.8))
        x_values = list(range(len(labels)))
        bottom = np.zeros(len(labels))
        for index, risk_name in enumerate(categories):
            values = np.array(matrix[index], dtype=float)
            ax.bar(
                x_values,
                values,
                bottom=bottom,
                color=RISK_COLORS.get(risk_name, RISK_COLORS["其他"]),
                width=0.72,
                label=risk_name,
            )
            bottom += values
        ax.set_xticks(x_values)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_ylim(0, 100)
        ax.set_ylabel("占比（%）")
        ax.set_title("季度风险主题构成")
        ax.grid(axis="y", linestyle="--")
        ax.legend(frameon=False, ncol=3, loc="upper left")
        _remove_top_right_spines(ax)
        _save_figure(fig, figure_dir / "risk_themes_by_quarter")
        plt.close(fig)
        generated.append("risk_themes_by_quarter")

    return {
        "status": "ok",
        "figure_dir": str(figure_dir),
        "figure_count": len(generated),
        "generated_slugs": generated,
        "coverage_end_date": resolved_coverage_end_date,
        "research_window_start": RESEARCH_WINDOW_START,
    }
