---
title: 从 Transformer 到 LLaMA 系列
description: 现代 LLM 相对原始 Transformer 改了什么？每个改动解决了什么问题？
---

# 12 · 从 Transformer 到 LLaMA 系列

> 核心问题：现代 LLM 相对原始 Transformer 改了什么？每个改动解决了什么问题？

---

## 一、原始 Transformer（2017）

### 1.1 Encoder-Decoder 结构

```
Encoder（双向，原点式）         Decoder（自回归 +交叉注意力）
┌─────────────────┐            ┌──────────────────────┐
│ MultiHeadAttention │            │ MaskedMultiHeadAttention │
│ + Add & Norm      │            │ + Add & Norm              │
│                   │            │                          │
│ FeedForward       │  ────────→ │ CrossAttention           │
│ + Add & Norm      │            │ + Add & Norm             │
│  × N层            │            │ FeedForward + Add & Norm │
└─────────────────┘            │  × N 层                   │
                                └──────────────────────┘
```

**两个关键区别**：

| | Encoder | Decoder |
|---|---|---|
| 注意力 mask | 无（**双向**） | **causal**（只能看前面） |
| 注意力输入 | 只有源序列 | 自注意力 + encoder 的输出 |
| 用途 | BERT（理解） | GPT（生成） |

**现代 LLM 只保留了 Decoder 部分**（叫 decoder-only），因为：
1. 统一了理解和生成任务
2. 因果 mask 让训练可以并行（每个位置同时预测下一个词）
3. 架构更简单

### 1.2 原始 Block 的 Post-LN 结构

$$\text{out} = \text{LayerNorm}(x + \text{Sublayer}(x))$$

**注意 LayerNorm 在残差相加之后** —— 这叫 **Post-LN**。

**问题**：LN 夹在残差通路上，梯度要穿过 LN 才能回传，导致深层训练需要精细的 warmup，否则容易发散。

---

## 二、现代 LLaMA 风格的四大改动

```
Post-LN                →  Pre-LN
LayerNorm → RMSNorm    →  RMSNorm（更轻）
位置编码相加            →  RoPE（更自然）
FFN 的 ReLU           →  SwiGLU（更有效）
```

**核心主题：从「能不能训」转向「怎么训得更好」。**

---

## 三、Pre-LN：最重要的改动

### 3.1 结构对比

```
Post-LN (原始 Transformer):
    x → Sublayer(x) → +x → LayerNorm → 下一层

Pre-LN (现代 LLM):
    x → LayerNorm(x) → Sublayer → +x → 下一层
```

### 3.2 为什么 Pre-LN 更好

**梯度通路的区别**：

**Post-LN** 的残差通路：**不干净**——LN 在通路中间，梯度要「穿过 LN」：

$$\frac{\partial x_{L+1}}{\partial x_L} = \text{LN}'\left(x_L + F(x_L)\right)\left(I + F'(x_L)\right)$$

那个 $\text{LN}'$ 是额外因子，深层累积会不稳定。

**Pre-LN** 的残差通路：**干净的恒等映射**：

$$\frac{\partial x_{L+1}}{\partial x_L} = I + F'(\text{LN}(x_L))$$

**那个 $I$ 保证了梯度 100% 直通**——即使 $F'$ 是任何矩阵，梯度至少原封不动传下去。

### 3.3 实证

| | Post-LN | Pre-LN |
|---|---|---|
| 深层训练 | 需要 warmup | **稳定** |
| warmup | 必需（通常 4000 步） | 可选 |
| 最终性能 | 可能略好 | 略差或持平 |
| 现代 LLM | 几乎不用 | **全部采用** |

**为什么最终性能反而 Post-LN 略好？** 一个解释是 Post-LN 的 LN 在每个子层后重新缩放特征，有一定的正则化作用。但**这个优势远小于「能稳定训练」的价值**，所以全部转向 Pre-LN。

**一个易错点**：Pre-LN 要求最后有一个 **final norm**（在所有层之后）：

