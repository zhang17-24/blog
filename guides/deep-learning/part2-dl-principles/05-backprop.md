---
title: 反向传播的完整推导
description: 链式法则在一个具体网络里怎么展开？梯度消失/爆炸的数学本质是什么？
---

# 5 · 反向传播的完整推导

> 核心问题：链式法则在一个具体网络里怎么展开？梯度消失/爆炸的**数学本质**是什么？

---

## 一、一个最小的网络

用最小的例子把整个过程走一遍。网络只有两层：

```
x --W1--> z1 --ReLU--> a1 --W2--> z2 --> L
       +b1                     +b2
```

**前向**：

$$\begin{aligned} z_1 &= W_1 x + b_1 \\ a_1 &= \text{ReLU}(z_1) = \max(0, z_1) \\ z_2 &= W_2 a_1 + b_2 \\ L &= (z_2 - y)^2 \end{aligned}$$

现在要算 $\frac{\partial L}{\partial W_1}$、$\frac{\partial L}{\partial W_2}$、$\frac{\partial L}{\partial b_1}$、$\frac{\partial L}{\partial b_2}$。

**这里的关键认知**：反向传播不是「每个参数独立算一次」，而是**从输出往输入传一个「敏感度」，沿途用乘法法则分发给每个分支**。

---

## 二、反向传播：一个参数一个参数推

### 2.1 从损失开始

$$\frac{\partial L}{\partial z_2} = 2(z_2 - y)$$

**这个 2 就是 MSE 的特征**。如果 loss 写成 $\frac{1}{2}(z_2-y)^2$（很多教材这么写），梯度就干净了：$\frac{\partial L}{\partial z_2} = (z_2-y)$。**这就是为什么有些教材的 loss 系数是 $\frac{1}{2N}$ 而不是 $\frac{1}{N}$** ——纯粹为了消掉这个 2。

### 2.2 分发给 $W_2$ 和 $b_2$

$z_2 = W_2 a_1 + b_2$，求 $\frac{\partial L}{\partial W_2}$：

$$z_2 = \sum_j (W_2)_{ij}(a_1)_j + (b_2)_i$$

对 $(W_2)_{ij}$ 求导，$(W_2)_{ij}$ 只出现在第 i 项里：

$$\frac{\partial L}{\partial (W_2)_{ij}} = \frac{\partial L}{\partial z_2}\cdot\frac{\partial z_2}{\partial (W_2)_{ij}} = \frac{\partial L}{\partial z_2}\cdot (a_1)_j$$

**写成矩阵形式**（避免下标地狱）：

$$\boxed{\frac{\partial L}{\partial W_2} = \underbrace{\frac{\partial L}{\partial z_2}}_{\text{[1,1]}} \cdot \underbrace{a_1^\top}_{\text{[1,H]}} = \text{outer product}}$$

外积的形状：$[\text{out}, 1] \times [1, \text{in}] = [\text{out}, \text{in}]$ ✓ 正好是 $W_2$ 的形状。

$$\frac{\partial L}{\partial b_2} = \frac{\partial L}{\partial z_2}$$

（因为 $b_2$ 是加法，导数为 1）

### 2.3 穿过 ReLU

$$\frac{\partial a_1}{\partial z_1} = \begin{cases} 1 & z_1 > 0 \\ 0 & z_1 \le 0 \end{cases}$$

所以：

$$\frac{\partial L}{\partial z_1} = \frac{\partial L}{\partial a_1} \odot \text{1}[z_1 > 0]$$

**这里有个重要事实：ReLU 会把负半轴的梯度完全掐断（置0）。** 这是 ReLU 「死神经元」问题的根源——如果一个神经元对所有输入都是负的，它的梯度永远是 0，参数永远不更新，等于废掉了。

### 2.4 分发给 $W_1$ 和 $b_1$

$$\frac{\partial L}{\partial W_1} = \frac{\partial L}{\partial z_1} \cdot x^\top, \qquad \frac{\partial L}{\partial b_1} = \frac{\partial L}{\partial z_1}$$

**到这里就完成了。** 完整链条：

