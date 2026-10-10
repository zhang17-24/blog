---
title: 数据变换
description: 把图片变成模型能吃的格式：ToTensor、Normalize 为什么这么取值、one-hot 的意义。
---

> 官方原文：https://docs.pytorch.ac.cn/tutorials/beginner/basics/transforms_tutorial.html
>
> ⚠️ **这一章官方原文只有 20 行**，因为它假设你已经知道「为什么要做这些变换」。下面的导读补上这部分。

---

## 导读：两个必须做变换的理由

FashionMNIST 原始数据是 **PIL 图片格式，像素值 0~255 的整数**，标签是**整数 0~9**。但神经网络不接受这种输入。两个问题，两个解法：

### 问题 1：像素值太大 → 必须归一化

**为什么 0~255 不行？**

- 一个像素差 255，经过几十层线性变换，数值会放大到几千几万，容易溢出
- 学习率很难调：大梯度会让训练震荡，小梯度又学不动

**标准做法**：把像素缩放到 **[0, 1]** 区间。

```
原始: 0   128   255      ← PIL 是 uint8 整数
归一化: 0.0  0.5   1.0     ← float32，落在 [0,1]
```

对应代码就是下面这句里的 `scale=True`：

```python
v2.ToDtype(torch.float32, scale=True)
```

它同时做了两件事：转成 `float32` + 除以 255 缩放到 [0,1]。

### 问题 2：分类任务的标签应该是什么格式？

这里有个容易困惑的点。**官方教程在变换里用了 one-hot，但训练时又没真的用上它。**

先看两种做法：

|做法 | 标签格式 |配损失函数 |
|---|---|---|
| **整数标签 + CrossEntropyLoss** | `3` | `nn.CrossEntropyLoss()` |
| one-hot + 别的损失 | `[0,0,0,1,0,0,0,0,0,0]` | `nn.MSELoss()`等 |

PyTorch 的官方建议是**第一种**：直接传整数标签，用 `CrossEntropyLoss`，它内部会帮你做 softmax + 对数，实际效果更好也更稳定。one-hot 是理解上的「教科书写法」，PyTorch 不推荐你真的这么用。

**本章的代码演示了 one-hot 的写法（为了讲清transforms 是什么），但第 6 章实际训练时传的是整数标签 + CrossEntropyLoss。** 这不是矛盾，是 PyTorch 的最佳实践。

###顺带一句：数据增强

本章的 transform 只做了「格式转换」。真实项目里 transform 还常用来做**数据增强**——随机旋转、裁剪、翻转、加噪声，让模型看到同一张图的不同版本，泛化能力更强、不会死记硬背。这是防过拟合的主要手段之一。

---

## 官方原文

### 基本用法

数据并不总是以训练机器学习算法所需的最终处理形式出现。我们使用转换（transforms）来对数据进行一些操作，使其适合训练。

所有 TorchVision 数据集都具有两个参数：用于修改特征的 `transform` 和用于修改标签的 `target_transform`，它们都接受包含转换逻辑的可调用对象。`torchvision.transforms` 模块开箱即用地提供了几种常用的转换。

FashionMNIST 的特征是 PIL 图像格式，而标签是整数。为了进行训练，我们需要将特征转换为归一化的张量，将标签转换为 one-hot 编码的张量。为了进行这些转换，我们使用 `torchvision.transforms.v2` API 以及 `torch.nn.functional.one_hot`。

```python
import torch
import torch.nn.functional as F
from torchvision import datasets
from torchvision.transforms import v2

ds = datasets.FashionMNIST(
    root="data",
    train=True,
    download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]),
    target_transform=v2.Lambda(
        lambda y: F.one_hot(torch.tensor(y), num_classes=10).float()
    ),
)
```

### ToImage() 和 ToDtype()

`torchvision.transforms.v2` API 将传统的 `ToTensor` 转换替换为一个两步管道。

- `v2.ToImage()` 把 PIL 图像或 NumPy `ndarray` 转换为 `torchvision.tv_tensors.Image` 张量
- 带`scale=True` 的 `v2.ToDtype()` 将其转换为 `float32`，并将像素强度值缩放到 `[0., 1.]` 范围内

> **老代码对照**：如果你看到教程或旧项目里写的是 `transforms.ToTensor()`，那就是这两个的合体。新代码建议统一用 v2。

### Lambda 转换

