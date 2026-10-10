---
title: 正则化与容量控制
description: L1/L2 在数学上做了什么？weight decay 和 L2 正则什么时候不等价？Dropout 的原理是什么？
---

# 3 · 正则化与容量控制

> 核心问题：L1/L2 在数学上做了什么？weight decay 和 L2 正则什么时候不等价？Dropout 的原理是什么？

---

## 一、正则化的统一视角

所有正则化方法都可以看成**在原目标函数上加一个惩罚项**：

$$\min_{\theta} \underbrace{L(\theta)}_{\text{数据拟合}} + \underbrace{\lambda \cdot R(\theta)}_{\text{复杂度惩罚}}$$

区别只在$R(\theta)$ 的定义：

| 方法 | $R(\theta)$ | 效果 |
|---|---|---|
| L2 正则 / weight decay | $\|\theta\|_2^2$ | 参数整体变小，均匀收缩 |
| L1 正则 | $\|\theta\|_1$ | 参数**变稀疏**（部分归零） |
| Dropout | —（随机丢弃） | 制造集成效果 |
| Early stopping | —（早停） | 限制有效训练步数 |
| 数据增强 | —（扩充数据） | 增加有效数据量 |

**统一理解**：这些方法都在**限制模型的有效容量**，只是途径不同。

### 一个关键区分：限制「空间」还是限制「路径」

这两类正则化作用机制完全不同，这是本文最重要的观点：

| | 限制假设空间 | 限制优化路径 |
|---|---|---|
| 手段 | L1/L2、网络结构变小 | Dropout、Early stopping、BatchNorm、初始化 |
| 效果 | 最优解本身变了 | 最优解没变，但**你到不了那里** |
| 类比 | 房子盖小一点 | 走小路绕过去 |

**这个区分解释了为什么有些正则化会互相冲突**。比如强L2（缩小空间）+ 强 Dropout（限制路径），可能两个一起用反而不如单独用。

---

## 二、L2 正则（权重衰减）

### 2.1 数学推导：为什么正则项能防止过拟合

目标函数：

$$\tilde{L}(\theta) = L(\theta) + \frac{\lambda}{2}\|\theta\|_2^2$$

对参数求梯度：

$$\frac{\partial \tilde{L}}{\partial \theta_j} = \frac{\partial L}{\partial \theta_j} + \lambda \theta_j$$

**梯度下降一步**：

$$\theta_j \leftarrow \theta_j - \eta\left(\frac{\partial L}{\partial \theta_j} + \lambda \theta_j\right) = (\theta_j - \eta \frac{\partial L}{\partial \theta_j}) - \eta\lambda\theta_j$$

整理一下：

$$\boxed{\theta_j \leftarrow (1 - \eta\lambda)\theta_j - \eta\frac{\partial L}{\partial \theta_j}}$$

**看到了什么？** 参数更新 = 数据梯度的修正 − 参数自身的衰减。

每一步参数都会**按比例 $(1-\eta\lambda)$ 缩小**。这就是「权重衰减」这个名字的来源——参数被持续地往零的方向拉。

### 2.2 拉普拉斯先验的解释（贝叶斯视角）

L2 正则等价于假设参数服从**标准正态先验**：

$$p(\theta) \propto \exp\left(-\frac{\lambda}{2}\|\theta\|^2\right)$$

由贝叶斯公式：

$$p(\theta|D) \propto \underbrace{p(D|\theta)}_{\text{似然（对应 } L(\theta)\text{）}} \times \underbrace{p(\theta)}_{\text{先验（对应 } \lambda R(\theta)\text{）}}$$

**对应关系**：

| 频率派（正则化） | 贝叶斯派（先验） |
|---|---|
| 数据拟合项 $L(\theta)$ | 似然 $p(D\|\theta)$ |
| 正则项 $\lambda R(\theta)$ | 参数先验 $p(\theta)$ |
| $\lambda$ 大 | 先验强（更相信先验） |

同理：

| 正则 | 对应先验 | 参数效果 |
|---|---|---|
| L2 | 高斯 $N(0, 1/\lambda)$ | 平滑收缩，不会恰好为 0 |
| L1 | 拉普拉斯，密度在 0 处有尖峰 | **稀疏** |

**L1 稀疏性的数学原因**：拉普拉斯分布的 PDF 在 0 处最高，所以后验在 0 处的概率最大 → 很多参数恰好被压到 0。

### 2.3 L2 为什么让模型更平滑

一个直觉解释：**L2 惩罚大参数**。

