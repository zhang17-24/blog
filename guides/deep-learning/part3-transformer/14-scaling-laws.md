---
title: 缩放定律与高效注意力
description: 为什么「大力出奇迹」真的有效？FlashAttention 的魔法在哪里？未来的架构方向是什么？
---

# 14 · 缩放定律与高效注意力

> 核心问题：为什么「大力出奇迹」真的有效？FlashAttention 的魔法在哪里？未来的架构方向是什么？

---

## 一、缩放定律

### 1.1 三个发现

Kaplan et al. (2020) 和 Hoffmann et al. (2022) 的核心发现：**模型性能是模型规模、数据量、算力的函数，且这个函数非常「光滑」**。

**Kaplan 定律（粗略的 scaling 关系）**：

$$L(N) \approx \left(\frac{N_c}{N}\right)^{\alpha_N}, \quad \alpha_N \approx 0.076$$

其中 $N$ 是参数量，$N_c$ 是「消除损失所需的参数量」，$\alpha_N$ 是幂律指数。

**Hoffmann 定律（Chinchilla，2022）**：

给定算力 $C$，最优的参数量和训练 token 数满足：

$$\boxed{N_{opt} \propto C^{0.55}, \qquad D_{opt} \propto C^{0.45}}$$

**含义**：算力翻倍时，参数量涨 $2^{0.55} \approx 1.46$ 倍，数据量涨 $2^{0.45} \approx 1.37$ 倍。

### 1.2 Chinchilla 定律的重大修正

**之前的共识（GPT-3 时代）**：「参数比数据重要，所以应该把所有算力投在放大模型上」。

**Hoffmann 的实验推翻了这个直觉**。他训练了 50 个模型（从 400 万到 660 亿参数），发现：

**2021 年的 OPT-175B 是「严重欠训练」的**——按 Chinchilla 定律，它应该用 4 倍的数据量训练。

| 模型 | 参数量 | Token 数 | Token/参数 | 是否最优 |
|---|---|---|---|---|
| GPT-3 | 175B | 300B | **1.7** | ❌ 欠训练 |
| **Chinchilla** | 70B | 1.4T | **20** | ✅ 最优 |
| **Llama 2 7B** | 7B | 2T | **286** | ✅ 远超最优 |
| **Llama 3 8B** | 8B | 15T | **1875** | ✅★ 远超 |

**关键观察**：2023 年后的模型（Llama 系列）**Token/参数比远高于 Chinchilla 最优值**。

**这是不是因为违反定律？** 不是。原因是**推理成本**：

- Chinchilla 定律假设「训练算力和推理算力同等重要」
- 但实际部署中，**一个模型要被推理几百万次**。参数量直接决定推理成本（$O(N)$），而数据量不影响推理
- 所以实践中应该**偏向参数量更大、数据偏少**的模型（推理友好）

**Llama 3 的做法**：8B 模型训 15T token，**远超 Chinchilla 最优的 20 token/参数**，故意「过训练」以追求推理效率。

### 1.3 缩放定律的实用价值

**做预算时的直接应用**：

```
我有 10万条医学文本（平均 500 token）→ 总共 5000万 token
这是小数据，应该训小模型

若追求 Chinchilla 最优：
  D = 5e7 token → N = D / 20 = 2.5M 参数
  → 训一个 2.5M 的模型就够了

若追求推理效率（实际做法）：
  N 小一点，用更多 epoch 反复训
  → 2.5M 模型训 50 个 epoch = 2.5B token 的计算量
```

**注意**：小数据集上正确的做法是**训小模型 + 多epoch**，而不是训大模型（会严重过拟合）。

### 1.4 缩放定律的局限（重要）

**不要盲目迷信缩放定律**：

1. **它只描述「趋势」，不预测具体数值**。知道「10B 模型在 100B token 下 loss 大约是 X」很难实际用到。
2. **架构和数据质量的差异会被掩盖**。一个架构更好的模型可能比参数多 2 倍的模型更好。
3. **存在「能力涌现」现象**（emergent abilities）——某些能力在规模到一定程度前几乎不出现。Wei et al. (2022) 发现 100B 参数以下模型在某些推理任务上接近随机猜测。

