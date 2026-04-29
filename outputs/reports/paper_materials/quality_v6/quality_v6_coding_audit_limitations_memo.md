# quality_v6 编码审计与局限说明 memo

## 用途

本 memo 记录当前 quality_v6 投稿层的最终可信度检查。它服务于论文写作和投稿前说明，不替代逐条语义复核。

## 范围

- 正式阶段：`quality_v6`
- 正式帖子 / 正式评论：`714 / 0`
- 来源组合：`quality_v5 514` + `supplemental_formalization_v1 200`
- 评论层：`comment_review_v2` 仍作为后续独立工作流处理
- 当前主稿入口：`outputs/reports/paper_materials/paper_master_manuscript_quality_v6_submission_cn_clean.md`

## 已核验证据

- `outputs/reports/freeze_checkpoints/quality_v6_consistency_report.json`
- `outputs/reports/freeze_checkpoints/quality_v6_research_db_summary.json`
- `outputs/reports/paper_materials/quality_v6/paper_materials_manifest.json`
- `outputs/reports/paper_materials/quality_v6/framework_v2/framework_v2_summary_tables.json`
- `outputs/reports/paper_materials/quality_v6/framework_v2/cross_tabs_v2.json`
- `outputs/reports/paper_materials/quality_v6/quality_v6_materials_review.md`

## 审计结论

- 数量一致性已对齐：freeze checkpoint 与论文口径均为 `714` 条正式帖子、`0` 条正式评论。
- `quality_v5` guard 仍保持 `514 / 0`，v6 staging 层未覆盖前一冻结基线。
- framework_v2 覆盖当前 post-only 层：`714` 条帖子已复核，missing posts 为 `0`，v6 summary tables 显示 coding complete 为 true。
- 主稿已将 F/G/H/I/J/K 字段作为 framework_v2 统计使用，并把多选字段写为编码出现次数，而不是互斥帖子比例。
- 评论层边界稳定：旁路评论、历史评论库、候选评论和后续评论复核材料均不作为当前正式发现。

## 高风险解释区

以下类别不是错误，但若后续需要行级复核，应优先抽查：

- 高强度替代：`G3`，258 次
- 自动执行：`F5`，249 次
- 治理监督：`F6`，123 次
- 正式规范参照，尤其是期刊政策、学校规定、科研诚信规则、审稿规范、署名规则、披露要求和数据伦理/隐私规则
- 边界结果中的替代去合法化：`K4`，25 次
- 边界结果中的治理争议化：`K6`，59 次
- 不确定或未编码项，包括科研活动场域 `uncoded=32`、工作流环节 `uncertain=32`，以及 v6 materials review 中提示的学科宽口径不确定项

这些类别应在主稿中保持谨慎表述：它们说明帖子层话语中的风险、争议或边界表达较集中，但不能直接推出总体研究者态度或制度共识。

## 主稿使用边界

当前 v6 主稿可以把 framework_v2 表格作为帖子层正式证据使用，但应持续说明：

- 研究对象限于 quality_v6 正式样本中的小红书公开帖子；
- 评论互动不属于当前正式分析范围；
- 多选字段是编码出现次数，不是互斥帖子比例；
- 平台话语不能直接泛化为所有研究者或所有社交媒体平台；
- AI 使用的规范评价应写成情境化、条件化和边界化判断，而不是简单合法或非法判断。

## 剩余局限

- 本研究不声称双人独立编码或盲法一致性检验。
- framework_v2 字段已进入当前正式层复核结果，但本 memo 没有新增逐条高风险记录复核。
- 参考文献和引文格式仍需按目标期刊样式调整。
- 如后续要讨论评论互动，需要先把 `comment_review_v2` 作为独立正式流程完成，再写入评论层发现。

## 判断

`quality_v6` 仍适合作为当前 post-only 投稿层。当前主要剩余风险不是 artifact 不一致，而是解释过度；主稿应继续在高强度替代、治理监督、正式规范参照和平台泛化等位置保留审慎措辞。
