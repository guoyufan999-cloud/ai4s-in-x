# candidate1000_round2_search_index 采集报告

本报告只描述 `xhs_expansion_candidate_v1` 的第二轮公开搜索结果候选池，不构成论文发现，不写入 `quality_v5` formal baseline，也不写入正式研究主库。

## 1. 运行摘要
- 执行查询词数量：`80` / `122`
- search_limit：`50`
- 新增 search-index 候选：`500`
- preliminary_decision：`review_needed`（全部需要人工打开公开页补正文与判断）
- quality_v5 guard：posts=`514`, comments=`0`

## 2. 查询组分布
- D. 数据分析与代码类: `138`
- E. 论文写作与成果表达类: `122`
- C. 研究设计与方法学习类: `121`
- B. 文献处理与知识整合类: `119`

## 3. 高产查询词
- `DeepSeek 论文润色`：hits=`17`, kept=`16`
- `DeepSeek 论文修改`：hits=`16`, kept=`15`
- `Cursor 科研代码`：hits=`15`, kept=`13`
- `ChatGPT 论文修改`：hits=`18`, kept=`13`
- `AI问卷量表`：hits=`15`, kept=`12`
- `Cursor 数据分析`：hits=`17`, kept=`12`
- `Cursor 论文代码`：hits=`16`, kept=`11`
- `AI绘制论文图表`：hits=`17`, kept=`11`
- `AI回复审稿意见`：hits=`14`, kept=`11`
- `ChatGPT 论文润色`：hits=`16`, kept=`10`
- `AI投稿信`：hits=`15`, kept=`10`
- `DeepSeek 文献综述`：hits=`17`, kept=`9`
- `Kimi 文献综述`：hits=`16`, kept=`9`
- `ChatGPT 问卷设计`：hits=`18`, kept=`9`
- `DeepSeek 问卷设计`：hits=`15`, kept=`9`
- `DeepSeek 统计分析`：hits=`15`, kept=`9`
- `AI统计建模`：hits=`12`, kept=`9`
- `NotebookLM 文献综述`：hits=`14`, kept=`8`
- `NotebookLM 论文总结`：hits=`17`, kept=`8`
- `DeepSeek 访谈提纲`：hits=`14`, kept=`8`

## 4. 重复与跳过
- duplicate_existing_db: `329`
- duplicate_previous_candidate: `293`
- duplicate_current_run: `131`

## 5. 方法边界
- 本轮只保存公开搜索结果元数据，包括标题、URL、查询词组和去重信息。
- 未保存 cookie、登录态或非公开内容；未绕过验证码、登录、限流、风控或封禁机制。
- 所有候选必须在人工 review 中补充或确认 `content_text`，否则不能进入 supplemental formalization 或 quality_v6。
