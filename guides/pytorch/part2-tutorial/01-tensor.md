---
title: 张量
description: PyTorch 的基本积木。张量 vs NumPy 数组、设备与 dtype、广播规则的常见坑。
---

> 官方原文：https://docs.pytorch.ac.cn/tutorials/beginner/basics/tensorqs_tutorial.html

---

## 导读：你为什么必须先懂张量

深度学习处理的一切——图片、文字、声音、模型的权重、梯度——在 PyTorch 里**全部是张量**。不会张量，后面每一章都读不懂。

### 张量 vs NumPy 数组

长得几乎一样，区别就三条，但每条都很重要：

| | NumPy `ndarray` | PyTorch `Tensor` |
|---|---|---|
| 跑在 GPU 上 | 不能（需额外库） | **能**，一行代码 |
| 自动求导 | 不能 | **能**（第5章） |
| 挂到计算图上 | 不管 | 能（第 5 章） |

所以 PyTorch 的思路是：造一个**长得像 NumPy 数组、但是能上 GPU、能自动求导**的东西。如果你熟悉 NumPy，这一章会非常快。

### 先记住这几个操作

```python
x = torch.tensor([[1, 2], [3, 4]])

x.shape        # torch.Size([2, 2])   形状
x.dtype # torch.int64           数据类型
x.device # 所在设备（cpu/cuda）
x.ndim         # 维度数= 2
x.numel()      # 元素总数 = 4
```

**初学者最常卡住的就是 shape。** 养成习惯：每次拿到数据先 `print(x.shape)`。

---

## 官方原文

### 初始化张量

张量可以通过多种方式进行初始化。

**直接从数据创建** — 数据类型会自动推断。

```python
import torch
import numpy as np

data = [[1, 2], [3, 4]]
x_data = torch.tensor(data)
```

**从 NumPy 数组创建**

```python
np_array = np.array(data)
x_np = torch.from_numpy(np_array)
```

**从另一个张量创建** — 除非显式覆盖，否则新张量会保留原张量的形状和数据类型。

```python
x_ones = torch.ones_like(x_data)                                # 保留属性
print(f"Ones Tensor: \n {x_ones} \n")

x_rand = torch.rand_like(x_data, dtype=torch.float)            # 覆盖数据类型
print(f"Random Tensor: \n {x_rand} \n")
```

```
Ones Tensor:
tensor([[1, 1],
        [1, 1]])

Random Tensor:
tensor([[0.6235, 0.2075],
        [0.6531, 0.8786]])
```

**随机张量** — `torch.rand` 生成 [0, 1) 的均匀分布，`torch.randn` 生成标准正态分布（均值 0 方差 1）。初始化权重用 `randn`，这是默认做法。

```python
shape = (2, 3, 4)
tensor = torch.rand(shape)
print(tensor)
```

```
tensor([[[0.8469, 0.3096, 0.2834, 0.1213],
         [0.9414, 0.9118, 0.4304, 0.5024],
         [0.3188, 0.9539, 0.0223, 0.3101]],
        [[0.0449, 0.3226, 0.3614, 0.1443],
         [0.4210, 0.9957, 0.4072, 0.0491],
         [0.1962, 0.8001, 0.8214, 0.7560]]])
```

**其他创建方式**

```python
# 全零 / 全一
print(torch.zeros(2, 3))
print(torch.ones(2, 3))

# 形状已知的张量，用 0 填充
shape = (3, 4)
x = torch.empty(shape, dtype=torch.int64)
print(x)

# 创建与参数张量同形状同类型的新张量
x = torch.tensor([[1, 2], [3, 4]], dtype=torch.float32)
y = torch.empty_like(x)
print(y)
```

**恒等矩阵**

```python
print(torch.eye(4))
```

```
tensor([[1., 0., 0., 0.],
        [0., 1., 0., 0.],
        [0., 0., 1., 0.],
        [0., 0., 0., 1.]])
```

**构造张量** — 用 `torch.tensor(data, dtype=...)` 指定数据类型。用 `torch.arange` 生成等差数列。

```python
t = torch.tensor([[1, 2], [3, 4]], dtype=torch.float32)
print(t)

x = torch.arange(0, 10, 2)
print(x)
print(x.dtype)

x = torch.arange(start=0, end=10, step=1, dtype=torch.float32)
print(x.dtype)
```

**索引与切片**

```python
t = torch.tensor([[1, 2], [3, 4]])

print(t[0])      # 第一行
print(t[:, 0])   # 第一列
print(t[1][0])   # 第2行第1列 → 标量
print(t[1, 0])   # 同上

# 切片
t = torch.tensor([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

print(t[:2])     # 前两行
print(t[1:])     # 从第2行到最后
print(t[:, 1:])  # 所有行的第2列起
print(t[1:2, 1:])  # 第2行，第2列起
print(t[::2])    # 每隔一行
print(t[1, 1:])  # 第2行的第2列起
```

**连接张量**

```python
t = torch.tensor([[1, 2], [3, 4]])

torch.cat((t, torch.tensor([[5, 6], [7, 8]])), dim=0)  # 上下拼 → (4,2)
torch.cat((t, torch.tensor([[5, 6], [7, 8]])), dim=1)  # 左右拼 → (2,4)

t = torch.tensor([[1, 2], [3, 4]])

torch.stack((t, t), dim=0)  # 新增一维 → (2,2,2)
torch.stack((t, t), dim=1)  # 新增一维 → (2,2,2)
```

`cat` 和 `stack` 的区别初学者常搞混：**`cat` 要求形状一致，在已有维度上拼接；`stack` 会新增一个维度**。

**矩阵乘法**

