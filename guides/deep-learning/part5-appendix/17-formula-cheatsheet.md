---
title: 公式速查表
description: 所有关键公式一页汇总。适合复习和面试前速记。
---

# 公式速查表

所有关键公式一页汇总。适合复习和面试前速记。

---

## 优化

### 梯度下降

$$\theta_{t+1} = \theta_t - \eta \nabla_\theta L$$

### SGD with Momentum

$$v_t = \beta v_{t-1} + g_t, \qquad \theta_t = \theta_{t-1} - \eta v_t$$

展开：$v_t = g_t + \beta g_{t-1} + \beta^2 g_{t-2} + \cdots$（指数加权平均）

### RMSProp

$$s_t = \beta s_{t-1} + (1-\beta)g_t^2, \qquad \theta_t = \theta_{t-1} - \frac{\eta}{\sqrt{s_t}+\epsilon}g_t$$

### Adam

$$\begin{aligned} m_t &= \beta_1 m_{t-1} + (1-\beta_1)g_t \\ v_t &= \beta_2 v_{t-1} + (1-\beta_2)g_t^2 \\ \hat{m}_t &= m_t / (1-\beta_1^t) \\ \hat{v}_t &= v_t / (1-\beta_2^t) \\ \theta_t &= \theta_{t-1} - \eta\frac{\hat{m}_t}{\sqrt{\hat{v}_t}+\epsilon} \end{aligned}$$

### AdamW（解耦 weight decay）

$$\theta_t = \theta_{t-1} - \eta\frac{\hat{m}_t}{\sqrt{\hat{v}_t}+\epsilon} - \eta\lambda\theta_{t-1}$$

**LLM 标准超参**：$\text{lr}=1\text{e-}4 \sim 3\text{e-}4$，$\beta_2=0.95$，$\text{wd}=0.1$，clip=1.0，warmup 2000 步 + cosine decay

---

## 正则化

### L2 / weight decay

$$\theta \leftarrow (1-\eta\lambda)\theta - \eta\frac{\partial L}{\partial\theta}$$

**bias 和 1 维参数（BN/LN 的 $\gamma,\beta$）不做衰减**。

### L1

$$\tilde{L} = L + \lambda\sum_j|\theta_j|$$

**产生稀疏性**（不可导点在 0）。

### Dropout

训练时以概率 $p$ 置零，**并除以 $1-p$**；推理时不丢弃。

---

## 反向传播

### 三条基本规则

| 运算 | 梯度 |
|---|---|
| $z = a + b$ | $\partial L/\partial a = \partial L/\partial z$ |
| $z = ab$ | $\partial L/\partial a = (\partial L/\partial z)b$ |
| $z = a^\top W$ | $\partial L/\partial a = W(\partial L/\partial z)^\top$，$\partial L/\partial W = a(\partial L/\partial z)^\top$ |

### 梯度消失/爆炸的量级

$$\frac{\partial L}{\partial x_1} \propto \prod_{l=1}^{L} \frac{1}{\sqrt{n}} = n^{-L/2}$$

sigmoid：$\sigma'(z) \le 0.25$，每层乘 0.25

---

## 初始化

| 方法 | $\sigma_w^2$ | 适用 |
|---|---|---|
| Xavier (Glorot) | $\frac{2}{n_{in}+n_{out}}$ | tanh / sigmoid |
| **He (Kaiming)** | $\frac{2}{n_{in}}$ | **ReLU / GELU** |
| LLaMA | $N(0, 0.02^2)$ | 配合 RMSNorm |

---

## 归一化

### BatchNorm

$$\hat{x} = \frac{x - \mu_B}{\sqrt{\sigma_B^2 + \epsilon}}, \qquad y = \gamma\hat{x} + \beta$$

**统计维度**：batch + 空间 → 训练/推理行为不同

### LayerNorm

$$\hat{x} = \frac{x - \mu}{\sqrt{\sigma^2+\epsilon}}$$

**统计维度**：特征 → 与 batch 无关

### RMSNorm

$$\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_j x_j^2 + \epsilon}} \odot \gamma$$

**省掉减均值**，只有 $\gamma$。

---

## CNN

### 卷积参数量

$$\text{params} = k \times k \times C_{in} \times C_{out} + C_{out}$$

### 感受野

$$r_l = r_{l-1} + (k_l - 1)\prod_{i=1}^{l-1}s_i, \qquad j_l = j_{l-1} + (k_l - 1)\prod_{i=1}^{l-1}s_i$$

stride=1 简化：$r_l = 1 + \sum_{i=1}^{l}(k_i - 1)$

### 空洞卷积

$$\text{有效感受野} = k + (k-1)(d-1), \quad \text{需padding} = d$$

---

## ResNet

### 残差连接

$$y = F(x) + x, \qquad \frac{\partial y}{\partial x} = \frac{\partial F}{\partial x} + I$$

梯度连乘展开：

$$\prod_{l=1}^{L}(I + J_l) = I + \sum J_l + \sum_{l<k} J_lJ_k + \cdots$$