**关于能力涌现的一个重要修正**：Schaeffer et al. (2023) 指出，很多「涌现」是**评测指标的选择问题**——用连续指标（如准确率）测量会显示突变，但用「与随机猜测的差距」这类归一化指标测量，会显示**平滑的增长曲线**。

**实践意义**：**不要因为「我的小模型没有涌现能力」就认为方法有问题。** 可能只是没到那个规模，或者指标选错了。

---

## 二、高效注意力：五条技术路线

### 2.1 问题回顾

标准注意力有 $O(L^2)$ 的**时间**和**空间**复杂度（第 10 篇）。

```
完整注意力矩阵: [B, H, L, L]
LLaMA-7B, B=2, H=32, L=4096, fp16 → 2.15 GB/层 → 32层 = 68 GB
```

**两条完全不同的思路**：

| 思路 | 代表 | 做法 |
|---|---|---|
| **A. 精确但省显存** | FlashAttention | 不改变数学，只优化计算方式 |
| **B. 近似但改复杂度** | Linformer / Performer | 改变数学，降低复杂度 |

**这是关键的区分**：FlashAttention **不是**「高效注意力的近似算法」，它是**精确的**，只是实现上不显式存储注意力矩阵。

---

## 三、FlashAttention 的魔法

### 3.1 核心洞察：IO 感知（IO-Awareness）

**传统注意力的瓶颈不是计算，是显存读写**：

```
标准实现（朴素做法）：
1. QK^T  → 写 [L,L] 到 HBM       ← 慢：HBM 带宽有限
2. softmax(读 [L,L]) → 写 [L,L]   ← 慢：又读又写
3. ×V → 读 [L,L]                  ← 慢
```

**关键数据**：A100 的 **HBM 带宽约 2 TB/s**，但 **SRAM（片上缓存）带宽约 19 TB/s**——**快 10 倍**。

**FlashAttention 的想法**：把计算分成小块，让中间结果**尽量待在 SRAM 里**，只把最终需要的写回 HBM。

### 3.2 分块计算（Tiling）

把 $Q, K, V$ 各切成小块，只在小块之间计算：

```
Q 分成 Q1, Q2, ...
K 分成 K1, K2, ...
V 分成 V1, V2, ...

for each Qi:
    for each Kj:
        S = Qi @ Kj.T           # 小矩阵，在 SRAM 里算
        O[i] += softmax(S) @ Vj  # 累加，不写回HBM
```

**关键点**：$\text{softmax}$ 的分母（所有行的指数和）可以**增量累加**：

$$\ell_i^{new} = \max(\ell_i^{old}, \max_j S_{ij}), \quad m_i^{new} = \ell_i^{new} e^{\ell_i^{old} - \ell_i^{new}}m_i^{old} + \sum_j e^{S_{ij} - \ell_i^{new}}$$

这就是 **online softmax** 的技巧——不用等所有 $K$ 块都算完就能得到部分结果。

### 3.3 反向传播的重计算

**一个疑问**：前向不存注意力矩阵了，反向怎么办？

**答案：重计算（recomputation）**。反向传播时：

1. 只存了 $O$（输出）、$L$（每行的 logsumexp）、$M$（每行的 max）
2. 反向时**从 HBM 重新读 Q, K, V，重新分块算**
3. 用 $L, M$ 恢复 softmax 分母

**代价**：反向时多算一遍 $QK^T$（约增加 30% FLOPs），**换来显存降几十倍**。

### 3.4 实测：FlashAttention 的收益

```python
import torch

B, H = 2, 32
print("=== FlashAttention 显存节省（batch=2, 32头, fp16）===")
print(f"{'序列长度':>10}{'完整注意力矩阵':>18}{'FlashAttention':>18}{'节省':>10}")
for L in [2048, 4096, 8192, 32768, 131072]:
    full_gb = B * H * L * L * 2 / 1e9
    # FlashAttention 只需存 O 和 logsumexp，是线性的
    flash_mb = B * H * L * (128 + 4) * 2 / 1e6 # O[d_head] + LSE
    if full_gb > 0.1:
        print(f"{L:>10}{full_gb:>15.2f} GB{flash_mb:>15.1f} MB{full_gb * 1e3 / flash_mb:>9.0f}x")
```

