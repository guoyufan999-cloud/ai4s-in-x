# 重构诊断与迁移清单

## 一、保留并迁移

### 论文正式事实源

- `quality_v4` 冻结文件
- 投稿版图表包
- 投稿版文稿与快照

迁移位置：
- `outputs/reports/`
- `outputs/figures/`

### 历史原始公开数据

- `data/raw/search`
- `data/raw/user`
- `data/raw/queues`
- `data/raw/media`
- `data/raw/media_files`

迁移位置：
- 保留在 `data/raw/`

## 二、归档

### 旧运行系统

- legacy SQLite 历史事实源
- 运行组件 provenance 说明

归档位置：
- `archive/legacy_collection_runtime/`
- 当前保留原则：`archive/legacy_collection_runtime/` 只保留 `data/db/ai4s_xhs.sqlite3` 与最小说明文件；`ai4s_xhs/`、脚本、配置、锁文件以及 `docker/`、`docker-compose.yml`、`opencli`、`opencli-main` 这类运行环境镜像都不再保留在主仓库中。

### 旧测试与旧示例

- 原 `tests/`
- 原 `examples/`

归档位置：
- `archive/legacy_tests/`
- `archive/legacy_examples/`
- 当前保留原则：`archive/legacy_tests/` 只保留索引说明，不再保留可执行旧测试集；`archive/legacy_examples/` 仅保留少量静态样例。

### 旧文档与旧规格

- 原 `README.md`
- 原 `docs/PROJECT_SPEC.md`
- 旧采集、数据库、失败规则、查询词说明文档

归档位置：
- `archive/legacy_specs/`
- 当前保留原则：只保留不带当前运行承诺的最小静态参考；`AI4S_DATABASE_DIAGRAMS.drawio` 可继续保留，其余旧操作手册、项目规格和历史 manifest 以索引说明替代。

### 旧导出与过程性产物

- 原 `data/exports/` 中除正式论文产物外的全部过程性结果

归档位置：
- `archive/legacy_exports/README.md`
- 当前保留原则：以索引说明替代大批过程目录与 CSV / Parquet 导出物

## 三、待审查

以下内容当前仓库中仍需进一步判断是否要转入活跃主线：

- grounded theory 相关历史产物
- legacy drawio 数据库图
- 零散运行残留文件（已处理根目录 `ai4s_xhs.db` 与 `cdp_session.lock`，其余持续巡检）

当前处理原则：
- 先保留，不删除
- 如暂看不出研究直接用途，则进入 `junk_review/`
