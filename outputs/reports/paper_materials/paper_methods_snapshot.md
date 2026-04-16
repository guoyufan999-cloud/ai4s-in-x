# Paper Methods Snapshot

## Baseline
- 当前正式覆盖截止日：`2026-04-10`
- 当前正式基线：`quality_v4 正式冻结版`
- 对比基线：`quality_v3 正式冻结版`
- 当前采集阶段：`stage_c -> 10000`
- 部署基线：`Docker Desktop + Docker Compose + Google Chrome(linux/amd64) + OpenCLI 1.4.1 + Python pipeline`
- 正式研究时间窗：`2024-01-01` 到 `2026-06-30`
- 正式分析维度：`月度 + 自然季度 + 半年度`，季度与半年度按正式覆盖截止日标注 `"(部分)"`。

## Collection Rules
- 数据口径：广覆盖抓取、后编码筛选，原始库尽量全保留。
- 评论抓取：一级评论最多 `80` 页、二级回复最多 `20` 页，连续 `2` 轮无新增即停止。
- 作者扩展：仅扩命中 `>=2` 条候选帖的作者，每作者最多 `30` 条公开笔记。
- 队列守门：`queued > 500` 优先 drain，`queued > 800` 暂停 harvest。
- 主结果默认排除 `actor_type=tool_vendor_or_promotional`，宣传账号另做附表。

## Quality Strengthening
- 第二轮 structure repair merged review：`235` 行
- `llm_auto_applied=1`：`223`；`override_sample_status=false`：`194`；宣传/推广 actor override：`6`
- 评论继承抽样审计：`3` 条

## Current Quality Focus
- 弱时间段：2024H1、2024H2、2025H1
- 弱学科：Social Sciences & Management、Life Sciences & Medicine、Natural Sciences
- 弱流程：学术交流与科研管理、数据获取与预处理、论文写作/投稿/审稿回复、研究设计与实验/方案制定
- `qs_broad_subject='uncertain'`：`729` 帖（`23.77%`）
- `workflow_primary='uncertain'`：`435` 帖（`14.18%`）

## Residual Limits
- `queued`：`22`；`temporarily_unavailable_300031`：`43`；`needs_manual_check`：`5`
- 最新媒体审计 `formal_media_gap`：`2218`
- 这些尾部债务在当前阶段作为限制说明处理，不再反向阻断论文写作主线。
