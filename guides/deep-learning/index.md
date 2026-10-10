---
title: 深度学习进阶
description: 网上（包括大部分系统课）的问题是：告诉你「用残差连接能解决退化」，但不告诉你为什么能、什么条件下会失效、怎么判断一个方案是真的有效还是在过拟合。
order: 0
---

# 深度学习进阶 · 从原理到研究方法

> 这套材料的定位：**把「会写代码」变成「能判断」**。
>
> 上一套 PyTorch 入门教你怎么做；这一套告诉你**为什么这样做、什么时候不该这样做**。  
> 目标是让你能独立读论文、独立判断一个方案对不对、自己找出改进点。

---

## 这套材料和网上教程的区别

网上（包括大部分系统课）的问题是：告诉你「用残差连接能解决退化」，但不告诉你**为什么能**、**什么条件下会失效**、**怎么判断一个方案是真的有效还是在过拟合**。

这套材料的写法是：

1. **推导优先**。每个概念都用数学推导讲一遍，不用「可以理解为」糊弄。
2. **给出边界**。每个方法都说明它在什么条件下成立、什么时候崩。
3. **可验证**。每篇有可运行的代码，验证公式确实成立。

**数学要求**：会用导数、会矩阵乘法、理解条件概率即可。深度学习里用到的数学比你想的浅——真正的难点在**直觉和判断力**，不在公式难度。

---

## 目录与学习顺序

左侧目录树就是完整结构，这里再给一份可以一次看完的总表。

### [Part 1 · 机器学习基础](/guides/deep-learning/part1-ml-basics/)（4 篇）

这一部分是**地基**。跳过它，后面所有内容都是空中楼阁。算法岗笔试和论文里反复出现的概念都在这里。

| # | 文档                                                    | 核心问题                                  |
| - | ----------------------------------------------------- | ------------------------------------- |
| 1 | [机器学习的本质是什么](/guides/deep-learning/part1-ml-basics/01-what-is-ml)              | 学习=搜索？损失函数到底在衡量什么？                    |
| 2 | [泛化、过拟合与偏差方差](/guides/deep-learning/part1-ml-basics/02-generalization)          | 训练集好测试集差，为什么？                         |
| 3 | [正则化与容量控制](/guides/deep-learning/part1-ml-basics/03-regularization)               | L1/L2 到底在做什么？为什么 weight decay 有时不等价？  |
| 4 | [优化器：从 SGD 到 AdamW](/guides/deep-learning/part1-ml-basics/04-optimizers) | Momentum/Adam 的更新量怎么推出来的？AdamW 修好了什么？ |

### [Part 2 · 深度学习原理](/guides/deep-learning/part2-dl-principles/)（5 篇）

这一部分讲**深度网络特有的机制**。为什么深网络能工作、为什么会出现梯度消失、以及那些"魔法数字"（为什么是 1e-3、为什么 warmup）背后是什么。

| # | 文档                                                  | 核心问题                                       |
| - | --------------------------------------------------- | ------------------------------------------ |
| 5 | [反向传播的完整推导](/guides/deep-learning/part2-dl-principles/05-backprop)           | 链式法则在这个网络里怎么具体展开？梯度消失的本质是什么？               |
| 6 | [归一化：从 BatchNorm 到 RMSNorm](/guides/deep-learning/part2-dl-principles/06-normalization) | 归一化到底在解决什么？为什么 BatchNorm 淘汰而 LayerNorm 统治？ |
| 7 | [卷积与感受野](/guides/deep-learning/part2-dl-principles/07-convolution)                 | 卷积为什么有效？什么条件下等价于全连接？                       |
| 8 | [残差连接与网络架构](/guides/deep-learning/part2-dl-principles/08-residual)             | 退化问题的数学本质是什么？                              |
| 9 | [初始化与数值稳定](/guides/deep-learning/part2-dl-principles/09-initialization)             | 为什么不能用 0 初始化？为什么深层需要特定初始化？                 |

### [Part 3 · Transformer 与现代 LLM](/guides/deep-learning/part3-transformer/)（5 篇）

这一部分是**当前主流架构**。从 Attention 的推导一路到 2024-2025 年的主流设计。

