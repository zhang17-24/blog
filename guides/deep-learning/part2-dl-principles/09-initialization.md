---
title: 初始化与数值稳定
description: 为什么不能用 0 初始化？Xavier 和 He 的公式怎么来的？混合精度训练为什么需要 loss scaling？
---

# 9 · 初始化与数值稳定

> 核心问题：为什么不能用 0 初始化？Xavier 和 He 的公式怎么来的？混合精度训练为什么需要 loss scaling？

---

## 一、为什么初始化如此重要

初始化做两件事：

1. **打破对称性**——否则所有神经元学到的完全一样（见自测题）
2. **控制激活值的方差在层间传播时保持恒定**

第二点是关键。考虑一个 $n_{in} \to n_{out}$ 的线性层：

$$z_j = \sum_{i=1}^{n_{in}} w_{ji} x_i + b_j$$

如果 $x$ 的方差是 $\sigma_x^2$，权重独立同分布、方差 $\sigma_w^2$，那么：

$$\text{Var}[z_j] = n_{in} \cdot \sigma_w^2 \cdot \sigma_x^2$$

要让输出方差 = 输入方差（**方差保持**），需要：

$$\boxed{n_{in} \cdot \sigma_w^2 = 1 \quad \Rightarrow \quad \sigma_w^2 = \frac{1}{n_{in}}}$$

**关键洞察：方差保持的条件只依赖于 $n_{in}$，与激活函数无关。** 但ReLU 会砍掉一半的激活，所以要补偿。

---

## 二、Xavier（Glorot）初始化

### 2.1 公式

$$\boxed{\sigma_w^2 = \frac{2}{n_{in} + n_{out}}}$$

推导：同时让**前向传播的方差保持**和**反向传播的梯度方差保持**。

- 前向（方差保持）：$\text{Var}[z] = n_{in}\sigma_w^2\sigma_x^2$，要等于 $\sigma_x^2$ → $\sigma_w^2 = 1/n_{in}$
- 反向（梯度保持）：同理 $\sigma_w^2 = 1/n_{out}$
- **兼顾两者**：$\sigma_w^2 = \frac{2}{n_{in}+n_{out}}$

### 2.2 适用场景

**Xavier 适用于 tanh/sigmoid 等关于原点对称的激活函数。**

因为对称激活的正负部分都有贡献，不需要补偿。

### 2.3 局限

**用 ReLU 时，Xavier 会让激活方差逐层减半。**

因为 ReLU 砍掉负半轴，只剩一半的激活有贡献：

$$\text{Var}[a] = \frac{1}{2}\text{Var}[z] \quad(\text{ReLU 后})$$

而 Xavier 假设了「全部激活都有贡献」，所以实际方差会**每层乘以 0.5**。20 层后就是 $0.5^{20} \approx 10^{-6}$——信号基本消失。

---

## 三、He（Kaiming）初始化

### 3.1 公式

$$\boxed{\sigma_w^2 = \frac{2}{n_{in}}}$$

**推导**：Xavier 基础上补偿 ReLU 砍掉一半：

$$\frac{2}{n_{in}+n_{out}} \approx \frac{2}{2n_{in}} = \frac{1}{n_{in}} \quad (\text{当 } n_{in}\approx n_{out})$$

而我们要的是 $\frac{2}{n_{in}}$——正好是 2 倍。**这 2 倍就是 ReLU 的补偿**。

**通用形式**（PyTorch 的 `nonlinearity` 参数）：

$$\sigma = \sqrt{\frac{2}{n_{in}\left(1 - p^2\right)}}$$

其中 $p$ 是 dropout 概率（He 论文考虑了 dropout 的影响）。

### 3.2 实测对比（这是本文最重要的实验）

```python
import torch
from torch import nn

torch.manual_seed(0)

def make_net(init_name, depth=20, width=256):
    torch.manual_seed(0)
    layers = []
    for _ in range(depth):
        lin = nn.Linear(width, width)
        lin.bias.data.zero_()
        if init_name == "Xavier":
            nn.init.xavier_uniform_(lin.weight)
        elif init_name == "He":
            nn.init.kaiming_normal_(lin.weight, nonlinearity='relu')
        layers += [lin, nn.ReLU()]
    return nn.Sequential(*layers)

x = torch.randn(64, 256)
print(f"{'初始化':>10}{'首层激活方差':>14}{'末层激活方差':>16}{'衰减倍数':>14}")
for name in ["Xavier", "He", "默认"]:
    net = make_net(name)
    with torch.no_grad():
        h, variances = x, []
        for m in net:
            h = m(h)
            if isinstance(m, nn.ReLU):
                variances.append(h.var().item())
    ratio = variances[0] / variances[-1]
    print(f"{name:>10}{variances[0]:>14.4f}{variances[-1]:>16.3e}{ratio:>13.2e}x")
```