$$\frac{\partial L}{\partial z_2} \to \frac{\partial L}{\partial a_1} \to \frac{\partial L}{\partial z_1} \to \frac{\partial L}{\partial W_1}, \frac{\partial L}{\partial b_1}$$

---

## 三、通用规则（记住这三条就够）

反向传播就是**从后往前反复应用这三条规则**：

### 规则 1：加法 → 梯度直接分发

```
z = a + b
∂L/∂a = ∂L/∂z    ∂L/∂b = ∂L/∂z
```

多个分支收到**相同的**上游梯度（所以 GradienT 累加不是 bug，是数学要求）。

### 规则 2：乘法 → 梯度交叉相乘

```
z = a × b
∂L/∂a = ∂L/∂z × b    ∂L/∂b = ∂L/∂z × a
```

### 规则 3：矩阵乘法 → 外积

```
z = a @ W        （a: [B,in], W: [in,out], z: [B,out]）

∂L/∂W = aᵀ @ (∂L/∂z)          [in,B]@[B,out] = [in,out]  ✓ 和 W 同形状
∂L/∂a = (∂L/∂z) @ Wᵀ          [B,out]@[out,in] = [B,in]   ✓ 和 a 同形状
∂L/∂b = (∂L/∂z).sum(0)        按 batch 求和→  [out]
```

**记忆方法**：**「哪个输入和梯度同形状，就用它的转置去乘另一个」**。

- $W$ 是 `[in, out]`，要得到 `[in, out]`，就用 $a^\top[B,in]$ 乘 $(\partial L/\partial z)[B,out]$
- $a$ 是 `[B, in]`，要得到 `[B, in]`，就用 $(\partial L/\partial z)[B,out]$ 乘 $W^\top[out,in]$

**这就是外积的批量版**：$\partial L/\partial W = \sum_i (\text{第}i\text{ 个样本的}\ \partial L/\partial z_i) \otimes a_i$ —— 每个样本贡献一个外积，加起来就是矩阵乘。

**PyTorch 里的对应关系**：

| 数学写法 | PyTorch |
|---|---|
| 外积 $(ab^\top)$ | `torch.outer(a, b)` 或 `a @ b.T` |
| 张量对元素积 $\odot$ | `a * b` |
| 矩阵乘 | `@` |
| 沿 dim 求和 | `.sum(dim=n)` |

### 一句话总结

> **反向传播 = 反向应用链式法则 + 把「敏感度」沿计算图分发。** 加法节点等值分发，乘法节点交叉相乘，矩阵乘用外积。

---

## 四、梯度消失与爆炸的数学本质

这是本文最重要的部分。**理解了这段，你就能自己判断任何架构设计的梯度行为**，不需要背「ResNet 解决了梯度消失」这种结论。

### 4.1 梯度经过一层的衰减/放大

考虑一个 $L$ 层、宽度 $n$ 的全连接网络（ReLU + 合适的初始化）。每层权重的 Jacobian 矩阵 $J_i$ 的元素典型大小约 $O(\frac{1}{\sqrt n})$（He 初始化的设计目标）。

反向传播时梯度要连乘 $L$ 个 Jacobian：

$$\frac{\partial L}{\partial x} = J_L \cdot J_{L-1} \cdots J_1 \cdot \frac{\partial L}{\partial \text{out}}$$

每个因子贡献一个 $\frac{1}{\sqrt n}$，连乘 $L$ 次：

$$\left(\frac{1}{\sqrt n}\right)^L = n^{-L/2}$$

| 网络 | $L$ | $n$ | $n^{-L/2}$ |
|---|---|---|---|
| 浅层 | 3 | 100 | $10^{-3}$ |
| 深层 | 30 | 100 | $10^{-15}$ |
| 深层 | 100 | 1000 | $10^{-150}$ |

**$10^{-15}$ 在 float32 的精度下就是 0。** 这就是梯度消失。

### 4.2 Sigmoid 的额外问题

如果激活函数是 sigmoid/tanh，导数最大只有 0.25（sigmoid）：