```python
a = torch.tensor([[1, 2], [3, 4]])
b = torch.tensor([[1, 1], [1, 1]])

a @ b          # 等价于 torch.matmul(a, b)
torch.mm(a, b)  # 限定二维
```

**乘法 / 除法 — 逐元素**

```python
a = torch.tensor([[1, 2], [3, 4]])
b = torch.tensor([[1, 1], [1, 1]])

a * b          # 逐元素相乘，不是矩阵乘法
```

**单元素张量转 Python 标量**

```python
a = torch.tensor([[1, 2], [3, 4]])
print(a.item())  # 报错
print(a[0][0].item())  # 1
```

`item()` 只能用于**只有一个元素**的张量。PyTorch 官方建议用 `.item()` 而不是直接下标取值——因为直接下标会保留计算图（需要梯度的图），`.item()` 是取出纯数值。

**副本与视图**

```python
a = torch.tensor([[1, 2], [3, 4]])
b = a            # b 和 a 共享同一块内存
b[0][0] = 111    # 改b，a 也变了
print(a)

b = a.clone()    # clone 才是真正的复制
```

**这一条非常关键**：`b = a` 不是复制，是**起别名**。初学者最常见的 bug 就是「我明明复制了一份，怎么改回去了」。

---

## 张量运算：Broadcasting

形状不同的张量能直接运算，靠的是 broadcasting 广播机制——从**最后一维开始**对齐，逐维比较：

- 尺寸相同 → 直接用
- 尺寸为 1 → 拉伸到另一边（这个 1 会被广播）
- 都不匹配 → 报错

```python
a = torch.tensor([[1], [2], [3]])   # (3, 1)
b = torch.tensor([[10], [20], [30]]) # (3, 1)
print(a + b)                        # (3, 1)

a = torch.tensor([[1], [2], [3]])   # (3, 1)
b = torch.tensor([10, 20, 30])      # (3,)  ← 只有一维
print(a + b)                        # (3, 3) 每个元素都加一遍
```

```
tensor([[11, 21, 31],
        [12, 22, 32],
        [13, 23, 33]])
```

**这是新手最容易懵的地方**：`a` 的形状是 (3,1)，`b` 的形状是 (3,)，结果却是 (3,3)。因为 `(3,1)` 被广播成了 `[[10],[20],[30]]`（第一维的 1 拉伸为 3），所以第二维的 3 变成结果维度。

Debug 技巧：出错时先 `print(a.shape, b.shape)`，手动判断能不能广播。

---

## NumPy 与 PyTorch 互转

PyTorch 也支持与 NumPy 互操作，**但有 GPU 张量不支持直接转 NumPy**。

```python
import torch
import numpy as np

# NumPy -> Tensor
a = np.ones(4)
t = torch.from_numpy(a)
print(t)

# Tensor -> NumPy（CPU 张量）
t = torch.ones(4)
n = t.numpy()
print(n)

# GPU -> NumPy
t = torch.ones(4, device='cuda')
print(t.cpu().numpy())  # 必须先 .cpu()
```

---

## 动手练习

**练习 1** — 预测下面的输出：

```python
a = torch.tensor([1, 2, 3])
b = torch.tensor([10, 20, 30])
print(a * b)
print(a + b)
print(a.shape)
```

<details>
<summary>答案</summary>

```
tensor([10, 40, 90])
tensor([11, 22, 33])
torch.Size([3])
```

**关键**：`*` 是**逐元素**乘法，不是矩阵乘法。
</details>

**练习 2** — 下面两行有什么本质区别？

```python
b = a
b = a.clone()
```

<details>
<summary>答案</summary>

`b = a` 只是给同一个内存起了个新名字（视图）。改 `b` 会同时改 `a`。`a.clone()` 才会真正复制一份独立内存。
</details>

**练习 3** — 求下面两个张量相加后的形状：

```python
a = torch.zeros(2, 3, 4)
b = torch.zeros(4)
```

<details>
<summary>答案</summary>

`torch.Size([2, 3, 4])`。

`b` 被广播成 `(1,1,4)` →再拉伸为 `(2,3,4)`，逐维对齐相加。
</details>

**练习 4**（有点挑战）— 打印一个 5×5 的单位矩阵，把主对角线之外全设成 0，用一行代码。

<details>
<summary>答案</summary>

```python
m = torch.eye(5)
mask = torch.arange(5)[:, None] == torch.arange(5)     # True 只在主对角线
print(m * mask.long())                # True/False 要转成 long 才能参与乘法
```

输出：
```
tensor([[1., 0., 0., 0., 0.],
        [0., 1., 0., 0., 0.],
        [0., 0., 1., 0., 0.],
        [0., 0., 0., 1., 0.],
        [0., 0., 0., 0., 1.]])
```
</details>

**练习 5** — 下面代码的最后一行会报错，为什么？

```python
t2 = torch.tensor([[1, 2], [3, 4]])
print(t2.sum(dim=0))
print(t2.sum(dim=0).item())
```

<details>
<summary>答案</summary>

第一行输出 `tensor([4, 6])` —— 有两个元素，所以最后一行 `.item()` 报错。

**规则**：`item()` 只能用于**只有一个元素**的张量。要取出单个值用 `t[0, 0].item()`。
</details>

---

**下一步** → [第 2 章：数据集与数据加载器](/guides/pytorch/part2-tutorial/02-dataset)

官方延伸阅读：
- [torch.Tensor 文档](https://docs.pytorch.ac.cn/docs/stable/tensors.html)
- [与 NumPy 的桥接](https://docs.pytorch.ac.cn/docs/stable/numpy.html)
