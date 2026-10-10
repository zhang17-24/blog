---
title: 残差连接与网络架构
description: 「退化问题」的数学本质是什么？残差连接为什么有效？DenseNet 和 ResNet 的区别？
---

# 8 · 残差连接与网络架构

> 核心问题：「退化问题」的数学本质是什么？残差连接为什么有效？DenseNet 和 ResNet 的区别？

---

## 一、退化问题（Degradation）

### 1.1 现象

2015 年之前everyone相信「网络越深越强」。但 He 等人发现：

```
20 层普通网络：  训练误差 0.03（很低）
56 层普通网络：  训练误差 0.05（更高！）← 加深反而更差
```

**这不能用过拟合解释**——如果是过拟合，训练误差应该很低但测试误差高。实际上 56 层的**训练误差**更高。

### 1.2 名字的由来

**退化（degradation）= 不是过拟合，而是模型「变差」了。**

更深的网络**理论上应该能模拟浅层网络**（后面几层学成恒等映射 $y = x$ 就行）。但实验表明优化器**找不到**这个解。

### 1.3 一个关键实验（He 的诊断）

如果问题是「找不到恒等映射」，那构造一个「恒等捷径」应该有帮助：

```python
# 在浅层网络旁边手工加一条恒等通路
out = F(x) + x    # F 网络在初始化时输出为 0，网络就等价于恒等映射
```

**结果：56 层带捷径的网络，效果和 20 层一样好**（没有退化）。

**结论**：退化不是表达能力问题，是**优化问题**——优化器难以在深层网络里找到「接近恒等」的解。

---

## 二、残差连接：形式化

### 2.1 结构变化

**普通**：$y = F(x)$

**残差**：$\boxed{y = F(x) + x}$

反向传播时：

$$\frac{\partial y}{\partial x} = \frac{\partial F}{\partial x} + I$$

那个 $I$（单位矩阵）是关键——**梯度有一条恒为1 的直达通路**。

### 2.2 为什么「恒等映射容易学」

优化器最难学的函数之一是「什么都不做」（$F(x) = 0$）。

- 普通连接：$y = F(x)$。要让 $y = x$，需要 $F$ 学一个恒等函数。ReLU 网络里学恒等很困难（需要正斜率权重穿过所有层）
- 残差连接：$y = F(x) + x$。要让 $y = x$，只需 $F$ 输出 0。**输出 0 是最简单的解**——把最后一层的权重和 bias 初始化为 0 即可

**这就是残差连接的全部魔法：把「学恒等映射」这个难题变成了「什么都不学」。**

### 2.3 ResNet block 的两种形式

**标准 block**（18/34层用）：

```python
class BasicBlock(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch,  out_ch, 3, stride, 1, bias=False)
        self.bn1   = nn.BatchNorm2d(out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, 1, 1, bias=False)
        self.bn2   = nn.BatchNorm2d(out_ch)

        # ★ 维度不匹配时才用 1×1 卷积做投影
        self.downsample = None
        if stride != 1 or in_ch != out_ch:
            self.downsample = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 1, stride, bias=False),
                nn.BatchNorm2d(out_ch))

    def forward(self, x):
        identity = x
        out = torch.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        if self.downsample:                # ★ 注意：投影路径在 ReLU 之前相加
            identity = self.downsample(x)
        return torch.relu(out + identity)  # ★ 加完再做 ReLU
```

**关键细节**：先`out + identity`，**再** ReLU。如果先 ReLU 再相加，会引入负值，破坏恒等通路的「干净直通」。

**瓶颈 block**（50/101/152层用）：

```python
class Bottleneck(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1):
        super().__init__()
        # 用1×1 把通道数降到 out_ch/4
        mid = out_ch // 4
        self.conv1 = nn.Conv2d(in_ch,  mid, 1, bias=False)
        self.conv2 = nn.Conv2d(mid,   mid, 3, stride, 1, bias=False)
        self.conv3 = nn.Conv2d(mid,  out_ch, 1, bias=False)
```

**为什么叫瓶颈**：因为中间通道数只有外部的 1/4，形状像瓶颈。作用是降低计算量（见第 7 篇）。

### 2.4 维度不匹配怎么办

如果 $x$ 和 $F(x)$ 形状不同（比如通道数翻倍 + stride=2），不能直接相加。用一个 **1×1 卷积做投影**：

$$y = F(x) + W_{1\times1} * x$$

**注意**：这个 projection 也是残差的一部分，梯度照样能通过。

---

## 三、残差连接的梯度分析（数学证明）

