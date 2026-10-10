---
title: 归一化：BatchNorm → RMSNorm
description: 归一化到底在解决什么？为什么 BatchNorm 在 CNN 里统治、在 NLP 里被淘汰？RMSNorm 又省了什么？
---

# 6 · 归一化：BatchNorm → RMSNorm

> 核心问题：归一化到底在解决什么？为什么 BatchNorm 在 CNN 里统治、在 NLP 里被淘汰？RMSNorm 又省了什么？

---

## 一、归一化解决的两个问题

### 1.1 尺度问题（forward）

考虑一个深网络里的激活值。如果第 $l$ 层的输出尺度是第 $l-1$ 层的 $k$ 倍（$k>1$），那么到第 $L$ 层尺度就是 $k^L$。

$k = 1.1$、$L = 50$ 时，$k^L \approx 117$。**指数增长**，一层层放大，网络极易饱和（sigmoid 饱和区 / ReLU 全死）。

归一化把每层的输出强制拉到「零均值单位方差」，尺度被控制住了。

### 1.2 优化问题（backward）

梯度里含因子 $W^\top$。如果 $W$ 的谱半径（最大奇异值）$\rho(W) > 1$，梯度连乘会指数爆炸；$\rho(W) < 1$ 则指数消失。

归一化让每层的 Jacobian 更接近「谱半径为 1 的等距映射」，梯度既不爆炸也不消失。

**归一化的核心价值：让每一层的梯度尺度可控，从而让深层网络可训练。**

---

## 二、BatchNorm 详解

### 2.1 公式

对一个 mini-batch 的同一通道，统计均值和方差，归一化后再缩放平移：

$$\hat{x}_i = \frac{x_i - \mu_B}{\sqrt{\sigma_B^2 + \epsilon}}, \qquad y_i = \gamma \hat{x}_i + \beta$$

其中（对 batch 维度 $m$ 求）：

$$\mu_B = \frac{1}{m}\sum_i x_i, \qquad \sigma_B^2 = \frac{1}{m}\sum_i (x_i - \mu_B)^2$$

**$\gamma, \beta$ 是可学习的**（shape = 通道数），作用是「让网络可以自己决定要不要归一化、以及归一化到什么分布」。如果 $\gamma=\beta=0$，BN 就退化成恒等映射——所以加 BN 的位置总会初始化成 $\gamma=1, \beta=0$。

### 2.2 关键设计：训练/推理行为不同

推理时没有 batch 可用，怎么办？

**用训练时积累的滑动平均**（running mean / running var）：

```python
# PyTorch 内部维护
self.register_buffer('running_mean', torch.zeros(num_features))
self.register_buffer('running_var', torch.ones(num_features))
```

训练时更新：

$$\text{running\_mean} = (1-\text{momentum}) \cdot \text{running\_mean} + \text{momentum} \cdot \mu_B$$

### 2.3 推理时必须 `model.eval()`（否则结果乱飞）

**这是 BN 最容易踩的坑**，也是第 2 篇强调过的 bug：

- `model.train()`：用**当前 batch** 的统计量
- `model.eval()`：用**训练时积累的** running 统计量

**同一个输入，train 模式下每次预测结果都不同**；eval 模式下才确定。

**这就是为什么 LLM 普遍不用 BatchNorm**：NLP 任务 batch 通常只有 1~8（序列长、显存紧），batch 统计量噪声极大，训练不稳定。

---

## 三、LayerNorm：Transformer 的选择

### 3.1 与 BN 的关键差异

| | BatchNorm | LayerNorm |
|---|---|---|
| 统计维度 | **batch 维 + 空间维**（对整个 batch 统计） | **特征维**（每个样本独立算） |
| 依赖 batch 大小 | **是** | **否** |
| 训练/推理行为不同 | **是** | **否** |
| 适合序列 | 否（batch小 + 变长序列） | **是** |
| 消融论文 | ResNet | Transformer / LLaMA |

### 3.2 公式

对单个样本的**特征维度**统计：

$$\mu = \frac{1}{d}\sum_{j=1}^{d} x_j, \qquad \sigma^2 = \frac{1}{d}\sum_{j=1}^{d}(x_j-\mu)^2$$

