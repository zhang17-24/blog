---
title: 优化模型参数
description: 训练循环：前向、算损失、反向、更新权重。学习率调大调小分别会发生什么。
---

> 官方原文：https://docs.pytorch.ac.cn/tutorials/beginner/basics/optimization_tutorial.html
>
> 这一章把所有零件组装起来：**训练循环**。

---

## 导读：训练循环的本质

第 5 章你已经知道怎么算梯度。这一章回答：拿到梯度之后，参数该怎么改？

```
反复做：
  1. 把一批数据喂给模型      → 前向
  2. 算出损失 loss
  3. 反向传播算梯度          → 第5章
  4. 按梯度更新参数          → 优化器
```

**这就是全部。** 你可以把训练想象成下山：损失是海拔，梯度是当前最陡的上坡方向，优化器就是每一步迈多大。

---

## 一、三个超参数

超参数是**你手动调的、不是学出来的**参数。

| 超参数 | 本教程值 | 含义 | 调大会怎样 |
|---|---|---|---|
| `epochs` | 5~10 | 完整过几遍数据集 | 时间线性增加，可能过拟合 |
| `batch_size` | 64 | 每次更新用几张图 | 更大→显存占用高，但梯度更稳 |
| `learning_rate` | 1e-3 | **每步更新幅度** | **最容易出事的一个** |

### 学习率的影响

`lr` 是整个训练里最重要的旋钮：

- **太小**（如 1e-6）：loss 几乎不动，训练像卡住了，学得极慢
- **太大**（如 1.0）：loss 剧烈震荡甚至变成 `nan`，模型彻底崩掉
- **太大一点点**（如 0.1）：loss 先降后回升，训练不稳定
- **合适**（1e-3 附近）：loss 平稳下降

**遇到 loss 变成 `nan` 或 `inf`，第一件事就是调小学习率。**

---

## 二、损失函数怎么选

`nn.CrossEntropyLoss()` 是分类任务的标准选择。它做的事情：

```
输入：模型输出的 logits（10 个原始分数）
      真实标签（一个整数，比如 3）
内部：先 softmax 变概率，再算对数损失
输出：一个标量，越小越好
```

**关键点：标签传整数，不是 one-hot。** 这就是第 3 章说过的 PyTorch 推荐做法。

其他常见损失：

| 损失 | 适用任务 |
|---|---|
| `nn.CrossEntropyLoss()` | **多分类**（本教程） |
| `nn.BCEWithLogitsLoss()` | 二分类（多标签） |
| `nn.MSELoss()` | 回归 |

---

## 三、优化循环的三步（必须背下来）

```python
optimizer.zero_grad()   # 1. 把上一轮残留的梯度清零
loss.backward()        # 2. 反向传播，梯度累加到参数上
optimizer.step()       # 3. 按梯度更新参数
```

**顺序不能乱。** 第 5 章已经解释过为什么需要 `zero_grad()`：梯度是累加的，不清零就等于把历史梯度全算进去。

优化器初始化：

```python
optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
```

`model.parameters()` 把模型所有需要训练的参数交给优化器管理。后面所有第 6、7 章的训练都是这个模式。

**顺便一提**：`model.parameters()` 里的参数都是 `nn.Parameter` 类型，它们默认 `requires_grad=True`——这就是第 5 章说的「PyTorch 自动给需要优化的参数打了标记」。

---

## 四、`model.train()` 和 `model.eval()` 别搞混

| 方法 | 干什么 | 什么时候用 |
|---|---|---|
| `model.train()` | 启用 dropout / batchnorm 的**训练行为** | 训练循环开头 |
| `model.eval()` | 切到**评估行为**（dropout 关闭等） | 测试循环开头 |
| `torch.no_grad()` | 不算梯度 | 评估时配合用 |

本教程的模型没有 dropout 和 batchnorm，所以这两个调用「本例中不必要」，但官方仍然写上了——**因为这是标准习惯，别省。** 等你用到 ResNet 之类的网络，忘了 `model.eval()` 会导致评估结果随机波动。

---

## 官方原文

### 预备代码

我们加载前几节关于数据集与数据加载器和构建模型的代码。

