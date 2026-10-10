---
title: 构建模型
description: 搭出神经网络。Linear / ReLU / Softmax 到底在算什么，带手算过程。
---

> 官方原文：https://docs.pytorch.ac.cn/tutorials/beginner/basics/buildmodel_tutorial.html

---

## 导读：nn.Module 的两条铁律

PyTorch 里所有模型都继承 `nn.Module`，写法上有两条规则，违反任何一条都会报错：

### 铁律一：所有层写在 `__init__` 里

```python
class Net(nn.Module):
    def __init__(self):
        super().__init__()        # ← 别忘了这句
        self.fc = nn.Linear(784, 10)
```

**为什么要单独一个 `__init__`？** 因为 `nn.Module.__init__()` 要做一件魔法般的事：**扫描你定义的所有属性，把它们注册成这个 Module 的子模块**。只有注册过的层，`.parameters()` 才能找到它们，优化器才能更新它们。

如果你把层写在 `forward` 里，每次前向都新建一层对象，参数就丢了，模型永远学不到东西。

### 铁律二：数据流向写在 `forward` 里

```python
    def forward(self, x):
        return self.fc(x)
```

`forward` 描述「数据怎么流过这些层」。调用方式是：

```python
model(x)        # ✅ 会自动调forward，还附带 no_grad 等处理
model.forward(x)  # ❌ 别这么写
```

### 本章模型逐层拆解

```
输入 (28×28=784)
   ↓ nn.Flatten           [3,28,28] → [3,784]   把图压成一条
   ↓ nn.Linear(784,512)   [3,784] → [3,512]   y = Wx + b
   ↓ nn.ReLU              [3,512] → [3,512]   负数砍成0
   ↓ nn.Linear(512,512)   [3,512] → [3,512]
   ↓ nn.ReLU
   ↓ nn.Linear(512,10)    [3,512] → [3,10]    ←输出10个分数（logits）
```

**注意输出叫 logits 而不是概率。** logits 是范围 (-∞, +∞) 的原始分数。要概率得再过 Softmax，但那一步放在训练里会不稳定（第 6 章会讲为什么 `CrossEntropyLoss` 自己内部做了这件事）。

### 几个层的直觉

| 层 | 干什么 | 形状变化 |
|---|---|---|
| `nn.Flatten` | 展平所有非批次的维度 | `[3,28,28]` → `[3,784]` |
| `nn.Linear(a,b)` | y = Wx + b，W 是 b×a 的矩阵 | `[3,a]` → `[3,b]` |
| `nn.ReLU` | max(0, x) | 不变 |
| `nn.Softmax(dim=1)` | 一行内归一化成概率 | 不变 |
| `nn.Sequential` | 顺序容器，按顺序串起来 | — |

---

## 官方原文

### 获取训练设备

我们希望能够在 CUDA、MPS、MTIA 或 XPU 等加速器上训练模型。如果当前加速器可用，我们将使用它。否则，我们使用 CPU。

```python
import os
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
print(f"Using {device} device")
```

```
Using cuda device
```

### 定义类

我们通过继承 `nn.Module` 来定义我们的神经网络，并在 `__init__` 中初始化神经网络层。每个 `nn.Module` 子类都会在 `forward` 方法中实现对输入数据的操作。

```python
class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28*28, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 10),
        )

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits

model = NeuralNetwork().to(device)
print(model)
```

```
NeuralNetwork(
  (flatten): Flatten(start_dim=1, end_dim=-1)
  (linear_relu_stack): Sequential(
    (0): Linear(in_features=784, out_features=512, bias=True)
    (1): ReLU()
    (2): Linear(in_features=512, out_features=512, bias=True)
    (3): ReLU()
    (4): Linear(in_features=512, out_features=10, bias=True)
  )
)
```

要使用该模型，我们将输入数据传递给它。这将执行模型的 `forward`，以及一些后台操作。**请勿直接调用 `model.forward()`！**

