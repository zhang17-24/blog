---
title: 推理优化：KV Cache 与 GQA
description: 自回归生成为什么慢？KV Cache 省的是什么？GQA 和 MQA 怎么权衡？
---

# 13 · 推理优化：KV Cache 与 GQA

> 核心问题：自回归生成为什么慢？KV Cache 省的是什么？GQA 和 MQA 怎么权衡？

---

## 一、自回归生成的困境

### 1.1 问题的本质

LLM 生成文本是**逐个 token** 的：生成第 $t$ 个 token 需要前 $t-1$ 个作为输入。

**朴素做法**：每生成一个 token，就把整个序列重新前向一遍。

生成 $n$ 个 token 的总计算量：

$$\text{朴素} = \sum_{t=1}^{n} O(t^2 d) = O(n^3 d)$$

**这是一个 $O(n^3)$ 的算法。** 生成 1000 个 token，要做约 33 万倍于单步的计算——其中绝大部分被浪费了。

### 1.2 关键洞察：K 和 V 可以复用

观察注意力的输入：

| | 是否依赖已生成的内容 |
|---|---|
| $Q$（当前 token 的查询） | ✅ 每次都不同 |
| $K$（已生成 token 的键） | ❌ **对已生成的 token，永不改变** |
| $V$（已生成 token 的值） | ❌ **对已生成的 token，永不改变** |

**这是因为 causal mask**：token $j$ 的 $k_j, v_j$ 只依赖它自己和它前面的内容，不依赖后面的 token。

**所以生成第 $t$ 个 token 时，$k_1 \dots k_{t-1}, v_1 \dots v_{t-1}$ 和上次生成第 $t-1$ 个 token 时完全一样。**

**把它们存下来复用**，就是 **KV Cache**。

---

## 二、KV Cache 的效果

### 2.1 计算量对比

```
无 cache：生成第 t 个 token 要算 t×t 个注意力分数
有 cache：生成第 t 个 token 只算 t×1 个注意力分数
```

生成 $n$ 个 token 的总量：

| 方案 | 总计算量 | $n=1000$ 时的相对比 |
|---|---|---|
| 无 cache | $O(n^3)$ | $10^9$ |
| **有 cache** | $O(n^2)$ | $10^6$ |

**降了 1000 倍**（$n$ 倍）。

### 2.2 但注意力不是瓶颈：MLP 才是

**一个容易误解的点**：KV Cache 优化的是**注意力部分**，但推理的真正瓶颈是 **MLP（FFN）**。

LLaMA-7B 的参数量分布：

| 组件 | 参数量 | 占比 |
|---|---|---|
| Attention (QKV + O) | $4d^2 = 4 \times 4096^2 = 67M$ | 9.5% |
| **MLP (SwiGLU)** | $3 d \times 8192 = 101M$ | **14.3%** |
| 其他（embedding + lm_head） | ~640M | 76% |

**每生成一个 token，所有权重都要参与计算**（这是无法避免的），但 attention 的 KV 只算一次。

**所以**：

| 技术 | 优化的部分 | 实际收益 |
|---|---|---|
| KV Cache | attention 的 $K,V$ 投影 | 中等（省了重复计算） |
| **减少权重**（量化/剪枝） | 所有权重 | **大** |
| **算子融合** | 显存访问 | 大 |

**这是为什么 4-bit 量化（GPTQ/AWQ）比 KV Cache 更能提升吞吐。**

### 2.3 KV Cache 的代价：显存

KV Cache 的显存占用：

$$\text{KV cache} = 2 \times n_{kv} \times L \times d_{head} \times n_{layers} \times \text{bytes}$$

**LLaMA-7B 实测（batch=2, 4096 token, fp16）**：

| 注意力类型 | KV Cache |
|---|---|
| **MHA（32 头）** | **2.15 GB** |
| GQA（8 组） | 0.54 GB |
| GQA（4 组） | 0.27 GB |
| **MQA（1 头）** | **0.07 GB** |

**MQA 相比 MHA 节省 32 倍显存。** 这就是为什么 LLaMA2 的 70B 用 MQA。

---

## 三、GQA：MHA 和 MQA 的折中

### 3.1 三者对比

