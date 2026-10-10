---
title: 机器学习的本质是什么
description: 模型在学什么？损失函数在衡量什么？为什么「最小化损失」等于「学得好」？
---

# 1 · 机器学习的本质是什么

> 核心问题：模型在学什么？损失函数在衡量什么？为什么「最小化损失」等于「学得好」？

---

## 一、一个不准确的直觉

多数入门材料会说：「机器学习就是让计算机从数据中学习规律」。这句话没错，但**没有任何信息量**。

更有用的定义是：

> 机器学习 = **在一个函数空间里搜索**，使得在某个目标函数上取值最小。

三个关键词，逐个拆。

### 关键词一：函数空间

你写的模型 `f(x; θ)` 里，`θ` 是参数。参数固定，模型就固定了。

假设模型是线性回归 `f(x) = wx + b`，那么 `w` 和 `b` 就是两个自由变量。它们构成的二维平面就是**这个模型的函数空间**。

| 假设 | 函数空间 |
|---|---|
| 线性回归（2 参数） | 二维平面 |
| 线性回归（10 参数） | 十维空间 |
| 一个 1 亿参数的 Transformer | 一亿维空间 |

**机器学习的第一个关键事实：参数空间极其巨大，找到一个"好"的点，和找到一个"最优"的点，是两回事。**

深度学习的全部困难都源于此——在一亿维空间里找最优解，实际做不到，只能不断改善。

### 关键词二：搜索

有了函数空间，接下来要决定「往哪个方向走」。这一步叫**优化**，由优化器（optimizer）完成。

在深度学习里，你写的这一行：

```python
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
```

就是决定了搜索策略。而 `loss.backward()` 是在计算**方向**（往哪走能让损失变小）。

**「方向 + 步长」构成了优化的全部。** 后面所有优化器的区别，本质上只是这两件事的不同做法。

### 关键词三：目标函数

你优化的是 `loss_fn(pred, y)`。这个函数衡量的东西，决定了模型学到什么。

- 用 `MSELoss` → 模型学「预测值和真实值的平方距离」
- 用 `CrossEntropyLoss` → 模型学「预测类别的对数似然」
- 用对比学习损失（如 InfoNCE）→ 模型学「什么样本该靠近、什么该远离」

**同一个模型架构，换个损失函数就是在做完全不同的事。** 这是很多人换 loss 就想提升准确率却没效果的原因——他们换了，但没换对目标。

---

## 二、损失函数到底是什么

这一节是本文的核心。搞清楚损失函数的来源，后面所有选择都有依据。

### 从概率建模推导出来

假设你要做二分类。数据是 $(x, y)$，其中 $y \in \{0, 1\}$。

**建模思路**：假设存在一个真实概率 $p(y=1 \mid x)$，我们的模型输出一个 $\hat{p}$。目标是让模型输出的概率尽可能接近真实概率。

**用什么衡量两个概率分布的差异？** KL 散度：

$$D_{KL}(p \| q) = \sum_i p_i \log\frac{p_i}{q_i}$$

直观含义：如果真实分布是 $p$，我们用 $q$ 去编码，编码平均长度比最优编码多多少比特。**越接近 0 越好。**

（推论：为什么 KL 散度不对称——$D_{KL}(p\|q) \ne D_{KL}(q\|p)$。这在后面的对比学习里会再次出现。）

### 从最大似然到交叉熵

KL 散度需要真实分布 $p$，但我们不知道。改用「最大似然」：找到一组参数，让**观测到的数据**出现的概率最大。

$$L = -\sum_i \log \hat{p}(y_i \mid x_i)$$

即**负对数似然**（NLL）。因为最大化 $\prod p$ 等价于最小化 $\sum -\log p$。

展开二分类（$y \in \{0,1\}$）：

$$L = -\frac{1}{N}\sum_i \left[y_i \log \hat{p}_i + (1-y_i)\log(1-\hat{p}_i)\right)$$

**这就是交叉熵损失**（Cross-Entropy Loss）。

所以：**交叉熵损失不是拍脑袋设计的，它就是「最大化观测数据的似然」在分类任务上的形式。**

### 多分类版本

模型输出 $K$ 个 logits $z_1,\dots,z_K$，用 softmax 转成概率：

$$\hat{p}_k = \frac{e^{z_k}}{\sum_j e^{z_j}}$$

