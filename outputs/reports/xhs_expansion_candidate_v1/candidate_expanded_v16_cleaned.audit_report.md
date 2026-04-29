# xhs_expansion_candidate_v1 expanded_v16 cleaned audit report

本报告记录对 `candidate_expanded_v15` 的数据质量检查与修复。所有输出仍为 supplemental candidate，不写入研究主库，不进入 `quality_v5` formal baseline。

## Scope Guard

- source_scope: `xhs_expansion_candidate_v1`
- input artifact: `outputs/tables/xhs_expansion_candidate_v1/candidate_expanded_v15.jsonl`
- cleaned artifact: `outputs/tables/xhs_expansion_candidate_v1/candidate_expanded_v16_cleaned.jsonl`
- quality_v5 formal posts/comments: `514 / 0`
- comment_review_v2: 未启动

## 主要问题与修复

- 旧批次非标准 query_group 已重分类为 A-G：`377` 条。
- search_result 或带临时参数 URL 已规范化为 `/explore/{note_id}`：`1886` 条。
- 含 `xsec/token/query` 风险的 URL 已从行内和 raw payload 中移除：`1886` 条。
- 已存在于研究主库的候选标记为 `duplicate_existing_post_in_research_db_nonformal_or_formal` 并预设剔除：`4336` 条。
- 正文少于 80 字的候选预设剔除：`2215` 条。

## 清洗后规模

- candidate rows: `6221`
- sidecar comments: `90027`
- review queue rows: `6221`
- review template rows: `6221`

## 清洗后 query_group 分布

- `D. 数据分析与代码类`: `1951`
- `G. 科研训练与效率类`: `977`
- `F. 科研规范与诚信类`: `901`
- `B. 文献处理与知识整合类`: `894`
- `A. AI科研总体类`: `763`
- `E. 论文写作与成果表达类`: `398`
- `C. 研究设计与方法学习类`: `337`

## 校验结果

- duplicate_candidate_ids: `0`
- duplicate_note_ids: `0`
- bad_query_group_rows: `0`
- bad_or_tokenized_url_rows: `6`
- bad_post_formal_flags: `0`
- bad_comment_formal_flags: `0`
- missing_post_url: `0`
- missing_query_group: `0`

## 编码流程入口

- review queue: `data/interim/xhs_expansion_candidate_v1/review_queues/xhs_expansion_candidate_v1.expanded_v16_cleaned.review_queue.jsonl`
- review template: `data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.expanded_v16_cleaned.review_template.jsonl`

后续 `codex_assisted_review` 只用于 supplemental staging，不是 `quality_v5` 正式人工编码。


## 二次清洗补记

- 页面 chrome/备案样板文本清理：`6` 条 content_text，`6` 条 raw source_text。
- 二次清洗后正文少于 80 字并预设剔除：`2221` 条。
- 二次清洗后 tokenized/search_result URL 行数：`0`。

## 队列决策与匿名字段修复

- author_name_masked 统一置空或移除 raw 作者名字段。
- preliminary_decision 已规范为 `include/exclude`：`{'prelim_include': 231, 'prelim_exclude': 5990}`。
- codex-assisted reviewed 输出：`data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.expanded_v16_cleaned.codex_reviewed.jsonl`。

## 作者字段同步修复

- candidate JSONL 的 `author_name_masked` 已统一置为 `null`。
- raw payload 中显式作者名字段已移除。
