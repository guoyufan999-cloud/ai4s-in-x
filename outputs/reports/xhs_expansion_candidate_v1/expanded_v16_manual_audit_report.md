# expanded_v16 manual audit report

本报告对 `xhs_expansion_candidate_v1` v16 cleaned 补充候选样本做方法附录式抽查。它不构成 `quality_v5` 正式编码，不写入研究主库，不启动 `comment_review_v2`。

## Scope Guard

- source_scope: `xhs_expansion_candidate_v1`
- quality_v5 formal posts/comments: `514 / 0`
- reviewed input: `data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.expanded_v16_cleaned.codex_reviewed.jsonl`
- staged accepted input: `data/interim/xhs_expansion_candidate_v1/staged_import/xhs_expansion_candidate_v1.expanded_v16_cleaned.accepted_posts.jsonl`
- sample output: `data/interim/xhs_expansion_candidate_v1/reviewed/xhs_expansion_candidate_v1.expanded_v16_cleaned.manual_audit_sample.jsonl`

## 抽查设计

- staged accepted 总量：`206`
- review_needed 总量：`11`
- 抽查 include：`80`，按 query_group 分层并保证小组覆盖
- 抽查 review_needed：`11`，全量复核
- 抽查总量：`91`

## 抽查结论

- pass：`77`
- needs_human_review：`14`
- exclude：`0`
- include 抽样通过率：`96.2%`

## 风险标签

- `ad_or_service_noise`: `13`
- `weak_ai_research_signal`: `1`

## query_group 分层结果

{
  "A. AI科研总体类": {
    "pass": 15,
    "needs_human_review": 4
  },
  "B. 文献处理与知识整合类": {
    "pass": 34,
    "needs_human_review": 9
  },
  "C. 研究设计与方法学习类": {
    "pass": 10,
    "needs_human_review": 1
  },
  "D. 数据分析与代码类": {
    "pass": 6
  },
  "E. 论文写作与成果表达类": {
    "pass": 2
  },
  "F. 科研规范与诚信类": {
    "pass": 8
  },
  "G. 科研训练与效率类": {
    "pass": 2
  }
}

## 代表性风险样本

