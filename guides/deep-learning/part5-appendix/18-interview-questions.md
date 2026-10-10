---
title: 面试高频问题
description: 算法岗面试会问的 30 个问题，按主题分组，附答案要点。按题目反查对应文档能深入理解。
---

# 面试高频问题

算法岗面试会问的 30 个问题，按主题分组，附答案要点。**按题目反查对应文档能深入理解。**

---

## 一、基础概念（1-6）

**1. 什么是过拟合？怎么判断？怎么解决？**
→ [Part1 第2篇](/guides/deep-learning/part1-ml-basics/02-generalization)

- **判断**：训练指标好但验证指标差；两者差距（泛化差距）大
- **本质**：模型容量 vs 数据量不匹配
- **解决**（按性价比排序）：加数据 > 数据增强 > 正则化 > 减容量
- **陷阱**：验证误差低于训练误差 = 数据泄漏

---

**2. L1 和 L2 正则的区别？为什么 L1 能产生稀疏？**
→ [Part1 第3篇](/guides/deep-learning/part1-ml-basics/03-regularization)

- L2 惩罚 $\lambda\|\theta\|^2$，梯度 $\lambda\theta$ → 参数**按比例**收缩，不会恰好为 0
- L1 惩罚 $\lambda\|\theta\|_1$，不可导点在 0 → 参数被压到**恰好为 0**
- **深层原因**：L1 对应拉普拉斯先验（密度在 0 处有尖峰），L2 对应高斯先验
- **联系**：$w \leftarrow (1-\eta\lambda)w - \eta\nabla L$（L2 = 权重衰减）

---

**3. 为什么 weight decay 不加在 bias 和 LayerNorm 上？**
→ [Part1 第3篇](/guides/deep-learning/part1-ml-basics/03-regularization)

- weight decay 惩罚的是「大权重 = 对输入敏感 = 不平滑」。**bias 的作用是平移决策边界**，对敏感度无贡献
- bias 初始化为 0，持续衰减会让它永远接近 0，等于关闭
- **标准写法**：`if p.ndim <= 1 or name.endswith('.bias'): 不衰减`

---

**4. 交叉熵损失是怎么来的？为什么不用 MSE 做分类？**
→ [Part1 第1篇](/guides/deep-learning/part1-ml-basics/01-what-is-ml)

- **来源**：从「最大化数据似然」推导 → KL 散度 → 负对数似然 → 交叉熵
- **不用 MSE**：MSE 对「概率应该多少」的约束弱（0.9 和 0.99 惩罚差距小），且梯度量级不合理
- **关键**：CrossEntropyLoss 接收 **logits** 不是概率（内部做 softmax + log）

---

**5. 什么是类别不平衡？怎么处理？**
→ [Part1 第2篇](/guides/deep-learning/part1-ml-basics/02-generalization)

- **表现**：训练准确率很高但「全预测多数类」
- **处理**：重采样（过采样少数/欠采样多数）、class weight、focal loss、调整决策阈值
- **诊断**：看混淆矩阵，别只看 accuracy

---

**6. Batch Norm 和 Layer Norm 的区别？为什么 LLM 用后者？**
→ [Part2 第6篇](/guides/deep-learning/part2-dl-principles/06-normalization)

| | BatchNorm | LayerNorm |
|---|---|---|
| 统计维度 | batch + 空间 | 特征 |
| 依赖 batch | **是** | 否 |
| 训练/推理行为 | **不同** | 相同 |

**LLM 用 LN 的三个原因**：batch 小（统计量不可靠）、变长序列（padding 污染）、推理需要确定性。

---

## 二、优化（7-13）

**7. SGD 和 Adam 的区别？AdamW 又改进了什么？**
→ [Part1 第4篇](/guides/deep-learning/part1-ml-basics/04-optimizers)

- SGD：只有 lr，无自适应
- Adam：一阶矩（动量）+ 二阶矩（自适应步长）
- **AdamW：解耦 weight decay**。Adam 里衰减会进入 $m_t, v_t$，被 $\frac{1}{\sqrt{v_t}}$ 缩放，行为不可预测；AdamW 直接 $\theta \leftarrow \theta - \eta\lambda\theta$
- **LLM 为什么全用 AdamW**：大数据下过拟合风险低，AdamW 更稳 + 可解耦其他衰减策略

---

**8. 为什么 Adam 需要偏差修正？**
→ [Part1 第4篇](/guides/deep-learning/part1-ml-basics/04-optimizers)

