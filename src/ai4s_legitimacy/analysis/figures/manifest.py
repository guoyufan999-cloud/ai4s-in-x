from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ai4s_legitimacy.analysis.figures.config import (
    FORMAL_HALFYEAR_LABELS,
    format_halfyear_sequence_text,
    format_month_window_text,
    format_quarter_sequence_text,
    formal_quarter_labels,
    halfyear_display,
    quarter_display,
    resolve_coverage_end_date,
)
from ai4s_legitimacy.utils.paths import project_relative_path


@dataclass(frozen=True)
class FigureManifestEntry:
    slug: str
    title: str
    placement: str
    data_basis_template: str
    takeaway_template: str


FIGURE_ENTRIES = (
    FigureManifestEntry(
        slug="posts_trend",
        title="月度正式帖子趋势",
        placement="正文",
        data_basis_template=(
            "研究主库 `paper_scope_quality_v4` 正式口径；基于 "
            "`vw_posts_paper_scope_quality_v4` 按月聚合；时间窗 "
            "{month_window_text}；按月补零并绘制 3 个月滚动均值。"
        ),
        takeaway_template=(
            "AI4S 讨论在 2025H2 后明显提速，并在 "
            "{latest_halfyear_label}达到当前样本内的最高活跃度。"
        ),
    ),
    FigureManifestEntry(
        slug="posts_by_period",
        title="半年度帖子与评论规模",
        placement="补充材料",
        data_basis_template=(
            "研究主库 `paper_scope_quality_v4` 正式口径；帖子与评论在半年度尺度上的规模变化；"
            "时间顺序固定为 {halfyear_sequence_text}。"
        ),
        takeaway_template=(
            "半年度尺度上，帖子与评论规模在 2025H2 之后同步抬升，平台讨论进入稳定扩张阶段。"
        ),
    ),
    FigureManifestEntry(
        slug="posts_by_quarter",
        title="季度帖子与评论规模",
        placement="正文",
        data_basis_template=(
            "研究主库 `paper_scope_quality_v4` 正式口径；帖子与评论在季度尺度上的规模变化；"
            "时间顺序固定为 {quarter_sequence_text}。"
        ),
        takeaway_template=(
            "季度尺度进一步显示，AI4S 讨论在 2025Q4 至 "
            "{latest_quarter_label}进入显著跃升区间。"
        ),
    ),
    FigureManifestEntry(
        slug="posts_heatmap",
        title="时间—学科—流程高频组合热力图",
        placement="正文",
        data_basis_template=(
            "研究主库 `paper_scope_quality_v4` 正式口径；高频“学科 × 流程”组合在半年度尺度上的帖子数；"
            "仅保留总量最高的 24 个组合并按固定学科/流程顺序排列。"
        ),
        takeaway_template=(
            "AI4S 并未均匀进入科研全流程，而是优先在工程技术与艺术人文的高频任务环节中形成可见扩散。"
        ),
    ),
    FigureManifestEntry(
        slug="comments_attitude",
        title="半年度评论态度结构",
        placement="正文",
        data_basis_template=(
            "研究主库 `paper_scope_quality_v4` 正式口径；正式评论在半年度尺度上的态度占比，"
            "使用 100% 堆叠柱图呈现结构变化。"
        ),
        takeaway_template=(
            "评论区长期以“中性经验帖”为主，但围绕风险和边界的规范协商始终持续存在。"
        ),
    ),
    FigureManifestEntry(
        slug="tools_by_period",
        title="半年度 AI 工具构成",
        placement="正文",
        data_basis_template=(
            "研究主库 `paper_scope_quality_v4` 正式口径；基于 "
            "`vw_posts_paper_scope_quality_v4` 的 `ai_tools_json` 字段按半年度聚合；"
            "仅保留全局 Top 5 工具，其余合并为「其他」。"
        ),
        takeaway_template=(
            "工具生态已从早期围绕单一工具的尝试，转向多模型并存、按任务切换的构成格局。"
        ),
    ),
    FigureManifestEntry(
        slug="tools_by_quarter",
        title="季度 AI 工具构成",
        placement="补充材料",
        data_basis_template=(
            "研究主库 `paper_scope_quality_v4` 正式口径；基于 "
            "`vw_posts_paper_scope_quality_v4` 的 `ai_tools_json` 字段按季度聚合；"
            "仅保留全局 Top 5 工具，其余合并为「其他」。"
        ),
        takeaway_template=(
            "季度尺度上可以更清楚地看到工具偏好的快速切换与多模型并存趋势。"
        ),
    ),
    FigureManifestEntry(
        slug="risk_themes_by_period",
        title="半年度风险主题构成",
        placement="正文",
        data_basis_template=(
            "研究主库 `paper_scope_quality_v4` 正式口径；基于 "
            "`vw_posts_paper_scope_quality_v4` 的 `risk_themes_json` 字段按半年度聚合；"
            "风险类别按论文叙述优先顺序固定。"
        ),
        takeaway_template=(
            "风险讨论并非平均分布，而是逐步集中到 detection 与 hallucination 等规范敏感议题上。"
        ),
    ),
    FigureManifestEntry(
        slug="risk_themes_by_quarter",
        title="季度风险主题构成",
        placement="补充材料",
        data_basis_template=(
            "研究主库 `paper_scope_quality_v4` 正式口径；基于 "
            "`vw_posts_paper_scope_quality_v4` 的 `risk_themes_json` 字段按季度聚合；"
            "风险类别按论文叙述优先顺序固定。"
        ),
        takeaway_template=(
            "季度尺度上，风险议题的结构变化进一步强化了规范协商随时间升温的判断。"
        ),
    ),
)

