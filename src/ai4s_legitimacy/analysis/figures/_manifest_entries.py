from __future__ import annotations

from dataclasses import dataclass


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
            "研究主库 `{source_contract}` 正式口径；基于 "
            "`{posts_scope_view}` 按月聚合；时间窗 "
            "{month_window_text}；按月补零并绘制 3 个月滚动均值。"
        ),
        takeaway_template=(
            "AI介入科研活动讨论在 2025H2 后明显提速，并在 "
            "{latest_halfyear_label}达到当前样本内的最高活跃度。"
        ),
    ),
    FigureManifestEntry(
        slug="posts_by_period",
        title="半年度正式帖子规模",
        placement="补充材料",
        data_basis_template=(
            "研究主库 `{source_contract}` 正式口径；正式帖子在半年度尺度上的规模变化；"
            "时间顺序固定为 {halfyear_sequence_text}。"
        ),
        takeaway_template=(
            "半年度尺度上，正式帖子规模在 2025H2 之后抬升，平台讨论进入稳定扩张阶段。"
        ),
    ),
    FigureManifestEntry(
        slug="posts_by_quarter",
        title="季度正式帖子规模",
        placement="正文",
        data_basis_template=(
            "研究主库 `{source_contract}` 正式口径；正式帖子在季度尺度上的规模变化；"
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
            "研究主库 `{source_contract}` 正式口径；高频“学科 × 流程”组合在半年度尺度上的帖子数；"
            "仅保留总量最高的 24 个组合并按固定学科/流程顺序排列。"
        ),
        takeaway_template=(
            "AI介入科研活动并未均匀进入科研全流程，而是优先在高频任务环节中形成可见扩散。"
        ),
    ),
    FigureManifestEntry(
        slug="comments_attitude",
        title="半年度评论态度结构",
        placement="正文",
        data_basis_template=(
            "研究主库 `{source_contract}` 正式口径；正式评论在半年度尺度上的态度占比，"
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
            "研究主库 `{source_contract}` 正式口径；基于 "
            "`{posts_scope_view}` 的 `ai_tools_json` 字段按半年度聚合；"
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
            "研究主库 `{source_contract}` 正式口径；基于 "
            "`{posts_scope_view}` 的 `ai_tools_json` 字段按季度聚合；"
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
            "研究主库 `{source_contract}` 正式口径；基于 "
            "`{posts_scope_view}` 的 `risk_themes_json` 字段按半年度聚合；"
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
            "研究主库 `{source_contract}` 正式口径；基于 "
            "`{posts_scope_view}` 的 `risk_themes_json` 字段按季度聚合；"
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
