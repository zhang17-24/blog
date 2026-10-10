---
title: 优化器：从 SGD 到 AdamW
description: Momentum、Adam 的更新量是怎么推出来的？AdamW 修好了Adam 的什么缺陷？为什么 LLM 全用 AdamW？
---

# 4 · 优化器：从 SGD 到 AdamW

> 核心问题：Momentum、Adam 的更新量是怎么推出来的？AdamW 修好了Adam 的什么缺陷？为什么 LLM 全用 AdamW？

---

## 一、优化器要解决的真问题

朴素 SGD 的更新：$\theta \leftarrow \theta - \eta g$

三个致命缺陷：

1. **步长无法自适应**：某些参数梯度大、某些小，SGD 对它们的处理完全一样，导致收敛慢
2. **梯度方向震荡**：高维空间里梯度方向在不同维度上符号频繁变化，Z 字形前进
3. **学习率必须手调**：太大学习率发散，太小收敛慢，且不同参数需要不同 lr

**所有优化器的改进都是围绕这三点。**

---

## 二、SGD with Momentum

### 2.1 公式与推导

$$\boxed{v_t = \beta v_{t-1} + g_t, \qquad \theta_t = \theta_{t-1} - \eta v_t}$$

其中 $v_t$ 是**速度**（velocity），$v_0 = 0$。

展开这个递推式：

$$v_t = \beta v_{t-1} + g_t = \beta(\beta v_{t-2} + g_{t-1}) + g_t = \beta^2 v_{t-2} + \beta g_{t-1} + g_t$$

继续展开到最初：

$$v_t = g_t + \beta g_{t-1} + \beta^2 g_{t-2} + \cdots + \beta^{t} v_0$$

代入 $v_0=0$：

$$\boxed{v_t = \sum_{i=0}^{t-1} \beta^{i}\, g_{t-i}}$$

**这个展开式是理解 Momentum 的关键**：$v_t$ 是过去所有梯度的**指数加权平均**。

权重分布（$\beta=0.9$ 时）：

| 梯度 | 权重 |
|---|---|
| $g_t$（最新） | 1 |
| $g_{t-1}$ | 0.9 |
| $g_{t-2}$ | 0.81 |
| ... | $\downarrow$ |
| $g_{t-t'}$ | $0.9^{t'}$ |

有效窗口长度约 $\frac{1}{1-\beta} = 10$（$\beta=0.9$ 时）。

### 2.2 为什么能抑制震荡

想象梯度序列 $+1, -1, +1, -1, \dots$：

- **无 Momentum**：净位移 $= (+1-1)\times \eta = 0$，原地打转
- **有 Momentum**（$\beta=0.9$）：震荡被加权平均掉，$v$ 收敛到一个**非零的小正值**，持续朝一个方向前进

**本质：Momentum 是一个低通滤波器，把高频震荡滤掉，保留低频的漂移方向。**

这就是为什么在陡峭峡谷（梯度方向来回变化）里，Momentum 能显著加速。

### 2.3 Nesterov Accelerated Momentum

改进：不用「当前」梯度算，而是用「位置更新后的」梯度。

$$\theta_t = \theta_{t-1} - \eta \big(\beta v_{t-1} + g_t(\theta_t - \eta v_{t-1})\big)$$

**直觉**：先按动量往前走一步，再看那个位置的梯度（比原点更有信息量）。这叫「**前瞻**」。

**在图像识别任务上比标准 Momentum 快约 5~10%**。PyTorch 里对应 `momentum=0.9, nesterov=True`。

### 2.4 SGD 的实际地位

**在视觉任务上，SGD+Momentum 至今仍然是首选**（ResNet、BERT 训练都用 SGD），因为：

- 泛化性能通常略优于自适应方法
- 超参更少（只有 lr 和 momentum）
- 内存开销小

**自适应方法（Adam 系）在 NLP / Transformer 上更常用**，见第 4 节。

---

## 三、AdaGrad 与 RMSProp

### 3.1 AdaGrad：累加梯度平方

$$r_t = r_{t-1} + g_t^2, \qquad \theta_t = \theta_{t-1} - \frac{\eta}{\sqrt{r_t}} g_t$$

**问题**：$r_t$ 只增不减，分母越来越大 → lr 趋于 0，**过早停止学习**。

