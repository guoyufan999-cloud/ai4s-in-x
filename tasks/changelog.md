# Changelog

## 2026-04-14｜研究工程仓库重构（第一轮）

### 做了什么

- 将旧运行代码、旧自动采集入口、旧运维脚本、旧浏览器运行环境整体迁入 `archive/legacy_collection_runtime/`
- 将旧测试迁入 `archive/legacy_tests/`，旧示例迁入 `archive/legacy_examples/`
- 将旧项目说明、运行规格、采集方法等历史文档迁入 `archive/legacy_specs/`
- 将 `data/exports` 迁入 `archive/legacy_exports/exports_legacy/`
- 将当前仍有论文价值的正式产物迁入新 `outputs/` 结构：
  - `paper_materials`
  - `paper_figures_submission`
  - `quality_v4` 冻结文件
- 将二进制媒体目录 `data/media` 重排到 `data/raw/media_files/`
- 创建新的研究型骨架：
  - `database/`
  - `src/`
  - `codebook/`
  - `outputs/`
  - `tasks/`
  - `junk_review/`
- 新增研究型文档：
  - `README.md`
  - `research_brief.md`
  - `analysis_plan.md`
  - `compliance_and_ethics.md`
  - `data/data_schema.md`
  - `database/schema.sql`
  - `database/views.sql`
  - `codebook/*`
  - `tasks/*`

### 为什么这样做

- 当前仓库已经进入“以稳定结果出论文”的阶段，旧自动采集与恢复 runner 已不适合作为默认主线
- 现有结构过度围绕运行链组织，不利于负责人快速理解研究问题、数据库结构、编码框架与当前进度
- 需要把仓库显式改造为研究问题导向、合规边界清晰、可复现的研究工程结构

### 影响了哪些文件与目录

- 根目录：`README.md`、`.gitignore`
- 新增：`research_brief.md`、`analysis_plan.md`、`compliance_and_ethics.md`
- 新增：`database/`、`src/`、`codebook/`、`tasks/`
- 迁移：`ai4s_xhs/`、`scripts/`、`docker/`、`opencli*`、`tests/`、`examples/`
- 重排：`data/exports/`、`data/media/`

### 下一步

1. 建立并验证研究型主库迁移脚本
2. 在新主库上接管最小清洗与编码准备流程
3. 完成剩余未分类内容的归档或待审查整理

## 2026-04-15｜重构收口与可运行验收

### 做了什么

- 运行并验证 legacy -> research 主库迁移脚本，成功生成：
  - `data/processed/ai4s_legitimacy.sqlite3`
  - `data/interim/legacy_to_research_migration_summary.json`
- 为迁移脚本增加“直接执行入口”兼容：
  - 现在同时支持 `python3 src/collection/import_legacy_sqlite.py --overwrite`
  - 和 `python3 -m src.collection.import_legacy_sqlite --overwrite`
- 补齐并通过新仓库最小测试链路：
  - `tests/test_schema.py`
  - `tests/test_cleaning.py`
  - `tests/test_coding_rules.py`
  - `tests/test_analysis_consistency.py`
  - 全量结果：`12 passed`
- 补齐 `notebooks/` 四个阶段性审查入口：
  - `01_data_audit.ipynb`
  - `02_cleaning_checks.ipynb`
  - `03_coding_exploration.ipynb`
  - `04_analysis_outputs.ipynb`
- 新增 `quality_v4` 一致性检查脚本并生成报告：
  - `src/analysis/quality_v4_consistency.py`
  - `data/interim/quality_v4_consistency_report.json`
  - 当前发现 `sample_status='true'` 口径与 `quality_v4` 冻结存在差异（posts `+51`，comments `+1536`）
- 清理根目录数据残留：
  - `data/ai4s_xhs.db` 迁入 `archive/legacy_collection_runtime/data/db/`
  - `data/cdp_session.lock` 迁入 `archive/legacy_collection_runtime/data/runtime_state/`