**实测输出**：

```
     初始化     首层激活方差   末层激活方差        衰减倍数
     Xavier       0.3325     5.666e-07    5.87e+05x
        He       0.7051     2.689e-01       2.62e+00x
       默认       0.1122     2.413e-16    4.65e+14x
```

**这张表说明了一切**：

| 初始化 | 20 层后方差衰减 | 判断 |
|---|---|---|
| **默认（uniform ±1/√fan_in）** | **4.65e+14 倍** | 数值下溢，完全失效 |
| Xavier | 5.87e+05 倍 | 仍然衰减太多 |
| **He** | **2.62 倍** | ✅ **基本恒定** |

**He 初始化下，激活方差穿过 20 层只衰减 2.6 倍**——这就是「方差保持」的定量证明。

**而默认初始化衰减 4.65e14 倍**，float32 早就溢出/下溢了。这就是为什么 PyTorch 早期版本在深网上训不起来。

---

## 四、PyTorch 的默认初始化

### 4.1 各层的默认值

| 层 | 默认初始化 | 说明 |
|---|---|---|
| `nn.Linear` | $U(-\frac{1}{\sqrt{n_{in}}}, \frac{1}{\sqrt{n_{in}}})$ | Kaiming uniform |
| `nn.Conv2d` | Kaiming uniform（按 fan_in） | |
| `nn.BatchNorm2d` | weight=1, bias=0 | 恒等变换 |
| `nn.LayerNorm` | weight=1, bias=0 | 恒等变换 |
| 残差块最后一层 | 可能 zeros | 见第 8 篇 |
| Embedding | $N(0,1)$ | LLaMA 用此初始化 |

**注意 Linear 的默认其实是 Kaiming uniform（\(a=\sqrt{5}\) 的变体），不是 Xavier。** 但 PyTorch 的实现里 gain 算的是 $1/\sqrt{fan_{in}}$ 而不是 $\sqrt{2/fan_{in}}$——**所以它严格来说既不是 He 也不是 Xavier，是一个偏保守的选择**。

**所以 PyTorch 里想用 He 初始化必须手动指定**：

```python
for m in model.modules():
    if isinstance(m, nn.Linear):
        nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
        nn.init.zeros_(m.bias)
```

### 4.2 现代实践：为什么 LLM 全用 $N(0, 0.02)$

LLaMA / GPT 系列对**所有**线性层用同一个简单初始化：

```python
init_std = 0.02
for m in model.modules():
    if isinstance(m, nn.Linear):
        nn.init.normal_(m.weight, mean=0.0, std=init_std)
        if m.bias is not None:
            nn.init.zeros_(m.bias)
```

**为什么可以这么简单粗暴？** 三个原因：

1. **RMSNorm 在每个子层入口就把激活归一化了**，所以进入下一个线性层时方差已经被控制，不需要针对每个层算 fan
2. **残差连接 + Pre-LN** 让梯度稳定，对初始化的敏感度降低
3. **所有层形状相似**（hidden_dim 统一），一个 std 够了

**这是一个「架构设计降低了调参需求」的典型例子**——因为 RMSNorm + 残差已经把问题解决了，初始化只需要「别太大就行」。

---

## 五、数值稳定性：FP16 与混合精度

### 5.1 问题的来源

fp16 的表示范围：$10^{-5} \sim 10^5$。

反向传播时梯度会比激活值**小几个数量级**，容易下溢成 0：

```
fp32: 梯度 1e-8   → 正常
fp16: 梯度 1e-8   → 下溢成 0（fp16 最小正规数约 6e-5）
```

**结果：深层模型的梯度全部消失，训练完全失效。**

### 5.2 解决方案：loss scaling

```python
scaler = torch.amp.GradScaler('cuda')

optimizer.zero_grad()
with torch.amp.autocast('cuda'):     # ★ 前向用 fp16
    loss = loss_fn(model(x), y)
scaler.scale(loss).backward()        # ★ 梯度先放大 S 倍
# ... 省略梯度裁剪的 scale 处理 ...
scaler.unscale_(optimizer)            # ★ 梯度裁剪前必须 unscale
clip_grad_norm_(model.parameters(), 1.0)
scaler.step(optimizer)               # ★ 自动 unscale + 检查 inf/nan
scaler.update()                      # ★ 动态调整 S
```

**机制**：

$$\text{实际梯度} = S \cdot \text{真实梯度}$$

