# quality_v4 正式冻结版 Delta Report

## Baseline
- 当前正式基线：`quality_v4 正式冻结版`
- 对比基线：`quality_v3 正式冻结版`

## Core Deltas
- 正式帖子：`3067`（较上一版 `-526`）
- 正式评论：`69880`（较上一版 `-6376`）
- `uncertain_subject_share`：`23.77%`（较上一版 `-5.45` 个百分点）
- `uncertain_workflow_share`：`14.18%`（较上一版 `-5.24` 个百分点）

## Boundary Tightening
- 第二轮 merged review：`235` 行
- `llm_auto_applied=1`：`223`
- `override_sample_status=false`：`194`
- 宣传/推广型 actor override：`6`
- `review_override_posts`：`280`
- 主要边界原因：borderline_generic_efficiency=`91`、borderline_tool_list=`57`、sample_override=`33`、borderline_template=`6`、actor_override=`5`、workflow_override=`2`

## Inheritance Audit
- 评论继承抽样：`3` 条
- 类别分布：sample_status_false=`1`、subject_changed=`1`、workflow_changed=`1`

## Known Tail Limits
- `queued`：`22`
- `temporarily_unavailable_300031`：`43`
- `needs_manual_check`：`5`
- 最新媒体审计 `formal_media_gap`：`2218`
- 说明：这部分尾部债务保留为方法限制，不再阻断 `quality_v4` 作为当前正式论文基线。