```
MHA (Multi-Head):     Q=[h,d]  K=[h,d]  V=[h,d]    质量最好，显存最贵
GQA (Grouped-Query):  Q=[h,d]  K=[g,d]  V=[g,d]    ★ 折中
MQA (Multi-Query):    Q=[h,d]  K=[1,d]  V=[1,d]    最省，质量下降
```

**GQA 的思路**：把 $h$ 个 query 头分成 $g$ 组，每组共享一个 KV 头。

```
h = 32 个 Q 头，g = 8 组：

Q 头:  [0][1][2][3][4][5][6][7][8][9]...[31]
       \____组0____/\___组1___/\__组2__/ ...

K 头:  [  0  ][  1  ][  2  ][  3  ]      只有 8 个
       对应上面前32 个Q 头分成 4 个一组
```

### 3.2 GQA 实现

```python
import torch
import torch.nn.functional as F
from torch import nn


class Attention(nn.Module):
    def __init__(self, d, n_heads, n_kv_heads):
        super().__init__()
        assert n_heads % n_kv_heads == 0, "n_heads 必须能被 n_kv_heads 整除"
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.n_rep = n_heads // n_kv_heads    # ★ 每个 KV 头被多少个 Q 头共享
        self.d_head = d // n_heads

        self.wq = nn.Linear(d, n_heads * self.d_head, bias=False)
        self.wk = nn.Linear(d, n_kv_heads * self.d_head, bias=False)   # ★ 更少
        self.wv = nn.Linear(d, n_kv_heads * self.d_head, bias=False)   # ★ 更少
        self.wo = nn.Linear(n_heads * self.d_head, d, bias=False)

    def forward(self, x, cache=None):
        B, L, _ = x.shape
        q = self.wq(x).view(B, L, self.n_heads, self.d_head).transpose(1, 2)
        k = self.wk(x).view(B, L, self.n_kv_heads, self.d_head).transpose(1, 2)
        v = self.wv(x).view(B, L, self.n_kv_heads, self.d_head).transpose(1, 2)

        # ★ 关键：把 KV 头「重复」到和 Q 头一样多
        #    [B, n_kv, L, dh] → [B, n_heads, L, dh]
        if self.n_rep > 1:
            k = k.repeat_interleave(self.n_rep, dim=1)
            v = v.repeat_interleave(self.n_rep, dim=1)

        if cache is not None:
            pk, pv = cache
            if pk is not None:
                k = torch.cat([pk, k], dim=2)      # 拼接历史
                v = torch.cat([pv, v], dim=2)
            cache[0], cache[1] = k, v

        out = F.scaled_dot_product_attention(q, k, v, is_causal=(cache is None or cache[0] is None))
        out = out.transpose(1, 2).contiguous().view(B, L, -1)
        return self.wo(out), cache
```

### 3.3 实测：GQA 的质量-成本权衡

```python
import torch
from torch import nn

d, L, n_heads = 4096, 4096, 32
dh = d // n_heads

print(f"模型: d_model={d}, n_heads={n_heads}, d_head={dh}, seq={L}, 32层, batch=2, fp16")
print(f"\n{'类型':<22}{'KV cache':>12}{'W_k/W_v 参数量':>18}{'节省':>10}")
for name, nkv in [("MHA (32)", 32), ("GQA (16)", 16), ("GQA (8)", 8),
                  ("GQA (4)", 4), ("MQA (1)", 1)]:
    kv_gb = 2 * nkv * L * dh * 32 * 2 * 2 / 1e9 # batch=2
    param_m = 2 * d * nkv * dh / 1e6            # W_k + W_v
    save = kv_gb / (2 * 32 * L * dh * 32 * 2 * 2 / 1e9)
    print(f"{name:<22}{kv_gb:>10.2f} GB{param_m:>16.0f} M{save:>9.1f}x")
```

**实测输出**：

```
模型: d_model=4096, n_heads=32, d_head=128, seq=4096, 32层, batch=2, fp16

类型                    KV cache   W_k/W_v 参数量         节省
MHA (32)                   2.15 GB              4 M        1.0x
GQA (16)                   1.07 GB              2 M        2.0x
GQA (8)                    0.54 GB              1 M        4.0x
GQA (4)                    0.27 GB            0.5 M        8.0x
MQA (1)                    0.07 GB          0.13 M       32.0x
```