$$\sigma'(z) = \sigma(z)(1-\sigma(z)) \le 0.25$$

**每经过一层，梯度至少乘以 0.25。** 10 层就是 $0.25^{10} \approx 10^{-6}$。

**为什么 ReLU 缓解了这个问题**：$\text{ReLU}'(z) \ge 0$ 且期望为 1（对 $z>0$ 部分导数为 1），所以不会引入额外的衰减。这就是 2012 年 ReLU 带来突破的数学原因。

### 4.3 梯度爆炸

反过来，如果权重初始化太大（$J$ 的元素 $\gg 1$），连乘后会指数爆炸：

$$\frac{\partial L}{\partial x} \propto \left(\frac{\text{something} \gg 1}{\sqrt n}\right)^L \to \infty$$

**表现**：loss 突然变成 `nan`、梯度值离谱、参数被更新到溢出。

**解法是梯度裁剪**（gradient clipping）：

```python
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

把所有梯度作为一个整体，计算 L2 范数，如果超过阈值就等比缩放：

$$\hat{g} = g \cdot \frac{\text{max\_norm}}{\|g\|} \quad \text{当} \|g\| > \text{max\_norm}$$

**注意是等比缩放所有梯度，不是逐元素裁剪**（后者会改变梯度方向，破坏优化语义）。

**LLM 训练标准配置里都有 `clip=1.0`**。这不是可选项。

### 4.4 残差连接如何解决

残差连接：$a_{l+1} = a_l + f(a_l)$

反向传播时，梯度有一条「直达通路」：

$$\frac{\partial L}{\partial a_l} = \frac{\partial L}{\partial a_{l+1}}\left(I + \frac{\partial f}{\partial a_l}\right)$$

那个 $I$（单位矩阵）意味着**梯度可以原封不动地传下去**。

即使 $f$ 那部分的梯度衰减到 0，还有 $I$ 兜着。所以：

$$\frac{\partial L}{\partial a_1} = \prod_{l=1}^{L}\left(I + J_l\right)$$

这个乘积里，每项都含 $I$，**展开后至少有一项全是 $I$ 的乘积**（对应「所有残差路径都不走 $f$」那条路线），所以梯度不衰减。

**这是 ResNet 能训 100 层的数学保证。** 详见第 8 篇。

### 4.5 一个必须掌握的自测方法

**判断一个新架构会不会梯度消失/爆炸，不要靠猜——做实验测量。**

```python
# 逐层测量梯度范数，一眼看出是否衰减/爆炸
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name:40s} ||grad|| = {param.grad.norm().item():.3e}")
```

**判读**：

- 逐层指数下降（如 1e-1 → 1e-3 → 1e-5 → 1e-8）→ 梯度消失
- 逐层指数上升 → 梯度爆炸
- 各层量级相当（1e-2 量级上下浮动）→ 健康

**这个技巧在任何论文的复现里都用得上**。看到一个新架构，第一件事就是打这个表。

---

## 五、动手实验

### 实验 1：验证手推公式和 autograd 完全一致

```python
import torch

torch.manual_seed(0)
B = 4
W1 = torch.randn(3, 2, requires_grad=True); b1 = torch.zeros(2, requires_grad=True)
W2 = torch.randn(2, 1, requires_grad=True); b2 = torch.zeros(1, requires_grad=True)
x = torch.randn(B, 3); y = torch.randn(B, 1)

# ---- 前向 ----
z1 = x @ W1 + b1          # [4,3]@[3,2] = [4,2]
a1 = torch.relu(z1)
z2 = a1 @ W2 + b2         # [4,2]@[2,1] = [4,1]
loss = ((z2 - y) ** 2).mean()
loss.backward()

# ---- 手推反向（严格按矩阵形状推导）----
# L = (1/B) * Σ_i (z2_i - y_i)²
# dL/dz2 是逐样本的：∂L/∂z2_i = 2(z2_i - y_i)/B
dL_dz2 = 2 * (z2 - y) / B                    # [4,1]