- $m_0=0$ → 第一步 $m_1 = (1-\beta)g_1 = 0.1g_1$，严重低估
- 修正：除以 $1-\beta^t$（几何级数的归一化因子）
- 效果：第一步的有效步长精确等于名义 lr

---

**9. 为什么 LLM 用 $\beta_2 = 0.95$ 而不是 0.999？**
→ [Part1 第4篇](/guides/deep-learning/part1-ml-basics/04-optimizers)

- $\frac{1}{1-\beta_2}$ = 二阶矩的有效窗口长度
- 0.999 → 1000 步窗口，训练中梯度尺度快速变化时会严重滞后
- 0.95 → 20 步窗口，能跟上当前状态
- **这是 HuggingFace / LLaMA 的默认配置，已成为事实标准**

---

**10. 为什么需要 warmup？**
→ [Part1 第4篇](/guides/deep-learning/part1-ml-basics/04-optimizers)

- 初期梯度方向噪声大，直接用满 lr 会破坏已学到的结构
- Adam 早期 $m_t, v_t$ 估计不准
- **配合 weight decay**：实际衰减率 = $\eta\lambda$，warmup 期间 lr 小 → 衰减也小（这是好事）

---

**11. 梯度裁剪怎么做？为什么不用逐元素裁剪？**
→ [Part2 第5篇](/guides/deep-learning/part2-dl-principles/05-backprop)

- **等比缩放**：`$\hat g = g \cdot \frac{c}{\|g\|}$`，保持梯度**方向不变**
- 逐元素裁剪会改变方向，破坏「沿最陡下降方向」的前提
- LLM 标准配置：`clip_grad_norm_(model.parameters(), 1.0)`

---

**12. 为什么混合精度要用 loss scaling？bf16 呢？**
→ [Part2 第9篇](/guides/deep-learning/part2-dl-principles/09-initialization)

- fp16 范围 $10^{\pm5}$，深层梯度 $10^{-8}$ 会**下溢成 0**
- loss scaling：梯度放大 $S=65536$ 倍，`scaler.step()` 内部除回去，**动态调整 S**（遇 inf/nan 就减小）
- **bf16 指数位与 fp32 相同**（$10^{\pm38}$），不下溢，**不需要 scaling**
- **注意**：用梯度裁剪时必须先 `scaler.unscale_(optimizer)`

---

**13. 学习率怎么调？太大太小分别什么现象？**
→ [Part1 第4篇](/guides/deep-learning/part1-ml-basics/04-optimizers)、[Part1 第6章](/guides/deep-learning/part1-ml-basics/04-optimizers)

| lr 过大 | lr 过小 |
|---|---|
| loss 震荡 / 变 nan | loss 几乎不降 |
| 训练像在发散 | 收敛极慢 |

- **最优 lr 随 batch size 缩放**（线性缩放法则）
- LLM 微调：`1e-4 ~ 3e-4`（AdamW）；预训练：`1e-4` 左右

---

## 三、深度学习原理（14-20）

**14. 反向传播的链式法则怎么用？**
→ [Part2 第5篇](/guides/deep-learning/part2-dl-principles/05-backprop)

三条规则：加法→等值分发；乘法→交叉相乘；矩阵乘→外积。

$$\frac{\partial L}{\partial W} = a^\top \cdot \frac{\partial L}{\partial z}$$

**踩坑点**：忘了 batch 平均的系数、矩阵乘法顺序写反（PyTorch 会静默广播出错结果）。

---

**15. 梯度消失的本质是什么？残差连接为什么有效？**
→ [Part2 第8篇](/guides/deep-learning/part2-dl-principles/08-residual)

- **本质**：$\frac{\partial L}{\partial x_1} \propto \prod_l \frac{1}{\sqrt{n}} = n^{-L/2}$，深层指数衰减
- **残差的保证**：$\prod_{l}(I + J_l)$ 展开后**第一项是 $I$**，即使所有 $J_l = 0$，梯度也原样传下去
- **实测**：60 层无残差梯度 = 0，有残差 = 1.01e+05

---

**16. 为什么不能用 0 初始化权重？**
→ [Part2 第9篇](/guides/deep-learning/part2-dl-principles/09-initialization)

- 全 0 → 输出 0 → 梯度 0 → 完全不训练
- **对称性问题**：所有神经元梯度相同 → 永远同步更新 → 等效于一个神经元
- **例外**：bias 可以初始化为 0；残差块最后一层的 BN 可以设 $\gamma=0$（让块初始为恒等）

---

