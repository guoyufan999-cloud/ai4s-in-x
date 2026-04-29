# xhs_expansion_candidate_v1 reviewed import precheck

本报告只检查 supplemental candidate reviewed JSONL 是否适合进入 staging JSONL。未写入研究主库，未更新 freeze checkpoint，未更新 `quality_v5` consistency report。

## Summary

- status: `pass_with_warnings`
- reviewed rows: `115`
- accepted staged rows: `78`
- json errors: `0`
- critical issues: `0`
- warnings: `1`
- reviewed path: `/Users/guoyufan/ai4s in xhs/data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.reviewed.jsonl`
- staged accepted path: `/Users/guoyufan/ai4s in xhs/data/interim/xhs_expansion_candidate_v1/staged_import/xhs_expansion_candidate_v1.accepted_posts.jsonl`

## Final Decision Counts

- `exclude`: `37`
- `include`: `78`

## Critical Issue Counts

- none

## Warning Counts

- `public_boundary_issue`: `1`

## Policy Guard

- `source_scope = xhs_expansion_candidate_v1`
- `formal_scope = false`
- `quality_v5_formal = false`
- `supplemental_candidate = true`
- 本步骤未写入研究主库，也未将候选样本计入正式论文结果。

## Warning Samples

- `xhs_expansion_candidate_v1:69ad1fd0000000001a0361ca` / `public_boundary_issue` / possible_non_public_content_marker
