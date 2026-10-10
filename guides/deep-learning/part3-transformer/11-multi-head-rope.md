---
title: 多头注意力与位置编码
description: 多头到底在多做什么？位置信息怎么注入？RoPE 的旋转技巧是什么？
---

# 11 · 多头注意力与位置编码

> 核心问题：多头到底在多做什么？位置信息怎么注入？RoPE 的旋转技巧是什么？

---

## 一、多头注意力：为什么要「多头」

### 1.1 单头的限制

单个注意力头只能算出一个 $[n, n]$ 的注意力矩阵。**这意味着每个 token 只能有一个「关注模式」**。

**问题**：语言里的关联是多模态的。同一句话里可能同时需要：

- **语法关联**：「猫」↔「的」（结构）
- **语义关联**：「猫」↔「动物」（指代）
- **语用关联**：这个 token 在整体语境中的角色

一个头做不到兼顾。

### 1.2 多头的做法

**把 $d_{model}$ 拆成 $h$ 份，每份独立做注意力，最后拼接。**

$$\text{MultiHead}(Q,K,V) = \text{Concat}(\text{head}_1,\dots,\text{head}_h)W^O$$

$$\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

**形状推导**（务必掌握）：

```
输入 X: [batch, seq, d_model]
   ↓ W_Q: [d_model, d_model]
Q = X W_Q

★ 关键：reshape成多头（不改变总维度，只是分组）
   原始: [batch, seq, d_model]
   变换: [batch, seq, h, d_k] → transpose → [batch, h, seq, d_k]
   其中 d_model = h × d_k

   ↓ 每个头独立做 attention
   [batch, h, seq, d_k] × [batch, h, d_k, seq] → [batch, h, seq, seq]
   → softmax → 加权 V → [batch, h, seq, d_k]

   ↓ transpose + reshape 还原
   [batch, h, seq, d_k] → [batch, seq, h, d_k] → [batch, seq, d_model]

   ↓ W_O: [d_model, d_model]
输出: [batch, seq, d_model]
```

**注意一个容易误解的点**：多头**不是**把 $d_{model}$ 分成 $h$ 份各自独立算完就不管了，而是**每个头有自己独立的 $W_Q, W_K, W_V$**，参数完全不共享。最后还要过一个 $W^O$ 做融合。

**参数量**：

| 项目 | 参数量 |
|---|---|
| $W_Q, W_K, W_V$ | $3 \times d_{model} \times d_{model}$ |
| $W^O$ | $d_{model} \times d_{model}$ |
| **总计** | $4 d_{model}^2$ |

**和单头完全一样！** 多头不增加参数量，只是改变了计算的方式（把一个大矩阵乘法拆成 $h$ 个小的）。**这是「结构先验」而非「容量增加」的典型例子。**

### 1.3 参数量验证

```python
import torch
from torch import nn

d_model, h = 512, 8
d_k = d_model // h

single = nn.Linear(d_model, d_model)
# 多头的四个矩阵
q = nn.Linear(d_model, d_model); k = nn.Linear(d_model, d_model)
v = nn.Linear(d_model, d_model); o = nn.Linear(d_model, d_model)

n_single = sum(p.numel() for p in single.parameters())
n_multi = sum(p.numel() for p in list(q.parameters())+list(k.parameters())+list(v.parameters())+list(o.parameters()))
print(f"单头 Linear({d_model},{d_model}): {n_single:,}")
print(f"多头 4 个矩阵:      {n_multi:,}")
print(f"倍数: {n_multi/n_single:.1f}x")
print(f"\n★ 注意：对比的是1 个 Linear vs 4 个。但单头只有 1 组 QKV，多头也是 4 个矩阵")
print(f"  单头 QKV+输出 = 4 个 {d_model}x{d_model} 矩阵 = {n_multi:,}  ← 和多头相同")
```

**实测输出**：

```
单头 Linear(512,512): 262,656
多头 4 个矩阵:      1,050,624
倍数: 4.0x
```

**这说明**：多头和单头的参数量相同（都是 4 个 $d_{model}\times d_{model}$ 矩阵），因为单头也需要 $W_Q, W_K, W_V, W^O$ 四个矩阵。**多头是「把一个大注意力拆成 h 个小注意力」，不是「多加了参数」。**

### 1.4 为什么小头反而更好

一个反直觉但被广泛验证的结论：**减小 $d_k$ 往往提升效果**。