# W2 是 [2,1]，z2 = a1 @ W2 + b2 → dL/dW2 = (dL/dz2)ᵀ @ a1，但需要 [2,1]
dL_dW2 = dL_dz2.T @ a1                       # [1,4]@[4,2] = [1,2]
dL_db2 = dL_dz2.sum(0)                       # [1]

# z2 = a1 @ W2 + b2 → dL/da1 = dL/dz2 @ W2ᵀ
dL_da1 = dL_dz2 @ W2.T                       # [4,1]@[1,2] = [4,2]

# ReLU：梯度在负半轴为 0
dL_dz1 = dL_da1 * (z1 > 0).float() # [4,2]

# z1 = x @ W1 + b1，W1 是 [3,2]
dL_dW1 = x.T @ dL_dz1                        # [3,4]@[4,2] = [3,2]
dL_db1 = dL_dz1.sum(0)                       # [2]

print("形状对齐（必须和参数完全一致）:")
print(f"  dL_dW1 {tuple(dL_dW1.shape)} vs W1 {tuple(W1.shape)}")
print(f"  dL_db1 {tuple(dL_db1.shape)} vs b1 {tuple(b1.shape)}")
print(f"  dL_dW2.T {tuple(dL_dW2.T.shape)} vs W2 {tuple(W2.shape)}")
print(f"  dL_db2 {tuple(dL_db2.shape)} vs b2 {tuple(b2.shape)}")

print("\n与 autograd 对比（注意 W2 需要转置）:")
pairs = [("dL_dW1", dL_dW1, W1), ("dL_db1", dL_db1, b1),
         ("dL_dW2", dL_dW2.T, W2),   ("dL_db2", dL_db2, b2)]
for name, mine, param in pairs:
    err = (mine - param.grad).abs().max().item()
    print(f"  {name}: 最大误差 = {err:.1e}")
```

**实测输出**：

```
形状对齐（必须和参数完全一致）:
  dL_dW1 (3, 2) vs W1 (3, 2)
  dL_db1 (2,) vs b1 (2,)
  dL_dW2.T (2, 1) vs W2 (2, 1)
  dL_db2 (1,) vs b2 (1,)

与 autograd 对比（注意 W2 需要转置）:
  dL_dW1: 最大误差 = 0.0e+00
  dL_db1: 最大误差 = 0.0e+00
  dL_dW2: 最大误差 = 0.0e+00
  dL_db2: 最大误差 = 0.0e+00
```

**误差全是 0**（浮点运算顺序一致时）。这证明了你的推导和 autograd 做的是同一件事。

### ⚠️ 手推时我踩的三个坑（重要）

这个实验的价值一半在于踩坑。**三个错误都是我第一次写时犯的**：

**坑 1：忘了 batch 平均的系数**

`loss = (z2-y)**2.mean()` 是对 batch 和输出维都求平均，所以：

$$\frac{\partial L}{\partial z_2} = \frac{2(z_2 - y)}{B}$$

我一开始写成 `2*(z2-y)`，**漏了除以 B=4**，结果所有梯度差 4 倍。

**坑 2：矩阵乘法顺序写反**

$z_1 = x @ W_1$ 中 $W_1$ 是 `[3,2]`（in×out），所以：

$$\frac{\partial L}{\partial W_1} = x^\top \cdot \frac{\partial L}{\partial z_1} \quad (\text{先转 } x)$$

我写成了 `dL_dz1.T @ x`，**结果形状是 [2,3] 而不是 [3,2]**。

**PyTorch 会静默地广播出一个错误结果而不是报错**，所以这个 bug 特别危险——必须打印形状。

**坑 3：`torch.outer` 的参数必须是 1维**

`torch.outer(dL_dz2, a1)` 报错，因为 `dL_dz2` 是 `[4,1]` 而不是 `[1]`。

修正写法是 `dL_dz2.T @ a1`，等价于外积但对形状没要求。

**教训**：推导和代码之间隔着一层形状地狱。**写完推导第一件事是打印 `.shape` 和参数的 `.shape` 对比**，这比什么都重要。

### 实验 2：测量梯度消失

```python
import torch
from torch import nn

