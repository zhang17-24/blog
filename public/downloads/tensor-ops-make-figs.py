#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
张量操作可视化绘图引擎
======================
为《张量与矩阵运算图解》生成全部配图。

用法:
    python make_figs.py

输出到 ./figs/ 目录。
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti TC", "Arial Unicode MS"]
# ★ monospace 必须指向含中文字形的字体，否则 "family='monospace'" 里的中文会变方块
#   （实测 matplotlib 3.11 在 monospace 别名上不做字体回退，Meno+中文会缺字形）
plt.rcParams["font.monospace"] = ["PingFang SC"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
os.makedirs(OUT, exist_ok=True)

# ---------------- 主题色（浅色主题） ----------------
C_BG = "#ffffff"
C_CELL = "#eef2f7"        # 单元格底色
C_CELL2 = "#dbe7f5"       # 次色（用于区分维度）
C_HL = "#ffd9a0"          # 高亮（选中的元素）
C_HL2 = "#ffb3b3"         # 次高亮（结果）
C_EDGE = "#9aa5b1"
C_TXT = "#1f2328"
C_LINE = "#d1242f"        # 强调线（红，与手册一致）


def _draw_cells(ax, data, ox=0, oy=0, cw=1.0, ch=1.0,
                face=C_CELL, edge=C_EDGE, lw=1.2,
                show=True, fs=10.5, fmt="{:.0f}", hl=None, hl_color=C_HL,
                txt_color=C_TXT, alpha=1.0):
    """在 ax 上画一个数值矩阵。data 是 2D 数组。"""
    data = np.atleast_2d(np.asarray(data))
    rows, cols = data.shape
    hl = hl or set()

    for i in range(rows):
        for j in range(cols):
            fc = hl_color if (i, j) in hl else face
            ax.add_patch(plt.Rectangle((ox + j * cw, oy + (rows - 1 - i) * ch),
                                       cw, ch, facecolor=fc, edgecolor=edge,
                                       linewidth=lw, alpha=alpha, zorder=2))
            if show:
                v = data[i, j]
                s = fmt.format(v) if isinstance(v, (int, float, np.floating, np.integer)) else str(v)
                ax.text(ox + j * cw + cw / 2, oy + (rows - 1 - i) * ch + ch / 2,
                        s, ha="center", va="center", fontsize=fs,
                        color=txt_color, zorder=3)
    return rows, cols


def _clean(ax, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")


def _title(ax, text, y, fs=13, color=C_TXT):
    ax.text(0, y, text, ha="center", va="center", fontsize=fs,
            color=color, fontweight="bold")


def _save(fig, name, pad=0.25):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=170, bbox_inches="tight", pad_inches=pad,
                facecolor=C_BG)
    plt.close(fig)
    print(f"  ✓ {name}")


# ============================================================
# 01 · 张量维度
# ============================================================
def fig_dimensions():
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.2))

    # 0D: 标量
    ax = axes[0]
    _draw_cells(ax, [[7]], cw=1.1, ch=1.1, fs=14)
    _clean(ax, (-0.6, 1.7), (-0.9, 2.1))
    _title(ax, "0 维 · 标量\nshape = ()", 1.6)
    ax.text(0.55, -0.45, "torch.tensor(7)", ha="center", fontsize=10,
            color=C_TXT, family="monospace", bbox=dict(fc="#f6f8fa", ec=C_EDGE, boxstyle="round,pad=0.4"))

    # 1D: 向量
    ax = axes[1]
    _draw_cells(ax, [[3, 1, 4, 1, 5]], cw=0.85, ch=1.0, fs=11)
    _clean(ax, (-0.5, 4.6), (-0.9, 2.1))
    _title(ax, "1 维 · 向量\nshape = (5,)", 1.6)
    ax.text(1.9, -0.45, "torch.tensor([3,1,4,1,5])", ha="center", fontsize=9,
            color=C_TXT, family="monospace", bbox=dict(fc="#f6f8fa", ec=C_EDGE, boxstyle="round,pad=0.4"))

    # 2D: 矩阵
    ax = axes[2]
    _draw_cells(ax, [[1, 2, 3], [4, 5, 6]], cw=0.85, ch=0.85, fs=11)
    _clean(ax, (-0.6, 3.2), (-0.9, 2.9))
    _title(ax, "2 维 · 矩阵\nshape = (2, 3)", 2.4)
    ax.annotate("", xy=(-0.25, 0), xytext=(-0.25, 1.7),
                arrowprops=dict(arrowstyle="<->", color=C_LINE, lw=1.6))
    ax.text(-0.45, 0.85, "2", ha="center", va="center", fontsize=10, color=C_LINE)
    ax.annotate("", xy=(0, 2.05), xytext=(2.55, 2.05),
                arrowprops=dict(arrowstyle="<->", color=C_LINE, lw=1.6))
    ax.text(1.28, 2.2, "3", ha="center", fontsize=10, color=C_LINE)

    # 3D: 三个通道
    ax = axes[3]
    off = 0.30
    for k, (d, a) in enumerate([([[1, 2], [3, 4]], 0.55),
                                ([[5, 6], [7, 8]], 0.75),
                                ([[9, 0], [1, 2]], 1.0)]):
        _draw_cells(ax, d, ox=k * off, oy=k * off, cw=0.78, ch=0.78,
                    fs=10, alpha=a, edge="#7b8794")
    _clean(ax, (-0.6, 3.3), (-0.9, 3.0))
    _title(ax, "3 维\nshape = (3, 2, 2)", 2.5)
    ax.text(0.95, -0.6, "3 个 2×2 的矩阵叠起来", ha="center", fontsize=9.5, color=C_TXT)

    fig.suptitle("四种维度的张量 —— 维度数（ndim）就是 shape 里数字的个数",
                 fontsize=14, fontweight="bold", y=1.04, color=C_TXT)
    _save(fig, "01-维度.png")


