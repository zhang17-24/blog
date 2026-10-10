---
title: 数据集与加载器
description: 把图片喂进模型：Dataset 与 DataLoader 的分工、什么是 batch、为什么必须 shuffle。
---

> 官方原文：<https://docs.pytorch.ac.cn/tutorials/beginner/basics/data_tutorial.html>

---

## 导读：为什么需要这两个类

写深度学习代码，80% 的时间在处理数据，不是在写模型。PyTorch 提供两个类，把这件事变得干净：

| 类            | 职责                      | 类比             |
| ------------ | ----------------------- | -------------- |
| `Dataset`    | **一次给你一个样本**（图 + 标签）    | 图书馆的一本书        |
| `DataLoader` | **批量给你样本**，自动打乱、自动多进程读取 | 图书馆的服务台，一次给你一批 |

**为什么必须用 DataLoader，不能自己 for 循环取？** 三个原因：

1. **要成批送**。神经网络一次吃一批（比如 64 张），不是一张一张。
2. **必须打乱**。每次都按固定顺序喂数据，模型会记住顺序（过拟合）。**训练集必须 `shuffle=True`；测试集绝对不要**（要固定的、可复现的评估）。
3. **要快**。`num_workers` 让多个进程并行读数据，喂 GPU 的时候不卡住。

---

## 官方原文

### 加载数据集

Fashion-MNIST 是一个 Zalando 商品图像的数据集，由 60,000 个训练样本和 10,000 个测试样本组成。每个样本包含一个 28×28 的灰度图像以及一个来自 10 个类别之一的关联标签。

我们使用以下参数加载 FashionMNIST 数据集：

- `root` — 存储训练/测试数据的路径
- `train` — 指定是训练还是测试数据集
- `download=True` — 如果 `root` 处没有数据，则从互联网下载
- `transform` 和 `target_transform` — 指定特征和标签转换

```python
import torch
from torch.utils.data import Dataset
from torchvision import datasets
from torchvision.transforms import v2
import matplotlib.pyplot as plt

training_data = datasets.FashionMNIST(
    root="data",
    train=True,
    download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
)

test_data = datasets.FashionMNIST(
    root="data",
    train=False,
    download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
)
```

### 迭代和可视化数据集

我们可以像列表一样手动索引 `Dataset`：`training_data[index]`。我们使用 `matplotlib` 来可视化训练数据中的一些样本。

```python
labels_map = {
    0: "T-Shirt", 1: "Trouser",   2: "Pullover",  3: "Dress",   4: "Coat",
    5: "Sandal",  6: "Shirt",     7: "Sneaker",   8: "Bag",     9: "Ankle Boot",
}

figure = plt.figure(figsize=(8, 8))
cols, rows = 3, 3
for i in range(1, cols * rows + 1):
    sample_idx = torch.randint(len(training_data), size=(1,)).item()
    img, label = training_data[sample_idx]
    figure.add_subplot(rows, cols, i)
    plt.title(labels_map[label])
    plt.axis("off")
    plt.imshow(img.squeeze(), cmap="gray")
plt.show()
```

### 为您的文件创建自定义数据集

自定义 `Dataset` 类必须实现三个函数：`__init__`、`__len__` 和 `__getitem__`。

在这个实现中，FashionMNIST 图像存储在一个目录 `img_dir` 中，它们的标签单独存储在一个 CSV 文件 `annotations_file` 中。

```python
import os
import pandas as pd
from torchvision.io import decode_image

class CustomImageDataset(Dataset):
    def __init__(self, annotations_file, img_dir, transform=None, target_transform=None):
        self.img_labels = pd.read_csv(annotations_file)
        self.img_dir = img_dir
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.img_labels)

    def __getitem__(self, idx):
        img_path = os.path.join(self.img_dir, self.img_labels.iloc[idx, 0])
        image = decode_image(img_path)
        label = self.img_labels.iloc[idx, 1]
        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            label = self.target_transform(label)
        return image, label
```

#### `__init__`

在实例化 Dataset 对象时，`__init__` 函数会运行**一次**。我们在这里初始化包含图像的目录、注释文件以及两个转换。

`labels.csv` 文件看起来像这样：

```
tshirt1.jpg, 0
tshirt2.jpg, 0
......
ankleboot999.jpg, 9
```

```python
def __init__(self, annotations_file, img_dir, transform=None, target_transform=None):
    self.img_labels = pd.read_csv(annotations_file)
    self.img_dir = img_dir
    self.transform = transform
    self.target_transform = target_transform
```

**注意**：这里不要读图，只读「清单」。6万 张图全读进内存会很慢——**这是 `Dataset` 的设计原则：懒加载**。

#### `__len__`

`__len__` 函数返回我们数据集中的样本数量。

```python
def __len__(self):
    return len(self.img_labels)
```

#### `__getitem__`

`__getitem__` 函数在给定的索引 `idx` 处加载并返回数据集中的一个样本。它根据索引识别图像在磁盘上的位置，使用 `decode_image` 将其转换为张量，从 CSV 中检索相应的标签，对它们调用转换函数，并返回包含张量图像和相应标签的元组。

```python
def __getitem__(self, idx):
    img_path = os.path.join(self.img_dir, self.img_labels.iloc[idx, 0])
    image = decode_image(img_path)
    label = self.img_labels.iloc[idx, 1]
    if self.transform:
        image = self.transform(image)
    if self.target_transform:
        label = self.target_transform(label)
    return image, label
```

