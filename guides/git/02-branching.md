---
title: 分支与合并
description: rebase 和 merge 的区别，以及怎么选一套分支模型。
---

# 分支与合并

## 分支在 Git 里到底是什么

分支**只是一个指向某个提交的指针**，40 字节。所以建分支是瞬间的、零成本的。

```bash
git switch -c feature/login    # 建并切到新分支
git switch main                # 切回
git branch -d feature/login    # 删掉（已合并的）
git branch -D feature/login    # 强制删（未合并的）
```

## merge vs rebase

假设 `main` 和 `feature` 分叉了：

```bash
# merge：保留两条线，产生一个合并提交
git switch main
git merge feature
# 历史：main ── A ── B ──── M(merge)
#              └── C ── D ──┘

# rebase：把 feature 的提交挪到 main 顶端，历史变成一条直线
git switch feature
git rebase main
# 历史：main ── A ── B ── C' ── D'
```

| | merge | rebase |
| --- | --- | --- |
| 历史形状 | 有分叉，真实 | 一条直线，整洁 |
| 提交 hash | 不变 | **会重写** |
| 冲突解决次数 | 一次解决全部 | 每个提交都可能冲突 |
| 安全性 | 安全 | **已 push 的分支上不要用** |

::: danger rebase 的黄金法则
**永远不要 rebase 已经推送到共享分支的提交。**

rebase 会生成新的提交（hash 变了），别人基于旧提交的工作会全部错乱。
自己的功能分支随便 rebase，`main` 上永远别碰。
:::

## 推荐的日常流程

```bash
# 1. 从最新的 main 开分支
git switch main && git pull --rebase
git switch -c feature/xxx

# 2. 开发，小步提交
git add -p && git commit -m "feat: ..."

# 3. 同步 main 的最新改动（保持自己的提交在顶端）
git fetch origin
git rebase origin/main

# 4. 推送
git push -u origin feature/xxx

# 5. 提 PR，合并后删掉本地分支
git switch main && git pull --rebase
git branch -d feature/xxx
```

## 处理冲突

```bash
git rebase origin/main
# CONFLICT (content): Merge conflict in src/app.ts
```

打开冲突文件，会看到：

```
<<<<<<< HEAD
当前分支的版本
=======
被合入分支的版本
>>>>>>> origin/main
```

改完之后：

```bash
git add <冲突文件>      # 标记为已解决
git rebase --continue

git rebase --abort      # 或者反悔，回到 rebase 之前
```

::: tip 用图形化工具解决冲突
`git mergetool` 可以配 VS Code：

```bash
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait "$MERGED"'
```

三栏对比比看 `<<<<<<<` 标记快得多。
:::

## 分支模型怎么选

| 模型 | 适用 | 说明 |
| --- | --- | --- |
| 主干开发 | 大多数项目 | 所有人往 `main` 提，靠 feature flag 控制发布 |
| GitHub Flow | 开源 / 小团队 | `main` + 短命功能分支 + PR |
| Git Flow | 有明确版本的软件 | `develop` / `release` / `hotfix` 多分支 |

**小项目不要上 Git Flow。** 它带来的流程开销远大于收益，
GitHub Flow 基本够用。

## 常用检查命令

```bash
git log --oneline main..feature     # feature 比 main 多了哪些提交
git branch --merged main            # 哪些分支已经合并了（可以删）
git branch --no-merged main         # 哪些还没合并
git diff main...feature             # 分叉点以来的差异（注意三个点）
```

`...` 和 `..` 的区别：`..` 是两边直接比，`...` 是**从共同祖先开始比**。
看「这个分支做了什么」要用三个点。

Git 指南到这里结束。
