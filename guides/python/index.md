---
title: Python
description: 从语法基础到数据结构、再到异步编程的完整路径。
order: 5
---

# Python

Python 好上手，但「能用」和「用得好」之间隔着不少东西：
可变对象陷阱、闭包的延迟绑定、GIL 与异步的关系……

这个指南按从语法到工程实践的顺序组织。

## 章节

| # | 章节 | 内容 |
| --- | --- | --- |
| 01 | [基础语法](/guides/python/01-basics) | 类型、可变与不可变、作用域 |
| 02 | [数据结构](/guides/python/02-data-structures) | list/dict/set 的复杂度与选择 |
| 03 | [异步编程](/guides/python/03-async) | asyncio、GIL、什么时候不该用 |

## 环境准备

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

::: tip 别用系统 Python
永远在虚拟环境里装包。`pip install` 到系统环境迟早会搞坏某个依赖，
而且 macOS 和多数 Linux 发行版已经开始阻止你这么做了。
:::
