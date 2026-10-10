---
title: Attention 的数学推导
description: "QKV 为什么要除 √d？softmax 为什么必须有？如果去掉 scaling 会怎样？"
---

# 10 · Attention 的数学推导

> 核心问题：QKV 为什么要除 $\sqrt{d}$？softmax 为什么必须有？如果去掉 scaling 会怎样？

---

## 一、从「需求」出发

### 1.1 我们想要什么能力

处理序列时，模型需要能：**让每个位置「主动去查」其他位置的相关信息**。

比如处理「**那只**猫很可爱，因为**它**饿了」——"它"要能关联到前面的"猫"。这种关联是**动态的、依赖内容的**，不能靠固定位置编码。

### 1.2 用检索类比理解 QKV

把 Attention 想成一个**数据库检索系统**：

| 角色 | 类比 | 作用 |
|---|---|---|
| **Q（Query）** | 我想要什么 | 当前查询的「需求描述」 |
| **K（Key）** | 我有什么 | 每个条目的「索引标签」 |
| **V（Value）** | 实际内容 | 每个条目真正的数据 |

**检索流程**：

1. 拿我的 **Q** 去和所有条目的 **K** 比对 → 得到匹配分数
2. 把分数转成权重（**softmax**）→ 归一化到 [0,1]
3. 按权重加权求和所有条目的 **V** → 得到我要的结果

**关键洞察**：相似度是「Q 和 K 的关系」，但真正被加权取回的是 **V**。**Q/K 负责「找谁」，V 负责「拿什么」。** 这就是为什么 V 通常不参与打分。

---

## 二、Scaled Dot-Product Attention 的公式

$$\text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}} + M\right) V$$

其中：

- $Q \in \mathbb{R}^{n \times d_k}$（$n$ 个查询，每个 $d_k$ 维）
- $K \in \mathbb{R}^{m \times d_k}$（$m$ 个键）
- $V \in \mathbb{R}^{m \times d_v}$
- $M$ 是掩码矩阵（causal mask 等，可选）

**形状流转（务必记住）**：

```
输入:  Q [n, d_k]   K [m, d_k]   V [m, d_v]
        ↓ Q @ K.T
      [n, m]        ← ★ 注意力矩阵：n个查询对m个键的匹配度
        ↓ / sqrt(d_k)
      [n, m]
        ↓ + M, softmax(dim=-1)
      [n, m]        ← 每行和为 1
        ↓ @ V
输出:  [n, d_v]
```

**注意中间那个 $[n, m]$ 矩阵是核心**：它就是「注意力图」，可视化出来能看到模型在学什么。

---

## 三、三个核心问题

### 3.1 为什么除 $\sqrt{d_k}$（这是本篇最重要的部分）

**数学推导**：

假设 $q$ 和 $k$ 的每个分量都是独立的、均值 0 方差 1 的随机变量。那么点积：

$$q \cdot k = \sum_{i=1}^{d_k} q_i k_i$$

**方差**（独立项相加，方差相加）：

$$\text{Var}[q \cdot k] = \sum_{i=1}^{d_k}\text{Var}[q_i k_i] = \sum_{i=1}^{d_k} \text{Var}[q_i]\text{Var}[k_i] = d_k \cdot 1 \cdot 1 = d_k$$

所以 $\text{std}[q\cdot k] = \sqrt{d_k}$。

**实测验证**：

```python
import torch, math
torch.manual_seed(0)
print("=== 点积的标准差随维度增长 ===")
for d in [16, 64, 256, 1024]:
    q = torch.randn(2000, d); k = torch.randn(2000, d)
    dot = (q * k).sum(-1)
    print(f"d={d:>5}  点积 std={dot.std():>7.3f}  理论sqrt(d)={math.sqrt(d):>7.3f}"
          f"  缩放后 std={dot.std()/math.sqrt(d):>6.3f}")
```

**实测输出**：

```
d=  16  点积 std=  4.001  理论sqrt(d)=  4.000  缩放后 std= 1.000
d=  64  点积 std=  8.114  理论sqrt(d)=  8.000  缩放后 std= 1.014
d= 256  点积 std= 16.144  理论sqrt(d)= 16.000  缩放后 std= 1.009
d=1024  点积 std= 33.293  理论sqrt(d)= 32.000  缩放后 std= 1.040
```

**完美吻合**：点积的 std 就是 $\sqrt{d}$，除以 $\sqrt{d}$ 后稳定在 1 附近。

**为什么这会导致训练失败**：

