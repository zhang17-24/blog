---
title: 环境安装与运行方式
description: 装 PyTorch、验证装好了、三种运行方式（本地脚本 / Jupyter / Colab）怎么选。
---

## 一、先确认一件事：你需不需要 GPU？

跑这套教程用 **CPU 完全够**。FashionMNIST 只有6 万张 28×28 的小图，CPU 上训练一轮大概十几秒。

```bash
# 看有没有 NVIDIA 显卡
nvidia-smi
```

- 有输出且看到 `CUDA Version` → 装 CUDA 版，速度快
- 提示找不到命令 / 你是 Mac → 装 CPU 版就行，教程代码不用改一行

> **不要在没搞懂之前折腾 GPU。** 第一遍学习用 CPU 完全不影响理解，等你真要训大模型再说。

---

## 二、安装

### 推荐：用 pip 装 CPU 版（最省事）

```bash
pip install torch torchvision
```

这条命令会自动装好 CPU 版。Mac（M1/M2/M3）也能用，装的是 MPS 后端，教程里的 `torch.accelerator` 会自动识别。

### 如果你有 NVIDIA 显卡

去 [pytorch.org/get-started/locally/](https://pytorch.ac.cn/get-started/locally/) 复制对应命令，**务必选对 CUDA 版本**。写代码时不需要做任何改动，`torch.cuda.is_available()` 会自动处理。

### 装完验证

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

应该输出类似：

```
2.14.0
False
```

`False` 在 CPU 环境下是正常的。

---

## 三、三种运行方式，怎么选

| 方式                   | 适合          | 优点            | 缺点        |
| -------------------- | ----------- | ------------- | --------- |
| **Google Colab**     | 只想快速看效果     | 不用装环境，有免费 GPU | 需要联网，环境会断 |
| **Jupyter Notebook** | 系统学习、跟着笔记敲  | 输出直观，可分段调试    | 要自己配环境    |
| **写 .py 脚本**         | 练工程能力、之后做项目 | 和真实开发一致       | 改错要重跑     |

### 推荐组合：Notebook 学概念 → .py 脚本做综合练习

---

## 四、Notebook 版怎么跑

```bash
# 1. 建一个虚拟环境（强烈建议，避免污染系统 Python）
python -m venv pytorch-env
source pytorch-env/bin/activate   # Windows: pytorch-env\Scripts\activate

# 2. 装 PyTorch
pip install torch torchvision matplotlib pandas

# 3. 装 Jupyter
pip install jupyter

# 4. 开Jupyter
jupyter notebook
```

浏览器打开后，新建 notebook。

### 注意：每个 notebook 都要重新导入 + 重新定义

官方教程每章都是**独立的 notebook**，第 6 章直接用了第 2、4 章的代码。如果你新建 notebook，**必须先跑一遍前面的定义**，否则会报 `NameError: name 'model' is not defined`。

解决：在每个 notebook 开头写一个 `setup.py` 片段，或者直接复制 `代码/fashion_mnist.py` 里的模型定义部分。

---

## 五、脚本版怎么跑

本笔记提供的完整脚本：

```bash
cd 代码
python fashion_mnist.py
```

脚本会自动下载 FashionMNIST（26MB，只下一次）到 `./data/`，然后开始训练。

第一次跑没有 GPU 会比较慢（5 轮大概 3-5 分钟），属于正常。终端会输出：

```
Epoch 1
-------------------------------
loss: 2.311154  [   64/60000]
...
Test Error:
 Accuracy: 45.9%, Avg loss: 2.150578
```

**你只需要盯两个数**：`loss` 应该往下走，`Accuracy` 应该往上涨。涨不动了就调大学习率（第 6 章会讲）。

---

## 六、常见问题

**Q: `ModuleNotFoundError: No module named 'torch'`**  
装的时候没装进当前环境。检查 `which python` 和 `pip` 指向的是不是同一个环境。虚拟环境忘了激活是最常见原因。

**Q: 装完 torch 之后 numpy 报冲突**

```bash
pip install numpy --upgrade
```

**Q: Mac 上很慢/报错**  
M1/M2 的 GPU 是 `mps` 后端。这套教程的代码兼容，但如果你在训练时遇到奇怪报错，可以先用 CPU 验证：

```python
device = "cpu"   # 临时改成这个
```

**Q: 下载 FashionMNIST 卡住**  
数据要下到 `root` 指定目录。默认是当前目录下的 `data/`。国内网络建议手动下载后放到 `data/FashionMNIST/` 下。

**Q: 报错说某个张量在 CPU、某个在 GPU**  
这是最常见的错误。规则：**模型 `.to(device)` 之后，所有输入数据也必须 `.to(device)`**。第 6 章会详细讲。

---

**下一步** → [先看懂整件事](/guides/pytorch/part1-basics/02-big-picture)