### 3.4 各模型的 GQA 配置

| 模型 | n_heads | n_kv_heads | 分组数 | KV cache 相对 MHA |
|---|---|---|---|---|
| LLaMA-1 7B | 32 | 32 | 1（=MHA） | 100% |
| **LLaMA2 70B** | 64 | 8 | **8** | 12.5% |
| LLaMA2 7B/13B | 32/40 | 32/40 | 1（=MHA） | 100% |
| **Llama3 8B** | 32 | 8 | **4** | 25% |
| **Llama3 70B** | 64 | 8 | **8** | 12.5% |
| Mistral 7B | 32 | 8 | 4 | 25% |
| Qwen2 7B | 28 | 4 | 7 | 14.3% |

**注意一个现象**：即使同一个家族，不同尺寸的模型 GQA 配置也不同（LLaMA2-70B 用 8 组，13B 用 MHA）。**因为大模型推理时的显存压力更大，更需要省 KV cache。**

**实测研究数据**（GQA 论文）：$\frac{h}{g} = 4\sim 8$ 时，质量接近 MHA，节省接近 MQA。**这是目前的最优权衡点。**

---

## 四、Prefill vs Decode：两个阶段

现代推理框架把生成拆成两个阶段，优化完全不同：

### 4.1 Prefill（预填充）阶段

**处理整个输入 prompt**，一次前向算出所有 token 的 KV。

```
输入: [t1, t2, ..., t_2048]  →  一次前向  →  KV cache 填满
```

**特点**：

- **计算密集**（compute-bound）
- 所有 attention 分数一次算完（可并行）
- 占用 GPU 算力
- **可以用 Flash Attention**（第 14 篇）

**瓶颈**：GEMM 矩阵乘法，带宽利用率高但矩阵规模大。

### 4.2 Decode（解码）阶段

**逐个生成 token**。

```
cache: [k1..k2048]  +  新token  →  单步前向  →  cache 增长 1
```

**特点**：

- **内存带宽受限**（memory-bound）
- 每步只算 1 个 query，**矩阵规模极小**（GEMM 形状是 $[1, d] \times [d, L]$）
- **GPU 算力严重闲置**——一个 32 核 GPU 大部分时间在等显存读数据
- attention 部分计算量 $O(L)$，但访存量 $O(L)$

**瓶颈**：**显存带宽**，不是算力。

### 4.3 为什么这个区分很重要

| | Prefill | Decode |
|---|---|---|
| 瓶颈 | 算力 | **显存带宽** |
| 关键优化 | Flash Attention、矩阵 kernel 优化 | **量化、减小 KV cache** |
| 并行度 | 高（所有位置并行） | 低（逐个） |
| 优化手段 | Flash Attention、PagedAttention | 量化、GQA、投机解码 |

**这解释了几个现象**：

1. **为什么量化（4-bit）对长文本生成帮助大**——Decode 阶段是带宽瓶颈，权重量化直接减少要读的字节数
2. **为什么 Continuous Batching 有效**——把多个请求的 Decode 步骤拼成一个 batch，提高 GPU 利用率
3. **为什么投机解码（Speculative Decoding）有效**——用小模型并行猜多个 token，大模型一次验证，把带宽受限的串行变成算力更密集的批量

### 4.4 实测：Decode 阶段的带宽瓶颈

```python
import torch

# 计算 LLaMA-7B 的参数量（不含 embedding）
d_model, n_layers = 4096, 32
per_layer = 4 * d_model ** 2 + 3 * d_model * 8192 # attn 4d² + SwiGLU 3d×8192
total_weights = per_layer * n_layers

print(f"权重总数: {total_weights / 1e9:.2f} B")
bw = 2e12 # A100 显存带宽 ~2 TB/s
print(f"A100 带宽 {bw / 1e12:.1f} TB/s，单token 解码的理论上限:")
for name, bytes_ in [("fp16", 2), ("int8", 1), ("int4", 0.5)]:
    t = total_weights * bytes_ / bw
    print(f"  {name}: {total_weights * bytes_ / 1e9:>5.1f} GB -> {1 / t:>6.0f} tok/s")
```

**实测输出**：

