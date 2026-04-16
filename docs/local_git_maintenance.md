# Local Git Maintenance

当前 `main` 已经是瘦身后的单根快照。用于保留旧本地历史的备份分支是 `backup/pre-clean-snapshot-20260416`，其删除前最后记录的提交 SHA 为 `9d0871bef8f29b0b8ca3f50793d7dd33e64efe6f`。只要这条分支还在，本地 `.git` 中的旧对象通常也会继续保留，因此 `git count-objects -vH` 看到的体积可能远大于当前 `HEAD` 的实际文件体量。

## 什么时候需要看这份说明

- 你发现当前仓库文件已经很轻，但 `.git` 目录仍然很大
- 你准备长期保留还是移除 `backup/pre-clean-snapshot-20260416`
- 你想在明确放弃旧本地历史后回收磁盘空间

## 默认策略

- 仓库不会自动删除备份分支
- 仓库不会在测试、脚本或 CLI 中自动执行 `git gc`
- 如果要回收空间，应作为显式人工维护动作来做

## 可选回收步骤

仅当你确认不再需要旧本地历史时，再手工执行以下命令。删除后，这份文档中的分支名与 SHA 就是最后保留的文字锚点：

```bash
git branch -D backup/pre-clean-snapshot-20260416
git reflog expire --expire=now --expire-unreachable=now --all
git gc --prune=now
```

## 建议的检查命令

```bash
git count-objects -vH
git branch -avv
git log --oneline --graph --decorate --all -n 20
```

如果你仍需要旧历史做审阅或回退，请保留备份分支，不要为了瘦身而仓促执行清理命令。
