---
title: 自动微分
description: PyTorch 最核心也最难懂的一章：梯度是什么、计算图怎么建、反向传播怎么走。
---

> 官方原文：https://docs.pytorch.ac.cn/tutorials/beginner/basics/autogradqs_tutorial.html
>
> **这是整套教程的核心章节，也是唯一一章真正需要理解的原理。** 前 4 章都是准备工作。

---

## 导读：为什么这一章最重要

训练神经网络的标准流程叫**反向传播**：算出「损失函数关于每个参数的梯度」，然后按梯度方向把参数往回调。

问题在于：一个深网络有几十万甚至几百万个参数，**手算每个参数的偏导数是不可能的**。

PyTorch 的 autograd 引擎解决了这件事：你只需要在正向计算时**记录下所有算子**，然后调一次 `loss.backward()`，它就用链式法则把所有梯度**自动算出来**。

> 一句话：**autograd 就是帮你自动求导的记账员。**

---

## 一、先理解「梯度」到底是什么

### 从一个最简单的函数说起

假设损失是 $L(w) = w^2$。我们已经算出当前 $w=3$，那么 $L(9)$。

要让它变小，该往哪走？

**导数告诉你答案。** $\frac{dL}{dw} = 2w = 6$。

- 梯度为正 → $w$ 增大会让损失变大 → 所以 $w$ 要**减小**
- 更新：`w = w - 学习率 × 梯度 = 3 - 0.1× 6 = 2.4`

再算一轮：$\frac{dL}{dw}=4.8$ → `w = 2.4 - 0.1×4.8 = 1.92`。损失从 9 → 5.76 → 3.69，一路下降。

**这就是梯度下降。** 「往负梯度方向走」。

### 一层网络：不止一个参数

现在稍微复杂一点。官方原文的例子：

```python
z = torch.matmul(x, w) + b        # x=[5], w=[5,3], b=[3] → z=[3]
loss = torch.nn.functional.binary_cross_entropy_with_logits(z, y)
```

这里 `w`（5×3 = 15 个数）和 `b`（3 个数）都需要求梯度。我们想知道：

$$\frac{\partial loss}{\partial w} \quad (15 个数), \qquad \frac{\partial loss}{\partial b} \quad (3 个数)$$

**手推这条链式法则会非常痛苦。** autograd 帮你做了。

### 链式法则：autograd 的底层逻辑

`loss` 的计算链路是：

```
x ──┐w ──┐
    ├── matmul ── + ── z ── BCEWithLogits ── loss
b ──┘           ↑
                grad_fn: AddBackward0
```

每个中间结果都记住了「我是怎么算出来的」，并且知道「要算我的梯度，得先知道下游传过来的梯度」。

`loss.backward()` 从根节点开始，反着走：`loss.grad_fn` 算出下游梯度 → 传给 `z` → `z` 拿到梯度后用自己的公式反推，算出 `matmul` 和 `+` 的两个输入的梯度 → 继续往前……直到叶子节点 `w` 和 `b`。

**最终结果存在 `w.grad` 和 `b.grad` 里。**

---

## 二、必须记住的四条规则

| 规则 | 代码 | 说明 |
|---|---|---|
| 标记需要梯度 | `requires_grad=True` | 必须在**创建时**设，或用 `x.requires_grad_(True)` |
| 从根节点反传 | `loss.backward()` | 必须在 scalar（单个数）上调用 |
| 梯度存哪 | `w.grad` | **累加**的，不是覆盖 |
| 关闭追踪 | `with torch.no_grad():` | 推理时用，省内存更快 |

### 关于 `requires_grad`

`requires_grad` 的含义是：「这个张量参与计算，请顺便记下计算过程」。

```python
w = torch.randn(5, 3, requires_grad=True)   # 创建时就标记
x = torch.randn(5)
x.requires_grad_(True)                       # 或者事后标记
```

**叶子张量 vs 非叶子张量**：只有叶子张量（你直接创建、没经过任何运算的）才有 `.grad`。中间结果 `z`、`loss` 的 `.grad` 是 `None`，它们只有 `.grad_fn`（记录了反向函数）。这是因为中间张量会被释放，不值得存梯度。

### 关于梯度累加（新手第一个 bug）

