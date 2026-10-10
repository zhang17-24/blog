#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档代码验证脚本
================
把《张量运算图解》正文里要用到的所有代码跑一遍，收集真实输出。
确保文档里写的每一个输出都是实测的。
"""
import torch

def sec(n, title):
    print(f"\n{'='*62}\n{n} {title}\n{'='*62}")


# ---------------------------------------------------------- 维度
sec("1", "张量与维度")
s = torch.tensor(7)
v = torch.tensor([3, 1, 4, 1, 5])
m = torch.tensor([[1, 2, 3], [4, 5, 6]])
c = torch.zeros(3, 2, 2)
for name, t in [("标量", s), ("向量", v), ("矩阵", m), ("3维", c)]:
    print(f"{name:4s} shape={str(tuple(t.shape)):12s} ndim={t.ndim}  numel={t.numel()}")


# ---------------------------------------------------------- 索引切片
sec("2", "索引与切片")
x = torch.arange(1, 13).reshape(3, 4)
print("x =\n", x)
print("x[0]        =", x[0].tolist(), "shape", tuple(x[0].shape))
print("x[:, 1]     =", x[:, 1].tolist(), "shape", tuple(x[:, 1].shape))
print("x[0:2, 1:3] =\n", x[0:2, 1:3], "shape", tuple(x[0:2, 1:3].shape))
print("x[-1]       =", x[-1].tolist(), "（负数从后往前数）")
print("x[1, 2]     =", x[1, 2].item(), "（取单个元素，变标量）")
# 布尔索引
print("x[x > 6]    =", x[x > 6].tolist())


# ---------------------------------------------------------- 形状变换
sec("3", "形状变换")
x = torch.arange(1, 13).reshape(3, 4)
print("原始:", tuple(x.shape))
print("reshape(2, 6)  ->", tuple(x.reshape(2, 6).shape))
print("reshape(-1)    ->", tuple(x.reshape(-1).shape), "（-1 表示自动推断）")
print("reshape(2, -1) ->", tuple(x.reshape(2, -1).shape))
print("T              ->", tuple(x.T.shape))
print("transpose(0,1) ->", tuple(x.transpose(0, 1).shape))
print("flatten()      ->", tuple(x.flatten().shape))
print("flatten(1) 保持 batch 维 ->", tuple(x.reshape(2, 6).flatten(1).shape))

# permute 三维
z = torch.zeros(2, 3, 4)
print("\n三维 (2,3,4):")
print("  permute(2,0,1) ->", tuple(z.permute(2, 0, 1).shape))
print("  permute(1,2,0) ->", tuple(z.permute(1, 2, 0).shape))
print("  transpose(0,2) ->", tuple(z.transpose(0, 2).shape))

# squeeze / unsqueeze
a = torch.zeros(1, 4)
print("\nsqueeze / unsqueeze:")
print("  (1,4) squeeze()      ->", tuple(a.squeeze().shape))
print("  (1,4) squeeze(0)     ->", tuple(a.squeeze(0).shape))
print("  (4,)  unsqueeze(0)   ->", tuple(torch.zeros(4).unsqueeze(0).shape))
print("  (4,)  unsqueeze(1)   ->", tuple(torch.zeros(4).unsqueeze(1).shape))
print("  (3,4) unsqueeze(0)   ->", tuple(x.unsqueeze(0).shape), "  ← 加 batch 维")
print("  (1,4) squeeze() 对 (4,) 无效 ->", tuple(torch.zeros(4).squeeze().shape))


# ---------------------------------------------------------- 广播
sec("4", "广播机制")
A = torch.ones(3, 3)
b = torch.tensor([10, 20, 30])
print("A(3,3) + b(3,)     ->", tuple((A + b).shape))
col = torch.tensor([[1.], [2.], [3.]])
row = torch.tensor([10., 20., 30.])
print("col(3,1) * row(3,) ->", tuple((col * row).shape), "★ 是 (3,3) 不是 (3,1)")
print("结果 =\n", col * row)
print("\n标量广播: (2,3) + 1.0 ->", tuple((torch.zeros(2, 3) + 1.0).shape))
print("(2,1,4) + (3,1) ->", tuple((torch.zeros(2, 1, 4) + torch.zeros(3, 1)).shape))
print("(1,3)   + (4,1) ->", tuple((torch.zeros(1, 3) + torch.zeros(4, 1)).shape))
# 失败案例
try:
    torch.zeros(2, 3) + torch.zeros(2, 4)
except RuntimeError as e:
    print("\n失败案例 (2,3)+(2,4):")
    print("  ", str(e).replace("\n", " ")[:110])


# ---------------------------------------------------------- 乘法
sec("5", "逐元素乘 vs 矩阵乘")
A = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
B = torch.tensor([[10., 20., 30.], [40., 50., 60.]])
print("A * B  (逐元素) shape", tuple((A * B).shape))
print(A * B)
print("\nA @ B.T  (矩阵乘) shape", tuple((A @ B.T).shape))
print(A @ B.T)
print("\n内积 x·y:", torch.dot(torch.tensor([1., 2.]), torch.tensor([3., 4.])).item())
# 批量矩阵乘
X = torch.randn(8, 4, 5)      # 8 个 (4,5) 矩阵
W = torch.randn(5, 3)
print("\n批量: (8,4,5) @ (5,3) ->", tuple((X @ W).shape))
# 失败
try:
    A @ B
except RuntimeError as e:
    print("\n失败案例 A(2,3) @ B(2,3):")
    print("  ", str(e).replace("\n", " ")[:110])


# ---------------------------------------------------------- 拼接
sec("6", "拼接与堆叠")
a, b = torch.tensor([[1, 2], [3, 4]]), torch.tensor([[5, 6], [7, 8]])
print("cat(dim=0)  ->", tuple(torch.cat([a, b], 0).shape))
print(torch.cat([a, b], 0))
print("cat(dim=1)  ->", tuple(torch.cat([a, b], 1).shape))
print(torch.cat([a, b], 1))
print("stack(dim=0)->", tuple(torch.stack([a, b], 0).shape))
print("stack(dim=1)->", tuple(torch.stack([a, b], 1).shape))
print("stack(dim=2)->", tuple(torch.stack([a, b], 2).shape))
print("\n不等长的 cat:")
p = torch.zeros(2, 3)
q = torch.zeros(2, 1)
print("  cat([(2,3),(2,1)], dim=1) ->", tuple(torch.cat([p, q], 1).shape))
try:
    torch.cat([p, q], 0)
except RuntimeError as e:
    print("  cat(..., dim=0) 失败:", str(e).replace("\n", " ")[:90])


# ---------------------------------------------------------- 归约
sec("7", "归约操作")
x = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
print("x =\n", x)
print("sum()             =", x.sum().item(), "  shape", tuple(x.sum().shape))
print("sum(dim=0)        =", x.sum(0).tolist(), "  shape", tuple(x.sum(0).shape))
print("sum(dim=1)        =", x.sum(1).tolist(), "  shape", tuple(x.sum(1).shape))
print("sum(dim=1,keepdim)= ", x.sum(1, keepdim=True).flatten().tolist(),
      " shape", tuple(x.sum(1, keepdim=True).shape))
print("mean(dim=0)       =", x.mean(0).tolist())
print("max(dim=1)        =", x.max(1).values.tolist(), "index", x.max(1).indices.tolist())
print("argmax(dim=1)     =", x.argmax(1).tolist())
print("softmax(dim=1)    =\n", torch.softmax(x, 1))
print("  每行和 =", torch.softmax(x, 1).sum(1).tolist())
print("\n★ 归约后维度会消失（除非 keepdim=True），这是广播失败的常见原因")


# ---------------------------------------------------------- 高级索引
sec("8", "高级索引")
x = torch.tensor([[10, 11, 12], [13, 14, 15], [16, 17, 18]])
print("x =\n", x)
print("index_select(0, [2,0])  ->\n", torch.index_select(x, 0, torch.tensor([2, 0])))
idx = torch.tensor([2, 0, 1])
print("花式索引 x[torch.arange(3), idx] ->", x[torch.arange(3), idx].tolist())
print("gather(dim=1)          ->\n", torch.gather(x, 1, idx.unsqueeze(1)))
print("masked: x[x > 12]      ->", x[x > 12].tolist())


# ---------------------------------------------------------- 内存
sec("9", "内存布局与 view")
x = torch.arange(6).reshape(2, 3)
print("x.stride()      =", x.stride())
print("x.T.stride()    =", x.T.stride(), "  ← 数据没动，只是换了读法")
print("x.T.is_contiguous() =", x.T.is_contiguous())
try:
    x.T.view(6)
except RuntimeError as e:
    print("x.T.view(6) 失败:", str(e).replace("\n", " ")[:80])
print("x.T.reshape(6) 成功:", x.T.reshape(6).tolist(), "  ← reshape 自动拷贝")
print("x.T.contiguous().view(6) 成功:", x.T.contiguous().view(6).tolist())
print("\n★ 结论：view 要求内存连续（更快），reshape 自动处理（更安全）")


# ---------------------------------------------------------- 实战报错
sec("10", "高频报错分类")
cases = []

# 1 形状不匹配
try:
    torch.zeros(2, 3) @ torch.zeros(2, 3)
except RuntimeError as e:
    cases.append(("矩阵乘内维不匹配", str(e)))

# 2 广播不兼容
try:
    torch.zeros(2, 3) + torch.zeros(2, 4)
except RuntimeError as e:
    cases.append(("广播维度不兼容", str(e)))

# 3 view 不连续
try:
    torch.zeros(2, 3).T.view(6)
except RuntimeError as e:
    cases.append(("view 遇到非连续张量", str(e)))

# 4 设备不一致
if torch.cuda.is_available():
    try:
        torch.zeros(2).cuda() + torch.zeros(2)
    except RuntimeError as e:
        cases.append(("设备不一致", str(e)))

# 5 数据类型
try:
    torch.zeros(2, dtype=torch.int64) + torch.zeros(2, dtype=torch.float32)
except RuntimeError as e:
    cases.append(("dtype 不兼容", str(e)))
else:
    cases.append(("dtype 不兼容", "（PyTorch 会自动提升为 float32，不报错）"))

for name, msg in cases:
    print(f"\n【{name}】")
    print("  ", msg.replace("\n", " ")[:150])

print("\n" + "=" * 62)
print("全部代码验证完成")
print("=" * 62)
