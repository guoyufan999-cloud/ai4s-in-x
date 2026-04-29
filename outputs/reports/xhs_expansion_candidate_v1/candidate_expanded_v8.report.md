# candidate_expanded_v8 扩样报告

## 运行结论

本轮没有继续对小红书 live 页面做高频重试。OpenCLI 搜索会话可连接，但搜索页只读检查返回“安全限制”，因此本轮不修 adapter、不绕过登录/验证码/风控机制，改用本地既有公开研究主库生成更高召回的补充候选集。

## 新增候选集

- 新增本地 broad backlog：2900 条。
- 其中已有正文上下文：2805 条。
- 缺失或不确定发帖日期：87 条，人工 review 时需优先核验。
- 合并后 v8 候选池总量：5565 条。
- 合并后已有正文上下文：3841 条。
- 合并后仍仅为搜索索引元数据：1629 条。

## 查询组分布

```json
{
  "A. AI科研总体类": 590,
  "B. 文献处理与知识整合类": 602,
  "C. 研究设计与方法学习类": 305,
  "D. 数据分析与代码类": 1780,
  "E. 论文写作与成果表达类": 370,
  "F. 科研规范与诚信类": 593,
  "G. 科研训练与效率类": 948,
  "boundary": 298,
  "practice": 62,
  "salience": 17
}
```

## 来源分布

```json
{
  "candidate_expanded_v7": 2665,
  "candidate_local_broad_backlog_v1": 2900
}
```

## 边界说明

- 本报告和 JSONL 均属于 `xhs_expansion_candidate_v1` supplemental candidate。
- 未写入 `data/processed/ai4s_legitimacy.sqlite3` 的正式范围。
- 未启动 `comment_review_v2`。
- 未修改 `quality_v5` freeze checkpoint 或 consistency report。
- `quality_v5` guard count 仍为帖子 / 评论：514 / 0。

## 人工复核建议

优先复核 `body_fetch_status=body_present_from_existing_research_db` 且 `date_window_status=in_requested_window` 的记录。`candidate_local_broad_backlog_v1` 是高召回扩展，噪声会高于 v7，不能直接解释为论文发现。
