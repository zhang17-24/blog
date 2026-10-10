---
title: Git
description: 从日常命令到分支策略，把版本控制真正用起来。
order: 7
---

# Git

Git 的命令不多，但「会用」和「用得舒服」差别很大。
大部分人的问题不是不会命令，而是**不理解为啥要这么设计**。

## 章节

| # | 章节 | 内容 |
| --- | --- | --- |
| 01 | [日常命令](/guides/git/01-basics) | 三个区域、提交、撤销、查看历史 |
| 02 | [分支与合并](/guides/git/02-branching) | 分支模型、rebase vs merge、冲突处理 |

## 先建立一张心智图

Git 有三个区域，理解它们就理解了一半：

```
工作区            暂存区            本地仓库           远程仓库
(working dir)  →  (index)      →   (repository)  →   (remote)
              add            commit            push
```

- `git add` 把改动放进暂存区 —— 这一步是在**挑选要提交什么**
- `git commit` 把暂存区的内容打包成一个快照
- `git push` 把本地提交推到远程

::: tip 为什么要暂存区
因为它让你可以「只提交这次改动的一部分」。
改了两个功能但只想提交一个时，暂存区就是干这个用的（`git add -p`）。
:::