```python
loss.backward()
loss.backward()   # 梯度会翻倍！
```

梯度是**累加**的。每次 `.backward()` 都会把新梯度**加到**已有的 `.grad` 上。训练循环里必须有：

```python
optimizer.zero_grad()   # 每次更新前清零
```

第 6 章会再强调这件事，因为它是最常见的错误来源。

---

## 三、`torch.no_grad()` 为什么必须用

训练时我们要梯度，推理时（模型已训好，只想预测）**不需要**。但只要张量还带 `requires_grad=True`，PyTorch 就会一直记录计算图，**浪费显存和时间**。

```python
with torch.no_grad():
    pred = model(x)   # 不记录计算图
```

三种等价做法：

```python
# 1. no_grad 上下文（推荐）
with torch.no_grad():
    z = torch.matmul(x, w) + b

# 2. detach —— 切断与计算图的连接
z = torch.matmul(x, w) + b
z_det = z.detach()

# 3. eval + no_grad 组合（推理的标准写法）
model.eval()
with torch.no_grad():
    pred = model(x)
```

**用途**：
- 冻结部分参数（`p.requires_grad_(False)`）
- 只做正向传播时提速省显存

---

## 四、计算图是**动态**的

这点很多人不理解但很关键：**PyTorch 的计算图是每次 forward 重新建的**。

```python
for batch in dataloader:
    if batch.size(0) == 1:      # 条件分支改变图的结构
        pred = model(batch)
    else:
        pred = model(batch.unsqueeze(0))
```

因为图是现搭的，你可以在模型里写 `if`、`for`、`while`，可以每个 iteration 用不同形状的数据。**这是 PyTorch 相比静态图框架（TensorFlow 1.x）的最大优势**——用起来像写普通 Python。

---

## 官方原文

### 计算梯度

在训练神经网络时，最常用的算法是反向传播。参数（模型权重）会根据损失函数关于该参数的梯度进行调整。

为了计算这些梯度，PyTorch 拥有内置的微分引擎 `torch.autograd`。它支持对任何计算图自动计算梯度。

考虑最简单的一层神经网络，具有输入 `x`、参数 `w` 和 `b`，以及某个损失函数：

```python
import torch

x = torch.ones(5)               # input tensor
y = torch.zeros(3)              # expected output
w = torch.randn(5, 3, requires_grad=True)
b = torch.randn(3, requires_grad=True)
z = torch.matmul(x, w) + b
loss = torch.nn.functional.binary_cross_entropy_with_logits(z, y)
```

### 张量、函数和计算图

这段代码定义了以下计算图：

```
x ──── matmul ────┐
                  ├── add ──── BCEWithLogits ──── loss
w ────────────────┘ ↑
b ───────────────────┘
```

在这个网络中，`w` 和 `b` 是我们需要优化的参数。因此，我们需要能够计算损失函数关于这些变量的梯度。为此，我们设置这些张量的 `requires_grad` 属性。

您可以在创建张量时设置 `requires_grad` 的值，或者稍后使用 `x.requires_grad_(True)` 方法。

我们应用于张量以构建计算图的函数实际上是类 `Function` 的一个对象。该对象知道如何计算正向方向的函数，以及如何在反向传播步骤中计算其导数。指向反向传播函数的引用存储在张量的 `grad_fn` 属性中。

```python
print(f"Gradient function for z = {z.grad_fn}")
print(f"Gradient function for loss = {loss.grad_fn}")
```

```
Gradient function for z = <AddBackward0 object at 0x7f9b346651e0>
Gradient function for loss = <BinaryCrossEntropyWithLogitsBackward0 object at 0x7f9b34666980>
```

**`grad_fn` 的命名规则**：`AddBackward0` = 加法的反向函数，`ReluBackward0` = ReLU 的反向函数，`MatmulBackward0` 之类。名字末尾的 0 表示这是该算子的第 0 个实例。

### 计算梯度

我们调用 `loss.backward()`，然后从 `w.grad` 和 `b.grad` 中检索值。

```python
loss.backward()
print(w.grad)
print(b.grad)
```