### 为什么这样做

- 第一轮重构后需要尽快确认“新骨架不是静态文档”，而是已经具备最小可运行能力
- 迁移脚本入口不稳定会影响负责人和协作者上手效率，因此优先修复
- 需要用可执行测试证明 schema、清洗函数和编码种子至少在当前版本内一致可用
- notebook 占位文件用于固定研究审查节奏，避免后续探索逻辑散落

### 影响了哪些文件与目录

- 更新：`src/collection/import_legacy_sqlite.py`
- 新增：`src/analysis/quality_v4_consistency.py`
- 新增：`notebooks/01_data_audit.ipynb`
- 新增：`notebooks/02_cleaning_checks.ipynb`
- 新增：`notebooks/03_coding_exploration.ipynb`
- 新增：`notebooks/04_analysis_outputs.ipynb`
- 新增：`tests/test_analysis_consistency.py`
- 迁移：`data/ai4s_xhs.db` -> `archive/legacy_collection_runtime/data/db/ai4s_xhs_root_legacy_copy.db`
- 迁移：`data/cdp_session.lock` -> `archive/legacy_collection_runtime/data/runtime_state/cdp_session.lock`

### 下一步

1. 定位并解释 `quality_v4` 冻结口径与研究主库 `sample_status=true` 的差异来源
2. 在 `src/analysis/` 补充从研究主库直接导出投稿指标的脚本
3. 完成投稿总稿与 `outputs/figures/paper_figures_submission/` 的路径联动校验

## 2026-04-15｜`quality_v4` 正式口径对齐完成

### 做了什么

- 在研究型主库 schema 中补入复现正式论文口径所需的字段：
  - `posts.legacy_crawl_status`
  - `posts.qs_broad_subject`
- 更新 legacy -> research 迁移脚本，把 legacy `crawl_status` 与 `qs_broad_subject` 正式写入新主库
- 重写 `database/views.sql`，显式区分三套口径：
  - `candidate_scope`
  - `research_scope`
  - `paper_scope_quality_v4`
- 新增 `paper_scope_quality_v4` 对应的正式分析接口：
  - 帖子正式集合视图
  - 评论正式集合视图
  - scope counts 视图
  - 时间、学科、流程、评论态度分布视图
- 重写 `src/analysis/reporting.py`，使其直接从研究主库导出：
  - `research_db_summary.json`
  - `paper_quality_v4` 关键统计
- 重写 `src/analysis/quality_v4_consistency.py`，将比较逻辑从“`sample_status=true`”改为“正式论文口径”
- 重新迁移、重新导出、重新测试，确认：
  - `formal_posts = 3067`
  - `formal_comments = 69880`
  - 与 `quality_v4_freeze_checkpoint.json` 一致
- 明确解释此前差异来源：
  - 不是主库多抓了 `51` 帖和 `1536` 评论
  - 而是早先误把 `sample_status='true'` 当作正式论文口径
  - 正式 `quality_v4` 实际口径为：`sample_status in ('true','review_needed')`，并叠加排除宣传账号、抓取成功、研究时间窗限制

### 为什么这样做

- 新研究型仓库如果不能稳定复现 `quality_v4`，就仍然只是 legacy 结果的“镜像壳”，还没有真正接管论文主事实源
- 先把正式口径写进数据库接口，后续图表、正文、补充材料和编码扩展才不会再次发生口径漂移
- 显式区分三套口径，可以避免把研究准备样本误写成正式论文主样本

### 影响了哪些文件与目录

- 更新：`database/schema.sql`
- 更新：`database/views.sql`
- 更新：`src/collection/import_legacy_sqlite.py`
- 更新：`src/analysis/reporting.py`
- 更新：`src/analysis/quality_v4_consistency.py`
- 更新：`data/data_schema.md`
- 更新：`tests/test_schema.py`
- 更新：`tests/test_analysis_consistency.py`
- 生成：`data/processed/research_db_summary.json`
- 生成：`data/interim/quality_v4_consistency_report.json`

