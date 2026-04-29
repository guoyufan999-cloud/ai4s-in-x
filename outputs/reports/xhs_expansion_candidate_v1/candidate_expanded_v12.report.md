# candidate_expanded_v12 扩样报告

## 运行结论

小红书 live 搜索仍返回“安全限制”。本轮未继续重试，也未绕过平台限制。

本轮只从 `quality_v5` rebaseline 的 `promoted_groups` 建议文件中抽取未进入 v11、且文本同时命中 AI 与科研活动的高信号候选。它们不是正式结果，全部进入 supplemental candidate review queue。

## 规模

- v12 帖子候选：5677 条。
- 本轮新增 promoted candidate：16 条。
- 实际带 `content_text` 上下文：3882 条。
- metadata-only：1795 条。
- sidecar 评论总量：78133 条。
- 本轮新增 sidecar 评论：128 条。
- `quality_v5` 正式帖子 / 评论：514 / 0。

## 边界

- `quality_v5_formal_scope=false`。
- `formal_scope=false`。
- `comment_review_v2_changed=false`。
- 不写入主库，不更新 freeze checkpoint，不自动填正式编码。

## 建议

继续扩“数量”的收益已经很低，下一步应改为复核 v12：优先处理新增 promoted candidates 和已有正文+sidecar 评论的候选帖。
