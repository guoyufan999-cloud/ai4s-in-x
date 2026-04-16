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

用途：保存研究使用的帖子层记录，是分析“科研工作流环节”和“帖子层合法性判断”的核心表。

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
| `workflow_stage` | TEXT | 当前迁移的工作流主环节 |
| `primary_legitimacy_stance` | TEXT | 当前帖子层主要态度/合法性判断取向 |
| `import_batch_id` | INTEGER | 对应导入批次 |
| `notes` | TEXT | 研究备注 |

### 2. `comments`

用途：保存评论层记录，用于分析态度表达、合法性依据和边界协商。

| 字段 | 类型建议 | 含义 |
|---|---|---|
| `comment_id` | TEXT PRIMARY KEY | 评论唯一标识 |
| `post_id` | TEXT | 所属帖子 |
| `parent_comment_id` | TEXT | 父评论，可为空 |
| `comment_date` | TEXT | 评论日期 |
| `comment_text` | TEXT | 评论正文 |
| `commenter_id_hashed` | TEXT | 哈希化评论者标识 |
| `stance` | TEXT | 评论层态度取向 |
| `legitimacy_basis` | TEXT | 评论中主要合法性依据或争议方向 |
| `is_reply` | INTEGER | 是否为回复 |
| `import_batch_id` | INTEGER | 对应导入批次 |

### 3. `codes`

用途：保存帖子或评论的结构化编码结果，支持多轮人工或半自动编码。

| 字段 | 类型建议 | 含义 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | 记录主键 |
| `record_id` | TEXT | 对应帖子或评论 ID |
| `record_type` | TEXT | `post / comment` |
| `parent_id` | TEXT | 上位记录 ID，例如评论所属帖子 |
| `workflow_stage_code` | TEXT | 工作流环节编码 |
| `ai_practice_code` | TEXT | AI 实践方式编码 |
| `legitimacy_code` | TEXT | 合法性判断编码 |
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

## 四、主键与关联关系

- `posts.post_id` 是帖子主键
- `comments.post_id` 外键关联 `posts.post_id`
- `codes.record_id + record_type` 逻辑上关联 `posts` 或 `comments`
- `codebook.code_id` 与 `codes.*_code` 形成编码定义关系
- `import_batches.batch_id` 关联 `posts.import_batch_id` 与 `comments.import_batch_id`

## 五、缺失值规则

- 时间无法确定时使用 `NULL`，不使用伪日期
- `engagement_collect` 当前无法稳定取得时允许为 `NULL`
- 尚未进入人工细分编码的 `ai_practice_code / boundary_negotiation_code` 允许为 `NULL`
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

### `paper_scope_quality_v4`

- 定义：当前正式论文口径，严格对应 `quality_v4`
- 帖子规则：
  - `sample_status in ('true', 'review_needed')`
  - 排除 `tool_vendor_or_promotional`
  - `legacy_crawl_status='crawled'`
  - `post_date` 位于 `2024-01-01` 至 `2026-06-30`
- 评论规则：
  - 上级帖子已进入 `paper_scope_quality_v4`
  - `comment_date` 位于 `2024-01-01` 至 `2026-06-30`
- 帖子接口：`vw_posts_paper_scope_quality_v4`
- 评论接口：`vw_comments_paper_scope_quality_v4`
- 用途：当前论文图表、正式结果与投稿写作的唯一主接口

## 七、清洗与标准化规则

1. 日期统一为 `YYYY-MM-DD`
2. 文本统一去除多余空白字符
3. 用户 ID 哈希化
4. 用户名掩码化
5. legacy `workflow_primary` 迁移到 `posts.workflow_stage` 和 `codes.workflow_stage_code`
6. legacy `attitude_polarity` 迁移到 `posts.primary_legitimacy_stance` 或评论 `stance`
7. legacy `controversy_type` 迁移到 `comments.legitimacy_basis` 或 `codes.boundary_negotiation_code`
8. legacy `crawl_status` 迁移到 `posts.legacy_crawl_status`，用于复现 `quality_v4` 正式口径
9. legacy `qs_broad_subject` 迁移到 `posts.qs_broad_subject`

## 八、当前设计的已知薄弱点

- 新研究主库仍需从 legacy 库迁移生成，当前仓库中的历史运行库仍是更完整的原始来源
- `AI 实践方式` 与 `边界协商机制` 的细粒度编码尚未全部回填到数据库，只完成了框架和迁移承接
- `engagement_collect` 等平台指标在 legacy 体系中并不完整，研究分析需谨慎解释
- 正式论文图表与结果已经统一由研究主库 `paper_scope_quality_v4` 直接复现，但更细粒度的历史过程产物不再作为活跃主线接口保留
