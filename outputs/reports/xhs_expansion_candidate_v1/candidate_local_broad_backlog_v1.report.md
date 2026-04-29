# candidate_local_broad_backlog_v1 生成说明

本文件从 `data/processed/ai4s_legitimacy.sqlite3:posts` 中抽取未进入 `quality_v5` 正式 514 条、也未进入 `candidate_expanded_v7` 的公开记录。筛选逻辑是标题、正文、原查询词或已有主题字段同时命中 AI 相关词与科研/学术活动相关词。

## 统计

- 输出候选：2900 条。
- 有正文上下文：2805 条。
- 缺失或不确定日期：87 条。
- 正式 guard：514 / 0。

## skipped counts

```json
{
  "already_in_candidate_expanded_v7": 780,
  "keyword_filter_not_ai_research": 1335,
  "outside_requested_date_window": 6,
  "quality_v5_formal_post": 514
}
```

## 查询组分布

```json
{
  "A. AI科研总体类": 388,
  "B. 文献处理与知识整合类": 364,
  "C. 研究设计与方法学习类": 77,
  "D. 数据分析与代码类": 1526,
  "E. 论文写作与成果表达类": 118,
  "F. 科研规范与诚信类": 190,
  "G. 科研训练与效率类": 237
}
```

## 使用限制

该批次是补充候选集，不是正式样本。所有记录默认 `review_needed`，人工 review 前不得写成论文结果。