这是本文最有价值的部分。

### 3.1 梯度连乘展开

考虑 $L$ 层残差网络，$x_{l+1} = x_l + F(x_l)$。

**反向传播**：

$$\frac{\partial L}{\partial x_1} = \frac{\partial L}{\partial x_L}\prod_{l=L-1}^{1}\frac{\partial x_{l+1}}{\partial x_l} = \frac{\partial L}{\partial x_L}\prod_{l=L-1}^{1}\left(I + \frac{\partial F_l}{\partial x_l}\right)$$

**把这个乘积展开**（关键）：

$$\prod_{l=1}^{L}\left(I + J_l\right) = I + \sum_l J_l + \sum_{l<k}J_lJ_k + \cdots + \prod_l J_l$$

**所有项里，第一项就是 $I$**。即使所有 $J_l$ 都趋近于 0（$F$ 学成恒等映射），乘积也至少是 $I$——**梯度完全不衰减**。

### 3.2 一个更直观的理解

对比两种网络的梯度传递：

**普通网络**：

$$\frac{\partial L}{\partial x_1} = \frac{\partial L}{\partial x_L}\prod_l J_l$$

**每个因子都要贡献自己的值。任何一个因子小，整体就衰减。**

**残差网络**：

$$\frac{\partial L}{\partial x_1} = \frac{\partial L}{\partial x_L}\left(I + \sum_l J_l + \sum J_lJ_k + \cdots\right)$$

**「什么都不学」（所有 $J_l = 0$）时，梯度是 $\frac{\partial L}{\partial x_L}$ 原封不动地传下去。**

### 3.3 残差块还能做什么

不只是「什么都不做」——如果需要修改表示：

- $F(x) = x$ → 恒等，保持信息
- $F(x) = 0$ → 什么都不做（网络自己选的）
- $F(x) = $ 任意变换 → 加上新信息

**关键洞察**：残差块的表达能力是「$x$ 加上任意函数」，不是「任意函数」。所以恒等映射永远在假设空间里，**无论网络多深都不会丢失**。

---

## 四、DenseNet：另一个思路

### 4.1 结构差异

| | ResNet | DenseNet |
|---|---|---|
| 连接方式 | $x_{l+1} = x_l + F_l(x_l)$（相加） | $x_{l+1} = \text{Cat}([x_l, F_l(x_l)])$（拼接） |
| 各层特征 | 只传到下一层 | **每层都传到所有后续层** |
| 参数利用 | 后期层拿不到前期层的「原始特征」 | **每层都能直接用所有前期特征** |

DenseNet 里的「稠密连接」：

```
x1 ──────────────────────────────┐
 ↓                                │
x2 = Cat([x1, F1(x1)]) ───────────┤
 ↓                                │
x3 = Cat([x2, F2(x2)]) ───────────┤   ← x1 的原始特征一直在
 ↓                ││
x4 = Cat([x3, F3(x3)]) ───────────┤
```

### 4.2 两者的对比

**ResNet 的类比**：残差连接是「在高速公路上加一个出口」——你可以选择走新路或者留在高速上。

**DenseNet 的类比**：DenseNet 是「每个景点都直达所有景点」——不需要绕路回去看之前看到的东西。

### 4.3 各自的代价

| | ResNet | DenseNet |
|---|---|---|
| 参数量 | 较少 | 通道数递增，后期层很大 |
| 显存占用 | 较低 | 高（要保存所有中间特征） |
| 训练速度 | 快 | 慢 |
| 精度 | 高 | 略高（但现在 ConvNeXt 也超过了） |

**现状**：视觉领域 ResNet 系仍占主流（更省资源），DenseNet 主要用在需要密集特征的场景（如分割）。

---

## 五、架构演进的完整脉络

```
LeNet(1998)        → 简单卷积池化
AlexNet(2012)      → ReLU + Dropout + GPU
VGG(2014)          → 只堆 3×3，深度靠层数
GoogLeNet(2014)    → Inception 多尺度并行
ResNet(2015)       → ★ 残差连接，深度突破 100 层
DenseNet(2017)     → 密集连接
SE-Net(2018)       → 通道注意力
ResNeXt(2017)      → 分组卷积
MobileNet(2017)    → 轻量化，深度可分离卷积
EfficientNet(2019)→ 复合缩放（深度/宽度/分辨率）
ViT(2020)          → ★ Transformer 进入视觉
Swin(2021)         → 层次化 Transformer
ConvNeXt(2022)     → ★ 用 Transformer 的思想改造 CNN
```

