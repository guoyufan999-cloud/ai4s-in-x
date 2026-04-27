# Canonical Backfill Contract

该说明文档把 canonical backfill 中的“保留型文件”正式纳入迁移合同。
summary / manifest / 空 JSONL 不再被视为 skipped 或失败；它们被记录为 preserved，原因是这些文件不是 row-level 语料，不能机械改写为 canonical JSONL。

- manifest：`outputs/reports/freeze_checkpoints/canonical_backfill_manifest.json`
- converted_files：`273`
- preserved_non_record_files：`29`
- preserved_empty_files：`5`

判定规则：
- `preserved_non_record_files`：manifest、summary、snapshot、checkpoint 等非单条帖子/评论 JSON。
- `preserved_empty_files`：语义上允许为空的 JSONL 占位文件。
- 只有 row-level JSONL/JSON/CSV 才进入 canonical row 迁移。
