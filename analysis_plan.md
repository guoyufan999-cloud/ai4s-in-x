# 分析计划

## 一、整体研究流程

当前项目进入 `quality_v6` 投稿主稿整合阶段。论文正式结果层为 `quality_v6 post-only`，正式帖子 `714`、正式评论 `0`，来源为 `quality_v5 514` + `supplemental_formalization_v1 200`；`quality_v5 post-only 514 / 0` 仍作为工程 guard 保留，`comment_review_v2 deferred`，`quality_v4 historical audit` 仅作历史审计。

本轮执行：

- 理论框架、论文大纲、codebook 和 coding rules 升级
- codebook seed 新增 F/G/H/I/J/K 代码组
- canonical JSONL / `reviewed_records.payload_json` / `claim_units` 支持空的 v2 字段
- `ai4s-build-quality-v6-artifacts` 生成独立 v6 staging-backed paper materials
- `outputs/reports/paper_materials/quality_v6/framework_v2/` 支持 714 条正式帖的 v2 统计和章节材料
- `paper_master_manuscript_quality_v6_submission_cn_clean.md` 集成 v6 口径、外部文献引用和章节表格

本轮不执行：

- 数据抓取
- 评论层正式编码
- 数据库 schema migration
- 自动填充正式 v2 人工编码字段
- 将 `quality_v4` 或 `quality_v5` 旧结果写成当前投稿正式口径

## 二、v2 分析框架

分析流程从旧的：

工作流 -> 合法性评价 -> 边界协商

升级为：

话语情境 -> 实践位置 -> 介入方式 -> 规范评价 -> 边界生成

### 1. 话语情境 `discourse_context`

识别平台、用户展示身份、文本类型与互动形式。当前优先使用既有字段映射：

- `platform_type` -> `platform`
- `user_display_identity` -> `actor_type` / `speaker_position_claimed`
- `text_type` -> `discursive_mode`
- `interaction_form` -> `record_type` / `context_used` / `interaction_level`

### 2. 实践位置 `practice_position`

继续沿用 A 组，但解释为实践位置：

- `A1` 科研生产
- `A2` 科研治理
- `A3` 科研训练与能力建构

### 3. AI介入方式 `ai_intervention_mode`

新增 F 组：

- `F1` 信息辅助
- `F2` 生成辅助
- `F3` 分析建模
- `F4` 判断建议
- `F5` 自动执行
- `F6` 治理监督

### 4. AI介入强度 `ai_intervention_intensity`

新增 G 组：

- `G1` 低强度辅助
- `G2` 中强度共创
- `G3` 高强度替代

介入强度不是由工具名称决定，而是由具体使用方式决定。同样是 ChatGPT，用于翻译文献可能是 `G1`，用于生成论文核心论证可能是 `G3`。

### 5. 规范评价 `normative_evaluation`

B 组保留为规范评价倾向，C 组保留为规范评价标准。旧“合法性”术语不删除，但作为规范评价的历史术语和理论来源处理。

新增 H/I 组：

- H 组评价张力
- I 组正式规范参照

### 6. 边界生成 `boundary_generation`

D 组保留为边界类型与表达方式，新增：

- J 组边界协商机制：条件化、责任化、规范化、风险化
- K 组边界协商结果：辅助合法化、条件合法化、风险问题化、替代去合法化、规范悬置、治理争议化

## 三、编码步骤

1. 先判断话语情境：文本类型、用户身份和互动形式能否从原文或 canonical 字段中识别。
2. 再判断实践位置：AI 是否进入科研生产、科研治理或科研训练与能力建构。
3. 再判断介入方式和强度：AI 具体做了什么，介入到什么程度。
4. 再判断规范评价：倾向、标准、张力和正式规范参照是否有原文证据。
5. 最后判断边界生成：边界类型、协商机制和结果是否能回到原文证据。

允许多重编码，但每个代码都必须能回到原文证据。不能为了凑满五层而补码。

framework v2 补码模板必须复制既有 `post_review_v2` 的 A/B/C/D 字段。`framework_v2_update=true` 导入时若旧字段被改动则拒绝；人工只补 F/G/H/I/J/K，不使用 LLM 预填形成正式字段。

## 四、纳入与剔除

### 纳入标准

- 明确涉及 AI 或可识别 AI 工具
- 能回到科研生产、科研治理、科研传播或科研训练语境
- 至少能支持五层中的一个实质判断

### 默认剔除

- 泛化科技新闻、纯产品广告、普通办公学习、求职编程、低信息口号
- 只有 AI 热点，没有科研实践位置
- 无法提供任何可审计原文证据的材料

## 五、比较分析维度

当前 framework v2 materials 至少支持：

1. 文本类型分布
2. 科研活动场域分布
3. 工作流环节分布
4. AI介入方式分布
5. AI介入强度分布
6. 规范评价标准分布
7. 规范评价倾向分布
8. 评价张力分布
9. 正式规范参照分布
10. 边界类型分布
11. 边界机制分布
12. 边界结果分布

交叉表包括：

- 工作流环节 × AI介入方式
- AI介入方式 × 规范评价标准
- AI介入强度 × 规范评价倾向
- 规范评价标准 × 边界类型
- 评价张力 × 边界协商机制
- 正式规范参照 × 边界类型
- 边界协商机制 × 边界结果

## 六、当前输出边界

`outputs/reports/paper_materials/quality_v6/framework_v2/` 只根据已有 reviewed payload 和 artifacts 输出材料。当前 framework_v2 reviewed 补码已覆盖 `714/714` 条 `quality_v6 post-only` 正式帖子，新增 F/G/H/I/J/K 字段可作为正式 v2 描述性统计使用。

方法边界仍需保留：F/G/H/I/J/K 字段来自 reviewed payload / framework_v2 reviewed 补码流程，可证明覆盖完整性和工程一致性，但不得写作“双人独立人工复核”或“编码完全无误”。如后续论文需要更强方法说服力，应对高强度替代、自动执行、治理监督、正式规范参照和替代去合法化等高风险组合进行人工抽查并记录修正率。