**17. Xavier 和 He 的区别？为什么 ReLU 网络要用 He？**
→ [Part2 第9篇](/guides/deep-learning/part2-dl-principles/09-initialization)

- Xavier：$\sigma^2 = \frac{2}{n_{in}+n_{out}}$，兼顾前向和反向方差保持，**适合对称激活**
- He：$\sigma^2 = \frac{2}{n_{in}}$，**补偿 ReLU 砍掉一半**
- **实测**（20 层）：Xavier 衰减 5.87e5 倍，He 衰减 2.62 倍，默认初始化衰减 4.65e14 倍

---

**18. Pre-LN 和 Post-LN 的区别？为什么现代 LLM 都用 Pre-LN？**
→ [Part3 第12篇](/guides/deep-learning/part3-transformer/12-transformer-to-llama)

- Pre-LN：`x + Sublayer(LN(x))` → 残差通路是**干净的恒等映射**
- Post-LN：`LN(x + Sublayer(x))` → LN 夹在通路中间
- **Pre-LN 需要 final norm**（因为最后一个 block 的输出没过 norm）—— 这是最常见的实现 bug

---

**19. RMSNorm 比 LayerNorm 少了什么？为什么效果不掉？**
→ [Part2 第6篇](/guides/deep-learning/part2-dl-principles/06-normalization)

- 少了：求均值、减均值、$\beta$ 参数
- **核心**：归一化的主要作用是「控制尺度」，不是「控制中心」
- **实测**：RMSNorm 保留输入偏移（+0.426），但标准差一样被控制（0.905）
- **收益在算子融合**，不在参数（省 $d$ 个参数微不足道）

---

**20. 什么是「退化问题」？和过拟合有什么区别？**
→ [Part2 第8篇](/guides/deep-learning/part2-dl-principles/08-residual)

- **退化**：网络加深，**训练误差**也上升 → 是优化问题，不是过拟合
- **过拟合**：训练误差低，验证误差高
- **原因**：优化器难以在深层网络中「找到」恒等映射的解

---

## 四、Transformer（21-27）

**21. Attention 的公式？为什么除以 $\sqrt{d_k}$？**
→ [Part3 第10篇](/guides/deep-learning/part3-transformer/10-attention)

$$\text{Attention} = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}} + M\right)V$$

**为什么**：$\text{Var}[q\cdot k] = d_k$ → std = $\sqrt{d_k}$。不缩放 → logits std 太大 → **softmax 饱和**。

**实测**：$d_k=64$ 时不缩放 max_p = 0.9990（完全 one-hot，梯度消失），缩放后 0.0350。

---

**22. 多头注意力的参数量比单头多吗？**
→ [Part3 第11篇](/guides/deep-learning/part3-transformer/11-multi-head-rope)

**一样多**，都是 $4d_{model}^2$。多头是把一个大注意力拆成 $h$ 个小的，**不是增加参数**。

**「多」的体现**：$h$ 个独立的注意力图，能学到不同的关系模式。

---

**23. RoPE 为什么比绝对位置编码好？**
→ [Part3 第11篇](/guides/deep-learning/part3-transformer/11-multi-head-rope)

**核心性质**：$\langle R_m q, R_n k\rangle = f(q,k,n-m)$，**内积只依赖相对位置**。

**四个优势**：内置相对位置关系 / 不占表示维度 / 外推更好 / 是正交变换（不破坏语义结构）。

**实测**：同一 $(q,k)$ 放不同位置，内积波动仅 1e-6。

---

**24. 什么是 KV Cache？为什么能加速？代价是什么？**
→ [Part3 第13篇](/guides/deep-learning/part3-transformer/13-kv-cache-gqa)

- **原理**：causal mask 保证已生成 token 的 $k_j, v_j$ **永不改变** → 存下来复用
- **收益**：计算量 $O(n^3) \to O(n^2)$
- **代价**：显存。LLaMA-7B, 4096 token, batch=2 → **2.15 GB**
- **关键认知**：**Decode 是显存带宽瓶颈，注意力不是主要成本**（MLP 占大头）

---

**25. MHA / GQA / MQA 的区别？怎么选？**
→ [Part3 第13篇](/guides/deep-learning/part3-transformer/13-kv-cache-gqa)

| | KV 头数 | KV cache（MHA 的比例） |
|---|---|---|
| MHA | $h$ | 100% |
| **GQA** | $g$ | $g/h$ |
| MQA | 1 | 3% |

