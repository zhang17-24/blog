---
title: 完整流程
description: 从图片到预测串一遍，含卷积输出尺寸公式和维度约定（NCHW）。
---

# 11. 完整流程：一张图看懂

![形状流程](/figs/tensor-ops/14-pipeline.png)

把上面的知识串起来，一个完整的图像分类流程：

```python
import torch
from torch import nn

torch.manual_seed(0)                 # 固定随机种子，让输出可复现
x = torch.randn(1, 3, 224, 224)      # ① 图片（加了 batch 维）
print("① 输入:     ", tuple(x.shape))

conv = nn.Conv2d(3, 64, kernel_size=3, stride=2, padding=1)
pool = nn.MaxPool2d(2)
x = pool(torch.relu(conv(x)))
print("② 卷积池化: ", tuple(x.shape))

x = x.flatten(1)                      # ③ 拉平（保留 batch 维）
print("③ 拉平:     ", tuple(x.shape))

fc = nn.Linear(x.shape[1], 10)
x = fc(x)
print("④ 全连接:   ", tuple(x.shape))

print("⑤ 预测:     ", x.argmax(1).tolist())
```

**实测输出**：

```
① 输入:      (1, 3, 224, 224)
② 卷积池化:  (1, 64, 56, 56)
③ 拉平:      (1, 200704)
④ 全连接:    (1, 10)
⑤ 预测:      [9]
```

**空间维度是怎么变的**：

$$\text{Conv2d}(k=3, s=2, p=1): \quad H_{out} = \left\lfloor\frac{H_{in} + 2p - k}{s}\right\rfloor + 1 = \frac{224 + 2 - 3}{2} + 1 = 112$$

$$\text{MaxPool2d}(2): \quad H_{out} = \frac{112}{2} = 56$$

所以 `200704 = 64 × 56 × 56`。

**⑤ 的预测值 `[9]` 是随机初始化的结果，没有意义**——它只是说明「形状对了，能跑通」。真实预测需要训练过的权重。

## 维度约定（必背）

| 数据类型 | 形状 | 含义 |
|---|---|---|
| 图像 | `(N, C, H, W)` | 批大小、通道、高、宽 |
| 序列 | `(N, L, D)` | 批大小、序列长度、特征维 |
| 分类标签 | `(N,)` | 批大小（整数） |

**注意 NCHW vs NHWC**：PyTorch 用 **NCHW**（通道在前），TensorFlow/Keras 用 **NHWC**。从别的框架转模型时，这是最常见的踩坑点。

**`nn.Linear` 只吃最后一维**：它把 `(..., D_in)` 变成 `(..., D_out)`，前面的维度（包括 batch）原样保留。

```python
lin = nn.Linear(10, 3)
print(lin(torch.randn(8, 10)).shape))       # (8, 3)
print(lin(torch.randn(8, 5, 10)).shape))    # (8, 5, 3)  ← 前面维度不动
```

---
