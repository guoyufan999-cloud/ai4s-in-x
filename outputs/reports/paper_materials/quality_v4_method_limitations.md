# quality_v4 正式冻结版 Method & Limitations

## Method Strengthening
- 当前正式基线：`quality_v4 正式冻结版`
- 第二轮结构修补 merged review：`235` 行
- `llm_auto_applied=1`：`223`；`llm_manual_check_required=1`：`0`
- 移出主样本：`194`；宣传/推广 actor override：`6`
- 评论继承抽样审计：`3` 条

## Main-Sample Boundary
- 当前数据库仍尽量保留原始记录，但论文主结果只采用 `quality_v4` 口径。
- 被移出的 `194` 条帖子不删除、不回退，只作为补充材料保留，用于解释样本边界收紧逻辑。

## Remaining Limits
- `queued`：`22`
- `temporarily_unavailable_300031`：`43`；`needs_manual_check`：`5`
- 最新媒体审计 `formal_media_gap`：`2218`
- 弱时间段：2024H1、2024H2、2025H1
- 弱学科：Social Sciences & Management、Life Sciences & Medicine、Natural Sciences
- 弱流程：学术交流与科研管理、数据获取与预处理、论文写作/投稿/审稿回复、研究设计与实验/方案制定
- 代表性薄单元格：2024H1 | Arts & Humanities | 研究设计与实验/方案制定=`1`、2024H1 | Engineering & Technology | uncertain=`1`、2024H1 | Engineering & Technology | 研究设计与实验/方案制定=`1`、2024H1 | Life Sciences & Medicine | 编码/建模/统计分析=`1`、2024H1 | Natural Sciences | 数据获取与预处理=`1`、2024H1 | uncertain | 数据获取与预处理=`1`、2024H1 | uncertain | 文献检索与综述=`1`、2024H1 | uncertain | 选题与问题定义=`1`

## Interpretation Rule
- 以上尾部债务作为论文方法限制单列说明，不再反向阻断当前写作主线。
- 若后续重新打开数据主线，必须以明确的论文阻断为依据，而不是惯性继续扩采或补媒体。