BODY_PRIORITY = {
    entry.slug for entry in FIGURE_ENTRIES if entry.placement == "正文"
}


def _latest_halfyear_label(coverage_end_date: str) -> str:
    resolved_coverage_end_date = resolve_coverage_end_date(coverage_end_date)
    if not FORMAL_HALFYEAR_LABELS:
        return ""
    return halfyear_display(FORMAL_HALFYEAR_LABELS[-1], resolved_coverage_end_date)


def _latest_quarter_label(coverage_end_date: str) -> str:
    resolved_coverage_end_date = resolve_coverage_end_date(coverage_end_date)
    quarter_labels = formal_quarter_labels()
    if not quarter_labels:
        return ""
    return quarter_display(quarter_labels[-1], resolved_coverage_end_date)


def _manifest_context(coverage_end_date: str) -> dict[str, str]:
    return {
        "month_window_text": format_month_window_text(),
        "halfyear_sequence_text": format_halfyear_sequence_text(
            coverage_end_date=coverage_end_date
        ),
        "quarter_sequence_text": format_quarter_sequence_text(
            coverage_end_date=coverage_end_date
        ),
        "latest_halfyear_label": _latest_halfyear_label(coverage_end_date),
        "latest_quarter_label": _latest_quarter_label(coverage_end_date),
    }


def _render_entry_template(template: str, coverage_end_date: str) -> str:
    return template.format(**_manifest_context(coverage_end_date))


def write_figure_manifest(
    figure_dir: Path,
    generated_slugs: Sequence[str],
    formal_posts: int,
    formal_comments: int,
    coverage_end_date: str,
) -> Path:
    manifest_path = figure_dir / "paper_figures_submission_manifest.md"
    generated_set = set(generated_slugs)
    figure_dir_display = project_relative_path(figure_dir)
    lines = [
        "# 投稿版图表包（quality_v4 正式冻结版）",
        "",
        "- 当前正式基线：`quality_v4 正式冻结版`",
        f"- 正式帖子 / 正式评论：`{formal_posts} / {formal_comments}`",
        f"- 正式覆盖截止日：`{resolve_coverage_end_date(coverage_end_date)}`",
        f"- 图表输出目录：`{figure_dir_display}`",
        f"- 已生成图表：`{len(generated_set)} / {len(FIGURE_ENTRIES)}`",
        "- 正文优先图：`posts_trend`、`posts_by_quarter`、`posts_heatmap`、`comments_attitude`、`tools_by_period`、`risk_themes_by_period`",
        "",
        "## 统一来源约定",
        "",
        "- `paper_scope_quality_v4`：可由研究主库正式口径直接复现的图表，当前覆盖全部 9 张投稿图。",
        "",
    ]
    for index, entry in enumerate(FIGURE_ENTRIES, start=1):
        slug = entry.slug
        status = "generated" if slug in generated_set else "skipped"
        lines.append(f"## 图{index} `{slug}`")
        lines.append(f"- 建议图题：{entry.title}")
        lines.append(f"- 建议放置：{entry.placement}")
        lines.append(f"- 状态：`{status}`")
        lines.append("- 来源标签：`paper_scope_quality_v4`")
        lines.append(
            f"- 数据口径：{_render_entry_template(entry.data_basis_template, coverage_end_date)}"
        )
        lines.append(
            f"- 正文可用结论句：{_render_entry_template(entry.takeaway_template, coverage_end_date)}"
        )
        if status == "generated":
            lines.append(f"- PNG：`{project_relative_path(figure_dir / (slug + '.png'))}`")
            lines.append(f"- SVG：`{project_relative_path(figure_dir / (slug + '.svg'))}`")
        lines.append("")
    manifest_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return manifest_path
