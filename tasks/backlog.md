# Backlog

## 当前下一步入口

1. [优先] 维护 `quality_v5` post-only 冻结基线作为工程 guard：正式帖子 `514`，正式评论 `0`
2. [优先] 以 `quality_v6` 作为当前投稿结果层：`quality_v5 514` + `supplemental_formalization_v1 200`，正式帖子 / 评论为 `714 / 0`
3. [优先] 保持 `post_review_v2 -> reviewed import -> rebuild artifacts` 链路可复跑，并以 `quality_v5_consistency_report.json` 的 posts/comments delta `0 / 0` 作为 guard 核验门槛
4. [优先] 将 `comment_review_v2` 作为后续独立工作流处理；本轮不把评论 corpus 写成正式评论结果
5. [优先] 维护 `quality_v6` 投稿入口；manifest、clean 主稿、方法附录、第四至第六章材料与图表包已完成口径统一，后续只做投稿前精修和审计补充

## P0：当前必须完成

1. [已完成] 验证 legacy 数据向研究型主库的完整迁移
2. [已完成] 校验 `posts / comments / codes / codebook` 与 `data/data_schema.md` 一致
3. [已完成] 把 `quality_v4` 关键正式结果与新研究型主库打通，并显式区分 `candidate / research / paper_quality_v4` 三套口径
4. [已完成] 复核当前输出目录与正式论文材料路径，并统一到 `outputs/` 活跃交付链
5. [已完成] 清理并归档剩余未分类历史文件（含当时的 `junk_review` 分流、legacy exports 归档与 `.DS_Store` 清理）
6. [已完成] 锁定 `quality_v5` 本轮 post-only formal baseline，并明确 `comment_review_v2` deferred

## P1：研究分析主线

1. [已完成] 在新主库上补齐工作流 × 合法性 × 边界协商分析视图（新增 10 个 paper_scope_quality_v4 视图）
2. [已完成] 将 legacy 标签向新编码框架的映射规则写实（新增 `codebook/legacy_mapping.md`）
3. [已完成] 补齐 codebook 示例与易混淆项（34 个 codebook 条目已完成示例替换）
4. [已完成] 建立帖子与评论的分析摘录工作流（新增 `src/analysis/excerpt_extraction.py` 与 19 个初始摘录文件）
5. [已完成] 将工具生态、风险主题等仍依赖 legacy 导出的字段逐步迁入研究主库（新增 benefit_themes_json + 3 个 lookup 表 + JSON 解析视图）

## P2：论文交付主线

1. [已完成] 在统一交付链上完成论文精修第一轮，形成 clean 版投稿阅读稿
2. [已完成] 精修摘要、引言、讨论与结论的第二轮措辞与论证密度
3. [已完成] 形成补充材料说明与方法透明度附录（内部版 + clean 版）
4. [已完成] 围绕 `quality_v6` post-only 口径复核 clean 稿，避免把 `quality_v4`、候选样本或评论层 corpus 写成当前正式结果
5. [已完成] 用“话语情境—实践位置—介入方式—规范评价—边界生成”重写论文理论框架、codebook、canonical payload 兼容层与 paper materials
6. [已完成] 将论文主稿口径切换到 `quality_v6`；`quality_v5` 仍保留为工程 guard

## P3：后续扩展

1. [已完成] 完成 `analysis/figures/queries.py` 与 `analysis/figures/render.py` 的可维护性收口，工程底座达到当前阶段稳定点
2. [后续] 如需正式评论层结果，单独启动 `comment_review_v2` 队列、人工 reviewed 导入与 artifacts 重建
3. [后续] 在 post-only 投稿口径稳定后，再评估 clean 稿终稿压缩、grounded theory 或补充样本
4. [后续] 如需进一步增强 v2 字段可信度，优先对高强度替代、自动执行、治理监督、正式规范参照和替代去合法化等高风险组合做抽查复核；当前 F/G/H/I/J/K 已进入 `quality_v6` framework_v2 正式统计
5. [已完成] 对 `xhs_expansion_candidate_v1` 候选帖子完成 supplemental formalization，并以 staging DB 方式进入 `quality_v6`，不污染 `quality_v5`
