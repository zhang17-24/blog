---
title: 练习清单
description: 15 个由浅入深的练习，覆盖张量、广播、autograd、训练循环和保存加载。
---

一共 40 道题，分5 组。全部代码在 [exercises.py](/downloads/pytorch-exercises.py)，题目和答案在各章末尾。

---

## 第 1 组 · 张量（10 题）

**对应**：[第 1 章 · 张量](/guides/pytorch/part2-tutorial/01-tensor)

- [ ] 1. `torch.zeros(2,3,4)` 加 `torch.zeros(4)` 结果形状是什么？
- [ ] 2. `a * b` 和 `a @ b` 有什么区别？哪个形状会变？
- [ ] 3. `b = a` 和 `b = a.clone()` 的本质区别？
- [ ] 4. 一行代码构造 5×5 单位矩阵，把非对角线位置置 0
- [ ] 5. 统计本章模型的参数量
- [ ] 6. 为什么 `t2.sum(dim=0).item()` 会报错？
- [ ] 7. 打印一个 5×5 单位矩阵的主对角线元素位置
- [ ] 8. `torch.cat` 和 `torch.stack` 的区别，各写一行
- [ ] 9. 把CPU 张量转成 NumPy 数组怎么写？
- [ ] 10. GPU 张量转 NumPy 要多做什么？

<details>
<summary>全部答案</summary>

1. `torch.Size([2,3,4])`，`b` 被广播成 `(1,1,4)`
2. `*` 逐元素，形状不变；`@` 是矩阵乘法，走 broadcasting 后形状可能变
3. `b = a` 是起别名，共享内存；`clone()` 才是真复制
4. `mask = torch.arange(5)[:,None] == torch.arange(5); m * mask.long()`
5. `sum(p.numel() for p in model.parameters())` = 669,706
6. `item()` 只能用于单元素张量，`sum(dim=0)` 有 2 个元素
7. `torch.arange(5)` 的位置
8. `cat` 在已有维度拼接（要求形状一致），`stack` 新增一个维度
9. `t.numpy()`
10. `t.cpu().numpy()`

</details>

---

## 第 2 组 · 自动微分（12 题）— 最重要的一组

**对应**：[第 5 章 · 自动微分](/guides/pytorch/part2-tutorial/05-autograd)

- [ ] 11. 为什么 `w.grad` 的形状一定等于 `w`？
- [ ] 12. 手算 `loss = w * x²` 在 `x=2, w=3` 时对 w 的梯度，用 autograd 验证
- [ ] 13. 为什么 `z.grad` 是 `None` 而 `z.grad_fn` 不是？
- [ ] 14. 找出这段训练代码的 bug

```python
for batch, (X, y) in dataloader:
    pred = model(X)
    loss = loss_fn(pred, y)
    loss.backward()
    optimizer.step()
```

- [ ] 15. 为什么 `x`（输入）不需要 `requires_grad=True`？
- [ ] 16. 连续两次 `loss.backward()`，梯度会怎样？代码验证
- [ ] 17. `zero_grad()` 之后再backward，梯度变回多少？
- [ ] 18. `torch.no_grad()` 和 `detach()` 有什么区别？
- [ ] 19. 什么时候需要 `retain_graph=True`？
- [ ] 20. 用数值微分（中心差分）求 `f(x)=x³` 在 `x=2` 的导数，和 autograd 对比
- [ ] 21. 为什么 `w.grad` 是累加而不是覆盖？这样设计有什么好处？
- [ ] 22. `AddBackward0` 这个名字怎么来的？

<details>
<summary>全部答案</summary>

11. 梯度是偏导数，元素一一对应，所以同形状
12. `∂loss/∂w = x² = 4`
13. `z` 是非叶子张量（由matmul 计算而来），中间张量不保存梯度，只保存反向函数
14. 缺 `optimizer.zero_grad()`
15. 只给需要优化的参数加；PyTorch 里 `nn.Parameter` 自动带 `requires_grad=True`
16. 翻倍（累加）
17. 恢复正常值
18. `no_grad()` 是上下文管理器，管整块代码；`detach()` 返回一个新张量，切断单个张量的计算图
19. 同一个计算图要多次 backward 时（官方第5 章的雅可比积例子）
20. 数值微分 ≈ 12.000000，autograd = 12.0。前者是猜，后者是链式法则推导
21. 为了支持多次 backward 累加梯度（比如雅可比积），也方便梯度累积做大 batch
22. 算子名+ `Backward` + 实例序号