# ============================================================
# 02 · 索引与切片
# ============================================================
def fig_indexing():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    data = np.arange(1, 13).reshape(3, 4)
    fs, cw, ch = 11, 0.95, 0.95

    def base(ax):
        _draw_cells(ax, data, cw=cw, ch=ch, fs=fs, edge="#c3cbd6")
        _clean(ax, (-1.0, 4.4), (-1.3, 3.6))

    # x[0] 取第一行
    ax = axes[0]
    base(ax)
    for j in range(4):
        _draw_cells(ax, [[data[0, j]]], ox=j * cw, oy=2 * ch, cw=cw, ch=ch,
                    fs=fs, face=C_HL, edge=C_LINE, lw=2)
    _title(ax, "x[0]  取第 0 行", 3.2)
    ax.text(1.7, -0.75, "shape: (3,4) → (4,)", ha="center", fontsize=10,
            color=C_LINE, family="monospace")

    # x[:, 1] 取第二列
    ax = axes[1]
    base(ax)
    for i in range(3):
        _draw_cells(ax, [[data[i, 1]]], ox=1 * cw, oy=(2 - i) * ch, cw=cw, ch=ch,
                    fs=fs, face=C_HL, edge=C_LINE, lw=2)
    _title(ax, "x[:, 1]  取第 1 列", 3.2)
    ax.text(1.7, -0.75, "shape: (3,4) → (3,)", ha="center", fontsize=10,
            color=C_LINE, family="monospace")

    # x[0:2, 1:3] 矩形切片
    ax = axes[2]
    base(ax)
    for i in range(2):
        for j in range(2):
            _draw_cells(ax, [[data[i, j + 1]]], ox=(j + 1) * cw, oy=(2 - i) * ch,
                        cw=cw, ch=ch, fs=fs, face=C_HL, edge=C_LINE, lw=2)
    _title(ax, "x[0:2, 1:3]  取子矩阵", 3.2)
    ax.text(1.7, -0.75, "shape: (3,4) → (2,2)", ha="center", fontsize=10,
            color=C_LINE, family="monospace")

    fig.suptitle("索引与切片：冒号「:」表示「这一维全都要」",
                 fontsize=14, fontweight="bold", y=1.02, color=C_TXT)
    _save(fig, "02-索引切片.png")


# ============================================================
# 03 · view / reshape
# ============================================================
def fig_view_reshape():
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6))
    data = np.arange(1, 13).reshape(3, 4)

    ax = axes[0]
    _draw_cells(ax, data, cw=0.9, ch=0.9, fs=11)
    _clean(ax, (-0.7, 4.2), (-0.8, 3.2))
    _title(ax, "原始 (3, 4)", 2.85)
    ax.text(1.8, -0.5, "内存顺序：1 2 3 4 5 6 … 12", ha="center",
            fontsize=9.5, color=C_TXT, family="monospace")

    ax = axes[1]
    flat = data.reshape(2, 6)
    _draw_cells(ax, flat, cw=0.72, ch=0.9, fs=11, face=C_CELL2)
    _clean(ax, (-0.7, 4.9), (-0.8, 3.2))
    _title(ax, ".reshape(2, 6) / .view(2, 6)", 2.85)
    ax.text(2.1, -0.5, "元素顺序完全不变，只是换了「排版」",
            ha="center", fontsize=9.5, color=C_LINE)

    fig.suptitle("reshape 与 view：不改变数据，只改变解读方式（总元素数必须相等）",
                 fontsize=14, fontweight="bold", y=1.02, color=C_TXT)
    _save(fig, "03-reshape.png")


