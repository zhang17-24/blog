---
title: 拼接与堆叠
description: cat 在已有维度上拼、stack 新增一维，以及各自的形状要求。
---

# 7. 拼接与堆叠：cat / stack

![拼接与堆叠](/figs/tensor-ops/09-cat-stack.png)

```python
a, b = torch.tensor([[1, 2], [3, 4]]), torch.tensor([[5, 6], [7, 8]])

print("cat(dim=0)  ->", tuple(torch.cat([a, b], 0).shape))
print("cat(dim=1)  ->", tuple(torch.cat([a, b], 1).shape))
print("stack(dim=0)->", tuple(torch.stack([a, b], 0).shape))
print("stack(dim=1)->", tuple(torch.stack([a, b], 1).shape))
print("stack(dim=2)->", tuple(torch.stack([a, b], 2).shape))
```

```
cat(dim=0)  -> (4, 2)
cat(dim=1)  -> (2, 4)
stack(dim=0)-> (2, 2, 2)
stack(dim=1)-> (2, 2, 2)
stack(dim=2)-> (2, 2, 2)
```

## 核心区别

| | `cat` | `stack` |
|---|---|---|
| 操作 | 在**已有维度**上拼接 | **新增**一个维度 |
| 形状要求 | **除了拼接维，其他必须相同** | **必须完全相同** |
| 维度数 | 不变 | **+1** |

**`stack` 的三个方向**（都是 `(2,2)` → `(2,2,2)`）：

```
stack(dim=0):  [a, b]        —— 两个矩阵叠起来
stack(dim=1):  a 和 b 的行交替 —— [[a[0], b[0]], [a[1], b[1]]]
stack(dim=2):  a 和 b 的元素交替
```

## cat 的不等长情况

```python
p = torch.zeros(2, 3)
q = torch.zeros(2, 1)
print("cat([(2,3),(2,1)], dim=1) ->", tuple(torch.cat([p, q], 1).shape))   # (2,4)
```

```
cat([(2,3),(2,1)], dim=1) -> (2, 4)
```

**`dim=1` 时，其他维（第 0 维）必须相同（都是 2），拼接维可以不同（3 和 1）。** 这就是 `cat` 比 `stack` 灵活的地方。

`dim=0` 时则要求第 1 维相同：

```
cat(..., dim=0) 失败: Sizes of tensors must match except in dimension 0.
                     Expected size 3 but got size 1 for tensor number 1 in the list
```

---