Lambda 转换可以应用任何用户定义的 lambda 函数。这里，我们使用 `torch.nn.functional.one_hot` 将整数标签转换为大小为 10 的 one-hot 编码张量，然后将其转换为 `float` 以匹配预期的数据类型。

```python
target_transform = v2.Lambda(
    lambda y: F.one_hot(torch.tensor(y), num_classes=10).float()
)
```

### 延伸阅读

- [transforms v2 入门](https://docs.pytorch.ac.cn/vision/stable/transforms.html)
- [torchvision.transforms.v2 API](https://docs.pytorch.ac.cn/docs/stable/torchvision/transforms.html)

---

## 常用变换速查

```python
from torchvision.transforms import v2

# 几何变换（数据增强的主力）
v2.RandomHorizontalFlip(p=0.5)              # 随机水平翻转
v2.RandomRotation(degrees=15)               # 随机旋转 ±15 度
v2.RandomResizedCrop(size=(28, 28), scale=(0.8, 1.0))  # 随机裁剪+缩放
v2.ColorJitter(brightness=0.2, contrast=0.2) # 亮度/对比度扰动（彩色图）

# 格式转换
v2.ToImage()                                  # PIL/ndarray → Image张量
v2.ToDtype(torch.float32, scale=True)         # → float32，缩放到 [0,1]
v2.Normalize(mean=[0.485], std=[0.229])        # 标准化到均值0方差1
v2.ToPILImage()                               # 张量 → PIL

# 组合
train_tf = v2.Compose([
    v2.RandomHorizontalFlip(),
    v2.ToImage(),
    v2.ToDtype(torch.float32, scale=True),
])

test_tf = v2.Compose([        # 测试集不做随机增强！
    v2.ToImage(),
    v2.ToDtype(torch.float32, scale=True),
])
```

> ⚠️ **关键习惯：训练集和测试集的 transform 必须分开。** 测试集只能做「格式转换」，绝不能加随机增强——否则你的准确率会随机波动，无法判断模型是变好了还是运气好。

---

## 动手练习

**练习 1** — 为什么 `scale=True` 很重要？写成代码验证一下效果。

<details>
<summary>答案</summary>

```python
from torchvision.transforms import v2
import torch
from PIL import Image

img = Image.new("RGB", (4, 4), color=(200, 100, 50))  # PIL

# 不缩放
a = v2.ToDtype(torch.float32)(v2.ToImage()(img))
print(a.min(), a.max())   # 50.0 200.0

# 缩放到 [0,1]
b = v2.ToDtype(torch.float32, scale=True)(v2.ToImage()(img))
print(b.min(), b.max())   # 0.196 0.784
```

缩放后数值小得多，梯度更稳定。
</details>

**练习 2** — 写出训练集和测试集的 transform：训练集随机翻转，测试集不翻转。

<details>
<summary>答案</summary>

```python
train_tf = v2.Compose([
    v2.RandomHorizontalFlip(p=0.5),
    v2.ToImage(),
    v2.ToDtype(torch.float32, scale=True),
])

test_tf = v2.Compose([
    v2.ToImage(),
    v2.ToDtype(torch.float32, scale=True),
])
```
</details>

**练习 3** — one-hot 编码标签 3（10 个类别）应该是什么形状？

<details>
<summary>答案</summary>

`torch.Size([10])`，内容是 `[0., 0., 0., 1., 0., 0., 0., 0., 0., 0.]`。

注意 `F.one_hot` 返回整数类型，必须 `.float()` 转成浮点才能参与计算。
</details>

**练习 4** — 预测：如果把归一化这一步去掉（像素保持 0~255），训练会怎样？

<details>
<summary>答案</summary>

大概率 loss 剧烈震荡、准确率上不去。因为输入量级大了 255 倍，第一层输出和梯度量级跟着暴涨，学习率 `1e-3` 就太大，必须降到 `1e-5` 量级才行。这就是「为什么要归一化」的本质。
</details>

**练习 5** — `v2.Compose` 里的 transform 是按什么顺序执行的？

<details>
<summary>答案</summary>

**按列表顺序从前往后**。所以必须先 `ToImage()`（变成张量）再 `ToDtype()`（转类型+缩放）。如果顺序反了，`ToDtype` 收到的是 PIL 对象会直接报错。
</details>

---

**下一步** → [第 4 章：构建模型](/guides/pytorch/part2-tutorial/04-build-model)