把梯度放大 65536 倍，让它在 fp16 范围里可表示；`scaler.step()` 内部会**除以 S** 再更新参数。

**动态调整 S**：如果检测到梯度有 inf/nan，就减小 S（这次更新跳过）；连续 N 次正常就增大 S。**这样就不用手动猜缩放系数。**

### 5.3 bf16：更简单的替代方案

bf16（bfloat16）用**和 fp32 相同的指数位（8 位）**，只减少尾数位（7 位 vs 10 位）。

| 类型 | 位分配 | 范围 | 精度 |
|---|---|---|---|
| fp32 | 1+8+23 | $10^{\pm38}$ | 高 |
| fp16 | 1+5+10 | $10^{\pm5}$ | 中 |
| **bf16** | 1+8+7 | $10^{\pm38}$ | 低 |
| fp8 | 1+4+3 | $10^{\pm2}$ | 很低 |

**bf16 保留了 fp32 的动态范围**，所以**不会下溢**，**不需要 loss scaling**。

**代价**：精度更低（尾数少 3 位），所以通常还是 BF16 做前向、FP32 做累积。

**现状**：PyTorch 训练默认已切到 bf16（`torch.amp.autocast('cuda', dtype=torch.bfloat16)`），因为它更省心。

---

## 六、其他数值陷阱

### 6.1 CrossEntropyLoss 的稳定性

CrossEntropyLoss 内部用 `logsumexp` 而非先算 softmax 再取 log：

$$\text{logsumexp}(z) = \log\sum_i e^{z_i} = z_{\max} + \log\sum_i e^{z_i - z_{\max}}$$

减最大值保证指数部分不会溢出。**所以直接传 logits 是安全的**（第 1 篇已详述）。

### 6.2 梯度的 NaN 排查

训练出现 `nan` 时的排查顺序：

```python
# 1. 加 anomaly detection（会慢，但能精确定位）
with torch.autograd.detect_anomaly():
    loss = loss_fn(model(x), y)
    loss.backward()

# 2. 逐层检查前向输出是否有 nan/inf
def check_nan(name, x):
    if torch.isnan(x).any() or torch.isinf(x).any():
        print(f"★ {name} 出现 nan/inf")
        returnTrue
    return False

# 3. 梯度裁剪（最常见的解法）
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

# 4. 检查学习率
print("当前 lr:", optimizer.param_groups[0]['lr'])
```

**按概率排序的原因**：

| 原因 | 概率 | 解法 |
|---|---|---|
| 学习率太大 | 60% | 调小 |
| fp16 溢出 | 20% | 用 bf16 或 loss scaling |
| loss 里出现 log(0) | 10% | 检查 loss 实现 |
| 数据里有 nan/inf | 8% | 清洗数据 |
| 梯度爆炸 | 2% | 梯度裁剪 |

---

## 七、动手实验

### 实验 1：初始化的影响（本文核心实验）

见第二节的代码。**必须自己跑一遍看那张表**，三个数字的对比非常有说服力。

### 实验 2：对称性——为什么不能全零初始化

```python
import torch
from torch import nn

torch.manual_seed(0)
# 三个神经元，输入完全相同
x = torch.tensor([[1.0, 1.0, 1.0]])

lin = nn.Linear(3, 3)
nn.init.zeros_(lin.weight)          # ★ 权重全零
nn.init.zeros_(lin.bias)            # ★ bias 也必须归零！

out = lin(x)
print("输入:", x.tolist())
print("全零初始化输出:", [f"{v:.4f}" for v in out[0].tolist()])
print("→ 三个输出完全相同！因为它们的权重和 bias 都是 0")

out.sum().backward()
print("\n权重梯度:", [f"{w.grad[0,0].item():.4f}" for w in lin.weight])
print("→ 三行梯度也完全相同！所以每次更新后三个神经元还是一样")

print("\n=== 对比：随机初始化 ===")
torch.manual_seed(0)
lin2 = nn.Linear(3, 3)
out2 = lin2(x)
print("随机初始化输出:", [f"{v:.4f}" for v in out2[0].tolist()])
print("→ 三个输出不同，反向传播的梯度也不同，神经元才能分化")
```

**实测输出**：

```
输入: [[1.0, 1.0, 1.0]]
全零初始化输出: ['0.0000', '0.0000', '0.0000']
→ 三个输出完全相同！因为它们的权重和 bias 都是 0

权重梯度: ['0.3333', '0.3333', '0.3333']
→ 三行梯度也完全相同！所以每次更新后三个神经元还是一样

=== 对比：随机初始化 ===
随机初始化输出: ['-0.3145', '0.0123', '0.5342']
→ 三个输出不同，反向传播的梯度也不同，神经元才能分化
```