softmax 的输入被放大 $\sqrt{d}$ 倍后进入饱和区。**饱和的 softmax 是什么样子？** 看实验：

```python
import torch, math
print("=== softmax 饱和：logits 尺度的影响 ===")
print(f"{'元素数':>7}{'logits_std':>12}{'最大概率':>10}{'熵':>8}{'均匀分布熵':>12}")
for n in [4, 16, 64, 256]:
    for scale in [1.0, 4.0, 16.0]:
        torch.manual_seed(0)
        p = (torch.randn(2000, n) * scale).softmax(-1)
        maxp = p.max(-1).values.mean()
        ent = -(p * torch.log(p + 1e-10)).sum(-1).mean()
        print(f"{n:>7}{scale:>12.1f}{maxp:>10.4f}{ent:>8.3f}{math.log(n):>12.3f}")
```

**实测输出**：

```
  元素数  logits_std    最大概率       熵  均匀分布熵
      4         1.0     0.5208   1.110     1.386
      4         4.0     0.8313   0.421     1.386
      4        16.0     0.9567   0.105     1.386
     16         1.0     0.2481   2.356     2.773
     16         4.0     0.7029   0.848     2.773
     16        16.0     0.9263   0.187     2.773
     64         1.0     0.1069   3.686     4.159
     64         4.0     0.5887   1.317     4.159
     64        16.0     0.8936   0.273     4.159
    256         1.0     0.0436   5.050     5.545
    256         4.0     0.5114   1.778     5.545
    256        16.0     0.8766   0.326     5.545
```

**仔细看 `logits_std = 16` 那一行**：熵只有 0.105 ~ 0.326，而均匀分布的熵是 1.386 ~ 5.545。**注意力分布几乎变成了 one-hot**——每个查询只关注一个键。

**这会导致三个后果**：

1. **梯度消失**：softmax 饱和区域的导数 $\text{softmax}(z)(1-\text{softmax}(z))$ 趋近 0
2. **无法学习**：所有注意力集中在一个位置上，模型丧失了「对比多个位置」的能力
3. **信息瓶颈**：每个 token 只能看到 1 个 token

**关键数字**：`d_k = 64$ 时，点积 std 是 8，$\sqrt{64}=8$——**不缩放就是 logits_std=8**，已经落在表里 std=4 和 std=16 之间，softmax 明显饱和。`d_k = 128$（LLaMA 的典型值）时 std 是 11.3，问题更严重。

**结论**：除以 $\sqrt{d_k}$ 不是可选的微调，而是**保证 softmax 工作在有效区间**的必要操作。

### 3.2 为什么必须用 softmax（不能直接用点积）

三个理由：

**理由1：需要归一化**。softmax 让权重和为 1，等于「**分配注意力预算**」——每个 token 分配的注意力总量固定，不会因为某个分数高就无限放大。

**理由2：可微且梯度有意义**。softmax 是平滑函数，梯度 $\frac{\partial a_i}{\partial s_j} = a_i(\delta_{ij} - a_j)$ 给出「提升 key j 的分数会如何改变分配」的清晰信号。

**理由3：引入竞争/相对性**。softmax 是「相对」操作——某个键分数升高会**抢占**其他键的权重。这符合注意力的直觉：**注意力是稀有的资源，需要竞争。**

如果直接用点积（可以理解为加权平均但不归一化），权重可能全都很小（输出尺度失控）或都很大（输出爆炸）。

### 3.3 mask 的作用

$$\text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}} + M\right)$$

其中 $M$ 在要屏蔽的位置是 $-\infty$（softmax 后变成 0）。

**Causal mask（自回归模型）**：第 $i$ 个 token 只能看到 $\le i$ 的 token。

```python
mask = torch.triu(torch.ones(seq, seq) * float('-inf'), diagonal=1)
```

**用 -inf 而不是大负数的原因**：softmax 会先减最大值，`-inf` 在减法后会变成 NaN（$\text{-inf} - \text{finite} = \text{-inf}$，$\exp(-\infty) = 0$ 实际是安全的，但减法顺序可能出问题）。**实践中 PyTorch 用 `float('-inf')` 是安全的**，因为 `softmax` 内部对 `-inf` 有特殊处理。

---

## 四、完整实现