### 下一步

1. 用 `paper_scope_quality_v4` 复核投稿版总稿中的关键数字、图题和正文表述
2. 继续精修摘要、引言、讨论与结论，使写作链完全切到新主库正式口径
3. 把工具生态、风险主题等仍主要停留在 legacy 导出的指标逐步迁入研究主库

## 2026-04-15｜投稿交付链统一（quality_v4）

### 做了什么

- 新增 `quality_v4_evidence_matrix.md`，登记投稿版总稿中的核心数字、6 张正文图及其来源标签
- 将投稿版图表 manifest 的输出路径统一切到 `outputs/figures/paper_figures_submission/quality_v4`
- 在图表 manifest 中显式区分：
  - `paper_scope_quality_v4`
  - `legacy_bridge_temp`
- 修正投稿版结果章节与投稿版总稿中的正文插图相对路径，统一改为当前 `outputs/` 目录下可解析的真实路径
- 在正文结果章节与总稿中补充来源说明：
  - 时间、学科、流程、评论态度统计由 `paper_scope_quality_v4` 直接复现
  - 工具生态与风险主题仍为 `legacy_bridge_temp`
- 更新活跃 paper materials / freeze checkpoint 元数据：
  - 清除残留 `data/exports/...` 路径
  - 补入 evidence matrix 路径
  - 补入交付链来源契约
- 新增 `tests/test_submission_artifacts.py`，用于校验：
  - 正文图路径存在
  - 活跃 manifest 不再回指 `data/exports`
  - source contract 存在且图表路径可解析

### 为什么这样做

- 口径对齐已经完成，如果交付链仍保留旧路径和旧来源说明，后续精修正文时仍会反复混入 legacy 语义
- 先把“数据库—图表—正文—manifest—freeze 说明”统一到同一套活跃交付链，后续论文精修才能真正建立在单一正式事实源上
- 对工具生态与风险主题采用显式临时桥接，比继续隐式混用 legacy 导出更可审计、更不容易返工

### 影响了哪些文件与目录

- 新增：`outputs/reports/paper_materials/quality_v4_evidence_matrix.md`
- 更新：`outputs/figures/paper_figures_submission/quality_v4/paper_figures_submission_manifest.md`
- 更新：`outputs/reports/paper_materials/paper_results_chapter_submission_cn.md`
- 更新：`outputs/reports/paper_materials/paper_master_manuscript_submission_cn.md`
- 更新：`outputs/reports/paper_materials/paper_results_snapshot.md`
- 更新：`outputs/reports/paper_materials/paper_materials_manifest.json`
- 更新：`outputs/reports/freeze_checkpoints/quality_v4_freeze_checkpoint.json`
- 更新：`outputs/reports/freeze_checkpoints/quality_v4_freeze_checkpoint.md`
- 新增：`tests/test_submission_artifacts.py`
- 更新：`tasks/backlog.md`

### 下一步

1. 在当前统一后的交付链上继续精修摘要、引言、讨论与结论
2. 评估工具生态与风险主题是否值得从 `legacy_bridge_temp` 迁入研究主库正式视图
3. 准备补充材料与方法透明度附录

## 2026-04-15｜论文精修第一轮（clean submission pass）

### 做了什么

- 在不改动 `quality_v4` 正式口径的前提下，保留带来源标签的投稿版总稿作为内部可审计 working master
- 新增一套 clean 版投稿阅读稿：
  - `paper_abstract_submission_cn_clean.md`
  - `paper_introduction_submission_cn_clean.md`
  - `paper_methods_limitations_submission_cn_clean.md`
  - `paper_results_chapter_submission_cn_clean.md`
  - `paper_discussion_chapter_submission_cn_clean.md`
  - `paper_conclusion_chapter_submission_cn_clean.md`
  - `paper_master_manuscript_submission_cn_clean.md`