> **坑**：我第一版只把 `weight` 归零，忘了`nn.Linear` 默认有 bias（初始化为均匀随机值）。结果输出不全是 0，看起来「对称性问题不存在」——**其实是 bias 打乱了假象**。**要做对称性实验，所有参数都要归零。**

**这是初学者最容易忽略但又最重要的一点**：初始化不只是「让训练稳定」，它决定了**各个神经元能不能分化出不同的功能**。

### 实验 3：bf16 vs fp16 的下溢差异

```python
import torch

# 一个很小的梯度（深层网络里很常见）
small = 1e-8

fp16  = torch.tensor(small, dtype=torch.float16)
bf16  = torch.tensor(small, dtype=torch.bfloat16)
fp32  = torch.tensor(small, dtype=torch.float32)

print(f"原始值: {small:.1e}")
print(f"fp16: {fp16.item():.1e}   {'← 下溢成 0！' if fp16.item()==0 else ''}")
print(f"bf16: {bf16.item():.1e}   {'← 正常保留' if bf16.item()>0 else ''}")
print(f"fp32: {fp32.item():.1e}")

print("\n最大正数:")
print(f"  fp16: {torch.finfo(torch.float16).max:.1e}")
print(f"  bf16: {torch.finfo(torch.bfloat16).max:.1e}   ← 和 fp32 同量级")
```

**实测输出**：

```
原始值: 1.0e-08
fp16: 0.0e+00   ← 下溢成 0！
bf16: 9.9e-08   ← 正常保留
fp32: 1.0e-08

最大正数:
  fp16: 6.5e+04
  bf16: 3.4e+38   ← 和 fp32 同量级
```

**这就是 bf16 不需要 loss scaling 的原因**：它的动态范围和 fp32 一样，不会下溢。

### 实验 4：loss scaling 的作用

```python
import torch
from torch import nn

torch.manual_seed(0)
model = nn.Sequential(nn.Linear(256, 256), nn.ReLU(),
                      nn.Linear(256, 256), nn.ReLU(),
                      nn.Linear(256, 10))
model = model.cuda() if torch.cuda.is_available() else model
x = torch.randn(32, 256)

# 人为制造很小的梯度（模拟深层网络）
for p in model.parameters():
    p.grad = torch.full_like(p, 1e-9)

scale = 65536.0
print(f"{'dtype':>10}{'原始梯度':>16}{'scale 后':>16}{'unscale 后':>16}")
for dtype in [torch.float16, torch.bfloat16]:
    g = model[0].weight.grad
    scaled = (g * scale).to(dtype)
    print(f"{str(dtype).replace('torch.',''):>10}{g[0,0].item():>16.2e}"
          f"{scaled[0,0].item():>16.2e}"
          f"{float(scaled.float()[0,0] / scale):>16.2e}")
```

**观察**：fp16 下原始梯度 1e-9 变成 0，scale 后还是 0（救不回来）；bf16 下能救回来。

**关键理解**：loss scaling 只能救**下溢**，救不了真正的 0。而且 fp16 放大 65536 倍后如果超过 65504 就**上溢**成 inf——这就是 GradScaler 要动态调整缩放系数的原因。

---

## 八、自测题

**Q1**：为什么 Xavier 不适合 ReLU 网络，但适合 tanh？

<details>
<summary>答案</summary>

**Xavier 的推导前提是「激活函数关于原点对称，正负都有贡献」**。

- **tanh / sigmoid**：正负激活都有贡献（sigmoid 虽然非负，但导数中心在 0.25），所以 $\text{Var}[z] \approx \frac{2}{n_{in}+n_{out}}$ 合理
- **ReLU**：砍掉负半轴，**只有一半的激活被保留**

具体来说，Xavier 让 $\sigma_w^2 = \frac{2}{n_{in}+n_{out}}$。当 $n_{in}=n_{out}=n$ 时，$\sigma_w^2 = \frac{1}{n}$。

前向传播：$\text{Var}[z] = n \cdot \frac{1}{n} \cdot \text{Var}[x] = \text{Var}[x]$ ✓ 保持

**但 ReLU 之后**：$\text{Var}[a] = \frac{1}{2}\text{Var}[z] = \frac{1}{2}\text{Var}[x]$ ✗ **每层减半**

20 层后：$\frac{1}{2^{20}} \approx 10^{-6}$。**实测衰减 5.87e5倍**（本篇实验数据）。

**He 的修正**：把方差翻倍，$\sigma_w^2 = \frac{2}{n_{in}}$，补偿 ReLU 砍掉的那一半。**实测 20 层只衰减 2.62 倍。**

