# AI介入科研活动规范评价研究工程仓库

## 项目简介

本仓库服务于论文《社交媒体中AI介入科研活动的实践呈现、规范评价与边界协商研究》。项目核心任务不是单纯抓取平台内容，而是围绕研究问题建立一套可复现、可审计、可持续迭代的研究工程：从公开讨论材料的整理入库、清洗标准化、编码支持，到规范评价分析和论文输出，形成完整链路。

AI4S 是旧项目表述，主要保留在仓库命名、legacy 迁移和历史审计语境中。当前论文口径更接近宽义 AI4Research，不把 AI 科研实践限定为狭义“AI 用于科学发现”，而是关注 AI 进入科研生产、科研训练与能力建构、科研治理等活动场域的过程。

当前仓库的工程 guard 仍保留 `quality_v5` post-only frozen baseline，以保证既有 514 / 0 交付链可复核；投稿主稿和 active paper materials 已切换到 `quality_v6` post-only formalized result layer。`quality_v4` 不再作为活跃编码主线，而是降级为一次性审计快照与历史对照；此前为自动采集、媒体补强、结构修补恢复服务的运行系统也已被压缩为 `archive/` 中的静态历史档案，只保留 legacy SQLite 历史事实源与最小索引说明，不再作为默认推荐路径。

`quality_v6` 使用 staging DB 将 `quality_v5` 的 514 条正式帖与 `supplemental_formalization_v1` 通过的 200 条小红书补充帖合并，形成 `714 / 0` 的 v6 结果层。该链路不写回 `quality_v5` freeze checkpoint，不启动评论层正式结果；当前代码常量 `ACTIVE_FORMAL_STAGE` 仍保持 `quality_v5` 以保证既有 artifact health 和历史交付链可复核。

## 研究主题

本研究关注的不是泛化的“AI 与科研”，而是五个递进分析层次：

1. 话语情境：讨论以工具推荐、经验分享、教程展示、风险提醒、伦理批评、规范解读或评论争论等何种形式出现。
2. 实践位置：AI 进入科研生产、科研治理、科研训练与能力建构的哪些具体位置。
3. 介入方式：AI 以信息辅助、生成辅助、分析建模、判断建议、自动执行或治理监督等何种方式介入。
4. 规范评价：平台用户如何围绕效率、可靠性、原创性、责任、披露、诚信、公平、训练价值等标准形成评价。
5. 边界生成：讨论中如何通过条件化、责任化、规范化和风险化机制划定合理辅助/不可接受替代、人机分工、科研规范与科研诚信边界。

旧“三线框架”仍保留为可追溯兼容层：科研工作流环节识别映射为实践位置，合法性评价识别映射为规范评价，边界协商机制识别映射为边界生成。

## 当前状态

- 当前工程 guard 阶段：`quality_v5`
- 当前投稿结果层：`quality_v6`
- 当前历史审计基线：`quality_v4`
- `quality_v5` 本轮正式基线：post-only artifact refresh
- `quality_v5` 正式帖子 / 正式评论：`514 / 0`
- `quality_v6` 投稿 post-only 结果层：`714 / 0`，来源为 `quality_v5 514` + `supplemental_formalization_v1 200`
- `comment_review_v2`：本轮明确 deferred；`formal_comments=0` 是设计选择，不是导入遗漏
- `quality_v4` 审计快照帖子 / 评论：`3067 / 69880`
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
- `src/`：源码根目录；实际公共包名为 `ai4s_legitimacy`，实现位于 `src/ai4s_legitimacy/`
- `codebook/`：编码框架、规则、判例与协商记录
- `docs/`：文献札记、研究备忘录、会议记录、图件说明与本地维护文档
- `docs/paper_working/`：版本化保留的工作稿与 LLM 中间稿，不属于正式交付链
- `notebooks/`：本地审查模板 notebook；默认不提交执行输出，不属于正式交付链
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

当前活跃编码框架保留旧 A/B/C/D/E 兼容层，并新增 framework v2 扩展组：

1. `A` 科研工作流环节
2. `B` 合法性评价
3. `C` 评价标准
4. `D` 边界协商
5. `E` 评论/互动层边界协商
6. `F` AI介入方式
7. `G` AI介入强度
8. `H` 评价张力
9. `I` 正式规范参照
10. `J` 边界协商机制
11. `K` 边界协商结果