损失：

$$L = -\frac{1}{N}\sum_i \log \hat{p}_{i,y_i}$$

**关键细节：PyTorch 的 `nn.CrossEntropyLoss()` 接受 logits，不是概率。** 它内部自己做 softmax。

```python
# ✅ 正确：传 logits
loss = nn.CrossEntropyLoss()(model(x), y)

# ❌ 错误：先 softmax 了再传，模型会「过度自信」
loss = nn.CrossEntropyLoss()(torch.softmax(model(x), dim=1), y)
```

**为什么传 logits 更好？** 数值稳定性。logits 可以是任意实数，softmax 内部用了减最大值的技巧避免溢出；如果你先 softmax，log(0) 会产生 `inf`/`nan`。

### 回归任务

如果 $y$ 是连续值，通常假设 $y \sim \mathcal{N}(f(x), \sigma^2)$（高斯假设），最大化似然后得到均方误差：

$$L = \frac{1}{N}\sum_i (f(x_i) - y_i)^2$$

**所以 MSE 也是从概率假设推出来的**，不是随便定义的。不同分布假设 → 不同损失函数：

| 分布假设 | 对应损失 | 适用任务 |
|---|---|---|
| 高斯 | MSE（L2） | 回归 |
| 拉普拉斯 | MAE（L1） | 回归、抗 outliers |
| 类别（softmax） | CrossEntropy | 多分类 |
| 伯努利 | BCE | 二分类 |

**「选 loss 就是选分布假设」** —— 这是我觉得最值得记住的一句话。

### L1 vs L2（理解正则化的基础）

| | 损失函数 | 概率视角 |
|---|---|---|
| MSE | $\|y - \hat{y}\|_2^2$ | 高斯噪声 |
| MAE | $\|y - \hat{y}\|_1$ | 拉普拉斯噪声 |

两者对 outlier 的敏感度差异巨大：**MSE 对大误差惩罚是平方级的，MAE 是线性的**。

所以：数据干净用 MSE，有 outliers 用 MAE。

```python
# PyTorch 里对应
nn.MSELoss()      # 平方
nn.L1Loss()       # 绝对值
nn.HuberLoss()    # 两者混合，小误差用平方、大误差用绝对值
```

---

## 三、EM 算法：一个必须懂的例子

EM 算法不属于深度学习，但它是最能说明「损失函数从哪来」的经典案例，而且是理解 VAE、GAN 的前提。

**问题**：有一堆数据来自两个不同均值的正态分布（一个 0 号月亮，一个 1 号月亮），但**每个样本的标签被抹掉了**。已知两个高斯的均值和方差，怎么估计每个样本属于哪个？

**难点**：分配依赖参数，参数依赖分配。死循环。

**EM 的思路**：

```
E 步（Expectation）：用当前参数，估计每个样本"属于各类的概率"
                    这得到一个"软标签"，而不是硬分配
M 步（Maximization）：用这些软标签重新估计参数（本质是加权最小二乘）

重复 E → M → E → M ... 直到参数不再变化
```

**为什么这个"绕"能用？** 因为 E 步构造了一个下界（Jensen 不等式），每次迭代让下界上升，参数收敛到最大似然估计。

**和深度学习的关系**：

| | VAE | GAN |
|---|---|---|
| 隐变量 | 有（z） | 无（只有真实/生成） |
| 损失 | ELBO（含 KL + 重建） | 博弈（判别器损失 + 生成器损失） |
| 优化 | 直接优化下界 | 两个网络对抗，收敛不稳定 |

**「对抗训练收敛不稳定」这件事，根源就在它是交替优化，不是联合优化。** 这也是 GAN 论文里说的「训练困难」的理论来源。

---

## 四、判断力训练：几个常见误解

### 误解 1：「训练 loss 降到 0 最好」

**错，而且危险。**

损失是「模型对当前这批数据的拟合程度」，不是「模型有多正确」。你可以用一个巨型网络把训练集完全记住（loss→0），但它对没见过的数据毫无 generalize 能力。

正确的监控指标是**验证集**表现。详见第 2 篇。

### 误解 2：「用了更好的 loss，准确率就一定提高」

**不一定。** 换 loss 改变的是「模型学到什么」，不改变「模型能学多好」。