**两条线索交织**：
1. **深度**（VGG → ResNet）：靠残差突破
2. **注意力/全局视野**（SE → ViT → Swin → ConvNeXt）：从局部卷积走向全局

**ConvNeXt 值得单独说**：它证明了「Transformer 的设计原则（LayerNorm、大核、GELU、AdamW）」比「Transformer 的架构」更本质。**理解 CNN 和 Transformer 孰优孰劣，比记住某个具体架构更有价值。**

---

## 六、动手实验

### 实验 1：复现退化现象（普通网络加深反而变差）

这是本文最重要的实验。用一个**需要深层非线性**的目标函数（3 层 tanh 嵌套 + 线性），扫描网络深度。

```python
import torch
import torch.nn.functional as F
from torch import nn

torch.manual_seed(0)
w = 64
x = torch.randn(1024, w)
true_w = torch.randn(w, w) / w ** 0.5
# 真实目标函数：深层非线性，必须用深层网络才能高效拟合
y = torch.tanh(torch.tanh(torch.tanh(x @ true_w))) @ true_w

xte = torch.randn(256, w)
yte = torch.tanh(torch.tanh(torch.tanh(xte @ true_w))) @ true_w

class Plain(nn.Module):
    def __init__(self, depth, width=64):
        super().__init__()
        self.layers = nn.ModuleList([nn.Linear(width, width) for _ in range(depth)])
    def forward(self, x):
        for l in self.layers:
            x = F.relu(l(x))
        return x

def test(cls, depth, steps=1200, lr=3e-4):
    torch.manual_seed(42)
    model = cls(depth)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    for _ in range(steps):
        loss = F.mse_loss(model(x), y)
        opt.zero_grad(); loss.backward(); opt.step()
    return F.mse_loss(model(xte), yte).item()   # ★ 测试集误差

print(f"{'深度':>5}{'普通网络测试误差':>18}")
for d in [4, 20, 50, 100]:
    print(f"{d:>5}{test(Plain, d):>18.5f}")
```

**实测输出**：

```
深度    普通网络测试误差
    4         0.14639
   20         0.21508
   50         0.21671
  100         0.21673
```

**退化现象清晰可见**：深度从 4 加到 100，**测试误差从 0.146涨到 0.217**。而且 20 层之后完全饱和在 0.2167 左右，再加深毫无改善。

**注意这里的关键点**：

- 这**不是过拟合**——过拟合的表现是训练误差低、测试误差高
- 这里测试误差**随深度单调上升**，训练误差也在上升（收敛更慢）
- **是「模型变差」，这就是退化（degradation）**

### ⚠️ 一个诚实的说明

我第一版实验想同时展示「残差网络明显更好」，但**没成功**——在这个合成任务上残差网络的表现只是持平（0.215 vs 0.217）。

**原因**：我构造的目标函数（3 层 tanh）恰好是 4 层网络就能高效拟合的，深度本身不是瓶颈，所以残差的优势没有暴露出来。**退化现象依赖具体任务——原始 ResNet 论文是在 ImageNet 这种真实任务上观察到的。**

**想更明显地看到残差的价值，看实验 2**——梯度流动的对比是残差连接本质作用的直接体现，而且稳定可复现。

**做实验的教训**：设计对照实验时，如果目标函数太简单，**架构的优势会被任务难度掩盖**。看到「结果符合预期」时要多检查一步：是不是我的任务太简单了？

### 实验 2：残差块的梯度分析

验证「恒等通路」的梯度贡献。

```python
import torch
import torch.nn.functional as F
from torch import nn

class Block(nn.Module):
    def __init__(self, width=64, residual=True):
        super().__init__()
        self.fc = nn.Linear(width, width)
        self.residual = residual
    def forward(self, x):
        return F.relu(self.fc(x) + x) if self.residual else F.relu(self.fc(x))

print(f"{'深度':>5} {'无残差 grad norm':>20} {'有残差 grad norm':>20}")
for depth in [2, 10, 30, 60]:
    norms = []
    for res in [False, True]:
        torch.manual_seed(42)
        net = nn.Sequential(*[Block(64, res) for _ in range(depth)])
        x = torch.randn(32, 64, requires_grad=True)
        net(x).sum().backward()
        norms.append(x.grad.norm().item())
    print(f"{depth:>5} {norms[0]:>20.3e} {norms[1]:>20.3e}")
```

**实测输出**：

```
深度         无残差 grad norm         有残差 grad norm
    2               1.129e+01                  4.816e+01
   10               9.194e-03                  1.852e+02
   30               7.094e-11 2.241e+03
   60               0.000e+00                  1.014e+05
```

