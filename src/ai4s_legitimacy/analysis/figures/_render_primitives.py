from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from ._render_runtime import remove_top_right_spines, save_figure


def render_posts_trend(
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
    remove_top_right_spines(ax)
    ax.set_xlim(-0.3, len(month_order) - 0.7)
    save_figure(fig, figure_dir / "posts_trend")
    plt.close(fig)


def render_dual_line_counts(
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
    ax.plot(
        x_values,
        post_values,
        color="#355070",
        linewidth=2.2,
        marker="o",
        label="帖子数",
    )
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
    remove_top_right_spines(ax)
    save_figure(fig, figure_dir / slug)
    plt.close(fig)


def render_heatmap(
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
    save_figure(fig, figure_dir / "posts_heatmap")
    plt.close(fig)


def render_stacked_share_chart(
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
    remove_top_right_spines(ax)
    save_figure(fig, figure_dir / slug)
    plt.close(fig)