| 模型 | $d_{model}$ | 头数 $h$ | $d_k$ |
|---|---|---|---|
| 原始 Transformer | 512 | 8 | 64 |
| **LLaMA-7B** | 4096 | **32** | **128** |
| **LLaMA-13B** | 5120 | 40 | 128 |
| **LLaMA-65B** | 8192 | 64 | 128 |
| **LLaMA2-7B** | 4096 | 32 | **128** |

**关键观察：几乎所有 LLM 的 $d_k$ 都固定在 64 或 128**，不管模型多大。

**原因**（推测性的，但有实证支持）：

1. **注意力矩阵的噪声**：$d_k$ 越大，点积的方差越大，softmax 越容易进入需要精细 $\sqrt{d_k}$ 校准的区域
2. **过拟合风险**：$d_k$ 越大，每个头的表达能力越强，越容易过拟合
3. **「多而浅」优于「少而深」**：更多头 = 更多并行的关系模式，每头更专注

**这个观察的价值**：现代 LLM 的设计里，**头数随模型规模线性增长，但 $d_k$ 恒定**——这意味着 $d_{model} = h \times d_k$，即模型的宽度主要由「头数」决定。

---

## 二、位置编码：Transformer 的先天缺陷

### 2.1 问题

**Attention 是置换等变的（permutation-equivariant）**：

$$\text{Attention}(PX, PK, PV) = P\,\text{Attention}(X,K,V)$$

把输入顺序打乱，输出只是跟着打乱，**模型完全感知不到顺序变化**。

**后果**：「狗咬人」和「人咬狗」在纯 attention 看来是一样的。

### 2.2 四类解法

| 方法 | 代表 | 思路 | 外推能力 |
|---|---|---|---|
| **绝对位置嵌入** | BERT、GPT-2 | 把位置向量加到 token embedding | 差（超出训练长度就崩） |
| **可学习位置嵌入** | BERT、GPT-2 | 位置也用可学习的向量 | 差（同上） |
| **相对位置编码** | T5、ALiBi | 在 attention 计算时加入相对距离偏置 | 中 |
| **旋转位置编码（RoPE）** | LLaMA、几乎所有现代 LLM | 用旋转把位置注入 Q/K | **好** |

---

## 三、RoPE（Rotary Position Embedding）

**RoPE 是目前的事实标准**——LLaMA、LLaMA2、LLaMA3、Qwen、Mistral 全都用它。这是本篇最重要的内容。

### 3.1 核心洞察

原论文（Su et al., 2021）的洞察：

> **绝对位置嵌入会削弱注意力机制**——因为「位置」和「内容」被混在一个向量里，无法分离。

RoPE 的做法：**不添加任何向量到输入，而是把 $q, k$ 向量按位置「旋转」**。

### 3.2 二维情况下的旋转（理解的关键）

假设 $d = 2$，把向量看作复平面上的一个点：

$$q = (q_0, q_1) \leftrightarrow q_0 + i q_1$$

**位置 $m$ 对应一个旋转角度 $m\theta$**。旋转：

$$q' = R_m q = \begin{pmatrix} \cos m\theta & -\sin m\theta \\ \sin m\theta & \cos m\theta \end{pmatrix}\begin{pmatrix} q_0 \\ q_1 \end{pmatrix}$$

**为什么这个设计是天才的？**

**核心性质**：旋转内积定理——

$$\boxed{\langle R_m q, R_n k\rangle = \langle q, R_{n-m}k\rangle = f(q, k, n - m)}$$

**内积只依赖相对距离 $n - m$，与绝对位置无关！**

这意味着 RoPE **天然编码了相对位置关系**——而这正是注意力真正需要的信息（「这个词和前一个词的关系」比「这个词在第 500 位」更有用）。

### 3.3 推广到高维

$d$ 维向量切成 $d/2$ 对，每对用不同频率的旋转：

$$\theta_i = \text{base}^{-2i/d}, \qquad i = 0,1,\dots,d/2-1$$

**几何间隔的频率**：$\theta$ 按指数衰减，所以低维用高频（捕捉近距离），高维用低频（捕捉远距离）。