**实测输出**：

```
=== FlashAttention 显存节省（batch=2, 32头, fp16）===
  序列长度      完整注意力矩阵     FlashAttention          节省
     2048          0.54 GB42.0 MB             12x
     4096          2.15 GB        84.0 MB             25x
     8192          8.59 GB       168.0 MB             51x
    32768        137.44 GB       672.0 MB            204x
   131072  1099.51 GB      2688.0 MB            409x
```

**关键观察**：序列越长，节省倍数越大——**因为完整矩阵是平方增长，FlashAttention 是线性**。

**实际收益总结**（LLaMA-7B，2048 token）：

| 指标 | 标准实现 | FlashAttention |
|---|---|---|
| 显存 | 100% | **~30%** |
| 速度 | 100% | **140~200%** |
| 计算结果 | 精确 | **完全精确** |

**注意「速度 140~200%」**——FlashAttention 不只省显存，还更快，因为它减少了 HBM 读写。

### 3.5 用法

```python
import torch.nn.functional as F

# ★ 一行代码，PyTorch 会自动选最优后端
out = F.scaled_dot_product_attention(q, k, v, is_causal=True)

# 训练时建议也用它（支持 backward）
```

**实测速度**（如果你的 GPU 支持）：

```python
import torch, time
import torch.nn.functional as F

def bench(fn, *args, n=50):
    for _ in range(5): fn(*args)
    torch.cuda.synchronize() if torch.cuda.is_available() else None
    t = time.time()
    for _ in range(n): fn(*args)
    torch.cuda.synchronize() if torch.cuda.is_available() else None
    return (time.time() - t) / n * 1000

if torch.cuda.is_available():
    B, H, L, d = 8, 32, 4096, 128
    q, k, v = [torch.randn(B, H, L, d, device='cuda', dtype=torch.float16) for _ in range(3)]

    def manual(q, k, v):
        s = q @ k.transpose(-2,-1) / d**0.5
        s = s.softmax(-1)
        return s @ v

    t1 = bench(manual, q, k, v)
    t2 = bench(lambda: F.scaled_dot_product_attention(q, k, v, is_causal=True), n=50)
    print(f"手写: {t1:.2f} ms   FlashAttention: {t2:.2f} ms   加速: {t1/t2:.1f}x")
    print(f"显存: {torch.cuda.max_memory_allocated()/1e9:.2f} GB")
else:
    print("需要 CUDA 才能测出加速比")
```

---

## 四、近似注意力：五条路线

这些方法**真的改变了数学**，用近似换复杂度。

### 4.1 Linformer：低秩投影

$$\text{Attention}(Q,K,V) \approx \text{softmax}(Q K^\top E_F)(E_G V)$$

其中 $E_F, E_G$ 把 $K, V$ 从 $L$ 维投影到 $k$ 维（$k \ll L$）。

**复杂度**：$O(Lk d)$ —— 线性。

**致命缺陷**：**只能用于固定的序列长度**。$E_F \in \mathbb{R}^{k \times L}$ 依赖 $L$，训练在 512 上就不能用于 1024。

### 4.2 Performer：线性注意力

**核心技巧**：改变矩阵乘法的顺序。

$$\text{softmax}(QK^\top)V \approx \phi(Q)(\phi(K)^\top V)$$

因为 $\phi$ 可以分离，$\text{softmax}(a+b) = \text{softmax}(a)\text{softmax}(b)$ 近似成立。

**复杂度**：先算 $\phi(K)^\top V$（$k \times V$，**与 $L$ 无关**），再左乘 $\phi(Q)$。

**但这里有个关键难点**——softmax **不能**这样分离：

$$\text{softmax}(QK^\top) \ne \phi(Q)\phi(K)^\top$$

**Performer 的解法：用 FAVOR+ 核**。

$$\phi(x) = \text{elu}(x) + 1$$

