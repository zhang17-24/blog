"""
PyTorch 完整训练脚本 —— FashionMNIST 衣服图片分类
================================================

本脚本是官方 8 章教程的完整整合版，可直接运行：

    pip install torch torchvision
    python fashion_mnist.py

可选参数：
    python fashion_mnist.py --epochs 10 --lr 0.01 --batch-size 128 --device cpu

输出示例：
    Using cpu device
    Epoch 1
    -------------------------------
    loss:   2.3111 [    64/60000]
    ...
    Test Error:
     Accuracy: 45.9%, Avg loss: 2.1506
"""

import argparse
import time

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import v2


# ============================================================
# 0. 命令行参数
# ============================================================
def parse_args():
    p = argparse.ArgumentParser(description="FashionMNIST 训练脚本")
    p.add_argument("--epochs", type=int, default=5, help="训练轮数")
    p.add_argument("--batch-size", type=int, default=64, help="批大小")
    p.add_argument("--lr", type=float, default=1e-3, help="学习率")
    p.add_argument("--hidden", type=int, default=512, help="隐藏层宽度")
    p.add_argument("--device", type=str, default=None, help="强制指定设备，如 cpu / cuda")
    p.add_argument("--num-workers", type=int, default=0, help="DataLoader 子进程数")
    p.add_argument("--save", type=str, default="model.pth", help="模型保存路径")
    return p.parse_args()


args = parse_args()


# ============================================================
# 1. 设备选择
# ============================================================
def get_device(forced=None):
    """优先用GPU，没有就退回 CPU。"""
    if forced:
        return forced
    if torch.accelerator.is_available():
        return torch.accelerator.current_accelerator().type
    return "cpu"


device = get_device(args.device)
print(f"Using {device} device")


# ============================================================
# 2. 数据（第 2、3 章）
# ============================================================
def build_dataloaders(batch_size, num_workers):
    """构建训练/测试数据集和加载器。"""

    # transform：把 PIL 图片转成 float32 张量，像素缩放到 [0, 1]
    # 训练集和测试集用同一个 transform —— 本教程不做数据增强
    tf = v2.Compose([
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),
    ])

    training_data = datasets.FashionMNIST(
        root="data", train=True, download=True, transform=tf)
    test_data = datasets.FashionMNIST(
        root="data", train=False, download=True, transform=tf)

    # 训练集必须 shuffle=True（防过拟合）
    # 测试集 shuffle=False（结果要可复现）
    train_dataloader = DataLoader(
        training_data, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    test_dataloader = DataLoader(
        test_data, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_dataloader, test_dataloader


train_dataloader, test_dataloader = build_dataloaders(args.batch_size, args.num_workers)


# ============================================================
# 3. 模型（第 4 章）
# ============================================================
class NeuralNetwork(nn.Module):
    """
    全连接网络：
        Flatten → Linear(784→H) → ReLU → Linear(H→H) → ReLU → Linear(H→10)
    """

    def __init__(self, hidden=512, num_classes=10):
        super().__init__()          # 必须调用：注册子模块
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28 * 28, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, num_classes),
        )

    def forward(self, x):
        """数据流向：返回 logits（原始分数，不是概率）。"""
        x = self.flatten(x)
        return self.linear_relu_stack(x)


model = NeuralNetwork(hidden=args.hidden).to(device)
print(model)

n_params = sum(p.numel() for p in model.parameters())
print(f"Total parameters: {n_params:,}\n")


# ============================================================
# 4. 损失函数与优化器（第 6 章）
# ============================================================
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=args.lr)


# ============================================================
# 5. 训练与评估循环（第 6 章）
# ============================================================
def train_loop(dataloader, model, loss_fn, optimizer):
    """跑完一个 epoch 的训练。"""
    size = len(dataloader.dataset)
    model.train()                  # 启用 dropout/batchnorm 的训练行为

    for batch, (X, y) in enumerate(dataloader):
        X, y = X.to(device), y.to(device)     # 数据也要搬到 device

        # --- 前向传播 + 算损失 ---
        pred = model(X)
        loss = loss_fn(pred, y)

        # --- 反向传播：计算梯度 ---
        loss.backward()

        # --- 更新参数 ---
        optimizer.step()

        # --- 清零梯度（必须放在最后！）---
        optimizer.zero_grad()

        if batch % 100 == 0:
            loss_val = loss.item()
            current = (batch + 1) * len(X)
            print(f"loss: {loss_val:>7.4f}  [{current:>5d}/{size:>5d}]")


def test_loop(dataloader, model, loss_fn):
    """在测试集上评估，返回 (平均损失, 准确率)。"""
    model.eval()                   # 切到评估模式

    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss = 0.0
    correct = 0

    # no_grad：不记录计算图，省显存、更快
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()

    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100 * correct):>0.1f}%, "
          f"Avg loss: {test_loss:>8.4f} \n")

    return test_loss, correct


# ============================================================
# 6. 主流程
# ============================================================
def main():
    t_start = time.time()
    best_acc = 0.0

    for epoch in range(args.epochs):
        print(f"Epoch {epoch + 1}\n" + "-" * 31)
        train_loop(train_dataloader, model, loss_fn, optimizer)
        _, acc = test_loop(test_dataloader, model, loss_fn)

        # 保存验证集上最好的模型（而不是最后一个）
        if acc > best_acc:
            best_acc = acc
            torch.save(model.state_dict(), args.save)
            print(f"  ↑ New best model saved ({100 * acc:.1f}%)")

    elapsed = time.time() - t_start
    print("Done!")
    print(f"Best accuracy: {100 * best_acc:.1f}%")
    print(f"Weights saved to: {args.save}")
    print(f"Total time: {elapsed:.1f}s")

    # --------------------------------------------------------
    # 7. 加载存档并做一次预测（第 7 章）
    # --------------------------------------------------------
    print("\n--- 重新加载模型并预测 ---")
    loaded = NeuralNetwork(hidden=args.hidden).to(device)
    loaded.load_state_dict(torch.load(args.save, weights_only=True))
    loaded.eval()

    classes = ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
               "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]

    with torch.no_grad():
        x, y = test_dataloader.dataset[0]
        pred = loaded(x.to(device))
        predicted = classes[pred[0].argmax(0)]
        print(f'Predicted: "{predicted}", Actual: "{classes[y]}"')


if __name__ == "__main__":
    main()