- clean 版统一去除了正文中的内部来源标签与过强工程痕迹，但保留现有正式数字、图表路径与论文结构
- 更新 `paper_materials_manifest.json`，把 clean 版摘要、引言、方法、结果、讨论、结论和总稿纳入活跃 paper materials 元数据
- 扩展 `tests/test_submission_artifacts.py`：
  - 将 clean 版总稿和 clean 版结果章节纳入图像路径校验
  - 校验 clean 版文稿不再残留 `paper_scope_quality_v4`、`legacy_bridge_temp`、`data/exports`

### 为什么这样做

- 当前交付链已经统一到 `quality_v4`，下一步最合理的不是回到数据主线，而是把文稿压到更接近中文期刊投稿语气
- 保留 working master 可以维持来源可追溯性；新增 clean 版则可以把“内部审计文本”和“投稿阅读文本”显式分开，减少后续排版和润色时的干扰
- 先形成一版 clean 版阅读稿，有助于后续集中处理摘要、引言、讨论和结论的第二轮深修，而不必再反复清理工程提示语

### 影响了哪些文件与目录

- 新增：`outputs/reports/paper_materials/paper_abstract_submission_cn_clean.md`
- 新增：`outputs/reports/paper_materials/paper_introduction_submission_cn_clean.md`
- 新增：`outputs/reports/paper_materials/paper_methods_limitations_submission_cn_clean.md`
- 新增：`outputs/reports/paper_materials/paper_results_chapter_submission_cn_clean.md`
- 新增：`outputs/reports/paper_materials/paper_discussion_chapter_submission_cn_clean.md`
- 新增：`outputs/reports/paper_materials/paper_conclusion_chapter_submission_cn_clean.md`
- 新增：`outputs/reports/paper_materials/paper_master_manuscript_submission_cn_clean.md`
- 更新：`outputs/reports/paper_materials/paper_materials_manifest.json`
- 更新：`tests/test_submission_artifacts.py`
- 更新：`tasks/backlog.md`

### 下一步

1. 以 clean 版总稿为投稿阅读底稿，继续精修摘要、引言、讨论与结论的第二轮论证
2. 形成补充材料说明与方法透明度附录
3. 视投稿需求决定是否将 clean 版再进一步压成更贴近期刊版式的终稿

## 2026-04-15｜论文精修第二轮（argument tightening pass）

### 做了什么

- 以 clean 版总稿为唯一精修底稿，对摘要、引言、讨论与结论进行了第二轮定向压缩
- 摘要改为更紧凑的“研究问题—样本—发现—结论”结构，保留 `5535 / 3067 / 69880 / 23.77% / 14.18%` 等关键数字不变
- 引言进一步收紧为“研究背景—现有缺口—本文对象与贡献—结构说明”的问题导向写法，减少背景性重复
- 讨论章节从结果复述转向解释性表达，突出：
  - AI4S 扩散的工作流化特征
  - 合法性判断的环节差异
  - 评论区作为边界协商场域
  - 不确定性作为平台表达特征
- 结论章节压缩为更高密度的三点结论与启示，减少与结果段落的重复
- 同步更新 `paper_master_manuscript_submission_cn_clean.md`，使 clean 版总稿与各章节稿保持一致
- 更新 `tasks/roadmap.md` 与 `tasks/backlog.md`，将第二轮精修标记为已完成，并把“方法透明度附录与补充材料说明”提升为下一优先级

### 为什么这样做

- 第一轮 clean submission pass 已完成“去工程标签”和“形成阅读稿”的任务，第二轮需要进一步提升可投性，而不是继续增加结果或扩展分析范围
- 当前正式口径已经稳定，继续动数据主线的收益明显低于继续压缩论文措辞、提高问题意识和论证密度
- 先把摘要、引言、讨论和结论收紧，可以让总稿更接近“可送导师/可投中文期刊”的状态，也为下一步补充方法透明度附录留出更清晰的正文边界