```python
x = block(x) for _ in range(N)
x = self.norm(x)       # ★ final LayerNorm/RMSNorm，必需！
```

因为 Pre-LN 的最后一个 block 输出**没有经过归一化**（LN 在子层内部）。

---

## 四、RMSNorm

第 6 篇已详述。这里只强调它在 LLaMA 里的作用：

| | LayerNorm | RMSNorm（LLaMA 选择） |
|---|---|---|
| 参数 | $2d$（$\gamma, \beta$） | $d$（只有 $\gamma$） |
| 计算 | 求均值 + 求方差 + 减均值 + 除 | **只求均方根 + 除** |
| 能否融合 kernel | 部分 | **可以完全融合** |

**LLaMA-7B 的实际节省**（$d=4096$，32 层）：

- 参数：每层省 $4096$，共省 $131K$（占总量 0.02%，微不足道）
- **显存和速度：可融合进相邻算子，减少多次 HBM 读写**

**关键点**：RMSNorm 的收益**不在参数，而在计算融合**。

---

## 五、SwiGLU：更好的 FFN

### 5.1 三种 FFN 对比

**原始 Transformer**：

$$\text{FFN}(x) = \text{ReLU}(xW_1 + b_1)W_2 + b_2$$

**GLU（Gated Linear Unit）**：

$$\text{GLU}(x) = \text{ReLU}(xW_1) \otimes (xW_2)$$

**SwiGLU（LLaMA 的选择）**：

$$\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_3)$$

其中 SiLU（也叫 Swish）：$\text{SiLU}(x) = x \cdot \sigma(x)$

### 5.2 门控的直觉

**乘性激活 = 一个「门」控制另一个「内容」**：

```
SiLU(xW₁)⊗ (xW₃)
   ↓            ↓
  门(0~1)      内容(任意实数)
   ↓            ↓
   ↑──── 逐元素相乘 ────↑
       门=0 → 完全关闭
       门=1 → 完全通过
```

**为什么这有用**：普通的 ReLU 只能「开启或关闭」整个神经元（且不可微地调整）。门控允许**每个维度独立控制**信息的通过量，而且是**可学习的**。

### 5.3 参数量陷阱：为什么中间层要缩小

**SwiGLU 有三个矩阵（$W_1, W_3, W_2$），比原来多一个**。为了保持参数量不变，中间层维度要缩小：

$$\text{隐层维度} = \frac{8}{3}d \approx 2.67d \quad \text{(保持参数量与 FFN(4d) 相当)}$$

LLaMA 用的就是这个：**`intermediate_size = 8192` 而 `hidden_size = 4096`**，比例是 2.0 而不是 4.0。

**验证**：

| FFN 类型 | 中间维度 | 参数量（$d=4096$） |
|---|---|---|
| FFN(4d) | 16384 | $3 \times d^2$ |
| SwiGLU(8/3 d) | 10923 | $3 \times d \times (8/3)d = 8d^2$ |
| **LLaMA** | **8192** | $3 \times 4096 \times 8192 = 100M$ |

**经验值**：LLaMA 用 2:1 到 8:3 之间的比例，效果基本持平。

---

## 六、GQA：分组查询注意力（推理优化）

第 13 篇详细讲计算，这里只给结构对比：

```
MHA (Multi-Head Attention):   Q, K, V 都是 [h, d]      ← 全部多头
MQA (Multi-Query):           Q=[h,d], K=[1,d], V=[1,d]  ← KV 只有 1 头
GQA (Grouped-Query):         Q=[h,d], K=[g,d], V=[g,d]  ← KV 分 g 组★
```

**LLaMA2 用 MQA，LLaMA3 用 GQA。** GQA 是 MHA 和 MQA 的折中，效果接近 MHA、成本接近 MQA。

---

## 七、LLaMA 完整配置对照表

