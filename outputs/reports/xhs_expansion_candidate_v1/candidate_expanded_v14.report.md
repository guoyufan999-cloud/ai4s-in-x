# candidate_expanded_v14 扩样报告

## 运行结论

小红书 live 搜索仍为“安全限制”，本轮未继续重试，也未绕过平台限制。

本轮没有新增帖子 URL，而是使用 macOS Vision 对 v13 中少数 metadata-only 候选的本地公开媒体文件进行 OCR，补足可人工核验的正文上下文。

## 规模

- v14 帖子候选：5680 条。
- 新增帖子 URL：0 条。
- OCR 聚合候选：6 条。
- OCR 通过 AI+科研过滤：2 条。
- 本轮补正文候选：2 条。
- 带 `content_text` 上下文：3887 条。
- metadata-only：1793 条。
- sidecar 评论：78177 条。
- `quality_v5` 正式帖子 / 评论：514 / 0。

## 边界

OCR 文本噪声较高，必须人工核验公开媒体图像后才能用于正式纳入判断。v14 仍是 supplemental candidate，不写入主库、不更新 freeze checkpoint、不启动正式评论层。
