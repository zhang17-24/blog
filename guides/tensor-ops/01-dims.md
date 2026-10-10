---
title: 张量与维度
description: 维度数就是 shape 里数字的个数。shape=() 和 shape=(1,) 是两回事。
---

# 1. 张量与维度

**维度数（`ndim`）就是 `shape` 里数字的个数。**

![四种维度](/figs/tensor-ops/01-dims.png)

```python
import torch

s = torch.tensor(7)                          # 标量
v = torch.tensor([3, 1, 4, 1, 5])            # 向量
m = torch.tensor([[1, 2, 3], [4, 5, 6]])     # 矩阵
c = torch.zeros(3, 2, 2)                     # 三维

for name, t in [("标量", s), ("向量", v), ("矩阵", m), ("3维", c)]:
    print(f"{name:4s} shape={str(tuple(t.shape)):12s} ndim={t.ndim}  numel={t.numel()}")
```

**实测输出**：

```
标量   shape=()           ndim=0  numel=1
向量   shape=(5,)         ndim=1  numel=5
矩阵   shape=(2, 3)       ndim=2  numel=6
3维   shape=(3, 2, 2)    ndim=3  numel=12
```

## 三个必记的属性

| 属性 | 含义 | 用途 |
|---|---|---|
| `.shape` | 每一维的长度 | **排查错误第一步** |
| `.ndim` | 维度数 | 判断是几维张量 |
| `.numel()` | 元素总个数 | 检查 reshape 是否可行 |

**关键点**：`shape=()` 和 `shape=(1,)` 是**不同**的。前者是标量（0 维），后者是长度 1 的向量（1 维）。这个问题在[第 5 节 · 广播机制](/guides/tensor-ops/05-broadcasting)会反复出现。

---
