# Legacy Runtime Static Archive

`archive/legacy_collection_runtime/` 现在只作为静态历史档案保留，不再承诺可直接运行。

当前保留内容：

- `data/db/ai4s_xhs.sqlite3`：legacy 运行库 SQLite 历史事实源
- `README.md`：当前 archive 合同说明
- `PROVENANCE.md`：历史运行组件来源与用途记录

本轮已移除的 legacy 运行残留：

- `ai4s_xhs/`
- `ai4s-xhs`
- `scripts/`
- `config/`
- `pyproject.toml`
- `requirements.lock`
- `requirements.multimodal.lock`
- `data/runtime_state/`
- `data/db/.gitkeep`
- `opencli-main/`
- `opencli`
- `docker/`
- `docker-compose.yml`
- legacy DB 的 `.sqlite3-wal` / `.sqlite3-shm`

如需追溯历史系统依赖过什么，请查看同目录下的 `PROVENANCE.md`。保留这些信息的目的，是解释历史系统依赖过什么，而不是继续在主仓库中 vendoring 整个运行环境。
