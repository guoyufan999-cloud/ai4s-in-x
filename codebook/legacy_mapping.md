# Legacy 标签向研究型编码框架的映射说明

## 一、概述

本文档记录 legacy 运行库中的标签字段如何映射到新的研究型主库。映射逻辑的代码实现位于 `src/ai4s_legitimacy/collection/import_legacy_sqlite.py`，编码种子数据位于 `src/ai4s_legitimacy/coding/codebook_seed.py`。

映射原则：
1. 旧字段可以映射到新字段，但必须写明映射逻辑
2. 无法可靠映射的字段不强行对齐，保留为待人工补充
3. 新 codebook 优先面向研究问题，而非面向旧工程字段命名

## 二、帖子级字段映射

| Legacy 来源表 | Legacy 字段 | 研究主库表 | 研究主库字段 | 映射类型 | 说明 |
|---|---|---|---|---|---|
| `note_details` | `note_id` | `posts` | `post_id` | 1:1 直接 | 主键，值不变 |
| `note_details` | `crawl_status` | `posts` | `legacy_crawl_status` | 1:1 直接 | 值不变，用于 quality_v4 口径筛选 |
| `note_details` | `canonical_url` / `source_url` | `posts` | `post_url` | 1:1 直接 | 优先取 canonical_url |
| `note_details` | `author_id` | `posts` | `author_id_hashed` | 变换 | SHA1 哈希化 |
| `authors` | `author_name` | `posts` | `author_name_masked` | 变换 | 掩码化（首尾保留，中间用 * 替代） |
| `note_details` | `publish_time` | `posts` | `post_date` | 标准化 | 统一为 YYYY-MM-DD |
| `note_details` | `updated_at` / `created_at` | `posts` | `capture_date` | 标准化 | 统一为 YYYY-MM-DD |
| `note_details` | `title` | `posts` | `title` | 1:1 直接 | 空白字符规范化 |
| `note_details` | `full_text` | `posts` | `content_text` | 1:1 直接 | 空白字符规范化 |
| `note_candidates` | `likes_text` | `posts` | `engagement_like` | 解析 | 文本→整数（支持"万"/"w"） |
| `comments` 聚合 | `COUNT(*)` | `posts` | `engagement_comment` | 聚合 | 按帖子聚合评论数 |
| `note_candidates` | `query_text` | `posts` | `keyword_query` | 聚合 | 多个查询词用 `\|` 连接 |
| `coding_labels_posts` | `sample_status` | `posts` | `sample_status` | 1:1 直接 | 值域：true / false / review_needed |
| `coding_labels_posts` | `actor_type` | `posts` | `actor_type` | 1:1 直接 | 值域：graduate_student / faculty / tool_vendor_or_promotional / institution / lab_or_group / undergraduate_research / uncertain |
| `coding_labels_posts` | `qs_broad_subject` | `posts` | `qs_broad_subject` | 1:1 直接 | 英文值：Engineering & Technology / Arts & Humanities / Natural Sciences / Life Sciences & Medicine / Social Sciences & Management / uncertain |
| `coding_labels_posts` | `workflow_primary` | `posts` | `workflow_stage` | 1:1 直接 | 中文标签原样保留 |
| `coding_labels_posts` | `workflow_primary` | `codes` | `workflow_stage_code` | 映射 | 中文→英文编码，见第四节 |
| `coding_labels_posts` | `attitude_polarity` | `posts` | `primary_legitimacy_stance` | 1:1 直接 | 中文标签：积极采用 / 积极但保留 / 中性经验帖 / 批判/担忧 / 明确拒绝 |
| `coding_labels_posts` | `ai_tools_json` | `posts` | `ai_tools_json` | 1:1 直接 | JSON 数组原样保留 |
| `coding_labels_posts` | `risk_themes_json` | `posts` | `risk_themes_json` | 1:1 直接 | JSON 数组原样保留 |
| `coding_labels_posts` | `benefit_themes_json` | — | — | **未迁移** | 见第五节 |
| `coding_labels_posts` | `workflow_secondary_json` | — | — | **未迁移** | legacy 中全为 `[]`，无有效数据 |
| `coding_labels_posts` | `decided_by` | `codes` | `coder` | 变换 | 非空值保留；空值转为 `legacy_rule` |
| `coding_labels_posts` | `review_override` | `codes` | `confidence` | 派生 | override=1 → 0.85；否则 → 0.65 |
| `coding_labels_posts` | `decided_by` + `review_override` | `posts` | `notes` | 组合 | 存为 `legacy_decided_by=...; legacy_review_override=...` |

## 三、评论级字段映射

