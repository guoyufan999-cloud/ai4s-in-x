# xhs_expansion_candidate_v1 candidate_expanded_v7 报告

`candidate_expanded_v7` 是补充样本候选池，不是 `quality_v5` 正式结果，不构成论文发现。

## 1. 总量
- 合并去重后候选总量：`2665`
- 其中有正文/既有候选正文的记录：`1036`
- 仅搜索结果元数据、需人工补正文的记录：`1629`
- 本轮新增本地非 formal 研究主库候选：`780`
- quality_v5 guard：posts=`514`, comments=`0`

## 2. 来源构成
- candidate_expanded_v6: `1885`
- candidate_local_research_backlog_v1: `780`

## 3. 查询组分布
- G. 科研训练与效率类: `711`
- F. 科研规范与诚信类: `403`
- boundary: `298`
- D. 数据分析与代码类: `254`
- E. 论文写作与成果表达类: `252`
- B. 文献处理与知识整合类: `238`
- C. 研究设计与方法学习类: `228`
- A. AI科研总体类: `202`
- practice: `62`
- salience: `17`

## 4. 运行问题与处理
- 实时小红书搜索当前返回安全限制/空结果；已确认不是适配器选择器漂移，不应绕过风控。
- 本轮新增改用本地研究主库中已有公开、非 quality_v5 formal 的 full-text 记录，作为 supplemental candidate backlog。

## 5. 方法边界
- 不写入正式研究主库，不更新 freeze checkpoint，不改变 quality_v5 consistency report。
- local backlog 不是新实时采集，但可直接进入人工 supplemental review。
- search-index 记录仍必须补足公开正文后才可进入 supplemental formalization 或 quality_v6。
