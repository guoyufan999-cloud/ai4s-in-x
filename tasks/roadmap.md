# Roadmap

## 当前下一步入口

- 压缩投稿 clean 稿措辞，生成更贴近期刊排版的终稿版本
- 进入下一轮可维护性重构，优先拆重 `analysis/excerpt_extraction.py`
- 启动 `ai_practice` / `legitimacy` 手工细分编码后，再单独扩展对应 analysis views 与正式合同

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

- 进入下一轮可维护性重构，优先拆重 `analysis/excerpt_extraction.py`，随后 `analysis/reporting.py` 与 `analysis/figures/manifest.py`
- 启动 `ai_practice` / `legitimacy` 手工细分编码后，再单独扩展对应 analysis views 与正式合同
- 视研究问题与投稿反馈，再评估 grounded theory、第三轮结构修补或补充样本
