---
title: Part 3 · Transformer 与 LLM
description: 当前主流架构。从 Attention 的推导一路到 2024–2025 年的主流设计。
order: 3
---

# Part 3 · Transformer 与 LLM

这一部分是**当前主流架构**。从 Attention 的推导一路到 2024–2025 年的主流设计。

| # | 章节 | 核心问题 |
| --- | --- | --- |
| 10 | [Attention 的数学推导](/guides/deep-learning/part3-transformer/10-attention) | QKV 为什么要除 √d？softmax 为什么必须有？ |
| 11 | [多头注意力与位置编码](/guides/deep-learning/part3-transformer/11-multi-head-rope) | 多头在多做什么？位置信息怎么注入？RoPE 的旋转思想 |
| 12 | [从 Transformer 到 LLaMA 系列](/guides/deep-learning/part3-transformer/12-transformer-to-llama) | 现代 LLM 改了什么？RMSNorm / SwiGLU / RoPE 各解决了什么？ |
| 13 | [推理优化：KV Cache 与 GQA](/guides/deep-learning/part3-transformer/13-kv-cache-gqa) | 自回归生成为什么慢？缓存和 GQA 怎么解决？ |
| 14 | [缩放定律与高效注意力](/guides/deep-learning/part3-transformer/14-scaling-laws) | 为什么可以「大力出奇迹」？FlashAttention 赢在哪？ |

## 配套代码

[从零实现的 LLaMA](/downloads/llama_from_scratch.py)（RMSNorm + RoPE + GQA + SwiGLU + Pre-LN），
163 行，已实测前向 + 反向通过。第 12、13 篇里的每个组件在这份代码里都有对应实现。

```bash
pip install torch
python llama_from_scratch.py    # 前向 + loss + 反向，全程通过
```

## 这一部分要建立的判断力

- 看到一个 LLM 架构图，能**逐个组件说出它为什么在那里**
- 能算清一次推理的**显存占用和 FLOPs**，判断瓶颈在哪
- 能区分**训练期优化**和**推理期优化** —— 两者的约束完全不同