回想第 1 篇——MSE 的目的是拟合噪声。而**大参数意味着对输入敏感**（$\hat{y} = Wx$，$W$ 越大，输入的小变化引起输出的大变化）。所以 L2 惩罚等价于惩罚「模型对输入的敏感度」，也就是在提升平滑性。

**平滑性 = 模型对微小扰动不敏感 = 对噪声不敏感 = 泛化更好。**

---

## 三、L1 正则与稀疏性

$$\tilde{L}(\theta) = L(\theta) + \lambda \|\theta\|_1$$

L1 的**不可导点**在 0，这导致它的解倾向于落在坐标轴上（很多参数恰好为 0）。

### L1 vs L2 的本质差异

| | L1 | L2 |
|---|---|---|
| 惩罚函数 | $\|x\|_1$，斜的 | $x^2$，光滑 |
| 稀疏性 | **有**，精确为 0 | 无，只是变小 |
| 梯度 | 子梯度：$+1$ 或 $-1$ | $2x$，与 x 成正比 |
| 收缩方式 | 均匀收缩小参数，**大参数收缩很少** | 与参数大小成比例收缩 |
| 适合 | 特征选择、稀疏模型 | 通用默认 |

**为什么 L1 产生稀疏**：直觉上，L1 对大参数的惩罚力度和 L2 不同——

- L2 惩罚 $\lambda x^2$：$x$ 越大，惩罚**越重**（所以大参数被压得厉害）
- L1 惩罚 $\lambda |x|$：惩罚**恒定**（所以大参数和小参数受到的「绝对压力」一样）

结果：大参数被 L2 压下去了但 L1 不管；小参数在 L1 下更容易被压到 0。**L1 因此偏向于「要么留下一个大的，要么完全不要」。**

### 什么时候用 L1

- **特征选择**：特征是几万个混杂在一起的信噪比时
- **需要可解释模型**：能说清哪些特征重要
- **模型压缩**：相比剪枝后直接得到小模型更方便

**实践中深度学习里很少用 L1**，因为 weight decay（L2）更稳定，且没有稀疏性需求。

---

## 四、weight decay vs L2 正则：什么时候不等价

这是最容易被忽略但面试常问的点。

### 4.1 理论上等价

L2 正则：把 $\lambda\|\theta\|^2$ 加到 loss 上。

```
optimizer.zero_grad()
loss = loss_fn(pred, y) + lambda * sum(p.pow(2).sum() for p in model.parameters())  # ← 加到 loss
loss.backward()
```

weight decay：优化器内部直接衰减参数，不经过 loss。

```python
optimizer = torch.optim.SGD(model.parameters(), lr, weight_decay=lambda)
```

### 4.2 两者的真实差异

| | L2 正则 | weight decay |
|---|---|---|
| 实现 | 手动加到 loss | 优化器内部做 `p -= lr*wd*p` |
| 梯度可见性 | 体现在 loss 数值里 | **loss 里看不到** |
| 系数与 lr 的关系 | $\lambda$ 独立 | 实际衰减率 = $\eta\lambda$，**依赖 lr** |
| 梯度裁剪的交互 | 会影响裁剪前的梯度 | 裁剪后再衰减，行为不同 |
| AMP / bf16 兼容 | 手写可能有问题 | 优化器原生支持 |

**关键差异：weight decay 的实际强度和 lr 耦合。** 因为衰减量是 $\eta\lambda\theta$——如果你把 lr 改大了，衰减也跟着变大。L2 正则则不受 lr 影响。

**实践建议：优先用 weight decay**（优化器原生支持，和 AMP/分布式兼容），不要手写 L2 加到 loss 上。

### 4.3 哪些参数不该衰减

这是现代实践里很重要的一点：**bias 和 LayerNorm/BatchNorm 的参数不应该做 weight decay**。

原因：
- bias 的作用是平移决策边界，衰减它没有正则化意义
- BN/LN 的 $\gamma, \beta$ 是缩放平移参数，它们应该自由调整

```python
decay, no_decay = [], []
for name, p in model.named_parameters():
    if not p.requires_grad:
        continue
    # 1维参数（BN/LN 的 weight 和 bias）以及所有 bias，都不衰减
    if p.ndim <= 1 or name.endswith(".bias"):
        no_decay.append(p)
    else:
        decay.append(p)

optimizer = torch.optim.AdamW([
    {'params': decay,    'weight_decay': 0.05},
    {'params': no_decay, 'weight_decay': 0.0},
], lr=3e-4)
```

