import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class RMSNorm(nn.Module):
    def __init__(self, d, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d))
        self.eps = eps

    def forward(self, x):
        # ★ 只除以均方根，不减均值
        rms = x.pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()
        return self.weight * (x * rms)


def precompute_rope_angles(d, base=10000):
    """预计算 RoPE 的 cos/sin 表"""
    half = d // 2
    inv_freq = 1.0 / (base ** (torch.arange(0, half, 2).float() / half))
    return inv_freq


def apply_rope(x, cos, sin):
    """x: [..., seq, d]，cos/sin: [seq, d//2]"""
    half = x.shape[-1] // 2
    x1, x2 = x[..., :half], x[..., half:]
    return torch.cat([x1 * cos - x2 * sin, x2 * cos + x1 * sin], dim=-1)


class RotaryEmbedding(nn.Module):
    def __init__(self, d, max_seq=2048, base=10000):
        super().__init__()
        self.d = d
        inv_freq = 1.0 / (base ** (torch.arange(0, d, 2).float() / d))
        pos = torch.arange(max_seq).float()
        angles = torch.outer(pos, inv_freq)              # [max_seq, d/2]
        self.register_buffer("cos_cached", angles.cos(), persistent=False)
        self.register_buffer("sin_cached", angles.sin(), persistent=False)

    def forward(self, seq_len):
        return self.cos_cached[:seq_len], self.sin_cached[:seq_len]


class Attention(nn.Module):
    """支持 GQA 的多头注意力"""

    def __init__(self, d, n_heads, n_kv_heads=None):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads or n_heads
        assert n_heads % self.n_kv_heads == 0, "n_heads 必须被 n_kv_heads 整除"
        self.n_rep = n_heads // self.n_kv_heads      # ★ GQA: 每个 KV 头被多少 Q 头共享
        self.d_head = d // n_heads

        self.wq = nn.Linear(d, n_heads * self.d_head, bias=False)
        self.wk = nn.Linear(d, self.n_kv_heads * self.d_head, bias=False)   # ★ 更少
        self.wv = nn.Linear(d, self.n_kv_heads * self.d_head, bias=False)   # ★ 更少
        self.wo = nn.Linear(n_heads * self.d_head, d, bias=False)

    def forward(self, x, cos, sin):
        B, L, _ = x.shape

        q = self.wq(x).view(B, L, self.n_heads, self.d_head).transpose(1, 2)
        k = self.wk(x).view(B, L, self.n_kv_heads, self.d_head).transpose(1, 2)
        v = self.wv(x).view(B, L, self.n_kv_heads, self.d_head).transpose(1, 2)

        # ★ RoPE 只作用在 q, k 上，不作用在 v
        q = apply_rope(q, cos, sin)
        k = apply_rope(k, cos, sin)

        # ★ GQA: 把 KV 头重复到和 Q 头一样多（必须在 attention 之前）
        if self.n_rep > 1:
            k = k.repeat_interleave(self.n_rep, dim=1)   # [B, n_kv, L, dh] -> [B, n_heads, L, dh]
            v = v.repeat_interleave(self.n_rep, dim=1)

        # ★ 用 PyTorch 内置的融合实现（自动选最优后端）
        out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        out = out.transpose(1, 2).contiguous().view(B, L, -1)
        return self.wo(out)


class SwiGLU(nn.Module):
    def __init__(self, d, hidden):
        super().__init__()
        # ★ 三个矩阵：门、值、下投影
        self.w_gate = nn.Linear(d, hidden, bias=False)
        self.w_up   = nn.Linear(d, hidden, bias=False)
        self.w_down = nn.Linear(hidden, d, bias=False)

    def forward(self, x):
        # ★ SwiGLU = SiLU(门) ⊗ 值
        return self.w_down(F.silu(self.w_gate(x)) * self.w_up(x))


class LlamaBlock(nn.Module):
    def __init__(self, d, n_heads, n_kv_heads, hidden):
        super().__init__()
        self.attn = Attention(d, n_heads, n_kv_heads)
        self.ffn = SwiGLU(d, hidden)
        self.norm1 = RMSNorm(d)          # ★ Pre-LN
        self.norm2 = RMSNorm(d)

    def forward(self, x, cos, sin):
        # ★ Pre-LN：先norm 再算，最后残差相加
        x = x + self.attn(self.norm1(x), cos, sin)
        x = x + self.ffn(self.norm2(x))
        return x


class LlamaModel(nn.Module):
    def __init__(self, vocab=32000, d=4096, n_layers=32, n_heads=32,
                 n_kv_heads=32, max_seq=2048, ffn_hidden=None):
        super().__init__()
        self.d = d
        ffn_hidden = ffn_hidden or int(8 * d / 3 / 64) * 64# 8/3 d，对齐64

        self.embed = nn.Embedding(vocab, d)
        self.rope = RotaryEmbedding(d // n_heads, max_seq)  # RoPE 在 d_head 维度上做
        self.layers = nn.ModuleList([
            LlamaBlock(d, n_heads, n_kv_heads, ffn_hidden) for _ in range(n_layers)
        ])
        self.norm = RMSNorm(d)          # ★ final norm，Pre-LN 必需
        self.lm_head = nn.Linear(d, vocab, bias=False)
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def forward(self, tokens):
        x = self.embed(tokens)
        cos, sin = self.rope(x.shape[1])
        for layer in self.layers:
            x = layer(x, cos, sin)
        x = self.norm(x)# ★ final norm
        return self.lm_head(x)


# 测试
if __name__ == "__main__":
    model = LlamaModel(vocab=32000, d=512, n_layers=4, n_heads=8,
                        n_kv_heads=2, max_seq=128, ffn_hidden=1365)
    print(model)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"\n总参数: {n_params:,}")

    tokens = torch.randint(0, 32000, (2, 16))
    logits = model(tokens)
    print(f"输入 {tuple(tokens.shape)} → 输出 {tuple(logits.shape)}")

    # 验证 causal
    loss = F.cross_entropy(logits[:, :-1].reshape(-1, 32000),
                tokens[:, 1:].reshape(-1))
    print(f"loss: {loss.item():.4f}")
    loss.backward()
    print("反向传播成功")
