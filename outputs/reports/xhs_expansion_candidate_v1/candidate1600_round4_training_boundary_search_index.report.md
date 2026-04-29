# candidate1600_round4_training_boundary_search_index 采集报告

本报告只描述 `xhs_expansion_candidate_v1` 的第四轮训练/边界定向候选池，不构成论文发现，不写入 `quality_v5` formal baseline，也不写入正式研究主库。

## 1. 运行摘要
- 执行查询词数量：`152` / `152`
- search_limit：`50`
- 新增 search-index 候选：`467`
- preliminary_decision：`review_needed`（全部需要人工打开公开页补正文与判断）
- quality_v5 guard：posts=`514`, comments=`0`

## 2. 查询组分布
- boundary: `253`
- G. 科研训练与效率类: `191`
- A. AI科研总体类: `23`

## 3. 高产查询词
- `AI不能替代思考`：hits=`16`, kept=`16`
- `AI科研路线图`：hits=`15`, kept=`14`
- `AI科研主体性`：hits=`17`, kept=`14`
- `AI不能替代阅读`：hits=`15`, kept=`14`
- `DeepSeek科研`：hits=`15`, kept=`14`
- `AI整理读书笔记`：hits=`15`, kept=`13`
- `AI署名边界`：hits=`17`, kept=`13`
- `AI幻觉怎么避免`：hits=`16`, kept=`12`
- `AI生成内容原创性`：hits=`15`, kept=`11`
- `AI论文答辩PPT`：hits=`15`, kept=`10`
- `AI写作边界`：hits=`16`, kept=`10`
- `AI科研边界感`：hits=`16`, kept=`10`
- `AI不能替代实验`：hits=`15`, kept=`10`
- `AI不能替代导师`：hits=`15`, kept=`10`
- `AI辅助判断`：hits=`16`, kept=`10`
- `AI科研模板`：hits=`16`, kept=`9`
- `AI开题报告模板`：hits=`16`, kept=`9`
- `AI辅助合法`：hits=`16`, kept=`9`
- `AI组会PPT`：hits=`15`, kept=`8`
- `AI做PPT科研`：hits=`15`, kept=`8`

## 4. 重复与跳过
- duplicate_previous_candidate: `517`
- duplicate_existing_db: `319`
- duplicate_current_run: `75`

## 5. 方法边界
- 本轮只保存公开搜索结果元数据，包括标题、URL、查询词组和去重信息。
- 未保存 cookie、登录态或非公开内容；未绕过验证码、登录、限流、风控或封禁机制。
- 所有候选必须在人工 review 中补充或确认 `content_text`，否则不能进入 supplemental formalization 或 quality_v6。
