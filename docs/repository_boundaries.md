# 仓库边界说明

本仓库是研究工程仓库，不是运行时镜像仓库。版本控制应当优先保留“研究事实”和“正式交付”，而不是保留浏览器缓存、依赖安装目录或临时运行状态。

## 允许版本化的内容

- `src/`、`database/`、`tests/`、`scripts/` 中的源码与工程配置
- `codebook/`、`docs/`、`tasks/` 中的研究规则、备忘与项目决策记录
- `data/external/` 中的参考词表与映射模板
- `outputs/reports/`、`outputs/figures/paper_figures_submission/` 中已纳入正式交付链的论文材料和图表
- `archive/legacy_collection_runtime/data/db/` 中作为历史事实源保留的 legacy SQLite 数据库
- `archive/legacy_collection_runtime/README.md`、`archive/legacy_collection_runtime/PROVENANCE.md`、`archive/legacy_exports/README.md`、`archive/legacy_specs/README.md`、`archive/legacy_tests/README.md` 这类静态档案说明

## 不应版本化的内容

- 浏览器 profile、缓存、Cookie、本地登录态
- `node_modules/`、前端构建产物、临时下载目录
- 仅服务于本地运行的 `.sqlite3-wal`、`.sqlite3-shm`、日志和中间缓存
- 无法作为研究事实引用、也不被当前交付链依赖的运行残留

## 当前执行规则

- 研究主库与正式输出可以保留在仓库中，但中间运行残留必须通过 `.gitignore` 拦截。
- `archive/legacy_collection_runtime/` 只保留 DB 历史事实源与最小 provenance 说明，不再保存 legacy 代码快照、脚本、配置或环境锁文件，也不承诺 archive 可直接运行。
- `archive/legacy_specs/` 与 `archive/legacy_tests/` 只保留索引式说明或静态参考，不再保留会被误读为当前可执行规范的旧操作手册和测试集。
- `archive/legacy_exports/` 只保留索引式静态说明，不再保留大批 CSV / Parquet / rerun 过程目录。
- `database/views.sql` 是由 `database/views.sql.template` 渲染得到的版本化产物；研究时间窗或 paper-scope 规则调整后，应同步更新模板与渲染结果。
