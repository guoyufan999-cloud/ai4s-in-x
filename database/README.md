# 数据库说明

## 当前数据库布局

本仓库当前有两套数据库语义：

1. **legacy 运行库**
   - 位置：`archive/legacy_collection_runtime/data/db/ai4s_xhs.sqlite3`
   - 作用：保留历史自动采集、媒体补强、结构修补和冻结过程的完整运行痕迹
   - 状态：历史保留，不再作为活跃研究主接口

2. **研究型主库**
   - 位置：`data/processed/ai4s_legitimacy.sqlite3`
   - 作用：围绕研究问题组织的正式分析数据库
   - 状态：当前活跃主接口

## 文件说明

- `schema.sql`：研究型主库建表脚本
- `views.sql.template`：研究型分析视图模板
- `views.sql`：由模板渲染后的版本化视图产物

## 设计原则

研究型主库优先服务以下问题：

1. 帖子在科研工作流中的位置是什么？
2. 评论如何表达合法性支持、质疑和边界协商？
3. 哪些编码结果需要长期保留并可追溯？

因此，新库不再围绕“自动采集是否顺利”组织，而是围绕“研究分析需要哪些结构”组织。

## 视图维护规则

研究时间窗和正式 paper-scope 规则已经集中到 Python 配置层。运行时初始化应优先使用 `src.config.research_scope.render_views_sql()` 的渲染结果，`database/views.sql` 只作为版本化审阅产物保留，不应手工维护。若调整正式时间窗或口径，应同时更新：

1. `src/config/research_scope.py`
2. `database/views.sql.template`
3. `database/views.sql`