```
tensor([[0.1700, 0.1906, 0.0093],
        [0.1700, 0.1906, 0.0093],
        [0.1700, 0.1906, 0.0093],
        [0.1700, 0.1906, 0.0093],
        [0.1700, 0.1906, 0.0093]])
tensor([0.1700, 0.1906, 0.0093])
```

先别纠结具体数值，重点是看它的形状：`w.grad` 和 `w` 形状一样 `[5,3]`，`b.grad` 和 `b` 形状一样 `[3]`。**梯度与它对应的张量同形状。**

为什么每一行都一样？因为 `x = torch.ones(5)`，所有元素相同，所以每个位置的梯度贡献也相同。

**两个重要提醒**：

- 我们只能获取计算图中**叶子节点**的 `grad` 属性，且这些节点的 `requires_grad` 必须为 `True`。
- 出于性能原因，对于给定的计算图，我们只能使用 `backward` 执行**一次**梯度计算。如果需要多次调用，必须传 `retain_graph=True`。

### 禁用梯度跟踪

默认情况下，所有设置了 `requires_grad=True` 的张量都会跟踪其计算历史并支持梯度计算。但在某些情况下我们不需要这样做，例如模型已训好、只想做正向计算时。

```python
z = torch.matmul(x, w) + b
print(z.requires_grad)

with torch.no_grad():
    z = torch.matmul(x, w) + b
print(z.requires_grad)
```

```
True
False
```

等效方法是在张量上使用 `detach()`：

```python
z = torch.matmul(x, w) + b
z_det = z.detach()
print(z_det.requires_grad)
```

```
False
```

您可能需要禁用梯度跟踪的原因包括：

- 将神经网络中的某些参数标记为冻结参数
- 在只进行正向传播时加速计算

### 更多关于计算图的内容

autograd 在一个由 `Function` 对象组成的有向无环图（DAG）中，保存了数据（张量）以及所有执行的操作（连同由此产生的新张量）的记录。在这个 DAG 中，叶子节点是输入张量，根节点是输出张量。通过从根节点到叶子节点追踪这个图，您可以使用链式法则自动计算梯度。

**在正向传播中，autograd 同时执行两件事**：

- 运行请求的操作以计算结果张量
- 在 DAG 中维护操作的梯度函数

**当在 DAG 根节点上调用 `.backward()` 时**，autograd 执行：

- 计算来自每个 `.grad_fn` 的梯度
- 将它们累加到对应张量的 `.grad` 属性中
- 使用链式法则，一路传播到叶子张量

### 在 PyTorch 中 DAG 是动态的

计算图是从头开始重新构建的；在每次调用 `.backward()` 后，autograd 开始构建一个新的计算图。这正是允许您在模型中使用控制流语句的原因；如果需要，您可以在每次迭代时更改张量的形状、大小以及执行的操作。

### 选读：张量梯度和雅可比乘积

在许多情况下，我们有一个**标量**损失函数，需要计算关于某些参数的梯度。但如果输出函数是一个任意张量呢？PyTorch 允许你计算所谓的**雅可比乘积**（Jacobian product），而不是实际的梯度。

对于向量函数 $\vec{y}=f(\vec{x})$，其梯度由雅可比矩阵 $J$ 给出。PyTorch 允许你为给定的输入向量 $v$ 计算 $v^T \cdot J$，而不是直接计算雅可比矩阵本身。这是通过调用 `backward` 并将 `v` 作为参数传递来实现的。

```python
inp = torch.eye(4, 5, requires_grad=True)
out = (inp + 1).pow(2).t()
out.backward(torch.ones_like(out), retain_graph=True)
print(f"First call\n{inp.grad}")

out.backward(torch.ones_like(out), retain_graph=True)
print(f"\nSecond call\n{inp.grad}")

inp.grad.zero_()
out.backward(torch.ones_like(out), retain_graph=True)
print(f"\nCall after zeroing gradients\n{inp.grad}")
```

```
First call
tensor([[4., 2., 2., 2., 2.],
        [2., 4., 2., 2., 2.],
        ...])

Second call
tensor([[8., 4., 4., 4., 4.],     ← 注意：变成了 2 倍！
        [4., 8., 4., 4., 4.],
        ...])

Call after zeroing gradients
tensor([[4., 2., 2., 2., 2.],     ← zero_() 之后恢复正常
        [2., 4., 2., 2., 2.],
        ...])
```

