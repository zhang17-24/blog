---
title: 高级索引
description: index_select / 花式索引 / gather / 布尔索引，以及 gather 与交叉熵的关系。
---

# 9. 高级索引

![高级索引](/figs/tensor-ops/12-advanced-index.png)

```python
x = torch.tensor([[10, 11, 12], [13, 14, 15], [16, 17, 18]])

print("index_select(0, [2,0]) ->\n", torch.index_select(x, 0, torch.tensor([2, 0])))
idx = torch.tensor([2, 0, 1])
print("花式索引 x[arange(3), idx] ->", x[torch.arange(3), idx].tolist())
print("gather(dim=1) ->\n", torch.gather(x, 1, idx.unsqueeze(1)))
print("masked: x[x > 12] ->", x[x > 12].tolist())
```

```
index_select(0, [2,0]) ->
 tensor([[16, 17, 18],
        [10, 11, 12]])
花式索引 x[arange(3), idx] -> [12, 13, 17]
gather(dim=1) ->
 tensor([[12],
        [13],
        [17]])
masked: x[x > 12]      -> [13, 14, 15, 16, 17, 18]
```

## 三种索引的用途

| 方法 | 挑选粒度 | 形状 | 典型用途 |
|---|---|---|---|
| `index_select` | 整行/整列 | 保留维度 | 按索引取样本 |
| 花式索引 `x[a, b]` | 逐元素 | 会降维 | 取对角线、按位置取值 |
| `gather` | 逐元素 | **同 input** | 从 logits 取目标类的分数 |
| 布尔索引 | 逐元素 | **压平** | 过滤 |

**`gather` 是 cross entropy 的内部实现**：

```python
logits = torch.randn(4, 10)                # 4 个样本，10 个类别
targets = torch.tensor([3, 7, 1, 9])
# 取每个样本「正确类别」的分数
picked = torch.gather(logits, 1, targets.unsqueeze(1))
print(picked.shape)                        # (4, 1)
```

---
