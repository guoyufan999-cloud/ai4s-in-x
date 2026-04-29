# Roadmap

## 当前下一步入口

- `quality_v5` 本轮已经锁定为 post-only 冻结基线和工程 guard：正式帖子 `514`，正式评论 `0`
- `quality_v6` 已切换为当前投稿结果层：正式帖子 `714`，正式评论 `0`，来源为 `quality_v5 514` + `supplemental_formalization_v1 200`
- 当前第一优先级是维护 `quality_v6` 投稿材料与 `quality_v5` guard 的边界，同时避免把 deferred 的 `comment_review_v2` 误写成正式评论层结果
- framework_v2 已完成当前投稿层所需的理论框架、codebook、canonical payload 兼容层、paper materials 与测试；不做 DB schema migration，不启动评论层正式编码
- 投稿 manifest、clean 主稿、方法附录、第四至第六章材料与图表包均以 `quality_v6` 为当前结果口径；`quality_v5` 仍作为 artifact health guard

## 阶段 1：仓库重构与主库迁移

- [已完成] 建立研究型目录结构
- [已完成] 归档 legacy 运行系统
- [已完成] 生成研究型 schema、数据说明和编码手册
- [已完成] 完成 legacy -> research DB 首轮迁移

## 阶段 2：分析主线接管

- [已完成] 在新主库上完成核心分析视图
- [已完成] 补齐工作流 × 合法性 × 边界协商的 paper_scope_quality_v4 交叉视图（10 个新视图）
- [已完成] 写实 legacy → 研究型编码框架映射规则（`codebook/legacy_mapping.md`）
- [已完成] 补齐 codebook 示例与易混淆项（全部 34 个条目）
- [已完成] 建立帖子与评论的分析摘录工作流（`src/analysis/excerpt_extraction.py`）
- [已完成] 将工具生态、风险主题、收益主题迁入研究主库（lookup 表 + JSON 解析视图）
- [已完成] 对齐 `quality_v4` 正式结果与新仓库输出，并锁定三套口径：
  - `candidate_scope`
  - `research_scope`
  - `paper_scope_quality_v4`

## 阶段 3：论文交付物统一

- [已完成] 完成投稿版文稿、图表和摘录路径统一
- [已完成] 完成摘要、引言、讨论与结论的第二轮精修
- [已完成] 补齐方法透明度附录与补充材料说明（双版本）
- [已完成] 基于新主库正式口径复核结果—图表—数据库一致性

## 阶段 4：后续研究扩展

- [已完成] 完成 `analysis/figures/queries.py` 与 `analysis/figures/render.py` 的可维护性收口，工程底座达到当前阶段稳定点
- [已完成] 重建 `quality_v5` post-only 正式基线：导出 `quality_v4` 审计快照、完成 rescreen 回灌、导入严格版 `post_review_v2`、刷新 active artifacts
- [进行中] 维护 `quality_v6` 投稿 materials 与 `quality_v5` guard artifacts 的一致性
- [已完成] 完成 framework_v2：建立“话语情境—实践位置—介入方式—规范评价—边界生成”理论框架、codebook、payload 兼容层与 `outputs/reports/paper_materials/quality_v6/framework_v2/`
- [已完成] 建立 `quality_v6` post-only formalization：使用 staging DB 合并 200 条 supplemental formalized posts，输出独立 freeze、consistency、provenance、paper materials 与 figure package
- [后续] 如论文或扩展研究需要评论层正式结果，再单独启动 `comment_review_v2`；完成前 `formal_comments=0` 仍是设计选择
- [已完成] 审阅 `quality_v6` 结果层材料，并把论文主稿从 `quality_v5` 口径切换到 `quality_v6`
- [后续] 如需扩展 v2 字段可信度，围绕高风险组合形成抽查复核记录；当前 F/G/H/I/J/K 已进入 `quality_v6` framework_v2 正式统计
