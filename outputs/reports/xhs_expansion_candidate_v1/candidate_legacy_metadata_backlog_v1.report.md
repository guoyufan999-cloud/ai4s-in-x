# candidate_legacy_metadata_backlog_v1 生成说明

本批次从 legacy 运行库 `note_candidates` 中抽取未进入 `quality_v5`、也未进入 `candidate_expanded_v8` 的候选记录。由于当前 live 小红书页面返回“安全限制”，本轮未继续 live 抓取，也未绕过平台限制。

## 统计

- 输出候选：28 条。
- 折叠的 legacy source rows：28 行。
- 有正文上下文：0 条。
- 元数据-only：28 条。
- 正式 guard：514 / 0。

## 查询组分布

```json
{
  "A. AI科研总体类": 3,
  "B. 文献处理与知识整合类": 2,
  "C. 研究设计与方法学习类": 3,
  "D. 数据分析与代码类": 3,
  "G. 科研训练与效率类": 17
}
```

## 限制

这些记录只有标题、URL、查询词和来源元数据，不能直接解释为正式研究样本。人工 review 必须打开公开页面确认正文、日期与研究相关性。