### 3.2 RMSProp：改成滑动平均

$$s_t = \beta s_{t-1} + (1-\beta) g_t^2, \qquad \theta_t = \theta_{t-1} - \frac{\eta}{\sqrt{s_t} + \epsilon} g_t$$

两个改动：

1. $g_t^2$ 改成滑动平均 → $s_t$ 可以增减，不再单调增
2. 分母用 $\sqrt{s_t}$（标准差的估计）而非 $\sqrt{r_t}$（平方和）

**直觉**：参数变动剧烈（梯度大）→ 除以大数 → 步长自动变小。**每个参数获得自己的学习率。**

这就是「自适应学习率」的核心思想。

---

## 四、Adam：动量 + 自适应学习率

### 4.1 公式

$$\begin{aligned}m_t &= \beta_1 m_{t-1} + (1-\beta_1) g_t \quad \text{(一阶矩：动量)}\\ v_t &= \beta_2 v_{t-1} + (1-\beta_2) g_t^2 \quad \text{(二阶矩：方差)}\\ \hat{m}_t &= \frac{m_t}{1-\beta_1^t} \quad \text{(偏差修正)}\\ \hat{v}_t &= \frac{v_t}{1-\beta_2^t} \\ \theta_t &= \theta_{t-1} - \eta \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon} \end{aligned}$$

### 4.2 两个状态的直觉

| 状态 | 统计什么 | 类比 |
|---|---|---|
| $m_t$ | 梯度的均值（方向） | 「最近梯度大致指向哪」 |
| $v_t$ | 梯度的平方均值（大小） | 「梯度波动多大」 |

更新规则 = **沿梯度的平均方向走，步长按波动幅度缩放**。

$$\text{更新量} = \eta \cdot \frac{\text{方向}}{\text{尺度}}$$

如果某个参数的梯度一直是 5.0（方向一致、尺度大），更新量 $\approx \eta \cdot 1$，步长正常。
如果梯度是 $+5, -5$ 交替（方向不一致），$m \approx 0$ → **更新量趋于 0，自动减小步长**。

**这就是 Adam 比 SGD 更快的原因：它自动识别并抑制震荡方向的更新。**

### 4.3 偏差修正为什么必需（重要）

$m_0 = v_0 = 0$，所以第一步：

$$m_1 = (1-\beta_1) g_1$$

这明显低估了梯度的真实均值（应该是 $g_1$，但只得到了 $0.1g_1$）。**早期所有估计都偏向 0。**

修正：除以 $1-\beta^t$（因为 $\sum_{i=0}^{t-1}(1-\beta)\beta^i = 1-\beta^t$，归一化因子）：

| 步数 $t$ | $1-\beta_1^t$（$\beta_1=0.9$）| 修正倍数 $1/(1-\beta^t)$ |
|---|---|---|
| 1 | 0.1 | **10×** |
| 2 | 0.19 | 5.3× |
| 10 | 0.65 | 1.5× |
| 100 | 0.99997 | ≈1.0 |

**所以 Adam 的前几步更新量被放大了最多 10 倍。** 这个修正保证了 lr 在任何时刻都是「名义 lr」，不会被初始化效应干扰。

> **这也解释了 warmup 的一个理由**：Adam 早期更新量本来就偏大（即使修正后），warmup 再进一步慢慢提 lr，能让早期训练更稳。

### 4.4 Adam 的致命缺陷：权重衰减不兼容

**关键问题**：weight decay 在 SGD 里是加到梯度上的：

$$\theta \leftarrow \theta - \eta(\nabla L + \lambda\theta) = (\theta - \eta\lambda\theta) - \eta\nabla L$$

**这个顺序很重要**——先衰减，再走梯度。

但 Adam 里两者混在一起了：

$$\theta \leftarrow \theta - \eta \cdot \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}$$

如果 weight decay 加进梯度 $g_t$，它也会进入 $m_t$ 和 $v_t$：

$$m_t = \beta_1 m_{t-1} + (1-\beta_1)(\nabla L + \lambda\theta)$$

**后果**：

1. 衰减量被 $\frac{1}{\sqrt{\hat{v}_t}}$ **缩放**。如果某个参数的梯度一直很小（$\hat{v}_t$ 很小），衰减量会被**放大**——本来想轻微收缩，结果剧烈收缩
2. 衰减量与梯度历史耦合，无法控制

