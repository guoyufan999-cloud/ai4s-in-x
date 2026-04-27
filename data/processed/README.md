# Processed DB Local Path

本目录是研究型主库的本地约定位置。

- 预期本地文件名：`ai4s_legitimacy.sqlite3`
- 默认由 Git 忽略：仓库版本化的是这个 README，而不是 SQLite 文件本身
- 相关入口：`ai4s-build-artifacts`、`python -m ai4s_legitimacy.analysis.reporting`、`python -m ai4s_legitimacy.analysis.quality_v4_consistency`
- 相关配置：`src/ai4s_legitimacy/config/settings.py` 中的 `RESEARCH_DB_PATH`
- 当前 `quality_v5` 重建入口中的 `REBASELINE_STAGING_DB_PATH` 指向同一个研究主库路径；本目录下若出现 `ai4s_legitimacy_quality_v5_staging.sqlite3` 这类 0B staging 文件，应视为过期本地残留并清理

正式 summary / consistency JSON 已迁入 `outputs/reports/freeze_checkpoints/`。本目录保留给本地数据库及其 `-wal` / `-shm` 运行文件，不作为正式交付物目录。
