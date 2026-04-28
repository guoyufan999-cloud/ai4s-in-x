# 数据结构说明

## 一、总体说明

本项目当前同时存在两套数据体系：

1. **legacy 运行体系**
   - 来源：历史自动采集、媒体补强、结构修补和冻结流程
   - 位置：`archive/legacy_collection_runtime/` 与 `archive/legacy_exports/README.md`
   - 作用：保留历史采集与分析基础的静态档案与索引说明，不再作为活跃研究主接口

2. **研究型主库体系**
   - 来源：从 legacy 运行库迁移、匿名化和标准化后的研究数据库
   - 位置：`data/processed/ai4s_legitimacy.sqlite3`
   - 作用：作为当前研究分析、编码、写作和后续扩展的主接口

本说明文档只定义研究型主库的正式口径。

## 二、核心表

### 1. `posts`

用途：保存研究使用的帖子层记录，是识别 `AI4S 科研工作流实践—合法性评价—边界协商` 的核心表。当前活跃正式编码不再依赖单一 legacy 主标签，而是通过 canonical JSONL、`reviewed_records.payload_json` 和 `claim_units` 归并摘要回填和导出。

| 字段 | 类型建议 | 含义 |
|---|---|---|
| `post_id` | TEXT PRIMARY KEY | 研究主库内帖子唯一标识 |
| `platform` | TEXT | 平台名称，当前固定以 `xiaohongshu` 为主 |
| `legacy_note_id` | TEXT | legacy 运行库中的原始 note_id |
| `legacy_crawl_status` | TEXT | legacy 运行库中的帖子抓取状态，用于复现正式论文口径 |
| `post_url` | TEXT | 公开帖子 URL |
| `author_id_hashed` | TEXT | 哈希化作者标识 |
| `author_name_masked` | TEXT | 掩码化作者名称 |
| `post_date` | TEXT | 发帖日期，统一为 `YYYY-MM-DD` |
| `capture_date` | TEXT | 迁移或采集入库日期 |
| `title` | TEXT | 帖子标题 |
| `content_text` | TEXT | 帖子正文文本 |
| `engagement_like` | INTEGER | 点赞或可替代热度指标 |
| `engagement_comment` | INTEGER | 评论数或可替代评论规模指标 |
| `engagement_collect` | INTEGER | 收藏数；当前仓库中如无法稳定获得可为空 |
| `keyword_query` | TEXT | 命中该帖的主要检索词或检索词摘要 |
| `is_public` | INTEGER | 是否为公开可见内容，默认 `1` |
| `sample_status` | TEXT | 样本状态，保留 `true / false / review_needed` |
| `actor_type` | TEXT | 作者角色类别 |
| `qs_broad_subject` | TEXT | 宽学科归类 |
| `workflow_stage` | TEXT | legacy/过渡期工作流主标签，保留作历史参照 |
| `primary_legitimacy_stance` | TEXT | legacy/过渡期帖子层主要态度标签，保留作历史参照 |
| `import_batch_id` | INTEGER | 对应导入批次 |
| `notes` | TEXT | 研究备注 |

### 2. `comments`

用途：保存评论层记录，用于分析合法性评价与边界协商；当前活跃口径下，评论不自动继承母帖的具体科研环节。

| 字段 | 类型建议 | 含义 |
|---|---|---|
| `comment_id` | TEXT PRIMARY KEY | 评论唯一标识 |
| `post_id` | TEXT | 所属帖子 |
| `parent_comment_id` | TEXT | 父评论，可为空 |
| `comment_date` | TEXT | 评论日期 |
| `comment_text` | TEXT | 评论正文 |
| `commenter_id_hashed` | TEXT | 哈希化评论者标识 |
| `stance` | TEXT | legacy/过渡期评论态度取向，保留作历史参照 |
| `legitimacy_basis` | TEXT | legacy/过渡期评论主要合法性依据，保留作历史参照 |
| `is_reply` | INTEGER | 是否为回复 |
| `import_batch_id` | INTEGER | 对应导入批次 |

### 3. `codes`

用途：保存帖子或评论的结构化编码结果，支持多轮人工或半自动编码。当前活跃正式口径以 `reviewed_records.payload_json` 中的 canonical row 与 `claim_units` 为准；`codes` 更偏向历史迁移与辅助镜像。

| 字段 | 类型建议 | 含义 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | 记录主键 |
| `record_id` | TEXT | 对应帖子或评论 ID |
| `record_type` | TEXT | `post / comment` |
| `parent_id` | TEXT | 上位记录 ID，例如评论所属帖子 |
| `workflow_stage_code` | TEXT | 工作流环节编码 |
| `ai_practice_code` | TEXT | 历史字段/占位字段，当前活跃口径不再把 AI 实践方式作为主轴 |
| `legitimacy_code` | TEXT | 历史字段或辅助编码字段 |
| `boundary_negotiation_code` | TEXT | 边界协商编码 |
| `coder` | TEXT | 编码者或编码来源 |
| `coding_date` | TEXT | 编码日期 |
| `confidence` | REAL | 编码置信度或质量判断 |
| `memo` | TEXT | 编码备注 |

### 4. `codebook`

用途：保存正式 codebook，作为编码定义和分析说明的数据库镜像。

