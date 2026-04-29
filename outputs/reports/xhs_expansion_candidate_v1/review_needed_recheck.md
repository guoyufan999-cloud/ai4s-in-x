# xhs_expansion_candidate_v1 review_needed recheck

本报告记录对 42 条 `review_needed` 候选帖的 Codex-assisted 人工复核。该复核只服务 supplemental candidate staging，不写入研究主库，不改变 `quality_v5 514 / 0`。

## Summary

- input review_needed rows: `42`
- rechecked rows: `42`
- final include / review_needed / exclude: `78 / 0 / 37`
- recheck include / exclude: `15 / 27`
- formal_scope: `false`
- quality_v5_formal: `false`

## Decision Rule

- 保留：文本明确呈现 AI 进入文献处理、研究设计、数据分析、科研绘图、问卷/访谈或规范风险等科研活动。
- 剔除：泛 AI 工具、职场/办公、模型测评、AI4S职业选择、AI作为研究对象但非工具使用、无 AI 介入、非公开数据风险。

## Rechecked Rows

| candidate_id | decision | reason | title |
|---|---|---|---|
| `xhs_expansion_candidate_v1:65d71acc0000000001028976` | `include` | AI生成论文插图并进入SCI发表，直接涉及成果表达、可靠性和学术诚信风险。 | AI生成论文插图，每幅都巨荒谬，竟发了SCI |
| `xhs_expansion_candidate_v1:669629770000000025015b5d` | `exclude` | 主要是办公/Excel数据分析工具合集，科研语境不足。 | 谁懂❓用这些AI工具数据分析真得很香 |
| `xhs_expansion_candidate_v1:66f8fd3f000000001a021120` | `exclude` | 问卷工具对比，未呈现AI介入科研活动。 | 问卷调研工具对比和分享 |
| `xhs_expansion_candidate_v1:67070fa6000000002c029801` | `exclude` | AI4S诺奖新闻/名单，不是社交媒体用户的AI科研实践。 | AI拿下诺贝尔物理化学奖，这里有份AI4S名单 |
| `xhs_expansion_candidate_v1:6772335d000000000800c842` | `exclude` | 国产大模型总体讨论，未指向科研活动。 | 国产大模型真的那么差劲？ |
| `xhs_expansion_candidate_v1:678df26c000000001d013259` | `exclude` | 职场Excel/办公数据分析，科研语境不足。 | Excel表格用AI进行数据分析，太快了吧‼️ |
| `xhs_expansion_candidate_v1:6794b18a000000001800e879` | `exclude` | 研究生文献工具清单，但主要是传统数据库/检索工具，AI介入不足。 | 研究生必备文献工具 |
| `xhs_expansion_candidate_v1:67bc51d10000000029010356` | `exclude` | 程序员/职场AI工具合集，科研语境不足。 | 这些AI工具让我卷死同事（建议收藏防删版） |
| `xhs_expansion_candidate_v1:67c2aaa1000000000302afeb` | `include` | Zotero+DeepSeek文献翻译/总结，明确AI介入文献处理。 | Zotero➕deepseek完美翻译 |
| `xhs_expansion_candidate_v1:67cbd81f000000002a000a9a` | `include` | DeepSeek PDF文献翻译与格式保留，明确AI介入文献处理。 | DeepSeek PDF 翻译超强指南 |
| `xhs_expansion_candidate_v1:67f76906000000001c01f66b` | `include` | 面向科研党/学术党的AI文献阅读工具教程。 | 谁懂啊，用edge浏览器读文献不要太爽😭 |
| `xhs_expansion_candidate_v1:681b409f000000000c03855c` | `include` | AI文献翻译/阅读工具推广，但实践对象明确为在线学术文献。 | 29岁理工男搞了一个AI文献翻译神器！学生党 |
| `xhs_expansion_candidate_v1:682daf810000000023017d1c` | `include` | 国自然申报书DeepSeek指令，涉及课题/基金申请材料生成。 | 20个国自然申报书DeepSeek高阶指令 |
| `xhs_expansion_candidate_v1:68316ca3000000002102c598` | `include` | DeepSeek生成科研绘图/流程图，属于成果表达辅助材料。 | 用deepseek快速生成流程图 |
| `xhs_expansion_candidate_v1:68317dab0000000022037a03` | `exclude` | AI for Science实习/职业选择讨论，不是AI工具介入科研工作流。 | 师弟问我为什么不出去找AI for Science实习 |
| `xhs_expansion_candidate_v1:67e257c9000000001203c954` | `include` | 问卷星+DeepSeek生成AI报告，且文本明确提到学术研究。 | 问卷星+DeepSeek R1，问卷分析王炸组合 |
| `xhs_expansion_candidate_v1:68387901000000002100b58c` | `include` | AI生成问卷，虽带一般调研噪声，但可作为研究设计候选。 | AI做问卷也太方便了吧！ |
| `xhs_expansion_candidate_v1:68440a480000000012003b7d` | `exclude` | AI4Science方向前景/升学就业咨询，不是AI介入科研活动实践。 | AI4Science方向的前景如何呢 |
| `xhs_expansion_candidate_v1:687f45e60000000010010378` | `exclude` | 访谈提纲模板，未呈现AI介入。 | 毕业论文访谈提纲模板（通用） |
| `xhs_expansion_candidate_v1:689b48d0000000001d01f79a` | `exclude` | AI4Research论文分享/概念综述，不是社交媒体用户实践材料。 | 论文分享——AI4Research（2） |
| `xhs_expansion_candidate_v1:68c2eec6000000001b036460` | `exclude` | 显卡/PyTorch环境问题，偏技术环境配置，AI介入科研实践不足。 | 难过，50系显卡不能简单地跑深度学习 |
| `xhs_expansion_candidate_v1:68d8037e000000000e00dc96` | `exclude` | 一人公司/职场产品化，不属于科研活动。 | 不要一直悲催打工，用AI赋能一人公司！ |
| `xhs_expansion_candidate_v1:68f04cd6000000000302c156` | `exclude` | 半结构化访谈方法说明，未呈现AI介入。 | 半结构化访谈提纲的设计原则与方法 |
| `xhs_expansion_candidate_v1:68f74e330000000007036835` | `exclude` | Agent设计模式科普，未指向科研活动。 | 吴恩达｜现在最流行的5种Agent设计模式 |
| `xhs_expansion_candidate_v1:690dc3f60000000003036b4c` | `exclude` | AI4S研究生数据困境，偏领域处境，不是AI介入科研活动的使用实践。 | AI4S研究生，都在“讨饭”要数据！ |
| `xhs_expansion_candidate_v1:69244c72000000001e0331fe` | `exclude` | 招募访谈对象，未呈现AI介入。 | 60r招募访谈对象 |
| `xhs_expansion_candidate_v1:6926fb84000000001e013996` | `exclude` | Agent学习路线/实习经验，科研活动指向不足。 | 分享一下我的 agent 学习路线 |
| `xhs_expansion_candidate_v1:692d9e44000000001d03e9d3` | `exclude` | 高校教改课题以AI为研究对象，不是AI介入科研工作流。 | 这篇“AI赋能高校教改”课题申报书，太新颖了 |
| `xhs_expansion_candidate_v1:692ee305000000001e00798e` | `exclude` | GPT高阶用法泛工具帖，科研语境不足。 | 23个你可能从未听说过的GPT高阶用法【上】 |
| `xhs_expansion_candidate_v1:692ef422000000001e002b18` | `include` | AI访谈/问卷星调研功能，涉及访谈提纲和调研执行。 | 用AI进行1v1访谈（问卷星） |
| `xhs_expansion_candidate_v1:6932f115000000001e022592` | `exclude` | 提示词元方法，未指向科研活动。 | 不会提示词的人，反而写出最强Prompt |
| `xhs_expansion_candidate_v1:6936567c0000000019024275` | `include` | AI设计访谈提纲，明确进入用户研究/访谈设计。 | 用户研究 / 怎么让AI帮你设计访谈提纲？ |
| `xhs_expansion_candidate_v1:69413f4c000000001b026674` | `include` | AI阅读论文工具幻觉/过度吹捧风险，明确文献阅读规范风险。 | 现在的AI阅读论文工具真的是没法用了 |
| `xhs_expansion_candidate_v1:6944112d000000001e03656b` | `exclude` | AI驾驭心法泛用帖，科研语境不足。 | 别背提示词模板了，普通人驾驭AI的终极心法 |
| `xhs_expansion_candidate_v1:69a0128d000000001a023756` | `include` | Gemini读文献并生成科研绘图prompt，涉及学术图示生成。 | 试了一下gemini学术界真天塌了 |
| `xhs_expansion_candidate_v1:69ad1fd0000000001a0361ca` | `exclude` | 微信聊天记录提取+AI分析，含非公开/个人数据边界风险且科研语境不足。 | 微信聊天记录提取 + AI 分析：把你的日常变 |
| `xhs_expansion_candidate_v1:69b6a4fc000000002103abd1` | `exclude` | 48小时学习一门学科，泛学习场景，科研活动不足。 | 如何用AI在48小时内吃透一门学科 |
| `xhs_expansion_candidate_v1:69c6516c000000002202a379` | `exclude` | AIGC设计岗面试，非科研场景。 | 有个女生面试AIGC设计岗，真的被笑到了 |
| `xhs_expansion_candidate_v1:69d2021f0000000022026065` | `include` | Gemini文献整理/假文献风险，明确文献核查问题。 | Gemini 3pro告别假文献熬夜整理！ |
| `xhs_expansion_candidate_v1:69d8b97800000000230157de` | `include` | 一次性阅读大量PDF并担心遗忘/编造，适合作为文献处理边界样本。 | 怎么用ai一次性阅读几十个pdf |
| `xhs_expansion_candidate_v1:69ec8b82000000001f005da3` | `exclude` | DeepSeek模型测评，未指向科研活动。 | 国外博主实测DeepSeek V4，没封神，但够用 |
| `xhs_expansion_candidate_v1:69edd0bb00000000350253dc` | `exclude` | Claude Code接入教程与小游戏/待办工具测试，科研语境不足。 | DeepSeek V4 接入Claude Code最全教程🔥 |

## Recommendation

当前补充样本可进入 supplemental 人工编码准备，但不建议直接并入 `quality_v5`。是否启动 `quality_v6` 应等 query metadata 修复、去重审计、正式人工编码和独立 formalization 方案完成后再决定。