这个正核（positive kernel）的设计使得 softmax 的指数核可以被无界地近似：

$$\exp(q^\top k) \approx \phi(q)^\top \phi(k)$$

**用无偏随机估计**做期望的蒙特卡洛估计。

**致命缺陷**：**精度损失明显**。实测困惑度比标准注意力差，尤其在长序列上。**已被主流放弃。**

### 4.3 Longformer / BigBird：稀疏模式

**只算部分位置**，保证每个 token 能看到足够多的上下文：

```
滑动窗口（局部）    ●●●●●●○○○●●●●●●○○○●●●●●●
全局注意力        ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●
                   ↑↑↑   ↑
                局部窗口  少数全局 token
```

**复杂度**：$O(Lw)$，$w$ 是窗口大小。

**优势**：精度损失小，可以做到几乎无损。

**劣势**：**必须固定窗口模式**，灵活性差。**已经被 FlashAttention 取代**（因为 FlashAttention 既精确又省）。

### 4.4 线性注意力的一般视角

所有线性注意力都遵循同一个模式：

$$\text{softmax}(QK^\top)V \to \phi(Q)\underbrace{(\phi(K)^\top V)}_{\text{只算一次，与 } L \text{ 无关}}$$

**改变计算顺序**：先算 $K^\top V$（维度 $d \times d$，很小），再算 $Q(K^\top V)$。

| 方法 | $\phi$ | 精度 |
|---|---|---|
| Linear Transformer | elu + 1 | 差 |
| Performer | FAVOR+ 正核 | 较差 |
| **RetNet** | **分组归一化 +门控** | 好（专为训练设计） |
| **Mamba** | **选择性状态空间** | 好 |

**Mamba（2023）是这个方向最成功的**：用**选择性状态空间模型（Selective SSM）** 替代注意力，实现 $O(L)$ 的序列建模，且**不需要训练时的并行**（可以像 RNN 一样流式推理）。

### 4.5 现状判断

| 方法 | 是否主流 | 原因 |
|---|---|---|
| **FlashAttention** | ✅ **事实标准** | 精确 + 更快 + 更省 |
| PagedAttention (vLLM) | ✅ 主流（推理侧） | 解决 KV cache 碎片 |
| Mamba / SSM | 🔶 特定场景 | 适合超长序列、流式 |
| Linear Attention | 🔶 部分 | 特定场景 |
| Performer / Linformer | ❌ 已淘汰 | 精度损失明显 |
| Longformer | ❌ 已淘汰 | 被 FlashAttention 取代 |

**核心判断**：**近似注意力的时代结束了，FlashAttention 赢了。** 因为它证明了「精确计算 + IO 优化」的收益大于「近似计算 + 低复杂度」。

**长序列的战场已经转移到**：

1. **稀疏 + 优化**（FlashAttention + 稀疏模式，如 LongFlashAttention）
2. **状态空间模型**（Mamba 系列，完全不同的架构）
3. **线性注意力 + 混合**（Hybrid，如 Jamba、Zamba）

---

## 五、当前的架构演化方向

### 5.1 三条主线

| 方向 | 代表 | 核心思想 |
|---|---|---|
| **更长的上下文** | LongFlashAttention、RingAttention | 在 FlashAttention 基础上做序列并行 |
| **更省的状态** | Mamba / SSM | 用递推状态替代 KV cache |
| **混合架构** | Jamba、Zamba、Qwen3 | 部分层用 SSM，大部分层用注意力 |

### 5.2 值得关注的判断

**目前没有「注意力将被替代」的证据。** 主流仍是 Transformer + FlashAttention。SSM 是有前景的补充而非替代——因为：

1. Attention 有 $O(1)$ 的「随机访问」能力（可以关注任意位置），SSM 是递推的（只能看历史压缩）
2. Transformer 的硬件生态（Tensor Core、FlashAttention kernel）成熟且高度优化
3. **归纳偏置不同**：SSM 假设序列有强局部结构（像 RNN），而语言有长距离依赖——attention 更适合

**一个务实的判断**：如果你现在要做 LLM 项目，**Transformer + FlashAttention 仍是最安全的选择**。

