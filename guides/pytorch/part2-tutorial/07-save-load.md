---
title: 保存与加载模型
description: 把训练成果存下来：state_dict 是什么、为什么推理前必须 model.eval()。
---

> 官方原文：https://docs.pytorch.ac.cn/tutorials/beginner/basics/saveloadrun_tutorial.html

---

## 导读：为什么要单独一章

训练一次要花几分钟到几小时。**训完之后如果模型没法存下来，一切白干。**

这一章讲两件事：

1. 怎么把训练好的参数存到磁盘
2. 怎么加载回来继续用 / 做预测

---

## 核心概念：state_dict

PyTorch 模型的学到的知识，都存在一个叫 **`state_dict`** 的字典里。长这样：

```python
model.state_dict()
```

```
OrderedDict([
  ('linear_relu_stack.0.weight',  tensor([...])),
  ('linear_relu_stack.0.bias',    tensor([...])),
  ('linear_relu_stack.2.weight',  tensor([...])),
  ('linear_relu_stack.2.bias',    tensor([...])),
  ('linear_relu_stack.4.weight',  tensor([...])),
  ('linear_relu_stack.4.bias',    tensor([...])),
])
```

**它只存「数字」，不存「结构」。** 这是理解本章所有内容的关键：

> `state_dict` = 所有参数的「值」
> 模型结构（类定义）= 「形状」

所以加载时必须**先新建一个同样结构的模型**，再把数字填进去。这也是为什么加载的代码长这样：

```python
model = NeuralNetwork()                          # 先造结构
model.load_state_dict(torch.load("model.pth"))   # 再填数字
```

**两个方法对比**：

| 方式 | 代码 | 安全性 | 灵活性 |
|---|---|---|---|
| **只存参数**（推荐） | `torch.save(model.state_dict(), 'p.pth')` | 高 | 好（改结构可以兼容） |
| 存整个模型 | `torch.save(model, 'p.pth')` | 低（用 pickle） | 差（必须能 import 那个类） |

**官方明确推荐第一种。** 第二个是遗留用法，加载时需要 `weights_only=False`，意味着会执行任意代码——如果你从别人手里拿到一个 `.pth` 文件，这等于直接跑别人的代码。

---

## 官方原文

### 保存和加载模型权重

PyTorch 模型将学习到的参数存储在名为 `state_dict` 的内部状态字典中。这些参数可以通过 `torch.save` 方法进行持久化。

```python
import torch
import torchvision.models as models

model = models.vgg16(weights='IMAGENET1K_V1')
torch.save(model.state_dict(), 'model_weights.pth')
```

要加载模型权重，您需要先创建相同模型的实例，然后使用 `load_state_dict()` 方法加载参数。

在下面的代码中，我们设置 `weights_only=True`，以将反序列化期间执行的函数限制为仅加载权重所需的函数。**在加载权重时，使用 `weights_only=True` 被视为最佳实践。**

```python
model = models.vgg16()  # 不指定 weights，即创建未训练模型
model.load_state_dict(torch.load('model_weights.pth', weights_only=True))
model.eval()
```

请务必在进行推理之前调用 `model.eval()` 方法，以将 dropout 和批归一化（batch normalization）层设置为评估模式。否则，将导致推理结果不一致。

### 保存和加载带结构的模型

在加载模型权重时，我们首先需要实例化模型类，因为该类定义了网络的结构。我们可能希望将该类的结构与模型保存在一起，在这种情况下，我们可以将 `model`（而不是 `model.state_dict()`）传递给保存函数。

```python
torch.save(model, 'model.pth')
```

然后，我们可以像下面演示的方式加载：

```python
model = torch.load('model.pth', weights_only=False)
```

此方法在序列化模型时使用 Python 的 `pickle` 模块，因此在加载模型时依赖于实际可用的类定义。

> ⚠️ 因为用了 `weights_only=False`，**加载不可信来源的 .pth 文件等同于运行陌生代码**。这在 PyTorch 官方文档里是被反复强调的安全风险。

---

## 在你自己的 FashionMNIST 模型上试试

官方用 VGG16 做例子（因为要下载预训练模型），但你自己的模型用法完全一样：

```python
import torch

# ---- 保存 ----
torch.save(model.state_dict(), "model.pth")
print("Saved!")

# ---- 加载：新建结构 ----
model = NeuralNetwork()
model.load_state_dict(torch.load("model.pth", weights_only=True))
model.eval()

# ---- 做预测 ----
classes = ["T-shirt/top","Trouser","Pullover","Dress","Coat",
           "Sandal","Shirt","Sneaker","Bag","Ankle boot"]

x, y = test_data[0][0], test_data[0][1]
with torch.no_grad():
    pred = model(x)
    predicted, actual = classes[pred[0].argmax(0)], classes[y]
print(f'Predicted: "{predicted}", Actual: "{actual}"')
```