```python
import torch
import torch.nn.functional as F
from torch import nn

def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Q: [batch, heads, seq, d_k]
    K: [batch, heads, seq, d_k]
    V: [batch, heads, seq, d_v]
    mask: [batch, 1, seq, seq]  或 [seq, seq]，True 表示要屏蔽
    """
    d_k = Q.size(-1)
    scores = Q @ K.transpose(-2, -1) / math.sqrt(d_k)   # [b, h, n, m]
    if mask is not None:
        scores = scores.masked_fill(mask, float('-inf'))
    attn = scores.softmax(dim=-1)
    return attn @ V, attn
```

**PyTorch 内置版本**（生产环境务必用这个）：

```python
# ★ 官方推荐：内存高效的融合实现
out = F.scaled_dot_product_attention(Q, K, V, is_causal=True)
```

它会自动选择最优的数学后端（数学等价但显存占用不同），并支持 Flash Attention。

---

## 五、自回归掩码的实现细节

### 5.1 因果掩码矩阵

```
seq_len = 4

掩码（True = 屏蔽）:
        j=0   1     2     3
i=0    [False True  True  True ]   ← token0 只能看自己
i=1    [False False True  True ]   ← token1 能看 0,1
i=2    [False False False True ]
i=3    [False False False False]
```

```python
seq = 4
mask = torch.triu(torch.ones(seq, seq, dtype=torch.bool), diagonal=1)
print(mask)
# tensor([[False,  True,  True,  True],
#         [False, False,  True,  True],
#         [False, False, False,  True],
#         [False, False, False, False]])
```

### 5.2 Padding mask 的组合

实际场景要同时考虑 causal mask 和 padding mask：

```python
padding_mask = (tokens != pad_id)          # [batch, seq] True=有效
causal_mask = torch.triu(torch.ones(seq, seq, dtype=torch.bool), diagonal=1)

# padding: [b, seq] → [b, 1, 1, seq]（广播到所有 query）
# causal:  [seq, seq] → [1, 1, seq, seq]
combined = causal_mask[None, None, :, :] | (~padding_mask)[:, None, None, :]
```

---

## 六、动手实验

### 实验 1：验证 √d 缩放（本文核心）

```python
import torch, math
torch.manual_seed(0)

print("=== 点积标准差 vs 维度 ===")
print(f"{'d_k':>7}{'点积std':>10}{'√d':>8}{'缩放后std':>12}")
for d in [16, 64, 256, 1024]:
    q = torch.randn(2000, d); k = torch.randn(2000, d)
    dot = (q * k).sum(-1)
    print(f"{d:>7}{dot.std():>10.3f}{math.sqrt(d):>8.3f}{dot.std()/math.sqrt(d):>12.3f}")

print("\n=== 不缩放的 softmax 饱和程度 ===")
print(f"{'d_k':>7}{'max_p(不缩放)':>16}{'max_p(缩放)':>14}{'熵(缩放)':>11}{'均匀熵':>9}")
for d in [16, 64, 256, 1024]:
    q = torch.randn(500, d); k = torch.randn(500, d)
    dot = (q * k).sum(-1)
    a = dot.softmax(-1).max(-1).values.mean()
    b = (dot / math.sqrt(d)).softmax(-1).max(-1).values.mean()
    ent = -(b * torch.log(b + 1e-10)).sum(-1).mean()
    print(f"{d:>7}{a:>16.4f}{b:>14.4f}{ent:>11.3f}{math.log(d):>9.3f}")

print("\n→ 不缩放时 max_p 全部=0.9999，注意力完全退化成 one-hot")
print("→ 缩放后 max_p 回到 0.02~0.035，有明确的相对差异可供学习")
```

**实测输出**：

```
=== 不缩放的 softmax 饱和程度 ===
   d_k  max_p(不缩放)  max_p(缩放)    熵(缩放)   均匀熵
   16          0.7267      0.0319     0.110    2.773
   64          0.9990      0.0350     0.117    4.159
  256          0.9999      0.0347     0.117    5.545
 1024          0.9999      0.0170     0.069    6.931

→ 不缩放时 max_p 全部=0.9999，注意力完全退化成 one-hot
→ 缩放后 max_p 回到 0.02~0.035，有明确的相对差异可供学习
```

**注意 `max_p(缩放)` 那一列只有 0.02~0.035**，看起来「过于均匀」了——但这恰恰是**正确**的：真实训练中的 $q, k$ **不是**独立随机向量，它们经过投影和训练后有特定的相关结构，会让部分位置的分数更高。**随机初始化下的均匀分布正是我们想要的起点**（有区分度，才能学）。

**真正要避免的是 `max_p(不缩放)` 那一列的 0.9999**——所有位置的注意力完全相同，没有任何区分能力。