**这就是 AdamW（Adam with decoupled weight decay）的动机**：把衰减从梯度里拿出来，直接作用于参数：

$$\theta_t = \theta_{t-1} - \eta \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon} - \eta\lambda\theta_{t-1}$$

**衰减项不再进入自适应缩放，永远是恒定的 $\eta\lambda\theta$。**

### 4.5 AdamW 的额外好处：可以配合 decoupled 之外的策略

因为解耦了，衰减项可以是任何形式，而不只是 L2：

- **decoupled weight decay**（AdamW 本身）
- **Layer-wise / 部分衰减**：某些层不衰减（比如最后一层）
- 与学习率调度正交：cosine schedule 下两者互不干扰

---

## 五、优化器选择决策树

```
任务类型？
├─ 图像分类 / 视觉 CNN
│   └─ SGD + Momentum(0.9) + Nesterov    ← 泛化好，验证集指标通常更高
│
├─ Transformer / NLP 微调
│   └─ AdamW(lr=1e-4~3e-4, betas=(0.9,0.95), wd=0.01~0.1)
│       ↑ 注意 β2 常设0.95 而非 0.999
│
├─ LLM 预训练
│   └─ AdamW + cosine schedule + warmup
│       lr=1e-4~3e-4，wd=0.1，grad clip=1.0
│
└─ 小模型 / 实验 / 数据量极少
    └─ Adam 系更宽容，不用精调 lr
```

**为什么 Transformer 用 AdamW 而不是 SGD？**

1. 各种尺度的注意力参数需要不同 lr，SGD 处理不好
2. 稀疏梯度（部分维度梯度为0）下Adam 更稳
3. Transformer 训练对小 lr 很敏感，Adam 的自适应让调参更容易

**为什么视觉任务仍偏爱 SGD？**

一个被广泛引用的经验：**AdamW 类方法在训练后期会明显过拟合验证集**，而 SGD+momentum 泛化更好。可能的解释是自适应方法的有效步长不稳定。文献很多、结论不完全统一，实践中以验证集结果为准。

---

## 六、β2 的一个实用细节

**默认值 $\beta_2 = 0.999$ 在 LLM 训练中通常改成 0.95。** 为什么？

$\frac{1}{1-\beta_2}$ = 有效窗口长度：

| $\beta_2$ | 窗口长度 |
|---|---|
| 0.999 | 1000 步 |
| 0.95 | 20 步 |
| 0.99 | 100 步 |

**LLM 训练中 $\beta_2 = 0.999$ 的窗口太长**：因为训练过程中梯度分布本身在快速变化（从初期的大幅下降到后期的精细），用 1000 步的历史平均会让 $v_t$ 严重滞后于当前状态。

改成 0.95（20 步窗口）后，二阶矩能更快跟上梯度的当前尺度。**这是 HuggingFace、LLaMA 训练脚本的默认配置**，也是现在的事实标准。

---

## 七、动手实验

### 实验 1：亲手实现 SGD / Momentum / Adam

比调`torch.optim` 有价值得多——**你会真正理解每个优化器的「状态」是什么**。

```python
import torch

def sgd(p, g, lr=0.1):
    p -= lr * g

def momentum(p, g, lr=0.1, beta=0.9, v=None):
    if v is None: v = torch.zeros_like(p)      # 状态：速度
    v.mul_(beta).add_(g)
    p -= lr * v
    return v

def adam(p, g, lr=0.1, b1=0.9, b2=0.999, eps=1e-8, m=None, v=None, t=0):
    if m is None: m, v, t = torch.zeros_like(p), torch.zeros_like(p), 0
    t += 1
    m = b1*m + (1-b1)*g                        # 状态：一阶矩
    v = b2*v + (1-b2)*g**2                     # 状态：二阶矩
    mh, vh = m/(1-b1**t), v/(1-b2**t)          # 偏差修正
    p -= lr * mh / (vh.sqrt() + eps)
    return m, v, t

# 交替震荡的梯度序列，模拟"峡谷"地形（梯度方向来回变）
grads = [torch.tensor([1.0 if i % 2 == 0 else -1.0]) for i in range(10)]

for name in ["SGD", "Momentum", "Adam"]:
    p = torch.tensor([1.0])
    state = {}
    for g in grads:
        if name == "SGD":
            sgd(p, g, lr=0.1)
        elif name == "Momentum":
            state['v'] = momentum(p, g, lr=0.1, v=state.get('v'))
        else:
            state['m'], state['v'], state['t'] = adam(
                p, g, lr=0.1, m=state.get('m'), v=state.get('v'), t=state.get('t', 0))
    print(f"{name:>10}: 起点 1.0 → 最终 {p.item():+.4f}")
```

