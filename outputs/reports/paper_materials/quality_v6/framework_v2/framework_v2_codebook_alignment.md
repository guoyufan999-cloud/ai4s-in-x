# Framework v2 Codebook Alignment

## 旧框架到新框架的映射

| 新五层框架 | 当前承载方式 | 说明 |
|---|---|---|
| 话语情境 | `platform`、`actor_type`、`discursive_mode`、`record_type`、`context_used` | 使用已有 canonical/source 字段映射，不新增重复字段。 |
| 实践位置 | A 组 `workflow_dimension` / `workflow_stage_codes` | A1 科研生产、A2 科研治理、A3 科研训练与能力建构被解释为实践位置。 |
| 介入方式 | F 组 `ai_intervention_mode_codes` | 通过 framework_v2 reviewed 补码进入正式统计。 |
| 介入强度 | G 组 `ai_intervention_intensity_codes` | 强度由具体使用方式决定，不由工具名称决定。 |
| 规范评价 | B 组倾向 + C 组标准 | “合法性”保留为历史术语，当前操作化为规范评价。 |
| 评价张力 | H 组 `evaluation_tension_codes` | 通过 framework_v2 reviewed 补码进入正式统计。 |
| 正式规范参照 | I 组 `formal_norm_reference_codes` | 通过 framework_v2 reviewed 补码进入正式统计。 |
| 边界生成 | D 组边界类型 + J/K 组机制与结果 | D 组保留，J/K 用于机制与结果扩展。 |

## 当前状态

- 已 reviewed 正式帖子：`714`
- 未完成正式帖子：`0`
- 是否完成：`True`
- 说明：framework_v2 正式帖子已完成人工 reviewed 补码，本表可作为正式 v2 统计使用。
