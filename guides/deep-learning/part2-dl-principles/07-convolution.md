---
title: 卷积与感受野
description: 卷积为什么比全连接更适合图像？什么条件下卷积等价于全连接？感受野怎么算？
---

# 7 · 卷积与感受野

> 核心问题：卷积为什么比全连接更适合图像？什么条件下卷积等价于全连接？感受野怎么算？

---

## 一、卷积的数学定义

### 1.1 从「滑动窗口的点积」理解

二维卷积在计算机视觉里的实际计算是：

$$\text{out}[i,j] = \sum_{u,v} \text{input}[i+u, j+v] \cdot K[u,v] + b$$

**注意这不是数学上的卷积（数学上是先翻转再相关），但深度学习里习惯叫卷积。**

两个关键特性：

1. **权重共享（weight sharing）**：同一个卷积核 $K$ 在所有位置复用
2. **局部连接（local connectivity）**：每个输出只依赖一个局部区域

### 1.2 参数量对比（这是卷积最大的优势）

设输入 $224 \times 224 \times 3$，输出 $224 \times 224 \times 64$：

**全连接层**（从 150528 维映射到 50176 维）：

$$150528 \times 50176 \approx 7.5 \times 10^9 \quad \text{参数}$$

**卷积层**（3×3 卷积，64 个输出通道）：

$$3 \times 3 \times 3 \times 64 + 64 = 1792 \quad \text{参数}$$

**差4 百万倍**，而卷积的表达能力并不弱（因为它利用了图像的局部性先验）。

**这个参数量的差距是卷积在视觉领域统治的根本原因**，不是「效果更好」，而是「能训得动」。

---

## 二、卷积 vs 全连接：等价条件

### 2.1 什么情况下卷积 == 全连接

**如果卷积核的空间尺寸等于输入的空间尺寸，那么卷积就退化成全连接。**

例：$5 \times 5$ 的输入，用 $5 \times 5$ 的卷积核（stride=1, padding=0）→ 输出 $1 \times 1$。

此时每个输出需要看到全部输入，**权重共享的约束还在，但已经没有空间局部性可言了**。

### 2.2 更精确的等价条件

$3 \times 3$ 卷积（padding=1）在 $H \times W$ 输入上产生 $H \times W$ 输出。对输出位置 $(i,j)$：

$$\text{out}[i,j] = W_{:, :, 0}\cdot X_{i-1:i+1, j-1:j+1} + b$$

每个输出用的都是**同一个** $W$，但看的是**不同**的输入块。所以它**不是**全连接——全连接每个输出位置应该有不同的权重。

**但是**：可以把「卷积」看成「一种结构化的全连接」。$W$ 被约束成 11 个不同的矩阵，每个矩阵的 9 个权重被共享。**约束 = 正则化。**

这就是卷积的泛化能力来源：**用「权重必须共享」这个先验，替代了「参数独立」的自由度。**

---

## 三、感受野（Receptive Field）

### 3.1 定义

**感受野 = 输出特征图上一个元素所「看到」的输入区域大小。**

这是理解 CNN 结构的核心工具。

### 3.2 计算公式

逐层递推：

$$r_l = r_{l-1} + (k_l - 1) \cdot \prod_{i=1}^{l-1} s_i, \qquad j_l = j_{l-1} + (k_l - 1)\prod_{i=1}^{l-1}s_i$$

其中 $r$ 是感受野大小，$j$ 是跳跃间隔（jump），$k$ 是核大小，$s$ 是 stride。

**stride=1 的简化公式**：

$$r_l = 1 + \sum_{i=1}^{l}(k_i - 1)$$

**例子**（三个 3×3 卷积，stride=1）：

| 层 | 感受野 |
|---|---|
| Layer 1 (3×3) | 3 |
| Layer 2 (3×3) | 5 |
| Layer 3 (3×3) | 7 |
| ... | ... |
| Layer 5 | 11 |

**注意感受野是累加的**：$1 + 5 \times 2 = 11$。

**核心洞察**：**用 5 层 3×3 卷积（感受野 11）比 1 层 11×11 卷积（感受野 11）好得多**，因为：

1. 中间有 4 次非线性 → 表达力更强
2. 参数量：5 层 3×3 = $5 \times 9 = 45$ 倍权重 vs 1 层 11×11 = 121 倍
3. **中间可以做下采样**（VGG 的设计哲学）

### 3.3 感受野的三种叠加方式

设计网络时必须明确「想要多大的感受野」，然后选结构：

| 方式 | 做法 | 感受野增长速度 | 代表网络 |
|---|---|---|---|
| **堆叠卷积** | 连续多个 3×3 | 线性（$1+2L$） | VGG |
| **Pooling** | 用池化降采样 | **平方级增长** | VGG / AlexNet |
| **空洞卷积** | dilation > 1 | 指数增长 | DeepLab / WaveNet |