### 影响了哪些文件与目录

- 更新：`outputs/reports/paper_materials/paper_abstract_submission_cn_clean.md`
- 更新：`outputs/reports/paper_materials/paper_introduction_submission_cn_clean.md`
- 更新：`outputs/reports/paper_materials/paper_discussion_chapter_submission_cn_clean.md`
- 更新：`outputs/reports/paper_materials/paper_conclusion_chapter_submission_cn_clean.md`
- 更新：`outputs/reports/paper_materials/paper_master_manuscript_submission_cn_clean.md`
- 更新：`tasks/roadmap.md`
- 更新：`tasks/backlog.md`

### 下一步

1. 补一版“方法透明度 + 补充材料说明”附录，集中承接结构修补、评论继承审计与 `legacy_bridge_temp` 说明
2. 视投稿要求，继续压缩摘要、标题、关键词和 clean 版总稿的篇幅
3. 在不打断论文主线的前提下，后置推进 `P1` 的编码与分析基础设施补强

## 2026-04-15｜方法透明度附录与补充材料说明（dual appendix pass）

### 做了什么

- 新增一套双版本附录：
  - `outputs/reports/paper_materials/paper_methods_transparency_appendix_cn.md`
  - `outputs/reports/paper_materials/paper_methods_transparency_appendix_cn_clean.md`
- 两份附录统一按 5 节收口：
  - `A1 正式基线与样本形成`
  - `A2 两轮结构修补与样本边界收紧`
  - `A3 评论继承审计与质量控制`
  - `A4 图表来源契约与临时桥接`
  - `A5 残余限制与补充材料使用方式`
- 内部版保留 `paper_scope_quality_v4`、`legacy_bridge_temp`、freeze contract 与 evidence matrix 的接口说明
- clean 版将同一组事实压成投稿补充材料语气，不再堆叠工程化标签
- 更新 `paper_materials_manifest.json`，把两份附录纳入当前活跃交付链
- 在 `paper_master_manuscript_submission_cn_clean.md` 中增加两处最小附录引用，保证正文与附录之间存在明确阅读入口
- 扩展 `tests/test_submission_artifacts.py`，新增对附录文件存在性、manifest 收录和 clean 主稿引用的校验
- 更新 `tasks/backlog.md` 与 `tasks/roadmap.md`，将附录任务标记为已完成

### 为什么这样做

- 当前正文主稿、图表与正式口径已经稳定，下一步最需要补齐的是一条能同时服务投稿、答辩和方法追溯的附录链路
- 将方法透明度说明集中收口，可以避免结构修补、评论继承审计、临时桥接说明继续分散在多个文件里，降低后续解释成本
- 采用内部版与 clean 版并行的方式，既保留研究工程的可审计性，也给导师和投稿场景提供更干净的阅读版本

### 影响了哪些文件与目录

- 新增：`outputs/reports/paper_materials/paper_methods_transparency_appendix_cn.md`
- 新增：`outputs/reports/paper_materials/paper_methods_transparency_appendix_cn_clean.md`
- 更新：`outputs/reports/paper_materials/paper_materials_manifest.json`
- 更新：`outputs/reports/paper_materials/paper_master_manuscript_submission_cn_clean.md`
- 更新：`tests/test_submission_artifacts.py`
- 更新：`tasks/backlog.md`
- 更新：`tasks/roadmap.md`

## 2026-04-15｜P0/P1 编码与分析基础设施补强完成

### 做了什么

- 清理并归档剩余未分类历史文件：
  - 将 `outputs/tables/legacy_analysis_exports/` 整体迁移到 `archive/legacy_exports/`
  - 将冗余 DB 副本移入 `junk_review/legacy_db_copies/`
  - 建立 `junk_review/README.md` 说明清理策略
