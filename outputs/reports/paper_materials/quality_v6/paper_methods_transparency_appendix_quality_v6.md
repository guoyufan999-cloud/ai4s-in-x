# quality_v6 Methods Transparency Appendix

## 样本升级链路

- 前一正式基线：`quality_v5 post-only 514 / 0`
- 补充候选来源：`xhs_expansion_candidate_v1`
- 补充 formalization：`supplemental_formalization_v1`
- 纳入 v6：`200` 条帖子
- 排除：`6` 条帖子
- v6 正式范围：`714 / 0`

## 方法边界

补充帖通过独立 staging DB 形成 `paper_scope_quality_v6`，未写回 `quality_v5` freeze checkpoint，未启动 `comment_review_v2`，也未将 sidecar 评论纳入正式结果。

## 校验状态

- consistency status：`aligned`
- quality_v5 guard：`514 / 0`
- excluded rows in v6：`0`