# ============================================================
# 04 · transpose / permute
# ============================================================
def fig_transpose_permute():
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.4))
    data = np.arange(1, 7).reshape(2, 3)

    ax = axes[0]
    _draw_cells(ax, data, cw=0.9, ch=0.9, fs=12)
    _clean(ax, (-0.7, 3.4), (-0.9, 2.9))
    _title(ax, "原始 (2, 3)", 2.5)
    ax.text(1.35, -0.55, "x", ha="center", fontsize=11, family="monospace", color=C_TXT)
    ax.text(1.35, 2.75, "(2,3)", ha="center", fontsize=10, family="monospace", color=C_TXT)

    ax = axes[1]
    _draw_cells(ax, data.T, cw=0.9, ch=0.9, fs=12, face=C_CELL2)
    _clean(ax, (-0.7, 3.4), (-0.9, 2.9))
    _title(ax, "x.T / x.transpose(0,1)", 2.5)
    ax.text(1.35, -0.55, "shape (3, 2)", ha="center", fontsize=10,
            family="monospace", color=C_LINE)

    ax = axes[2]
    cube = np.arange(1, 9).reshape(2, 2, 2)
    off = 0.55
    for k in range(2):
        _draw_cells(ax, cube[k], ox=k * off, oy=k * off, cw=0.8, ch=0.8,
                    fs=11, alpha=0.6 + 0.4 * k, edge="#7b8794")
    _clean(ax, (-0.7, 3.4), (-1.3, 2.9))
    _title(ax, "三维张量 (2, 2, 2)", 2.5)
    ax.text(1.2, -0.95, "permute(2,0,1) 可重排任意维度\n（transpose 只能交换两个）",
            ha="center", fontsize=9.5, color=C_LINE)

    fig.suptitle("转置：交换维度。注意——数据没被复制，只是「读法」变了（返回的是视图）",
                 fontsize=13.5, fontweight="bold", y=1.02, color=C_TXT)
    _save(fig, "04-转置.png")


# ============================================================
# 05 · squeeze / unsqueeze
# ============================================================
def fig_squeeze():
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.4))

    # (1,4)
    ax = axes[0]
    _draw_cells(ax, [[1, 2, 3, 4]], cw=0.8, ch=0.9, fs=11)
    _clean(ax, (-0.9, 4.6), (-1.2, 2.3))
    _title(ax, "shape (1, 4)", 1.8)
    ax.annotate("", xy=(-0.35, 0), xytext=(-0.35, 0.9),
                arrowprops=dict(arrowstyle="<->", color=C_LINE, lw=1.6))
    ax.text(-0.6, 0.45, "1", fontsize=10, color=C_LINE, ha="center")
    ax.text(1.9, -0.85, "这个维度是多余的", ha="center", fontsize=9.5, color=C_TXT)

    # squeeze -> (4,)
    ax = axes[1]
    _draw_cells(ax, [[1, 2, 3, 4]], cw=0.8, ch=0.9, fs=11, face=C_CELL2)
    _clean(ax, (-0.9, 4.6), (-1.2, 2.3))
    _title(ax, ".squeeze() → (4,)", 1.8)
    ax.text(1.9, -0.85, "把 size=1 的维度删掉", ha="center", fontsize=9.5, color=C_LINE)

    # unsqueeze -> (1,1,4)
    ax = axes[2]
    _draw_cells(ax, [[1, 2, 3, 4]], cw=0.8, ch=0.9, fs=11, face=C_HL)
    _clean(ax, (-0.9, 4.6), (-1.2, 2.3))
    _title(ax, ".unsqueeze(0) → (1, 1, 4)", 1.8)
    ax.text(1.9, -0.85, "在指定位置插入一个 size=1 的维度\n（常用：给单张图加 batch 维）",
            ha="center", fontsize=9.5, color=C_LINE)

    fig.suptitle("squeeze / unsqueeze：增删「长度为 1」的维度，元素数据完全不变",
                 fontsize=13.5, fontweight="bold", y=1.02, color=C_TXT)
    _save(fig, "05-增删维度.png")