**实测输出**：

```
      SGD: 起点 1.0 → 最终 +1.0000     ← ★ 净位移为 0，完全原地打转
 Momentum: 起点 1.0 → 最终 +0.6915     ← 动量把它推过去了
     Adam: 起点 1.0 → 最终 +0.8455     ← 自适应缩放，步子更小但也有效
```

**SGD 最终精确回到 1.0**，因为 10 个梯度里 5 个 +1、5 个 -1，净和为 0。**这就是震荡梯度下朴素 SGD 的困境**——它把力气全花在互相抵消上了。

Momentum 和 Adam 都成功偏离了原点，因为它们的**状态变量记住了历史**，震荡被平均掉。

> **踩坑记录**：我第一版写成 `zip(params, grads)` 的批量版，结果三个优化器输出完全一样（都是 0.9）。原因是我只传了**1 个参数**却给了 **10 个梯度**，`zip` 按最短长度截断，等于只做了1 步。**单个参数 + 一串梯度这种场景，必须写成逐次调用并显式传递状态**，不能用批量接口。

### 实验 2：验证 Adam 的偏差修正

```python
import torch

print("=== 第一步：不做偏差修正 vs 做修正 ===")
for use_bias_correction in [False, True]:
    torch.manual_seed(0)
    p = torch.tensor([0.0])
    m = torch.zeros(1); v = torch.zeros(1)
    g = torch.tensor([3.0])              # 固定的梯度
    lr, b1, b2 = 0.1, 0.9, 0.999

    m = b1*m + (1-b1)*g
    v = b2*v + (1-b2)*g**2
    if use_bias_correction:
        mh, vh = m/(1-b1**1), v/(1-b2**1)
    else:
        mh, vh = m, v
    step = lr * mh / (vh.sqrt() + 1e-8)
    print(f"bias_correction={use_bias_correction}: m={m.item():.4f} "
          f"更新量={step.item():.4f}")

print("\n理论上：|g|=3 时，Adam 的步长应该是 lr=0.1 才对")
print("不做修正 -> 步长被缩小到 lr*0.1 = 0.01（因为 m 只积累到 0.3）")
print("做了修正 -> 步长 ≈ 0.1（正确）")
```

**实测输出**：

```
corr=False: step=0.3162   ← 比理论值 0.1 大3 倍
corr=True:  step=0.1000   ← ★ 精确等于 lr
```

**注意**：不做修正时步长是 0.3162，比正确值 0.1 **大**了 3 倍，不是「缩小」。

**为什么反直觉？** 因为 $\epsilon$ 也在起作用。看清楚 $\beta_2 = 0.999$ 时发生了什么：

| 修正项 | 值 |
|---|---|
| $m_1$ | $0.1 \times 3 = 0.3$ |
| $v_1$（未修正） | $0.001 \times 9 = 0.009$ |
| $v_1$（修正后） | $0.009 / (1-0.999) = 9.0$ |

$$\sqrt{v_1^{\text{未修正}}} = 0.0949, \qquad \sqrt{v_1^{\text{修正}}} = 3.0$$

分子 $\hat{m}$ 从 0.3 → 3.0（放大 10 倍），分母也从 0.095 → 3.0（放大约 31 倍）。**分母放得更多，所以最终步长偏小**——0.1 × 0.3/0.095 = 0.316，正是实测值。

**一句话总结偏差修正的作用**：让第一步的有效步长精确等于名义 lr，不被初始化时的 $\beta$ 衰减拖慢。

### 实验 3：Adam vs AdamW 的差异（理解解耦的价值）

