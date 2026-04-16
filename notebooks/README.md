# Notebook Templates

`notebooks/` 只保留本地审查模板，不作为正式交付链或版本化证据链的一部分。

使用约定：

- 这些 notebook 是模板入口，不是已执行产物
- 默认不要提交执行输出、缓存结果或临时截图
- 正式版本化产物仍以 `outputs/`、`outputs/reports/freeze_checkpoints/`、`outputs/reports/paper_materials/` 为准
- 如需在本地运行，请优先先更新研究主库和 freeze checkpoints，再把 notebook 当成临时探索工作台

当前模板：

- `01_data_audit.ipynb`：研究主库行数、缺失字段和导入完整性检查
- `02_cleaning_checks.ipynb`：标准化、匿名化和迁移后字段质量抽查
- `03_coding_exploration.ipynb`：工作流 / 合法性编码分布与裁决支持
- `04_analysis_outputs.ipynb`：围绕 `quality_v4` 的图表与分析输出核对