**这是所有主流 LLM 微调代码的标准写法**（如 HuggingFace、LLaMA 微调脚本）。面试如果问「你怎么调weight decay」，能说出这一段是加分项。

---

## 五、Dropout 的原理

### 5.1 做了什么

训练时，每个神经元以概率 $p$ 被丢弃（置零）。测试时，**不做丢弃**，而是把激活值除以 $1-p$（PyTorch 用 inverted dropout：训练时除以 $1-p$）。

### 5.2 为什么有效：集成视角

一个关键洞察：**Dropout 每次前向都在训练一个不同的子网络**。

```
第1次前向: 用神经元 {1,3,5,7}
第2次前向: 用神经元 {2,4,6}
第3次前向: 用神经元 {1,2,6,8}
...
```

训练 $N$ 次等于训练了 $N$ 个不同结构的模型，每个都只看到部分数据。推理时用全部神经元，相当于对这些子网络的**集成平均**。

$$\mathbb{E}[\text{输出}] \approx \text{各个子网络输出的加权平均}$$

**这就是为什么 Dropout 能降低方差**——集成学习降低方差，这是机器学习的基本结论。

### 5.3 常见误解

| 误解 | 事实 |
|---|---|
| Dropout 能防止梯度消失 | 不能，那是 ResNet 和归一化的作用 |
| Dropout 越多越好 | 太大（>0.5）会大量损失信息，训练变慢 |
| Dropout 在推理时也随机 | **错误**，推理时是确定的。忘了 `eval()` 就是 bug |
| BatchNorm 和 Dropout 二选一 | 实践中常一起用（分类任务），但 LLM 里都不用 Dropout |

### 5.4 现代替代品

| 方法 | 相比 Dropout 的优势 |
|---|---|
| DropPath / Stochastic Depth | 训练更稳定，是 ResNet 的默认做法 |
| DropConnect | 丢弃的是权重而不是激活，有理论分析支持 |
| LayerDrop / DropBlock | 对卷积特征图做块状丢弃，更适合 CNN |
| **不用任何 Dropout** | 现代 LLM 普遍不用，靠数据规模和 weight decay 控制过拟合 |

**LLM 为什么不用 Dropout**：预训练数据量足够大（远超参数量），过拟合风险低；而 Dropout 会让梯度估计噪声变大，对大规模训练的效率不利。

---

## 六、Early Stopping 与学习率的关系

Early stopping 的逻辑：监控验证指标，当连续 N 轮不再改善就停止。

### 和 weight decay 的深层联系

有个有趣的理论联系值得知道：

> 在线性模型 + SGD 的设定下，「跑T 步的 SGD」与「L2 正则 + 特定步长」的解是**等价**的。

也就是说，**early stopping 在做的事，和 weight decay 在做的事，本质上是一回事**——都是「阻止参数走到极端」。

这个结论（Karpathy 的 practical deep learning lecture 里有详细推导）解释了：

- 为什么 early stopping 和 weight decay 可以互相替代
- 为什么它们的最佳强度需要一起调（同时用太强会「过度正则」）

---

## 七、动手实验

### 实验 1：L2 正则的权重衰减效应

亲手看到参数被「拉向零」。

```python
import torch
from torch import nn

torch.manual_seed(42)
X = torch.randn(100, 10)
y = X @ torch.randn(10, 1) + 0.01 * torch.randn(100, 1)   # 真权重

def train(l2_lambda=0.0, steps=2000, lr=0.05):
    torch.manual_seed(42)
    model = nn.Linear(10, 1, bias=False)
    w_true = model.weight.detach().clone() # 初始化时的权重
    opt = torch.optim.SGD(model.parameters(), lr=lr, weight_decay=l2_lambda)
    for _ in range(steps):
        loss = ((model(X) - y) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    return model.weight.detach(), w_true, loss.item()

for l2 in [0.0, 0.001, 0.01, 0.1]:
    w, w0, final = train(l2)
    print(f"l2={l2:<7} ||w||={w.norm():.4f}  loss={final:.5f}")
```

**实测输出**：

```
l2=0.0     ||w||=4.4956  loss=0.00011
l2=0.001   ||w||=4.4933  loss=0.00011
l2=0.01    ||w||=4.4721  loss=0.00063
l2=0.1     ||w||=4.2732  loss=0.04749
```

**观察**：$l_2$ 越大，$\|w\|$ 越小，训练损失越高。这就是「偏差-方差权衡」的实证——压得越狠，训练越差但泛化可能越好。