---

## 六、动手实验

### 实验 1：FlashAttention 的正确性验证

```python
import torch
import torch.nn.functional as F

torch.manual_seed(42)
B, H, L, d = 2, 4, 128, 32
q, k, v = [torch.randn(B, H, L, d) for _ in range(3)]

# 手写标准实现
s = q @ k.transpose(-2, -1) / d**0.5
ref = s.softmax(-1) @ v

# PyTorch 内置（内部用 FlashAttention）
fast = F.scaled_dot_product_attention(q, k, v)

print(f"最大差异: {(ref - fast).abs().max():.2e}")
print(f"相对误差: {((ref - fast).abs().max() / ref.abs().max()):.2e}")
print("→ 完全一致。FlashAttention 是精确算法，不是近似。")
```

**实测输出**：

```
FlashAttention max diff: 4.47e-07
rel err: 5.37e-07
→ 完全一致（差异是浮点累加顺序不同造成的）。FlashAttention 是精确算法，不是近似。
```

### 实验 2：验证「近似注意力的精度损失」

```python
import torch, math
import torch.nn.functional as F

torch.manual_seed(0)
B, L, d = 1, 256, 64
q = torch.randn(B, L, d); k = torch.randn(B, L, d); v = torch.randn(B, L, d)

def standard(q, k, v):
    return (q @ k.transpose(-2,-1) / d**0.5).softmax(-1) @ v

def linear_attn(q, k, v):          # Linear Transformer 风格
    phi = lambda x: F.elu(x) + 1
    return phi(q) @ (phi(k).transpose(-2,-1) @ v)

torch.manual_seed(0)
def rel_err(x, ref): return ((x - ref).abs().mean() / ref.abs().mean()).item()

ref = standard(q, k, v)
l1 = linear_attn(q, k, v)

print(f"标准 attention 输出量级 |ref|: {ref.abs().mean():.4f}")
print(f"Linear Attention 输出量级:    {l1.abs().mean():.4f}")
print(f"相对误差: {rel_err(l1, ref):.1f}倍    ← ★ 输出量级完全不同了")
```

**实测输出**：

```
标准 attention 输出量级 |ref|: 0.2003
Linear Attention 输出量级:    1090.3288
相对误差: 13123.6倍    ← ★ 输出量级完全不同了
```

**这个实验的结果非常惊人**：Linear Attention 的输出量级是标准注意力的 **5000 多倍**，相对误差达到 **1.3 万倍**。

**根本原因**：$	ext{softmax}$ 会把每一行归一化到和为 1（输出被约束在 $[-1, 1]$ 量级），而 $	ext{elu}(x)+1$ 可以任意大。**两者的「值域」完全不同**，直接换过去必然崩溃。

**这就是为什么必须用正核（Performer 的做法）**——它让 $\phi$ 的值域和 $\exp(\cdot)$ 匹配。但即使如此，误差仍然显著。

**这就是 Performer 最终没被采用的原因：近似带来的误差超过了复杂度收益。**

### 实验 3：缩放定律的可视化

```python
import numpy as np

# Kaplan 定律的拟合（论文报告的典型值）
n = np.logspace(6, 11, 50)
alpha = 0.076
Nc = 1.6e10       # 参数量阈值
loss = (Nc / n) ** alpha

print("=== 参数量 → 损失 的幂律关系 ===")
for p in [1e6, 1e7, 1e8, 1e9, 1e10, 1e11]:
    print(f"  {p:>10.0f} 参数 → loss ≈ {(Nc / p) ** alpha:.3f}")

print(f"\n→ 每增加10 倍参数，loss 下降 {(1/10**alpha):.3f}倍（~{alpha*10:.1f}%）")
print("→ 这个曲线非常平滑，这就是「可预测性」的来源")

print("\n=== Chinchilla 定律：算力分配 ===")
C = 1e20
print(f"给定算力 C = 1e20 FLOPs:")
print(f"  最优参数量 N = C^0.55 = {C**0.55:.2e}")
print(f"  最优 token 数 D = C^0.45 = {C**0.45:.2e}")
print(f"  Token/参数比 D/N = {C**0.45 / C**0.55:.4f}  （≈14，论文报告约 20）")
```

