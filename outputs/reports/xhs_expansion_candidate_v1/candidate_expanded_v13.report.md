# candidate_expanded_v13 扩样报告

## 运行结论

小红书 live 搜索仍返回“安全限制”，本轮未继续重试，也未绕过平台限制。

本轮从已存在的 reviewed/priority rebaseline 文本产物中做严格增量抽取：只看原帖文本、标题、主题与关键词，不使用模型解释字段触发召回，并排除已判定“剔除”的记录。

## 规模

- v13 帖子候选：5680 条。
- 本轮新增 reviewed/priority 候选：3 条。
- 实际带 `content_text` 上下文：3885 条。
- metadata-only：1795 条。
- sidecar 评论总量：78177 条。
- 本轮新增 sidecar 评论：44 条。
- `quality_v5` 正式帖子 / 评论：514 / 0。

## 判断

可追溯本地增量已经基本耗尽。继续“扩数量”会显著增加噪声；建议转入 v13 分层人工复核，或等待小红书 live 访问恢复后再开新一轮 live candidate。
