---
title: 日常命令
description: 提交、撤销、看历史，以及每个新手都会踩的那几个坑。
---

# 日常命令

## 最常用的十条

```bash
git status                 # 现在处于什么状态（最该常敲的一条）
git add <文件>              # 把改动放进暂存区
git add -p                 # 交互式挑选要暂存的部分 ← 强烈推荐
git commit -m "说明"        # 提交
git log --oneline --graph  # 看历史（带分支图）
git diff                   # 工作区 vs 暂存区
git diff --staged          # 暂存区 vs 上次提交
git pull --rebase          # 拉取并变基
git switch -c 新分支        # 建分支并切过去
git restore <文件>          # 丢弃工作区改动
```

## 撤销：分清楚撤什么

这是最容易搞混的地方。**先问「改的东西在哪个区域」**：

| 想撤销什么 | 命令 | 危险程度 |
| --- | --- | --- |
| 工作区的改动（还没 add） | `git restore <文件>` | 低，但改动会丢 |
| 已 add，想撤回暂存 | `git restore --staged <文件>` | 无，改动还在工作区 |
| 上一次 commit 的说明写错了 | `git commit --amend` | 低（未 push 时） |
| 上一次 commit 少加了文件 | `git add <文件> && git commit --amend --no-edit` | 低（未 push 时） |
| 想撤销一次已 push 的提交 | `git revert <commit>` | 安全，生成反向提交 |

::: danger 别用 `--hard` 除非你确定
`git reset --hard` 会**永久丢弃**工作区和暂存区的改动，找不回来。
真要用之前先 `git stash` 存一份。

已经 commit 过的东西一般不会丢 —— `git reflog` 能找回 30 天内的所有 HEAD 移动记录：
```bash
git reflog                    # 找到误删提交的 hash
git reset --hard <hash>       # 恢复
```
:::

## 忽略文件

```txt
node_modules/
dist/
.env
*.log
.DS_Store
```

- 已经提交过的文件加进 `.gitignore` **不会自动失效**，要先 `git rm --cached <文件>`
- `git check-ignore -v <文件>` 能告诉你某个文件为什么被忽略

## 提交信息的写法

```
feat: 支持文章分页
fix: 修正日期格式解析错误
docs: 补充部署说明
refactor: 抽出文章列表组件
```

前缀不是强制的，但**「动词开头、说清做了什么」**是底线。
半年后你会感谢自己。

## 几个提高效率的配置

```bash
git config --global alias.st "status -sb"
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global pull.rebase true          # pull 默认用 rebase
git config --global rerere.enabled true       # 记住冲突解决方式，重放时自动套用
git config --global core.autocrlf input       # 避免换行符导致的整文件 diff
```

`rerere` 这个配置很少人知道，但做 rebase 时非常好用 ——
同一个冲突解决一次，之后重放会自动套用。

下一篇：[分支与合并](/guides/git/02-branching)。
