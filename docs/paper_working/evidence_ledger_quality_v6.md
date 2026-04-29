# quality_v6 论文证据台账

## 总体口径

| 论文段落主题 | 使用的数据表或文件 | 对应数字 | 可用摘录文件 | 是否可以作为正式结果 | 风险提示 |
|---|---|---:|---|---|---|
| 当前投稿结果层 | `outputs/reports/paper_materials/paper_analysis_snapshot.md`; `outputs/reports/paper_materials/quality_v6/quality_v6_post_only_contract.md`; `outputs/reports/paper_materials/quality_v6/paper_materials_manifest.json` | 正式帖子 714；正式评论 0；研究时间窗 2024-01-01 至 2026-06-30；覆盖截止日 2026-04-26 | 不适用 | 是 | 只能写为帖子层 post-only 正式结果，不能写入评论结论 |
| v6 来源组合 | `outputs/reports/paper_materials/paper_analysis_snapshot.md`; `outputs/reports/paper_materials/quality_v6/paper_methods_transparency_appendix_quality_v6.md` | quality_v5 514 + supplemental formalization 200；排除 6 条；v6 范围 714/0 | 不适用 | 是 | v5 是前一冻结基线，不是当前投稿结果层 |
| consistency 与 staging DB | `outputs/reports/freeze_checkpoints/quality_v6_consistency_report.json`; `outputs/reports/freeze_checkpoints/quality_v6_research_db_summary.json` | status aligned；candidate posts 5735；candidate comments 106543；paper_quality_v6_posts 714；paper_quality_v6_comments 0 | 不适用 | 是，作为方法背景 | staging DB 规模不能写成正式样本规模 |

## 摘要、引言与研究设计

| 论文段落主题 | 使用的数据表或文件 | 对应数字 | 可用摘录文件 | 是否可以作为正式结果 | 风险提示 |
|---|---|---:|---|---|---|
| 研究对象与数据口径 | `paper_analysis_snapshot.md`; `quality_v6_post_only_contract.md`; `paper_materials_manifest.json` | 714 帖；0 评论；comment_review_v2 deferred | 不适用 | 是 | 摘要必须明确评论层 deferred |
| 五层框架 | `README.md`; `research_brief.md`; `analysis_plan.md`; `outputs/reports/paper_materials/quality_v6/framework_v2/framework_v2_codebook_alignment.md` | 五层框架及 A/B/C/D/F/G/H/I/J/K 映射 | 不适用 | 是，作为分析框架 | `research_brief.md` 与 `analysis_plan.md` 的 v5 数字不可沿用 |
| 编码流程 | `outputs/reports/paper_materials/quality_v6/framework_v2/README.md`; `framework_v2_summary_tables.json` | reviewed posts 714；missing posts 0；coding complete true | 不适用 | 是 | 不得写双人独立编码或编码完全无误 |
| 研究伦理 | `compliance_and_ethics.md`; `quality_v6_post_only_contract.md` | 公开数据、匿名化、最小化、formal_comments=0 | 不适用 | 是，作为方法与伦理说明 | `compliance_and_ethics.md` 的 v5 基线需替换为 v6 主稿口径 |

## 研究发现一：话语情境与实践图谱

| 论文段落主题 | 使用的数据表或文件 | 对应数字 | 可用摘录文件 | 是否可以作为正式结果 | 风险提示 |
|---|---|---:|---|---|---|
| 文本类型分布 | `outputs/reports/paper_materials/quality_v6/framework_v2/framework_v2_chapter_materials.md`; `framework_v2_summary_tables.json` | 经验分享 284；教程展示 251；其他 112；风险提醒 42；规范解读 25 | `outputs/excerpts/post_stance_*.md` 可作去标识化例证 | 是 | 文本类型是本正式样本分布，不代表平台总体舆论 |
| 科研活动场域 | 同上 | A1 科研生产 657；A3 科研训练与能力建构 16；A2 科研治理 9；uncoded 32 | `outputs/excerpts/workflow_*.md` | 是 | A 组场域计数不可解释为所有科研共同体分布 |
| 工作流环节 | 同上；`outputs/tables/quality_v6/workflow_distribution.json` | 文献调研与知识整合 339；研究构思与问题定义 127；数据处理与分析建模 88；学术写作与成果表达 52；uncertain 32 | `outputs/excerpts/workflow_文献检索与综述.md` 等旧摘录需谨慎 | 是 | 旧摘录命名沿用旧工作流词，不应改变为真实引文；uncertain 应作为方法边界 |

