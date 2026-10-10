---
title: 一页速查
description: 查形状、改形状、拼接、归约、索引，一页速查。
---

# 附录：一页速查

```python
# ---- 查形状 ----
x.shape           # 每一维长度          ★ 排查第一步
x.ndim            # 维度数
x.numel()         # 元素总数
x.dtype           # 数据类型
x.device          # 所在设备
x.stride()        # 内存步长
x.is_contiguous() # 是否内存连续

# ---- 改形状 ----
x.reshape(...)              # 最安全，-1 自动推断
x.view(...)                 # 要求内存连续（更快）
x.flatten(start_dim=1)      # 保留 batch 维，拉平其余
x.squeeze()                 # 删掉长度为 1 的维度
x.unsqueeze(n)              # 在第 n 个位置插入维度
x.transpose(i, j)           # 交换两维
x.permute(...)              # 重排所有维度
x.T                         # 全部反转（二维常用）

# ---- 拼接 ----
torch.cat([a, b], dim=n)    # 在 dim=n 上拼接（其他维必须同）
torch.stack([a, b], dim=n)  # 新增一维（形状必须全同）
torch.split(x, size, dim)   # 切成多块

# ---- 归约 ----
x.sum(dim=n, keepdim=True)   # 求和
x.mean(dim=n, keepdim=True)  # 均值
x.max(dim=n)                 # 返回 (values, indices)
x.argmax(dim=n)              # 只要下标
torch.softmax(x, dim=-1)     # 归一化成概率

# ---- 索引 ----
x[i, j]                # 单元素（降维）
x[i]                   # 一行（降维）
x[i:j]                 # 切片（保维）
x[:, n]                # 一列（降维）
x[x > 0]               # 布尔索引（压平）
torch.index_select(x, dim, idx)      # 按索引取
torch.gather(x, dim, idx)            # 逐元素取

# ---- 判断广播能否成功（手动推演）----
def broadcast_result(*shapes):
    """传入若干形状，返回广播后的形状（从后往前对齐）"""
    ndim = max(len(s) for s in shapes)
    padded = [(1,) * (ndim - len(s)) + tuple(s) for s in shapes]
    out = []
    for dim_sizes in zip(*padded):
        big = max(dim_sizes)
        if any(d not in (1, big) for d in dim_sizes):
            return f"❌ 无法广播: {dim_sizes}"
        out.append(big)
    return tuple(out)

print(broadcast_result((2,3,4), (3,1)))    # (2, 3, 4)
print(broadcast_result((3,1), (3,)))       # (3, 3)
print(broadcast_result((2,3), (2,4)))      # ❌ 无法广播
```

---

**配套材料**：

- [PyTorch 入门学习笔记](/guides/pytorch/) —— API 和完整训练流程
- [深度学习进阶](/guides/deep-learning/) —— 原理推导和 Transformer

**源文件**：

- [make_figs.py](/downloads/tensor-ops-make-figs.py) —— 生成全部 14 张图
- [verify.py](/downloads/tensor-ops-verify.py) —— 验证本文所有代码输出