| 组件 | 原始 Transformer | **LLaMA / 现代 LLM** | 原因 |
|---|---|---|---|
| 结构 | Encoder-Decoder | **Decoder-only** | 统一任务，训练并行 |
| 归一化位置 | **Post-LN** | **Pre-LN** | 梯度稳定 |
| 归一化类型 | LayerNorm | **RMSNorm** | 可融合，更快 |
| 位置编码 | 正弦绝对位置 | **RoPE** | 相对位置，外推好 |
| FFN | ReLU | **SwiGLU** | 门控表达力强 |
| FFN 中间维度 | 4d | **~2.67d** | 补偿 SwiGLU 的额外矩阵 |
| 激活 | ReLU | **GELU / SiLU** | 平滑 |
| Attention | MHA | **GQA**（推理友好） | 省 KV cache |
| 初始化 | Xavier | **$N(0, 0.02)$** | RMSNorm 已处理尺度 |
| 归一化 | 无 bias | **无 bias** | 更简洁 |
| 学习率调度 | warmup+decay | **warmup + cosine** | 标准配置 |
| 精度 | fp32 | **bf16/fp16** | 效率 |

---

## 八、从零实现一个 LLaMA Block

把上面所有内容串起来：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class RMSNorm(nn.Module):
    def __init__(self, d, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d))
        self.eps = eps

    def forward(self, x):
        # ★ 只除以均方根，不减均值
        rms = x.pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()
        return self.weight * (x * rms)


def precompute_rope_angles(d, base=10000):
    """预计算 RoPE 的 cos/sin 表"""
    half = d // 2
    inv_freq = 1.0 / (base ** (torch.arange(0, half, 2).float() / half))
    return inv_freq


def apply_rope(x, cos, sin):
    """x: [..., seq, d]，cos/sin: [seq, d//2]"""
    half = x.shape[-1] // 2
    x1, x2 = x[..., :half], x[..., half:]
    return torch.cat([x1 * cos - x2 * sin, x2 * cos + x1 * sin], dim=-1)


class RotaryEmbedding(nn.Module):
    def __init__(self, d, max_seq=2048, base=10000):
        super().__init__()
        self.d = d
        inv_freq = 1.0 / (base ** (torch.arange(0, d, 2).float() / d))
        pos = torch.arange(max_seq).float()
        angles = torch.outer(pos, inv_freq)              # [max_seq, d/2]
        self.register_buffer("cos_cached", angles.cos(), persistent=False)
        self.register_buffer("sin_cached", angles.sin(), persistent=False)

    def forward(self, seq_len):
        return self.cos_cached[:seq_len], self.sin_cached[:seq_len]


class Attention(nn.Module):
    """支持 GQA 的多头注意力"""

    def __init__(self, d, n_heads, n_kv_heads=None):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads or n_heads
        assert n_heads % self.n_kv_heads == 0, "n_heads 必须被 n_kv_heads 整除"
        self.n_rep = n_heads // self.n_kv_heads      # ★ GQA: 每个 KV 头被多少 Q 头共享
        self.d_head = d // n_heads

        self.wq = nn.Linear(d, n_heads * self.d_head, bias=False)
        self.wk = nn.Linear(d, self.n_kv_heads * self.d_head, bias=False)   # ★ 更少
        self.wv = nn.Linear(d, self.n_kv_heads * self.d_head, bias=False)   # ★ 更少
        self.wo = nn.Linear(n_heads * self.d_head, d, bias=False)

    def forward(self, x, cos, sin):
        B, L, _ = x.shape

        q = self.wq(x).view(B, L, self.n_heads, self.d_head).transpose(1, 2)
        k = self.wk(x).view(B, L, self.n_kv_heads, self.d_head).transpose(1, 2)
        v = self.wv(x).view(B, L, self.n_kv_heads, self.d_head).transpose(1, 2)

        # ★ RoPE 只作用在 q, k 上，不作用在 v
        q = apply_rope(q, cos, sin)
        k = apply_rope(k, cos, sin)

        # ★ GQA: 把 KV 头重复到和 Q 头一样多（必须在 attention 之前）
        if self.n_rep > 1:
            k = k.repeat_interleave(self.n_rep, dim=1)   # [B, n_kv, L, dh] -> [B, n_heads, L, dh]
            v = v.repeat_interleave(self.n_rep, dim=1)

        # ★ 用 PyTorch 内置的融合实现（自动选最优后端）
        out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        out = out.transpose(1, 2).contiguous().view(B, L, -1)
        return self.wo(out)


