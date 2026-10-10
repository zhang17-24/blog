---
title: 归约操作
description: dim=n 就是「消灭第 n 维」。keepdim 为什么几乎总是必须的。
---

# 8. 归约操作：sum / mean / max

![归约](/figs/tensor-ops/10-reduction.png)

```python
x = torch.tensor([[1., 2., 3.], [4., 5., 6.]])

print("sum()             =", x.sum().item(), "  shape", tuple(x.sum().shape))
print("sum(dim=0)        =", x.sum(0).tolist(), "  shape", tuple(x.sum(0).shape))
print("sum(dim=1)        =", x.sum(1).tolist(), "  shape", tuple(x.sum(1).shape))
print("sum(dim=1,keepdim)= ", x.sum(1, keepdim=True).flatten().tolist(),
      " shape", tuple(x.sum(1, keepdim=True).shape))
print("max(dim=1)        =", x.max(1).values.tolist(), "index", x.max(1).indices.tolist())
print("argmax(dim=1)     =", x.argmax(1).tolist())
```

```
sum()             = 21.0   shape ()
sum(dim=0)        = [5.0, 7.0, 9.0]   shape (3,)
sum(dim=1)        = [6.0, 15.0]   shape (2,)
sum(dim=1,keepdim)=  [6.0, 15.0]  shape (2, 1)
max(dim=1)        = [3.0, 6.0] index [2, 2]
argmax(dim=1)     = [2, 2]
```

## dim 的方向（关键）

| 写法 | 效果 | 结果形状 | 记忆 |
|---|---|---|---|
| `x.sum()` | 全部求和 | `()` | 压成标量 |
| `x.sum(dim=0)` | **竖着压**（每列求和） | `(3,)` = 列数 | 消灭第 0 维 |
| `x.sum(dim=1)` | **横着压**（每行求和） | `(2,)` = 行数 | 消灭第 1 维 |

**规律：`dim=n` 就是「消灭第 n 维」，剩下的是其他维的长度。**

`(2,3)` 用 `dim=0` → 消灭 2 → 剩 `(3,)` ✓
`(2,3)` 用 `dim=1` → 消灭 3 → 剩 `(2,)` ✓

## 为什么 keepdim 这么重要

```python
x = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
print(x.shape)                            # (2,3)
print(x.mean(dim=1).shape)                # (2,)    ← 维度没了
print(x.mean(dim=1, keepdim=True).shape)  # (2,1)   ← 保留为 1
```

**忘了 keepdim 通常会报错**（`(2,3) - (2,)` 里最后一维 `3 vs 2` 不匹配）：

```python
wrong = x - x.mean(dim=1)
# RuntimeError: The size of tensor a (3) must match the size of tensor b (2)
#               at non-singleton dimension 1
```

**正确写法**：

```python
right = x - x.mean(dim=1, keepdim=True)
print(right)
print("每行和:", right.sum(dim=1).tolist())   # [0.0, 0.0] ✓ 每行均值为 0
```

**为什么 keepdim 是必须的**：`(2,3)` 减 `(2,1)` 广播成 `(2,3)`，是「**每行**减去**自己的**均值」；如果维度是 `(2,)`，广播语义完全不同（而且大概率报错）。

**立刻验证的习惯**：算完归一化，马上 `print(result.sum(dim=1))` 看是不是 0。

## softmax 一样的道理

```python
print(torch.softmax(x, 1))
```

```
tensor([[0.0900, 0.2447, 0.6652],
        [0.0900, 0.2447, 0.6652]])
```

`dim=1` 表示**在每一行内部做归一化**，所以每行和为 1。**分类任务里永远是 `softmax(dim=-1)`**（最后一维是类别）。

---