**这一段极其重要**，它直观展示了梯度累加：第二次调用结果翻倍，`zero_()` 之后又恢复正常。实际训练中优化器的 `zero_grad()` 就是干这个的。

> 之前我们调用 `backward()` 没有参数，这实际上等同于 `backward(torch.tensor(1.0))`——对于标量值函数来说是个方便的简写。

---

## 动手练习

**练习 1** — 为什么 `w.grad` 的形状一定等于 `w` 的形状？

<details>
<summary>答案</summary>

因为梯度就是「损失对每个元素的偏导数」，每个元素对应一个偏导数。所以数量必须一一对应，形状相同。

这也是为什么优化器可以直接用 `zip(model.parameters(), grads)` 来配对更新。
</details>

**练习 2** — 手算 `x=2`，`w=3`，`loss = w*x^2`，求 `loss` 对 `w` 的梯度。

<details>
<summary>答案</summary>

$\frac{\partial loss}{\partial w} = x^2 = 4$

代码验证：
```python
x = torch.tensor(2.0)
w = torch.tensor(3.0, requires_grad=True)
loss = w * x**2
loss.backward()
print(w.grad)   # 4.0
```
</details>

**练习 3** — 下面这段代码的输出是什么？为什么 `z.grad` 是 `None`？

```python
x = torch.ones(5)
w = torch.randn(5, 3, requires_grad=True)
z = torch.matmul(x, w)
print(z.grad)
print(z.grad_fn)
```

<details>
<summary>答案</summary>

`z.grad` 是 `None`，因为 `z` 不是叶子张量（它是由 `matmul` 计算出来的）。只有叶子张量才有 `.grad`；中间张量有的是 `.grad_fn`（这里应该是 `MatmulBackward0` 或 `AddmmBackward0`）。

梯度会被继续往叶子节点传，`z` 自己不保存梯度。
</details>

**练习 4** — 找出这段代码的 bug：

```python
for batch, (X, y) in dataloader:
    pred = model(X)
    loss = loss_fn(pred, y)
    loss.backward()
    optimizer.step()
```

<details>
<summary>答案</summary>

缺少 `optimizer.zero_grad()`。梯度会跨batch 累加，等于把前面所有 batch 的梯度加在一起更新参数，训练完全坏掉。

正确顺序：
```python
    optimizer.zero_grad()   # 1. 清零
    pred = model(X)
    loss = loss_fn(pred, y)
    loss.backward()        # 2. 反传，梯度累加到 .grad
    optimizer.step() # 3. 更新
```
</details>

**练习 5** — 为什么 `x` 是输入、不需要梯度，而 `w` 需要？

<details>
<summary>答案</summary>

如果我给 `x` 也加了 `requires_grad=True`，训练循环里 `loss.backward()` 会在**输入张量**上也累加梯度，越积越多占内存。

**结论**：只给**需要优化的参数**（模型权重）加 `requires_grad=True`。PyTorch 里这一步是自动的——`nn.Parameter` 默认就带 `requires_grad=True`，第 6 章会看到。
</details>

**练习 6**（挑战）— 用 autograd 实现「对一个数求导」：

```python
def derivative(f, x, eps=1e-5):
    """用中心差分近似求 f 在 x 处的导数"""
    return (f(x + eps) - f(x - eps)) / (2 * eps)

f = lambda t: t**2
print(derivative(f, torch.tensor(3.0)))   # 应该是 6.0
```

<details>
<summary>答案</summary>

输出 `tensor(6.0000)`。这就是数值微分。

对比一下 autograd 的做法：
```python
w = torch.tensor(3.0, requires_grad=True)
f(w).backward()
print(w.grad)   # tensor(6.)
```

**两者结果一致，但原理完全不同**：数值微分靠「猜」（试两个点算差值，精度受 `eps` 影响），autograd 靠**链式法则精确推导**。这也是 autograd 比手动数值微分快几个数量级的原因——网络有 67 万个参数时，数值微分要跑 67 万次前向传播。
</details>

---

**下一步** → [第 6 章：优化模型参数](/guides/pytorch/part2-tutorial/06-optimization)