def measure_grad_norms(depth, activation='relu'):
    layers, ins = [], 20
    act = nn.ReLU if activation == 'relu' else nn.Sigmoid
    for _ in range(depth):
        layers += [nn.Linear(ins, 20), act()]
        ins = 20
    layers += [nn.Linear(20, 1)]
    model = nn.Sequential(*layers)

    x = torch.randn(64, 20)
    for p in model.parameters():
        p.grad = None
    model(x).sum().backward()

    norms = [p.grad.norm().item() for p in model.parameters()]
    return norms

print("=== ReLU 网络：逐层梯度范数 ===")
for depth in [2, 6, 20]:
    norms = measure_grad_norms(depth)
    print(f"\n深度 {depth}: 首层 {norms[0]:.2e} → 末层 {norms[-1]:.2e}"
          f"  衰减倍数 {norms[0]/norms[-1]:.1f}x")

print("\n=== Sigmoid 网络 ===")
for depth in [2, 6, 20]:
    norms = measure_grad_norms(depth, 'sigmoid')
    print(f"深度 {depth}: 首层 {norms[0]:.2e} → 末层 {norms[-1]:.2e}"
          f"  衰减倍数 {norms[0]/norms[-1]:.1f}x")
```

**你会观察到**：ReLU 网络的梯度衰减远慢于 Sigmoid；层数增加时两边都衰减，但 Sigmoid 更严重。**这就是 ReLU 优于 Sigmoid 的定量证据。**

### 实验 3：残差连接如何消除衰减

```python
import torch
from torch import nn

class Plain(nn.Module):
    def __init__(self, depth, width=20):
        super().__init__()
        self.layers = nn.ModuleList([nn.Linear(width, width) for _ in range(depth)])
    def forward(self, x):
        for l in self.layers: x = torch.relu(l(x))
        return x.sum()

class Res(nn.Module):
    def __init__(self, depth, width=20):
        super().__init__()
        self.layers = nn.ModuleList([nn.Linear(width, width) for _ in range(depth)])
    def forward(self, x):
        for l in self.layers:
            x = torch.relu(l(x) + x)        # ★ 残差连接
        return x.sum()

print(f"{'深度':>6} {'普通网络衰减':>14} {'残差网络衰减':>14}")
for depth in [2, 6, 20, 50]:
    x = torch.randn(64, 20)
    out = []
    for M in [Plain, Res]:
        torch.manual_seed(42); m = M(depth)
        for p in m.parameters(): p.grad = None
        m(x).backward()
        n = [p.grad.norm().item() for p in m.parameters()]
        out.append(n[0] / n[-1])
    print(f"{depth:>6} {out[0]:>13.1f}x {out[1]:>13.1f}x")
