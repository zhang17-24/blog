---
title: Rust
description: 从所有权开始，把 Rust 的心智模型真正搭起来。
order: 1
---

# Rust

Rust 的难点不在语法，而在于它要求你把「这块内存归谁管」想清楚。
以前写 C++ 或 Go，这些决定是隐式的；Rust 把它们摆到台面上。

这个指南按我自己的理解路径组织，建议顺着读。

## 章节

| # | 章节 | 内容 |
| --- | --- | --- |
| 01 | [所有权](/guides/rust/01-ownership) | 三条规则、移动、借用、NLL |
| 02 | [生命周期](/guides/rust/02-lifetimes) | 标注语法、省略规则、结构体里的引用 |
| 03 | [Trait 与泛型](/guides/rust/03-traits) | 抽象、关联类型、静态分发与动态分发 |

## 读之前需要什么

- 至少写过一门带指针的语言（C / C++ / Go 都行）
- 装好 Rust 工具链：`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

::: tip 一句话心法
**编译不过的时候，先问「这个值的所有者是谁」，而不是先想着加 `clone()`。**
大部分借用错误都能靠调整数据的所有权结构解决，而不是靠 clone 绕过去。
:::