```python
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import v2

training_data = datasets.FashionMNIST(
    root="data", train=True, download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
)
test_data = datasets.FashionMNIST(
    root="data", train=False, download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
)

train_dataloader = DataLoader(training_data, batch_size=64)
test_dataloader = DataLoader(test_data, batch_size=64)

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

model = NeuralNetwork()
```

### 超参数

超参数是可调节的参数，能让你控制模型的优化过程。不同的超参数值会影响模型训练和收敛速度。

我们为训练定义以下超参数：

- **迭代轮数（Number of Epochs）** — 遍历整个数据集的次数
- **批大小（Batch Size）** — 在更新参数之前传播到网络中的数据样本数量
- **学习率（Learning Rate）** — 在每个批次/轮次中更新模型参数的幅度。较小的值会导致学习速度缓慢，而较大的值可能会在训练期间导致不可预测的行为

```python
learning_rate = 1e-3
batch_size = 64
epochs = 5
```

### 损失函数

面对某些训练数据时，我们未受训练的网络可能不会给出正确的答案。损失函数衡量所得结果与目标值之间的不相似程度，而我们在训练期间想要最小化的正是这个损失函数。

常见的损失函数包括用于回归任务的 `nn.MSELoss`（均方误差）以及用于分类的 `nn.NLLLoss`（负对数似然）。`nn.CrossEntropyLoss` 结合了 `nn.LogSoftmax` 和 `nn.NLLLoss`。我们将模型的输出 logits 传递给 `nn.CrossEntropyLoss`，它将归一化 logits 并计算预测误差。

```python
loss_fn = nn.CrossEntropyLoss()
```

### 优化器

优化是在每个训练步骤中调整模型参数以减少模型误差的过程。优化算法定义了如何执行这个过程（在此示例中，我们使用随机梯度下降）。所有的优化逻辑都被封装在 `optimizer` 对象中。

我们通过注册需要训练的模型参数并传入学习率超参数来初始化优化器：

```python
optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
```

PyTorch 中还提供了许多不同的优化器，如 ADAM 和 RMSProp，它们能更好地适用于不同类型的模型和数据。

### 完整实现

```python
def train_loop(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    # Set the model to training mode - important for batch normalization and dropout layers
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        # Compute prediction and loss
        pred = model(X)
        loss = loss_fn(pred, y)

        # Backpropagation
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        if batch % 100 == 0:
            loss, current = loss.item(), batch * batch_size + len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

def test_loop(dataloader, model, loss_fn):
    # Set the model to evaluation mode
    model.eval()
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss, correct = 0, 0

    # Evaluating the model with torch.no_grad() ensures that no gradients are computed
    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()

    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")

loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)

epochs = 10
for t in range(epochs):
    print(f"Epoch {t+1}\n-------------------------------")
    train_loop(train_dataloader, model, loss_fn, optimizer)
    test_loop(test_dataloader, model, loss_fn)
print("Done!")
```

**输出结果**（10 轮）：

```
Epoch 1:  Accuracy: 45.9%, Avg loss: 2.150578
Epoch 2:  Accuracy: 52.3%, Avg loss: 1.874600
Epoch 3:  Accuracy: 57.8%, Avg loss: 1.517382
Epoch 4:  Accuracy: 62.9%, Avg loss: 1.263355
Epoch 5:  Accuracy: 64.9%, Avg loss: 1.100687
Epoch 6:  Accuracy: 65.9%, Avg loss: 0.992516
Epoch 7:  Accuracy: 67.3%, Avg loss: 0.917575
Epoch 8:  Accuracy: 68.5%, Avg loss: 0.863106
Epoch 9:  Accuracy: 69.8%, Avg loss: 0.821541
Epoch 10: Accuracy: 71.1%, Avg loss: 0.788337
```

**读这两个数**：

- **loss 在稳降**（2.15 → 0.79）：模型在学
- **准确率在稳升**（45.9% → 71.1%）：模型确实变强了

**训练 loss 降但测试准确率不涨甚至降 = 过拟合**，该停了、加正则化或加数据增强了。

---

## 完整代码（可直接运行）

