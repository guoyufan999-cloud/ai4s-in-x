# quality_v4 正式冻结版 Results Claims

## Claim 1
AI4S 讨论在 `2025H2 -> 2026H1(部分)` 明显加速扩散，并伴随覆盖面的同步扩大。

证据：2024H1=`52`、2024H2=`125`、2025H1=`383`、2025H2=`738`、2026H1(部分)=`1769`；季度扩散广度高点为 `2024Q1=`13`、2024Q2=`13`、2024Q3=`16`、2024Q4=`27`、2025Q1=`39`、2025Q2=`34`、2025Q3=`37`、2025Q4=`43`、2026Q1=`46`、2026Q2(部分)=`31``。

## Claim 2
学科分布并不均衡，工程技术与艺术人文是当前最主要的显性入口，但不确定学科占比已被压降到可讨论水平。

证据：Engineering & Technology=`1101`、uncertain=`729`、Arts & Humanities=`700`、Natural Sciences=`201`、Life Sciences & Medicine=`184`、Social Sciences & Management=`152`；`uncertain_subject_share=23.77%`。

## Claim 3
流程讨论集中于文献检索、选题与编码分析，越接近可验证任务，越容易形成相对直接的接受。

证据：文献检索与综述=`790`、选题与问题定义=`697`、编码/建模/统计分析=`530`、uncertain=`435`、研究设计与实验/方案制定=`255`、论文写作/投稿/审稿回复=`200`、数据获取与预处理=`114`、学术交流与科研管理=`46`；高频学科×流程组合：Arts & Humanities×选题与问题定义=`292`、Engineering & Technology×文献检索与综述=`245`、Engineering & Technology×选题与问题定义=`235`、Engineering & Technology×编码/建模/统计分析=`233`、Arts & Humanities×文献检索与综述=`207`、uncertain×文献检索与综述=`197`。

## Claim 4
评论区是规范协商和风险放大的关键场域，`detection` 与 `hallucination` 在评论层更突出。

证据：评论风险=detection=`649`、hallucination=`525`、ethics=`104`；评论争议=none=`68721`、risk=`1159`。

## Claim 5
第二轮结构修补明显收紧了主结果边界，使当前 `quality_v4` 更适合直接进入论文写作。

证据：第二轮 merged review=`235`，自动回填=`223`，移出主样本=`194`。

## Writing Caution
- 结果章节一律以 `quality_v4` 为主基线。
- 不再把媒体尾部缺口当作继续主线，而是作为限制说明单列。
- 被移出主样本的 `194` 条只作为补充材料和方法透明度说明，不回写主结果。
