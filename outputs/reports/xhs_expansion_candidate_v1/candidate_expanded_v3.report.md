# xhs_expansion_candidate_v1 candidate_expanded_v3 报告

`candidate_expanded_v3` 是补充样本候选池，不是 `quality_v5` 正式结果，不构成论文发现。

## 1. 总量
- 合并去重后候选总量：`618`
- 其中有正文/既有候选正文的记录：`256`
- 仅搜索结果元数据、需人工补正文的记录：`362`
- quality_v5 guard：posts=`514`, comments=`0`

## 2. 来源构成
- candidate500_live_search_index: `362`
- candidate_expanded_v2: `256`

## 3. 查询组分布
- B. 文献处理与知识整合类: `88`
- A. AI科研总体类: `87`
- F. 科研规范与诚信类: `79`
- E. 论文写作与成果表达类: `77`
- C. 研究设计与方法学习类: `75`
- practice: `62`
- D. 数据分析与代码类: `59`
- G. 科研训练与效率类: `42`
- boundary: `32`
- salience: `17`

## 4. 排除情况
- candidate500_live_sidecar:invalid_or_login_url: `1`

## 5. 方法边界
- 不写入正式研究主库，不更新 freeze checkpoint，不改变 quality_v5 consistency report。
- `search_result_metadata_only` 记录只能作为人工复核线索；必须补足公开正文后才可进入 supplemental formalization 或 quality_v6。
- 当前最合适的下一步是按查询组分层抽样 review 80-120 条，优先补正文而不是继续盲目扩大。
