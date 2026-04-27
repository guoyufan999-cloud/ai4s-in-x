# Backlog

## 当前下一步入口

1. [优先] 启动 `quality_v5` 正式基线重建：先导出 `quality_v4` 一次性审计快照，再生成未编码 staging DB
2. [优先] 对全部 `5535` 条候选帖执行 `rescreen_posts` 重筛，并通过 `review queue -> reviewed import` 逐步重建 `sample_status / actor_type`
3. [优先] 在帖子、评论和细分编码三条 reviewed 队列上推进重标，完成后再重建 `quality_v5` 正式 artifacts

## P0：当前必须完成

1. [已完成] 验证 legacy 数据向研究型主库的完整迁移
2. [已完成] 校验 `posts / comments / codes / codebook` 与 `data/data_schema.md` 一致
3. [已完成] 把 `quality_v4` 关键正式结果与新研究型主库打通，并显式区分 `candidate / research / paper_quality_v4` 三套口径
4. [已完成] 复核当前输出目录与正式论文材料路径，并统一到 `outputs/` 活跃交付链
5. [已完成] 清理并归档剩余未分类历史文件（含当时的 `junk_review` 分流、legacy exports 归档与 `.DS_Store` 清理）

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
4. [挂起] `quality_v5` 正式基线稳定前，不继续推进 clean 稿终稿压缩

## P3：后续扩展

1. [已完成] 完成 `analysis/figures/queries.py` 与 `analysis/figures/render.py` 的可维护性收口，工程底座达到当前阶段稳定点
2. [进行中] 通过 `review queue -> reviewed import -> rebuild artifacts` 链重建 `ai_practice / legitimacy / boundary` 正式编码
3. `quality_v5` 重建完成后，再评估是否转向 clean 稿终稿或研究扩展第二轮