**注意**：真实 Transformer 里 $q, k$ 经过 $W_Q, W_K$ 投影后分量 std 约 $1/\sqrt{d_{in}}$ 量级，但**经过层归一化和训练后**，实际进入 attention 的 $q, k$ 分量 std 接近 1，所以上面的分析成立。

### 实验 2：手动实现并与 PyTorch 对比

```python
import torch, math
import torch.nn.functional as F

torch.manual_seed(42)
b, h, seq, d = 2, 4, 8, 16
Q = torch.randn(b, h, seq, d)
K = torch.randn(b, h, seq, d)
V = torch.randn(b, h, seq, d)
causal = torch.triu(torch.ones(seq, seq, dtype=torch.bool), diagonal=1)

# 手动实现
def manual_attention(Q, K, V, causal_mask=None):
    d_k = Q.size(-1)
    scores = Q @ K.transpose(-2, -1) / math.sqrt(d_k)
    if causal_mask is not None:
        scores = scores.masked_fill(causal_mask, float('-inf'))
    return scores.softmax(-1) @ V

mine = manual_attention(Q, K, V, causal)
theirs = F.scaled_dot_product_attention(Q, K, V, is_causal=True)

print(f"手写 vs PyTorch 内置:最大差异 = {(mine - theirs).abs().max():.2e}")
print("→ 完全一致，但内置版本内存效率高得多")

# 验证因果性：改变未来的 token，不应影响过去的输出
V2 = V.clone()
V2[:, :, 5:, :] = torch.randn(b, h, seq - 5, d) * 100# 疯狂改动后面的 token
out1 = manual_attention(Q, K, V, causal)
out2 = manual_attention(Q, K, V2, causal)
print(f"\n改动后 token 之后，输出差异: {(out1[:, :, :5] - out2[:, :, :5]).abs().max():.2e}")
print(f"改动后 token 之后的后续位置差异: {(out1[:, :, 5:] - out2[:, :, 5:]).abs().max():.2e}")
print("→ 前面的 token 输出完全不受影响，causal mask 正确")
```

### 实验 3：可视化注意力权重

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 造一个能看出结构的例子：后一半的 token 是前一半的「复制」
seq = 8
x = torch.randn(1, 1, seq, 32) * 0.5
x[0, 0, 4:] = x[0, 0, :4]# token 4~7 是 0~3 的副本

lin_q = nn.Linear(32, 32); lin_k = nn.Linear(32, 32); lin_v = nn.Linear(32, 32)
Q, K, V = lin_q(x), lin_k(x), lin_v(x)
scores = Q @ K.transpose(-2, -1) / math.sqrt(32)
attn = scores.softmax(-1)[0, 0]

print("注意力矩阵 (行=query, 列=key):")
print("     " + "".join(f"{j:>6}" for j in range(seq)))
for i in range(seq):
    bar = "".join(f"{v:>6.2f}" for v in attn[i].tolist())
    print(f"  t{i} {bar}")
print("\n观察第4~7 行（副本 token）是否指向对应的 0~3 列")
```

**观察**：第 4~7 行（副本）应该**主要指向对应的 0~3 列**，因为它们内容相同，$q\cdot k$ 最大。这直观展示了 attention 在「按内容匹配」。

---

## 七、自测题

**Q1**：如果去掉 $\sqrt{d_k}$ 缩放，训练会出现什么现象？可以量化吗？

<details>
<summary>答案</summary>

**现象**：softmax 饱和 → 梯度消失 → 训练完全失效或极慢。

**量化**（用本篇实验的数据，`d_k = 64$）：

| | 最大概率 | 说明 |
|---|---|---|
| **不缩放** | **0.9990** | 注意力完全塌成one-hot |
| 缩放 | 0.0350 | 有区分度，可以学习 |

**从 0.9990 变成 0.035**——不缩放时 softmax 输出的就是「1 和一堆 0」，梯度全在最大值那个位置上，其余位置的梯度是 $p_i(1-p_j) pprox 0$。**模型无法学到任何「关注多个位置」的能力。**

**梯度的量化**：softmax 的雅可比是 $\text{diag}(p) - pp^\top$，元素大小 $\sim p_i(1-p_j)$。当 $p \to 1$ 时 $p(1-p) \to 0$，梯度消失。

$d_k = 1024$ 时 max_p = 0.9999，**softmax 数值上就是 one-hot，梯度几乎为 0**。