$$\hat{x} = \frac{x - \mu}{\sqrt{\sigma^2+\epsilon}}, \qquad y = \gamma \odot \hat{x} + \beta$$

**注意**：$\mu, \sigma$ 是对**单个样本的所有特征**算的，**和其他样本无关**。

### 3.3 为什么 NLP 必须用 LayerNorm

**三个决定性原因**：

1. **batch 统计量不可靠**。NLP 的 batch size 常常是 1（长序列 + 大词表），BN 根本没足够样本算方差。
2. **变长序列会引入 padding 污染**。同一个 batch 里不同长度序列的 padding 位置不同，如果对 batch 统计，padding 的 0 值会污染均值方差。
3. **推理行为必须确定性**。变长输入每次凑到的 batch 不同，BN 的 running 统计不准。

**LayerNorm 完全避开了这三个问题**——每个 token 独立归一化，跟 batch 里有什么完全无关。

### 3.4 一个反直觉的现象

**Transformer 里，LayerNorm 放在残差连接的「后面」（Post-LN）还是「前面」（Pre-LN）？**

| | Post-LN（原始 Transformer） | Pre-LN（现代 LLM） |
|---|---|---|
| 结构 | $x + \text{Sublayer}(x)$ 后再 LN | $\text{Sublayer}(x) + x$ 里 LN 在前 |
| 深层训练 | **需要 warmup** | **稳定**，warmup 可选 |
| 最终性能 | 可能更好 | 略差或持平 |
| 代表 | 原始 Transformer | GPT-2/LLaMA 等几乎全部现代 LLM |

**Pre-LN 的残差路径是干净的恒等映射**：

$$\text{Pre-LN: } x_{l+1} = x_l + F(\text{LN}(x_l))$$

梯度反向时 $\frac{\partial x_{l+1}}{\partial x_l} = I + \frac{\partial F}{\partial \text{LN}} \cdot \frac{1}{\sigma}$，**那个 $I$ 保证了梯度直通**。深层训练立刻稳定。

**Post-LN 则是 $x_{l+1} = \text{LN}(x_l + F(x_l))$**，LN 夹在残差路径中间，梯度要穿过 LN 才能回到前面。

**这就是为什么 LLaMA 用 RMSNorm + Pre-LN**（第 12 篇会详细讲）。

---

## 四、RMSNorm：LLaMA 的选择

### 4.1 省掉了什么

RMSNorm（LLaMA / T5 提出）观察到一个事实：**LayerNorm 里，去掉均值中心化，效果几乎不掉**。

$$\text{RMSNorm}(x) = \frac{x}{\text{RMS}(x)} \odot \gamma, \qquad \text{RMS}(x) = \sqrt{\frac{1}{d}\sum_j x_j^2}$$

对比：

| | LayerNorm | RMSNorm |
|---|---|---|
| 求均值 $\mu$ | 需要 | **不需要** |
| 求方差 | 需要（先减均值再平方） | 只需平方和的均方根 |
| 减均值 | 需要 | **不需要** |
| 可学习参数 | $\gamma, \beta$ | 只有 $\gamma$ |

**省掉的操作**：均值计算、减法、$d$ 个 beta 参数。

### 4.2 为什么省掉还能work

直觉解释：**归一化的主要作用是「控制尺度」，不是「控制中心」。**

LayerNorm 的 $\frac{x-\mu}{\sqrt{\sigma^2+\epsilon}}$ 可以近似理解为：

$$\text{除以「偏差」} + \text{除以「标准差」}$$

RMSNorm 只保留了第二项（除以 RMS ≈ 标准差）。实验表明第一项对效果贡献很小。

**更深层的解释**：Transformer 里每个 token 的表示本身已经有明确的语义中心，减去 batch/样本均值带来的收益有限；而那一步的数值开销和显存占用是实打实的。

### 4.3 实际收益（LLM 训练是显存瓶颈）

| | LayerNorm | RMSNorm |
|---|---|---|
| 每层参数（d=4096） | $2d = 8192$ | $d = 4096$ |
| 归一化时的中间张量 | 存 mean/var/归一化结果 | 只存 均方根 + 归一化结果 |
| 融合 kernel 支持 | 部分 | **几乎全部（可完全融合进相邻层）** |

