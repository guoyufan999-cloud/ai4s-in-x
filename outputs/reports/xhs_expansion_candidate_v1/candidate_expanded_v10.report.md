# candidate_expanded_v10 扩样报告

## 运行结论

live 小红书搜索仍处于“安全限制”状态，本轮没有绕过平台限制。扩样通过本地 legacy 公开采集库中的 OCR 文本完成。

## 合并后规模

- v10 候选池总量：5661 条。
- 实际 `content_text` 长度 >= 30 的上下文记录：3866 条。
- 仍为 metadata-only（`content_text` 少于 30 字）：1795 条。
- 本轮新增 OCR 候选：68 条。
- 本轮增强既有候选正文：40 条。
- `quality_v5` 正式帖子 / 评论：514 / 0。

## 来源分布

```json
{
  "candidate_expanded_v9_enriched_with_ocr": 5593,
  "candidate_legacy_media_ocr_backlog_v1": 68
}
```

## 使用限制

`candidate_expanded_v10` 仍是 supplemental candidate，不是正式论文结果。OCR 文本可用于人工筛选和正文补足，但必须核验噪声，不自动填 F/G/H/I/J/K，也不写入正式数据库。
