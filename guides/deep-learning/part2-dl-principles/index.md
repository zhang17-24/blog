---
title: Part 2 · 深度学习原理
description: 深度网络特有的机制 —— 为什么深网络能工作、为什么会出现梯度消失。
order: 2
---

# Part 2 · 深度学习原理

这一部分讲**深度网络特有的机制**。为什么深网络能工作、为什么会出现梯度消失、以及那些「魔法数字」背后是什么。

| # | 章节 | 核心问题 |
| --- | --- | --- |
| 05 | [反向传播的完整推导](/guides/deep-learning/part2-dl-principles/05-backprop) | 链式法则在这个网络里怎么具体展开？梯度消失的本质是什么？ |
| 06 | [归一化：从 BatchNorm 到 RMSNorm](/guides/deep-learning/part2-dl-principles/06-normalization) | 归一化到底在解决什么？为什么 BatchNorm 淘汰而 LayerNorm 统治？ |
| 07 | [卷积与感受野](/guides/deep-learning/part2-dl-principles/07-convolution) | 卷积为什么有效？什么条件下等价于全连接？ |
| 08 | [残差连接与网络架构](/guides/deep-learning/part2-dl-principles/08-residual) | 退化问题的数学本质是什么？ |
| 09 | [初始化与数值稳定](/guides/deep-learning/part2-dl-principles/09-initialization) | 为什么不能用 0 初始化？为什么深层需要特定初始化？ |

## 这一部分要建立的判断力

- 训练不收敛时，能**按顺序排查**：初始化 → 归一化 → 残差 → 学习率
- 看到一个「训练技巧」时，能说清它**在数学上改变了什么**
- 能区分**优化困难**和**表达能力不足** —— 这两个的解法完全不同

::: warning 第 5 篇是硬骨头
它把反向传播在一个具体网络上一项一项推完。第一次读会慢，但推完一遍之后，
第 6-9 篇里所有「为什么这样设计」都会变得显然。
:::
