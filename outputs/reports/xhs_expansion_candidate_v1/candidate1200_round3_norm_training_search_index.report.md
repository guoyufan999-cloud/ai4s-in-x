# candidate1200_round3_norm_training_search_index 采集报告

本报告只描述 `xhs_expansion_candidate_v1` 的第三轮规范/训练定向候选池，不构成论文发现，不写入 `quality_v5` formal baseline，也不写入正式研究主库。

## 1. 运行摘要
- 执行查询词数量：`48` / `88`
- search_limit：`50`
- 新增 search-index 候选：`300`
- preliminary_decision：`review_needed`（全部需要人工打开公开页补正文与判断）
- quality_v5 guard：posts=`514`, comments=`0`

## 2. 查询组分布
- F. 科研规范与诚信类: `274`
- G. 科研训练与效率类: `26`

## 3. 高产查询词
- `维普AIGC检测`：hits=`16`, kept=`15`
- `AI审稿伦理`：hits=`17`, kept=`14`
- `AIGC检测率`：hits=`15`, kept=`13`
- `期刊AI政策`：hits=`16`, kept=`13`
- `格子达AI检测`：hits=`14`, kept=`13`
- `Turnitin AI论文检测`：hits=`15`, kept=`12`
- `AI检测论文怎么办`：hits=`16`, kept=`11`
- `导师不让用ChatGPT`：hits=`16`, kept=`11`
- `论文AI使用说明`：hits=`17`, kept=`10`
- `AI生成参考文献 幻觉`：hits=`16`, kept=`10`
- `博士DeepSeek写论文`：hits=`17`, kept=`9`
- `AI写论文 学术诚信`：hits=`18`, kept=`8`
- `AI生成内容检测论文`：hits=`15`, kept=`8`
- `知网AIGC检测`：hits=`15`, kept=`8`
- `AIGC论文披露`：hits=`17`, kept=`7`
- `DeepSeek 瞎编文献`：hits=`17`, kept=`7`
- `学校禁止AI写论文`：hits=`18`, kept=`7`
- `论文降AI率`：hits=`18`, kept=`7`
- `ChatGPT润色要披露吗`：hits=`14`, kept=`7`
- `AI论文披露要求`：hits=`18`, kept=`6`

## 4. 重复与跳过
- duplicate_previous_candidate: `232`
- duplicate_existing_db: `167`
- duplicate_current_run: `50`

## 5. 方法边界
- 本轮只保存公开搜索结果元数据，包括标题、URL、查询词组和去重信息。
- 未保存 cookie、登录态或非公开内容；未绕过验证码、登录、限流、风控或封禁机制。
- 所有候选必须在人工 review 中补充或确认 `content_text`，否则不能进入 supplemental formalization 或 quality_v6。