| candidate_id | query_group | decision | risk_tags | excerpt |
| --- | --- | --- | --- | --- |
| `xhs_expanded_v3_4288bdc654c810a7` | B. 文献处理与知识整合类 | `needs_human_review` | weak_ai_research_signal | 1️⃣分钟自查虚假文献 你知道导师是怎么一眼看出来文献真实性的吗 #科研[话题]# #参考文献[话题]# #SCI[话题]# #文献[话题]# #文献综述[话题]# #教育作者扶持计划[话题]# @校园薯 |
| `xhs_expanded_v3_454764d0ab712de6` | C. 研究设计与方法学习类 | `needs_human_review` | ad_or_service_noise | 最近比较常用到的文献阅读整理工具搭配 ai时代人人在讲工作流，但学习和搭建工作流的过程常常要花很多时间，我在尝试每一个工具的时候都在想不能折腾工具陷入伪工作的状态。 zotero和notebooklm都是老选手了，我在zotero里装了awesome GPT，就可以直接完成paper的总结概括工作，插件attanger整理pdf很不错，方便之后丢进notebooklm来深度分析。 obsidian是我看到非常多人推荐于是开始学习使用，所以如果有其他好的使用方法欢迎大家评论！我 |
| `xhs_expanded_v3_8750cc7955e64fa9` | A. AI科研总体类 | `needs_human_review` | ad_or_service_noise | 真的都没用过consensus找文献吗？ 震惊❗️原来很多人不知道consensus吗[失望R]（小小标题党一下） [吧唧R]因为听到身边人写论文时在吐槽gpt，我不允许我的gpt老师被说[哭惹R] [向右R]简单介绍一下，ChatGPT通过Consensus插件连接Consensus AI research，其为一种利用人工智能技术摘取并整理科研文献信息的搜索引擎。在启动Consensus之后，用户只需用一句话描述想了解的问题，插件就能从 2 亿篇论文中搜索并整理出答案，并 |
| `xhs_expanded_v3_ee8a0c942b6c2f84` | B. 文献处理与知识整合类 | `needs_human_review` | ad_or_service_noise | Cursor断供多款模型，程序员震怒：退钱！ 最近，有大量开发者反映，美国知名AI编程软件Cursor在中国大陆断供来自Anthropic、谷歌和OpenAI的多款模型。 [彩虹R]这波断供来得突然，没有任何预兆或提前通知，现在当用户选择上述模型时，Cursor会弹出“模型供应商不为您所在的地区提供服务”的提示，智东西的实测也验证了这点。 [加油R]在国内社交媒体平台上，以“Cursor不能用了”为关键词搜索，可以看到开发者们已经炸锅了，相关帖子引发热议。 [看R]本次断供的 |
| `xhs_expanded_v3_8c7df2e4aa4c9710` | A. AI科研总体类 | `needs_human_review` | ad_or_service_noise | 问卷调研工具对比和分享 最近做一个设计方案的问卷调研，寻找合适的问卷调研工具。之前公司买了问卷星，但是使用率低没有续费。所以试用了几款问卷调研工具：问卷星、飞书、腾讯问卷、网易问卷、zoho survey。推荐飞书和问卷星，不推荐腾讯问卷。如果大家有好用免费的问卷工具，请分享！[飞吻R] 基本上所有的工具，免费只针对个人版本，企业版本需要收费。以下是使用体验对比 · 1、问卷星 不限调研数量，不限回答数量 有简单统计 界面有点丑 设计问卷的操作有点繁琐 缺点：用户可以免费创建 |
| `xhs_expanded_v3_566e34a73f076f94` | B. 文献处理与知识整合类 | `needs_human_review` | ad_or_service_noise | 分享一下我的 agent 学习路线 分享一下我的 agent 学习路线 有许多小伙伴私信我，咨询一些学习建议，所以我写了一点，仅供参考(。。)四希望大家都能找到自己满意的实习!#我的学习进化论 #实习日记 #agent日常 #互联网大厂[话题]# #大模型[话题]# #面经[话题]# #深度学习与神经网络[话题]# #强化学习[话题]# #经验[话题]# #机器学习[话题]# |
| `xhs_expanded_v3_7f5d94659b7ff22d` | B. 文献处理与知识整合类 | `needs_human_review` | ad_or_service_noise | 横行比较9种PDF论文翻译的方式 学长带你像喝水一样读文献！ 1. Dochero（网站）点击「论文翻译」按钮，上传PDF论文，直接自动开始翻译（论文翻译免费，其他pdf翻译免费+付费，效果见图一，自带术语高亮） 2. InOtherWord (网站) 首页直接上传，不需要登录，也可翻译PDF文件（保留格式，免费+付费模式，效果图二） 3. DeepL（网站） 点击页面「翻译文件」按钮，上传PDF （需要登录，需要梯子，付费翻译） 4. calibre（电子书管理应用） 下载 |
| `xhs_expanded_v3_15895d753a8bfcc4` | B. 文献处理与知识整合类 | `needs_human_review` | ad_or_service_noise | 不要一直悲催打工，用AI赋能一人公司！ 后台好多朋友评论说，上班跟上坟似的，一想到要去公司就崩溃，但为了生存又不得不扛着，到底该咋办啊？ 其实从现在起，你赶紧把自己 “产品化”，把自己打造成一个人的公司，长远来看，这一定是应对 “不想上班” 的好办法。 而且现在有 AI 帮忙，这事能比以前容易不少，关键是做好这五种能力： 1、定位力 你自己就是公司的核心产品，所以首个步得找准定位。要是特别讨厌现在的工作，别硬扛，用 AI 工具扒一扒当下的热门需求 —— 比如看看大家都在关心什 |
| `xhs_expanded_v3_df1f9e8ff81a18b2` | B. 文献处理与知识整合类 | `needs_human_review` | ad_or_service_noise | 这篇“AI赋能高校教改”课题申报书，太新颖了 哈喽老师们， 当下有很多高校课题申报正在进行哦！今天就给大家分享一份人工智能赋能高校教育教改项目课题申报书范文，课题研究聚焦数字化背景下高校人工智能通识课程建设研究方向！ 课题研究核心:1.课题探讨了开展人工智能通识课程建设的背景和意义。2.分析了人工智能通识教育所面临的挑战：知识多、跨度大，学生理解难度大；实验资源和实验平台不足，学生实践机会较少；教学体系亟待完善。3.针对挑战，提出了人工智能通识课程的建设策略，包括采用“三融合 |
| `xhs_expanded_v3_9a3e797b5c39abda` | A. AI科研总体类 | `needs_human_review` | ad_or_service_noise | 经验帖｜deepseek读文献的神奇指令库🌟 作为日均啃5篇paper的科研狗，姐整理了一套AI读文献的宝藏指令公式！效率直接翻倍，分享给宝子们👇 🔮首先，记得赋予AI身份：“你是xx专业的研究专家\u002F博导\u002F教授……”，接着： 1️⃣总结核心 “请列举这篇文献的题目、作者、期刊、摘要、关键词、研究问题、研究方法、研究结论、创新点、不足之处，用中文分点输出。” 2️⃣解释难点 “请用通俗易懂的语言解释文中XXX概念\u002F理论\u002F公式，并举例说明其 |
| `xhs_expanded_v3_3dff9515990de83e` | B. 文献处理与知识整合类 | `needs_human_review` | ad_or_service_noise | Claude无良卖家，差点报警了 事发清明居家无聊，国内模型用着难受 动不动就超时，等待coding过程 去了趟海鲜市场 看着划算下单商家刚才是开始也算诚恳 结果就是 6号的Max5 9号的Free [鄙视R]当时的第一心情就是 透了tm 万幸的是处理的还算妥当，顺利退款 Ps: 中途还打电话威胁我(闲鱼下单有电话和地址) [doge]差点我就去找 fo波嘞 了 #网络交易需谨慎[话题]# #远离无良商家[话题]# #退款也是原路退回[话题]# #维护自身权益[话题]# |
| `xhs_expanded_v3_398d995ca6133def` | A. AI科研总体类 | `needs_human_review` | ad_or_service_noise | 谁懂❓用这些AI工具数据分析真得很香 推荐大家使用几款常见的 Al 工具进行数据分析[赞R] 🔥excelform ulabot 免费在几秒内将文本指令转换成Excel公式 🔥Ch*tExcel 可以仅通过聊天来操控你的表格 🔥Ajelix 将文本指令转换成Excel公式 🔥Sheet+ 将文本指令转换成Excel公式和Google表格公式 🔥AlExcel Bot 将文本指令转换成Excel公式 可以编写VBA并在几秒内解释 🔥ExcelForm ulator 将文本指令转 |
| `xhs_expanded_v3_ac14b9e05dc94309` | B. 文献处理与知识整合类 | `needs_human_review` | ad_or_service_noise | 60r招募访谈对象 大家好，我是中山大学在读硕士，因为课题需要，现有偿招募1-2名访谈对象 1、访谈主题：婚姻和生育的意义、人工流产、生育假、育儿补贴 2、访谈对象要求： （1）在85年后出生的女性 （2）在广东工作 （3）有过人工流产的经历 3、访谈时长：60分钟，会根据实际情况有一定延长 4、访谈时间：本周三（11.26）或本周四（11.27）晚上19：00-22：00任一时段 5、访谈形式：腾讯会议，会在征求同意后录音 6、报酬：60r 7、访谈要求 （1）为提升访谈质 |
| `xhs_expanded_v3_b1457e4552698468` | B. 文献处理与知识整合类 | `needs_human_review` | ad_or_service_noise | AI4Science方向的前景如何呢 bg：USTC，22级，凝聚态物理实验方向 有在考虑保外，除了常规的物理方向的夏令营外，之前也参加了上海创智的夏令营，也报名了上海人工智能实验室的夏令营，报的都是AI4S方向，这两天刷到有帖子问各个方向的选择建议然后评论区好多喷AI4S的……[石化R] 因为我本人也不算AI科班生，对各个方向的发展情况及前景也不算很了解，发这篇帖子希望各位老师和同学能给点意见供参考[皱眉R]比如找工作和就业方面的情况，非常感谢各位 #上海人工智能实验室[话 |

## 纳入建议

建议：`start_supplemental_formalization_not_quality_v6`。

解释：include 抽样通过率为 `96.2%`。当前样本可作为 `supplemental formalization` 的候选池继续推进，但不建议直接升级为 `quality_v6` 主结果。下一步应对 `needs_human_review` 与风险标签样本做人工确认，并对 `206` 条 staged accepted 全量补五层框架编码后再决定是否 formalize。