| Legacy 来源表 | Legacy 字段 | 研究主库表 | 研究主库字段 | 映射类型 | 说明 |
|---|---|---|---|---|---|
| `comments` | `comment_id` | `comments` | `comment_id` | 1:1 直接 | 主键 |
| `comments` | `note_id` | `comments` | `post_id` | 1:1 直接 | 外键 |
| `comments` | `parent_comment_id` | `comments` | `parent_comment_id` | 1:1 直接 | 非空时保留 |
| `comments` | `comment_time` | `comments` | `comment_date` | 标准化 | 统一为 YYYY-MM-DD |
| `comments` | `comment_text` | `comments` | `comment_text` | 1:1 直接 | 空白字符规范化 |
| `comments` | `commenter_id` / `commenter_name` | `comments` | `commenter_id_hashed` | 变换 | SHA1 哈希化，优先取 commenter_id |
| `coding_labels_comments` | `attitude_polarity` | `comments` | `stance` | 1:1 直接 | 与帖子相同的 5 个中文值 |
| `coding_labels_comments` | `controversy_type` | `comments` | `legitimacy_basis` | 1:1 直接 | 仅有一个值：risk |
| `coding_labels_comments` | `controversy_type` | `codes` | `boundary_negotiation_code` | 条件映射 | risk → `boundary.assistance_vs_substitution`；否则 NULL |
| `coding_labels_comments` | `workflow_primary` | `codes` | `workflow_stage_code` | 映射 | 同帖子级映射，见第四节 |
| `coding_labels_comments` | `benefit_themes_json` | — | — | **未迁移** | 见第五节 |
| `coding_labels_comments` | `ai_tools_json` | — | — | **未迁移** | 继承自父帖子，非评论特有 |
| `coding_labels_comments` | `risk_themes_json` | — | — | **未迁移** | 继承自父帖子，非评论特有 |

## 四、工作流中文→英文编码映射

| Legacy 中文标签 | 研究主库编码 | codebook 中的名称 | 注意 |
|---|---|---|---|
| 选题与问题定义 | `workflow.topic_definition` | 选题与问题定义 | 直接匹配 |
| 文献检索与综述 | `workflow.literature_review` | 文献检索与阅读 | codebook 用"阅读"，legacy 用"综述" |
| 研究设计与实验/方案制定 | `workflow.research_design` | 研究设计 | 直接匹配 |
| 数据获取与预处理 | `workflow.data_processing` | 数据处理 | 直接匹配 |
| 编码/建模/统计分析 | `workflow.modeling_computation` | 建模与计算 | 直接匹配 |
| 论文写作/投稿/审稿回复 | `workflow.paper_writing` | 论文写作 | legacy 合并了写作+投稿+答辩 |
| 学术交流与科研管理 | `workflow.collaboration_management` | 协作与项目管理 | 直接匹配 |

**无 legacy 对应的 codebook 类目（需人工编码）：**

| codebook 编码 | codebook 名称 | 说明 |
|---|---|---|
| `workflow.hypothesis_formation` | 假设形成 | legacy 中未单独区分 |
| `workflow.result_interpretation` | 结果解释 | legacy 中未单独区分 |
| `workflow.visualization_presentation` | 可视化呈现 | legacy 中未单独区分 |

**`uncertain` 的处理：** legacy 中 `workflow_primary` 为空或标记为 uncertain 的帖子，在 `posts.workflow_stage` 中保留为 `uncertain`，在 `codes.workflow_stage_code` 中不写入编码（NULL）。

## 五、未迁移字段

### 5.1 `benefit_themes_json`

- **来源：** `coding_labels_posts.benefit_themes_json` 和 `coding_labels_comments.benefit_themes_json`
- **数据量：** 1,861 个帖子 + 2,513 个评论有非空值
- **值域：** 3 个独立值
  - `efficiency`：效率提升
  - `coding_support`：编程辅助
  - `idea_generation`：思路生成
- **当前状态：** 未迁移到研究主库
- **后续计划：** 在 P1-5 阶段迁移到研究主库的 `posts.benefit_themes_json` 和 `comments.benefit_themes_json`

### 5.2 `workflow_secondary_json`

- **来源：** `coding_labels_posts.workflow_secondary_json`
- **数据量：** legacy 中全为 `[]`，无有效数据
- **后续计划：** 暂不迁移。如后续需要多标签工作流编码，应在 `codes` 表中通过多行记录实现

### 5.3 评论的 `ai_tools_json` / `risk_themes_json`

- **来源：** `coding_labels_comments`
- **说明：** 评论的工具和风险主题继承自父帖子，非评论特有标签
- **后续计划：** 不在评论级别单独存储。如需查询评论关联的工具/风险主题，通过 `comments.post_id` 关联 `posts` 表获取

## 六、待人工编码字段

以下 `codes` 表字段当前为空或极少填充，需要人工编码才能产生有效数据：

| 字段 | 当前状态 | codebook 条目数 | 说明 |
|---|---|---|---|
| `codes.ai_practice_code` | **全 NULL** | 7 | 替代执行 / 辅助建议 / 自动生成 / 结构化整理 / 质量检查 / 解释支持 / 协作协调 |
| `codes.legitimacy_code` | **全 NULL** | 10 | 效率正当性 / 专业能力边界 / 原创性 / 学术诚信 / 可解释性 / 可复现性 / 责任归属 / 工具适配性 / 学科规范一致性 / 教育·训练价值 |
| `codes.boundary_negotiation_code` | **部分填充** | 6 | 仅 `boundary.assistance_vs_substitution`（来自 `controversy_type=risk` 的条件映射，1,363 条评论）。其余 5 个编码需人工补充 |

当前 `paper_scope_quality_v5` 的活跃重建链不再把 `ai_practice` 作为正式主轴；正式筛选与编码以 canonical JSONL 中的 `claim_units` 和帖子/评论层归并摘要为准，`quality_v4` 仅保留为历史审计快照。

后续若需要保留 `ai_practice` 历史字段，应明确视其为独立扩展轮次，而不是继续把它与当前活跃的 `A/B/C/D` 研究口径混用。