编码顺序升级为：话语情境 -> 实践位置 -> 介入方式 -> 规范评价 -> 边界生成。只要帖子能支持识别具体科研实践位置、规范评价或边界生成之一，就进入研究候选；泛化“AI 与科研”讨论、纯产品介绍、普通学习办公和低信息帖子默认剔除。现阶段仓库保留了 `quality_v4` 历史编码结果与输出物用于审计追溯；`quality_v5` 主线则通过 staging DB、review queue 与 reviewed import 重新判定样本边界，并以 canonical JSONL、`reviewed_records.payload_json`、`claim_units` 归并摘要和 `outputs/tables/*.jsonl` 作为正式长期协议。

新增 v2 字段优先由 canonical JSONL 和 `reviewed_records.payload_json` 承载；未完成人工编码时允许为空。程序不会自动推断 F/G/H/I/J/K 正式字段，DeepSeek/LLM 预填只生成 draft，人工 reviewed import 才能形成正式结果。

## 如何开始使用项目

建议按以下顺序阅读和使用：

1. 阅读 `research_brief.md`
2. 阅读 `analysis_plan.md`
3. 阅读 `compliance_and_ethics.md`
4. 查看 `data/data_schema.md`、`database/schema.sql`、`archive/legacy_collection_runtime/data/db/README.md` 与 `data/processed/README.md`
5. 按上述两个 README 准备本地 legacy DB 与研究主库路径
6. 首次拉起开发环境或完成包名迁移后，先执行 `./.venv/bin/pip install -e '.[dev]'`；如需严格复现当前 `quality_v5` post-only 验证环境，参考 `docs/runtime_environment_snapshot.md` 并使用 `requirements.lock.txt`
7. 运行 `ai4s-import-legacy --mode rebaseline_quality_v5_staging --audit-snapshot outputs/reports/freeze_checkpoints/quality_v4_audit_snapshot.json`，重建 `quality_v5` 本地研究主库并保留 `quality_v4` 审计快照；当前 `REBASELINE_STAGING_DB_PATH` 指向 `data/processed/ai4s_legitimacy.sqlite3`
8. 使用 `ai4s-prepare-review-batches --phase rescreen_posts` 生成全量 review queue、按批次切分的 JSONL、`batch_00` reviewed 模板与判例 memo，再通过 `ai4s-import-reviewed-decisions` 回写人工审核完成的 reviewed 结果
9. 对正式编码使用 `ai4s-prepare-review-batches --phase post_review_v2`；本轮 `quality_v5` 已接受 post-only 正式基线，`comment_review_v2` 暂不进入正式编码，后续若启动评论层正式结果再单独生成和导入对应队列。review template、reviewed import 与 artifacts 都统一使用 canonical JSONL；帖子/评论层字段只是 `claim_units` 的归并摘要，发生冲突时以 `claim_units` 为准。
10. 对 `post_review_v2` 单个 batch 做 DeepSeek 预填时，先通过环境变量提供 `DEEPSEEK_API_KEY`，再执行 `ai4s-llm-prefill-post-review --queue data/interim/rebaseline_quality_v5/review_queues/post_review_v2.batch_00.jsonl`；输出会落到 `data/interim/rebaseline_quality_v5/reviewed/post_review_v2.batch_00.ai_draft.jsonl`，只生成 canonical 草稿，不会写库。
11. 如需用 DeepSeek 做二次复筛，先通过环境变量提供 `DEEPSEEK_API_KEY`，再执行 `ai4s-llm-rescreen-posts --queue data/interim/rebaseline_quality_v5/review_queues/rescreen_posts.jsonl --shard-count 24 --shard-index 0` 跑单个 shard；全部 shard 完成后再执行 `ai4s-llm-rescreen-posts --queue data/interim/rebaseline_quality_v5/review_queues/rescreen_posts.jsonl --shard-count 24 --merge-only` 合并 full draft、delta、priority 包和分析报告。复筛口径固定为“AI + 具体科研环节 + 实践/评价/规范/边界信息之一”。
12. 如需启动 framework v2 的人工补码轮次，执行 `ai4s-prepare-framework-v2-review-batches`；该入口只导出 `quality_v5` 正式帖子，复制现有 `post_review_v2` 旧字段，并只开放 F/G/H/I/J/K 人工补填，不使用 LLM 预填。
13. 如需把版本化历史导出物统一回 canonical row，执行 `ai4s-backfill-canonical-history`
14. 使用 `ai4s-build-artifacts` 或 `python -m ai4s_legitimacy.analysis.*` 入口重建 `quality_v5` 正式分析产物
15. 如需重建独立 `quality_v6` post-only 结果层，执行 `ai4s-build-quality-v6-artifacts`；该入口复制 `data/processed/ai4s_legitimacy.sqlite3` 到 `data/interim/quality_v6/` staging DB 后导入 200 条 supplemental formalized posts，并输出 `quality_v6` freeze、consistency、provenance、paper materials 与图表包，不覆盖 `quality_v5`

