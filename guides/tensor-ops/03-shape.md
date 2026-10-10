---
title: 形状变换
description: reshape / view / transpose / permute / flatten：改形状不改数据。
---

# 3. 形状变换：reshape / view / transpose

## reshape 与 view：只改「排版」，不改数据

![reshape](/figs/tensor-ops/03-reshape.png)

```python
x = torch.arange(1, 13).reshape(3, 4)
print("原始:", tuple(x.shape))
print("reshape(2, 6)  ->", tuple(x.reshape(2, 6).shape))
print("reshape(-1)    ->", tuple(x.reshape(-1).shape), "（-1 表示自动推断）")
print("reshape(2, -1) ->", tuple(x.reshape(2, -1).shape))
```

```
原始: (3, 4)
reshape(2, 6)  -> (2, 6)
reshape(-1)    -> (12,) （-1 表示自动推断）
reshape(2, -1) -> (2, 6)
```

**硬性约束**：`reshape` 前后元素总数必须相等（`numel()` 不变）。`(3,4)=12` 个元素，可以变成 `(2,6)`、`(12,)`、`(1,12)`、`(2,2,3)`，但**不能**变成 `(5,3)`。

**`-1` 是通配符**：让 PyTorch 自动算出这一维应该是多少。`(3,4).reshape(2,-1)` → 自动算出 `-1` = 6。

## transpose 与 permute：交换维度

![转置](/figs/tensor-ops/04-transpose.png)

```python
x = torch.arange(1, 13).reshape(3, 4)
print("T              ->", tuple(x.T.shape))
print("transpose(0,1) ->", tuple(x.transpose(0, 1).shape))

z = torch.zeros(2, 3, 4)
print("\n三维 (2,3,4):")
print("  permute(2,0,1) ->", tuple(z.permute(2, 0, 1).shape))
print("  permute(1,2,0) ->", tuple(z.permute(1, 2, 0).shape))
print("  transpose(0,2) ->", tuple(z.transpose(0, 2).shape))
```

```
T              -> (4, 3)
transpose(0,1) -> (4, 3)

三维 (2,3,4):
  permute(2,0,1) -> (4, 2, 3)
  permute(1,2,0) -> (3, 4, 2)
  transpose(0,2) -> (4, 3, 2)
```

**区别**：

| 方法 | 能力 | 适用 |
|---|---|---|
| `.T` | 反转所有维度 | 二维（矩阵） |
| `.transpose(i, j)` | 交换任意两维 | 任意维 |
| `.permute(...)` | **重排所有维度** | 三维以上 |

**`permute` 的参数是「新顺序」不是「位置对」**。`permute(2,0,1)` 的意思是：新张量的第 0 维来自原来的第 2 维，第 1 维来自原来的第 0 维，第 2 维来自原来的第 1 维。

`(2,3,4)` 按 `(2,0,1)` 重排 → 取原第 2 维(4)、第 0 维(2)、第 1 维(3) → `(4,2,3)` ✓

## flatten：拉平

```python
print("flatten()      ->", tuple(x.flatten().shape))
print("flatten(1)     ->", tuple(x.reshape(2, 6).flatten(1).shape))
```

```
flatten()      -> (12,)
flatten(1)     -> (2, 6)
```

**`flatten(1)` 是最常用的形式**——它保留第 0 维（batch 维），只把后面的维度拉平。这正是从卷积到全连接需要做的操作。

---
