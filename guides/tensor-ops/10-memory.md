---
title: 内存布局
description: stride 是什么，转置为什么不搬数据，view 为什么会对非连续张量报错。
---

# 10. 内存布局：view vs reshape

![内存连续性](/figs/tensor-ops/13-contiguity.png)

**这是很多人没意识到但很关键的一节。**

```python
x = torch.arange(6).reshape(2, 3)
print("x.stride()      =", x.stride())
print("x.T.stride()    =", x.T.stride())
print("x.T.is_contiguous() =", x.T.is_contiguous())
```

```
x.stride()      = (3, 1)
x.T.stride()    = (1, 3)
x.T.is_contiguous() = False
```

## stride 是什么

**`stride` 告诉你「在某一维上走一步，内存里要跳几个元素」**。

```
x = [[0,1,2],
     [3,4,5]]       内存里的实际排列：[0][1][2][3][4][5]
                     stride = (3, 1)

  访问 x[1][0] = 内存下标 1*3 + 0*1 = 3  → 值 3   ✓
```

**转置不移动数据**，只改 stride：

```
x.T 逻辑上是 [[0,3],
              [1,4],
              [2,5]]   但内存里还是 [0][1][2][3][4][5]
                       stride = (1, 3)

  访问 x.T[1][0] = 内存下标 1*1 + 0*3 = 1  → 值 1  ✓
```

## 为什么这很重要

```python
try:
    x.T.view(6)
except RuntimeError as e:
    print("失败:", str(e)[:100])
```

```
失败: view size is not compatible with input tensor's size and stride
      (at least one dimension spans across two contiguous subspaces).
      Use .reshape(...) instead.
```

**`view` 要求内存连续**（能用一个 stride 描述），而转置后的张量不连续，所以 `view` 报错。

| 方法 | 要求 | 速度 | 安全性 |
|---|---|---|---|
| `.view()` | 内存必须连续 | 快（零拷贝） | 会报错 |
| `.reshape()` | 无要求 | 可能需要拷贝 | **总是能用** |

```python
print("x.T.reshape(6)            =", x.T.reshape(6).tolist())
print("x.T.contiguous().view(6)  =", x.T.contiguous().view(6).tolist())
```

```
x.T.reshape(6)            = [0, 3, 1, 4, 2, 5]
x.T.contiguous().view(6)  = [0, 3, 1, 4, 2, 5]
```

**实用建议**：**日常用 `reshape`**（总是能用）。只有在确认连续且追求性能时才用 `view`。

---