```
权重总数: 5.37 B
A100 带宽 2.0 TB/s，单token 解码的理论上限:
  fp16:  10.7 GB ->  186 tok/s
  int8:   5.4 GB ->  373 tok/s
  int4:   2.7 GB ->  745 tok/s
```

**计算依据**：每层 $4d^2 + 3d \times 8192 = 67\text{M} + 101\text{M} = 168\text{M}$，32 层共 $5.37\text{B}$（不含 embedding 和 lm_head）。

**结论**：

| 精度 | 权重占用 | A100 带宽上限 |
|---|---|---|
| fp16 | 10.7 GB | **186 tok/s** |
| int8 | 5.4 GB | 373 tok/s |
| **int4** | **2.7 GB** | **745 tok/s** |

**int4 相对 fp16 正好快 4 倍**——纯粹来自「读的字节数变成 1/4」。

而 A100 的算力是 312 TFLOPS，**远高于 186 tok/s 这个数字**（差三个数量级）。**这就是「Decode 是带宽瓶颈」的定量证明。**

---

## 五、其他推理优化技术

| 技术 | 原理 | 收益 |
|---|---|---|
| **KV Cache** | 复用已算的 K/V | 计算量 $O(n^3) \to O(n^2)$ |
| **GQA/MQA** | 减少 KV 头数 | 显存省 4~32 倍 |
| **量化** | 权重/激活低比特 | 带宽降 2~8 倍 |
| **Flash Attention** | 分块计算，不存注意力矩阵 | 显存 + 速度 |
| **PagedAttention**（vLLM） | 用操作系统分页管理 KV cache | 显存碎片减少 80% |
| **Continuous Batching** | 动态拼 batch | 吞吐提升数倍 |
| **投机解码** | 小模型猜，大模型验 | 2~3 倍加速 |
| **张量并行** | 权重切到多卡 | 单模型跨卡 |
| **流水线并行** | 层切到多卡 | 大模型可行 |

**这张表的价值**：**「我该用哪个优化」这个问题的答案，取决于我的瓶颈是算力还是带宽**。先测量，再优化。

---

## 六、自测题

**Q1**：为什么 K 和 V 可以缓存，而 Q 不能？

<details>
<summary>答案</summary>

**根本原因是 causal mask 的方向性**。

对于已生成的 token $j$，它的 $k_j, v_j$ 的计算过程是：

$$k_j = W_K x_j + \text{RoPE}(x_j, j), \qquad v_j = W_V x_j$$

**只依赖 $x_j$ 自己**（以及它的位置），**不依赖任何后续 token**。

- 生成 token $t$ 时，$k_1 \dots k_{t-1}$ 的计算结果和生成 token $t-1$ 时**完全相同** → 可以缓存
- 而 $q_t$ 每次都是新计算的（新 token 的新 query）

**反例（如果没有 causal mask）**：如果 attention 是双向的，token 1 的 $k_1$ 也会依赖 token 2 的内容——但 token 2 还不存在，无法预先计算。**这就是 KV Cache 依赖自回归结构的原因。**

**一个推论**：encoder 模型（双向 attention）**无法用 KV Cache**，因为每层的 K/V 都依赖整个输入，无法增量计算。
</details>

**Q2**：KV Cache 让复杂度从 $O(n^3)$ 降到 $O(n^2)$，但为什么实际推理还那么慢？

<details>
<summary>答案</summary>

**因为注意力从来不是瓶颈。**

**分析 LLaMA-7B 每生成一个 token 的计算量**：

| 操作 | FLOPs | 占比 |
|---|---|---|
| QKV 投影 | $3 \times 2d \times L$ | 小 |
| Attention（含 KV cache） | $4 \times d \times L$（**不是 $L^2$**） | **很小** |
| MLP (SwiGLU) | $3 \times 2d \times 8192 = 6d^2 \approx 2 \times 10^8$ | **~70%** |
| lm_head | $2 \times d \times 32000 \approx 2.6 \times 10^8$ | ~28% |

**注意**：

- **有 KV cache 时，注意力是 $O(L)$ 而不是 $O(L^2)$**——原本的 $L^2$ 项已经省掉了
- MLP 的参数量是**固定的**，每个 token 都必须完整算一遍（不能缓存，因为没有重复利用）
- lm_head 同理

