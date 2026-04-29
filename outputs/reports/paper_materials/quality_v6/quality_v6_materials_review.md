# quality_v6 Materials Review

## Review Decision

`quality_v6` 已可作为当前论文主结果层；本轮已新增并修订独立的 v6 clean 主稿，不直接覆盖前一轮 clean 主稿。

当前 v6 数据契约已经成立，`outputs/reports/paper_materials/paper_master_manuscript_quality_v6_submission_cn_clean.md` 已吸收 v6 的方法说明、结果表述、边界说明、基础外部文献引用和正文统计表。前一轮 `paper_master_manuscript_submission_cn_clean.md` 可继续作为历史短稿保留，但不再作为 v6 主稿的唯一入口。

## Evidence Checked

- `outputs/reports/freeze_checkpoints/quality_v6_consistency_report.json`
- `outputs/reports/freeze_checkpoints/quality_v6_research_db_summary.json`
- `outputs/reports/paper_materials/quality_v6/paper_materials_manifest.json`
- `outputs/reports/paper_materials/quality_v6/paper_results_chapter_quality_v6.md`
- `outputs/reports/paper_materials/quality_v6/paper_methods_transparency_appendix_quality_v6.md`
- `outputs/reports/paper_materials/quality_v6/framework_v2/framework_v2_summary_tables.json`
- `outputs/reports/paper_materials/quality_v6/framework_v2/cross_tabs_v2.json`
- `outputs/reports/paper_materials/paper_master_manuscript_quality_v6_submission_cn_clean.md`
- `docs/paper_working/quality_v6_source_of_truth_note.md`

## Positive Findings

- v6 consistency 已对齐：正式帖子 / 正式评论为 `714 / 0`。
- v5 guard 保持不变：`quality_v5` 仍为 `514 / 0`，未被 v6 staging DB 覆盖。
- v6 来源组合清楚：`quality_v5 514` + `supplemental_formalization_v1 200`。
- 评论层边界清楚：`comment_review_v2` 仍为 deferred，sidecar comments 未进入正式结果。
- framework_v2 在 v6 范围内显示 `714` 条正式帖已 reviewed，missing posts 为 `0`。
- v6 第五章/第六章所需的 F/G/H/I/J/K 分布和交叉表已经非空，可支撑结果层写作。

## Switch Risks

- 前一轮 `paper_master_manuscript_submission_cn_clean.md`、分章 clean 版和方法透明度 clean 版仍保留前一冻结基线说明；当前 v6 clean 主稿应优先使用 `paper_master_manuscript_quality_v6_submission_cn_clean.md`。
- v6 方法附录目前是透明度摘要，尚未充分展开补充样本的采集、预筛、formalization、排除 6 条、风险复核和 staging DB 策略。
- v6 结果章目前是材料表摘要，不是完整论文结果章节；需要把第四章、第五章、第六章的叙述段落补齐。
- framework_v2 的部分表是 code occurrence / claim-unit occurrence，不是 post-level count；主稿切换时必须明确计数单位，避免把多选编码次数误读为帖子数。
- v6 中仍有 `uncoded` / `uncertain` 项，例如科研活动场域 `uncoded=32`、工作流环节 `uncertain=32`、学科宽口径 `uncertain=485`。这些可以保留，但主稿必须解释其来源与限制。
- v6 framework README 提到 audit report 可由 builder 生成，但当前 v6 framework 目录未包含单独的 v6 coding audit report；若主稿正式切换，建议补一份 v6 coding audit/limitations memo。

## Decision

不建议原地覆盖前一轮 clean 主稿；建议以独立 v6 clean 主稿作为当前投稿主稿入口。

本轮已完成的集成项：

1. 新增 `quality_v6` 版 clean 主稿。
2. 在主稿中明确 `quality_v6 714 / 0` 是新的 post-only 正式结果层，`quality_v5 514 / 0` 是前一冻结基线。
3. 将第四章使用 v6 的话语情境、实践位置和工作流分布。
4. 将第五章使用 v6 的 F/G/H/I 与 B/C 统计，并注明多选编码的计数单位。
5. 将第六章使用 v6 的 D/J/K 统计，并衔接边界协商机制。
6. 保留评论层 deferred 的边界表述，不把 sidecar comments 写入正式结论。
7. 补入基础外部文献引用、参考文献表和正文统计表。

仍建议后续补充 `quality_v6` coding audit / limitations memo，并按导师或期刊要求扩展中文社交媒体和小红书平台文献。

## Bottom Line

`quality_v6` 可以作为当前主结果层。当前优先入口为 `paper_master_manuscript_quality_v6_submission_cn_clean.md`；后续重点是方法审计补充、参考文献格式统一和期刊格式排版。