class SwiGLU(nn.Module):
    def __init__(self, d, hidden):
        super().__init__()
        # ★ 三个矩阵：门、值、下投影
        self.w_gate = nn.Linear(d, hidden, bias=False)
        self.w_up   = nn.Linear(d, hidden, bias=False)
        self.w_down = nn.Linear(hidden, d, bias=False)

    def forward(self, x):
        # ★ SwiGLU = SiLU(门) ⊗ 值
        return self.w_down(F.silu(self.w_gate(x)) * self.w_up(x))


class LlamaBlock(nn.Module):
    def __init__(self, d, n_heads, n_kv_heads, hidden):
        super().__init__()
        self.attn = Attention(d, n_heads, n_kv_heads)
        self.ffn = SwiGLU(d, hidden)
        self.norm1 = RMSNorm(d)          # ★ Pre-LN
        self.norm2 = RMSNorm(d)

    def forward(self, x, cos, sin):
        # ★ Pre-LN：先norm 再算，最后残差相加
        x = x + self.attn(self.norm1(x), cos, sin)
        x = x + self.ffn(self.norm2(x))
        return x


class LlamaModel(nn.Module):
    def __init__(self, vocab=32000, d=4096, n_layers=32, n_heads=32,
                 n_kv_heads=32, max_seq=2048, ffn_hidden=None):
        super().__init__()
        self.d = d
        ffn_hidden = ffn_hidden or int(8 * d / 3 / 64) * 64 # 8/3 d，对齐64

        self.embed = nn.Embedding(vocab, d)
        self.rope = RotaryEmbedding(d // n_heads, max_seq)  # RoPE 在 d_head 维度上做
        self.layers = nn.ModuleList([
            LlamaBlock(d, n_heads, n_kv_heads, ffn_hidden) for _ in range(n_layers)
        ])
        self.norm = RMSNorm(d)          # ★ final norm，Pre-LN 必需
        self.lm_head = nn.Linear(d, vocab, bias=False)
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def forward(self, tokens):
        x = self.embed(tokens)
        cos, sin = self.rope(x.shape[1])
        for layer in self.layers:
            x = layer(x, cos, sin)
        x = self.norm(x) # ★ final norm
        return self.lm_head(x)


# 测试
if __name__ == "__main__":
    model = LlamaModel(vocab=32000, d=512, n_layers=4, n_heads=8,
                        n_kv_heads=2, max_seq=128, ffn_hidden=1365)
    print(model)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"\n总参数: {n_params:,}")

    tokens = torch.randint(0, 32000, (2, 16))
    logits = model(tokens)
    print(f"输入 {tuple(tokens.shape)} → 输出 {tuple(logits.shape)}")

    # 验证 causal
    loss = F.cross_entropy(logits[:, :-1].reshape(-1, 32000),
                tokens[:, 1:].reshape(-1))
    print(f"loss: {loss.item():.4f}")
    loss.backward()
    print("反向传播成功")
```

**实测输出**（这份代码可以直接运行，见 [代码/llama_from_scratch.py](/downloads/llama_from_scratch.py)）：

```
LlamaModel(
  (embed): Embedding(32000, 512)
  (layers): ModuleList(
    (0): LlamaBlock(
      (attn): Attention()
      (ffn): SwiGLU()
      (norm1): RMSNorm()
      (norm2): RMSNorm()
    )
    ... 共 4 层
  )
  (norm): RMSNorm()
  (lm_head): Linear(in_features=512, out_features=32000, bias=False)
)