注意这个任务是**无噪声线性回归**（生成数据时用了同一个 `torch.randn(10,1)`），所以真实最优 $\lambda = 0$。**如果你的任务有噪声，$\lambda > 0$ 应该在验证集上真的更好**——这是检验正则化是否有效的正确方式。

### 实验 2：L1 产生稀疏，L2 不产生

```python
import torch
from torch import nn

def train_with(penalty, steps=3000):
    torch.manual_seed(42)
    X = torch.randn(200, 20)
    # 真实只有前 3 个维度有效，其余是噪声
    w_true = torch.zeros(20, 1); w_true[:3] = torch.randn(3, 1)
    y = X @ w_true + 0.1 * torch.randn(200, 1)

    w = nn.Parameter(torch.zeros(20, 1))    # 从零初始化（实验用）
    opt = torch.optim.Adam([w], lr=0.01)
    for _ in range(steps):
        pred = X @ w
        l2 = penalty(w.pow(2).sum())
        l1 = penalty(w.abs().sum())
        loss = ((pred - y) ** 2).mean() + l2 * 0.01 + l1 * 0.01
        opt.zero_grad(); loss.backward(); opt.step()
    return w.detach().flatten()

torch.manual_seed(0)
for name, penalty in [("L2", torch.norm), ("L1", torch.abs)]:
    w = train_with(penalty)
    n_zero = (w.abs() < 1e-3).sum().item()
    print(f"{name}: 零参数 {n_zero}/20   ||w||={w.norm():.3f}   前3维={[round(v,3) for v in w[:3].tolist()]}")
```

**你会观察到**：L1 产生大量恰好为 0 的参数（稀疏），L2 只是把所有参数缩小。

### 实验 3：dropout 的集成视角

验证「不同 dropout 模式 = 不同子网络」。

```python
import torch
from torch import nn

torch.manual_seed(0)
model = nn.Sequential(nn.Linear(20, 64), nn.ReLU(), nn.Dropout(0.5), nn.Linear(64, 10))
model.eval()                # 注意：必须 eval，否则每次输出都不同

x = torch.randn(1, 20)
with torch.no_grad():
    outputs = [model(x) for _ in range(5)]
print("eval 模式下 5 次输出是否一致:", all(torch.allclose(outputs[0], o) for o in outputs))

model.train()                # 切回 train
with torch.no_grad():
    outputs = [model(x) for _ in range(5)]
print("train 模式下 5 次输出是否一致:", all(torch.allclose(outputs[0], o) for o in outputs))
```

**输出**：`eval 模式下 True`，`train 模式下 False`

**这就是为什么推理必须 `eval()`。**

### 实验 4：weight decay 的强度和 lr 绑定

这条差异可以精确验证：把梯度手动置零，让**只有 weight decay 在起作用**，然后对比不同 lr 下的衰减量。

```python
import torch

torch.manual_seed(42)
w0 = torch.randn(20)

print("梯度置零，只剩weight decay 的效果（wd=0.1）")
for lr in [0.001, 0.01, 0.1, 1.0]:
    w = w0.clone().requires_grad_(True)
    opt = torch.optim.SGD([w], lr=lr, weight_decay=0.1)
    before = w.detach().clone()

    w.grad = torch.zeros_like(w)      # ★ 关键：把数据梯度清零
    opt.step()

    predicted = lr * 0.1 * before.abs().mean()          # 公式：lr * wd * |w|
    actual = (before.abs().mean() - w.detach().abs().mean()).item()
    print(f"lr={lr:<7} 公式预测={predicted:.6f}  实际={actual:.6f}  比值={actual/predicted:.2f}")
```

**实测输出**：

```
lr=0.001   公式预测=0.000080  实际=0.000080  比值=1.00
lr=0.01    公式预测=0.000802  实际=0.000802  比值=1.00
lr=0.1     公式预测=0.008015  实际=0.008016  比值=1.00
lr=1.0     公式预测=0.080154  实际=0.080155  比值=1.00
```

**三个结论**：

1. **公式精确成立**：衰减量就是 $\eta\lambda\theta$，比值全是 1.00。
2. **衰减量随 lr 线性变化**：lr 放大 10 倍，衰减量也放大 10 倍。**这正是 weight decay 和 L2 的差异所在。**
3. 如果你用 L2 加到 loss 上，衰减量会是 $\lambda\theta$（**不含 lr**），和 lr 无关。

