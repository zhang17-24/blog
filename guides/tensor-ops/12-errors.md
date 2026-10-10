---
title: 报错对照表
description: 9 条高频报错的成因与修法。看到报错先 print(x.shape)。
---

# 12. 高频报错对照表

**看到报错先做一件事：`print(x.shape)`（把所有涉及的张量都打出来）。**

| 报错信息关键词 | 原因 | 修法 |
|---|---|---|
| `mat1 and mat2 shapes cannot be multiplied` | 矩阵乘内维不匹配 | 检查 `@` 两侧的最后两维是否等于对方倒数第二维；可能漏了 `.T` |
| `must match the size of tensor b (4) at non-singleton dimension 1` | 广播不兼容 | 看报错指出的那一维；用 `unsqueeze` / `keepdim` 补齐 |
| `view size is not compatible ... size and stride` | 对非连续张量用 `view` | 改 `reshape`，或先 `.contiguous()` |
| `Expected all tensors to be on the same device` | 模型和数据不在同一设备 | 数据也要 `.to(device)` |
| `expected scalar type Float but found Long` | dtype 不匹配 | `.float()` 或 `.long()` |
| `only one element tensors can be converted to Python scalars` | 对多元素张量用 `.item()` | 用 `t[0].item()` 或 `.tolist()` |
| `shape '[...]' is invalid for input of size N` | reshape 元素数不对 | 检查 `numel()` 是否一致 |
| `IndexError: index out of range` | 索引越界 | 检查该维长度 |
| `The size of tensor a (8) must match tensor b (2)` | 多头注意力里 KV 头数不对 | 检查 Q 和 K 的头数（GQA 需要 repeat_interleave） |

## 三个真实报错示例

```python
# ① 矩阵乘内维不匹配
torch.zeros(2, 3) @ torch.zeros(2, 3)
# mat1 and mat2 shapes cannot be multiplied (2x3 and 2x3)

# ② 广播维度不兼容
torch.zeros(2, 3) + torch.zeros(2, 4)
# The size of tensor a (3) must match the size of tensor b (4) at non-singleton dimension 1

# ③ view 遇到非连续张量
torch.zeros(2, 3).T.view(6)
# view size is not compatible with input tensor's size and stride ...
```

## 一个反直觉的发现

**dtype 不匹配时 PyTorch 不报错**：

```python
a = torch.zeros(2, dtype=torch.int64)
b = torch.zeros(2, dtype=torch.float32)
print((a + b).dtype)      # torch.float32 —— 自动提升，不报错
```

**类型提升规则**（和 NumPy 类似）：`int64 + float32 → float32`。

**但这可能掩盖 bug**：如果你期望整数运算却得到浮点结果，可能在后续 `argmax`、索引或 `one_hot` 时才暴露出问题。**显式指定 dtype 是好习惯。**

---
