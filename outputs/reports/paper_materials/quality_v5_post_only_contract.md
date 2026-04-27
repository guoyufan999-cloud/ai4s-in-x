# quality_v5 Post-Only Contract

- 当前正式基线：`quality_v5 正式重建基线`
- 研究时间窗：`2024-01-01` 至 `2026-06-30`
- 正式覆盖截止日：`2026-04-10`
- 当前状态：`post_review_v2_imported_post_only`
- 当前正式帖子 / 正式评论：`514 / 0`
- 当前 canonical corpus：帖子 `5535` 条，评论 `12362` 条

这个文件记录 active baseline 的 post-only 合同状态。当前 canonical 主线已经完成数据库升级、rescreen 回灌、严格版 `post_review_v2` 导入、summary / consistency / canonical corpus 重建。
本轮正式基线接受帖子层 post-only 口径；`comment_review_v2` 暂不进入正式编码，`formal_comments=0` 是设计选择，不是导入遗漏。

- 活跃 summary：`outputs/reports/freeze_checkpoints/research_db_summary.json`
- 活跃 consistency：`outputs/reports/freeze_checkpoints/quality_v5_consistency_report.json`
- canonical corpus 帖子：`outputs/tables/post_review_v2_master.jsonl`
- canonical corpus 评论：`outputs/tables/comment_review_v2_master.jsonl`
- backfill contract：`docs/canonical_backfill_contract.md`