在输入上调用模型会返回一个二维张量，其中 dim=0 对应每个输出（样本），dim=1 对应每个输出的 10 个类别的原始预测值。我们通过将这些值传递给 `nn.Softmax` 模块的一个实例来获得预测概率。

```python
X = torch.rand(1, 28, 28, device=device)
logits = model(X)
pred_probab = nn.Softmax(dim=1)(logits)
y_pred = pred_probab.argmax(1)
print(f"Predicted class: {y_pred}")
```

```
Predicted class: tensor([3], device='cuda:0')
```

### 模型层

让我们拆解 FashionMNIST 模型中的各层。我们采集一个包含 3 张 28×28 大小图像的微批次（minibatch），看看它在通过网络时会发生什么。

```python
input_image = torch.rand(3, 28, 28)
print(input_image.size())
```

```
torch.Size([3, 28, 28])
```

#### nn.Flatten

将每张二维的 28×28 图像转换为一个由 784 个像素值组成的连续数组（同时保持 dim=0 处的微批次维度）。

```python
flatten = nn.Flatten()
flat_image = flatten(input_image)
print(flat_image.size())
```

```
torch.Size([3, 784])
```

#### nn.Linear

线性层是一个使用其存储的权重和偏置对输入进行线性变换的模块。

```python
layer1 = nn.Linear(in_features=28*28, out_features=20)
hidden1 = layer1(flat_image)
print(hidden1.size())
```

```
torch.Size([3, 20])
```

#### nn.ReLU

非线性激活函数在模型的输入和输出之间建立了复杂的映射。它们在线性变换之后应用，用以引入非线性，帮助神经网络学习各种各样的现象。

```python
print(f"Before ReLU: {hidden1}\n\n")
hidden1 = nn.ReLU()(hidden1)
print(f"After ReLU: {hidden1}")
```

```
Before ReLU: tensor([[ 0.3144,  0.2564,  0.0715,  0.0674,  0.0325, -0.2803, -0.2889,  0.3323,
          0.2607, -0.2992,  0.2304,  0.0465,  0.4094, -0.2759, -0.0787,  0.2125,
          0.3665,  0.3805,  0.1715, -0.1769],
        ...
After ReLU: tensor([[0.3144, 0.2564, 0.0715, 0.0674, 0.0325, 0.0000, 0.0000, 0.3323, 0.2607,
         0.0000, 0.2304, 0.0465, 0.4094, 0.0000, 0.0000, 0.2125, 0.3665, 0.3805,
         0.1715, 0.0000],
        ...
```

看清楚了：**ReLU 就是把所有负数变成 0.0000**，正数不变。

#### nn.Sequential

`nn.Sequential` 是一个有序的模块容器。数据按照定义的相同顺序通过所有模块。

```python
seq_modules = nn.Sequential(
    flatten,
    layer1,
    nn.ReLU(),
    nn.Linear(20, 10)
)
input_image = torch.rand(3, 28, 28)
logits = seq_modules(input_image)
```

#### nn.Softmax

神经网络的最后一个线性层返回 logits—— 范围在 [-∞, +∞] 内的原始值 —— 这些值会被传递给 `nn.Softmax` 模块。这些 logits 将被缩放到 [0, 1] 区间内的值，代表模型对每个类别的预测概率。`dim` 参数指定了各值相加之和必须为 1 的维度。

```python
softmax = nn.Softmax(dim=1)
pred_probab = softmax(logits)
```

### 模型参数

神经网络内部的许多层都是参数化的，即具有在训练期间会被优化的相关权重和偏置。继承 `nn.Module` 会自动跟踪模型对象内定义的所有字段，并使所有参数可通过 `parameters()` 或 `named_parameters()` 方法访问。

```python
print(f"Model structure: {model}\n\n")

for name, param in model.named_parameters():
    print(f"Layer: {name} | Size: {param.size()} | Values : {param[:2]} \n")
```

