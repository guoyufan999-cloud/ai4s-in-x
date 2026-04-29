# xhs_expansion_candidate_v1 supplemental analysis

本报告只描述 `xhs_expansion_candidate_v1` 补充候选样本结构，不生成论文结论，不把候选样本混同为 `quality_v5` 正式结果。

## Scope Guard

- source_scope: `xhs_expansion_candidate_v1`
- staged include input: `data/interim/xhs_expansion_candidate_v1/staged_import/xhs_expansion_candidate_v1.expanded_v16_cleaned.accepted_posts.jsonl`
- decision count source: `reviewed JSONL`
- reviewed input: `data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.expanded_v16_cleaned.codex_reviewed.jsonl`
- quality_v5 comparison source: `vw_posts_paper_scope_quality_v5`
- quality_v5 formal scope remains: `514 / 0`
- 本报告未写入研究主库，未更新 freeze checkpoint，未更新 `quality_v5` consistency report。

## 1. 补充样本总量

- staged accepted posts: `206`
- reviewed candidate rows: `6221`
- quality_v5 formal posts for comparison: `514`

## 2. include / review_needed / exclude 数量

| decision | count | share |
| --- | --- | --- |
| include | 206 | 0.0331 |
| review_needed | 11 | 0.0018 |
| exclude | 6004 | 0.9651 |

## 3. 查询词组分布

查询词组元数据可用于后续抽样评估。

| query_group | count | share |
| --- | --- | --- |
| B. 文献处理与知识整合类 | 81 | 0.3932 |
| A. AI科研总体类 | 36 | 0.1748 |
| F. 科研规范与诚信类 | 33 | 0.1602 |
| C. 研究设计与方法学习类 | 31 | 0.1505 |
| D. 数据分析与代码类 | 21 | 0.1019 |
| E. 论文写作与成果表达类 | 2 | 0.0097 |
| G. 科研训练与效率类 | 2 | 0.0097 |

## 4. 发帖时间分布

| month | count | share |
| --- | --- | --- |
| 2024-02 | 1 | 0.0049 |
| 2024-06 | 2 | 0.0097 |
| 2024-10 | 3 | 0.0146 |
| 2024-11 | 2 | 0.0097 |
| 2024-12 | 4 | 0.0194 |
| 2025-01 | 6 | 0.0291 |
| 2025-02 | 8 | 0.0388 |
| 2025-03 | 20 | 0.0971 |
| 2025-04 | 6 | 0.0291 |
| 2025-05 | 13 | 0.0631 |
| 2025-06 | 8 | 0.0388 |
| 2025-07 | 14 | 0.068 |
| 2025-08 | 8 | 0.0388 |
| 2025-09 | 10 | 0.0485 |
| 2025-10 | 4 | 0.0194 |
| 2025-11 | 9 | 0.0437 |
| 2025-12 | 15 | 0.0728 |
| 2026-01 | 5 | 0.0243 |
| 2026-02 | 3 | 0.0146 |
| 2026-03 | 21 | 0.1019 |

## 5. 文本类型初步分布

该分布来自 supplemental reviewed/staging 中的 `discourse_context`，属于初步结构描述，不等于正式论文发现。

| text_type | count | share |
| --- | --- | --- |
| 工具推荐 | 81 | 0.3932 |
| 经验分享 | 49 | 0.2379 |
| 教程展示/经验教程 | 29 | 0.1408 |
| 风险提醒 | 26 | 0.1262 |
| 规范解读 | 14 | 0.068 |
| 评论争论 | 7 | 0.034 |

## 6. AI科研实践主题初步分布

该分布来自 `workflow_stage` 的 supplemental 初步人工/半人工 review 字段，仅用于判断补充样本结构。

| theme | count | share |
| --- | --- | --- |
| AI文献阅读与知识整合 | 99 | 0.4806 |
| 其他/无法判断 | 36 | 0.1748 |
| AI数据分析与代码 | 31 | 0.1505 |
| AI研究设计与方法学习 | 14 | 0.068 |
| AI论文写作与成果表达 | 13 | 0.0631 |
| AI科研训练与效率 | 10 | 0.0485 |
| AI科研规范与治理 | 3 | 0.0146 |

