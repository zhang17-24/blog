---
title: 速查表
description: 常用 API 一页速查：张量创建、形状操作、模型、损失、优化器、训练循环。
---

一页看完常用 API。适合已经读过正文、只是忘了语法的时候回来查。

---

## 张量

```python
import torch

# 创建
torch.tensor([[1, 2], [3, 4]])        # 从数据（会拷贝）
torch.from_numpy(np_array)             # 从 NumPy（共享内存）
torch.zeros(2, 3); torch.ones(2, 3)   # 全0 / 全1
torch.rand(3, 3)                       # [0,1) 均匀分布
torch.randn(3, 3)                      # 标准正态分布 ←初始化权重用这个
torch.empty(2, 3)                      # 未初始化（内存里的垃圾值）
torch.eye(4)                           # 单位矩阵
torch.arange(0, 10, 2)                 # 等差数列
torch.ones_like(x); torch.randn_like(x)  # 同形状同类型
torch.zeros_like(x, dtype=torch.float)   # 覆盖 dtype

# 属性
x.shape      # torch.Size([2, 3])   ★ 排查错误第一步
x.dtype      # torch.float32 / int64
x.device     # cpu / cuda:0
x.ndim       # 维度数
x.numel()    # 元素总数
x.requires_grad  # 是否追踪梯度

# 索引切片
x[0]x[:, 0]       x[1, 2]       # 行列 / 标量
x[:2]     x[1:]     x[:, 1:]     x[1, 1:]

# 变换
x.reshape(2, 6);  x.view(2, 6)   # 改形状
x.T;  x.transpose(0, 1)      # 转置
x.permute(2, 0, 1)            # 换维度顺序
x.flatten(start_dim=1)         # 展平，保留批次维
x.squeeze();  x.unsqueeze(0)    # 去掉/增加 size=1 的维度
x.clamp(0, 1);  x.clamp_min(0)             # 裁剪数值

# 数学
x.sum();  x.sum(dim=1);  x.mean();  x.max()
torch.matmul(a, b);  a @ b         # 矩阵乘
a * b                             # 逐元素乘
x.item()                          # ★ 单元素张量→Python 数
x.numpy();  t.cpu().numpy()       # → NumPy（GPU 要先 .cpu()）
```

---

## nn.Module

```python
from torch import nn

# 层
nn.Linear(in_features, out_features)   # y = Wx + b
nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1)
nn.ReLU();  nn.Sigmoid();  nn.Tanh();  nn.GELU()
nn.Dropout(p=0.5)
nn.BatchNorm1d(n);  nn.LayerNorm(n)
nn.Flatten(start_dim=1)
nn.Softmax(dim=1);  nn.LogSoftmax(dim=1)

# 容器
nn.Sequential(nn.Linear(10, 20), nn.ReLU(), nn.Linear(20, 2))

# 模型骨架 —— 两条铁律
class Net(nn.Module):
    def __init__(self):
        super().__init__()               # ① 必须
        self.fc1 = nn.Linear(784, 512)   # ① 层定义在这里

    def forward(self, x):                # ② 数据流在这里
        return self.fc1(x)

# 用法
model = Net()
model(x)                # ✅ 调 forward
model.forward(x)        # ❌ 不要
model.to(device)        # 搬到 GPU
model.parameters()      # 迭代所有参数
model.named_parameters() # 带名字
model.state_dict()      # 参数字典
model.train(); model.eval()
```

---

## Dataset / DataLoader

```python
from torch.utils.data import Dataset, DataLoader

class MyDataset(Dataset):
    def __init__(self, root, transform=None):     # 只初始化，不读数据
        self.root = root
        self.transform = transform

    def __len__(self):
        return self.n

    def __getitem__(self, idx):# 按需读一个样本
        img, label = load(idx)
        if self.transform:
            img = self.transform(img)
        return img, label

dl = DataLoader(ds,
                batch_size=64,
                shuffle=True,      # 训练 True / 测试 False
                num_workers=0,     # Linux 4，Windows/macOS 先 0 或 2
                pin_memory=False,  # GPU 训练设 True
                drop_last=False)

for X, y in dl:      # X: [batch, C, H, W]
    ...              # y: [batch]
```

---

## 优化