```
Layer: linear_relu_stack.0.weight | Size: torch.Size([512, 784]) | Values : tensor([[-0.0166, -0.0180,  0.0229,  ..., -0.0333,  0.0246,  0.0229],
        [ 0.0009,  0.0007, -0.0021,  ..., -0.0105,  0.0037,  0.0194]],
       device='cuda:0', grad_fn=<SliceBackward0>)

Layer: linear_relu_stack.0.bias | Size: torch.Size([512]) | Values : tensor([-0.0041,  0.0117], device='cuda:0')
Layer: linear_relu_stack.2.weight | Size: torch.Size([512, 512]) | ...
Layer: linear_relu_stack.4.weight | Size: torch.Size([10, 512]) | ...
```

**参数名为什么是 `linear_relu_stack.0.weight` 这种形式？** 因为嵌套结构：`NeuralNetwork` → `linear_relu_stack`（Sequential） → 第 0 个模块（Linear） → `weight`。

顺手算一下参数量：`784×512 + 512×512 + 512×10 + biases = 669,706（约 67 万）`。这模型很小，跑CPU 也不慢。

---

## 动手练习

**练习 1** — 下面这个写法错在哪？为什么模型学不到东西？

```python
class BadNet(nn.Module):
    def forward(self, x):
        self.fc = nn.Linear(784, 10)
        return self.fc(x)
```

<details>
<summary>答案</summary>

层定义在了 `forward` 里。每次调用 forward 都新建一个 `nn.Linear`，参数是全新的随机值，前一次算的梯度全丢了。而且 `self.fc = ...` 这样赋值会让 PyTorch 报「Module不能被直接赋值」的错。

**结论：层必须在 `__init__` 里定义并注册。**
</details>

**练习 2** — 输入 `[64, 1, 28, 28]`，经过本章的模型后输出是什么形状？

<details>
<summary>答案</summary>

`torch.Size([64, 10])`。

链路：`[64,1,28,28]` → Flatten → `[64,784]` → Linear → `[64,512]` → ReLU → `[64,512]` → Linear → `[64,10]`。

Flatten 默认从 dim=1 开始展平，所以批次数64 保留。
</details>

**练习 3** — 手动算一个 `nn.Linear(3, 2)` 的输出。

```python
lin = nn.Linear(3, 2)
x = torch.tensor([[1.0, 2.0, 3.0]])
print(lin(x))
```

<details>
<summary>答案</summary>

输出形状 `[1, 2]`。计算：`y = W @ x + b`，其中 W 是 `[2, 3]` 矩阵，b 是 `[2]` 向量。

**亲手验证一遍**：

```python
manual = lin.weight @ x[0] + lin.bias
print(torch.allclose(manual, lin(x)[0]))    # True
```

注意这里用 `x[0]`（一维）而不是 `x`（二维），因为 W 是 `[2,3]`，`x[0]` 是 `[3]`，正好能对上。输出会和 `lin(x)[0]` 一致。

**强烈建议动手算一次**，这能帮你真正理解 Linear 在做什么。
</details>

**练习 4** — 如果把模型里的所有 `nn.ReLU()` 都删掉，训练结果会怎样？

<details>
<summary>答案</summary>

准确率会掉到接近瞎猜水平（10% 左右）。

因为多个 Linear 叠加在数学上等价于**一个** Linear——`Linear→Linear→Linear` 可以合并成一个矩阵乘法。叠层完全没意义，模型退化成一条直线，只能处理线性可分的问题。
</details>

**练习 5** — 统计模型的参数总数。

<details>
<summary>答案</summary>

```python
total = sum(p.numel() for p in model.parameters())
print(total)   # 669706
```

也可以分权重/偏置看：
```python
for name, p in model.named_parameters():
    print(name, p.numel())
```
</details>

---

**下一步** → [第 5 章：自动微分](/guides/pytorch/part2-tutorial/05-autograd)（核心章节）