`archive/` 当前不再保留 legacy 代码快照、旧测试或可直接运行的环境镜像；如需追溯历史运行来源，请查看 `archive/legacy_collection_runtime/README.md`、`archive/legacy_collection_runtime/PROVENANCE.md` 与 `archive/legacy_exports/README.md`。

当前活跃的正式核验 JSON 默认落在 `outputs/reports/freeze_checkpoints/`，包括 `research_db_summary.json` 与 `quality_v5_consistency_report.json`；`quality_v4` 同目录文件仅作审计快照保留，不再作为活跃重建结果。

当前 `quality_v5` freeze checkpoint 明确采用 post-only formal scope：正式帖子为 `514` 条、正式评论为 `0` 条。评论层 `comment_review_v2` 的正式编码被延后，后续如需评论层正式结果，应重新准备评论队列、导入 reviewed 结果并重建 artifacts。

当前 `quality_v6` 产物位于 `outputs/reports/paper_materials/quality_v6/`、`outputs/reports/freeze_checkpoints/quality_v6_*` 与 `outputs/figures/paper_figures_submission/quality_v6/`。它现在是投稿主稿结果层，但不改变 `quality_v5` 的 artifact health guard 口径。

当前投稿正式输出已经统一到 `outputs/reports/paper_materials/` 与 `outputs/figures/paper_figures_submission/quality_v6/`；`quality_v5` 保留为前一冻结基线与工程 guard，`quality_v4` 保留为历史审计快照。工作稿和 LLM 中间稿统一放在 `docs/paper_working/`，不属于正式交付链。

推荐入口：

- `ai4s-import-legacy`
- `ai4s-export-baseline-audit`
- `ai4s-export-review-queue`
- `ai4s-prepare-review-batches`
- `ai4s-prepare-framework-v2-review-batches`
- `ai4s-import-reviewed-decisions`
- `ai4s-llm-prefill-post-review`
- `ai4s-llm-rescreen-posts`
- `ai4s-xhs-expansion-candidate-v1`
- `ai4s-build-quality-v6-artifacts`
- `ai4s-backfill-canonical-history`
- `ai4s-build-artifacts`
- `python -m ai4s_legitimacy.analysis.reporting`
- `python -m ai4s_legitimacy.analysis.framework_v2_materials`
- `python -m ai4s_legitimacy.analysis.quality_v5_consistency`
- `python -m ai4s_legitimacy.analysis.quality_v4_consistency`
- `python -m ai4s_legitimacy.analysis.excerpt_extraction --batch`

开发验证建议：

- 标准 `src-layout` 依赖 editable 安装；首次拉起环境或拉到本轮重命名后，先执行 `./.venv/bin/pip install -e '.[dev]'`。
- `requirements.dev.txt` 与 `environment.yml` 仅作为本地开发 convenience wrappers；当前可复现版本快照见 `requirements.lock.txt` 与 `docs/runtime_environment_snapshot.md`。
- 推荐使用 `./.venv/bin/python -B -m pytest -q`，避免在 `src/`、`tests/` 下生成 `__pycache__` / `.pyc`，让工作树更容易保持可提交态。
- 正式交付链验收建议至少执行：`./.venv/bin/ruff check .`、`./.venv/bin/python -m mypy`、`./.venv/bin/python -B -m pytest -q`、`./.venv/bin/python -B scripts/artifact_health.py --json --allow-missing-source-db`、`./.venv/bin/python -B scripts/repo_health.py --json --allow-missing-source-db`。
- `scripts/artifact_health.py` 只检查 formal counts、provenance、0B tracked files 与 WAL/SHM；`scripts/repo_health.py` 在此基础上额外盘点 ignored local cache 体量。
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
- 维护 `quality_v5` post-only 冻结基线作为工程 guard，并以 `quality_v6` 作为当前投稿结果层；`comment_review_v2` 留作后续独立评论层工作流
- 维护 framework v2 输出目录 `outputs/reports/paper_materials/framework_v2/`，只根据已有人工编码生成写作提示和空表说明，不自动生成论文结论
- 如需继续扩宽后续分析数据库，先使用 `ai4s-xhs-expansion-candidate-v1` 生成小红书补充样本候选集；该链路输出 `xhs_expansion_candidate_v1` exploratory artifacts，必须经过新的 formalization 才能进入后续质量层。

下一阶段的优先任务见 `tasks/backlog.md` 与 `tasks/roadmap.md`。

仓库边界约束见 `docs/repository_boundaries.md`，本地 Git 维护说明见 `docs/local_git_maintenance.md`。
