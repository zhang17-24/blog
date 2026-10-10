"""
PyTorch 入门练习题 —— 由浅入深
================================

用法：
    1. 每次只做一道题
    2. 先自己写，写完再展开答案
    3. 做完在终端跑一遍验证输出

    python exercises.py          # 跑基础题（不需要下载数据集）
    python exercises.py --all    # 跑全部

运行这个文件不需要下载 FashionMNIST，只有第 12 题需要。
"""

import sys

import torch
from torch import nn
from torch.utils.data import Dataset


# ============================================================
# 第1 关：张量基础
# ============================================================

def ex01_shape_basics():
    """预测输出：a.shape / b.shape / a + b 的形状"""
    a = torch.zeros(2, 3, 4)
    b = torch.zeros(4)
    # TODO: 先猜，再运行验证
    return a.shape, b.shape, (a + b).shape


def ex02_elementwise_vs_matmul():
    """预测输出：a * b 和 a @ b 的形状与含义"""
    a = torch.tensor([[1., 2.], [3., 4.]])
    b = torch.tensor([[1., 1.], [1., 1.]])
    # TODO
    return (a * b), (a @ b)


def ex03_alias_vs_clone():
    """解释：为什么下面两段代码行为不同"""
    a = torch.tensor([[1., 2.], [3., 4.]])

    # 情况1：b = a  ->  改 b 会改到 a
    b = a
    b[0][0] = 999.
    case_alias = a[0][0].item()

    # 情况2：a 恢复原状，然后用 clone 试
    a = torch.tensor([[1., 2.], [3., 4.]])
    c = a.clone()
    c[0][0] = -1.
    case_clone = a[0][0].item()

    return f"b=a 改后 a[0][0]={case_alias}（被改了）, c=a.clone() 改后 a[0][0]={case_clone}（没变）"


def ex04_eye_mask():
    """一行代码构造 5×5 单位矩阵，把非对角线位置置 0"""
    m = torch.eye(5)
    mask = torch.arange(5)[:, None] == torch.arange(5)   # True 只在主对角线
    return m * mask.long()


def ex05_numel_and_param_count():
    """统计本章模型的参数量，并分权重/偏置列出"""
    model = nn.Sequential(
        nn.Flatten(),
        nn.Linear(784, 512), nn.ReLU(),
        nn.Linear(512, 512), nn.ReLU(),
        nn.Linear(512, 10),
    )
    return sum(p.numel() for p in model.parameters())   # 669706


# ============================================================
# 第 2 关：自动微分
# ============================================================

def ex06_simple_grad():
    """
    手算并验证：loss = w * x^2, x=2, w=3
    d(loss)/dw = x^2 = 4
    """
    x = torch.tensor(2.0)
    w = torch.tensor(3.0, requires_grad=True)   # ★别忘了 requires_grad
    loss = w * x ** 2
    loss.backward()
    return w.grad      # tensor(4.)  因为 d(loss)/dw = x^2 = 4


def ex07_non_leaf_grad():
    """
    解释：为什么 z.grad 是 None，但 z.grad_fn 不是 None？
    """
    x = torch.ones(5)
    w = torch.randn(5, 3, requires_grad=True)
    z = torch.matmul(x, w)
    return f"z.grad = {z.grad}, z.grad_fn = {type(z.grad_fn).__name__}"


def ex08_no_grad():
    """用 no_grad 验证推理时不需要追踪计算图"""
    x = torch.randn(3)
    w = torch.randn(3, requires_grad=True)

    y1 = (x * w).sum()

    with torch.no_grad():
        y2 = (x * w).sum()
    return f"no_grad外: {y1.requires_grad}, no_grad内: {y2.requires_grad}"


def ex09_gradient_accumulation():
    """
    演示梯度累加：连续两次 backward，梯度会翻倍
    """
    w = torch.tensor([2.0], requires_grad=True)
    loss1 = (w ** 2).sum()
    loss1.backward()
    g1 = w.grad.clone()

    loss2 = (w ** 2).sum()
    loss2.backward()
    g2 = w.grad.clone()

    # TODO: zero_ 之后再来一次
    w.grad.zero_()
    loss3 = (w ** 2).sum()
    loss3.backward()
    g3 = w.grad.clone()

    return g1, g2, g3