# ============================================================
# 06 · 广播：矩阵 + 向量（最重要）
# ============================================================
def fig_broadcast_row():
    fig = plt.figure(figsize=(13.5, 5.0))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], hspace=0.45, wspace=0.18)

    A = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    b = np.array([10, 20, 30])

    # A
    ax = fig.add_subplot(gs[:, 0])
    _draw_cells(ax, A, cw=0.9, ch=0.9, fs=12)
    _clean(ax, (-0.7, 3.4), (-1.4, 3.4))
    _title(ax, "A  shape (3, 3)", 2.95)

    # 符号
    ax = fig.add_subplot(gs[0, 1])
    ax.text(0.5, 0.5, "+", ha="center", va="center", fontsize=34, color=C_LINE)
    ax.axis("off")
    ax = fig.add_subplot(gs[1, 1])
    ax.text(0.5, 0.5, "=", ha="center", va="center", fontsize=34, color=C_LINE)
    ax.axis("off")

    # b 广播
    ax = fig.add_subplot(gs[0, 2])
    B_rep = np.tile(b, (3, 1))
    _draw_cells(ax, B_rep, cw=0.9, ch=0.72, fs=11, face=C_HL, alpha=0.9)
    _clean(ax, (-0.7, 3.4), (-0.5, 2.6))
    _title(ax, "b  (3,)  →  被广播成 (3, 3)", 2.25, fs=12)
    ax.text(1.35, -0.3, "原来的 b 只有一行，复制 3 份", ha="center",
            fontsize=9.5, color=C_TXT)

    # 结果
    ax = fig.add_subplot(gs[1, 2])
    _draw_cells(ax, A + B_rep, cw=0.9, ch=0.72, fs=11, face="#d8f0dc")
    _clean(ax, (-0.7, 3.4), (-0.5, 2.6))
    _title(ax, "结果  (3, 3)", 2.25, fs=12)

    fig.suptitle("广播规则（从最后一维往前对齐）：尺寸相同 → 直接用；尺寸为 1 → 拉伸；都不匹配 → 报错",
                 fontsize=13.5, fontweight="bold", y=1.0, color=C_TXT)
    _save(fig, "06-广播-行.png")


def fig_broadcast_shape():
    """列向量 + 行向量 = 外积形状，最容易懵的情况"""
    fig, ax = plt.subplots(figsize=(13.5, 5.4))

    col = np.array([[1], [2], [3]])
    row = np.array([10, 20, 30])
    cw, ch = 0.88, 0.82

    # 列向量 (3,1)
    _draw_cells(ax, col, ox=0.4, oy=1.0, cw=cw, ch=ch, fs=12.5, face=C_HL)
    ax.text(0.4 + cw / 2, 3.55, "列向量 (3, 1)", ha="center", fontsize=12,
            fontweight="bold")
    ax.annotate("", xy=(0.4 - 0.22, 1.0), xytext=(0.4 - 0.22, 1.0 + 3 * ch),
                arrowprops=dict(arrowstyle="<->", color=C_LINE, lw=1.4))
    ax.text(0.4 - 0.42, 1.0 + 1.5 * ch, "3", ha="center", va="center",
            fontsize=10, color=C_LINE)

    ax.text(2.1, 2.15, "*", ha="center", va="center", fontsize=30, color=C_LINE)

    # 行向量 (3,)
    _draw_cells(ax, [row], ox=2.6, oy=1.82, cw=cw, ch=ch, fs=12.5, face=C_CELL2)
    ax.text(2.6 + 1.5 * cw, 3.02, "行向量 (3,)", ha="center", fontsize=12,
            fontweight="bold")
    ax.annotate("", xy=(2.6, 1.82 - 0.22), xytext=(2.6 + 3 * cw, 1.82 - 0.22),
                arrowprops=dict(arrowstyle="<->", color=C_LINE, lw=1.4))
    ax.text(2.6 + 1.5 * cw, 1.82 - 0.48, "3", ha="center", fontsize=10, color=C_LINE)

    ax.text(5.35, 2.15, "=", ha="center", va="center", fontsize=30, color=C_LINE)

    # 结果 (3,3)
    res = col * row
    _draw_cells(ax, res, ox=5.9, oy=1.0, cw=cw, ch=ch, fs=12, face="#d8f0dc")
    ax.text(5.9 + 1.5 * cw, 3.55, "结果 (3, 3)", ha="center", fontsize=12,
            fontweight="bold", color="#1a7f37")

    # 底部说明
    ax.text(0.4, 0.35,
            "逐维从后往前对齐：  (3, 1)  *  (3, )   ->   (3, 3)\n"
            "                        最后一维：1 vs 3  → 1 被拉伸成 3\n"
            "                        倒数第二维：3 vs (缺) → 补成 3",
            ha="left", va="top", fontsize=11.5, family="monospace", color=C_TXT,
            bbox=dict(fc="#f6f8fa", ec=C_EDGE, boxstyle="round,pad=0.6"))

    ax.text(5.9, 0.42, "3 个元素\n变 9 个", ha="left", va="top", fontsize=11,
            color=C_LINE, fontweight="bold")

    ax.set_xlim(0, 9.4)
    ax.set_ylim(-0.1, 4.3)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.suptitle("最容易出错的情况：(3,1) 和 (3,) 广播后是 (3,3)，不是 (3,1)",
                 fontsize=13.5, fontweight="bold", y=0.99, color=C_TXT)
    _save(fig, "07-广播-外积形状.png")