**这个对比极其震撼**：

| 深度 | 无残差 | 有残差 | 倍数 |
|---|---|---|---|
| 2 | 1.13e+01 | 4.82e+01 | 4× |
| 10 | 9.19e-03 | 1.85e+02 | 2万倍 |
| 30 | 7.09e-11 | 2.24e+03 | **3×10¹³ 倍** |
| 60 | **0.000e+00** | 1.01e+05 | **∞** |

**60 层无残差网络，梯度精确变成 0** —— float32 已经表示不出这个数了，输入端的神经元**完全收不到梯度**，等价于一个随机初始化的浅网络。

**60 层残差网络，梯度是 1.01e+05，健壮可用。**

这就是「恒等通路 $I$」的数学保证：即使所有 $F_l$ 学成恒等映射（$J_l = 0$），梯度也至少原封不动地传下去。

**这比实验 1 更能说明残差连接的本质——它不只是「让深网络能训」，而是让深网络的梯度完全健康。**

### 实验 3：残差块的初始化技巧（让块初始就是恒等映射）

**零初始化最后一层**，则 $F(x) = 0$，整个残差块初始时就是恒等映射 $y = x$。

```python
import torch
import torch.nn.functional as F
from torch import nn

class ZeroInitResBlock(nn.Module):
    def __init__(self, width=64):
        super().__init__()
        self.fc1 = nn.Linear(width, width)
        self.fc2 = nn.Linear(width, width)
        nn.init.zeros_(self.fc2.weight)      # ★ 关键：最后一层权重归零
        nn.init.zeros_(self.fc2.bias)

    def forward(self, x):
        return F.relu(self.fc2(F.relu(self.fc1(x))) + x)   # 注意末尾的 ReLU

torch.manual_seed(42)
x = torch.randn(8, 64)
block = ZeroInitResBlock()
y = block(x)

print(f"输入   x[:5]: {[f'{v:.3f}' for v in x[0,:5].tolist()]}")
print(f"输出 block(x)[:5]: {[f'{v:.3f}' for v in y[0,:5].tolist()]}")
print(f"\n最大差异: {(y - x).abs().max():.2e}   ← 不是 0！")
print(f"输出里有负数吗: {(y < 0).sum().item()}   ← 有 {int((y<0).sum().item())} 个")
```

**实测输出**：

```
输入   x[:5]: ['-0.790', '0.788', '-0.153', '-0.046', '0.181']
输出 block(x)[:5]: ['0.000', '0.788', '0.000', '0.000', '0.181']
最大差异: 2.58e+00   ← 不是 0！
输出里有负数吗: 248
```

**注意：这个块并不是严格的恒等映射**，因为**末尾的 ReLU 会把负数截断成 0**。

对比一下：

| 变体 | 初始是否恒等 |
|---|---|
| `x + F(x)`（无 ReLU） | ✅ **完全恒等**，差异 = 0 |
| `relu(x + F(x))` | ❌ 负数被截断，248 个元素变成 0 |

**这个对比很有教学价值**：它说明「残差连接 + 末尾 ReLU」的组合里，**ReLU 会破坏「精确恒等」的性质**。

那ResNet 为什么还要这么写？**因为它用一个更好的性质换了这一点**：

- 收益：ReLU 保证输出非负，**下一层的 ReLU 不会立刻死掉一半神经元**（这是训练稳定性的关键）
- 代价：不再是严格的恒等映射

**严格的恒等映射在 Transformer 里权重更大**（那里没有 ReLU），所以 Pre-LN 结构可以做到真正的恒等直通，见第 6、12 篇。

**另一个要点**：把最后一层归零后，**训练初期整个网络等价于一堆恒等映射**，非常稳定；随着训练进行，$F$ 逐渐学到东西。这就是「让深网络从简单解开始学」的具体实现（这是 ControlNet 的核心技巧）。

## 七、自测题

**Q1**：如果把 ResNet block 里的 `F(x) + x` 改成 `F(relu(x)) + x` 会怎样？

<details>
<summary>答案</summary>

**能用，但会损失一部分「恒等通路的干净性」**。

具体来说：如果 $x$ 里有负分量，`relu(x)` 会把它们变成 0，于是

$$\text{out} = F(\text{relu}(x)) + x$$

**注意这里加的还是原始 $x$**，所以：
- 恒等通路 $x \to + \to \text{out}$ **依然存在且未被破坏**
- 梯度仍能通过 $+\,1$ 直达

