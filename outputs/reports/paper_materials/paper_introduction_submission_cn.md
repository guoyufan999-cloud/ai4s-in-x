# 投稿引言（quality_v5 active）

- 当前正式基线：`quality_v5 正式重建基线`
- 研究时间窗：`2024-01-01` 至 `2026-06-30`
- 正式覆盖截止日：`2026-04-10`
- 当前状态：`post_review_v2_imported_post_only`
- 当前正式帖子 / 正式评论：`514 / 0`
- 当前 canonical corpus：帖子 `5535` 条，评论 `12362` 条

当前活跃交付链已经切到 `quality_v5`。本轮正式基线采用帖子层 post-only 口径：严格版 `post_review_v2` 已导入，正式帖子为 `514` 条；`comment_review_v2` 暂不进入正式编码，因此正式评论为 `0`。`formal_comments=0` 是本轮设计选择，不是评论队列或导入遗漏；`quality_v4` 仅作为历史审计快照保留。
当前更重要的工作不是扩样，而是维护 post-only 正式基线与 artifacts 一致性；后续若需要评论层结果，应单独启动 `comment_review_v2` 工作流。