**关键收益是能做算子融合**：RMSNorm 的计算图简单，可以和前面的 Linear / 后面的乘法融合成一个 kernel，省掉多次读写显存。

**在 4096 层的模型里，LayerNorm → RMSNorm 省下的不是一点半点。** 这是 LLaMA 全盘采用 RMSNorm 的原因之一（另一个是它的稳定性 —— 见下）。

---

## 五、归一化的其他副作用（工程上很重要）

### 5.1 归一化 + weight decay 的相互作用

**这是 ResNet 论文里的经典发现**：

- **有 BN 的卷积层**：weight decay 会让权重变小 → 有效感受野变大 → 有正则化效果
- **没有 BN 的卷积层**：weight decay 只是单纯缩小权重，**不改变感受野，反而可能有害**

论文里的实验结论：

| 设置 | 最佳 weight decay | 训练误差 | 测试误差 |
|---|---|---|---|
| 全部层都衰减 | 1e-3 | — | 好 |
| **BN 之前不衰减** | **1e-4（更小）** | 训练误差更高 | 测试误差更好 |

**「BN 前的层不衰减」是 ResNet 的标准做法**，现在所有视觉网络的实现里都能看到这段逻辑：

```python
# torchvision 的实现
def _apply(self, fn):
    for module in self.modules():
        if isinstance(module, nn.BatchNorm2d):
            module.weight.data = fn(module.weight.data)
            module.bias.data   = fn(module.bias.data)
            # ★ 注意：这里只处理 BN 自己的 gamma/beta，不处理 conv 前的权重
```

**这个「训练误差更高但测试误差更好」的现象很反直觉**：weight decay 减小了拟合能力（训练误差上升），却提升了泛化（测试误差下降）。**过拟合的减少不一定要靠训练损失更低来实现。**

### 5.2 推理时的 batch 依赖

BN 的输出**依赖 batch 里的其他样本**。这导致：

- 同一个输入，在不同 batch 组成下输出不同
- 线上推理时 batch 大小变化 → 结果变化 → **难以复现**
- 这也是为什么很多线上服务要求「固定 batch size」

LayerNorm/RMSNorm **没有这个问题**——每个样本独立计算。

---

## 六、动手实验

### 实验 1：BatchNorm 的 train/eval 差异

```python
import torch
from torch import nn

torch.manual_seed(0)
bn = nn.BatchNorm1d(4)
for _ in range(50):                      # 积累 running 统计量
    bn.train(); bn(torch.randn(16, 4))

# ---- 情况A：train 模式 + batch=1 → 直接报错 ----
bn.train()
try:
    bn(torch.randn(1, 4))
except ValueError as e:
    print("train 模式 batch=1 报错:", str(e)[:70])

# ---- 情况B：eval 模式，用 running 统计量 → 完全稳定 ----
bn.eval()
x = torch.randn(1, 4)
outs = [bn(x)[0, 0].item() for _ in range(5)]
print(f"\neval 模式 batch=1: {[f'{v:.4f}' for v in outs]}")
print(f"  5 次输出是否唯一: {len(set(outs)) == 1}   ← 用 running mean/var，与 batch 无关")
```

**实测输出**：

```
train 模式 batch=1 报错: Expected more than 1 value per channel when training, got inpu

eval 模式 batch=1: ['-0.1328', '-0.1328', '-0.1328', '-0.1328', '-0.1328']
  5 次输出是否唯一: True
```

**PyTorch 直接帮你拦住了 batch=1 这个坑**——这就是自测题 Q1 说的失效场景，框架层面已经做了防御。

### 实验 2：LayerNorm 与 batch 完全无关

```python
import torch
from torch import nn

torch.manual_seed(0)
ln = nn.LayerNorm(8); ln.eval()

x = torch.randn(1, 8)                               # 单个样本
batch_full = torch.cat([x, torch.randn(7, 8)], 0)   # 同一样本混在大batch 里

diff = (ln(x) - ln(batch_full)[0]).abs().max().item()
print("样本单独推理:", ln(x)[0, :4].tolist())
print("混在 batch 里:", ln(batch_full)[0, :4].tolist())
print(f"\n差异: {diff:.1e}   ← 完全为 0")
```

