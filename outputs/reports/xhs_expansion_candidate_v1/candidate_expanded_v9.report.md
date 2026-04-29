# candidate_expanded_v9 扩样报告

## 运行结论

本轮 OpenCLI 会话正常，但小红书搜索页只读检查仍返回“安全限制”。因此没有修 adapter，也没有绕过登录、验证码、风控或限流机制。扩样通过本地已有公开 legacy `note_candidates` 元数据完成。

## 合并后规模

- v9 候选池总量：5593 条。
- 已有正文上下文：3841 条。
- 搜索索引或 legacy 元数据-only：1657 条。
- 本轮新增 legacy metadata 候选：28 条。
- `quality_v5` 正式帖子 / 正式评论：514 / 0。

## 来源分布

```json
{
  "candidate_expanded_v8": 5565,
  "candidate_legacy_metadata_backlog_v1": 28
}
```

## 查询组分布

```json
{
  "A. AI科研总体类": 593,
  "B. 文献处理与知识整合类": 604,
  "C. 研究设计与方法学习类": 308,
  "D. 数据分析与代码类": 1783,
  "E. 论文写作与成果表达类": 370,
  "F. 科研规范与诚信类": 593,
  "G. 科研训练与效率类": 965,
  "boundary": 298,
  "practice": 62,
  "salience": 17
}
```

## 人工复核优先级

1. 先复核已有正文上下文的 3841 条，优先判断 include/exclude。
2. 对 legacy metadata-only 记录，只作为发现线索；人工打开公开页面补正文后再决定是否纳入。
3. 不把 v9 直接写入论文发现，也不写入 `quality_v5` formal baseline。