# ============================================================
# 08 · 逐元素乘 vs 矩阵乘
# ============================================================
def fig_mul_compare():
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
    A = np.array([[1, 2, 3], [4, 5, 6]])
    B = np.array([[10, 20, 30], [40, 50, 60]])

    ax = axes[0]
    _draw_cells(ax, A, cw=0.8, ch=0.85, fs=11.5)
    _clean(ax, (-0.7, 3.2), (-1.5, 2.9))
    _title(ax, "A (2, 3)", 2.5)

    ax = axes[1]
    _draw_cells(ax, B, cw=0.8, ch=0.85, fs=10.5, face=C_CELL2)
    _clean(ax, (-0.7, 3.2), (-1.5, 2.9))
    _title(ax, "B (2, 3)", 2.5)

    # 逐元素乘
    ax = axes[2]
    _draw_cells(ax, A * B, cw=0.85, ch=0.85, fs=10)
    _clean(ax, (-0.7, 3.5), (-1.5, 2.9))
    _title(ax, "A * B  →  (2, 3)", 2.5)
    ax.text(1.35, -0.62, "逐元素相乘\n位置对位置，形状不变", ha="center",
            fontsize=9.5, color=C_LINE, va="top")

    # 矩阵乘：A @ B.T
    ax = axes[3]
    _draw_cells(ax, A @ B.T, cw=0.85, ch=0.85, fs=10.5, face="#d8f0dc")
    _clean(ax, (-0.7, 3.5), (-1.5, 2.9))
    _title(ax, "A @ B.T  →  (2, 2)", 2.5)
    ax.text(1.35, -0.62, "矩阵乘法\n行 × 列求和，形状会变", ha="center",
            fontsize=9.5, color=C_LINE, va="top")

    fig.suptitle("* 是逐元素相乘（形状不变）；@ 是矩阵乘（内维必须匹配）",
                 fontsize=13.5, fontweight="bold", y=1.02, color=C_TXT)
    _save(fig, "08-乘法的两种.png")


# ============================================================
# 09 · cat 与 stack
# ============================================================
def fig_cat_stack():
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8))
    cw, ch = 0.78, 0.78

    ax = axes[0]
    _draw_cells(ax, [[1, 2], [3, 4]], cw=cw, ch=ch, fs=12)
    _draw_cells(ax, [[5, 6], [7, 8]], oy=2 * ch, cw=cw, ch=ch, fs=12, face=C_HL)
    _clean(ax, (-0.7, 2.4), (-1.1, 4.3))
    _title(ax, "cat(dim=0)  →  (4, 2)", 3.8)
    ax.text(0.85, -0.6, "上下拼：第一个维度相加", ha="center", fontsize=9.5, color=C_LINE)

    ax = axes[1]
    _draw_cells(ax, [[1, 2], [3, 4]], cw=cw, ch=ch, fs=12)
    _draw_cells(ax, [[5, 6], [7, 8]], ox=2 * cw, cw=cw, ch=ch, fs=12, face=C_HL)
    _clean(ax, (-0.7, 4.4), (-1.1, 3.0))
    _title(ax, "cat(dim=1)  →  (2, 4)", 2.6)
    ax.text(1.6, -0.6, "左右拼：第二个维度相加", ha="center", fontsize=9.5, color=C_LINE)

    ax = axes[2]
    off = 0.32
    _draw_cells(ax, [[1, 2], [3, 4]], cw=cw, ch=ch, fs=11, alpha=0.65)
    _draw_cells(ax, [[1, 2], [3, 4]], ox=off, oy=off, cw=cw, ch=ch, fs=11, alpha=0.9,
                face=C_HL)
    _clean(ax, (-0.7, 3.0), (-1.1, 3.0))
    _title(ax, "stack([t, t], dim=0) → (2,2,2)", 2.6)
    ax.text(1.15, -0.6, "新增一个维度\n形状必须完全一致", ha="center",
            fontsize=9.5, color=C_LINE)

    fig.suptitle("cat 在已有维度上拼接（形状可不同）；stack 新增一个维度（形状必须相同）",
                 fontsize=13.5, fontweight="bold", y=1.02, color=C_TXT)
    _save(fig, "09-拼接与堆叠.png")