| 字段 | 类型建议 | 含义 |
|---|---|---|
| `code_id` | TEXT PRIMARY KEY | 编码唯一标识 |
| `code_group` | TEXT | 编码所属层级/分组 |
| `code_name` | TEXT | 编码名称 |
| `definition` | TEXT | 定义 |
| `include_rule` | TEXT | 包含标准 |
| `exclude_rule` | TEXT | 排除标准 |
| `example` | TEXT | 示例或示例占位 |

## 三、辅助表

### `import_batches`

记录一次导入/迁移任务的来源、时间、使用的 freeze 基线和迁入规模。

### `source_queries`

保存 legacy 查询词或研究使用的检索词来源，支持追溯“数据从哪里来”。

### `platform_sources`

记录平台来源与公开边界说明，当前主要为 `xiaohongshu`。

### `workflow_stage_lookup`

记录工作流环节的固定顺序、显示名称与定义，支撑视图与图表排序。

### `legitimacy_dimension_lookup`

记录合法性判断维度的固定顺序、显示名称与定义。

### `reviewed_records`

当前活跃的 `post_review_v2 / comment_review_v2` 结构化审核结果保存在本表的 `payload_json` 中。它们使用统一的 canonical JSONL shape，帖子/评论层字段只是 `claim_units` 的归并摘要，是后续研究筛选、复核与材料库建设的正式接口。

## 四、主键与关联关系

- `posts.post_id` 是帖子主键
- `comments.post_id` 外键关联 `posts.post_id`
- `codes.record_id + record_type` 逻辑上关联 `posts` 或 `comments`
- `codebook.code_id` 与 `codes.*_code` 形成编码定义关系
- `import_batches.batch_id` 关联 `posts.import_batch_id` 与 `comments.import_batch_id`

## 五、缺失值规则

- 时间无法确定时使用 `NULL`，不使用伪日期
- `engagement_collect` 当前无法稳定取得时允许为 `NULL`
- 尚未进入人工细分编码的 `ai_practice_code / legitimacy_code / boundary_negotiation_code` 允许为 `NULL`
- `keyword_query` 若同一帖子命中多个检索词，可用连接文本保存摘要

## 六、当前正式使用的三套口径

### `candidate_scope`

- 定义：迁移入研究主库的全量帖子与评论
- 帖子接口：`vw_posts_candidate_scope`
- 评论接口：`vw_comments_candidate_scope`
- 用途：保留全量候选材料，支持追溯与后续人工补充

### `research_scope`

- 定义：研究准备口径，默认纳入 `sample_status in ('true', 'review_needed')`
- 帖子接口：`vw_posts_research_scope`
- 评论接口：`vw_comments_research_scope`
- 用途：支持编码准备、结构核查和研究探索，不等于正式论文主结果

### `paper_scope_quality_v5`

- 定义：当前活跃重建口径，严格对应 `quality_v5`
- 帖子规则：
  - `sample_status in ('true', 'review_needed')`
  - 排除 `tool_vendor_or_promotional`
  - `legacy_crawl_status='crawled'`
  - `post_date` 位于 `2024-01-01` 至 `2026-06-30`
- 评论规则：
  - 上级帖子已进入 `paper_scope_quality_v5`
  - `comment_date` 位于 `2024-01-01` 至 `2026-06-30`
- 帖子接口：`vw_posts_paper_scope_quality_v5`
- 评论接口：`vw_comments_paper_scope_quality_v5`
- 用途：`quality_v5` staging 经 reviewed 导入后，用于重建正式图表、结果与投稿写作主接口；`quality_v4` 仅保留为审计快照

### supplemental / candidate 扩展口径

- 当前小红书补充样本候选集命名为 `xhs_expansion_candidate_v1`
- 输出位置默认为 `outputs/tables/xhs_expansion_candidate_v1/`、`outputs/reports/review_v2/xhs_expansion_candidate_v1.summary.json` 与 `data/interim/xhs_expansion_candidate_v1/review_queues/`
- 用途：扩宽后续分析数据库的候选材料来源；进入正式分析前必须经过人工筛选、去重和单独 reviewed / checkpoint 设计
- 边界：不写入 `vw_posts_paper_scope_quality_v5`，不启动 `comment_review_v2`，不改变 `quality_v5` 正式帖子 / 正式评论 `514 / 0`

## 七、清洗与标准化规则

1. 日期统一为 `YYYY-MM-DD`
2. 文本统一去除多余空白字符
3. 用户 ID 哈希化
4. 用户名掩码化
5. legacy `workflow_primary` 迁移到 `posts.workflow_stage` 和 `codes.workflow_stage_code`
6. legacy `attitude_polarity` 迁移到 `posts.primary_legitimacy_stance` 或评论 `stance`
7. legacy `controversy_type` 迁移到 `comments.legitimacy_basis` 或 `codes.boundary_negotiation_code`
8. legacy `crawl_status` 迁移到 `posts.legacy_crawl_status`，用于复现 `quality_v5` 活跃重建口径，并保留 `quality_v4` 审计对照
9. legacy `qs_broad_subject` 迁移到 `posts.qs_broad_subject`

## 八、当前设计的已知薄弱点

- 新研究主库仍需从 legacy 库迁移生成，当前仓库中的历史运行库仍是更完整的原始来源
- 当前活跃正式分析不再以 `AI 实践方式` 为主轴；正式长期协议改为 canonical JSONL + `claim_units` + 轻派生摘要层
- `engagement_collect` 等平台指标在 legacy 体系中并不完整，研究分析需谨慎解释
- 正式论文图表与结果将由研究主库 `paper_scope_quality_v5` 重新复现；`quality_v4` 输出只作为历史审计快照保留
