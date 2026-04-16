# Legacy DB Local Path

本目录是 legacy 历史运行库的本地约定位置。

- 预期本地文件名：`ai4s_xhs.sqlite3`
- 默认由 Git 忽略：仓库版本化的是这个 README，而不是 SQLite 文件本身
- 相关入口：`ai4s-import-legacy`、`python -m ai4s_legitimacy.collection.import_legacy_sqlite`
- 相关配置：`src/ai4s_legitimacy/config/settings.py` 中的 `LEGACY_DB_PATH`

如果本地不存在这份 DB，上述导入命令会直接失败；这是预期行为。`.sqlite3-wal`、`.sqlite3-shm` 等运行残留也应只保留在本地，不进入版本控制。