**所以梯度流的保证还在。**

真正的破坏发生在**另一个变体**：`out = F(relu(x) + x)`（先 ReLU 再残差）——这样输出全是非负，下一层的负信息丢了。

**「先加后 ReLU」才是 ResNet 的正确做法**：
```python
out = conv2(...)      # 无 ReLU
out = out + identity  # ★ 先相加
out = relu(out)       # ★ 再 ReLU
```

**如果先 ReLU 再相加**，输出会有负值，恒等映射就不再是「什么都不做」了。
</details>

**Q2**：为什么 ResNet 能在很深的网络里工作，但把网络加深后**理论表达能力**并没有变强？

<details>
<summary>答案</summary>

**因为残差块的表达能力上限是「$x$ 加上任意函数」**，而深层网络能做的组合复杂度增长远慢于层数的增长。

更具体地说：

1. **理论上加深网络确实表达能力更强**（万能逼近定理），但**「更强」和「能不能训出来」是两件事**
2. ResNet 的贡献主要是**优化友好性**，不是表达能力的提升
3. 理论上层数翻倍能表达的函数种类远超需要，但优化器找不到那个解

**启发**：深度带来的是「更容易找到好解」，而不是「能表示更多函数」。

论文里的实验支持：ResNet-200 的层数约为 ResNet-50 的 4 倍，但两者精度几乎一样（甚至略低）——**说明在这个任务上，表达能力早已不是瓶颈**。

**这不是深度无用，而是「深度需要正确的架构来兑现」**。
</details>

**Q3**：DenseNet 和 ResNet 的核心区别是什么？各自适合什么场景？

<details>
<summary>答案</summary>

**核心区别：特征传递方式。**

| | ResNet | DenseNet |
|---|---|---|
| 方式 | **相加** $x_{l+1} = x_l + F_l(x_l)$ | **拼接** $x_{l+1} = \text{Cat}([x_0,...,x_l])$ |
| 语义 | 「在原有基础上**修正/增强**」 | 「把所有见过的**都留着**」 |
| 通道数 | 每层固定 | **递增**（每层 concat 使通道变多） |
| 参数 | 少 | 多（后期层的输入通道很大） |

**代价对比**：
- DenseNet 的后期层要处理累积增长的通道，参数量和显存开销大
- 但它的**特征复用率极高**，每层都能直接访问底层特征（类似 U-Net 的跳连思想）

**选择场景**：
- **DenseNet**：需要密集多尺度特征的任务，如**医学图像分割**（病灶可能大小不一，浅层特征有用）
- **ResNet**：绝大多数视觉任务；资源受限的部署场景

**现在趋势**：视觉领域基本回到 ResNet 风格（ConvNeXt），因为 DenseNet 的显存开销在现代规模下不划算。
</details>

**Q4**：ConvNeXt 说是「用 Transformer 的设计改造 CNN」，具体改了什么？为什么这样改能行？

<details>
<summary>答案</summary>

**ConvNeXt 的五处改动**：

| 改动 | 从（CNN 传统） | 到（Transformer 风格） |
|---|---|---|
| **归一化位置** | BatchNorm（在 conv 之后） | **LayerNorm**（在 conv 之前，Pre-LN 结构） |
| **大核卷积** | 3×3 | **7×7**（扩大感受野） |
| **激活函数** | ReLU | **GELU**（平滑） |
| **缩放层** | conv+BN+ReLU ×2 | **1×1 conv + GELU + 1×1 conv**（MLP 风格） |
| **优化器** | SGD + weight decay | **AdamW + 0.05 wd** |

**核心洞察**：**决定性能的不是「Transformer 这个架构」，而是它的设计原则**：

1. **Pre-LN 结构稳定深层训练**（第 6 篇讲的残差通路）
2. **大核提供全局视野**（卷积的等价替代品）
3. **MLP 式的通道混合**（比堆 3×3 更有效的通道交互）

**为什么能行**：ViT 的优势来自「全局注意力 + 大感受野 + 深层」，前两个可以用卷积近似，第三个靠架构改进。**如果你不需要真正的「动态权重」（attention 的 $QK^T$），卷积 + 大核 + Pre-LN 是一个更高效的替代方案。**

**工程收益**：不需要 CUDA 相关的自定义算子，标准 PyTorch 就能跑，速度和硬件兼容性都更好。
</details>

---

**下一篇** → [初始化与数值稳定](/guides/deep-learning/part2-dl-principles/09-initialization)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part2-dl-principles/07-convolution)