**论文结论**：$h/g = 4\sim8$ 时质量接近 MHA。**实践**：LLaMA3-70B 用 $g=8$，7B 用 $g=8$（$h/g=4$）。

---

**26. Prefill 和 Decode 的瓶颈有什么不同？优化手段？**
→ [Part3 第13篇](/guides/deep-learning/part3-transformer/13-kv-cache-gqa)

| | Prefill | Decode |
|---|---|---|
| 瓶颈 | **算力** | **显存带宽** |
| 矩阵形状 | $[2048, d]\times[d,d]$ | $[1, d]\times[d,d]$ |
| 优化 | Flash Attention | **量化**、GQA、continuous batching |

**推论**：Decode 带宽瓶颈 → 同权重下 batch 越大吞吐越高（这就是 continuous batching 的依据）。

---

**27. 从头写一个 LLaMA Block 需要哪些组件？**
→ [Part3 第12篇](/guides/deep-learning/part3-transformer/12-transformer-to-llama)

```
RMSNorm → Attention(SwiGLU 无) → 残差
RMSNorm → SwiGLU → 残差
```

**必备组件**：RMSNorm、MultiHeadAttention（含 RoPE）、SwiGLU、causal mask、final norm。

**参数量配置**：4 个 $d^2$（QKVO）+ $3 \times d \times h_{ffn}$（SwiGLU，$h_{ffn} \approx \frac{8}{3}d$）。

---

## 五、研究方法（28-30）

**28. 论文报告的提升 1%，可信吗？怎么验证？**
→ [Part4 第16篇](/guides/deep-learning/part4-research/16-designing-experiments)

**五步验证**：
1. 算置信区间（$n=1000$ 时 1% 差异可能只有 1.4 个 SE）
2. 3+ 随机种子报 ±std
3. **配对检验**（McNemar），不是独立 t 检验
4. **给 baseline 也调参**（最容易出问题的地方）
5. 换数据集验证 + 报告代价

---

**29. 消融实验怎么做才可信？**
→ [Part4 第16篇](/guides/deep-learning/part4-research/16-designing-experiments)

**四个原则**：
1. 一次只改一个东西
2. **去掉后要重新调超参**（最常被忽略）
3. 多 seed
4. **要做组合消融**（检测交互作用）

**组合消融的例子**：单独去 A 掉 0.5%，单独去 B 掉 2%，但同时去掉掉 8% → A 和 B 强耦合，「B 重要 A 不重要」是错误结论。

---

**30. 训练时 loss 变成 nan，怎么排查？**
→ [Part2 第9篇](/guides/deep-learning/part2-dl-principles/09-initialization)

**按概率排序的原因**：

| 原因 | 概率 | 解法 |
|---|---|---|
| 学习率太大 | 60% | 调小 |
| fp16 溢出 | 20% | bf16 或 loss scaling |
| log(0) | 10% | 检查 loss 实现 |
| 数据有 nan/inf | 8% | 清洗 |
| 梯度爆炸 | 2% | 梯度裁剪 |

**定位工具**：`torch.autograd.detect_anomaly()`

---

## 附录：高频「陷阱题」

**Q：训练时 `model.eval()` 了会怎样？**
A：Dropout/BatchNorm 行为错误。**eval 时 BN 用 running 统计量**，train 时用当前 batch 统计量 → 结果不可复现。**eval 不是「冻结」，是「切换行为」。**

**Q：为什么测试集不能用 `shuffle=True`？**
A：评估必须可复现，否则准确率的变化无法归因。**而且训练集必须 shuffle（防过拟合），测试集绝不能。**

**Q：Batch Size 是不是越大越好？**
A：不是。大 batch → 梯度更准，但（a）泛化可能变差（小 batch 的噪声有正则化作用）；（b）lr 要按比例放大；（c）显存受限。

**Q：`torch.optim.Adam` 和 `AdamW` 我该用哪个？**
A：**永远用 AdamW**。`Adam + weight_decay` 在长训练里衰减行为不可预测，且和 AMP/分布式兼容性更差。

**Q：为什么 LLM 不用 Dropout？**
A：预训练数据量远超参数量，过拟合风险低；Dropout 引入梯度噪声降低训练效率。**但 LoRA 微调时反而要用**（数据少）。

**Q：模型 train loss 很低但效果不好，怎么排查？**
A：① 训练/验证数据集是否同分布 ② 验证集是否有泄漏 ③ 是否只监控了 loss 没监控业务指标 ④ 人工看 50 个错例（**最有效的排查手段**）

---

**回到** [目录](/guides/deep-learning/)
