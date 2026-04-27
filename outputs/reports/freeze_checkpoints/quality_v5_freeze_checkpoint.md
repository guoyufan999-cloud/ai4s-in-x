# QUALITY_V5 Freeze Checkpoint

- 当前状态：`post_review_v2_imported_post_only`
- 当前阶段：`quality_v5`
- 研究时间窗：`2024-01-01` 至 `2026-06-30`
- 正式覆盖截止日：`2026-04-10`
- 去重候选帖：`5535 / 5535`
- 正式帖子 / 正式评论：`514 / 0`
- 当前 queued：`5535`

## Rebaseline Note

- 当前 freeze 记录 active baseline 的帖子层正式主样本：`post_review_v2` strict reviewed runs 已导入主库。
- 本轮明确采用 post-only artifact refresh；`formal_comments=0` 是本轮设计选择，不是评论队列或导入遗漏。
- `comment_review_v2` 暂不进入正式编码，后续若启动需重新修正/生成正式评论复核队列。
- `quality_v4` 对应的 freeze、图表和论文材料继续保留为历史审计快照。

## Outputs

- Checkpoint JSON：`outputs/reports/freeze_checkpoints/quality_v5_freeze_checkpoint.json`
- Consistency JSON：`outputs/reports/freeze_checkpoints/quality_v5_consistency_report.json`
- 活跃图表目录：`outputs/figures/paper_figures_submission/quality_v5/`
- 工作稿索引：`docs/paper_working/README.md`（版本化保留，但不属于 freeze contract）

## Next Step

- `defer_comment_review_v2_or_prepare_future_comment_queue`