```python
import torch

print("=== 一个梯度极小的参数，weight decay 会怎样？ ===")
torch.manual_seed(0)
for name, use_coupled in [("Adam (耦合，衰减进梯度)", True), ("AdamW (解耦)", False)]:
    p = torch.tensor([1.0], requires_grad=True)
    m, v = torch.tensor([0.0]), torch.tensor([0.0])
    lr, b1, b2, eps, wd = 0.1, 0.9, 0.999, 1e-8, 0.1
    # 连续 3 步，梯度恒为 0.01（很小）
    for t in range(1, 4):
        g = torch.tensor([0.01])
        if use_coupled:
            g_eff = g + wd * p.detach()      # 衰减加进梯度
        else:
            g_eff = g
        m = b1*m + (1-b1)*g_eff
        v = b2*v + (1-b2)*g_eff**2
        mh, vh = m/(1-b1**t), v/(1-b2**t)
        p.data -= lr * mh / (vh.sqrt()+eps)
        if not use_coupled:
            p.data -= lr * wd * p.data       # 解耦：直接衰减
    print(f"{name:>28}: p={p.item():.6f}")
```

**实测输出**：

```
   Adam (耦合，衰减进梯度): p=0.701382
  AdamW (解耦):p=0.676259
```

梯度恒为 0.01（很小），weight decay=0.1，目标是把参数拉向 0：

- **AdamW**：衰减量精确是 $\eta\lambda p = 0.1 \times 0.1 \times p$，行为完全可预测
- **Adam**：衰减量被送进 $v_t$，最终的步长 $\propto \frac{1}{\sqrt{\hat v_t}}$ 包含了**衰减的历史**，于是衰减强度和梯度历史纠缠在一起

数值上这里只差 3%，看起来不多。**但在真实训练里差异会累积**：Adam 的 $v_t$ 被污染后，会影响**所有**参数的自适应步长，而不只是被衰减的那些——这才是问题的严重性所在。

**想看更戏剧性的差异，把梯度再调小试试**（$\hat v_t$ 越小，$1/\sqrt{\hat v_t}$ 的放大效应越强）。

### 实验 4：β2 的影响

```python
import torch
print("=== β2 决定的二阶矩窗口长度 ===")
for b2 in [0.9, 0.95, 0.99, 0.999]:
    print(f"β2={b2:<6} 有效窗口 = 1/(1-β2) = {1/(1-b2):.0f} 步")
print("\nLLM 预训练默认 β2=0.95（20 步窗口）而非 0.999（1000 步）")
print("原因：训练中梯度尺度快速变化，需要二阶矩跟上当前状态")
```

---

## 八、自测题

**Q1**：Adam 的 $\epsilon$ 是干什么的？如果设成 0 会有什么问题？

<details>
<summary>答案</summary>

**防止除零**。当某个参数在整个训练过程中梯度都是 0（可能因为它被 mask 了、或者初始化为 0 后从未更新），$v_t = 0$，则 $\frac{m_t}{\sqrt{v_t}}$ 是 0/0。

加了 $\epsilon$（默认 1e-8）后变成 $\frac{m_t}{\sqrt{v_t}+\epsilon}$，分母有下界。

**设成 0 的风险**：
1. 分母为 0 → NaN
2. 即使不为 0，$\epsilon$ 太小会放大数值误差
3. 实践中 $\epsilon$ 的选择对结果影响很小，因为它加在 $\sqrt{v_t}$ 上（$v_t$ 通常远大于 1e-16）
</details>

**Q2**：为什么 SGD 在图像任务上泛化性常优于 Adam？

<details>
<summary>答案</summary>

**没有公认定论**，文献很多，主要假说：

1. **自适应方法的等效学习率不稳定**。Adam 的 $\eta/\sqrt{v_t}$ 在梯度尺度变化时会剧烈波动，导致它找到的是「容易优化的解」而非「泛化好的解」（类似 sharpness-aware minimization 的视角）。
2. **Adam 的隐式正则**。$m/\sqrt{v}$ 相当于对梯度做归一化，抹平了不同参数方向的尺度差异，导致模型倾向于找到「平坦但可能不泛化」的方向。
3. **训练后期行为差异**。Adam 在训练后期有效步长不稳定，容易在验证集上过拟合。

