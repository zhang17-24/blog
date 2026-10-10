---
title: 张量运算图解
description: 用 14 张图讲清 PyTorch 里最容易搞错的形状问题——广播、reshape、拼接、归约、内存连续性，每个操作配实测输出。
order: 1
---

# 张量运算图解

> 用图讲清楚 PyTorch 里最容易搞错的形状问题。
>
> 全部 14 张图都是脚本生成的（[make_figs.py](/downloads/tensor-ops-make-figs.py)），全部代码输出都是实测的（[verify.py](/downloads/tensor-ops-verify.py)）。
>
> **配套**：[PyTorch 入门学习笔记](/guides/pytorch/) · [深度学习进阶](/guides/deep-learning/)

---

## 为什么单独做这份图解

入门笔记里讲过张量的 API，但**形状问题光看文字是学不会的**。

「`(3,1)` 和 `(3,)` 相加得到 `(3,3)`」—— 这句话你读十遍也可能记不住。但看一张图，一眼就懂。

这份文档把 14 个最容易出错的操作用图讲清楚。**建议对着图跑一遍代码。**

---

## 目录

| # | 内容 | 图 |
|---|---|---|
| 1 | [张量与维度](/guides/tensor-ops/01-dims) | 四种维度的张量 |
| 2 | [索引与切片](/guides/tensor-ops/02-indexing) | 取行/取列/取子矩阵 |
| 3 | [形状变换](/guides/tensor-ops/03-shape) | reshape 与转置 |
| 4 | [增删维度](/guides/tensor-ops/04-squeeze) | squeeze / unsqueeze |
| 5 | [**广播机制**](/guides/tensor-ops/05-broadcasting) ★ | 广播的三种情况 |
| 6 | [矩阵运算](/guides/tensor-ops/06-matrix) ★ | 两种乘法的区别 |
| 7 | [拼接与堆叠](/guides/tensor-ops/07-cat-stack) | cat / stack |
| 8 | [归约操作](/guides/tensor-ops/08-reduction) | dim 的方向 |
| 9 | [高级索引](/guides/tensor-ops/09-advanced-index) | index_select / gather |
| 10 | [内存布局](/guides/tensor-ops/10-memory) | 连续性问题 |
| 11 | [完整流程串联](/guides/tensor-ops/11-pipeline) | 从图像到输出 |
| 12 | [报错对照表](/guides/tensor-ops/12-errors) | — |
| 13 | [练习](/guides/tensor-ops/13-exercises) | — |
| 14 | [一页速查](/guides/tensor-ops/14-cheatsheet) | 常用操作汇总 |

---

## 配套材料

这三份是同一套学习路径，按顺序读：

| 指南 | 讲什么 | 什么时候看 |
|---|---|---|
| [张量运算图解](/guides/tensor-ops/) | 14 张图讲清形状、广播、矩阵乘 | 就是本文 |
| [PyTorch 入门学习笔记](/guides/pytorch/) | API 和完整训练流程 | **读完本文接着读** |
| [深度学习进阶](/guides/deep-learning/) | 从反向传播推导到 Transformer 与 LLaMA | 想懂原理时 |

## 源文件

- [tensor-ops-make-figs.py](/downloads/tensor-ops-make-figs.py) —— 生成全部 14 张图
- [tensor-ops-verify.py](/downloads/tensor-ops-verify.py) —— 验证本文所有代码输出

## 离线阅读

- [张量运算图解 · 离线手册](/downloads/tensor-ops-handbook.html) —— 单文件 HTML，14 张图已内联，双击即看，不需要网络