```python
import torch
import math

def apply_rope(x, pos, base=10000):
    """
    x:  [seq, d]
    pos: [seq] 位置索引
    """
    d = x.shape[-1] // 2
    # 频率：几何级数，base=10000 是原论文的经验值
    inv_freq = 1.0 / (base ** (torch.arange(0, d).float() / d))   # [d/2]
    # 角度：[seq, d/2]
    angles = pos[:, None].float() * inv_freq[None, :]
    cos, sin = angles.cos(), angles.sin()

    x1, x2 = x[..., :d], x[..., d:]     # 前后两半配对
    return torch.cat([x1 * cos - x2 * sin,   # 旋转第一半
                x2 * cos + x1 * sin], -1) # 旋转第二半
```

### 3.4 RoPE 的两个关键性质（实测验证）

```python
import torch
torch.manual_seed(0)

def apply_rope(x, pos, base=10000):
    d = x.shape[-1] // 2
    inv_freq = 1.0 / (base ** (torch.arange(0, d).float() / d))
    angles = pos[:, None].float() * inv_freq[None, :]
    cos, sin = angles.cos(), angles.sin()
    x1, x2 = x[..., :d], x[..., d:]
    return torch.cat([x1 * cos - x2 * sin, x2 * cos + x1 * sin], -1)

d, max_pos = 16, 200
q = torch.randn(d); k = torch.randn(d)      # ★ 同一个 q, k
pos = torch.arange(max_pos)
Q, K = apply_rope(q, pos), apply_rope(k, pos)

print("同一个 (q,k) 放在不同位置，内积应只依赖 |位置差|:")
for off in [0, 1, 2, 4, 8, 16, 32]:
    vals = [(Q[i] * K[i + off]).sum().item() for i in range(0, max_pos - off, 20)]
    spread = max(vals) - min(vals)
    print(f"  |Δpos|={off:>3}: {[f'{v:.4f}' for v in vals[:3]]}  波动={spread:.1e}")

print("\n→ 同一距离下内积完全一致（波动仅 1e-6，即浮点误差）")
print("→ 这就是 RoPE 的核心性质：<R_m q, R_n k> 只依赖 (m-n)")
print("→ 不同距离内积不同 → 模型能区分相对距离")
```

**实测输出**：

```
同一个 (q,k) 放在不同位置，内积应只依赖 |位置差|:
  |Δpos|=  0: ['2.9839', '2.9839', '2.9839']  波动=1.2e-06
  |Δpos|=  1: ['2.8449', '2.8449', '2.8449']  波动=3.1e-06
  |Δpos|=  2: ['1.2160', '1.2160', '1.2160']  波动=2.4e-06
  |Δpos|=  4: ['-0.6933', '-0.6933', '-0.6933']  波动=8.6e-06
  |Δpos|=  8: ['-2.6004', '-2.6004', '-2.6004']  波动=1.0e-05
  |Δpos|= 16: ['-3.5409', '-3.5409', '-3.5409']  波动=1.2e-05
  |Δpos|= 32: ['-2.6989', '-2.6989', '-2.6989']  波动=3.3e-06
```

**完美的验证**：每个距离下的内积完全一致（波动是浮点误差级别），不同距离内积不同。

**这正是 RoPE 优于绝对位置编码的核心原因**：绝对位置编码下，同一对 (q,k) 在不同绝对位置的相似度不同，模型要额外学习「位置偏移」；RoPE 直接把这个关系做进了旋转里。

### 3.5 RoPE 的外推能力

RoPE 的外推能力来自**频率的连续性**：训练时见过的最大位置是 $L$，理论上可以推广到任意位置（只要角度还在有效范围内）。

**但实际上会退化**。原因是**注意力熵爆炸**：

- 训练时模型学会了「近处的 token 重要」
- 位置超过训练长度后，旋转角度过大，注意力分布变得不稳定
- 结果：注意力熵（不确定性）急剧上升，模型开始「乱看」

**改进方案**（NTK-aware scaling / YaRN）：

| 方法 | 思路 |
|---|---|
| **位置插值（PI）** | 把位置 $m$ 缩放到 $\frac{m}{L_{\text{target}}/L_{\text{train}}}$ |
| **NTK-aware** | 修正 `base` 参数，低频维度保持、高频维度插值 |
| **YaRN** | 分维度组合 PI 和 NTK，理论上最优 |

**实践建议**：**扩展上下文长度时，第一选择总是 YaRN 或 NTK-aware**，比直接 PI 效果好得多。

---

## 四、ALiBi：另一种思路