## 研究发现二：AI介入方式、介入强度与规范评价

| 论文段落主题 | 使用的数据表或文件 | 对应数字 | 可用摘录文件 | 是否可以作为正式结果 | 风险提示 |
|---|---|---:|---|---|---|
| AI 介入方式 | `framework_v2_chapter_materials.md`; `framework_v2_summary_tables.json` | 生成辅助 576；信息辅助 530；分析建模 418；判断建议 371；自动执行 249；治理监督 123 | workflow/post stance 摘录仅作去标识化说明 | 是 | F 组为多选/编码出现次数，不加总为帖子总数 |
| AI 介入强度 | 同上 | 中强度共创 378；高强度替代 258；低强度辅助 80 | 不适用 | 是 | 不能把高强度替代直接写成违规 |
| 规范评价标准 | 同上 | 能力补充 518；人机分工 428；效率提升 352；可靠性与可验证性 253；训练价值 247；规范适配 242 | 不适用 | 是 | C 组为多选，不写百分比总和 |
| 规范评价倾向 | 同上 | 有条件接受 265；混合/冲突性评价 219；未表达评价 145；正面接受 65；质疑/否定 22 | `outputs/excerpts/post_stance_*.md` | 是 | 不说用户普遍支持或公众普遍反对 |
| 评价张力 | 同上 | 人机共创 vs 责任归属 417；技术可用性 vs 规范不确定性 270；便利性 vs 可靠性 246；能力补充 vs 能力替代 197 | 不适用 | 是 | 张力是编码出现，不是制度冲突事实 |
| 正式规范参照 | 同上 | 未明确参照 291；期刊政策 210；学校规定 173；科研诚信规则 112；审稿规范 87 | 不适用 | 是 | 平台帖子援引规范不等于平台或制度已形成正式规则 |

## 研究发现三：边界协商

| 论文段落主题 | 使用的数据表或文件 | 对应数字 | 可用摘录文件 | 是否可以作为正式结果 | 风险提示 |
|---|---|---:|---|---|---|
| 边界类型 | `framework_v2_chapter_materials.md`; `framework_v2_summary_tables.json` | 人机分工边界 357；辅助与替代边界 249；验证/复核边界 199；署名与贡献边界 68；学术诚信边界 65 | `outputs/excerpts/boundary_boundary_assistance_vs_substitution.md` | 是 | D 组为边界表达出现，不代表稳定共识 |
| 边界协商机制 | 同上 | 条件化机制 449；规范化机制 327；风险化机制 268；责任化机制 256 | 同上 | 是 | 机制可说明边界生成方式，不等同制度政策 |
| 边界协商结果 | 同上 | 条件合法化 377；治理争议化 59；风险问题化 41；替代去合法化 25；辅助合法化 15；规范悬置 9 | 同上 | 是 | 条件合法化不是无条件正当化 |

## 不进入正式结论的材料

| 材料 | 原因 | 可否在正文出现 | 风险提示 |
|---|---|---|---|
| `outputs/excerpts/comment_stance_*.md` | 评论层正式结果为 0，`comment_review_v2 deferred` | 不作为结果，可作为未来研究方向提及 | 禁止写评论区正式发现 |
| `outputs/tables/xhs_expansion_candidate_v1/*sidecar_comments*` | sidecar 评论未进入 formal comments | 否 | 禁止作为评论层统计 |
| `docs/paper_working/paper_results_chapter_draft.md` | quality_v4 旧口径 | 仅可参考行文结构 | 其中 3067/69880 不能进入 v6 主稿 |
| `docs/paper_working/paper_discussion_chapter_draft.md` | quality_v4 旧口径且含评论分析 | 仅可参考讨论结构 | 不得复用评论区规范协商结论 |
| `docs/paper_working/framework_v2_chapter_*_draft.md` | quality_v5 旧口径 | 可参考章节逻辑 | 需替换所有 514/516 等 v5 数字 |