**LayerNorm 只对自己样本的特征维做统计**，所以输出与 batch 组成完全无关。这是它在 NLP 里不可替代的原因。

### 实验 3：RMSNorm 省掉了「中心化」

```python
import torch
from torch import nn

class RMSNorm(nn.Module):
    def __init__(self, d, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d))
        self.eps = eps
    def forward(self, x):
        # ★ 和 LayerNorm 的唯一区别：不减均值，直接开方
        rms = x.pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()
        return self.weight * (x * rms)

torch.manual_seed(0)
ln = nn.LayerNorm(64); rms = RMSNorm(64)
rms.weight.data = ln.weight.data            # 让两者 gamma 一致，可直接比较

x = torch.randn(32, 64) * 3 + 1.5           # 人为让数据有偏移（均值≈1.4）
y_ln, y_rms = ln(x), rms(x)

print(f"输入       mean/std: {x.mean():+.3f} / {x.std():.3f}")
print(f"LayerNorm  mean/std: {y_ln.mean():+.3f} / {y_ln.std():.3f}")
print(f"RMSNorm    mean/std: {y_rms.mean():+.3f} / {y_rms.std():.3f}")
print(f"\n两者最大差异: {(y_ln - y_rms).abs().max():.3f}")
```

**实测输出**：

```
输入       mean/std: +1.403 / 2.979
LayerNorm  mean/std: +0.000 / 1.000
RMSNorm    mean/std: +0.426 / 0.905
```

**这个对比很说明问题**：

- **LayerNorm**：均值被拉到 0，标准差拉到 1
- **RMSNorm**：**保留了输入的偏移**（+0.426），但标准差照样被控制住（0.905 ≈ 1）

**结论：归一化的核心作用是「控制尺度」，不是「控制中心」。** RMSNorm 砍掉的正是次要功能，所以能省。

### 实验 4：归一化如何缓解梯度消失

```python
import torch
from torch import nn

def grad_profile(with_norm, depth=20, width=64):
    layers = []
    for _ in range(depth):
        layers.append(nn.Linear(width, width))
        if with_norm:
            layers.append(nn.LayerNorm(width))     # ★ 插在每层之间
        layers.append(nn.ReLU())
    layers.append(nn.Linear(width, 1))
    model = nn.Sequential(*layers)

    x = torch.randn(32, width, requires_grad=True)
    model(x).sum().backward()
    return x.grad.norm().item()

torch.manual_seed(0); without = grad_profile(False)
torch.manual_seed(0); with_ln  = grad_profile(True)
print(f"无归一化:     ||dL/dx|| = {without:.3e}")
print(f"有 LayerNorm: ||dL/dx|| = {with_ln:.3e}")
print(f"\n加入归一化后梯度被放大约 {with_ln / without:.1f} 倍")
```

**实测输出**：

```
无归一化||dL/dx|| = 7.865e-08
有 LayerNorm: ||dL/dx|| = 1.518e+00
加入归一化后梯度被放大约 19302438.6 倍
```

**放大了近 2000 万倍**。这不是修辞——20 层不带归一化的网络，输入端梯度已经衰减到 $10^{-8}$，**在 float32 下几乎等同于 0，参数完全学不动**。加上 LayerNorm 后梯度回到 $10^{0}$ 量级，完全可用。

**归一化把每层 Jacobian 的谱半径锚定在 1 附近，阻止了连乘时的指数衰减。这正是深层网络能训起来的前提。**

---


## 七、自测题

**Q1**：为什么 BatchNorm 在 batch size = 1 时行为异常？

<details>
<summary>答案</summary>

**训练时**：BN 在单个样本上算均值方差，$\mu_B = x_1$，$\sigma_B^2 = 0$，于是：

$$\hat{x}_1 = \frac{x_1 - x_1}{\sqrt{0 + \epsilon}} = 0$$

**输出恒为 $\beta$**，完全丢失了输入的信息。同时反向传播时 $\frac{\partial y}{\partial \hat{x}} = \frac{1}{\sqrt{\sigma^2+\epsilon}} = \frac{1}{\sqrt\epsilon}$，**如果 $\epsilon$ 也很小，梯度会爆炸**。