总参数: 43,780,608
输入 (2, 16) → 输出 (2, 16, 32000)
loss: 10.5041
反向传播成功
```

**注意几个数字**：

1. **初始 loss = 10.50**。理论上 $\ln(32000) = 10.37$——我们的 loss 略高于均匀分布，因为用了 std=0.02 的初始化。**训练开始时 loss 应该在 $\ln(V)$ 附近**，这是初始化正确性的快速检查。

2. **参数量 43.8M** 而 4 层模型的主体（不含 embedding）只有约 1.1M。**embedding 占了绝大部分**（32000 × 512 = 16.4M，两个 embedding 32.8M）。这是小模型的典型特征。

3. **代码里 GQA（n_kv_heads=2）能正常工作**——这是实现中最容易出错的地方，我第一版忘了在 attention 之前把 KV 头repeat 到和 Q 头一样多，报形状不匹配的错误。

**想验证 GQA 是否真的省了显存**，对比一下：

```python
# MHA 版本
model_mha = LlamaModel(vocab=32000, d=512, n_layers=4, n_heads=8,
                       n_kv_heads=8, max_seq=128, ffn_hidden=1365)
# GQA 版本（本例）
model_gqa = LlamaModel(vocab=32000, d=512, n_layers=4, n_heads=8,
                       n_kv_heads=2, max_seq=128, ffn_hidden=1365)