> 这个实验也解释了为什么「把 lr 调大一倍，正则化强度也跟着变强一倍」。用 lr schedule 时（比如 warmup），实际正则强度是在变的。

> 我最初试过在完整训练里对比不同 lr 的 $\|w\|$，结果看不出差异——因为任务很快就收敛了，收敛后的 $\|w\|$ 由数据拟合需求主导，衰减的影响被淹没。**做实验时如果观察不到预期现象，先怀疑实验设置。** 隔离变量（梯度置零）是更可靠的做法。

---

## 八、自测题

**Q1**：为什么 bias 不做 weight decay？

<details>
<summary>答案</summary>

三个理由：

1. **无正则意义**：weight decay 惩罚的是「模型对输入的敏感度」（大权重 → 对输入敏感 → 平滑性差）。而 bias 的作用是**平移决策边界**，对输入敏感度没有贡献。衰减 bias 只会让决策边界往原点靠，纯属有害。
2. **数学上**：bias 通常初始化为 0，如果持续衰减，它永远接近 0，等于关闭了 bias 项。
3. **和 norm 层同理**：LayerNorm 的 $\gamma, \beta$、BatchNorm 的 $\gamma, \beta$ 都是 1 维参数（`p.ndim == 1`），它们的作用是缩放和平移，同样不该衰减。

所以标准做法是：`if p.ndim <= 1 or name.endswith('.bias'): 不衰减`。这是所有主流 LLM 微调代码的标准配置。
</details>

**Q2**：为什么 Dropout 在推理时要除以 $1-p$（或者反过来乘保留概率）？

<details>
<summary>答案</summary>

为了**让训练和推理的期望输出一致**。

训练时，神经元以概率 $p$ 被置零。某个神经元的激活值 $x$：
- 以概率 $1-p$ 保留：期望贡献 $(1-p)x$
- 以概率 $p$ 丢弃：贡献 0

所以期望是 $(1-p)x$。如果不修正，训练时的期望输出会比推理时小 $(1-p)$ 倍，推理时输出会系统性偏大。

两种修正方式：
- **inverted dropout**（PyTorch 用）：训练时激活值除以 $1-p$，推理时不修正
- 训练时不修正，推理时所有激活值乘 $1-p$

两种等价，PyTorch 选前者是为了推理时更简单高效。
</details>

**Q3**：现代 LLM（如 LLaMA）为什么不用 Dropout？

<details>
<summary>答案</summary>

三个原因：

1. **过拟合风险低**：预训练数据量（万亿 token 级）远超参数量，模型几乎不会过拟合。这是数据规模化的直接收益。
2. **梯度噪声影响效率**：大规模预训练是吞吐敏感的。Dropout 引入随机梯度噪声，需要更多步数收敛，训练效率下降。
3. **有更好的替代手段**：
   - weight decay（AdamW）控制参数规模
   - 大量数据 + 更深的网络本身就有正则化效应
   - 现代预训练配方里正则化项占很小比重

**但 LoRA 等高效微调方法下，情况不同**：数据量小（几万条），过拟合风险高，所以微调时反而会用 dropout（LoRA 原论文就用 0.05）。**这说明正则化的选择取决于数据量与模型容量的比值，不存在「永远不用」或「永远用」的规则。**
</details>

**Q4**：手写 L2 正则加到 loss 上和用 weight_decay，如果你的 lr schedule 用了 warmup，两种会有区别吗？

<details>
<summary>答案</summary>

**会有区别，而且值得注意。**

warmup 期间 lr 很小（接近 0），此时：
- **weight decay** 的衰减量 $\eta\lambda\theta$ 也很小 → 几乎没有衰减
- **L2 加到 loss**：梯度 $\lambda\theta$ 是常数项，**不依赖 lr** → 照常衰减

所以 warmup 初期，L2 正则的实际强度比 weight decay **更强**。

如果 warmup 阶段 loss 出现异常（比如初期就过拟合），可以考虑：

```python
# 让 weight decay 跳过 warmup（部分实现的做法）
if current_step < warmup_steps:
    for group in optimizer.param_groups:
        group['weight_decay'] = 0.0
```

不过实践中大多数框架的 weight decay 实现里，这两者差异被忽略了，因为 warmup 阶段的权重还很小，衰减多少都无所谓。
</details>

---

**下一篇** → [优化器：从 SGD 到 AdamW](/guides/deep-learning/part1-ml-basics/04-optimizers)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part1-ml-basics/02-generalization)