## 7. 与 quality_v5 现有 514 条样本的差异

下表只比较主题结构比例，不表示理论规律。

| theme | supplemental_n | supplemental_share | quality_v5_n | quality_v5_share | share_delta |
| --- | --- | --- | --- | --- | --- |
| AI研究设计与方法学习 | 14 | 0.068 | 137 | 0.2665 | -0.1986 |
| 其他/无法判断 | 36 | 0.1748 | 0 | 0.0 | 0.1748 |
| AI科研训练与效率 | 10 | 0.0485 | 7 | 0.0136 | 0.0349 |
| AI论文写作与成果表达 | 13 | 0.0631 | 47 | 0.0914 | -0.0283 |
| AI文献阅读与知识整合 | 99 | 0.4806 | 241 | 0.4689 | 0.0117 |
| AI科研规范与治理 | 3 | 0.0146 | 6 | 0.0117 | 0.0029 |
| AI数据分析与代码 | 31 | 0.1505 | 76 | 0.1479 | 0.0026 |

文本类型结构对比如下。注意：supplemental 的文本类型来自 `discourse_context`，
`quality_v5` 的文本类型来自 `discursive_mode` 映射，二者不是完全同构字段；
例如 `工具推荐` 在 `quality_v5` 旧字段中没有直接同名类别。

| text_type | supplemental_n | supplemental_share | quality_v5_n | quality_v5_share | share_delta |
| --- | --- | --- | --- | --- | --- |
| 工具推荐 | 81 | 0.3932 | 0 | 0.0 | 0.3932 |
| 经验分享 | 49 | 0.2379 | 265 | 0.5156 | -0.2777 |
| 教程展示/经验教程 | 29 | 0.1408 | 208 | 0.4047 | -0.2639 |
| 风险提醒 | 26 | 0.1262 | 16 | 0.0311 | 0.0951 |
| 规范解读 | 14 | 0.068 | 11 | 0.0214 | 0.0466 |
| 评论争论 | 7 | 0.034 | 0 | 0.0 | 0.034 |
| 其他/无法判断 | 0 | 0.0 | 14 | 0.0272 | -0.0272 |

## 8. 对既有样本不足方向的补充价值

| direction | supplemental_n | quality_v5_comparable_n | assessment |
| --- | --- | --- | --- |
| 科研训练材料 | 10 | 7 | 有一定补充价值，建议进入人工编码评估。 |
| AI数据分析材料 | 31 | 76 | 有一定补充价值，建议进入人工编码评估。 |
| AI使用披露讨论 | 5 | None | 有少量补充，但不足以直接支撑主结果。 |
| AI学术诚信讨论 | 11 | None | 有一定补充价值，建议进入人工编码评估。 |
| AI审稿/检测讨论 | 15 | 6 | 有一定补充价值，建议进入人工编码评估。 |

## 9. 纳入建议

建议先作为补充材料并进入人工编码；暂不直接进入论文主结果。若后续完成 supplemental formalization，可再讨论是否启动 quality_v6。

建议口径：

- 当前只作为 `xhs_expansion_candidate_v1` 补充材料和候选样本结构报告。
- 可以进入下一轮人工编码，尤其是对 `review_needed` 与边界/规范信号较强样本做复核。
- 不建议直接并入 `quality_v5` 主结果。
- 是否进入新的 `quality_v6`，应在完成去重、query metadata 修复、人工编码和 supplemental formalization 方案后单独决定。

## Additional Tables

- AI介入方式：`supplemental_ai_intervention_mode_distribution.*`
- AI介入强度：`supplemental_ai_intervention_intensity_distribution.*`
- 规范评价信号：`supplemental_normative_signal_distribution.*`
- 边界信号：`supplemental_boundary_signal_distribution.*`

所有表格均标注 `source_scope = xhs_expansion_candidate_v1`，不得作为 `quality_v5` 正式统计引用。
