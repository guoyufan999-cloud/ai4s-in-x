# quality_v6 论文主稿口径说明

## 采用口径

本文主稿采用 `quality_v6 post-only formalized result layer` 作为唯一当前投稿结果层。正式分析单位为帖子层正式结果，正式帖子为 `714` 条，正式评论为 `0` 条；`comment_review_v2` 继续 deferred，评论层材料不进入当前正式结论。

## 证据路径

1. `outputs/reports/paper_materials/paper_analysis_snapshot.md` 明确记录当前投稿结果层为 `quality_v6 post-only formalized result layer`，当前正式帖子 / 正式评论为 `714 / 0`，研究时间窗为 `2024-01-01` 至 `2026-06-30`，正式覆盖截止日为 `2026-04-26`。
2. `outputs/reports/paper_materials/quality_v6/README.md` 说明 v6 是独立 paper materials 目录，不覆盖 `quality_v5`，来源组合为 `quality_v5 514` + `supplemental_formalization_v1 200`，评论层为 `comment_review_v2 deferred`。
3. `outputs/reports/paper_materials/quality_v6/quality_v6_post_only_contract.md` 固定 `formal_source_contract=paper_scope_quality_v6`、`formal_posts/formal_comments=714/0`，并说明 v6 使用独立 staging DB，不修改 `data/processed/ai4s_legitimacy.sqlite3`。
4. `outputs/reports/paper_materials/quality_v6/paper_materials_manifest.json` 将 `formal_stage` 标为 `quality_v6`，并指向 v6 summary、consistency、figure、framework_v2 与 `outputs/tables/quality_v6/*` 表。
5. `outputs/reports/freeze_checkpoints/quality_v6_consistency_report.json` 显示 observed paper scope 为 `714 / 0`，与 checkpoint 差值为 `0`，status 为 `aligned`；同时保留 `quality_v5_guard=514/0`。
6. `outputs/reports/paper_materials/quality_v6/framework_v2/README.md` 与 `framework_v2_summary_tables.json` 显示 framework_v2 已 reviewed 正式帖子为 `714`，missing posts 为 `0`，framework_v2 coding complete 为 `true`。

## 与旧材料的冲突处理

`research_brief.md`、`analysis_plan.md`、`compliance_and_ethics.md` 已更新为当前边界：`quality_v6 714 / 0` 是投稿结果层，`quality_v5 514 / 0` 是工程 guard。`docs/paper_working/` 下多份旧工作稿仍保留 `quality_v5 514 / 0` 或 `quality_v4` 口径，这些历史稿件可作为研究问题、理论框架和章节结构参考，但不能作为当前投稿主稿的数据口径来源。

旧稿中涉及 `quality_v4` 的正式帖子、正式评论、评论区规范协商、工具生态扩散、候选样本规模等内容，不进入当前 `quality_v6` 主稿正式结论。`quality_v5` 在当前主稿中只作为前一冻结基线和工程 guard 出现，不写成当前投稿结果层。

## 写作边界

- 可以写入当前主稿：v6 帖子层样本结构、framework_v2 文本类型、实践位置、工作流环节、AI 介入方式、介入强度、规范评价、评价张力、正式规范参照、边界类型、边界机制和边界结果。
- 不写入当前正式结论：sidecar 评论、legacy 评论库、候选样本、未通过 supplemental formalization 的样本、quality_v4 历史审计统计、quality_v5 旧结果章数字。
- 方法表述应写为人工 reviewed 编码、reviewed payload / framework_v2 reviewed 补码、描述性统计与质性内容分析；不得写作双人独立人工编码、访谈、问卷或评论层正式分析。
