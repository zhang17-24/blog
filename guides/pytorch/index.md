---
title: PyTorch 入门学习笔记
description: 基于官方 8 篇教程整理：每章配大白话导读、官方原文要点和动手练习，用 FashionMNIST 一个项目串起从张量到完整训练脚本的全过程。
order: 2
---

# PyTorch 入门学习笔记

> 基于官方教程 `docs.pytorch.ac.cn/tutorials/beginner/basics/` 整理，去掉官网的导航噪音，为「会 Python 但没学过深度学习」的人补上概念铺垫。
>
> 对应官方版本：PyTorch 2.14.0+cu130 文档

---

## 这套文档是什么

官方那8 篇教程本身质量很高，但有几个对初学者不友好的地方：

1. **每章都假设你已经在别处学过东西**——比如「数据变换」那章只有 20 行就结束了，因为它默认你知道什么是归一化、为什么要 one-hot。
2. **8 个章节其实是同一段代码的 8 次局部放大**，单独看每章都很突兀。
3. **没有练习**——看完「优化循环」你知道自己要干什么，但不知道哪一步做错了。

所以这套笔记的写法是：**先给大白话导读（这是什么、为什么需要它），再放官方原文（准确、权威），最后给动手练习（把知识变成手感）**。

---

## 怎么用

**推荐路线：一条主线走到底。**

这份教程用的是同一个小项目——用神经网络给 **FashionMNIST** 衣服图片分类（10 个类别：T恤/裤子/套头衫/连衣裙/外套/凉鞋/衬衫/运动鞋/包/踝靴）。8 个章节是它的 8 个步骤：

```
1. 张量          →  搞懂 PyTorch 的基本积木
2. 数据集与加载器 →  把图片喂进去
3. 数据变换      →  把图片变成模型能吃的格式
4. 构建模型      →  搭出神经网络
5. 自动微分      →  让机器自动算梯度（最核心也最难懂）
6. 优化模型参数  →  训练循环，模型开始变聪明
7. 保存与加载    →  把训练成果存下来
8. 快速入门      →  把 1-7 压缩成一个完整脚本
```

**如果你赶时间**：直接看第 8 章「快速入门」，15 分钟拿到一个能跑的完整训练脚本，再回头逐章理解。

**如果你要理解原理**：`01 → 02 → 03 → 04 → 05 → 06 → 07`，别跳。

---

## 目录

### [Part 1 · 起步](/guides/pytorch/part1-basics/)

| 文档 | 内容 |
|---|---|
| [环境安装与运行方式](/guides/pytorch/part1-basics/01-setup) | 装 PyTorch、验证装好了、三种运行方式怎么选 |
| [先看懂整件事](/guides/pytorch/part1-basics/02-big-picture) | **强烈建议先读这个**。深度学习到底在做什么，一张图讲完整个流程 |

### [Part 2 · 官方教程 8 章](/guides/pytorch/part2-tutorial/)（导读 + 原文 + 练习）

| # | 文档 | 官方原文 | 本笔记补充 |
|---|---|---|---|
| 1 | [张量](/guides/pytorch/part2-tutorial/01-tensor) | tensorqs_tutorial | 张量 vs NumPy 数组、广播规则常见坑 |
| 2 | [数据集与数据加载器](/guides/pytorch/part2-tutorial/02-dataset) | data_tutorial | 什么是「batch」、为什么必须 shuffle |
| 3 | [数据变换](/guides/pytorch/part2-tutorial/03-transforms) | transforms_tutorial | 为什么要归一化到 [0,1]、one-hot 的意义 |
| 4 | [构建模型](/guides/pytorch/part2-tutorial/04-build-model) | buildmodel_tutorial | Linear/ReLU/Softmax 到底在算什么（带手算） |
| 5 | [自动微分](/guides/pytorch/part2-tutorial/05-autograd) | autogradqs_tutorial | 梯度是什么、计算图、雅可比积（最硬的一章） |
| 6 | [优化模型参数](/guides/pytorch/part2-tutorial/06-optimization) | optimization_tutorial | 学习率调大调小会怎样、三步循环的原理 |
| 7 | [保存与加载模型](/guides/pytorch/part2-tutorial/07-save-load) | saveloadrun_tutorial | state_dict 是什么、为什么要 `model.eval()` |
| 8 | [快速入门](/guides/pytorch/part2-tutorial/08-quickstart) | quickstart_tutorial | 全文压缩版，一页看完整个流程 |

### [Part 3 · 动手与附录](/guides/pytorch/part3-practice/)

| 文档 | 内容 |
|---|---|
| [fashion_mnist.py](/downloads/pytorch-fashion-mnist.py) | 完整训练脚本，可直接 `python fashion_mnist.py` 运行 |
| [exercises.py](/downloads/pytorch-exercises.py) | 15 个由浅入深的小练习，带答案 |
| [练习清单](/guides/pytorch/part3-practice/01-exercises) | 全部练习题汇总，可勾选 |
| [速查表](/guides/pytorch/part3-practice/02-cheatsheet) | 常用 API 一页速查 |


---

## 一句话记住整件事

> **给神经网络看很多张图片，告诉它每张是什么，它就不断调整自己的内部参数，让猜错的次数越来越少。**

「调整内部参数」这件事，就是第 5 章的自动微分 + 第 6 章的优化循环在干。其余 6 章都只是为了让这件事能跑起来。

---

## 关于官方 Colab

每篇原文页面顶部都有「在 Google Colab 中运行」的链接。如果你不打算在本地配环境，直接点那个链接在浏览器里跑，**不用装任何东西**。

- 原始链接：`https://docs.pytorch.ac.cn/tutorials/beginner/basics/intro.html`
- 快速开始 Colab：`https://docs.pytorch.ac.cn/tutorials/beginner/quickstart_tutorial.html`

---

## 学习建议

1. **每章的代码都自己敲一遍**，别复制粘贴。看懂和写出来之间隔着一道墙。
2. **把输出结果和文档里的对比**。数值不一样没关系，趋势对就行（loss 下降、准确率上升）。
3. **卡住了先打印 shape**。90% 的 PyTorch 报错都是 shape 不对，`print(x.shape)` 能解决大部分。
4. **做练习，不要只读**。练习答案在 `exercises.py` 里，但先自己想。
5. **不要跳第 5 章**。自动微分是 PyTorch 最大的价值所在，也是唯一一章真正需要理解的原理。

---

## 配套材料

这三份是同一套学习路径，按顺序读：

| 指南 | 讲什么 | 什么时候看 |
|---|---|---|
| [张量运算图解](/guides/tensor-ops/) | 14 张图讲清形状、广播、矩阵乘 | **读本文之前**，先把形状问题看明白 |
| [PyTorch 入门学习笔记](/guides/pytorch/) | API 和完整训练流程 | 就是本文 |
| [深度学习进阶](/guides/deep-learning/) | 从反向传播推导到 Transformer 与 LLaMA | 读完本文、想懂原理时 |

## 离线阅读

- [PyTorch 入门学习笔记 · 离线手册](/downloads/pytorch-handbook.html) —— 单文件 HTML，公式和代码高亮都在，双击即看，不需要网络