```python
# 优化器
torch.optim.SGD(params, lr=1e-3, momentum=0.9)
torch.optim.Adam(params, lr=1e-3)
torch.optim.AdamW(params, lr=1e-3, weight_decay=1e-4)

# 学习率调度
torch.optim.lr_scheduler.StepLR(opt, step_size=2, gamma=0.5)
torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=10)

# 损失
nn.CrossEntropyLoss()          # 多分类（传整数标签 + logits）
nn.BCEWithLogitsLoss()         # 二分类
nn.MSELoss()                   # 回归
nn.NLLLoss()                   # 配合 LogSoftmax
nn.KLDivLoss()                 # 蒸馏常用

# 训练三步（顺序不能乱）
optimizer.zero_grad()   # 1. 清零
loss.backward()        # 2. 反传
optimizer.step()       # 3. 更新
```

---

## 自动微分

```python
x = torch.randn(3, requires_grad=True)      # 创建时标记
x.requires_grad_(True)                      # 或事后标记

y = (x ** 2).sum()
y.backward()              # 从标量根节点反传
x.grad                    # ★ 梯度，和 x 同形状

with torch.no_grad():     # 关闭追踪（推理）
    y = model(x)

z = y.detach()            # 切断单个张量的计算图

y.backward(retain_graph=True)   # 同一图多次反传

p.requires_grad_(False)        # 冻结参数
```

---

## 保存 / 加载

```python
# 推荐：只存参数
torch.save(model.state_dict(), "model.pth")
model = Net()
model.load_state_dict(torch.load("model.pth", weights_only=True))
model.eval()

# 完整 checkpoint（可恢复训练）
torch.save({
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "epoch": epoch,
    "best_acc": best_acc,
}, "ckpt.pth")

ckpt = torch.load("ckpt.pth", weights_only=False)
model.load_state_dict(ckpt["model_state_dict"])
optimizer.load_state_dict(ckpt["optimizer_state_dict"])   # ★ 别忘

# ❌ 不推荐：加载不可信来源的文件
torch.save(model, "whole.pth")                # pickle
torch.load("whole.pth", weights_only=False)   # 等于执行陌生代码
```

---

## torchvision transforms

```python
from torchvision.transforms import v2

# 格式转换
v2.ToImage() # PIL/ndarray → Image 张量
v2.ToDtype(torch.float32, scale=True)          # → float32, [0,1]
v2.Normalize(mean=[0.5], std=[0.5])             # → 标准化
v2.ToPILImage()

# 数据增强（★只用在训练集）
v2.RandomHorizontalFlip(p=0.5)
v2.RandomRotation(degrees=15)
v2.RandomResizedCrop(size=(224,224), scale=(0.8,1.0))
v2.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2)
v2.RandomGrayscale(p=0.1)

# 组合（★ 按列表顺序执行）
train_tf = v2.Compose([v2.RandomHorizontalFlip(), v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
test_tf  = v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
```

---

## 设备

```python
# 自动选
device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"

# 老写法（兼容旧版本）
device = "cuda" if torch.cuda.is_available() else "cpu"
if torch.cuda.is_available():
    device = "cuda:0"                    # 指定第 0 张卡
    torch.cuda.empty_cache()             # 显存不够时清缓存

model = model.to(device)
X, y = X.to(device), y.to(device)        # ★ 数据也要搬，容易漏
```

---

## 调试清单

| 症状 | 先查这个 |
|---|---|
| `Expected all tensors to be on the same device` | `X.to(device)` 漏了 |
| `size mismatch` | `print(x.shape)`，逐层对比 |
| loss 变成 `nan` | 学习率太大 |
| loss 不降 | 学习率太小 / 数据没归一化 / 忘了 `zero_grad()` |
| 准确率一直 10% | 模型输出层维度不对 / 标签传错 / 忘了 ReLU |
| 测试准确率随机波动 | 忘了 `model.eval()` |
| 显存不够 | 减小 batch_size / 测试时加 `no_grad()` |
| 训练极慢 | `num_workers=4`、`pin_memory=True` |
| `NameError` | Notebook 没重跑前面的定义 |

---

## 完整训练模板（背下来）

```python
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import v2

device = "cuda" if torch.cuda.is_available() else "cpu"

train_ds = datasets.FashionMNIST("data", train=True, download=True,
    transform=v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]))
train_dl = DataLoader(train_ds, batch_size=64, shuffle=True)

model = nn.Sequential(
    nn.Flatten(), nn.Linear(784, 512), nn.ReLU(),
    nn.Linear(512, 512), nn.ReLU(), nn.Linear(512, 10)).to(device)

loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)

for epoch in range(5):
    model.train()
    for X, y in train_dl:
        X, y = X.to(device), y.to(device)
        pred = model(X)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
    print(f"Epoch {epoch+1} done")

torch.save(model.state_dict(), "model.pth")
```
