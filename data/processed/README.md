# Processed DB Local Path

本目录是研究型主库的本地约定位置。

- 预期本地文件名：`ai4s_legitimacy.sqlite3`
- 默认由 Git 忽略：仓库版本化的是这个 README，而不是 SQLite 文件本身
- 相关入口：`ai4s-build-artifacts`、`python -m ai4s_legitimacy.analysis.reporting`、`python -m ai4s_legitimacy.analysis.quality_v4_consistency`
- 相关配置：`src/ai4s_legitimacy/config/settings.py` 中的 `RESEARCH_DB_PATH`

正式 summary / consistency JSON 已迁入 `outputs/reports/freeze_checkpoints/`。本目录保留给本地数据库及其 `-wal` / `-shm` 运行文件，不作为正式交付物目录。