> **性能提示**：`DataLoader` 内部依赖 `__getitem__` 的时候如果发现磁盘 IO 是瓶颈，会自动用 `multiprocessing` 并行。多 worker 时，每个 worker 会复制一份 `self.img_labels`（内存占用×N），数据量大的时候要注意。

### 使用 DataLoader 准备训练数据

`Dataset` 一次检索一个样本的数据集特征和标签。在训练模型时，我们通常希望：

- 以「小批量（minibatches）」的形式传递样本
- 在每个时期（epoch）重新打乱数据以减少模型过拟合
- 使用 Python 的 `multiprocessing` 来加速数据检索

`DataLoader` 是一个可迭代对象，它通过一个简单的 API 帮我们抽象了这种复杂性。

```python
from torch.utils.data import DataLoader

train_dataloader = DataLoader(training_data, batch_size=64, shuffle=True)
test_dataloader = DataLoader(test_data, batch_size=64, shuffle=True)
```

> ⚠️ **注意**：测试集也写了 `shuffle=True`，这是官方教程为了简化写的，**实际项目里测试集应该去掉**。测试集必须固定顺序，否则每次评估的准确率没法直接比较。

### 遍历 DataLoader

每次迭代都会返回一批 `train_features` 和 `train_labels`。因为指定了 `shuffle=True`，遍历完所有批次后数据会被打乱。

```python
# Display image and label.
train_features, train_labels = next(iter(train_dataloader))
print(f"Feature batch shape: {train_features.size()}")
print(f"Labels batch shape: {train_labels.size()}")
img = train_features[0].squeeze()
label = train_labels[0]
plt.imshow(img, cmap="gray")
plt.show()
print(f"Label: {label}")
```

```
Feature batch shape: torch.Size([64, 1, 28, 28])
Labels batch shape: torch.Size([64])
Label: 0
```

**看懂这个 shape**：`[64, 1, 28, 28]` = `[批大小, 通道数, 高, 宽]`，这是图像数据的标准格式（NCHW）。`[64]` 是 64 个标签。

---

## 必须掌握的参数清单

```python
DataLoader(dataset,
           batch_size=64,      # 每批多少样本
           shuffle=True,       # 是否打乱（训练集True，测试集 False）
           num_workers=0,      # 几个子进程读数据。0=主进程，4 通常更快
           pin_memory=False,   # 用GPU 时设 True，加速数据搬运
           drop_last=False)    # True = 丢掉最后不满一批的
```

| 场景                 | 推荐配置                             |
| ------------------ | -------------------------------- |
| Windows / macOS 调试 | `num_workers=0`（设为4 时常出多进程启动错误）  |
| Linux 训练           | `num_workers=4`                  |
| 用GPU 训练            | `num_workers=4, pin_memory=True` |

---

## 动手练习

**练习 1** — 60000 张图，`batch_size=64`，一个 epoch 有多少个批次？

<details>

<summary>答案</summary>

`60000 // 64 = 937`，加上最后不完整的一批（默认 `drop_last=False`，会保留），一共 **938** 个 batch。用 `len(train_dataloader)` 直接就能拿到这个数。

用 `len(train_dataloader)` 就能拿到这个数。

</details>

**练习 2** — 下面这两句有什么区别？

```python
train_features, train_labels = next(iter(train_dataloader))
# vs
train_features, train_labels = train_dataloader
```

<details>

<summary>答案</summary>

第一句：`iter()` 创建一个迭代器，`next()` 只取**第一批**（64 个样本）。

第二句：直接把 DataLoader 对象赋值给变量，**不会**执行任何数据读取，因为它本身不是一个批次。

</details>

**练习 3** — 为什么测试集不该`shuffle=True`？

<details>

<summary>答案</summary>

因为要保证每次评估看到的数据顺序一致，这样准确率的变化才能归因于模型变化，而不是数据顺序变化。而且测试时你想看固定的样本，不要随机跳。

同时 `shuffle=True` 会让每个 batch 的标签分布变化，也会让调试更难。

</details>

**练习 4** — 写一个 `Dataset`，读取一个文件夹里的所有 txt 文件作为样本，文件名去掉扩展名当标签。

<details>

<summary>答案</summary>

```python
import os
from pathlib import Path
from torch.utils.data import Dataset

class TxtDataset(Dataset):
    def __init__(self, root):
        self.root = Path(root)
        self.files = sorted(self.root.glob("*.txt"))

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        p = self.files[idx]
        return p.read_text(), p.stem      # (内容, 标签)
```

注意 `__init__` 里只列文件清单、不读内容——保持懒加载。

</details>

**练习 5** — 你的 DataLoader 很慢，怎么优化？

<details>

<summary>答案</summary>

1. `num_workers=4`（Windows/macOS 先试 2，太多会启动失败）
2. 用 GPU 时加 `pin_memory=True`
3. 检查是不是在 `__getitem__` 里做了重量级操作（比如每张图都做一次磁盘 IO 以外的重活）
4. 如果内存装得下，`transform` 可以在 `__init__` 之后批量预处理；但要权衡内存

</details>

---

**下一步** → [第 3 章：数据变换](/guides/pytorch/part2-tutorial/03-transforms)

官方延伸阅读：[torch.utils.data API](https://docs.pytorch.ac.cn/docs/stable/data.html)
