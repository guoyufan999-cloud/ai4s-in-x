# 投稿版图表包（quality_v5 正式重建基线）

- 当前正式基线：`quality_v5 正式重建基线`
- 正式帖子 / 正式评论：`514 / 0`
- 正式覆盖截止日：`2026-04-10`
- 图表输出目录：`outputs/figures/paper_figures_submission/quality_v5`
- 已生成图表：`4 / 9`
- 正文优先图：`posts_trend`、`posts_by_quarter`、`posts_heatmap`、`comments_attitude`、`tools_by_period`、`risk_themes_by_period`

## 统一来源约定

- `paper_scope_quality_v5`：可由研究主库正式口径直接复现的图表，当前覆盖全部 9 张投稿图。

## 图1 `posts_trend`
- 建议图题：月度正式帖子趋势
- 建议放置：正文
- 状态：`generated`
- 来源标签：`paper_scope_quality_v5`
- 数据口径：研究主库 `paper_scope_quality_v5` 正式口径；基于 `vw_posts_paper_scope_quality_v5` 按月聚合；时间窗 `2024-01` 至 `2026-06`；按月补零并绘制 3 个月滚动均值。
- 正文可用结论句：AI4S 讨论在 2025H2 后明显提速，并在 2026H1(部分)达到当前样本内的最高活跃度。
- PNG：`outputs/figures/paper_figures_submission/quality_v5/posts_trend.png`
- SVG：`outputs/figures/paper_figures_submission/quality_v5/posts_trend.svg`

## 图2 `posts_by_period`
- 建议图题：半年度帖子与评论规模
- 建议放置：补充材料
- 状态：`generated`
- 来源标签：`paper_scope_quality_v5`
- 数据口径：研究主库 `paper_scope_quality_v5` 正式口径；帖子与评论在半年度尺度上的规模变化；时间顺序固定为 `2024H1 -> 2024H2 -> 2025H1 -> 2025H2 -> 2026H1(部分)`。
- 正文可用结论句：半年度尺度上，帖子与评论规模在 2025H2 之后同步抬升，平台讨论进入稳定扩张阶段。
- PNG：`outputs/figures/paper_figures_submission/quality_v5/posts_by_period.png`
- SVG：`outputs/figures/paper_figures_submission/quality_v5/posts_by_period.svg`

## 图3 `posts_by_quarter`
- 建议图题：季度帖子与评论规模
- 建议放置：正文
- 状态：`generated`
- 来源标签：`paper_scope_quality_v5`
- 数据口径：研究主库 `paper_scope_quality_v5` 正式口径；帖子与评论在季度尺度上的规模变化；时间顺序固定为 `2024Q1 -> 2024Q2 -> 2024Q3 -> 2024Q4 -> 2025Q1 -> 2025Q2 -> 2025Q3 -> 2025Q4 -> 2026Q1 -> 2026Q2(部分)`。
- 正文可用结论句：季度尺度进一步显示，AI4S 讨论在 2025Q4 至 2026Q2(部分)进入显著跃升区间。
- PNG：`outputs/figures/paper_figures_submission/quality_v5/posts_by_quarter.png`
- SVG：`outputs/figures/paper_figures_submission/quality_v5/posts_by_quarter.svg`

## 图4 `posts_heatmap`
- 建议图题：时间—学科—流程高频组合热力图
- 建议放置：正文
- 状态：`generated`
- 来源标签：`paper_scope_quality_v5`
- 数据口径：研究主库 `paper_scope_quality_v5` 正式口径；高频“学科 × 流程”组合在半年度尺度上的帖子数；仅保留总量最高的 24 个组合并按固定学科/流程顺序排列。
- 正文可用结论句：AI4S 并未均匀进入科研全流程，而是优先在工程技术与艺术人文的高频任务环节中形成可见扩散。
- PNG：`outputs/figures/paper_figures_submission/quality_v5/posts_heatmap.png`
- SVG：`outputs/figures/paper_figures_submission/quality_v5/posts_heatmap.svg`

## 图5 `comments_attitude`
- 建议图题：半年度评论态度结构
- 建议放置：正文
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v5`
- 数据口径：研究主库 `paper_scope_quality_v5` 正式口径；正式评论在半年度尺度上的态度占比，使用 100% 堆叠柱图呈现结构变化。
- 正文可用结论句：评论区长期以“中性经验帖”为主，但围绕风险和边界的规范协商始终持续存在。

## 图6 `tools_by_period`
- 建议图题：半年度 AI 工具构成
- 建议放置：正文
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v5`
- 数据口径：研究主库 `paper_scope_quality_v5` 正式口径；基于 `vw_posts_paper_scope_quality_v5` 的 `ai_tools_json` 字段按半年度聚合；仅保留全局 Top 5 工具，其余合并为「其他」。
- 正文可用结论句：工具生态已从早期围绕单一工具的尝试，转向多模型并存、按任务切换的构成格局。

## 图7 `tools_by_quarter`
- 建议图题：季度 AI 工具构成
- 建议放置：补充材料
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v5`
- 数据口径：研究主库 `paper_scope_quality_v5` 正式口径；基于 `vw_posts_paper_scope_quality_v5` 的 `ai_tools_json` 字段按季度聚合；仅保留全局 Top 5 工具，其余合并为「其他」。
- 正文可用结论句：季度尺度上可以更清楚地看到工具偏好的快速切换与多模型并存趋势。

## 图8 `risk_themes_by_period`
- 建议图题：半年度风险主题构成
- 建议放置：正文
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v5`
- 数据口径：研究主库 `paper_scope_quality_v5` 正式口径；基于 `vw_posts_paper_scope_quality_v5` 的 `risk_themes_json` 字段按半年度聚合；风险类别按论文叙述优先顺序固定。
- 正文可用结论句：风险讨论并非平均分布，而是逐步集中到 detection 与 hallucination 等规范敏感议题上。

## 图9 `risk_themes_by_quarter`
- 建议图题：季度风险主题构成
- 建议放置：补充材料
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v5`
- 数据口径：研究主库 `paper_scope_quality_v5` 正式口径；基于 `vw_posts_paper_scope_quality_v5` 的 `risk_themes_json` 字段按季度聚合；风险类别按论文叙述优先顺序固定。
- 正文可用结论句：季度尺度上，风险议题的结构变化进一步强化了规范协商随时间升温的判断。
