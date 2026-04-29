# 方法透明度与补充材料说明（quality_v6 active submission）

- 当前投稿结果层：`quality_v6 post-only formalized result layer`
- 前一冻结基线：`quality_v5 post-only 514 / 0`
- 研究时间窗：`2024-01-01` 至 `2026-06-30`
- 正式覆盖截止日：`2026-04-26`
- 当前状态：`post_only_formalized`
- 当前正式帖子 / 正式评论：`714 / 0`
- 当前 v6 staging research DB：帖子 `5735` 条，评论 `106543` 条

## 样本链路

`quality_v6` 是新的帖子层正式结果层：`quality_v5` 前一冻结基线的 514 条正式帖子，与 `xhs_expansion_candidate_v1` 中经 `supplemental_formalization_v1` 人工/方法审计通过的 200 条补充帖子合并。补充 formalization 前有 206 条候选进入最终复核，其中 200 条 include，6 条 exclude；excluded 记录不进入 `paper_scope_quality_v6`。

## 数据库与视图边界

v6 使用 `data/interim/quality_v6/ai4s_legitimacy_quality_v6.sqlite3` 作为 staging DB，并通过 `vw_posts_paper_scope_quality_v6` 与 `vw_comments_paper_scope_quality_v6` 表达正式范围。`vw_posts_paper_scope_quality_v6` 为 714 条，`vw_comments_paper_scope_quality_v6` 为 0 条。该链路不写回 `data/processed/ai4s_legitimacy.sqlite3` 的 `quality_v5` freeze checkpoint，也不更改 `quality_v5_consistency_report.json`。

## 编码与统计边界

v6 主稿采用 framework v2 五层框架：话语情境、实践位置、介入方式、规范评价、边界生成。A/B/C/D 作为旧框架兼容层继续使用，F/G/H/I/J/K 已完成 714 条帖子覆盖。帖子级表用于描述样本分布；claim unit 表和多选代码表用于描述编码出现结构，合计可能大于正式帖子数。

## 评论层与合规边界

`comment_review_v2` 继续 deferred，sidecar 评论不进入正式结果。`formal_comments=0` 是本轮方法设计，不是评论缺失。研究主线仍遵守公开可获取材料、作者匿名化、只读采集、不绕过登录/验证码/风控/限流/封禁机制的边界。

## 可复核材料

- v6 paper materials：`outputs/reports/paper_materials/quality_v6/`
- v6 framework v2 materials：`outputs/reports/paper_materials/quality_v6/framework_v2/`
- v6 freeze checkpoint：`outputs/reports/freeze_checkpoints/quality_v6_freeze_checkpoint.json`
- v6 consistency report：`outputs/reports/freeze_checkpoints/quality_v6_consistency_report.json`
- v6 figure manifest：`outputs/figures/paper_figures_submission/quality_v6/paper_figures_submission_manifest.md`