# ============================================================
# 10 · 归约 sum / mean / max
# ============================================================
def fig_reduction():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.0))
    data = np.array([[1, 2, 3], [4, 5, 6]])
    cw, ch = 0.85, 0.85

    # ---- dim=0：竖着压扁 ----
    ax = axes[0]
    _draw_cells(ax, data, cw=cw, ch=ch, fs=12)
    for j in range(3):
        _draw_cells(ax, [[data[0, j]], [data[1, j]]], ox=j * cw, oy=ch,
                    cw=cw, ch=ch, fs=12, face=C_HL, edge=C_LINE, lw=1.8, alpha=0.95)
    _clean(ax, (-2.6, 3.2), (-3.0, 3.5))
    _title(ax, "x.sum(dim=0)", 3.15)
    ax.text(1.28, 2.72, "(3,4) → (3,)", ha="center", fontsize=10.5,
            family="monospace", color=C_LINE)
    # 每列一个向下小箭头（不穿过矩阵，从矩阵底部指向结果）
    for j in range(3):
        ax.annotate("", xy=(j * cw + cw / 2, -1.02), xytext=(j * cw + cw / 2, -0.12),
                    arrowprops=dict(arrowstyle="-|>", color=C_LINE, lw=2.2))
    ax.text(-1.15, 0.85, "每一列\n各自求和", ha="center", va="center",
            fontsize=10, color=C_LINE)
    _draw_cells(ax, [[5, 7, 9]], oy=-1.62, cw=cw, ch=0.72, fs=11.5, face="#d8f0dc")
    ax.text(1.28, -2.5, "结果：3 个数（列数）", ha="center", fontsize=10.5,
            color="#1a7f37")

    # ---- dim=1：横着压扁 ----
    ax = axes[1]
    _draw_cells(ax, data, cw=cw, ch=ch, fs=12)
    for i in range(2):
        for j in range(3):
            _draw_cells(ax, [[data[i, j]]], ox=j * cw, oy=(1 - i) * ch,
                        cw=cw, ch=ch, fs=12, face=C_HL, edge=C_LINE, lw=1.8,
                        alpha=0.95)
    _clean(ax, (-1.3, 5.0), (-2.6, 3.4))
    _title(ax, "x.sum(dim=1)", 3.05)
    ax.text(2.55, 2.62, "(3,4) → (2,)", ha="center", fontsize=10.5,
            family="monospace", color=C_LINE)
    ax.annotate("", xy=(4.15, 0.85), xytext=(2.65, 0.85),
                arrowprops=dict(arrowstyle="-|>", color=C_LINE, lw=2.4))
    ax.text(1.28, 2.1, "每一行\n各自求和", ha="center", fontsize=10,
            color=C_LINE)
    _draw_cells(ax, [[6], [15]], ox=3.35, cw=0.72, ch=ch, fs=11.5, face="#d8f0dc")
    ax.text(4.0, -1.4, "结果：2 个数\n（行数）", ha="center", fontsize=10.5,
            color="#1a7f37")

    # ---- keepdim ----
    ax = axes[2]
    _draw_cells(ax, data, cw=cw, ch=ch, fs=12)
    _clean(ax, (-1.3, 5.2), (-2.6, 3.4))
    _title(ax, "x.sum(dim=1, keepdim=True)", 3.05)
    ax.text(2.6, 2.62, "(3,4) → (2,1)", ha="center", fontsize=10.5,
            family="monospace", color=C_LINE)
    ax.annotate("", xy=(4.15, 0.85), xytext=(2.65, 0.85),
                arrowprops=dict(arrowstyle="-|>", color=C_LINE, lw=2.4))
    _draw_cells(ax, [[6], [15]], ox=3.35, cw=0.72, ch=ch, fs=11.5, face="#d8f0dc")
    ax.text(2.6, -1.55,
            "keepdim 把被压扁的维度\n保留为长度 1（不是删掉）",
            ha="center", fontsize=10.5, color=C_LINE,
            bbox=dict(fc="#fff1f0", ec="#ffa39e", boxstyle="round,pad=0.45"))

    fig.suptitle("dim 指定「压扁哪一维」：dim=0 竖着压（剩列数），dim=1 横着压（剩行数）",
                 fontsize=13.5, fontweight="bold", y=1.0, color=C_TXT)
    _save(fig, "10-归约.png")