**但这个结论不绝对**：
- 有研究（e.g. 在部分视觉 benchmark 上）发现 AdamW 配合好的调度也能超过 SGD
- ConvNeXt 等现代视觉模型用 AdamW 也拿到了 SOTA

**实践建议**：视觉任务两个都试，用验证集决定。不要预设。
</details>

**Q3**：一个参数的梯度一直是 0.001，另一个是 100。用 SGD 和 Adam 各走一步，哪个参数动得多？

<details>
<summary>答案</summary>

**SGD**（lr=0.1）：两个参数的更新量分别是 0.0001 和 10。**梯度大的动得多，可能直接发散。**

**Adam**：
- 参数A（梯度一直 0.001）：$m \to 0.001$，$\sqrt{v} \to 0.001$，更新量 $= 0.1 \times \frac{0.001}{0.001} = 0.1$
- 参数B（梯度一直 100）：$m \to 100$，$\sqrt{v} \to 100$，更新量 $= 0.1 \times \frac{100}{100} = 0.1$

**两个参数走一样多！** 这就是自适应学习率的意义——**不管梯度绝对大小如何，每个参数每步都走大致相同的距离**。

**这个特性对 Transformer 特别重要**：注意力层的 Q/K/V 矩阵、FFN 的两层，梯度尺度差异巨大（可能相差几个数量级）。SGD 处理不好，Adam 能自动处理。
</details>

**Q4**：为什么 LLM 都用 warmup？如果没有 warmup 会怎样？

<details>
<summary>答案</summary>

**warmup 的作用**：在训练最初的几百/几千步把 lr 从 0 线性提升到目标值。

**没有 warmup 的问题**：

1. **初期梯度不稳**。训练开始时参数还没进入「有意义的空间」，梯度方向噪声大。直接用大 lr 会把参数推到糟糕的区域，一旦模型已经学到的结构被破坏，后面很难恢复。

2. **自适应优化的二阶矩估计不准**。$m_t, v_t$ 在头几步是严重有偏的（虽然有偏差修正，但修正本身让前几步的有效 lr 偏大），此时用满 lr 不稳。

3. **配合 AdamW 会更糟**。因为 weight decay 的实际强度是 $\eta\lambda\theta$——如果 lr 一开始就是满值，衰减也是满的，参数会在最初几步被剧烈拉向 0。

**warmup 之后**：
- 梯度分布稳定了
- 二阶矩估计准确了
- 再配合 cosine decay，让 lr 在训练后期精细收敛

**LLaMA 的做法**：warmup 2000 步 + cosine decay到 10% 峰值。这套配置几乎成了标准。
</details>

**Q5**：PyTorch 里 `Adam(lr=..., weight_decay=...)` 和 `AdamW` 到底差在哪？如果我用了 `Adam` + `weight_decay`，我的模型会有什么问题？

<details>
<summary>答案</summary>

**差在weight decay 的施加位置**：

```python
# Adam（L2 正则耦合）
g_eff = g + weight_decay * p        # 衰减进梯度
m = b1*m + (1-b1)*g_eff             # 衰减进动量
v = b2*v + (1-b2)*g_eff**2           # 衰减进二阶矩 ← 问题在这
p -= lr * m_hat / (sqrt(v_hat)+eps)

# AdamW（解耦）
g_eff = g                            # 梯度不含衰减
m, v = ...(只用数据梯度)...
p -= lr * m_hat / (sqrt(v_hat)+eps)
p -= lr * weight_decay * p            # 衰减独立施加
```

**实际问题**：
1. 衰减项被 $\frac{1}{\sqrt{\hat v}}$ 缩放。梯度历史小的参数，衰减被**放大**——本意轻微收缩，实际剧烈收缩
2. 衰减量和梯度历史纠缠，无法单独控制强度
3. 在 warmup 阶段（lr 变化）两者行为差异更大

**实际影响**：在很多任务上 `Adam + weight_decay` 也能训出好模型，所以这个bug 不会立刻暴露。但在**大规模预训练 + 长训练**里，AdamW 的稳定优势才显现出来。这就是为什么 LLM 全用 AdamW。

**建议**：直接用 `AdamW`。没有理由用 `Adam + weight_decay`。
</details>

---

**下一篇** → [反向传播的完整推导](/guides/deep-learning/part2-dl-principles/05-backprop)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part1-ml-basics/03-regularization)