</details>

---

## 第 3 组 · 构建模型（9 题）

**对应**：[第 4 章 · 构建模型](/guides/pytorch/part2-tutorial/04-build-model)

- [ ] 23. 下面这个写法错在哪？为什么模型学不到东西？

```python
class BadNet(nn.Module):
    def forward(self, x):
        self.fc = nn.Linear(784, 10)
        return self.fc(x)
```

- [ ] 24. 输入 `[64,1,28,28]`，经过标准模型输出什么形状？
- [ ] 25. 手算验证 `nn.Linear(3,2)` 的输出
- [ ] 26. 如果把所有 `nn.ReLU()` 删掉，训练结果会怎样？
- [ ] 27. 为什么输出叫 logits 而不是概率？
- [ ] 28. 为什么模型的输出层是 10 而不是 1？
- [ ] 29. `nn.Flatten()` 默认从哪一维开始展平？
- [ ] 30. `nn.Sequential` 和手写 `forward` 逐层调用有什么区别？
- [ ] 31. 为什么参数名是 `linear_relu_stack.0.weight` 这种嵌套形式？

<details>
<summary>全部答案</summary>

23. 层定义在了 `forward` 里，每次调用都新建层，参数丢失且不被注册
24. `torch.Size([64, 10])`
25. `y = W @ x + b`，W 是 `[2,3]`，b 是 `[2]`
26. 掉到接近瞎猜。多个 Linear 叠加在数学上等价于一个 Linear
27. 神经网络中间计算用无约束实数更稳定，Softmax 放训练损失函数内部做
28. 10 个类别，每个类别一个分数
29. dim=1（保留批次维）
30. 功能等价，`Sequential` 更简洁
31. 嵌套结构：Network → Sequential → 第 0 个模块 → weight

</details>

---

## 第 4 组 · 数据与变换（9 题）

**对应**：[第 2 章](/guides/pytorch/part2-tutorial/02-dataset)、[第 3 章](/guides/pytorch/part2-tutorial/03-transforms)

- [ ] 32. 60000 张图、batch_size=64，一个 epoch 有多少个 batch？
- [ ] 33. `next(iter(dl))` 和 `dl` 的区别？
- [ ] 34. 为什么测试集不该`shuffle=True`？
- [ ] 35. 写一个 Dataset，读取文件夹里所有 txt 文件，文件名当标签
- [ ] 36. DataLoader 很慢怎么优化？
- [ ] 37. 为什么 `__init__` 里不要把所有图片读进内存？
- [ ] 38. 为什么必须把像素归一化到 [0,1]？
- [ ] 39. 写出训练集（随机翻转）和测试集（不翻转）的 transform
- [ ] 40. one-hot 编码标签 3（10 类）是什么形状？为什么 PyTorch 官方不建议真的这么做？

<details>
<summary>全部答案</summary>

32. 938 个（`len(DataLoader(ds, batch_size=64))`）
33. 前者取第一批（64 个样本），后者只是赋值，不读数据
34. 要保证评估可复现，且测试时不该打乱顺序
35. 见 `exercises.py` 的 `ex17_custom_txt_dataset`
36. `num_workers=4`（Windows/macOS 试 2）+ GPU 时 `pin_memory=True`；检查 `__getitem__` 里有无重活
37. 懒加载原则，6 万张图全读会爆内存
38. 输入量级大 255 倍 → 梯度量级暴涨 → 学习率极难调、易震荡
39. 见第 3 章练习 2
40. `torch.Size([10])`。官方建议直接传整数标签 + `CrossEntropyLoss`（内部已处理 softmax + 对数）

</details>

---

## 加分题（做完上面再做）

- [ ] A. 把学习率从 1e-3 改成 1.0 / 1e-6，各跑 2 轮，对比现象
- [ ] B. 故意删掉 `optimizer.zero_grad()`，观察 loss 变成什么
- [ ] C. `epochs` 改成 30，找出准确率从哪一轮开始不再上涨（过拟合）
- [ ] A. 加 `StepLR` 学习率调度器，对比固定学习率
- [ ] E. 把 `CrossEntropyLoss` 换成 `MSELoss`，观察报错信息并解释原因
- [ ] F. 保存「验证集上最好的模型」而不是「最后一个模型」
- [ ] G. 把模型换成两层隐藏层（512→1024→512），看参数量和准确率变化

---

**下一步** → [速查表](/guides/pytorch/part3-practice/02-cheatsheet)
