---
title: 广播机制 ★
description: 最容易出错的一节。从最后一维往前对齐，四种情况逐一推演，含静默出错的防御手段。
---

# 5. 广播机制（最容易出错的一节）

**广播规则（从最后一维往前对齐）**：

```
① 维度数不同 → 在【前面】补 1
② 尺寸相同   → 直接用
③ 尺寸为 1   → 拉伸到另一边
④ 都不匹配   → 报错
```

## 情况 1：矩阵 + 行向量

![广播-行](/figs/tensor-ops/06-broadcast-row.png)

```python
A = torch.ones(3, 3)
b = torch.tensor([10., 20., 30.])
print("A(3,3) + b(3,) ->", tuple((A + b).shape))
print(A + b)
```

```
A(3,3) + b(3,) -> (3, 3)
tensor([[11., 21., 31.],
        [11., 21., 31.],
        [11., 21., 31.]])
```

`b` 从 `(3,)` 被**补成 `(1,3)`**，再拉伸成 `(3,3)`。每一行都加上同一个 `b`。

## 情况 2：列向量 × 行向量 → 外积形状

![广播-外积](/figs/tensor-ops/07-broadcast-outer.png)

**这是最容易懵的情况。**

```python
col = torch.tensor([[1.], [2.], [3.]])     # (3,1)
row = torch.tensor([10., 20., 30.])         # (3,)
print("col(3,1) * row(3,) ->", tuple((col * row).shape))
print(col * row)
```

```
col(3,1) * row(3,) -> (3, 3)
tensor([[10., 20., 30.],
        [20., 40., 60.],
        [30., 60., 90.]])
```

**为什么是 `(3,3)` 而不是 `(3,1)`？** 逐维对齐看：

```
  (3, 1)
* (3,   )      ← 维度数少，前面补 1 → (1, 3)
─────────
最后一维：  1 vs 3  → 1 被拉伸成 3
倒数第二维：3 vs 1  → 1 被拉伸成 3
─────────
结果：      (3, 3)     ★ 3 个元素变成了 9 个
```

**这个行为常常不是你想要的。** 如果你想做「每行减去自己的均值」，写成 `x - x.mean(dim=1)` 会怎样？

```python
x = torch.randn(4, 5)
print(x.mean(dim=1).shape)               # (4,)   —— 是 1 维向量
x - x.mean(dim=1)                        # ❌ 直接报错（见下）
print(x.mean(dim=1, keepdim=True).shape) # (4, 1)
y = x - x.mean(dim=1, keepdim=True)      # ✅ (4,5) - (4,1) → (4,5)
```

**好消息：这里会直接报错，不会静默出错。**

```
RuntimeError: The size of tensor a (5) must match the size of tensor b (4)
              at non-singleton dimension 1
```

推演一下为什么：`(4,5)` 减 `(4,)`，后者补成 `(1,4)`，最后一维 `5 vs 4` 不匹配 → 报错。

**但有一个例外，而且很危险：**

```python
x = torch.zeros(3, 3)          # ★ 方阵
r = x - torch.zeros(3)         # 不报错！→ (3,3)
```

**方阵时 `(3,3) - (3,)` 会静默通过**（因为 `(3,)` 补成 `(1,3)`，最后一维恰好都是 3）。这是**巧合**，不是你的本意。**方阵是唯一会踩到这个坑的形状。**

## 真正危险的静默 bug：dim 用错

比「形状报错」更危险的是**形状对得上、不报错、但语义全错**：

```python
x = torch.tensor([[1., 2., 3.], [10., 20., 30.]])   # 2 个样本，3 个特征

print("按行(样本)归一化 dim=1:\n", x - x.mean(dim=1, keepdim=True))
print("按列(特征)归一化 dim=0:\n", x - x.mean(dim=0, keepdim=True))
```

**实测输出**：

```
按行(样本)归一化 dim=1:
tensor([[ -1.,   0.,   1.],
        [-10.,   0.,  10.]])

按列(特征)归一化 dim=0:
tensor([[-4.5000,  -9.0000, -13.5000],
        [ 4.5000,   9.0000,  13.5000]])
```

**两者都不报错、形状都是 `(2,3)`，但结果完全不同。**

**这是最需要警惕的一类 bug**——报错是好事（它告诉你哪里错了），静默出错会浪费你几小时甚至几天。

**防御手段**：对归一化/标准化这类操作，**写完立刻验证「结果的性质是否符合预期」**：

```python
normed = x - x.mean(dim=1, keepdim=True)
print(normed.sum(dim=1).tolist())    # [0.0, 0.0] ← 每行均值为 0 ✓ 对了
```

**记住：涉及「按某一维做归一化」时，永远用 `keepdim=True`，并立刻验证结果的和/均值。**

## 情况 3：其他常见组合

```python
print("标量:    (2,3) + 1.0      ->", tuple((torch.zeros(2, 3) + 1.0).shape))
print("多对一:  (2,1,4) + (3,1)  ->", tuple((torch.zeros(2, 1, 4) + torch.zeros(3, 1)).shape))
print("互补:    (1,3)   + (4,1)  ->", tuple((torch.zeros(1, 3) + torch.zeros(4, 1)).shape))
```

```
标量:    (2,3) + 1.0      -> (2, 3)
多对一:  (2,1,4) + (3,1)  -> (2, 3, 4)
互补:    (1,3)   + (4,1)  -> (4, 3)
```

**`(2,1,4) + (3,1)` 的推演**：

```
  (2, 1, 4)
+ (   3, 1)     ← 前面补 1 → (1, 3, 1)
─────────────
逐维取最大：max(2,1)=2, max(1,3)=3, max(4,1)=4
─────────────
结果：(2, 3, 4)
```

## 情况 4：失败

```python
try:
    torch.zeros(2, 3) + torch.zeros(2, 4)
except RuntimeError as e:
    print(e)
```

```
The size of tensor a (3) must match the size of tensor b (4) at non-singleton dimension 1
```

**注意报错信息里的「non-singleton dimension 1」**——它告诉你是**第 1 维**（从 0 开始数）出问题了，尺寸 3 和 4 都不为 1，无法广播。

**读报错信息的技巧**：看到这个错误，立刻去检查这一维。

---
