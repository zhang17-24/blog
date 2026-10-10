---
title: Part 3 · 动手与附录
description: 练习清单与常用 API 速查表，以及两个可直接运行的 Python 脚本。
order: 3
---

# Part 3 · 动手与附录
看懂和写出来之间隔着一道墙。这部分是把知识变成手感的地方。

## 本部分内容

| 章节 | 讲什么 |
|---|---|
| [练习清单](/guides/pytorch/part3-practice/01-exercises) | 15 个由浅入深的练习，覆盖张量、广播、autograd、训练循环、保存加载 |
| [速查表](/guides/pytorch/part3-practice/02-cheatsheet) | 常用 API 一页速查：张量创建、形状操作、模型、损失、优化器、训练循环 |

## 可运行的代码

两个脚本都可以直接下载运行，**建议先自己敲一遍再看**：

| 文件 | 用途 |
|---|---|
| [fashion_mnist.py](/downloads/pytorch-fashion-mnist.py) | 完整训练脚本，`python fashion_mnist.py` 直接跑 |
| [exercises.py](/downloads/pytorch-exercises.py) | 15 个练习的参考答案 |

```bash
pip install torch torchvision
python fashion_mnist.py
```

## 学习建议

1. **每章的代码都自己敲一遍**，别复制粘贴。
2. **把输出结果和文档里的对比**。数值不一样没关系，趋势对就行（loss 下降、准确率上升）。
3. **卡住了先打印 shape**。`print(x.shape)` 能解决大部分报错。
4. **做练习，不要只读**。答案在 `exercises.py` 里，但先自己想。
