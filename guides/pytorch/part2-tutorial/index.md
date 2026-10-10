---
title: Part 2 · 官方教程 8 章
description: 官方 8 篇入门教程的导读版：每章先讲大白话，再放原文要点，最后给动手练习。
order: 2
---

# Part 2 · 官方教程 8 章
对应官方 `docs.pytorch.ac.cn/tutorials/beginner/basics/` 的 8 篇教程。

**这 8 章其实是同一段代码的 8 次局部放大**——用神经网络给 FashionMNIST 衣服图片分类（10 个类别：T恤 / 裤子 / 套头衫 / 连衣裙 / 外套 / 凉鞋 / 衬衫 / 运动鞋 / 包 / 踝靴）。

每章的写法是：**先给大白话导读（这是什么、为什么需要它）→ 再放官方原文要点（准确、权威）→ 最后给动手练习（把知识变成手感）**。

## 章节

| # | 章节 | 官方原文 | 一句话 |
|---|---|---|---|
| 1 | [张量](/guides/pytorch/part2-tutorial/01-tensor) | tensorqs_tutorial | PyTorch 的基本积木 |
| 2 | [数据集与加载器](/guides/pytorch/part2-tutorial/02-dataset) | data_tutorial | 把图片喂进去 |
| 3 | [数据变换](/guides/pytorch/part2-tutorial/03-transforms) | transforms_tutorial | 变成模型能吃的格式 |
| 4 | [构建模型](/guides/pytorch/part2-tutorial/04-build-model) | buildmodel_tutorial | 搭出神经网络 |
| 5 | [自动微分](/guides/pytorch/part2-tutorial/05-autograd) | autogradqs_tutorial | 让机器自动算梯度 ★ 最难 |
| 6 | [优化模型参数](/guides/pytorch/part2-tutorial/06-optimization) | optimization_tutorial | 训练循环，模型开始变聪明 |
| 7 | [保存与加载模型](/guides/pytorch/part2-tutorial/07-save-load) | saveloadrun_tutorial | 把成果存下来 |
| 8 | [快速入门](/guides/pytorch/part2-tutorial/08-quickstart) | quickstart_tutorial | 把 1–7 压成一页 |

## 怎么读

- **赶时间**：直接看第 8 章 [快速入门](/guides/pytorch/part2-tutorial/08-quickstart)，15 分钟拿到一个能跑的完整训练脚本，再回头逐章理解。
- **要理解原理**：`01 → 02 → 03 → 04 → 05 → 06 → 07`，别跳。**第 5 章是唯一真正需要理解原理的一章**，自动微分是 PyTorch 最大的价值所在。
- **卡住了先 `print(x.shape)`**。90% 的 PyTorch 报错都是形状不对，形状问题看 [张量运算图解](/guides/tensor-ops/)。

做完这 8 章，进 [Part 3 · 动手与附录](/guides/pytorch/part3-practice/) 把练习过一遍。
