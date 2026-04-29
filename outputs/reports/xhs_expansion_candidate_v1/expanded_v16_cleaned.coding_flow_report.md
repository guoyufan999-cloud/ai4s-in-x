# xhs_expansion_candidate_v1 expanded_v16 cleaned coding flow report

本报告记录 v16 清洗后补充候选集的整理、预审、staging 与结构分析流程。该流程不写入研究主库，不更新 freeze checkpoint，不改变 `quality_v5 514 / 0` formal baseline。

## 1. 数据清洗

- 输入候选：`6221`
- 清洗后候选：`6221`
- sidecar comments：`90027`
- query_group 重分类：`377`
- URL 规范化：`1886`
- 页面 chrome 清理：`6`
- 标记主库重复并预设剔除：`4336`
- 正文少于 80 字并预设剔除：`2221`

## 2. 清洗后校验

- duplicate_candidate_ids：`0`
- duplicate_note_ids：`0`
- bad_query_group_rows：`0`
- bad_or_tokenized_url_rows：`0`
- bad_post_formal_flags：`0`
- bad_comment_formal_flags：`0`

## 3. 编码流程产物

- cleaned candidates：`outputs/tables/xhs_expansion_candidate_v1/candidate_expanded_v16_cleaned.jsonl`
- cleaned sidecar comments：`outputs/tables/xhs_expansion_candidate_v1/candidate_expanded_v16_cleaned_sidecar_comments.jsonl`
- review queue：`data/interim/xhs_expansion_candidate_v1/review_queues/xhs_expansion_candidate_v1.expanded_v16_cleaned.review_queue.jsonl`
- review template：`data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.expanded_v16_cleaned.review_template.jsonl`
- codex-assisted reviewed：`data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.expanded_v16_cleaned.codex_reviewed.jsonl`
- precheck report：`outputs/reports/xhs_expansion_candidate_v1/expanded_v16_cleaned.reviewed_import_precheck.md`
- staged accepted：`data/interim/xhs_expansion_candidate_v1/staged_import/xhs_expansion_candidate_v1.expanded_v16_cleaned.accepted_posts.jsonl`

## 4. Precheck 结果

- status：`pass_with_warnings`
- reviewed rows：`6221`
- final include / review_needed / exclude：`206 / 11 / 6004`
- accepted staged rows：`206`
- critical issues：`0`
- warnings：`6912`

警告主要来自已剔除样本的主库重复、短文本 public status 和缺失日期；这些样本没有进入 staged include。

## 5. 结构分析

- analysis report：`outputs/reports/xhs_expansion_candidate_v1/supplemental_analysis_v16_cleaned.md`
- analysis table dir：`outputs/tables/xhs_expansion_candidate_v1/analysis_v16_cleaned/`
- staged accepted count：`206`
- quality_v5 comparison count：`514`

该分析只描述补充候选样本结构，不生成论文结论，不作为 `quality_v5` 正式统计。
