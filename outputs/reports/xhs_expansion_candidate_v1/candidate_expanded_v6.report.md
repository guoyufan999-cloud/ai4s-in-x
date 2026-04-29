# xhs_expansion_candidate_v1 candidate_expanded_v6 报告

`candidate_expanded_v6` 是补充样本候选池，不是 `quality_v5` 正式结果，不构成论文发现。

## 1. 总量
- 合并去重后候选总量：`1885`
- 其中有正文/既有候选正文的记录：`256`
- 仅搜索结果元数据、需人工补正文的记录：`1629`
- 本轮新增 round4 训练/边界 search-index：`467`
- round4 后段 soft-zero 查询数：`63`
- quality_v5 guard：posts=`514`, comments=`0`

## 2. 来源构成
- candidate_expanded_v5: `1418`
- candidate1600_round4_training_boundary_search_index: `467`

## 3. 查询组分布
- F. 科研规范与诚信类: `353`
- boundary: `285`
- G. 科研训练与效率类: `259`
- B. 文献处理与知识整合类: `207`
- E. 论文写作与成果表达类: `199`
- D. 数据分析与代码类: `197`
- C. 研究设计与方法学习类: `196`
- A. AI科研总体类: `110`
- practice: `62`
- salience: `17`

## 4. 运行问题与处理
- 第四轮前半段正常产出，后半段小红书 OpenCLI search 连续返回空数组；`AI论文润色` 烟测同样返回空，判定为会话/平台软失败。
- 未绕过安全验证或风控；Google/Bing 公共索引 fallback 未取得可用小红书结果。
- 已保留 467 条有效新增候选，尾部 0 命中只作为运行限制记录，不作为研究发现。

## 5. 方法边界
- 不写入正式研究主库，不更新 freeze checkpoint，不改变 quality_v5 consistency report。
- `search_result_metadata_only` 记录只能作为人工复核线索；必须补足公开正文后才可进入 supplemental formalization 或 quality_v6。
- 下一步建议等小红书会话恢复后再补跑 round4 的 0-hit 尾部查询；当前更应先对 G/boundary/F 做分层人工补正文。