# ============================================================
# 11 · matmul 的形状规则
# ============================================================
def fig_matmul_shape():
    fig, ax = plt.subplots(figsize=(14, 5.2))

    # (2,3) @ (3,4) -> (2,4)
    A_w, A_h = 2.3, 1.7
    B_w, B_h = 3.0, 1.7
    R_w, R_h = 2.3, 1.7
    y = 2.2

    ax.add_patch(plt.Rectangle((0, y), A_w, A_h, fc=C_CELL, ec=C_EDGE, lw=1.6))
    ax.text(A_w / 2, y + A_h / 2 + 0.18, "A", ha="center", fontsize=15, fontweight="bold")
    ax.text(A_w / 2, y + A_h / 2 - 0.22, "(2, 3)", ha="center", fontsize=12,
            family="monospace", color=C_TXT)

    ax.text(A_w + 0.35, y + A_h / 2, "@", ha="center", va="center", fontsize=24, color=C_LINE)

    ax.add_patch(plt.Rectangle((A_w + 0.85, y), B_w, B_h, fc=C_CELL2, ec=C_EDGE, lw=1.6))
    ax.text(A_w + 0.85 + B_w / 2, y + B_h / 2 + 0.18, "B", ha="center",
            fontsize=15, fontweight="bold")
    ax.text(A_w + 0.85 + B_w / 2, y + B_h / 2 - 0.22, "(3, 4)", ha="center",
            fontsize=12, family="monospace", color=C_TXT)

    ax.text(A_w + 0.85 + B_w + 0.35, y + A_h / 2, "=", ha="center", va="center",
            fontsize=24, color=C_LINE)

    ax.add_patch(plt.Rectangle((A_w + 0.85 + B_w + 0.85, y), R_w, R_h,
                               fc="#d8f0dc", ec=C_EDGE, lw=1.6))
    ax.text(A_w + 0.85 + B_w + 0.85 + R_w / 2, y + R_h / 2 + 0.18, "结果",
            ha="center", fontsize=14, fontweight="bold")
    ax.text(A_w + 0.85 + B_w + 0.85 + R_w / 2, y + R_h / 2 - 0.22, "(2, 4)",
            ha="center", fontsize=12, family="monospace", color=C_TXT)

    # 标注内维
    ax.annotate("", xy=(A_w / 2, y - 0.15), xytext=(A_w + 0.85 + B_w / 2, y - 0.15),
                arrowprops=dict(arrowstyle="-", color=C_LINE, lw=2, ls="--"))
    ax.annotate("", xy=(A_w / 2, y - 0.42), xytext=(A_w + 0.85 + B_w / 2, y - 0.42),
                arrowprops=dict(arrowstyle="-", color=C_LINE, lw=2, ls="--"))
    ax.text((A_w + 0.85 + B_w) / 2, y - 0.95,
            "内层维度必须相等（3 = 3），算完就消失",
            ha="center", fontsize=11.5, color=C_LINE, fontweight="bold")

    ax.text(A_w + 0.85 + B_w + 0.85 + R_w / 2, y - 1.0,
            "外层维度\n照抄下来", ha="center", fontsize=11, color="#1a7f37")

    ax.text(0, y + A_h + 1.55,
            "(..., m, k)  @  (..., k, n)  ->  (..., m, n)\n"
            "「内维消掉，外维保留」—— 前面可以有任意多个 batch 维度",
            ha="left", va="top", fontsize=12.5, color=C_TXT, family="monospace",
            bbox=dict(fc="#f6f8fa", ec=C_EDGE, boxstyle="round,pad=0.6"))

    # 常见错误
    ax.text(0, y - 1.75,
            "常见错误（一定报错）：(2,3) @ (2,3)  内维 3 ≠ 2\n"
            "   想看它们的相似度？用 (2,3) @ (2,3).T = (2,2)",
            ha="left", va="top", fontsize=11.5, color=C_TXT, family="monospace",
            bbox=dict(fc="#fff1f0", ec="#ffa39e", boxstyle="round,pad=0.6"))

    ax.set_xlim(-0.4, 11.6)
    ax.set_ylim(-0.2, y + A_h + 3.0)
    ax.set_aspect("equal")
    ax.axis("off")
    _save(fig, "11-matmul形状.png")


# ============================================================
# 12 · 高级索引 gather / index_select
# ============================================================
def fig_gather():
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4))
    data = np.array([[10, 11, 12], [13, 14, 15], [16, 17, 18]])

    ax = axes[0]
    idx = [2, 0]
    _draw_cells(ax, data, cw=0.95, ch=0.85, fs=12)
    for i in range(3):
        if i in idx:
            for j in range(3):
                _draw_cells(ax, [[data[i, j]]], ox=j * 0.95, oy=(2 - i) * 0.85,
                            cw=0.95, ch=0.85, fs=12, face=C_HL, edge=C_LINE, lw=2)
    _clean(ax, (-0.8, 3.6), (-1.2, 3.0))
    _title(ax, "index_select(0, [2, 0])", 2.65)
    ax.text(1.35, -0.75, "按索引「挑行」→ shape (2, 3)", ha="center",
            fontsize=10, color=C_LINE)

    ax = axes[1]
    _draw_cells(ax, data, cw=0.95, ch=0.85, fs=12)
    _clean(ax, (-0.8, 3.6), (-1.2, 3.0))
    _title(ax, "gather / 花式索引", 2.65)
    ax.text(1.35, -0.75, "每行取「不同列」，可任意组合\nx[range(3), [2,0,1]] → (3,)",
            ha="center", fontsize=10, color=C_LINE)

    fig.suptitle("高级索引：index_select 整行/整列地挑；gather 逐个元素地挑",
                 fontsize=13.5, fontweight="bold", y=1.02, color=C_TXT)
    _save(fig, "12-高级索引.png")