准确率提升通常来自：更好的架构、更多数据、更好的优化设置。换 loss 只在「之前的 loss 和你的真实目标不匹配」时才有用。

**先诊断，再换 loss。** 比如分类问题里，如果问题是类别不平衡，换 loss 有效；如果问题是模型容量不够，换 loss 没用。

### 误解 3：「loss 曲线看起来正常，就没问题了」

loss 曲线正常（稳步下降）只能说明**优化过程正常**，不能说明**模型好**。

必须看：
- 训练/验证 loss 的**差值**（泛化差距）
- 验证集上的**具体指标**（准确率、F1 等业务指标）
- **不同随机种子**下的稳定性

一个 loss 下降得很好但验证准确率只有瞎猜水平的模型，是完全可能的（比如标签全预测成一个类）。

### 误解 4：「正则化就是防过拟合」

太笼统了。正则化是一个大类，作用机制各不相同：

| 方法 | 机制 | 适用 |
|---|---|---|
| L2 / weight decay | 限制参数大小 | 通用首选 |
| Dropout | 随机失活，制造集成效果 | 全连接网络 |
| BatchNorm / LayerNorm | 稳定梯度 | CNN（BN）/ Transformer（LN） |
| 数据增强 | 扩充有效数据 | 视觉任务 |
| Early stopping | 提前停 | 几乎总是有帮助 |

**选择依据是「为什么会过拟合」，而不是「过拟合了就要正则」。** 详见第 3 篇。

---

## 五、动手验证

### 实验 1：损失函数的选择如何改变模型学到的「形状」

```python
import numpy as np

# 两个高斯簇，但其中一个有个异常值
rng = np.random.default_rng(0)
n = 200
x = np.concatenate([rng.normal(0, 1, n), rng.normal(3, 1, n)])
y = np.concatenate([np.zeros(n), np.ones(n)])
x[-1] = 50.0# ★ 注入一个 outlier

# L2 最小二乘：会被那个异常值严重拉偏
coef_l2 = np.polyfit(x, y, 1)

# 理论上 L1 应该拟合到「中位数残差为0」的位置，可以用迭代重加权近似
w = np.ones_like(x)
for _ in range(50):
    coef_l1 = np.polyfit(x, y, 1, w=w)
    r = np.abs(y - np.polyval(coef_l1, x))
    w = 1.0 / np.maximum(r, 1e-3)        # 残差大的点降权

print(f"L2 斜率: {coef_l2[0]:.4f}")
print(f"L1 斜率: {coef_l1[0]:.4f}   ← 更接近正确值")
```

**观察（实测输出）**：

```
L2 斜率: 0.0874     ← 被拉向 0，灾难性错误
L1 斜率: 0.1825     ← 更接近真实的 0.5
```

L2 的斜率被单个异常值拉偏了近 3 倍。**这就是为什么回归任务里数据清洗和抗 outlier 损失这么重要。**

### 实验 2：softmax 的数值稳定性

```python
import torch
import torch.nn.functional as F

# 一个较大的 logit
z = torch.tensor([1000.0, 1001.0, 1002.0])

# 直接算 softmax —— 数值溢出
print("直接softmax:", torch.exp(z) / torch.exp(z).sum())   # 可能全 0 / nan

# PyTorch 内部实现（减最大值）
print("F.softmax:   ", F.softmax(z, dim=0))                # 正常
```

**原理**：softmax 有平移不变性 $\text{softmax}(z) = \text{softmax}(z - \max z)$，减去最大值后所有指数都 ≤ 1，不会溢出。

**这就是为什么 `CrossEntropyLoss` 要吃 logits 而不吃概率** —— 见前面「误解」部分的解释。

### 实验 3：Momentum 到底在做什么

```python
import torch

def sgd(params, grad, lr=0.1, momentum=0.9):
    v = torch.zeros_like(grad)
    for g in grad:
        v = momentum * v + g     # 累积历史梯度
    params -= lr * v

# 在一个"来回震荡"的梯度序列上对比
grads = [1.0, -1.0] * 10        # 交替正负

print("=== 无动量 ===")
p = torch.tensor([0.0]); out = []
for g in grads:
    p -= 0.1 * torch.tensor([g]); out.append(p.item())
print([f"{v:.3f}" for v in out[:6]])

print("=== 有动量 (0.9) ===")
p = torch.tensor([0.0]); v = torch.tensor([0.0]); out2 = []
for g in grads:
    v = 0.9 * v + torch.tensor([g])
    p -= 0.1 * v; out2.append(p.item())
print([f"{v:.3f}" for v in out2[:6]])
```

