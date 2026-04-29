# xhs_expansion_candidate_v1 candidate500_live_batch01 采集报告

本报告只描述小红书补充样本候选集 `xhs_expansion_candidate_v1` 的试采集过程，不构成论文发现，不写入 `quality_v5` formal baseline，也不写入正式研究主库。

## 1. 查询词使用

- 载入查询词数量：`16`
- 实际执行检索的查询词数量：`16`
- 查询来源：`query_file`
- 查询词文件：`data/external/xhs_expansion_candidate_v1_queries.json`

## 2. 每个查询词搜索命中

| query | query_group/category | search_hits | verified_kept | skipped |
| --- | --- | ---: | ---: | ---: |
| AI科研 | A. AI科研总体类 | 13 | 0 | 13 |
| AI辅助科研 | A. AI科研总体类 | 13 | 0 | 13 |
| ChatGPT科研 | A. AI科研总体类 | 14 | 0 | 14 |
| 生成式AI科研 | A. AI科研总体类 | 17 | 0 | 17 |
| AI研究助手 | A. AI科研总体类 | 16 | 0 | 16 |
| AI4Research | A. AI科研总体类 | 17 | 0 | 17 |
| AI4S | A. AI科研总体类 | 14 | 0 | 14 |
| 科研AI工具 | A. AI科研总体类 | 15 | 0 | 15 |
| AI文献阅读 | B. 文献处理与知识整合类 | 13 | 0 | 13 |
| AI读文献 | B. 文献处理与知识整合类 | 13 | 0 | 13 |
| AI文献综述 | B. 文献处理与知识整合类 | 15 | 0 | 15 |
| ChatGPT文献综述 | B. 文献处理与知识整合类 | 15 | 0 | 15 |
| AI总结论文 | B. 文献处理与知识整合类 | 12 | 0 | 12 |
| AI论文阅读 | B. 文献处理与知识整合类 | 16 | 0 | 16 |
| AI文献管理 | B. 文献处理与知识整合类 | 16 | 0 | 16 |
| AI翻译文献 | B. 文献处理与知识整合类 | 16 | 0 | 16 |

## 3. 验证与编码结果

- 成功验证的公开帖子数量：`0`
- 目标候选数量：`150`
- 纳入 / 待复核 / 剔除：`0 / 0 / 0`
- 与现有 `data/processed/ai4s_legitimacy.sqlite3` 的重复数量：`93`

## 4. 跳过原因

- 不可访问或抓取失败：`0`
- 登录限制或访问受限：`0`
- 无正文：`142`
- 日期不符合：`0`
- 当前轮重复：`0`
- 作者上限过滤：`0`
- 标题/正文近似重复：`0`
- 无效 URL：`0`

## 5. fallback 状态

- 是否触发 fallback：`false`
- 实际 provider：`opencli_xiaohongshu`

## 6. 合规风险说明

- 本轮只处理公开可访问帖子材料，不绕过登录、验证码、风控、限流或封禁机制。
- 不使用私信、封闭群组、非公开主页或受限内容。
- 不保存浏览器 cookie、本地登录态或可识别个人身份信息。
- 输出是 candidate / supplemental，不进入 `quality_v5` 正式结果。

## 7. 下一步建议

- 暂不建议扩大到 200 或 300 条；应先调整查询词和公开访问策略。
- 是否值得进入人工 review 队列：暂不建议进入正式人工 review 队列，应先调整查询词或访问策略。
- 是否建议继续扩大到 500 条：不建议立即扩大到 500 条；应先复核 candidate300 的噪声率、主题覆盖和重复结构。

## 8. 查询词表现与 pilot 对比

对比基线：`outputs/tables/xhs_expansion_candidate_v1/candidate_expanded_v2.jsonl`；pilot row_count=0, included=0。

表现更好的查询词：
- 暂无。

带来较多噪声或重复的查询词：
- `生成式AI科研`：verified_kept=0, search_hits=17, skipped=17
- `AI4Research`：verified_kept=0, search_hits=17, skipped=17
- `AI研究助手`：verified_kept=0, search_hits=16, skipped=16
- `AI论文阅读`：verified_kept=0, search_hits=16, skipped=16
- `AI文献管理`：verified_kept=0, search_hits=16, skipped=16
- `AI翻译文献`：verified_kept=0, search_hits=16, skipped=16
- `科研AI工具`：verified_kept=0, search_hits=15, skipped=15
- `AI文献综述`：verified_kept=0, search_hits=15, skipped=15

建议降权或删除的查询词：
- `生成式AI科研`：verified_kept=0, search_hits=17, skipped=17
- `AI4Research`：verified_kept=0, search_hits=17, skipped=17
- `AI研究助手`：verified_kept=0, search_hits=16, skipped=16
- `AI论文阅读`：verified_kept=0, search_hits=16, skipped=16
- `AI文献管理`：verified_kept=0, search_hits=16, skipped=16
- `AI翻译文献`：verified_kept=0, search_hits=16, skipped=16
- `科研AI工具`：verified_kept=0, search_hits=15, skipped=15
- `AI文献综述`：verified_kept=0, search_hits=15, skipped=15

## 9. 主题覆盖

- AI文献阅读：`0`
- AI论文写作：`0`
- AI数据分析：`0`
- AI科研训练：`0`
- AI使用披露：`0`
- AI学术诚信：`0`
- AI审稿或AI检测：`0`

## 10. 话语类型初步判断

- 工具推荐：`0`
- 经验分享：`0`
- 风险提醒：`0`
- 规范讨论：`0`
- 评论争论：`0`

说明：上述主题和话语类型只用于候选集采集质量评估，不是论文发现；正式解释仍需人工 review。