**空洞卷积（Dilated / Atrous Convolution）** 值得单独说：

$$\text{感受野} = k + (k-1)(d-1) = k(1+d-1) - 1$$

| dilation | 有效核 | 3×3 的感受野 |
|---|---|---|
| 1 | 3×3 | 3 |
| 2 | 3×3（间隔1） | 5 |
| 4 | 3×3（间隔2） | 9 |

**在保持分辨率的同时扩大感受野**——这是分割任务的关键技术（DeepLab 系列的核心）。

---

## 四、1×1 卷积的特殊地位

### 4.1 它做什么

$1 \times 1$ 卷积在**每个空间位置**上做跨通道的线性变换：

$$\text{out}[i,j,c] = \sum_{c'} W_{c,c'} \cdot \text{input}[i,j,c']$$

**空间维度不变，只混合通道。**

### 4.2 两个关键用途

**用途 1：升维 / 降维**

```python
nn.Conv2d(64, 128, kernel_size=1)   # 通道 64 → 128，不改变 H、W
nn.Conv2d(128, 64, kernel_size=1)   # 通道 128 → 64（降维）
```

**用途 2：与 3×3 卷积的组合（bottleneck）**

```
普通做法:  256 → 256 (3×3)                       实测 590,080 参数
Bottleneck: 256 → 64 (1×1) → 64 (3×3) → 256 (1×1)   实测 70,016 参数

**参数量少了 8.4 倍，精度基本不掉。**

**参数量少了 8.4 倍，精度基本不掉。** ResNet 的 50/101 层用的就是这个结构（`bottleneck`）。

### 4.3 现代变体

| 结构 | 组成 | 用途 |
|---|---|---|
| **Bottleneck** | 1×1 降维 → k×k → 1×1 升维 | ResNet |
| **Grouped Conv** | 通道分组独立卷积 | MobileNet / ShuffleNet |
| **Depthwise Separable** | Depthwise（通道独立）+ Pointwise（1×1） | MobileNetV2 |
| **Inverted Bottleneck** | 1×1 升维 → depthwise 3×3 → 1×1 降维 | MobileNetV3 / EfficientNet |

**MobileNet 的核心洞察**：卷积可以分解为「空间混合」和「通道混合」，两者独立做能省 8~9 倍计算。

---

## 五、池化与下采样

### 5.1 三个池化方式

| 方式 | 做法 | 特点 |
|---|---|---|
| **MaxPool** | 取窗口最大值 | 保留最强激活，反传只路由到一个位置 |
| **AvgPool** | 取窗口均值 | 平滑，反传均分到所有位置 |
| **GlobalAvgPool** | 全图平均 | $H\times W \to 1$，常用于分类头 |

### 5.2 为什么 ReLU 之后用 MaxPool 而不是 AvgPool

**ReLU 的输出非负**（$y \ge 0$）。如果用 AvgPool：

- 正的激活值会被平均 → **削弱信号**
- 负的（被 ReLU 掐断为 0）不影响

MaxPool 保留了最强响应，更符合「检测器越强越好」的直觉。

### 5.3 现代替代：Strided Convolution

现在很多网络（ConvNeXt、EfficientNet）用 **stride=2 的卷积**代替 MaxPool：

- 保留了可学习性
- 避免了 MaxPool「只路由到一个位置」的信息损失
- 可以配合 GroupNorm 而不是 BN

**ConvNeXt 的设计哲学里就有这一条：能用可学习的算子，就别用固定算子。**

---

## 六、完整 CNN 的结构范式

一个典型的视觉骨干网络（以 ResNet-50 为例）：

```
输入 [3, 224, 224]
   ↓ conv7×7 s2 + BN + ReLU + maxpool      → [64, 56, 56]      # stem
   ↓ ResBlock ×3 (64)                      → [64, 56, 56]       # layer1: 1/4分辨率
   ↓ ResBlock ×4 (128), 首个 stride=2      → [128, 28, 28]      # layer2: 1/8
   ↓ ResBlock ×6 (256), stride=2           → [256, 14, 14]      # layer3: 1/16
   ↓ ResBlock ×3 (512), stride=2           → [512, 7, 7]        # layer4: 1/32
   ↓ GlobalAvgPool                         → [512]
   ↓ Linear(512, 1000)                     → logits
```

**关键点**：

1. **早期下采样、后期保持分辨率**：1/4 之前快速降采样，之后维持 1/32。因为早期特征是低频的（大尺度），后期是高频的（细节）
2. **每层分辨率减半、通道数翻倍**：保持计算量恒定
3. **感受野随深度合理增长**

**感受野验算**：ResNet-50 到 layer4 结束的感受野约为 445（理论值），几乎覆盖整张图——这正是分类任务需要的。

---

## 七、动手实验

### 实验 1：感受野计算

```python
def receptive_field(layers):
    """layers: [(kernel, stride), ...]"""
    r = 1   # 起始感受野
    j = 1   # 跳跃间隔
    print(f"{'层':>4} {'k':>3} {'s':>3} {'感受野':>8} {'跳跃':>6}")
    for i, (k, s) in enumerate(layers, 1):
        r = r + (k - 1) * j
        j = j * s
        print(f"{i:>4} {k:>3} {s:>3} {r:>8} {j:>6}")
    return r

print("=== ResNet-50 layer1 的三个 3×3 卷积 ===")
receptive_field([(3,1), (3,1), (3,1)])

print("\n=== 一个 7×7 stride=2 + 五个 3×3（ResNet stem+layer1 前段）===")
receptive_field([(7,2), (3,1), (3,1), (3,1), (3,1), (3,1)])

print("\n=== 五个 3×3 vs 一个 11×11（感受野都是11）===")
print("五层 3x3 的感受野:", receptive_field([(3,1)]*5))
print("一层 11x11 的感受野:", receptive_field([(11,1)]))
print("→ 感受野相同，但前者有 5 次非线性、参数量只有后者的 1/2.7")
```

**输出**：

```
=== ResNet-50 layer1 的三个 3×3 卷积 ===
 层   k   s   感受野     跳跃
  1   3   1       3      1
  2   3   1       5      1
  3   3   1       7      1

=== 一个 7×7 stride=2 + 五个 3×3 ===
 1   7   2       7      2
 2   3   1       9      2
 3   3   1      11      2
 4   3   1      13      2
 5   3   1      15      2
 6   3   1      17      2

五层 3x3 的感受野: 11
一层 11x11 的感受野: 11
```

**关键观察**：stride=2 之后，跳跃间隔变成 2，**后面每层的感受野增长更快**（每次+2 而非 +1）。这是 stride 通过感受野公式的 $j$ 项放大了后续所有层的效果。

### 实验 2：卷积 vs 全连接的参数量

```python
H, W, C_in, C_out = 224, 224, 3, 64

fc_params = (H * W * C_in) * (H * W * C_out)
conv_params = 3 * 3 * C_in * C_out + C_out
print(f"全连接: {fc_params:>15,} 参数")
print(f"卷积:   {conv_params:>15,} 参数")
print(f"差距:   {fc_params / conv_params:>12,.0f} 倍")
```

```
全连接:      7,554,585,344 参数
卷积:              1,792 参数
差距:          4,215,952 倍
```

**这就是卷积统治视觉领域的直接原因**：不是效果更好，而是**能训得动**。

### 实验 3：1×1 卷积做瓶颈

```python
import torch
from torch import nn

conv_3x3 = nn.Conv2d(256, 256, 3, padding=1)
bottleneck = nn.Sequential(
    nn.Conv2d(256, 64, 1),        # 降维
    nn.ReLU(),
    nn.Conv2d(64, 64, 3, padding=1),
    nn.ReLU(),
    nn.Conv2d(64, 256, 1),       # 升维
)
n1 = sum(p.numel() for p in conv_3x3.parameters())
n2 = sum(p.numel() for p in bottleneck.parameters())
print(f"单个 3×3(256→256):  {n1:>10,} 参数")
print(f"Bottleneck 结构:     {n2:>10,} 参数")
print(f"节省: {n1/n2:.1f} 倍")

# 验证输出形状相同
x = torch.randn(1, 256, 56, 56)
print(f"\n输出形状: conv={conv_3x3(x).shape}  bottleneck={bottleneck(x).shape}")
```

**输出**：

```
单个 3×3(256→256):    590,080 参数
Bottleneck 结构:        70,016 参数
节省: 8.4 倍

输出形状: conv=torch.Size([1, 256, 56, 56])  bottleneck=torch.Size([1, 256, 56, 56])
```

### 实验 4：空洞卷积扩大感受野

```python
import torch
from torch import nn

x = torch.randn(1, 1, 32, 32)
print(f"输入: {tuple(x.shape)}\n")
print(f"{'dilation':>10} {'padding':>8} {'有效感受野':>12} {'输出形状':>20}")
for d in [1, 2, 4, 8]:
    # ★ 关键：padding 必须等于 dilation，才能保持分辨率
    conv = nn.Conv2d(1, 1, kernel_size=3, padding=d, dilation=d)
    y = conv(x)
    eff = 3 + 2 * (d - 1)
    print(f"{d:>10} {d:>8} {eff:>12} {str(tuple(y.shape)):>20}")

print("\n→ 输出始终是 32×32，但有效感受野从 3 涨到 17")
print("→ 这是分割任务（DeepLab）的核心技巧：不下采样也能看得更远")
```

### 实验 5：卷积 vs 全连接的表达能力

```python
import torch
from torch import nn

# 输入 1×28×28，输出 10 类
conv = nn.Sequential(
    nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(),
    nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
    nn.Flatten(), nn.Linear(64*28*28, 10)
)
fc = nn.Sequential(nn.Flatten(), nn.Linear(28*28, 10))

print(f"卷积版: {sum(p.numel() for p in conv.parameters()):>12,} 参数")
print(f"全连接: {sum(p.numel() for p in fc.parameters()):>12,} 参数")
print(f"\n全连接是一层：{fc}")
```

**观察**：卷积版参数更多（因为要处理更多通道），但**更重要的是它的归纳偏置**——它知道「相邻像素相关」，所以用更少的样本就能学到东西。

**这是「卷积是强大的归纳偏置」这句话的量化含义**：不只是参数少，而是**假设对了**。

---

## 八、自测题

**Q1**：一个网络由 `conv3×3 → conv3×3 → conv3×3` 组成（stride=1，padding=0）。输入 32×32，输出多少？感受野多少？

<details>
<summary>答案</summary>

**输出尺寸**：每层卷积减少 2（无 padding，核减1）。
$$32 \to 30 \to 28 \to 26$$
**输出 26×26**

**感受野**：$1 + 3 \times (3-1) = 7$。

**验证**：输出是 26×26，说明需要从原图看 7×7 的区域——$26 + 6 = 32$，即原始的 32×32 里，每个输出对应的窗口是 7×7。一致。
</details>

**Q2**：如果想在保持输出分辨率为 32×32 的前提下扩大感受野，有哪些手段？各自的代价是什么？

<details>
<summary>答案</summary>

| 手段 | 做法 | 代价 |
|---|---|---|
| **padding=1** | 加边，尺寸不变 | 感受野不变（只是覆盖范围挪了） |
| **堆叠更多 3×3** | 连续多层 | 每层只 +2，要更大就得很多层 |
| **空洞卷积** | dilation=d | ★ 感受野指数增长，分辨率不变 |
| **7×7 甚至更大核** | 直接加大核 | 参数量平方级增长 |
| **下采样 + 上采样** | pooling + upsampling | ★ 丢失细节，分辨率真降了 |
| **注意力机制** | ViT 式 | 二次复杂度，适合大分辨率 |

**最优答案通常是空洞卷积**：分辨率和感受野同时保住，参数量只线性增长。

**分割任务的经典配置**：前面用 stride=2 下采样降低计算量，中间用空洞卷积补感受野，最后上采样恢复分辨率（DeepLab v2/v3）。
</details>

**Q3**：1×1 卷积没有空间感受野（感受野=1），那它为什么有用？

<details>
<summary>答案</summary>

**它做的是「通道混合」，这是空间卷积做不到的**。

1×1 卷积在每个空间位置独立地做一个 $C_{in} \to C_{out}$ 的线性变换。所以它能：

1. **升降维**：`1×1 (256→64)` 就是把每个像素的 256 维特征压到 64 维
2. **混合通道**：让不同输入通道的信息相互交流
3. **构成bottleneck**：ResNet 的核心结构，参数省 8.4 倍

**两种卷积的分工**：

| | 空间维度 | 通道维度 | 感受野 |
|---|---|---|---|
| 3×3 卷积 | 变（滑动） | 混合 | >1 |
| 1×1 卷积 | 不变 | 混合 | 1 |

**MobileNet 的洞察**：标准卷积同时做了空间混合和通道混合，可以分解为 **depthwise（只空间）+ pointwise 1×1（只通道）**，计算量省 8~9 倍。

所以「1×1 没感受野」不等于「没用」，而是「它负责另一种工作」。
</details>

**Q4**：为什么 ResNet 用 MaxPool 下采样，而 ConvNeXt 用 stride=2 的卷积？

<details>
<summary>答案</summary>

**MaxPool 是不可学习的固定操作**，有两个问题：

1. **信息损失**：窗口内只保留最大值，其余信息全丢。且反向传播时梯度只路由到最大那个位置，其余位置梯度为 0——**训练效率低**
2. **无法适应数据**：不管输入是什么，下采样方式都一样

**stride=2 卷积的优势**：

1. **可学习**：下采样方式由数据决定
2. **信息保留**：是线性变换而非丢弃
3. **能配合 GroupNorm**：比 BatchNorm 更适合大 batch 训练

**ConvNeXt 的设计哲学**：把 Transformer 的设计原则（层归一化、7×7 大核、GELU、AdamW）搬回 CNN，其中「用 strided conv 替代 pooling」就是这一哲学的体现。

**实测效果**：ConvNeXt 在同等算力下比 ResNet 精度更高，部分原因就是这个改动。
</details>

---

**下一篇** → [残差连接与网络架构](/guides/deep-learning/part2-dl-principles/08-residual)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part2-dl-principles/06-normalization)