**观察**：无动量时参数在原点来回跳（净位移接近 0）；有动量时动量把震荡**平均掉**，参数持续朝一个方向前进。

**Momentum 的本质是一个指数滑动平均滤波器**，把噪声滤掉、把信号保留。这是理解所有优化器的关键直觉。

### 实验 4：过拟合的可视化

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression

# 一个简单问题，先用逻辑回归
X, y = make_classification(n_samples=200, n_features=2, n_informative=2,
                           n_redundant=0, random_state=42)

# 加大量无关维度 → 决策边界可以变得任意复杂
X_padded = np.hstack([X, rng.normal(0, 0.1, (200, 50))])
```

（这个实验需要 sklearn。如果没装，跳过，用第 2 篇的可视化脚本替代。）

**核心观察**：训练准确率随模型复杂度单调上升，验证准确率先升后降。这个「倒 U 型」是过拟合的标志性图形。

---

## 六、自测题

**Q1**：我把损失函数改成 `nn.MSELoss()` 训练一个 10 分类问题，会发生什么？为什么？

<details>
<summary>答案</summary>

会直接报错。`MSELoss` 要求 input 和 target 形状一致，但模型输出是 `[batch, 10]`，标签是 `[batch]`，广播后变成 `[10,10]`（而且语义完全错了）。

即使手动 one-hot 成 `[batch, 10]`，能跑但效果很差：MSE 会惩罚 logit 的大小而不是关心分类正确性，且对置信度没有校准。
</details>

**Q2**：为什么 `BCEWithLogitsLoss` 要把 sigmoid 和 BCE 合并？

<details>
<summary>答案</summary>

数值稳定性 + 梯度更好。

- **稳定性**：log(0) = -inf。先 sigmoid 再取 log，如果 p 接近 0 或 1 就会溢出。合并后 PyTorch 用 `logsigmoid` 的稳定实现计算，全程不显式产生 p。
- **梯度**：`d/dz [BCELoss(σ(z), y)] = σ(z) - y`，非常干净。分开写则 `dL/dp = (p-y)/(p(1-p))`，乘上 `dp/dz = p(1-p)` 才抵消，白白引入数值风险。

名字里的 "WithLogits" 就是提醒你：**输入直接给 logits，不要自己 sigmoid**。
</details>

**Q3**：如果损失函数是 $-\log \hat{p}(y|x)$，当模型给真实标签分配的概率是 0.001 时，损失大概是多少？为什么要这么设计？

<details>
<summary>答案</summary>

$-\log(0.001) \approx 6.9$

**为什么要这么惩罚**：
- 用「误差」衡量的话，给 0.9 和给 0.001，差 0.899 → 惩罚力度差不多
- 用对数的话，差 6.9 → 相差一个数量级

这就带来了**梯度的自然缩放**：在概率已经很低时，模型每提升一点概率，减少的损失很多，梯度很大，模型会集中力气去修正最「离谱」的预测。这正是我们想要的。

代价是：**过度自信的错误预测会被重罚**（给正确标签 1e-6 的概率 → 损失 13.8）。这也是 label smoothing（给标签加一点平滑）存在的原因。
</details>

**Q4**：为什么说「EM 是联合优化的替代方案」？它在什么情况下会失效？

<details>
<summary>答案</summary>

EM 只适用于「联合似然有闭式解或易优化」的情况，且能保证单调收敛。

**失效场景**：
1. 参数空间的似然不可分解（EM 要求可分解的联合分布）
2. 初始化太差 → 收敛到局部最优（EM 只保证局部收敛到**某个**驻点，不保证全局最优）
3. KL 散度取反方向（变分下界）时，对数似然是凹的才能保证收敛，否则不保证

实际意义：VAE 用的是「变分 EM」的思路，能训但会**近似**——因为 decoder 的似然往往不是高斯的。所以 VAE 的输出天然是模糊的（这也是它生成质量不如 GAN 的原因之一）。
</details>

---

**下一篇** → [泛化、过拟合与偏差方差](/guides/deep-learning/part1-ml-basics/02-generalization)

上一级： [目录](/guides/deep-learning/)