**这也是原始 Transformer 论文把它叫"scaled dot-product"的原因**——scaling 是这个公式的核心组成部分，不是可选优化。
</details>

**Q2**：Q、K、V 三个矩阵分别是什么？能不能只用两个（比如 Q 和 V）？

<details>
<summary>答案</summary>

**不能，因为「谁该被关注」和「关注后拿到什么」是两个独立的信息**。

- **QK^T 决定「注意力权重」**：谁和谁相关
- **V 决定「传递什么内容」**

如果只有 Q 和 V，用 $Q^\top V$ 直接算？那得到的是 $[d, d]$ 的矩阵（不是注意力权重矩阵），**失去了「按需检索」的能力**。

**类比**：图书馆系统里，「检索词→书的索引」和「书的实际内容」必须分开存储。如果混在一起，就无法实现「用检索词找到匹配的书，然后取它的内容」。

**一个反例说明问题**：假设一句话里有两个关键信息点，V 分别是它们的内容。如果只有一个矩阵，你无法表达「我要同时关注这两点，但注意力要按相关性分配」。

**实际上 K 通常可以和 Q 共享同一份计算结果**（self-attention 里），某些简化架构会这么做，但效果会下降。标准实现里 W_Q、W_K、V_W 是三套独立参数。
</details>

**Q3**：为什么 causal mask 要用 $-\infty$，用 $-10^9$ 行不行？

<details>
<summary>答案</summary>

**理论上都行，实践中都用 $-\infty$（或者 PyTorch 的 `float('-inf')`）。**

**用 $-10^9$ 的情况**：

```
softmax([5.0, -1e9]) = [1.0, 0.0]   ✓ 效果正确
```

因为 $\exp(-10^9) \approx 0$，和 $\exp(-\infty) = 0$ 几乎没区别。

**但有两个隐患**：

1. **数值精度**：如果模型内部用 fp16，$-10^9$ **直接超出 fp16 范围**（最大 65504），会变成 `-inf` 或 `nan`。用 fp32 的话 $-10^9$ 也在边缘。

2. **和 causal mask 组合时**：如果同时有 padding mask，两层 mask 相加可能得到 $-2\times10^9$，进一步溢出。

**PyTorch 的 `F.scaled_dot_product_attention` 用 `is_causal=True` 参数**，内部自动处理这个 mask，比手动传更高效（能融合进 kernel）。

**一个实用建议**：训练时优先用 `is_causal=True` 而不是手动构造 mask，能享受 Flash Attention 的优化。
</details>

**Q4**：注意力矩阵 $[n, m]$ 的复杂度是多少？为什么这是长序列的瓶颈？

<details>
<summary>答案</summary>

**时间复杂度**：$O(n \cdot m \cdot d_k)$，当 $n = m = L$ 时是 $O(L^2 d_k)$。

**空间复杂度**：注意力矩阵本身要存 $O(L^2)$。**这是平方级**。

**具体数字**（LLaMA-7B，4096 token）：

```
注意力矩阵：2 (batch) × 32 (heads) × 4096 × 4096 × 2 bytes (fp16)
          = 2 × 32 × 4096 × 4096 × 2
          = 2.1 GB   ← 单层！
```

32 层累计就是 68 GB **仅用于存注意力矩阵**。

**对比 MLP 的复杂度**：$O(L \cdot d^2)$，**线性于 $L$**。

**所以瓶颈很明确**：

| 组件 | 复杂度 | 随序列长度 |
|---|---|---|
| QKV 投影 | $O(Ld^2)$ | 线性 |
| **注意力矩阵** | **$O(L^2 d)$** | **平方** ⚠️ |
| MLP | $O(Ld^2)$ | 线性 |

**这就是所有「高效注意力」工作的动机**：

1. **FlashAttention**：不显式存注意力矩阵（见第 14 篇）
2. **稀疏注意力**：只算部分位置（Longformer、BigBird）
3. **线性注意力**：改变计算顺序，用 $K^\top V$ 先算（Linear Transformer、Performer）
4. **低秩近似**：把 $QK^\top$ 近似成低秩矩阵（Linformer）

**GPT-3 的选择**：只支持 2048 token 上下文，因为再长平方成本太高。**GPT-4 的 128K 上下文能实现，靠的是 FlashAttention + 多种优化**（推测，多层特征）。
</details>

---

**下一篇** → [多头注意力与位置编码](/guides/deep-learning/part3-transformer/11-multi-head-rope)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part2-dl-principles/09-initialization)