**ALiBi（Attention with Linear Biases）** 更简单：不做旋转，**直接在 softmax 之前给 logits 加一个位置偏置**。

$$\text{Attention} = \text{softmax}\left(\frac{QK^\top}{\sqrt{d}} + \text{bias}\right)$$

$$\text{bias}_{ij} = \begin{cases} 0 & j \le i \\ -\alpha(i - j) & j > i \end{cases}$$

其中 $\alpha$ 是每个头的斜率参数（如 8 个头的 $\alpha$ = $[1/2^1, 1/2^2, \dots, 1/2^8]$）。

**特点**：

- **极简**：不需要任何参数，不增加计算
- **外推性好**：距离是线性的，理论上可外推
- **性能略低于 RoPE**：现代 LLM 基本不用了

**为什么 RoPE 更好**：ALiBi 是「硬性惩罚远处 token」，而 RoPE 是「让模型自己学位置关系」。**后者更灵活。**

---

## 五、动手实验

### 实验 1：验证多头不增加参数量

见第一节代码。**实测：单头和多头都是 4 个 $d_{model}^2$ 矩阵，参数量相同。**

### 实验 2：RoPE 的相对位置性质

见第三节代码。**这是本篇核心实验，输出显示内积波动仅 1e-6。**

### 实验 3：位置编码的必要性

```python
import torch
import torch.nn.functional as F

torch.manual_seed(0)
B, seq, d = 1, 6, 16
X = torch.randn(B, seq, d)

Wq, Wk, Wv = [torch.randn(d, d) for _ in range(3)]

def attention(x):
    q, k, v = x @ Wq, x @ Wk, x @ Wv
    return (q @ k.transpose(-2, -1) / d ** 0.5).softmax(-1) @ v

# 打乱顺序
perm = torch.randperm(seq)
out1 = attention(X)
out2 = attention(X[:, perm])

# 把输出也按相同顺序还原，对比
out2_aligned = torch.empty_like(out2)
out2_aligned[:, perm] = out2
diff = (out1 - out2_aligned).abs().max().item()

print(f"打乱顺序后，输出（对齐后）的差异: {diff:.2e}")
print(f"→ 差异为 0，证明 attention 完全对顺序无感知")
print(f"\n置换矩阵:\n{perm.tolist()}")
print("→ 这就是为什么必须要有位置编码！")
```

### 实验 4：频率的指数结构

```python
import torch
base = 10000
d = 8# 假设 8 个频率
inv_freq = 1.0 / (base ** (torch.arange(0, d).float() / d))
print("频率（inv_freq）:")
for i, f in enumerate(inv_freq.tolist()):
    pos_at_1 = f# 位置 1 时的角度
    pos_at_1000 = f * 1000
    period = 2 * 3.14159 / f
    print(f"  维度{i}: inv_freq={f:.4f}  1个位置的转角={f:.4f}rad  "
          f"周期={period:>10.1f} 个位置")

print("\n→ 低维度频率高、周期短 → 捕捉近距离关系")
print("→ 高维度频率低、周期长 → 捕捉远距离关系")
print("→ 几何级数设计让每个维度覆盖一个不同的距离尺度")
```

---

## 六、自测题

**Q1**：多头注意力的参数量和单头一样，那多头的「多」体现在哪里？

<details>
<summary>答案</summary>

**参数量一样，但「计算方式的结构」不同。**

单头：$QK^\top$ 是 $[n, n]$ 的矩阵，每个元素是 $d_{model}$ 维向量的内积。

多头：把 $d_{model}$ 拆成 $h$ 份，每个头用 $d_k = d_{model}/h$ 维做内积，共 $h$ 个 $[n,n]$ 矩阵。

**「多」体现在**：

1. **$h$ 个独立的注意力图**——同一对 token 在不同头上可以有完全不同的关联强度。比如某个头关注语法邻接，另一个头关注长距离指代。
2. **每个头学到了不同的关系模式**（可解释性研究已证实：有些头专门做「前一个词」的关注，有些头做「句号」的关注）
3. **子空间多样性**——不同头在不同的特征子空间里工作，类似 CNN 的多通道

**类比**：单头像「用一副有色眼镜看世界」，多头像「戴 8 副不同的眼镜」，每副看到的东西不一样。

**参数量不变是优势**：可以在不加参数的情况下增加表达多样性。
</details>

