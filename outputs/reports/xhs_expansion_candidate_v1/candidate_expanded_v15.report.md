# xhs_expansion_candidate_v1 expanded_v15 report

本报告只描述 `xhs_expansion_candidate_v1` 补充候选样本扩充结果，不构成论文发现，不写入 `quality_v5` formal baseline，也不写入正式研究主库。

## 扩充来源与边界

- 扩充方式：对历史公开 `note_candidates` / `note_details` / `media_assets` 缓存中未进入 v14 的条目进行 AI + 科研关键词再筛。
- live XHS 状态：OpenCLI search 返回空，web read 返回“安全限制”；未尝试绕过登录、验证码、风控或访问限制。
- 评论处理：仅生成 post-linked sidecar context，不启动 `comment_review_v2`，不计入 formal comments。
- formal baseline guard：`quality_v5` 正式帖子 / 正式评论仍为 `514 / 0`。

## 规模

- v14 候选帖：`5680`
- 本轮扫描未入 v14 的 legacy note：`1740`
- 本轮新增候选帖：`541`
- v15 候选帖总量：`6221`
- v15 sidecar comments：`90027`，其中本轮新增 `11850`
- 有文本上下文候选：`4428`
- 仅元数据候选：`1793`

## 新增 query_group 分布

- `B. 文献处理与知识整合类`: `239`
- `D. 数据分析与代码类`: `98`
- `F. 科研规范与诚信类`: `151`
- `E. 论文写作与成果表达类`: `21`
- `C. 研究设计与方法学习类`: `26`
- `G. 科研训练与效率类`: `5`
- `A. AI科研总体类`: `1`

## 新增内容来源

- `full_text`: `389`
- `full_text_plus_media_excerpt_if_needed`: `152`

## 跳过原因

- `date_out_of_range`: `179`
- `missing_ai_or_research_signal`: `1019`
- `insufficient_text`: `1`

## 校验

- duplicate_candidate_ids：`0`
- duplicate_note_ids：`0`
- missing_query_group：`0`
- missing_post_url：`0`
- formal_flagged_post_rows：`0`
- formal_flagged_sidecar_comment_rows：`0`

## 输出文件

- candidate JSONL：`outputs/tables/xhs_expansion_candidate_v1/candidate_expanded_v15.jsonl`
- 新增 backlog：`outputs/tables/xhs_expansion_candidate_v1/candidate_legacy_rescreen_backlog_v15.jsonl`
- sidecar comments：`outputs/tables/xhs_expansion_candidate_v1/candidate_expanded_v15_sidecar_comments.jsonl`
- review queue：`data/interim/xhs_expansion_candidate_v1/review_queues/xhs_expansion_candidate_v1.expanded_v15.review_queue.jsonl`
- review template：`data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.expanded_v15.review_template.jsonl`

## 下一步建议

- 不建议继续强行 live 抓取，除非 XHS 只读浏览器会话恢复为可稳定公开访问状态。
- 建议先抽样 review v15 新增的 535 条，重点检查广告/工具推广、纯课程营销、非科研语境和重复帖。
- 若 v15 新增样本人工通过率可接受，再决定是否启动 supplemental formalization 或单独创建 `quality_v6` checkpoint。
