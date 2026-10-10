---
title: 练习题
description: 8 道预测形状与排查 bug 的题，答案折叠。
---

# 13. 练习题

先自己想，再展开答案。

**Q1** — 预测形状：

```python
a = torch.zeros(2, 3, 4)
b = torch.zeros(3, 1)
print((a + b).shape)
```

<details>
<summary>答案</summary>

**`(2, 3, 4)`**

逐维对齐：
```
  (2, 3, 4)
+ (   3, 1)   ← 前面补 1 → (1, 3, 1)
─────────────
逐维取最大：max(2,1)=2, max(3,3)=3, max(4,1)=4
→ (2, 3, 4)
```
</details>

**Q2** — 下面这段代码有什么问题？

```python
x = torch.randn(4, 5)        # 4 个样本，5 个特征
x = x - x.mean(dim=1)        # 想做标准化
```

<details>
<summary>答案</summary>

**会直接报错**（这是好事）：

```
RuntimeError: The size of tensor a (5) must match the size of tensor b (4)
              at non-singleton dimension 1
```

**推演**：`x.mean(dim=1)` 的形状是 `(4,)`，广播时补成 `(1,4)`，和 `(4,5)` 对齐后最后一维是 `5 vs 4`，不匹配 → 报错。

**正确写法**：
```python
x = x - x.mean(dim=1, keepdim=True)     # (4,5) - (4,1) → (4,5) ✓
```

**但请注意一个例外**：如果 `x` 是**方阵**，这个错误会静默通过。

```python
x = torch.randn(3, 3)          # 方阵
r = x - x.mean(dim=1)          # 不报错！(3,3) - (3,) 恰好能广播
print(r.shape)                 # (3,3) —— 看起来「成功」了
```

因为 `(3,)` 补成 `(1,3)`，最后一维恰好都是 3。**这是巧合，不是你的本意。方阵是唯一会踩到这个坑的形状。**

**所以真正的危险不是「报错」，而是「碰巧能算但语义错」**——详见[第 5 节](/guides/tensor-ops/05-broadcasting)里 `dim` 用错的例子。
</details>

**Q3** — `x[0]` 和 `x[0:1]` 有什么区别？

<details>
<summary>答案</summary>

```python
x = torch.arange(12).reshape(3, 4)
print(x[0].shape)      # (4,)   —— 维度减 1
print(x[0:1].shape)    # (1, 4) —— 维度保留
```

**`x[0]` 是「取第 0 行」，降维。**
**`x[0:1]` 是「取第 0 行到第 1 行之间」，是切片，不降维。**

**实际影响**：
```python
batch = x[0]            # (4,)    —— 少了 batch 维！
batch = x[0:1]          # (1, 4)  —— 正确的「只取一个样本」
model(batch)            # 用 x[0] 可能报错或行为异常
```

**规则**：单个整数索引 → 降维；切片（含冒号） → 保维。**想保持维度就用切片或 `unsqueeze`。**
</details>

**Q4** — 怎么把 `(N, H, W, C)` 变成 `(N, C, H, W)`？

<details>
<summary>答案</summary>

```python
x = torch.randn(8, 224, 224, 3)          # NHWC
y = x.permute(0, 3, 1, 2)                 # NCHW
print(y.shape)                            # (8, 3, 224, 224)
```

**`permute(0, 3, 1, 2)` 的含义**：新第 0 维来自原第 0 维，新第 1 维来自原第 3 维，以此类推。

`(N,H,W,C)` 按 `(0,3,1,2)` 取 → `(N, C, H, W)` ✓

**注意**：`permute` 后张量**不连续**，如果后面要 `view` 需要先 `.contiguous()`。这也是把 TensorFlow 模型转到 PyTorch 最常踩的坑。
</details>

**Q5** — 为什么这个 `cat` 会报错？

```python
a = torch.zeros(2, 3)
b = torch.zeros(2, 1)
torch.cat([a, b], dim=0)
```