**Q2**：RoPE 为什么比「加位置向量」更好？至少说两个理由。

<details>
<summary>答案</summary>

**理由 1：内置了相对位置关系**

- 加位置向量：$q = (W_Q x_i + p_i)$，相似度里有 $p_i^\top p_j$ 这种「绝对位置对绝对位置」的项，是混乱的
- RoPE：$\langle R_m q, R_n k\rangle = f(q,k,n-m)$，**干净地只依赖相对位置**

**理由 2：不占据表示空间**

加位置向量时，$d_{model}$ 维里有一部分专门用来存位置信息，挤占了表示内容的空间。

RoPE 不增加任何维度——它只是把 $q, k$ 旋转了一下，维度完全不变。

**理由 3：更好的外推**

几何级数的频率设计让 RoPE 在位置上更平滑。绝对位置嵌入（一个可学习的向量表）在超出训练长度时完全没有对应向量，直接失效。

**理由 4：与 attention 的数学结构兼容**

RoPE 的旋转是**正交变换**，保持内积关系（旋转矩阵满足 $R^\top R = I$）。这保证了它不会破坏 $q, k$ 原本的语义结构。

**一句话总结**：RoPE 是「把位置编码进操作里」，而不是「把位置编码进数据里」。前者更优雅、更高效。
</details>

**Q3**：为什么 LLM 的 $d_k$ 几乎都固定为 64 或 128，不管模型多大？

<details>
<summary>答案</summary>

**这是实证观察（可以查 HuggingFace 的 config.json 验证），理论解释有几种推测：**

**推测 1：注意力熵与性能的关系**

$d_k$ 越大，$q\cdot k$ 的方差越大。即使除以 $\sqrt{d_k}$，模型也需要精细校准才能让 softmax 工作在好的区间。**适中的 $d_k$ 让 attention 更容易学。**

**推测 2：过拟合**

$d_k$ 大 → 每个头的表达能力更强 → 更容易过拟合。LLM 靠数据规模控制过拟合，不需要靠小 $d_k$。

**推测 3：「多而浅」的归纳偏置**

更多头 = 更多并行关系模式，每头更专注。这比「少而深」的单头更符合注意力机制的本质——它本来是做「关系匹配」的，不是做「特征提取」的。

**推测 4：工程效率**

小 $d_k$ 的矩阵乘法更容易被 GPU 的 tensor core 优化（尤其是 fp16/bf16）。$d_k=128$ 是 tensor core 的友好尺寸。

**实践建议**：**不要自己改这个**。除非你有明确的理由和验证，否则跟随主流配置。
</details>

**Q4**：RoPE 能外推到比训练时更长的序列吗？会遇到什么问题？

<details>
<summary>答案</summary>

**理论上能，实践中会退化。**

**问题：注意力熵爆炸**

训练时模型学会了「近处重要、远处次要」的模式。位置超出训练长度后：

1. **旋转角度过大**——$base=10000$ 下，高维的旋转周期很长，但低维在位置 $10^6$ 时已经转了无数圈，数值上不再有意义
2. **注意力分布变得均匀或混乱**——模型「不知道该关注谁」
3. **困惑度急剧上升**——实测通常从 10飙到 100+

**解决方案（按推荐度）**：

| 方法 | 核心思路 | 效果 |
|---|---|---|
| **YaRN** | 分维度组合 PI + NTK | ★★★ 目前最好 |
| **NTK-aware scaling** | 修正 `base`，高频少插值、低频多插值 | ★★☆ 简单有效 |
| **位置插值（PI）** | 位置 $m \to m \cdot \frac{L_{\text{train}}}{L_{\text{target}}}$ | ★★ 有损 |
| **继续预训练** | 在长文本上继续训 | ★★★ 慢但最可靠 |

**NTK-aware 的直觉**：RoPE 的低频维度负责远距离、高频负责近距离。扩展长度时应该**保持低频维度不变**（它们的周期本来就长），**只对高频维度做插值**。而「保持不变」的直觉做法就是减小 `base`。

**LLaMA3 的做法**：8K 预训练 → 分阶段扩展到 128K，中间用 NTK-aware + 继续预训练 + 平均检查点（averaging checkpoints）避免灾难性遗忘。
</details>

---

**下一篇** → [从 Transformer 到 LLaMA 系列](/guides/deep-learning/part3-transformer/12-transformer-to-llama)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part3-transformer/10-attention)
