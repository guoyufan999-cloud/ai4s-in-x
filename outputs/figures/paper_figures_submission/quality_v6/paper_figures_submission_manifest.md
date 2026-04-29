# 投稿版图表包（quality_v6 正式结果层）

- 当前正式基线：`quality_v6 正式结果层`
- 正式帖子 / 正式评论：`714 / 0`
- 正式覆盖截止日：`2026-04-26`
- 图表输出目录：`outputs/figures/paper_figures_submission/quality_v6`
- 已生成图表：`4 / 9`
- 正文优先图：`posts_trend`、`posts_by_quarter`、`posts_heatmap`、`comments_attitude`、`tools_by_period`、`risk_themes_by_period`

## 统一来源约定

- `paper_scope_quality_v6`：可由研究主库正式口径直接复现的图表；当前生成 4 张，未生成图只登记口径，不进入本轮正式图件。
- 本轮为帖子层 post-only artifact refresh；`formal_comments=0` 是设计选择，不是评论队列遗漏。

## 图1 `posts_trend`
- 建议图题：月度正式帖子趋势
- 建议放置：正文
- 状态：`generated`
- 来源标签：`paper_scope_quality_v6`
- 数据口径：研究主库 `paper_scope_quality_v6` 正式口径；基于 `vw_posts_paper_scope_quality_v6` 按月聚合；时间窗 `2024-01` 至 `2026-06`；按月补零并绘制 3 个月滚动均值。
- 正文可用结论句：AI介入科研活动讨论在 2025H2 后明显提速，并在 2026H1(部分)达到当前样本内的最高活跃度。
- PNG：`outputs/figures/paper_figures_submission/quality_v6/posts_trend.png`
- SVG：`outputs/figures/paper_figures_submission/quality_v6/posts_trend.svg`

## 图2 `posts_by_period`
- 建议图题：半年度正式帖子规模
- 建议放置：补充材料
- 状态：`generated`
- 来源标签：`paper_scope_quality_v6`
- 数据口径：研究主库 `paper_scope_quality_v6` 正式口径；正式帖子在半年度尺度上的规模变化；时间顺序固定为 `2024H1 -> 2024H2 -> 2025H1 -> 2025H2 -> 2026H1(部分)`。
- 正文可用结论句：半年度尺度上，正式帖子规模在 2025H2 之后抬升，平台讨论进入稳定扩张阶段。
- PNG：`outputs/figures/paper_figures_submission/quality_v6/posts_by_period.png`
- SVG：`outputs/figures/paper_figures_submission/quality_v6/posts_by_period.svg`

## 图3 `posts_by_quarter`
- 建议图题：季度正式帖子规模
- 建议放置：正文
- 状态：`generated`
- 来源标签：`paper_scope_quality_v6`
- 数据口径：研究主库 `paper_scope_quality_v6` 正式口径；正式帖子在季度尺度上的规模变化；时间顺序固定为 `2024Q1 -> 2024Q2 -> 2024Q3 -> 2024Q4 -> 2025Q1 -> 2025Q2 -> 2025Q3 -> 2025Q4 -> 2026Q1 -> 2026Q2(部分)`。
- 正文可用结论句：季度尺度进一步显示，AI4S 讨论在 2025Q4 至 2026Q2(部分)进入显著跃升区间。
- PNG：`outputs/figures/paper_figures_submission/quality_v6/posts_by_quarter.png`
- SVG：`outputs/figures/paper_figures_submission/quality_v6/posts_by_quarter.svg`

## 图4 `posts_heatmap`
- 建议图题：时间—学科—流程高频组合热力图
- 建议放置：正文
- 状态：`generated`
- 来源标签：`paper_scope_quality_v6`
- 数据口径：研究主库 `paper_scope_quality_v6` 正式口径；高频“学科 × 流程”组合在半年度尺度上的帖子数；仅保留总量最高的 24 个组合并按固定学科/流程顺序排列。
- 正文可用结论句：AI介入科研活动并未均匀进入科研全流程，而是优先在高频任务环节中形成可见扩散。
- PNG：`outputs/figures/paper_figures_submission/quality_v6/posts_heatmap.png`
- SVG：`outputs/figures/paper_figures_submission/quality_v6/posts_heatmap.svg`

## 图5 `comments_attitude`
- 建议图题：半年度评论态度结构
- 建议放置：正文
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v6`
- 数据口径：研究主库 `paper_scope_quality_v6` 正式口径；正式评论在半年度尺度上的态度占比，使用 100% 堆叠柱图呈现结构变化。
- 跳过说明：本轮为帖子层 post-only 正式口径，评论层暂未进入正式编码，故不生成评论态度图。

## 图6 `tools_by_period`
- 建议图题：半年度 AI 工具构成
- 建议放置：正文
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v6`
- 数据口径：研究主库 `paper_scope_quality_v6` 正式口径；基于 `vw_posts_paper_scope_quality_v6` 的 `ai_tools_json` 字段按半年度聚合；仅保留全局 Top 5 工具，其余合并为「其他」。
- 跳过说明：当前正式口径下该图所需结构化字段没有可绘制数据，保留登记但不作为本轮正式图件。

## 图7 `tools_by_quarter`
- 建议图题：季度 AI 工具构成
- 建议放置：补充材料
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v6`
- 数据口径：研究主库 `paper_scope_quality_v6` 正式口径；基于 `vw_posts_paper_scope_quality_v6` 的 `ai_tools_json` 字段按季度聚合；仅保留全局 Top 5 工具，其余合并为「其他」。
- 跳过说明：当前正式口径下该图所需结构化字段没有可绘制数据，保留登记但不作为本轮正式图件。

## 图8 `risk_themes_by_period`
- 建议图题：半年度风险主题构成
- 建议放置：正文
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v6`
- 数据口径：研究主库 `paper_scope_quality_v6` 正式口径；基于 `vw_posts_paper_scope_quality_v6` 的 `risk_themes_json` 字段按半年度聚合；风险类别按论文叙述优先顺序固定。
- 跳过说明：当前正式口径下该图所需结构化字段没有可绘制数据，保留登记但不作为本轮正式图件。

## 图9 `risk_themes_by_quarter`
- 建议图题：季度风险主题构成
- 建议放置：补充材料
- 状态：`skipped`
- 来源标签：`paper_scope_quality_v6`
- 数据口径：研究主库 `paper_scope_quality_v6` 正式口径；基于 `vw_posts_paper_scope_quality_v6` 的 `risk_themes_json` 字段按季度聚合；风险类别按论文叙述优先顺序固定。
- 跳过说明：当前正式口径下该图所需结构化字段没有可绘制数据，保留登记但不作为本轮正式图件。
