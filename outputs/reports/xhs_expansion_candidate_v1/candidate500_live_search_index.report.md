# candidate500_live_search_index 采集报告

本报告只描述 `xhs_expansion_candidate_v1` 的公开搜索结果候选池，不构成论文发现，不写入 `quality_v5` formal baseline，也不写入正式研究主库。

## 1. 运行摘要
- 查询词数量：`56`
- search_limit：`50`
- 新增 search-index 候选：`362`
- preliminary_decision：`review_needed`（全部需要人工打开公开页补正文与判断）
- quality_v5 guard：posts=`514`, comments=`0`

## 2. 查询组分布
- F. 科研规范与诚信类: `79`
- E. 论文写作与成果表达类: `77`
- D. 数据分析与代码类: `48`
- A. AI科研总体类: `47`
- G. 科研训练与效率类: `42`
- C. 研究设计与方法学习类: `38`
- B. 文献处理与知识整合类: `31`

## 3. 表现较好的查询词
- `AI论文修改`：hits=`17`, kept=`16`
- `AI检测`：hits=`17`, kept=`14`
- `AI4Research`：hits=`16`, kept=`12`
- `AI翻译文献`：hits=`16`, kept=`12`
- `AI辅助建模`：hits=`16`, kept=`12`
- `AI论文润色`：hits=`17`, kept=`12`
- `AI审稿`：hits=`15`, kept=`12`
- `AI结果解释`：hits=`16`, kept=`11`
- `AI投稿信`：hits=`15`, kept=`11`
- `AI科研诚信`：hits=`16`, kept=`11`
- `AI4S`：hits=`14`, kept=`10`
- `ChatGPT写论文`：hits=`16`, kept=`10`

## 4. 重复与跳过
- duplicate_existing_db: `276`
- duplicate_existing_candidate: `137`
- duplicate_current_run: `91`

## 5. 方法边界
- 本轮只保存公开搜索结果元数据，包括标题、URL、查询词组和去重信息。
- 未保存 cookie、登录态或非公开内容；未绕过验证码、登录、限流、风控或封禁机制。
- 因详情页直连会触发访问频繁/登录边界，本轮不把空正文候选伪装成正式样本。
- 所有候选必须在人工 review 中补充或确认 `content_text`，否则不能进入 supplemental formalization 或 quality_v6。

## 6. 下一步建议
- 先从本 search-index 候选池中按查询组抽样 80-120 条人工打开公开页补正文。
- 对能够稳定补正文的查询词再做第二轮 live body capture；不能补正文的只保留为发现线索。
- 不建议把 search-index 候选直接并入论文主结果。
