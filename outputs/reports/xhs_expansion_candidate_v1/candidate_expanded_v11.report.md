# candidate_expanded_v11 扩样报告

## 运行结论

小红书 live 搜索仍返回“安全限制”，公开搜索索引也没有稳定返回可用 XHS URL。因此本轮不继续 live 抓取，不绕过平台限制。

本轮扩展重点改为：保留 v10 的帖子候选池，并为候选帖导出本地已有公开评论 sidecar 上下文。评论 sidecar 只服务人工复核和语境判断，不属于 `quality_v5` 正式评论层，也不启动 `comment_review_v2`。

## 规模

- 帖子候选：5661 条。
- 实际带 `content_text` 上下文的帖子：3866 条。
- metadata-only 帖子：1795 条。
- sidecar 评论：78005 条。
- 有 sidecar 评论的候选帖：2567 条。
- `quality_v5` 正式帖子 / 评论：514 / 0。

## sidecar 评论层边界

- `formal_result_scope=false`。
- `quality_v5_formal_scope=false`。
- `comment_review_v2_scope=false`。
- 不写入正式数据库，不更新 freeze checkpoint，不改变 consistency report。

## 复核建议

优先处理有正文且有 sidecar 评论的候选帖，因为这些记录最适合判断话语情境、互动争议和边界协商线索。metadata-only 记录仍只能作为 URL 发现线索。