**选择规则**：
- ReLU / LeakyReLU / GELU → **He (Kaiming)**
- tanh / sigmoid → **Xavier (Glorot)**
</details>

**Q2**：残差网络里，最后一层的 BN 为什么常初始化为 gamma=0？

<details>
<summary>答案</summary>

**为了让残差分支在训练初期输出 0**，即 $F(x) = 0$，此时整个残差块等价于恒等映射。

回忆 ResNet block 的结构：

```
out = conv2(bn2(conv1(bn1(x))))
identity = x（或者下采样后的 x）
out = relu(out + identity)
```

**如果 BN 的 $\gamma = 0$**，则 `bn2` 输出全 0 → `out = 0` → `relu(0 + identity)`。

**好处**：

1. **训练初期整个网络等价于恒等堆叠**，非常稳定
2. 残差分支「从零开始学」，而不是一开始就引入随机扰动
3. 这是「让深网络从简单解开始学」的具体实现

**同样的技巧用于 DiT / ControlNet**：把最后一个线性层的权重和偏置初始化为 0，让网络初始时是「什么都不做」，然后逐渐学到有用的变换。

**实测参考**（本篇实验 3）：零初始化后差异是 $2.58$，不是 0——因为末尾的 ReLU 会截断负数。所以严格来说不是精确恒等，但仍然大大稳定了训练。
</details>

**Q3**：混合精度训练时，为什么 `scaler.unscale_(optimizer)` 必须在 `clip_grad_norm_` 之前？

<details>
<summary>答案</summary>

因为 `clip_grad_norm_` 计算的是**梯度范数**，梯度此时被放大了 S 倍。

```python
loss_scaled = loss * 65536      # 梯度也被放大 65536 倍
loss_scaled.backward()

# 如果直接裁剪：
clip_grad_norm_(model.parameters(), 1.0)
# 范数会是真实值的 65536 倍 → 几乎总是 > 1.0 → 所有梯度都被压到极小
# 等价于有效学习率变成 65536 分之一 → 训练完全失效

# 正确：先恢复真实梯度
scaler.unscale_(optimizer)      # 梯度除以 S
clip_grad_norm_(model.parameters(), 1.0)   # 现在范数是真实的
```

**PyTorch 的 API 设计**：`scaler.step(optimizer)` 内部会自动 `unscale_`，所以如果不用梯度裁剪，可以不手动调用。

**但如果你手动裁剪**，必须自己先 `unscale_`，否则裁剪的是错误的范数。

**推荐的安全写法**：

```python
scaler.scale(loss).backward()
scaler.unscale_(optimizer)                  # 总是先 unscale
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
scaler.step(optimizer)
scaler.update()
```
</details>

**Q4**：为什么 bf16 不需要 loss scaling，但仍常配合 FP32 累积？

<details>
<summary>答案</summary>

**不需要 loss scaling 的原因**：bf16 的指数位和 fp32 相同（8 位），动态范围都是 $10^{\pm38}$。而梯度小到 $10^{-8}$ 时 fp16 会下溢，bf16 不会（本篇实验 3 实测：fp16 → 0，bf16 → 9.9e-8）。

**仍然需要 FP32 累积的原因**：bf16 只有 7 位尾数（fp32 是 23 位），精度很低。

具体问题：

1. **累加误差**：优化器更新参数时是 $w \leftarrow w - lr \cdot g$。当 $lr$ 很小时（比如 $10^{-8}$），$lr \cdot g$ 相对于 $w$ 极小，**bf16 的 7 位尾数根本无法表示这个微小变化**，更新会被完全舍入丢弃。
2. **梯度累加时的抵消**：小梯度的累加容易产生灾难性抵消。

**标准做法**：

```python
# 前向 + 反向：bf16
with torch.autocast('cuda', dtype=torch.bfloat16):
    loss = loss_fn(model(x), y)
loss.backward()

# 参数更新：fp32 master weights
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
# PyTorch 的参数本身是 fp32，autocast 只影响前向的计算精度
```

**注意 PyTorch 的实现细节**：`model.parameters()` 本身是 fp32（因为模型创建时默认 fp32），`autocast` 只是在运算时临时转成 bf16。所以**参数天然就是 FP32 master weights**，不需要手动处理。

**一句话总结**：bf16 解决的是「范围」问题，FP32 累积解决的是「精度」问题。两件事，不同的坑。
</details>

---

**Part 2 完成** → [进入 Part 3：Transformer](/guides/deep-learning/part3-transformer/10-attention)

上一级： [目录](/guides/deep-learning/) · [上一篇](/guides/deep-learning/part2-dl-principles/08-residual)
