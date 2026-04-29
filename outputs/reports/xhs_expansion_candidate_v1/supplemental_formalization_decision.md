# xhs_expansion_candidate_v1 supplemental formalization decision

本报告只服务 `xhs_expansion_candidate_v1` 补充样本决策，不改变 `quality_v5 post-only 514 / 0` 正式基线。

## Current Status

- reviewed candidates: `115`
- final include / review_needed / exclude: `78 / 0 / 37`
- staged accepted posts: `78`
- query_group missing after repair: `0`
- precheck status: `pass_with_warnings`
- warning: `1` 条已剔除样本存在公开边界风险标记，未进入 staging。

## Decision

当前不启动 `quality_v6`。

当前可以启动 supplemental formalization 的准备工作，但不应直接把 78 条样本并入论文主结果。更合适的下一步是为这 78 条 staged include 样本建立正式人工编码队列，完成去重审计、F/G/H/I/J/K 或对应 v2 字段人工编码、典型摘录抽查后，再决定是否形成独立 supplemental formal checkpoint。

## Rationale

- query metadata 已修复，可以支持查询组维度的补充样本结构描述。
- 78 条 include 样本具备补充价值，尤其是文献处理、研究设计和部分数据分析材料。
- 样本规模和规范/治理方向覆盖仍不足，不适合直接升级为新的主正式样本。
- 当前 reviewed/recheck 属于 Codex-assisted supplemental review，不等同于完整人工正式编码。
- `quality_v5` 是现有论文主线的稳定正式基线，不能被 exploratory supplemental 样本直接覆盖。

## Recommended Next Step

1. 为 78 条 staged include 样本生成 supplemental formalization review queue。
2. 人工复核去重、广告噪声、公开边界、研究相关性。
3. 对保留样本补齐 v2 字段和 evidence。
4. 生成 supplemental-only artifacts，与 `quality_v5` 主结果分开呈现。
5. 仅在 supplemental formalization 完整通过后，再讨论是否另起 `quality_v6`。
