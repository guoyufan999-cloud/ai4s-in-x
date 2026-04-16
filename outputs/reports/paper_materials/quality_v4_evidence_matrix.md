# quality_v4 投稿交付链证据矩阵

## 说明

- 本矩阵用于登记投稿版总稿中的核心数字、6 张正文图及其当前证据来源。
- 当前所有核心数字和正文图均以 `paper_scope_quality_v4` 为来源标签，即可由研究主库正式口径直接复现
- 当前正式核验接口：
  - `outputs/reports/freeze_checkpoints/research_db_summary.json`
  - `outputs/reports/freeze_checkpoints/quality_v4_consistency_report.json`
  - `outputs/reports/freeze_checkpoints/quality_v4_freeze_checkpoint.json`

## 一、核心数字

| 项目 | 当前值 | 主要位置 | 来源标签 | 直接接口 / 说明 |
|---|---:|---|---|---|
| 去重候选帖 | 5535 | 摘要、引言、方法 | `paper_scope_quality_v4` | `vw_scope_counts.candidate_posts`；已导出到 `research_db_summary.json` |
| 正式帖子 | 3067 | 摘要、引言、方法、结果 | `paper_scope_quality_v4` | `vw_scope_counts.paper_quality_v4_posts`；已导出到 `research_db_summary.json` 与一致性报告 |
| 正式评论 | 69880 | 摘要、引言、方法、结果 | `paper_scope_quality_v4` | `vw_scope_counts.paper_quality_v4_comments`；已导出到 `research_db_summary.json` 与一致性报告 |
| `uncertain_subject_share` | 23.77% | 摘要、引言、方法、结果、结论 | `paper_scope_quality_v4` | 以 `vw_posts_paper_scope_quality_v4` 中 `qs_broad_subject='uncertain'` 计算；当前冻结值记录于 `quality_v4_freeze_checkpoint.json` |
| `uncertain_workflow_share` | 14.18% | 摘要、引言、方法、结果、结论 | `paper_scope_quality_v4` | 以 `vw_posts_paper_scope_quality_v4` 中 `workflow_stage='uncertain'` 计算；当前冻结值记录于 `quality_v4_freeze_checkpoint.json` |
| `quality_v3 -> quality_v4` 帖子变化 | -526 | 方法 | `paper_scope_quality_v4` | `quality_v4_delta_report.md` |
| `quality_v3 -> quality_v4` 评论变化 | -6376 | 方法 | `paper_scope_quality_v4` | `quality_v4_delta_report.md` |
| `223` 自动回填 | 223 | 方法 | `paper_scope_quality_v4` | `quality_v4_method_limitations.md` 中的 round2 merged review 说明 |
| `194` 条移出主样本 | 194 | 方法 | `paper_scope_quality_v4` | `quality_v4_method_limitations.md` 中的边界收紧说明 |
| `queued` | 22 | 方法、限制 | `paper_scope_quality_v4` | `quality_v4_freeze_checkpoint.json` |
| `temporarily_unavailable_300031` | 43 | 方法、限制 | `paper_scope_quality_v4` | `quality_v4_method_limitations.md` / `quality_v4_freeze_checkpoint.json` |
| `formal_media_gap` | 2218 | 方法、限制 | `paper_scope_quality_v4` | 来自 legacy 媒体审计结果，已迁入研究主库正式视图 |

## 二、正文优先图

| 图号 | 文件 | 结果章节位置 | 来源标签 | 直接接口 / 说明 |
|---|---|---|---|---|
| 图1 | `posts_trend` | 3.1 | `paper_scope_quality_v4` | 基于 `vw_posts_paper_scope_quality_v4` 按月聚合，投稿图包已落到 `outputs/figures/paper_figures_submission/quality_v4/` |
| 图2 | `posts_by_quarter` | 3.1 | `paper_scope_quality_v4` | 基于 `vw_posts_paper_scope_quality_v4` 与 `vw_comments_paper_scope_quality_v4` 按季度聚合 |
| 图3 | `posts_heatmap` | 3.2 | `paper_scope_quality_v4` | 基于 `vw_posts_paper_scope_quality_v4` 的学科 × 流程 × 时间组合聚合 |
| 图4 | `comments_attitude` | 3.3 | `paper_scope_quality_v4` | 基于 `vw_comments_paper_scope_quality_v4` 的态度结构聚合 |
| 图5 | `tools_by_period` | 3.4 | `paper_scope_quality_v4` | 基于 `vw_posts_paper_scope_quality_v4` 的 `ai_tools_json` 字段按半年度聚合 |
| 图6 | `risk_themes_by_period` | 3.4 | `paper_scope_quality_v4` | 基于 `vw_posts_paper_scope_quality_v4` 的 `risk_themes_json` 字段按半年度聚合 |

## 三、正文段落来源约定

1. 摘要、引言、方法和结果中与样本规模、时间分布、学科分布、流程分布、评论态度相关的核心数字，统一以 `paper_scope_quality_v4` 为正式来源。
2. 结果章节 3.4 中关于工具生态与风险主题的图表与对应数字，已全部从研究主库正式口径复现，不再依赖 legacy 桥接。
3. 后续论文精修默认只在这套矩阵之内调整表述；若新增关键数字或新增正文图，必须先补登记再进入正文。
