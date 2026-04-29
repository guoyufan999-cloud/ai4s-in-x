# xhs_expansion_candidate_v1 candidate_expanded_v4 报告

`candidate_expanded_v4` 是补充样本候选池，不是 `quality_v5` 正式结果，不构成论文发现。

## 1. 总量
- 合并去重后候选总量：`1118`
- 其中有正文/既有候选正文的记录：`256`
- 仅搜索结果元数据、需人工补正文的记录：`862`
- 本轮新增 round2 search-index：`500`
- quality_v5 guard：posts=`514`, comments=`0`

## 2. 来源构成
- candidate_expanded_v3: `618`
- candidate1000_round2_search_index: `500`

## 3. 查询组分布
- B. 文献处理与知识整合类: `207`
- E. 论文写作与成果表达类: `199`
- D. 数据分析与代码类: `197`
- C. 研究设计与方法学习类: `196`
- A. AI科研总体类: `87`
- F. 科研规范与诚信类: `79`
- practice: `62`
- G. 科研训练与效率类: `42`
- boundary: `32`
- salience: `17`

## 4. 方法边界
- 不写入正式研究主库，不更新 freeze checkpoint，不改变 quality_v5 consistency report。
- `search_result_metadata_only` 记录只能作为人工复核线索；必须补足公开正文后才可进入 supplemental formalization 或 quality_v6。
- 下一步建议按查询组分层抽样 120-180 条补正文；优先处理 F 规范诚信、D 数据分析、G 科研训练和 E 写作表达。