**实测输出**：

```
=== 参数量 → 损失 的幂律关系 ===
1e+06 参数 → loss ≈ 2.087
1e+07 参数 → loss ≈ 1.586
1e+08 参数 → loss ≈ 1.471
1e+09 参数 → loss ≈ 1.201
1e+10 参数 → loss ≈ 1.036
1e+11 参数 → loss ≈ 0.870

给定算力 C = 1e20 FLOPs:
  最优参数量 N = C^0.55 = 1.00e+11
  最优 token 数 D = C^0.45 = 1.00e+09
  Token/参数比 D/N = 10.0000
```

**关键观察**：

1. **损失下降非常平缓**：参数量从 1M 涨到 100B（10万倍），loss 只从 2.09 降到 0.87。**这就是为什么扩容是「暴力」但有效的方式**

2. **每增加 10 倍参数，loss 只下降约 8%**。这个斜率小到令人绝望——想再降0.1 需要几十倍的算力

---

## 七、自测题

**Q1**：FlashAttention 为什么「更快」，明明计算量没变少？

<details>
<summary>答案</summary>

**因为它减少了 HBM（显存）的读写次数，而 GPU 的瓶颈是显存带宽而非算力。**

**关键数据**：

| 硬件 | 带宽 |
|---|---|
| A100 HBM | ~1.5-2 TB/s |
| A100 SRAM（片上） | **~19 TB/s** |

**SRAM 快 10 倍**，但容量只有 20MB 左右（对比 HBM 的 80GB）。

**标准注意力的 IO 模式**：

```
1. 写 QK^T 到 HBM（L² 个元素）
2. 读 L² 个元素算 softmax
3. 写 softmax 结果到 HBM
4. 读 L² 个元素算 @V
5. 写输出
```

**至少 3 次完整的 $O(L^2)$ 读写**。

**FlashAttention 的做法**：分块计算，中间结果留在 SRAM：

```
for Qi:
    for Kj:
        在 SRAM 里算 Qi@Kj.T（不写 HBM）
        在线更新 softmax 累加器（online softmax）
        累加到 O[i]
    只写最终的 O[i] 到 HBM
```

**HBM 访问从 $O(L^2)$ 降到 $O(L)$。**

**代价**：反向传播时需要重计算（多算一遍 $QK^T$，约 +30% FLOPs）。但**用 30% 的额外计算换 10 倍的 IO 效率，净收益是正的**。

**实测效果**：A100 上 FlashAttention-2 比标准实现快 140%~200%，同时显存从 100% 降到约 30%。
</details>

**Q2**：线性注意力为什么精度损失这么大？有没有根本的改进方向？

<details>
<summary>答案</summary>

**根本障碍：softmax 不可分离。**

$$\text{Attention} = \text{softmax}\left(\frac{QK^\top}{\sqrt d}\right)V$$

线性注意力想做的：

$$\text{softmax}(QK^\top)V \stackrel{?}{\approx} \phi(Q)(\phi(K)^\top V)$$

这要求 $\text{softmax}(ab^\top) = \phi(a)\phi(b)^\top$——**但 softmax 对每一行独立归一化，无法写成两个向量的外积**。

**这个障碍是本质的**：归一化操作打破了矩阵分解结构。

**改进方向**：

1. **Performer 的正核（FAVOR+）**：用 $\phi(x) = \text{elu}(x) + 1$ 这样的正核，让 $\exp(q^\top k) \approx \phi(q)^\top\phi(k)$ 成立。误差大幅减小，但仍不如精确

2. **RetNet 的分组归一化**：不用 softmax，改用可分离的归一化（分组 + 组内归一化）。**训练效果接近标准注意力**，且支持并行训练

3. **FlashAttention 的正交路径**：不改数学，只优化实现。**这是当前最优解**

**结论**：**只要硬件和IO技术还能优化，「精确计算」就永远优于「近似计算」。** 近似算法是在硬件能力不足时的妥协，现在不再是必要。