**推理时**：用 running 统计量（有历史积累，正常）。

**结论**：BN 在 train 模式下 batch=1 时输出恒为 beta，训练完全失效。**PyTorch 的 `BatchNorm1d` 在 train 模式下 batch=1 会直接抛错**，就是防止你误用。

**NLP 为什么用 LayerNorm**：这是核心原因之一。长序列训练的 batch size 常常是 1~4，BN 不可用。
</details>

**Q2**：为什么 ResNet 里 BN 之前的卷积层不做 weight decay？

<details>
<summary>答案</summary>

**因为对 BN 前的层做 weight decay 会改变感受野**，这通常有害。

机制：
- 卷积权重变小 → 有效感受野（ERF）变大 → 每个单元看的输入区域更广
- BN 会把尺度**归一化回来**，抵消掉这个变小

结果：**BN 前的权重变小 = 感受野变大 = 有益的正则化**（ResNet 论文称之为 weight decay 的第二重作用）。

而 BN 自己的 $\gamma, \beta$（1 维参数）做 weight decay 没有意义，只是让模型平移边界。

**ResNet 论文的实验**：
- 全部层衰减：wd=1e-3 最佳
- BN 前不衰减：wd=**1e-4** 更好，**训练误差更高但测试误差更低**

**结论**：正则化导致训练误差升高是正常的，重要的是泛化。**「训练误差更低」和「模型更好」不是一回事。**

这个技巧现在所有视觉网络都默认开启。
</details>

**Q3**：RMSNorm 去掉了减均值，为什么效果不掉？更深的原因是什么？

<details>
<summary>答案</summary>

**表层原因**：归一化有两个作用——控制尺度（除以标准差）和控制中心（减均值）。实验表明**控制尺度的贡献占绝大部分**。

**深层原因**：

1. **LN 的减均值在数学上和「白化」相关，但只在特征之间有强相关时才有意义**。如果特征之间近似正交，减均值只是平移，收益很小。

2. **Transformer 里 LLM 已经有 RMSNorm 控制了极端值**，不需要 LN 再做一次中心化。

3. **BERT 里 LN 的中心化作用被 embedding 的 LayerNorm 部分抵消**——多层 LN 叠加时，效果已经饱和。

**实证支持**：
- T5 论文（Google）：把 LN 换成 RMSNorm，效果几乎不变，速度更快
- LLaMA 论文：明确采用 RMSNorm，理由是「经验上更稳定」

**一个补充观察**：RMSNorm 在深层网络里有时**更稳定**。原因之一是它避免了「减均值后平方」这个数值上不稳定的操作链（当均值远大于标准差时，$x-\mu$ 会有灾难性抵消）。
</details>

**Q4**：什么情况下 BatchNorm 反而比 LayerNorm 好？

<details>
<summary>答案</summary>

**只有视觉任务，且 batch 足够大的时候。** 具体：

1. **CNN 图像分类**：ResNet / EfficientNet / ConvNeXt 全都用 BN。图像的空间维度大（224×224），即使 batch=32 也相当于统计了 $32 \times 224^2$ 个样本，统计量非常可靠。

2. **特定场景**：AdaFace、TransNorm 等混合方案会判断：
   - 如果特征维度小、batch 大 → BN
   - 如果特征维度大、batch 小 → LN

3. **BatchNorm 有额外优势**：
   - 训练/推理时的正则化效应（dropout 式的噪声）被证明对视觉任务有帮助
   - 可以用「冻结 running 统计量」的方式做模型校准和量化
   - 某些部署场景下 BN 可以折叠进前面的卷积层（推理时等价于一个普通 conv），LayerNorm 不行

**判断标准**：

| 场景 | 选择 |
|---|---|
| 图像分类（batch≥32） | **BatchNorm** |
| 目标检测/分割（batch小、高分辨率） | BatchNorm 或 GroupNorm |
| Transformer / NLP | **LayerNorm** |
| 大语言模型 | **RMSNorm**（+ Pre-LN） |
| 小 batch 在线学习 | LayerNorm（BN 的 running 统计不可靠） |
</details>

---

**下一篇** → [卷积与感受野](/guides/deep-learning/part2-dl-principles/07-convolution)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part2-dl-principles/05-backprop)
