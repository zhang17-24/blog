---
title: 增删维度
description: squeeze 只删长度为 1 的维度；unsqueeze(n) 是插入而不是修改。
---

# 4. 增删维度：squeeze / unsqueeze

![增删维度](/figs/tensor-ops/05-squeeze.png)

```python
a = torch.zeros(1, 4)
print("(1,4) squeeze()      ->", tuple(a.squeeze().shape))
print("(1,4) squeeze(0)     ->", tuple(a.squeeze(0).shape))
print("(4,)  unsqueeze(0)   ->", tuple(torch.zeros(4).unsqueeze(0).shape))
print("(4,)  unsqueeze(1)   ->", tuple(torch.zeros(4).unsqueeze(1).shape))
print("(3,4) unsqueeze(0)   ->", tuple(torch.zeros(3, 4).unsqueeze(0).shape))
print("(4,)  squeeze()      ->", tuple(torch.zeros(4).squeeze().shape))
```

```
(1,4) squeeze()      -> (4,)
(1,4) squeeze(0)     -> (4,)
(4,)  unsqueeze(0)   -> (1, 4)
(4,)  unsqueeze(1)   -> (4, 1)
(3,4) unsqueeze(0)   -> (1, 3, 4)
(4,)  squeeze()      -> (4,)
```

## 两个关键点

**① `squeeze()` 只删长度为 1 的维度。** 如果该维度不是 1，它什么也不做（不报错）。

```python
print(torch.zeros(3, 4).squeeze().shape)   # (3, 4) —— 没变
```

**② `unsqueeze(n)` 在第 n 个位置【插入】一个维度**，不是修改第 n 维。

| 原形状 | `unsqueeze(0)` | `unsqueeze(1)` | `unsqueeze(2)` |
|---|---|---|---|
| `(4,)` | `(1,4)` | `(4,1)` | ❌ 越界 |
| `(3,4)` | `(1,3,4)` | `(3,1,4)` | `(3,4,1)` |

**最常用场景**：给单张图片加 batch 维。

```python
img = torch.randn(3, 224, 224)        # 一张图 (C,H,W)
batch = img.unsqueeze(0)              # (1,3,224,224) —— 模型要吃 batch
```

---
