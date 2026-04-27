from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ai4s_legitimacy.analysis.figures._manifest_entries import FIGURE_ENTRIES
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
from ai4s_legitimacy.config.formal_baseline import (
    ACTIVE_FORMAL_LABEL,
    ACTIVE_FORMAL_SOURCE_CONTRACT,
    paper_scope_contract_name,
)
from ai4s_legitimacy.utils.paths import project_relative_path


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


def _skip_reason(slug: str, formal_comments: int) -> str:
    if slug == "comments_attitude" and formal_comments == 0:
        return "本轮为帖子层 post-only 正式口径，评论层暂未进入正式编码，故不生成评论态度图。"
    return "当前正式口径下该图所需结构化字段没有可绘制数据，保留登记但不作为本轮正式图件。"


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
        f"# 投稿版图表包（{ACTIVE_FORMAL_LABEL}）",
        "",
        f"- 当前正式基线：`{ACTIVE_FORMAL_LABEL}`",
        f"- 正式帖子 / 正式评论：`{formal_posts} / {formal_comments}`",
        f"- 正式覆盖截止日：`{resolve_coverage_end_date(coverage_end_date)}`",
        f"- 图表输出目录：`{figure_dir_display}`",
        f"- 已生成图表：`{len(generated_set)} / {len(FIGURE_ENTRIES)}`",
        "- 正文优先图：`posts_trend`、`posts_by_quarter`、`posts_heatmap`、`comments_attitude`、`tools_by_period`、`risk_themes_by_period`",
        "",
        "## 统一来源约定",
        "",
        f"- `{paper_scope_contract_name()}`：可由研究主库正式口径直接复现的图表；"
        f"当前生成 {len(generated_set)} 张，未生成图只登记口径，不进入本轮正式图件。",
        "- 本轮为帖子层 post-only artifact refresh；`formal_comments=0` 是设计选择，不是评论队列遗漏。",
        "",
    ]
    for index, entry in enumerate(FIGURE_ENTRIES, start=1):
        slug = entry.slug
        status = "generated" if slug in generated_set else "skipped"
        lines.append(f"## 图{index} `{slug}`")
        lines.append(f"- 建议图题：{entry.title}")
        lines.append(f"- 建议放置：{entry.placement}")
        lines.append(f"- 状态：`{status}`")
        lines.append(f"- 来源标签：`{ACTIVE_FORMAL_SOURCE_CONTRACT}`")
        lines.append(
            f"- 数据口径：{_render_entry_template(entry.data_basis_template, coverage_end_date)}"
        )
        if status == "generated":
            lines.append(
                f"- 正文可用结论句：{_render_entry_template(entry.takeaway_template, coverage_end_date)}"
            )
            lines.append(f"- PNG：`{project_relative_path(figure_dir / (slug + '.png'))}`")
            lines.append(f"- SVG：`{project_relative_path(figure_dir / (slug + '.svg'))}`")
        else:
            lines.append(f"- 跳过说明：{_skip_reason(slug, formal_comments)}")
        lines.append("")
    manifest_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return manifest_path