def ex10_numerical_derivative():
    """
    数值微分：对比中心差分和 autograd 的结果
    """
    def derivative(f, x, eps=1e-5):
        return (f(x + eps) - f(x - eps)) / (2 * eps)

    f = lambda t: t ** 3
    x = torch.tensor(2.0)

    numeric = derivative(f, x)

    t = torch.tensor(2.0, requires_grad=True)
    (t ** 3).backward()
    return f"数值微分: {numeric.item():.4f}, autograd: {t.grad.item()} (真值12)"


# ============================================================
# 第 3 关：nn.Module
# ============================================================

def ex11_why_init_matters():
    """
    下面这个「错误」的模型能训练吗？为什么？

    class BadNet(nn.Module):
        def forward(self, x):
            self.fc = nn.Linear(784, 10)
            return self.fc(x)
    """
    # TODO: 想清楚答案，不必写代码
    return "能" if False else "不能"


def ex12_forward_shapes():
    """输入 [64, 1, 28, 28]，经过标准模型输出什么形状？"""
    model = nn.Sequential(
        nn.Flatten(), nn.Linear(784, 512), nn.ReLU(), nn.Linear(512, 10))
    x = torch.rand(64, 1, 28, 28)
    return model(x).shape    # torch.Size([64, 10])


def ex13_linear_manual_check():
    """
    手算验证 nn.Linear(3, 2) 的输出：
    y = W @ x + b
    """
    lin = nn.Linear(3, 2)
    x = torch.tensor([[1., 2., 3.]])
    pred = lin(x)

    # TODO: 用W @ x + b 自己算一遍，注意 x 是一维的 x[0]
    manual = lin.weight @ x[0] + lin.bias
    return pred, manual, torch.allclose(manual, pred[0])


def ex14_relu_effect():
    """
    验证：删掉所有 ReLU 后，模型参数量不变但表达能力下降
    （观察若干层 Linear 叠加能否被单个 Linear 替代）
    """
    x = torch.randn(10, 5)

    with_relu = nn.Sequential(nn.Linear(5, 20), nn.ReLU(), nn.Linear(20, 20), nn.ReLU(), nn.Linear(20, 5))
    without_relu = nn.Sequential(nn.Linear(5, 20), nn.ReLU(), nn.Linear(20, 20), nn.Linear(20, 5))

    # TODO: 思考——为什么 without_relu 里第一层保留ReLU？
    return with_relu, without_relu


# ============================================================
# 第 4 关：Dataset
# ============================================================

class DummyDataset(Dataset):
    """第 4 步练习用的小数据集：返回 (序号, 平方值)"""

    def __init__(self, n):
        self.n = n

    def __len__(self):
        return self.n

    def __getitem__(self, idx):
        return idx, idx ** 2


def ex15_dataloader_batches():
    """60000 个样本、batch_size=64，一个 epoch 有多少个 batch？"""
    ds = DummyDataset(60000)
    dl = torch.utils.data.DataLoader(ds, batch_size=64)
    return len(dl)


def ex16_batch_iteration():
    """取第一批，打印 X 和 y 的 shape"""
    ds = DummyDataset(60000)
    dl = torch.utils.data.DataLoader(ds, batch_size=64, shuffle=True)

    X, y = next(iter(dl))          # iter() 建迭代器, next() 取第一批
    return X.shape, y.shape


def ex17_custom_txt_dataset():
    """实现一个读取文件夹里所有 .txt 的 Dataset，文件名当标签"""
    import tempfile
    from pathlib import Path

    class TxtDataset(Dataset):
        def __init__(self, root):
            self.root = Path(root)
            self.files = sorted(self.root.glob("*.txt"))   # 只列清单，不读内容

        def __len__(self):
            return len(self.files)

        def __getitem__(self, idx):
            p = self.files[idx]
            return p.read_text(), p.stem      # (内容, 标签)

    # 自测
    with tempfile.TemporaryDirectory() as d:
        Path(d, "cat.txt").write_text("meow")
        Path(d, "dog.txt").write_text("woof")
        ds = TxtDataset(d)
        return len(ds), sorted(ds[i][1] for i in range(len(ds))), ds[0]


