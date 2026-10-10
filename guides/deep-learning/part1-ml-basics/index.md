---
title: Part 1 · 机器学习基础
description: 地基部分。跳过它，后面所有内容都是空中楼阁。
order: 1
---

# Part 1 · 机器学习基础

这一部分是**地基**。跳过它，后面所有内容都是空中楼阁 —— 算法岗笔试和论文里反复出现的概念都在这里。

四条线，按顺序看：

| # | 章节 | 核心问题 |
| --- | --- | --- |
| 01 | [机器学习的本质是什么](/guides/deep-learning/part1-ml-basics/01-what-is-ml) | 学习 = 搜索？损失函数到底在衡量什么？ |
| 02 | [泛化、过拟合与偏差方差](/guides/deep-learning/part1-ml-basics/02-generalization) | 训练集好测试集差，为什么？ |
| 03 | [正则化与容量控制](/guides/deep-learning/part1-ml-basics/03-regularization) | L1/L2 到底在做什么？为什么 weight decay 有时不等价？ |
| 04 | [优化器：从 SGD 到 AdamW](/guides/deep-learning/part1-ml-basics/04-optimizers) | Momentum / Adam 的更新量怎么推出来的？AdamW 修好了什么？ |

## 这一部分要建立的判断力

- 看到「模型效果好」时，先问：**好在哪个集合上**、**和什么比**
- 看到「加了正则化」时，先问：**它约束的是什么**，是参数范数还是函数复杂度
- 看到「换了个优化器」时，先问：**它改的是步长还是方向**

::: tip 顺序不能跳
第 2 篇（偏差方差）是后面所有内容的公共语言。
第 5 篇讲梯度消失时会直接引用它，第 14 篇讲缩放定律也会。
:::