# ============================================================
# 13 · 内存布局：contiguous / view
# ============================================================
def fig_contiguous():
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6))
    data = np.arange(1, 7).reshape(2, 3)

    ax = axes[0]
    _draw_cells(ax, data, cw=0.9, ch=0.9, fs=12)
    _clean(ax, (-0.8, 3.4), (-1.3, 2.9))
    _title(ax, "x (2, 3) 内存连续", 2.5)
    ax.text(1.3, -0.75,
            "内存里的实际排列：\n[1][2][3][4][5][6]\n"
            "stride = (3, 1)",
            ha="center", fontsize=10, family="monospace", color=C_TXT,
            bbox=dict(fc="#f6f8fa", ec=C_EDGE, boxstyle="round,pad=0.5"))

    ax = axes[1]
    _draw_cells(ax, data.T, cw=0.9, ch=0.9, fs=12, face=C_HL)
    _clean(ax, (-0.8, 3.4), (-1.3, 2.9))
    _title(ax, "x.T (3, 2) 不再连续", 2.5)
    ax.text(1.3, -0.75,
            "数据没动！只是 stride 变成 (1, 3)\n"
            "所以 .view() 会报错\n"
            "要改形状必须先 .contiguous()",
            ha="center", fontsize=10, family="monospace", color=C_LINE,
            bbox=dict(fc="#fff1f0", ec="#ffa39e", boxstyle="round,pad=0.5"))

    fig.suptitle("view 要求内存连续；reshape 会自动处理副本（更安全但可能有拷贝开销）",
                 fontsize=13, fontweight="bold", y=1.02, color=C_TXT)
    _save(fig, "13-内存连续性.png")


# ============================================================
# 14 · 完整流程：一张图看懂形状变换
# ============================================================
def fig_pipeline():
    fig, ax = plt.subplots(figsize=(16, 5.8))

    steps = [
        ("原始图片", "[3, 224, 224]", "C, H, W", "#eef2f7"),
        ("加 batch 维", "[1, 3, 224, 224]", "unsqueeze(0)", "#dbe7f5"),
        ("卷积/池化", "[1, 64, 56, 56]", "空间下采样", "#dbe7f5"),
        ("展平", "[1, 200704]", "flatten(1)", "#ffe8cc"),
        ("全连接", "[1, 10]", "Linear", "#d8f0dc"),
    ]

    bw, bh = 2.62, 1.55
    y0 = 1.75
    x = 0.0
    for i, (title, shape, op, color) in enumerate(steps):
        ax.add_patch(plt.Rectangle((x, y0), bw, bh, fc=color, ec=C_EDGE, lw=1.6))
        ax.text(x + bw / 2, y0 + bh - 0.30, title, ha="center", fontsize=11.5,
                fontweight="bold")
        ax.text(x + bw / 2, y0 + bh - 0.72, shape, ha="center", fontsize=10.5,
                family="monospace", color=C_TXT)
        ax.text(x + bw / 2, y0 + 0.28, op, ha="center", fontsize=9.5, color=C_LINE,
                family="monospace")

        if i < len(steps) - 1:
            ax.annotate("", xy=(x + bw + 0.42, y0 + bh / 2),
                        xytext=(x + bw + 0.06, y0 + bh / 2),
                        arrowprops=dict(arrowstyle="-|>", color=C_LINE, lw=2.2))
        x += bw + 0.48

    ax.text(0.0, y0 + bh + 0.72,
            "记住一句话：报错先 print(x.shape) —— 90% 的 PyTorch 错误都是形状不对",
            fontsize=13, fontweight="bold", color=C_TXT)

    ax.text(0.0, y0 - 0.55,
            "维度约定：\n"
            "  图像  (N, C, H, W)   —— 批大小、通道、高、宽\n"
            "  序列  (N, L, D) 或 (N, L) —— 批大小、序列长度、特征维\n"
            "  通道优先 (NCHW) 是 PyTorch 的默认；TensorFlow 用 NHWC\n"
            "nn.Linear 只吃最后一维：把 (..., D_in) 变成 (..., D_out)",
            ha="left", va="top", fontsize=11.5, color=C_TXT, family="monospace",
            linespacing=1.75,
            bbox=dict(fc="#f6f8fa", ec=C_EDGE, boxstyle="round,pad=0.65"))

    ax.set_xlim(-0.3, x + 0.1)
    ax.set_ylim(-1.55, y0 + bh + 1.25)
    ax.set_aspect("equal")
    ax.axis("off")
    _save(fig, "14-形状流程.png")


if __name__ == "__main__":
    print("生成可视化图片…")
    fig_dimensions()
    fig_indexing()
    fig_view_reshape()
    fig_transpose_permute()
    fig_squeeze()
    fig_broadcast_row()
    fig_broadcast_shape()
    fig_mul_compare()
    fig_cat_stack()
    fig_reduction()
    fig_matmul_shape()
    fig_gather()
    fig_contiguous()
    fig_pipeline()
    print(f"\n完成，共输出到 {OUT}")
