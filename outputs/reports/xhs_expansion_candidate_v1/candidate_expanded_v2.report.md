# xhs_expansion_candidate_v1 candidate_expanded_v2 report

本报告合并仓库内已有 supplemental / external pilot 采集产物，形成更大的补充候选样本合集。该合集不写入研究主库，不进入 `quality_v5` formal baseline。

## Summary

- unique candidate posts: `256`
- decision counts: `{'待复核': 58, '纳入': 146, '剔除': 52}`
- missing query_group: `0`
- formal_scope: `false`
- quality_v5_formal: `false`

## Source Contribution

| source | input_rows | unique_added | duplicate_current_merge | duplicate_existing_db |
|---|---:|---:|---:|---:|
| candidate300_reviewed_source | 115 | 115 | 0 | 0 |
| external_xhs_ai4s_2025plus_pilot100 | 100 | 97 | 3 | 0 |
| pilot50 | 50 | 27 | 23 | 0 |
| post_expansion_with_comment_sidecar | 20 | 14 | 6 | 0 |
| external_xhs_ai4s_lightpush_20260428_2queries | 2 | 2 | 0 | 0 |
| external_xhs_ai4s_smoketest_3queries | 1 | 1 | 0 | 0 |

## Query Group Distribution

| query_group | count |
|---|---:|
| practice | 62 |
| B. 文献处理与知识整合类 | 57 |
| A. AI科研总体类 | 40 |
| C. 研究设计与方法学习类 | 37 |
| boundary | 32 |
| salience | 17 |
| D. 数据分析与代码类 | 11 |

## Live Collection Attempt

- 本轮尝试运行大参数实时扩样 `candidate_more_raw`。
- 当前 OpenCLI Browser Bridge 未连接，采集器退到 Bing fallback，但未获得可验证公开帖子。
- 因合规边界要求，本轮未尝试绕过登录、验证码、风控或受限访问。

## Next Step

建议以本合集生成新的人工 review queue；若需要继续实时扩样，需要先恢复 OpenCLI Browser Bridge 的只读浏览器会话。