- 写实 legacy 标签向新编码框架的映射规则：
  - 新增 `codebook/legacy_mapping.md`，覆盖帖子/评论字段映射、工作流中英文编码映射、未迁移字段清单和待人工编码字段清单
  - 更新 `codebook/coding_rules.md` 与 `data/data_schema.md` 添加交叉引用
- 将工具生态、风险主题、收益主题迁入研究主库：
  - 在 schema 中新增 `ai_tools_lookup`、`risk_themes_lookup`、`benefit_themes_lookup` 三个查找表
  - 在 `posts` 和 `comments` 中补入 `benefit_themes_json` 字段
  - 新增 3 个 JSON 解析视图，并在 `import_legacy_sqlite.py` 中完成 benefit_themes 迁移
- 补齐 10 个 `paper_scope_quality_v4` 交叉分析视图：
  - 工作流 × 合法性立场、学科 × 工作流、学科 × 合法性立场、边界协商汇总等 4 个 HIGH 视图
  - AI 实践方式分布、工作流 × AI 实践、合法性维度分布等 3 个 schema 占位视图
  - 评论合法性依据分布、半年度工作流/学科分布等 3 个补充视图
  - 更新 `src/analysis/reporting.py` 添加交叉表汇总函数
- 补齐 codebook 示例与易混淆项：
  - 替换 `src/coding/codebook_seed.py` 中全部 34 处 `示例待补`
  - 更新 `codebook/codebook.md` 中的工作流、AI 实践方式、合法性维度和边界协商机制示例
- 建立帖子与评论的分析摘录工作流：
  - 新增 `src/analysis/excerpt_extraction.py`，支持按工作流环节、合法性立场、边界协商码提取去标识摘录
  - 新增 `tests/test_excerpt_extraction.py` 进行内存 DB 测试
  - 批量生成 19 个初始摘录文件到 `outputs/excerpts/`
- 全局验证：
  - `pytest` 全量通过（20 passed）
  - `quality_v4` 正式口径保持 `3067` 帖 / `69880` 评论
  - `codebook` 表无残余 `示例待补`
  - `figure_generation.py` 可正常运行并输出 9 张投稿图
- 更新 `tasks/roadmap.md` 与 `tasks/backlog.md`，将 P0/P1 任务全部标记为已完成

### 为什么这样做

- 论文交付链（P2）已经稳定，但研究分析基础设施（P1）仍存在 legacy 依赖和文档缺口，会阻碍后续 grounded theory 扩展和人工编码接管
- 通过一次性补齐映射规则、查找表、交叉视图、codebook 示例和摘录工作流，使研究主库成为真正可独立运行的分析事实源
- 将 `quality_v4` 口径锁定与基础设施补强显式分离，保证论文数字不变的同时扩展编码框架的可操作性

### 影响了哪些文件与目录

- 新增：`codebook/legacy_mapping.md`
- 新增：`src/analysis/excerpt_extraction.py`
- 新增：`tests/test_excerpt_extraction.py`
- 新增：`outputs/excerpts/`
- 更新：`database/schema.sql`、`database/views.sql`
- 更新：`src/collection/import_legacy_sqlite.py`
- 更新：`src/analysis/reporting.py`
- 更新：`src/coding/codebook_seed.py`
- 更新：`codebook/codebook.md`、`codebook/coding_rules.md`
- 更新：`tests/test_schema.py`
- 迁移：`outputs/tables/legacy_analysis_exports/` -> `archive/legacy_exports/legacy_analysis_exports/`
- 迁移：冗余 DB 副本 -> `junk_review/legacy_db_copies/`
- 更新：`tasks/backlog.md`、`tasks/roadmap.md`、`tasks/changelog.md`

### 下一步

1. 视投稿需要，进一步压缩 clean 版总稿并生成更贴近期刊排版的终稿
2. 评估 grounded theory 路径如何接入当前活跃主线
3. 视论文审稿反馈决定是否需要第三轮结构修补或补充样本