```python
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import v2

device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
print(f"Using {device} device")

training_data = datasets.FashionMNIST(
    root="data", train=True, download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
)
test_data = datasets.FashionMNIST(
    root="data", train=False, download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
)

train_dataloader = DataLoader(training_data, batch_size=64, shuffle=True)
test_dataloader = DataLoader(test_data, batch_size=64, shuffle=False)

class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28*28, 512), nn.ReLU(),
            nn.Linear(512, 512),       nn.ReLU(),
            nn.Linear(512, 10),
        )
    def forward(self, x):
        return self.linear_relu_stack(self.flatten(x))

model = NeuralNetwork().to(device)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)

def train_loop(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        X, y = X.to(device), y.to(device)          # 数据也要搬到 device
        pred = model(X)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        if batch % 100 == 0:
            loss, current = loss.item(), (batch + 1) * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

def test_loop(dataloader, model, loss_fn):
    model.eval()
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")

epochs = 5
for t in range(epochs):
    print(f"Epoch {t+1}\n-------------------------------")
    train_loop(train_dataloader, model, loss_fn, optimizer)
    test_loop(test_dataloader, model, loss_fn)
print("Done!")
```

> **注意那两行 `X, y = X.to(device), y.to(device)`** —— 这是新手最常见的报错来源：`model` 在 GPU 上但数据在 CPU，就会报 `Expected all tensors to be on the same device`。

---

## 动手练习

**练习 1** — 把 `learning_rate` 从 `1e-3` 改成 `1.0`，跑 2 轮，描述现象。再改成 `1e-6`，再跑 2 轮。

<details>
<summary>答案</summary>

- `lr=1.0`：loss 大概率剧烈震荡甚至变成 `nan`。梯度一步就把参数推到很远的地方，来回跳，收敛不了。
- `lr=1e-6`：loss 几乎不动（从 2.3 只降到 2.29 左右）。学习太慢，5 轮等于没训练。

**这就是「学习率是最重要的超参数」的直观含义。**
</details>

**练习 2** — 故意删掉 `optimizer.zero_grad()`，跑 2 轮，会发生什么？

<details>
<summary>答案</summary>

loss 会剧烈震荡甚至 `nan`。因为每个 batch 的梯度都被累加到同一个 `.grad` 上，越积越大，更新幅度越来越大，最后参数被推到极端值。

这是 PyTorch 新手最高频的 bug，和第 5 章的「梯度累加」是同一个知识点。
</details>

**练习 3** — 把 `epochs` 改成 30（测试集也这么改），观察准确率曲线。你发现了什么？

<details>
<summary>答案</summary>

前 20 轮左右准确率稳步上升到 ~72%，之后开始**停滞甚至下降**，而训练 loss 还在继续降。

这就是**过拟合**：模型开始记住训练集的具体样本，而不是学general规律。用同一批训练数据评估等于作弊，所以必须用没见过的测试集来监控。
</details>

**练习 4** — 把学习率调度器加进去，看效果：

```python
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=2, gamma=0.5)
# 在 train_loop 之后加：
for epoch in range(epochs):
    train_loop(...)
    scheduler.step()
```

<details>
<summary>答案</summary>

每 2 轮学习率减半。准确率通常比固定学习率更高、收敛更平稳——因为前期大步走，后期小步精修。这叫**学习率衰减**，几乎所有正式训练都会用。
</details>

**练习 5** — `pred.argmax(1) == y` 在做什么？

<details>
<summary>答案</summary>

`pred` 是 `[64, 10]`，`argmax(1)` 沿第 1 维取最大值的位置，得到每个样本的预测类别 `[64]`。然后和真实标签 `[64]` 逐元素比较，得到布尔张量。`.type(torch.float).sum()` 把 True 记为 1 求和，得到「猜对的个数」。
</details>

**练习 6**（挑战）— 试试把 `nn.CrossEntropyLoss()` 换成 `nn.MSELoss()`，为什么不行？

<details>
<summary>答案</summary>

因为 CrossEntropyLoss 内部做了 softmax + 对数，是专门为「logits + 整数标签」设计的。MSELoss 是给回归用的，它假设输入和目标形状相同。

logits 有 10 列，标签只有 1 列，形状不匹配会直接报错；即使手动改成 one-hot，MSELoss 在分类上的收敛效果也远不如 CrossEntropyLoss。
</details>

---

**下一步** → [第 7 章：保存与加载模型](/guides/pytorch/part2-tutorial/07-save-load)