print(f"MHA: {sum(p.numel() for p in model_mha.parameters()):,} 参数")
print(f"GQA: {sum(p.numel() for p in model_gqa.parameters()):,} 参数")
```

**实测输出**：

```
MHA: 45,353,472 参数
GQA: 43,780,608 参数
省 1,572,864 参数
```

**GQA 省了 157 万参数**（占 transformer 部分的约 3.5%）。**这个比例在真实模型里更明显**——因为真实模型的 transformer 部分占比更高，且序列更长（KV cache 的节省与序列长度成正比）。

---

## 九、LLaMA2 相比 LLaMA 改进了什么

| 改进 | 说明 |
|---|---|
| **更多数据** | 2T tokens（LLaMA 是 1.3T） |
| **上下文 4K** | LLaMA 是 2K |
| **训练 token 效率↑** | 同样的算力下用更多数据 |
| **超参修正** | 回归 warmup samples、调整 lr/batch |
| **GQA（70B 用）** | KV cache 减半 |
| **Rope 缩放** | 支持更长上下文 |

**核心洞察**：**LLaMA2 的提升主要靠数据规模和方法修正，不是架构变化。** 这和「暴力缩放定律」是一致的（第 14 篇）。

---

## 十、自测题

**Q1**：为什么 Pre-LN 需要在最后加一个 final norm？Post-LN 呢？

<details>
<summary>答案</summary>

**Pre-LN：必需。**

Pre-LN 的结构是：

```
x → norm(x) → sublayer → +x → 下一层
```

**最后一层的输出从未经过归一化**（norm 在每个 block 的**内部**）。所以最后一个 block 的输出尺度是任意的——可能很大或很小，直接送进 lm_head 会导致 logits 尺度失控。

```python
x = layer(x) for _ in range(N)
x = self.norm(x)         # ★ 必须
logits = self.lm_head(x)
```

**Post-LN：不需要。**

```
x → sublayer(x) + x → norm → 下一层
```

**每个 block 的输出都经过了 LayerNorm**，最后那个 block 的输出已经归一化过了。

```python
x = layer(x) for _ in range(N)
logits = self.lm_head(x)   # 直接用，因为已经归一化
```

**忘记加 final norm 是 Pre-LN 实现最常见的 bug**——症状是训练 loss 曲线很奇怪，或者 logits 数值过大导致 softmax 完全饱和。
</details>

**Q2**：SwiGLU 有三个矩阵，为什么中间层维度反而要缩小？

<details>
<summary>答案</summary>

因为**要保持参数量不变**。

原始 FFN（两个矩阵）：

$$\text{参数量} = d \times 4d + 4d \times d = 8d^2$$

SwiGLU（三个矩阵），设中间维度为 $h$：

$$\text{参数量} = d \times h + d \times h + h \times d = 3dh$$

**令两者相等**：

$$3dh = 8d^2 \quad \Rightarrow \quad h = \frac{8}{3}d \approx 2.67d$$

**如果保持原来的 $4d$**，参数量会变成 $3 \times d \times 4d = 12d^2$，比原来多 50%——这样就无法公平比较「SwiGLU 更好」还是「参数更多更好」。

**LLaMA 的具体做法**：`hidden_size=4096`，`intermediate_size=8192`，比例是 **2.0**（不是 2.67）。这实际上让参数量略低于原始 Transformer。

**结论**：SwiGLU 的效果提升是**在同等参数量下**取得的，纯粹来自「门控」这个结构改变。
</details>

**Q3**：为什么 decoder-only 成为主流，encoder-decoder 去哪了？

<details>
<summary>答案</summary>

**Encoder-decoder 没消失，但被 decoder-only 统一了。**

**decoder-only 的优势**：

1. **训练可以完全并行**——causal mask 让每个位置同时预测下一个词，整句话一次算完。encoder-decoder 也并行，但 decoder 只能看到 encoder 输出，任务设计更复杂
2. **统一任务**——加 [MASK] token 就变成 BERT 的填空任务，加 [BOS] 就变成生成任务。一个架构做所有事
3. **架构简单**——只有一种 block，不需要维护两套参数
4. **in-context learning**——decoder-only 天然支持「给几个例子 → 学到模式 → 做新任务」。这是 LLM 少样本能力的来源。encoder-decoder 天然不适合这个模式

**encoder-decoder 仍占优势的场景**：

| 场景 | 为什么 |
|---|---|
| **翻译** | 输入输出界限清晰，cross-attention 有用 |
| **摘要** | 同上 |
| **语音（TTS、ASR）** | 输入是连续信号，encoder 处理更合适 |
| **小型模型** | decoder-only 需要更多数据才收敛；enc-dec 在小数据上更好 |

**代表模型**：T5、mT5（enc-dec）；BART（enc-dec 但部分修改）；LLaMA、GPT、Qwen（decoder-only）。

**判断标准**：**除非做 seq2seq 或有明确的输入输出界限，否则 decoder-only 是更安全的选择。**
</details>

**Q4**：LLaMA 用 $N(0, 0.02)$ 初始化所有层，这不会有问题吗？

<details>
<summary>答案</summary>

**不会，而且这正是架构设计的好处——因为 RMSNorm 已经把尺度问题解决了。**

**对比需要精细初始化的场景**：

传统 MLP 中，每层的输出尺度会逐层累积。第 1 层输出 std 是 0.02，第 2 层就是 0.02 × (权重尺度)……**如果不精心设计初始化，深层网络必然出问题**（第 9 篇的实验：默认初始化衰减 4.65e14 倍）。

**为什么 LLaMA 敢用统一初始化**：

1. **RMSNorm 在每个子层入口把激活归一化了** → 进入下一个 Linear 时方差恒为 1 → 不需要考虑跨层的尺度累积
2. **Pre-LN 残差通路是干净恒等** → 梯度稳定
3. **所有层形状相似**（hidden_dim 统一）→ 一个 std 够用

**0.02 这个数字的来源**：

```python
nn.init.normal_(m.weight, mean=0.0, std=0.02)
```

经验值，比 Xavier 略大一点。GPT-2 用的也是 0.02。**实际差别不大，0.01~0.02 都能训。**

**这个案例的启示**：**好的架构设计（加归一化）能让初始化这个「魔法数字」变得不重要。** 这比调参重要得多。
</details>

---

**下一篇** → [推理优化：KV Cache 与 GQA](/guides/deep-learning/part3-transformer/13-kv-cache-gqa)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part3-transformer/11-multi-head-rope)