**展开后第一项是 $I$**，所以梯度不衰减。

---

## Attention

### Scaled Dot-Product Attention

$$\text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}} + M\right)V$$

**为什么除 $\sqrt{d_k}$**：点积方差 $\text{Var}[q\cdot k] = d_k$，std $=\sqrt{d_k}$。不缩放会让 softmax 饱和（实测 $d_k=64$ 时 max_p = 0.9990，缩放后 0.0350）。

**形状流转**：`[n, d_k] × [d_k, m] → [n, m] → @ [m, d_v] → [n, d_v]`

### 多头

$$\text{MultiHead}(Q,K,V) = \text{Concat}(\text{head}_1,\ldots,\text{head}_h)W^O$$

**参数量和单头相同**：$4d_{model}^2$

---

## RoPE

$$\theta_i = \text{base}^{-2i/d}, \qquad R_m q = \begin{pmatrix}\cos m\theta & -\sin m\theta \\ \sin m\theta & \cos m\theta\end{pmatrix}q$$

核心性质：

$$\langle R_m q, R_n k\rangle = \langle q, R_{n-m}k\rangle = f(q,k,n-m)$$

**内积只依赖相对位置。** base=10000（几何频率）。

---

## 现代 LLM 组件

### SwiGLU

$$\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_3), \qquad \text{SiLU}(x) = x\sigma(x)$$

**三个矩阵**，中间维度取 $\frac{8}{3}d$ 以保持参数量。

### GQA

```
MHA:  Q=[h,d]  K=[h,d]  V=[h,d]
GQA:  Q=[h,d]  K=[g,d]  V=[g,d]   ★ h/g = 4~8 最优
MQA:  Q=[h,d]  K=[1,d]  V=[1,d]
```

### KV Cache

$$\text{KV cache} = 2 \times n_{kv} \times L \times d_{head} \times n_{layers} \times \text{bytes}$$

LLaMA-7B, L=4096, batch=2, fp16：

| 类型 | KV cache |
|---|---|
| MHA（32） | 2.15 GB |
| GQA（8） | 0.54 GB |
| MQA（1） | 0.07 GB |

---

## 缩放定律

$$\text{Kaplan:}\quad L(N) = \left(\frac{N_c}{N}\right)^{\alpha_N}, \quad \alpha_N \approx 0.076$$

$$\text{Chinchilla:}\quad N_{opt} \propto C^{0.55}, \quad D_{opt} \propto C^{0.45}$$

**Token/参数比最优 ≈ 20**（但实践上为推理效率会超过这个值）。

---

## 损失函数

| 损失 | 来源假设 | 公式 | 任务 |
|---|---|---|---|
| MSE | 高斯 | $\frac{1}{N}\sum(y-\hat{y})^2$ | 回归 |
| MAE | 拉普拉斯 | $\frac{1}{N}\sum|y-\hat{y}|$ | 抗 outlier 回归 |
| CrossEntropy | 类别 | $-\log \hat{p}_y$ | 多分类 |
| BCE | 伯努利 | 交叉熵（二分类） | 二分类 |
| NLL | — | $-\sum\log p$ | 配合 LogSoftmax |
| InfoNCE | 对比 | $-\log\frac{e^{sim(i,i)}}{\sum_j e^{sim(i,j)}}$ | 对比学习 |

**关键**：CrossEntropyLoss / BCEWithLogitsLoss 接受 **logits**，不是概率。

---

## 统计

### 偏差-方差分解

$$\mathbb{E}[(y - \hat{y})^2] = \text{Bias}^2 + \text{Var} + \sigma^2$$

### 标准误与置信区间

$$\text{SE} = \sqrt{\frac{p(1-p)}{n}}, \qquad 95\%\text{CI} = p \pm 1.96\,\text{SE}$$

### 泛化差距

$$\text{gap} = \text{train\_loss} - \text{val\_loss} \quad (\text{或 train\_acc} - \text{val\_acc})$$

---

## 数值稳定

### Loss Scaling

$$\text{实际梯度} = S \cdot \text{真实梯度}$$

**bf16 不需要**（指数位与 fp32 相同，动态范围 $10^{\pm38}$）。

### 梯度裁剪

$$\hat{g} = g\cdot\frac{\text{max\_norm}}{\|g\|} \quad \text{当 } \|g\| > \text{max\_norm}$$

**等比缩放**（不是逐元素裁剪，后者改变梯度方向）。

---

## 数值速查

| 概念 | 数值 |
|---|---|
| LLaMA-7B 参数量 | 6.7B（transformer 部分 5.37B） |
| LLaMA-7B 隐藏维度 | 4096 |
| LLaMA-7B 头数 / $d_k$ | 32 / 128 |
| ResNet-50 参数量 | 25.6M |
| FashionMNIST 模型参数量 | 669,706 |
| 输入 224² 全连接 vs 卷积 | 4.83e11 vs 1792（2.7亿倍） |