# ============================================================
# 第 5 关：保存与加载
# ============================================================

def ex18_state_dict_keys():
    """打印模型的 state_dict 的 key 和形状"""
    model = nn.Sequential(nn.Flatten(), nn.Linear(784, 10))
    return [(k, tuple(v.shape)) for k, v in model.state_dict().items()]


def ex19_roundtrip_save_load():
    """
    保存模型 → 修改权重 → 加载回来 → 验证权重恢复了
    """
    model = nn.Linear(4, 2)
    torch.save(model.state_dict(), "/tmp/_test_ex19.pth")
    original = model.weight.detach().clone()

    with torch.no_grad():
        model.weight.add_(100.)          # 人为破坏权重
    broken = model.weight.detach().clone()

    # TODO: 重新加载（新建结构 -> load_state_dict）
    model.load_state_dict(torch.load("/tmp/_test_ex19.pth", weights_only=True))

    restored = torch.equal(model.weight.detach(), original)
    changed = not torch.equal(broken, original)
    return f"权重已恢复: {restored}, 破坏生效: {changed}"


def ex20_eval_does_not_change_params():
    """验证 model.eval() 不会修改任何参数"""
    model = nn.Sequential(nn.Linear(4, 4), nn.BatchNorm1d(4), nn.Dropout(0.5))
    before = {k: v.clone() for k, v in model.state_dict().items()}

    model.eval()

    same = all(torch.equal(before[k], v) for k, v in model.state_dict().items())
    return f"eval() 后参数完全一致: {same}   (training标志: {model.training})"


# ============================================================
# 运行器
# ============================================================
EXERCISES = [
    ("01张量形状基础", ex01_shape_basics),
    ("02逐元素vs矩阵乘法", ex02_elementwise_vs_matmul),
    ("03别名vs克隆", ex03_alias_vs_clone),
    ("04单位矩阵置零", ex04_eye_mask),
    ("05统计参数数量", ex05_numel_and_param_count),
    ("06简单梯度", ex06_simple_grad),
    ("07非叶子张量梯度", ex07_non_leaf_grad),
    ("08 no_grad", ex08_no_grad),
    ("09梯度累加", ex09_gradient_accumulation),
    ("10数值微分对比", ex10_numerical_derivative),
    ("11为什么层要放__init__", ex11_why_init_matters),
    ("12前向形状追踪", ex12_forward_shapes),
    ("13 Linear手算验证", ex13_linear_manual_check),
    ("14 ReLU的作用", ex14_relu_effect),
    ("15 batch数量", ex15_dataloader_batches),
    ("16取第一批", ex16_batch_iteration),
    ("17自定义Dataset", ex17_custom_txt_dataset),
    ("18 state_dict的key", ex18_state_dict_keys),
    ("19保存加载往返", ex19_roundtrip_save_load),
    ("20 eval不改参数", ex20_eval_does_not_change_params),
]


def main():
    print("=" * 60)
    print("PyTorch 入门练习")
    print("=" * 60)

    todo = sys.argv[1:] or [str(i + 1) for i in range(len(EXERCISES))]
    targets = {int(t) for t in todo if t.isdigit()} if todo == list(todo) or all(t.isdigit() for t in todo) else set()

    for i, (name, fn) in enumerate(EXERCISES, 1):
        if targets and i not in targets:
            continue
        print(f"\n{'='*60}")
        print(f"练习 {i:2d} · {name}")
        print("=" * 60)
        try:
            result = fn()
            if result is not None:
                print(f"→ {result}")
            else:
                print("→ (返回 None，检查 TODO 是否填了)")
        except Exception as e:
            print(f"✗ {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
