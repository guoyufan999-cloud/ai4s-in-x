# Legacy Tests Archive Index

`archive/legacy_tests/` 现在只保留索引式静态说明，不再保留可执行的 legacy 测试集。

此前这里主要保存：

- legacy CLI 解析测试
- legacy coding / grounded / OpenCLI runner 相关测试
- 围绕 `data/exports`、`./ai4s-xhs` 和旧运行目录结构的历史断言

这些旧测试已经移出当前工作树，因为它们：

- 绑定已删除的 legacy 运行接口与目录结构
- 会误导为当前主线仍支持旧运行方式
- 对当前 `quality_v4` 研究工程主线不再提供有效回归价值

如需追溯旧测试曾覆盖过什么，请结合 `tasks/changelog.md` 与 `archive/legacy_collection_runtime/PROVENANCE.md` 阅读。

