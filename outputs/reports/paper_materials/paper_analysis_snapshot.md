# Paper Analysis Snapshot

## Freeze Gap
- 正式研究时间窗：`2024-01-01` 到 `2026-06-30`
- 当前正式覆盖截止日：`2026-04-10`
- 去重候选帖 / 已抓详情：`5535 / 5535`
- 正式帖子 / 正式评论：`3067 / 69880`
- 当前 `crawled / queued / failed`：`5210 / 22 / 298`

## Time Diffusion
- 半年度帖子规模：2024H1=`52`；2024H2=`125`；2025H1=`383`；2025H2=`738`；2026H1(部分)=`1769`
- 季度帖子规模：2024Q1=`15`；2024Q2=`37`；2024Q3=`39`；2024Q4=`86`；2025Q1=`210`；2025Q2=`173`；2025Q3=`239`；2025Q4=`499`；2026Q1=`1603`；2026Q2(部分)=`166`
- 季度扩散广度（非零学科×流程单元格）：2024Q1=`13`；2024Q2=`13`；2024Q3=`16`；2024Q4=`27`；2025Q1=`39`；2025Q2=`34`；2025Q3=`37`；2025Q4=`43`；2026Q1=`46`；2026Q2(部分)=`31`

## Core Findings
- 学科分布：Engineering & Technology=`1101`；uncertain=`729`；Arts & Humanities=`700`；Natural Sciences=`201`；Life Sciences & Medicine=`184`；Social Sciences & Management=`152`
- 流程分布：文献检索与综述=`790`；选题与问题定义=`697`；编码/建模/统计分析=`530`；uncertain=`435`；研究设计与实验/方案制定=`255`；论文写作/投稿/审稿回复=`200`；数据获取与预处理=`114`；学术交流与科研管理=`46`
- 帖子态度：中性经验帖=`1659`；积极但保留=`573`；批判/担忧=`288`；积极采用=`283`；明确拒绝=`264`
- 评论态度：中性经验帖=`67392`；积极采用=`1256`；明确拒绝=`620`；批判/担忧=`424`；积极但保留=`188`
- 帖子风险：hallucination=`292`；detection=`182`；ethics=`105`
- 评论风险：detection=`649`；hallucination=`525`；ethics=`104`
- 评论争议类型：none=`68721`；risk=`1159`

## Subject × Workflow
- `Arts & Humanities × 选题与问题定义`：`292`
- `Engineering & Technology × 文献检索与综述`：`245`
- `Engineering & Technology × 选题与问题定义`：`235`
- `Engineering & Technology × 编码/建模/统计分析`：`233`
- `Arts & Humanities × 文献检索与综述`：`207`
- `uncertain × 文献检索与综述`：`197`
- `uncertain × uncertain`：`186`
- `Engineering & Technology × uncertain`：`172`

## Workflow × Attitude
- `uncertain`：中性经验帖=`336`；积极采用=`40`；批判/担忧=`26`
- `学术交流与科研管理`：中性经验帖=`34`；明确拒绝=`5`；积极但保留=`3`
- `数据获取与预处理`：中性经验帖=`53`；积极但保留=`23`；明确拒绝=`15`
- `文献检索与综述`：中性经验帖=`373`；积极但保留=`169`；批判/担忧=`84`
- `研究设计与实验/方案制定`：中性经验帖=`164`；积极但保留=`34`；明确拒绝=`24`
- `编码/建模/统计分析`：中性经验帖=`331`；明确拒绝=`55`；积极但保留=`54`
- `论文写作/投稿/审稿回复`：中性经验帖=`102`；积极但保留=`62`；积极采用=`16`
- `选题与问题定义`：中性经验帖=`266`；积极但保留=`218`；批判/担忧=`102`

## Workflow × Risk
- `uncertain`：hallucination=`19`；detection=`8`；ethics=`8`
- `学术交流与科研管理`：detection=`3`；hallucination=`3`
- `数据获取与预处理`：hallucination=`15`；detection=`7`；ethics=`3`
- `文献检索与综述`：hallucination=`121`；detection=`64`；ethics=`19`
- `研究设计与实验/方案制定`：hallucination=`25`；detection=`8`；ethics=`2`
- `编码/建模/统计分析`：hallucination=`30`；detection=`22`；ethics=`7`
- `论文写作/投稿/审稿回复`：detection=`17`；ethics=`8`；hallucination=`4`
- `选题与问题定义`：hallucination=`75`；ethics=`58`；detection=`53`

## Subject × Tool Preference
- `Arts & Humanities`：ChatGPT=`196`；Claude=`186`；Gemini=`113`；DeepSeek=`93`
- `Engineering & Technology`：ChatGPT=`233`；Claude=`197`；Gemini=`125`；DeepSeek=`84`
- `Life Sciences & Medicine`：Gemini=`53`；ChatGPT=`28`；Claude=`18`；DeepSeek=`15`
- `Natural Sciences`：ChatGPT=`60`；Claude=`37`；Gemini=`26`；DeepSeek=`17`
- `Social Sciences & Management`：ChatGPT=`23`；Claude=`19`；DeepSeek=`13`；Gemini=`9`
- `uncertain`：ChatGPT=`130`；Gemini=`109`；DeepSeek=`80`；Claude=`75`

## Time × Tool Evolution
- `2024H1`：ChatGPT=`34`；Copilot=`5`；Claude=`4`；Gemini=`3`
- `2024H2`：ChatGPT=`54`；Copilot=`18`；Claude=`12`；Kimi=`12`
- `2025H1`：DeepSeek=`125`；ChatGPT=`117`；Claude=`56`；Gemini=`25`
- `2025H2`：ChatGPT=`150`；Gemini=`94`；Claude=`72`；DeepSeek=`66`
- `2026H1`：Claude=`388`；ChatGPT=`315`；Gemini=`311`；DeepSeek=`110`

## Uncertainty As Result
- `qs_broad_subject='uncertain'`：`729` 帖（`23.77%`）
- `workflow_primary='uncertain'`：`435` 帖（`14.18%`）
- 这部分既是方法限制，也可作为平台表达风格与自陈信息稀缺性的结果加以讨论。

## Suggested Result Sections
- `应用扩散趋势`
- `不同学科的 AI4S 切入路径`
- `科研流程中的态度分化`
- `工具生态演进`
- `评论区的规范协商`
- `平台表达的不确定性`
