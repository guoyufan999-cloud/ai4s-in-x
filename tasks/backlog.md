# Backlog

## P0：当前必须完成

1. [已完成] 验证 legacy 数据向研究型主库的完整迁移
2. [已完成] 校验 `posts / comments / codes / codebook` 与 `data/data_schema.md` 一致
3. [已完成] 把 `quality_v4` 关键正式结果与新研究型主库打通，并显式区分 `candidate / research / paper_quality_v4` 三套口径
4. [已完成] 复核当前输出目录与正式论文材料路径，并统一到 `outputs/` 活跃交付链
5. [已完成] 清理并归档剩余未分类历史文件（junk_review 建立、legacy exports 归档、DS_Store 清理）

## P1：研究分析主线

1. [已完成] 在新主库上补齐工作流 × 合法性 × 边界协商分析视图（新增 10 个 paper_scope_quality_v4 视图）
2. [已完成] 将 legacy 标签向新编码框架的映射规则写实（新增 `codebook/legacy_mapping.md`）
3. [已完成] 补齐 codebook 示例与易混淆项（34 个 codebook 条目全部替换示例待补）
4. [已完成] 建立帖子与评论的分析摘录工作流（新增 `src/analysis/excerpt_extraction.py` 与 19 个初始摘录文件）
5. [已完成] 将工具生态、风险主题等仍依赖 legacy 导出的字段逐步迁入研究主库（新增 benefit_themes_json + 3 个 lookup 表 + JSON 解析视图）

## P2：论文交付主线

1. [已完成] 在统一交付链上完成论文精修第一轮，形成 clean 版投稿阅读稿
2. [已完成] 精修摘要、引言、讨论与结论的第二轮措辞与论证密度
3. [已完成] 形成补充材料说明与方法透明度附录（内部版 + clean 版）
4. [下一步优先] 视投稿需要，进一步压缩正文措辞并生成更贴近期刊排版的 clean 版终稿

## P3：后续扩展

1. 视需要评估 grounded theory 路径如何接入新仓库
2. 视研究阻断决定是否需要第三轮结构修补
3. 视论文需求决定是否需要新增人工导入或补充样本
