# Legacy Exports Archive Index

`archive/legacy_exports/` 现在只保留索引式静态说明，不再保留大批过程目录、CSV / Parquet 导出物或 rerun 结果。

此前归档内容主要分为三类：

- `exports_legacy/`：candidate gap completion、freeze checkpoints、stage runner、structure repair、rerun 状态等过程性导出
- `grounded_pilot/`：grounded theory 试跑与 smoke / pilot 结果
- `legacy_analysis_exports/`：历史分析面板、候选/评论/作者/媒体等 CSV / Parquet 导出

移出这些目录的原因：

- 它们不再作为当前研究主线的事实源
- 它们显著扩大仓库体量和 Git 文件数
- 正式论文链路已经统一切到研究主库与 `outputs/` 正式产物

需要追溯历史流程时，应优先结合以下静态事实源与说明：

- `archive/legacy_collection_runtime/data/db/ai4s_xhs.sqlite3`
- `archive/legacy_collection_runtime/README.md`
- `archive/legacy_collection_runtime/PROVENANCE.md`
- `archive/legacy_specs/README.md`