<details>
<summary>答案</summary>

报错：`Sizes of tensors must match except in dimension 0. Expected size 3 but got size 1`

**`cat` 的规则**：除了 `dim` 指定的那一维，其他维必须完全相同。

- `dim=0` → 第 1 维（3 和 1）必须相同 → 不同 → 报错
- `dim=1` → 第 0 维（2 和 2）相同 → 可以拼 → `(2, 4)` ✓

所以 `torch.cat([a, b], dim=1)` 是对的。
</details>

**Q6** — 报错 `mat1 and mat2 shapes cannot be multiplied (2x3 and 4x2)`，怎么排查？

<details>
<summary>答案</summary>

**读法**：第一个矩阵是 `(2,3)`，第二个是 `(4,2)`。

**矩阵乘要求**：`(m, k) @ (k, n)`，即第一个的**最后一维**必须等于第二个的**倒数第二维**。

这里 `3 ≠ 4` → 报错。

**排查步骤**：
1. `print(a.shape, b.shape)` 确认形状
2. 想清楚你要做什么：
   - 如果要「矩阵乘」→ 检查是不是该对某一个转置（`.T`）
   - 如果要「逐元素」→ 应该用 `*` 不是 `@`
   - 如果要「算相似度」→ 需要 `a @ b.T`
3. 如果是 `nn.Linear` 报的错 → 检查输入的**最后一维**是否等于 `in_features`

```python
lin = nn.Linear(10, 5)
lin(torch.randn(8, 7))     # ❌ (8,7) 最后一维是 7 ≠ 10
lin(torch.randn(8, 10))    # ✅
```
</details>

**Q7** — 归约后维度消失了导致广播失败，怎么快速定位？

<details>
<summary>答案</summary>

**症状**：形状「看起来能算」但结果不对，或者报广播错误。

**快速定位方法**：把归约前后的形状都打出来。

```python
x = torch.randn(4, 5, 6)
print("x:            ", x.shape)
print("x.mean(1):    ", x.mean(1).shape)          # (4,6) —— 5 没了
print("x.mean(1,keepdim=True):", x.mean(1, keepdim=True).shape)  # (4,1,6)
```

**规律**：`dim=n` 会「消灭第 n 维」。

**修法两种**：
```python
# ① keepdim=True（推荐）
y = x / x.mean(1, keepdim=True)

# ② 手动 unsqueeze
y = x / x.mean(1).unsqueeze(1)
```

**`keepdim=True` 更清晰**，直接在语义上说明「我要保留这个维度」。PyTorch 的 `BatchNorm`、`LayerNorm` 内部都是这么做的。
</details>

**Q8**（进阶）— 为什么 `LayerNorm` 的 `normalized_shape` 参数要传 `(D,)` 而不是 `D`？

<details>
<summary>答案</summary>

因为**归一化的维度可以是多个**。

```python
ln1 = nn.LayerNorm(64)              # 等价于 normalized_shape=(64,)
ln2 = nn.LayerNorm((64,))           # 完全一样
ln3 = nn.LayerNorm((8, 64))         # 对最后两维一起归一化
```

**关键点**：`LayerNorm` 会**把最后 `len(normalized_shape)` 个维度当成一组**，在这一组内算均值和方差。

```python
x = torch.randn(4, 10, 64)          # (batch, seq, d_model)
ln = nn.LayerNorm(64)               # 对最后一维归一化
print(ln(x).shape)                  # (4, 10, 64)

ln2 = nn.LayerNorm((10, 64))
print(ln2(x).shape)                 # (4, 10, 64) —— 但对 (10,64) 整体归一化
```

**这就是为什么 Transformer 里 `LayerNorm` 只对特征维归一化**——每个 token 独立处理，与 batch 和序列长度无关。这也是它优于 `BatchNorm` 的根本原因（详见[深度学习进阶第 6 篇](/guides/deep-learning/part2-dl-principles/06-normalization)）。
</details>

---