| #  | 文档                                                                     | 核心问题                                    |
| -- | ---------------------------------------------------------------------- | --------------------------------------- |
| 10 | [Attention 的数学推导](/guides/deep-learning/part3-transformer/10-attention)              | QKV 为什么要除 √d？softmax 为什么必须有？            |
| 11 | [多头注意力与位置编码](/guides/deep-learning/part3-transformer/11-multi-head-rope)                       | 多头在多做什么？位置信息怎么注入？RoPE 的旋转思想             |
| 12 | [从 Transformer 到 LLaMA 系列](/guides/deep-learning/part3-transformer/12-transformer-to-llama) | 现代 LLM 改了什么？RMSNorm/SwiGLU/RoPE 各解决了什么？ |
| 13 | [推理优化：KV Cache 与 GQA](/guides/deep-learning/part3-transformer/13-kv-cache-gqa)         | 自回归生成为什么慢？缓存和 GQA 怎么解决？                 |
| 14 | [缩放定律与高效注意力](/guides/deep-learning/part3-transformer/14-scaling-laws)                       | 为什么可以「大力出奇迹」？FlashAttention 赢在哪？        |

### [Part 4 · 研究方法论](/guides/deep-learning/part4-research/)（2 篇）

这一部分是**从「会学」到「会研究」**。算法岗面试和实际研究，靠的是这套东西。

| #  | 文档                                  | 核心问题                  |
| -- | ----------------------------------- | --------------------- |
| 15 | [怎么读一篇论文](/guides/deep-learning/part4-research/15-reading-papers) | 三遍法怎么用？如何判断一个方法的真实贡献？ |
| 16 | [怎么设计实验](/guides/deep-learning/part4-research/16-designing-experiments)   | 消融实验怎么做才可信？如何避免自欺欺人？  |

### [Part 5 · 附录](/guides/deep-learning/part5-appendix/)

| 文档 | 内容 |
| --- | --- |
| [公式速查表](/guides/deep-learning/part5-appendix/17-formula-cheatsheet) | 所有关键公式一页汇总 |
| [面试高频问题](/guides/deep-learning/part5-appendix/18-interview-questions) | 算法岗面试会问的 30 个问题（含答案要点） |
| [llama_from_scratch.py](/downloads/llama_from_scratch.py) | **从零实现的 LLaMA**（RMSNorm + RoPE + GQA + SwiGLU + Pre-LN），已实测前向 + 反向通过 |
| [深度学习进阶手册.html](/downloads/deep-learning-handbook.html) | 单页离线阅读版（19 篇全部打包，含公式与代码高亮） |

---

## 三条学习路线

**路线 A · 打基础 + 读论文（推荐，最扎实）**  
按 1 → 16 顺序完整走一遍。适合有 2-3 个月、目标是能独立读论文和做研究。

**路线 B · 只要工程能力（最快落地）**  
`1 → 2 → 4 → 6 → 10 → 12 → 13`。跳过推导细节，但 Part 3 全部要读——那是当前架构的必需品。

**路线 C · 面试突击**  
直接看 [面试高频问题](/guides/deep-learning/part5-appendix/18-interview-questions)，按题目反查对应文档。重点：Part 1 全部 + Part 2 的推导 + Part 3 的 Attention。

---

## 前置知识清单

开始前确认你会这些，不会就先补：

**必须会**

- 导数、偏导、链式法则
- 矩阵乘法、求逆（不用手算，知道意思即可）
- 概率：条件概率、贝叶斯、期望、方差
- Python + NumPy 基本操作

**不用会（会查就行）**

- 矩阵特征值、SVD 推导
- 大数定律的严格证明
- 卷积的傅里叶视角

**边学边补**

- 如果梯度公式不熟 → 先看 Part 2 第 5 篇，它会完整推导一遍
- 如果注意力机制第一次接触 → 直接从 Part 3 第 10 篇开始，那里从零推导

---

## 每篇的读法建议

**不要只读。** 每篇都有代码，建议流程：

```
1. 先读推导，假装自己懂了
2. 手推一遍关键公式（纸上）
3. 跑代码验证你推的结果
4. 合上文档，用自己的话复述「这个方法解决什么问题」
5. 做最后的「边界条件」自测题
```

第 4 步是关键。**如果你能讲清楚一个方法在什么情况下会失效，你才是真懂了。**

---

## 关于代码

**完整的 LLaMA 实现**：[llama_from_scratch.py](/downloads/llama_from_scratch.py)，163 行，可运行：

```bash
pip install torch
python llama_from_scratch.py    # 前向 + loss + 反向，全程通过
```

它包含 RMSNorm、RoPE、GQA、SwiGLU、Pre-LN 全部现代组件，可以直接作为你的实现参考。

**文档里每段代码的输出都对应某个公式或结论（都是实测的）。如果你推出来的数和代码算出来的不一样，先信代码。**

---

**从第 1 篇开始** → [机器学习的本质是什么](/guides/deep-learning/part1-ml-basics/01-what-is-ml)
