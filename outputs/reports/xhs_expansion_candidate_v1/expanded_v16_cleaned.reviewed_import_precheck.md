# xhs_expansion_candidate_v1 reviewed import precheck

本报告只检查 supplemental candidate reviewed JSONL 是否适合进入 staging JSONL。未写入研究主库，未更新 freeze checkpoint，未更新 `quality_v5` consistency report。

## Summary

- status: `pass_with_warnings`
- reviewed rows: `6221`
- accepted staged rows: `206`
- json errors: `0`
- critical issues: `0`
- warnings: `6912`
- reviewed path: `data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.expanded_v16_cleaned.codex_reviewed.jsonl`
- staged accepted path: `data/interim/xhs_expansion_candidate_v1/staged_import/xhs_expansion_candidate_v1.expanded_v16_cleaned.accepted_posts.jsonl`

## Final Decision Counts

- `exclude`: `6004`
- `include`: `206`
- `review_needed`: `11`

## Critical Issue Counts

- none

## Warning Counts

- `duplicate_existing_post`: `4336`
- `missing_post_date`: `347`
- `public_boundary_issue`: `2229`

## Policy Guard

- `source_scope = xhs_expansion_candidate_v1`
- `formal_scope = false`
- `quality_v5_formal = false`
- `supplemental_candidate = true`
- 本步骤未写入研究主库，也未将候选样本计入正式论文结果。

## Warning Samples

- `xhs_expanded_v3_5382e9eb517cfa3b` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_e4c631f742844915` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_bc58056d4e51d7e9` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_b5f07dab248125d2` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_27d229dc869fd1a3` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_d8c65ae403a436c3` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_ac85ea5897de5f90` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_000578e241c0088b` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_59a52917314e2b27` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_e94c230854948fb4` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_e46f3ee04ab95cef` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_fd08cd5d33f70ccc` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_31903d4bf2940da3` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_09796b35bf6d7e1a` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_0584912741759625` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_4e804bbe3f262f51` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_87b79feaac24b65a` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_7e763df3571567dc` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_3d15619ee2577afa` / `public_boundary_issue` / public_access_status_not_ok
- `xhs_expanded_v3_784bd05b2158f209` / `public_boundary_issue` / public_access_status_not_ok