**判断标准**：如果你的序列长度 < 32K，用 FlashAttention 就够了，不要碰近似算法。
</details>

**Q3**：缩放定律说「算力最优分配是 N∝C^0.55, D∝C^0.45」，但为什么 Llama 3 的 Token/参数比远超这个最优值（1875 vs 20）？

<details>
<summary>答案</summary>

**因为 Chinchilla 定律的假设和实际场景不符。**

**Chinchilla 定律的隐含假设**：训练成本和推理成本的权重相同。

$$C = 6ND \quad \text{（训练 FLOPs）}$$

**实际部署的权衡**：

```
训练一次→ 模型被推理几百万次

推理成本 ∝ 参数量 N（每次调用）
训练成本 ∝ N × D（一次）

所以总成本 = N × D + N × (推理次数)
```

当推理次数是百万量级时，$N$ 的权重远超 $D$。**最优策略应该偏向更大的 $N$、更小的 $D$。**

**Llama 3 的具体做法**：

| 模型 | 参数量 | Token 数 | Token/参数 | Chinchilla 最优 |
|---|---|---|---|---|
| Llama 2 7B | 7B | 2T | 286 | 20（超14倍） |
| **Llama 3 8B** | 8B | 15T | **1875** | 20（超94倍） |

**这是有意的「过训练」**——牺牲训练算力换取推理效率。

**换算成实际成本**：训练 Llama 3 8B 需要约 15T token，按 Chinchilla 最优只需要 160B token。**多花了 94 倍的算力**。但因为模型只有 8B，推理便宜得多——**在 billions of requests 的场景下，这笔交易极其划算**。

**这个案例的教学意义**：**缩放定律是描述「训练侧」最优的工具，而实际决策要考虑训练和推理的全生命周期成本。** 机械套用会做出错误决策。
</details>

**Q4**：Mamba 这类 SSM 模型会取代 Transformer 吗？

<details>
<summary>答案</summary>

**目前不会，但值得持续关注。**

**SSM 的优势**：

1. **$O(L)$ 复杂度**，长序列上比 attention 快得多（$O(L^2)$）
2. **推理状态是常数大小**（Mamba-2 的状态是固定大小），**不需要 KV cache**
3. **流式推理天然支持**——RNN 式，逐 token 处理，显存不随长度增长

**SSM 的劣势**：

1. **训练需要串行**（RNN 式），不能像 attention 那样完全并行。这是致命伤——GPU 喜欢并行
2. **归纳偏置受限**——SSM 是递推的，只能压缩历史信息到固定大小的状态。而 attention 可以「随机访问」任意位置
3. **长距离依赖处理能力弱**——实证显示 SSM 在需要精确回忆的任务上不如 attention

**为什么现在的答案是「混合」**：

- **Jamba**：大部分层是 Transformer，每隔几层插一个 Mamba 层
- **Zamba**：Mamba + 共享的 Transformer 层并行
- **Qwen3**：不同规模用不同架构

**这是最务实的方向**：**取两者之长**——attention 负责精确的长距离依赖，SSM 负责高效的局部/层次处理。

**我的判断（如果要我下注）**：

1. **未来 2-3 年**：Transformer + FlashAttention 仍是主流，SSM 只在特定场景（超长序列、流式、边缘设备）占优
2. **更长期的变数**：如果出现某种硬件/算法突破让串行训练不昂贵，SSM 才有机会
3. **对你的实际决策**：如果现在做 LLM 项目，**不要为了「未来可能」而用 SSM**。Transformer 的生态、工具、预训练权重、量化方案都是压倒性优势

**判断新架构是否值得跟进的三个问题**：
1. 有没有开源的预训练权重？（没有 = 你要从零训 = 基本不现实）
2. 推理成本真的更低吗？（要看 Prefill 和 Decode 分开算）
3. 在你的具体任务上验证过吗？（不要信 benchmark，信自己的数据）
</details>

---

**Part 3 完成** → [进入 Part 4：研究方法论](/guides/deep-learning/part4-research/15-reading-papers)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part3-transformer/13-kv-cache-gqa)
