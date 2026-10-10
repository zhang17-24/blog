---
title: 快速入门
description: 把前 7 章压缩成一个完整可跑的训练脚本，15 分钟拿到能用的流程。
---

> 官方原文：https://docs.pytorch.ac.cn/tutorials/beginner/basics/quickstart_tutorial.html
>
> **如果你赶时间，只看这一章就够了。** 前面 7 章的内容全压缩在这里，一个脚本跑完整个流程。

---

## 导读：这是你最终要写的东西

前 7 章把这个脚本拆成了 7 段讲。现在把它拼回去——**这 60 行代码就是完整的 PyTorch 训练流程**：

```
① 准备数据      Dataset + DataLoader + transform
② 搭模型        nn.Module
③ 前向+算损失    pred = model(X); loss = loss_fn(pred, y)
④ 反向传播      loss.backward()
⑤ 更新参数      optimizer.step(); optimizer.zero_grad()
⑥ 循环          for epoch in range(epochs)
⑦ 保存          torch.save(model.state_dict(), ...)
```

---

## 官方原文

### 处理数据

PyTorch 提供了两个处理数据的基本原语：`torch.utils.data.DataLoader` 和 `torch.utils.data.Dataset`。`Dataset` 存储样本及其对应的标签，而 `DataLoader` 则围绕 `Dataset` 包装了一个可迭代对象。

```python
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import v2

training_data = datasets.FashionMNIST(
    root="data",
    train=True,
    download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]),
)
test_data = datasets.FashionMNIST(
    root="data",
    train=False,
    download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]),
)

batch_size = 64
train_dataloader = DataLoader(training_data, batch_size=batch_size)
test_dataloader = DataLoader(test_data, batch_size=batch_size)

for X, y in test_dataloader:
    print(f"Shape of X [N, C, H, W]: {X.shape}")
    print(f"Shape of y: {y.shape} {y.dtype}")
    break
```

```
Shape of X [N, C, H, W]: torch.Size([64, 1, 28, 28])
Shape of y: torch.Size([64]) torch.int64
```

### 构建模型

为了在 PyTorch 中定义神经网络，我们创建一个继承自 `nn.Module` 的类。我们在 `__init__` 函数中定义网络层，并在 `forward` 函数中指定数据如何通过网络。

```python
device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
print(f"Using {device} device")

class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28*28, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 10)
        )

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits

model = NeuralNetwork().to(device)
print(model)
```

### 优化模型参数

```python
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)

def train(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        X, y = X.to(device), y.to(device)

        # Compute prediction error
        pred = model(X)
        loss = loss_fn(pred, y)

        # Backpropagation
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        if batch % 100 == 0:
            loss, current = loss.item(), (batch + 1) * len(X)
            print(f"loss: {loss:>7f} [{current:>5d}/{size:>5d}]")

def test(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    model.eval()
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
    train(train_dataloader, model, loss_fn, optimizer)
    test(test_dataloader, model, loss_fn)
print("Done!")
```

### 保存与加载

保存模型的一种常见方法是序列化其内部状态字典（包含模型参数）。

```python
torch.save(model.state_dict(), "model.pth")
print("Saved PyTorch Model State to model.pth")
```

加载模型的步骤包括重新创建模型结构，并将状态字典加载到其中。

```python
model = NeuralNetwork().to(device)
model.load_state_dict(torch.load("model.pth", weights_only=True))
```

现在，该模型可用于进行预测：

```python
classes = [
    "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
    "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot",
]

model.eval()
x, y = test_data[0][0], test_data[0][1]
with torch.no_grad():
    x = x.to(device)
    pred = model(x)
    predicted, actual = classes[pred[0].argmax(0)], classes[y]
    print(f'Predicted: "{predicted}", Actual: "{actual}"')
```

```
Predicted: "Ankle boot", Actual: "Ankle boot"
```

---

## 完整可运行版本

把上面所有片段拼起来，中间不要漏。完整文件在 [fashion_mnist.py](/downloads/pytorch-fashion-mnist.py)：

```python
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import v2

device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
print(f"Using {device} device")

# ① 数据
training_data = datasets.FashionMNIST(
    root="data", train=True, download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]))
test_data = datasets.FashionMNIST(
    root="data", train=False, download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]))
train_dataloader = DataLoader(training_data, batch_size=64, shuffle=True)
test_dataloader = DataLoader(test_data, batch_size=64)

# ② 模型
class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28*28, 512), nn.ReLU(),
            nn.Linear(512, 512), nn.ReLU(),
            nn.Linear(512, 10))
    def forward(self, x):
        return self.linear_relu_stack(self.flatten(x))

model = NeuralNetwork().to(device)

# ③⑤ 损失 + 优化器
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)

# ⑥ 训练循环
def train(dataloader, model, loss_fn, optimizer):
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        X, y = X.to(device), y.to(device)
        pred = model(X)
        loss = loss_fn(pred, y)
        loss.backward()        # ④ 反向
        optimizer.step()       # ⑤ 更新
        optimizer.zero_grad()
        if batch % 100 == 0:
            print(f"loss: {loss.item():>7f}  [{(batch+1)*len(X):>5d}/{len(dataloader.dataset)}]")

def test(dataloader, model, loss_fn):
    model.eval()
    size = len(dataloader.dataset)
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    print(f"Test Error: \n Accuracy: {100*correct/size:>0.1f}%, "
          f"Avg loss: {test_loss/len(dataloader):>8f} \n")

for t in range(5):
    print(f"Epoch {t+1}\n" + "-"*31)
    train(train_dataloader, model, loss_fn, optimizer)
    test(test_dataloader, model, loss_fn)

# ⑦ 保存
torch.save(model.state_dict(), "model.pth")
print("Done! Saved to model.pth")
```

**运行**：

```bash
cd 代码 && python fashion_mnist.py
```

---

## 把这一章的流程刻进脑子里

以后写任何 PyTorch 项目，脑子里都是这 7 步：

```python
# ① 数据
ds    = Dataset(...)                        # 数据怎么读
dl    = DataLoader(ds, batch_size=64)      # 怎么成批

# ② 模型
class Net(nn.Module):
    def __init__(self): ...                 # 有哪些层
    def forward(self, x): ...               # 怎么流

# ③ 损失 + 优化器
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=...)

# ④⑤⑥ 训练
for epoch in range(EPOCHS):
    for X, y in dl:
        pred = model(X)                # 前向
        loss = loss_fn(pred, y)        # 算损失
        loss.backward()                # 反向传播
        optimizer.step()               # 更新参数
        optimizer.zero_grad()          # 清零梯度

# ⑦ 保存
torch.save(model.state_dict(), "model.pth")
```

**换个数据集、换个任务（文本/音频/推荐），骨架完全不变**，只是 ① 和 ③ 会变。

---

**你已经走完官方 8 章了。** 接下来建议：

- 做[练习清单](/guides/pytorch/part3-practice/01-exercises) 里的题巩固
- 换个数据集练手（比如用 Kaggle 上的真实图片做分类）
- 想深入，改 [exercises.py](/downloads/pytorch-exercises.py) 里的进阶题

**延伸阅读**：
- [PyTorch 官方教程](https://docs.pytorch.ac.cn/tutorials/beginner/basics/intro.html)
- [torch.nn API](https://docs.pytorch.ac.cn/docs/stable/nn.html)
- [torch.optim API](https://docs.pytorch.ac.cn/docs/stable/optim.html)