```
Predicted: "Ankle boot", Actual: "Ankle boot"
```

---

## `model.eval()` 到底做了什么

**它只改一个内部标志位，不改变任何参数。**

- `model.train()` → True（默认）
- `model.eval()` → False

模型里每个层都可以定义「我在训练时该怎么做，在评估时该怎么做」：

| 层 | `train()` 模式 | `eval()` 模式 |
|---|---|---|
| Dropout | 随机丢掉一部分神经元 | **全部保留** |
| BatchNorm | 用当前 batch 的均值方差 | **用训练时积累的滑动均值方差** |

本教程的模型没有 dropout / batchnorm，所以调不调都一样。但**测试真实模型时忘了 `model.eval()`，评估结果会有随机波动**，是常见的低级错误。

---

## 实际项目里的最佳实践

只存 `state_dict` 是不够的——真实项目里你通常需要把**训练配置**一起存下来：

```python
# 保存
torch.save({
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "epoch": epoch,
    "best_acc": best_acc,
    "model_config": {"hidden": 512, "num_classes": 10},  # 结构参数
}, "checkpoint.pth")

# 加载
ckpt = torch.load("checkpoint.pth", weights_only=False)
model = NeuralNetwork()                       # 结构由 model_config 重建
model.load_state_dict(ckpt["model_state_dict"])
optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)
optimizer.load_state_dict(ckpt["optimizer_state_dict"])   # 关键：还要恢复优化器
start_epoch = ckpt["epoch"] + 1
```

**为什么必须存优化器状态？** 因为 Adam/SGD 优化器内部也维护状态（比如 momentum 累积的动量）。不恢复的话，训练虽然能继续，但收敛行为会跟不中断时不一样。

---

## 动手练习

**练习 1** — 为什么加载模型前必须先 `model = NeuralNetwork()`？

<details>
<summary>答案</summary>

因为 `state_dict` 只存数字，不存结构。`load_state_dict()` 是「把数字按名字填进已有结构」，如果模型结构不存在（或者参数名字对不上），就会报 `RuntimeError: Error(s) in loading state_dict`。

它是「填坑」，不是「造坑」。
</details>

**练习 2** — 试着改一下模型结构（比如把 `nn.Linear(512, 512)` 改成 `nn.Linear(256, 256)`），再加载原来的存档，会发生什么？

<details>
<summary>答案</summary>

会报错。因为 key `linear_relu_stack.2.weight` 对应的形状从 `[512,512]` 变成了 `[256,256]`，和存档里的 `[512,512]` 不一致。

报错信息类似：
```
RuntimeError: Error(s) in loading state_dict for NeuralNetwork:
size mismatch for linear_relu_stack.2.weight: copying a param with shape
torch.Size([512, 512]) from checkpoint, the shape in current model is torch.Size([256, 256]).
```

**这也说明了为什么推荐只存 state_dict**：结构改了还能改回来（做微调时常需要）。
</details>

**练习 3** — 用 `torch.save(model, 'whole.pth')` 存整个模型，然后在新脚本里加载。需要先定义 `NeuralNetwork` 这个类吗？

<details>
<summary>答案</summary>

需要。pickle 会记录「这个对象属于哪个类、在哪个模块里」，加载时必须能 import 到那个类。如果在另一个脚本里直接加载而没定义类，会报 `AttributeError: Can't get attribute 'NeuralNetwork'`。

**这就是存整个模型的最大麻烦**——模型代码成了运行时的硬依赖。这也是官方推荐只存 state_dict 的原因。
</details>

**练习 4** — `model.eval()` 会修改模型的参数吗？

<details>
<summary>答案</summary>

不会。它只设置一个 `training` 标志位。参数一点都没变。

验证：
```python
before = model.state_dict()["linear_relu_stack.0.bias"].clone()
model.eval()
after = model.state_dict()["linear_relu_stack.0.bias"]
print(torch.equal(before, after))   # True
```
</details>

**练习 5** — 实现「保存最好的模型」：

```python
best_acc = 0.0
# 在测试循环之后
if correct > best_acc:
    best_acc = correct
    torch.save(model.state_dict(), "best_model.pth")
    print(f"New best! {100*correct:.1f}%")
```

<details>
<summary>答案</summary>

上面就是完整答案。这是实际训练里最常用的模式——**不要保存最后一个模型，要保存验证集上最好的那个**，因为最后一个可能已经过拟合了。
</details>

---

**下一步** → [第 8 章：快速入门（全文压缩版）](/guides/pytorch/part2-tutorial/08-quickstart)
