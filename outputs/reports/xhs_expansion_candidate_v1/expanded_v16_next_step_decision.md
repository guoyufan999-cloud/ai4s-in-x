# expanded_v16 next step decision

本决策只针对 `xhs_expansion_candidate_v1` 补充候选样本，不影响 `quality_v5 514 / 0` formal baseline。

## Decision

建议启动 `supplemental formalization`，暂不启动 `quality_v6`。

## Basis

- staged accepted: `206`
- review_needed: `11`
- audit sample: `91`
- include sample pass rate: `96.2%`
- sample pass / needs_human_review / exclude: `77 / 14 / 0`
- main risk tags: `{'ad_or_service_noise': 13, 'weak_ai_research_signal': 1}`

## Why not quality_v6 yet

- 当前审核是 Codex-assisted method appendix audit，不是完整人工 formal coding。
- v16 样本仍有 `14` 条抽查风险样本需要人工确认，主要是广告/服务转化噪声。
- F/G/H/I/J/K 与五层框架字段还没有在 206 条 accepted 上形成正式 reviewed coding。

## Recommended Next Work

1. 对 206 条 staged accepted 做 supplemental formalization 队列。
2. 对 14 条风险样本先人工确认：广告/服务噪声如确认较高，加入排除规则。
3. 对通过样本补全五层框架字段：话语情境、实践位置、介入方式、规范评价、边界生成。
4. 生成 `supplemental_formalization_v1` 独立报告和表格；只作为补充结果，不并入 `quality_v5`。
5. 若 supplemental formalization 通过率稳定，再讨论是否新建 `quality_v6` checkpoint。
