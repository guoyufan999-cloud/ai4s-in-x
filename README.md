# AI4S 合法性研究工程仓库

## 项目简介

本仓库服务于论文《社交媒体中AI4S科研工作流的实践与合法性讨论》。项目核心任务不是单纯抓取平台内容，而是围绕研究问题建立一套可复现、可审计、可持续迭代的研究工程：从公开讨论材料的整理入库、清洗标准化、编码支持，到合法性分析和论文输出，形成完整链路。

当前仓库以 `quality_v4` 作为唯一正式研究基线。围绕该基线生成的投稿版文稿、图表和方法说明，已经转入活跃主线。此前为自动采集、媒体补强、结构修补恢复服务的运行系统已被压缩为 `archive/` 中的静态历史档案，只保留 legacy SQLite 历史事实源与最小索引说明，不再作为默认推荐路径。

## 研究主题

本研究关注两个相互关联的问题：

1. AI 如何嵌入科研工作流的不同环节，并在社交媒体中被呈现为具体实践。
2. 围绕这些实践，平台讨论如何形成差异化的合法性判断，以及这些判断如何通过边界协商被稳定下来。

## 当前状态

- 当前正式论文基线：`quality_v4`
- 当前正式帖子：`3067`
- 当前正式评论：`69880`
- 当前不确定学科占比：`23.77%`
- 当前不确定流程占比：`14.18%`
- 现有 legacy 运行库中：
  - `note_details = 5535`
  - `comments = 106543`
  - `media_assets = 34052`
- 第二轮结构修补已完成并冻结，`194` 条帖子因边界收紧被移出主样本，但原始记录仍保留在历史运行体系中。

## 目录说明

- `research_brief.md`：研究背景、问题、对象、方法和预期产出
- `analysis_plan.md`：研究流程、数据处理步骤、编码与分析路径
- `compliance_and_ethics.md`：公开数据边界、匿名化、引用与风险控制说明
- `data/`：研究数据层
  - `raw/`：原始公开资料、导入文件、历史媒体文件
  - `interim/`：清洗中间产物与迁移审计
  - `processed/`：研究型主库的本地约定路径与版本化说明
  - `external/`：词表、映射表、外部参考配置
- `database/`：研究型数据库 schema、视图与说明
- `src/`：围绕研究流程组织的代码
- `codebook/`：编码框架、规则、判例与协商记录
- `docs/`：文献札记、研究备忘录、会议记录、图件说明与本地维护文档
- `docs/paper_working/`：版本化保留的工作稿与 LLM 中间稿，不属于正式交付链
- `outputs/`：正式图表、表格、摘录和报告
- `tasks/`：backlog、roadmap、changelog、迁移诊断
- `archive/`：静态历史档案、legacy DB 索引与历史参考说明

## 数据流程概览

当前活跃主线按研究工程语义组织为：

1. 在本地将 legacy 历史运行库放在 `archive/legacy_collection_runtime/data/db/ai4s_xhs.sqlite3`；该路径是约定位置，仓库版本化的是说明文件而不是 SQLite 文件本身。
2. 将 legacy 库映射、匿名化并导入本地研究型主库 `data/processed/ai4s_legitimacy.sqlite3`；该主库同样默认由 `.gitignore` 拦截，不作为当前快照自带文件。
3. 在研究型主库中围绕 `posts / comments / codes / codebook` 开展清洗、编码准备与分析。
4. 将正式分析结果输出到 `outputs/`，作为论文写作和审稿回复的直接材料。

## 编码分析流程概览

本研究的编码框架分为四层：

1. 科研工作流环节
2. AI 实践方式
3. 合法性判断维度
4. 边界协商机制

现阶段数据库中已保存 legacy 规则编码和两轮结构修补结果；新主线将这些既有标签转化为可审计的研究型编码表，并在 `codebook/` 中重写为面向研究问题的编码手册。

## 如何开始使用项目

建议按以下顺序阅读和使用：

1. 阅读 `research_brief.md`
2. 阅读 `analysis_plan.md`
3. 阅读 `compliance_and_ethics.md`
4. 查看 `data/data_schema.md`、`database/schema.sql`、`archive/legacy_collection_runtime/data/db/README.md` 与 `data/processed/README.md`
5. 按上述两个 README 准备本地 legacy DB 与研究主库路径
6. 运行 `ai4s-import-legacy`，将 legacy 运行库迁入新的研究型主库
7. 使用 `ai4s-build-artifacts` 或 `python -m src.analysis.*` 入口更新正式分析产物

`archive/` 当前不再保留 legacy 代码快照、旧测试或可直接运行的环境镜像；如需追溯历史运行来源，请查看 `archive/legacy_collection_runtime/README.md`、`archive/legacy_collection_runtime/PROVENANCE.md` 与 `archive/legacy_exports/README.md`。

当前活跃的正式核验 JSON 默认落在 `outputs/reports/freeze_checkpoints/`，包括 `research_db_summary.json` 与 `quality_v4_consistency_report.json`；它们属于版本化正式产物，不再放在 `data/processed/` 或 `data/interim/` 下长期维护。

当前正式投稿稿件、分析快照和图表 manifest 保留在 `outputs/reports/paper_materials/` 与 `outputs/figures/paper_figures_submission/quality_v4/`；工作稿和 LLM 中间稿统一放在 `docs/paper_working/`，不属于正式交付链。

推荐入口：

- `ai4s-import-legacy`
- `ai4s-build-artifacts`
- `python -m src.analysis.reporting`
- `python -m src.analysis.quality_v4_consistency`
- `python -m src.analysis.excerpt_extraction --batch`

开发验证建议：

- 推荐使用 `./.venv/bin/python -B -m pytest -q`，避免在 `src/`、`tests/` 下生成 `__pycache__` / `.pyc`，让工作树更容易保持可提交态。
- 如果此前已经运行过默认测试命令，可在收尾时执行一次 `find src tests -type d -name '__pycache__' -prune -exec rm -rf {} +` 清理本地缓存。

本地历史备份说明：

- 当前活跃主线 `main` 已在 `2026-04-16` 收敛为瘦身后的单根快照提交，用于降低仓库体量并保证 GitHub 推送稳定。
- 原先的本地提交链曾保留在 `backup/pre-clean-snapshot-20260416`；如该分支已在本地瘦身时删除，删除前的最后锚点 SHA 见 `docs/local_git_maintenance.md`。
- 仓库不会自动删除备份分支或自动执行 `git gc`；如需评估旧历史对本地 `.git` 体积的影响、或显式回收空间，请查看 `docs/local_git_maintenance.md`。

## 当前状态与后续计划

当前项目已经完成“从平台数据到正式论文基线”的第一阶段，重点不再是继续补抓，而是：

- 把 legacy 运行工程重构为研究工程仓库
- 完成研究型主库迁移
- 把编码框架、分析视图和输出路径全部研究问题化
- 在 `quality_v4` 基线上继续精修论文正文与分析结果

下一阶段的优先任务见 `tasks/backlog.md` 与 `tasks/roadmap.md`。

仓库边界约束见 `docs/repository_boundaries.md`，本地 Git 维护说明见 `docs/local_git_maintenance.md`。