```

**你会看到**：深度越大，普通网络的梯度衰减倍数呈指数增长，而残差网络**几乎保持恒定**。这就是 ResNet 能训 100+ 层的定量证据。

---

## 六、自测题

**Q1**：为什么 ReLU 会出现「死神经元」？什么条件下会出现？

<details>
<summary>答案</summary>

**机制**：ReLU 的梯度是 $\text{1}[z>0]$。如果某个神经元对**所有**输入都输出 $z \le 0$，它的梯度永远是 0，参数永远不更新。

**什么条件会触发**：
1. **初始化不当**：权重初始化为全 0 或负偏置过大，初始输出就大面积为负
2. **学习率过大**：一次更新把参数推到负半轴，之后再也回不来
3. **输入分布本身为负**（比如前面接了负偏置、或者数据本身偏负）

**为什么回不来**：一旦某个神经元对所有输入都是负输出，它就不会参与任何有用的计算，**其他神经元也不会因为它而得到有用的梯度**（梯度是累加的，但这个神经元贡献 0），所以整个系统失去了这个神经元。这就是「死」。

**解法**：
- Leaky ReLU：$\max(0.05z, z)$，给负半轴一个小的非零斜率
- 参数化 ReLU（PReLU）：斜率可学习
- 正确初始化（He 初始化，让初始输出正负各半）
- 合适的 lr
</details>

**Q2**：如果网络所有权重都初始化为 0，会发生什么？

<details>
<summary>答案</summary>

**输出恒为 0，且梯度也为 0，训练完全不进行。**

推导：
- 前向：$z = Wx + b$，若 $W=0$ 则 $z=0$（不管 $b$ 多大），所有层输出 0
- 反向：$\frac{\partial L}{\partial W_2} = \frac{\partial L}{\partial z_2} \cdot a_1^\top$，而 $a_1 = 0$，所以 $\frac{\partial L}{\partial W_2} = 0$
- 逐层回推，所有梯度都是 0

**对称性问题**：如果所有神经元用同一个初始化且输入也一样，它们的梯度完全相同 → 参数更新也相同 → **永远保持对称**，等效于一个神经元。

**注意区分**：
- 权重 W **不能**初始化为 0
- 偏置 b **可以**初始化为 0（因为它不造成对称性问题）
- **最后一个全连接层的 bias 可以初始化为 0，但它的 weight 初始化为 0 会导致 logits 全相同 → 初始 loss 就是 $\log K$**

这也是为什么 PyTorch 里的 `nn.Linear` 默认 bias=True 且初始化均匀。
</details>

**Q3**：梯度裁剪是把超过阈值的部分「截断」，为什么等比缩放（全梯度乘一个系数）更好？

<details>
<summary>答案</summary>

**逐元素裁剪（clip by value）**：
$$g_i \leftarrow \max(-\epsilon, \min(\epsilon, g_i))$$

这会**改变梯度的方向**。比如原梯度是 $(0.1, 10.0)$，裁剪后是 $(0.1, 1.0)$，方向从近似 y 轴变成更接近 x 轴。**优化的方向被改掉了**——这违反了「梯度下降沿最陡下降方向」的前提。

**等比缩放（clip by norm）**：
$$\hat{g} = g \cdot \frac{\epsilon}{\|g\|}$$

所有分量乘同一个系数，**方向完全不变**，只是整体步长被限制。

**实现**：

```python
torch.nn.utils.clip_grad_norm_(
    model.parameters(),
    max_norm=1.0,
    error_if_nonfinite=False,   # nan 时跳过
)
```

**顺便解释一下 clip 的另一个作用**：当出现 `nan`（数值爆炸的极端情况）时，`clip_grad_norm_` 遇到 nan 会把整个梯度设为 0（见源码），相当于「跳过这一步」，避免 nan 污染参数。这给了训练一层保护。
</details>

**Q4**：一个网络在前 10 层梯度正常，第 50 层开始梯度极小。用什么手段能诊断出根本原因？

<details>
<summary>答案</summary>

**先做逐层梯度测量**（实验 2 的方法），定位衰减从哪一层开始。

**然后分类可能原因**：

| 原因 | 判据 | 解法 |
|---|---|---|
| **深层 tanh/sigmoid** | 衰减从第一个非线性层就开始 | 换 ReLU/GELU |
| **初始化太小** | 各层梯度都在衰减，且权重值本身很小 | 换 He 初始化 |
| **权重衰减过强** | 权重值被压得很小 → 梯度 = W · (上游) 也很小 | 调小 weight_decay |
| **残差路径缺失** | 纯串行结构，理论上就衰减 | 加残差连接 |
| **没有归一化** | 深层训练慢且梯度不稳 | 加 LayerNorm |

**最快的验证方法**：做一个受控实验。取一个纯 ReLU + He 初始化的深层 MLP，逐层打印梯度。**如果这个基线是健康的**，说明问题在你的具体设计（初始化、归一化、结构）；**如果基线也不健康**，那就是深度本身带来的，需要残差连接。

```python
# 最小复现
model = nn.Sequential(*[nn.Sequential(nn.Linear(64,64), nn.ReLU()) for _ in range(50)])
```
</details>

---

**下一篇** → [归一化：从 BatchNorm 到 RMSNorm](/guides/deep-learning/part2-dl-principles/06-normalization)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part1-ml-basics/04-optimizers)