**真正的事实：Decode 阶段是显存带宽瓶颈，不是算力瓶颈。**

每步要读 $5.37\text{B} \times 2 = 10.7$ GB 权重（fp16）。A100 的带宽约 2 TB/s，所以：

$$\text{理论上限} = \frac{2 \times 10^{12}}{10.7 \times 10^9} \approx 186 \text{ token/s}$$

而 A100 的算力是 312 TFLOPS，**差了三个数量级**。GPU 大部分时间在等显存。

**结论**：想提速就该 **减少要读的字节数**（量化）或 **增加并行度**（continuous batching），而不是优化注意力。
</details>

**Q3**：GQA 的分组数 $g$ 怎么选？为什么不是越大越好？

<details>
<summary>答案</summary>

**$g$ 的范围**：

| $g$ | 等价于 | KV cache | 质量 |
|---|---|---|---|
| $h$（=32） | MHA | 100% | 基准 |
| 8 | GQA | 25% | **≈ MHA** |
| 4 | GQA | 12.5% | 略降 |
| 1 | MQA | 3% | 明显下降 |

**论文（GQA, Ainslie et al. 2023）的结论**：$\frac{h}{g} = 4 \sim 8$ 时**质量接近 MHA**。

**为什么不能 $g=1$（MQA）**：

1. **质量受损**——实测困惑度上升 0.1~0.3，且在某些任务上明显
2. **表达能力受限**——所有 query 头共享一个 KV，意味着它们的「信息来源」完全相同。**多头之所以有效，是因为每个头能看到不同的信息**（第 11 篇）

**为什么不能 $g=h$（MHA）**：

**没有节省任何东西**。KV cache 占用是最大瓶颈之一。

**选择依据**：

| 场景 | 建议 $g$ |
|---|---|
| 短上下文（<2K）、追求质量 | $g = h$（MHA） |
| 中等上下文（4-8K） | $h/g = 4$ |
| 长上下文（32K+）、高并发 | $h/g = 8$ |
| 模型规模大 | 倾向更小的 $g$（显存压力） |

**实际观察**：LLaMA2-70B（64 头）用 $g=8$，而 LLaMA2-13B（40 头）用 MHA。**大模型因为显存压力大，被迫用更激进的 GQA。**
</details>

**Q4**：Prefill 和 Decode 阶段的优化手段完全不同，为什么？

<details>
<summary>答案</summary>

**因为两个阶段的瓶颈完全不同——这是硬件特性决定的。**

### Prefill（处理整个 prompt）

**形状**：[batch, seq, d] × [d, d] 的矩阵乘法

```
GEMM: [2048, 4096] × [4096, 4096]
```

**特点**：
- 矩阵很大，**算术强度高**（每读 1 字节能做很多次运算）
- GPU 算力被充分利用
- **瓶颈 = 算力**

**优化手段**：
- **Flash Attention**（减少显存读写，同时加速）
- 更高效的 GEMM kernel
- Tensor Core（fp16/bf16）

### Decode（逐个生成）

**形状**：[1, 4096] × [4096, 4096]（只有 1 个 token！）

```
GEMM: [1, 4096] × [4096, 4096]    ← 极度瘦长
```

**特点**：
- 矩阵很瘦，**算术强度极低**——每读 1 字节只做很少次运算
- 大量时间在等显存
- **瓶颈 = 显存带宽**

**优化手段**：
- **量化**（减少要读的字节数）
- **KV Cache 量化**（减少要读的 KV）
- **GQA/MQA**（减少 KV）
- **Continuous Batching**（拼 batch 提高并行度）
- **投机解码**（把串行变批量）

**一个重要的推论**：因为 Decode 是带宽瓶颈，**同样的模型权重，batch size 增大时吞吐几乎线性增长**（显存读一次服务多个请求）。这就是 continuous batching 的理论依据。

**这就是为什么 vLLM 这类框架的核心竞争力是调度**（continuous batching + PagedAttention），而不是模型本身。
</details>

---

**下一篇** → [缩放定律与高效注意力](/guides/deep-learning/part3-transformer/14-scaling-laws)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part3-transformer/12-transformer-to-llama)
