# 学习指南 · 维护说明

> 内部文档，放在 `docs/` 下（`srcExclude` 已排除整个 `docs/`），不参与站点构建。
>
> 注意：**不要**把维护说明放回 `guides/<技术>/` 下。`guides.data.ts` 里的
> `createContentLoader('guides/**/*.md')` 会扫到同目录下所有 .md，
> 放在那边会被当成一章算进「共 N 篇」的计数里。

## 三套指南是一套学习路径

| # | 指南 | 目录 | 章节 | 定位 |
| --- | --- | --- | --- | --- |
| 1 | 张量运算图解 | `guides/tensor-ops/` | 14 | 形状问题看图，最先读 |
| 2 | PyTorch 入门学习笔记 | `guides/pytorch/` | 12 | API 与完整训练流程 |
| 3 | 深度学习进阶 | `guides/deep-learning/` | 18 | 原理推导，到 Transformer 与 LLaMA |

侧栏顺序由各 `index.md` 的 `order` 决定（1 / 2 / 3）。
后面 7 个指南（Rust 4、Python 5、Docker 6、Git 7、SQL 8、Linux 9、Go 10）依次排在其后。
**改顺序只改这一个数字。**

三份 `index.md` 末尾都有「配套材料」小节互相链接，改动时一起维护。

## 命名为什么是 ASCII

原始文件名是中文（`章节/01-张量.md`、`Part1-机器学习基础/01-机器学习的本质.md`），
站点里统一改成 ASCII slug（`part2-tutorial/01-tensor.md`、`part1-ml-basics/01-what-is-ml.md`），
因为其他指南和博客文章全部用 ASCII，保持一致，URL 和 RSS/sitemap 也干净。

正文里的一级标题保持中文不变，读者看到的还是中文。

---

## 1. 张量运算图解

来源：`WorkBuddy/2026-10-06-00-32-08/张量运算图解/`

原文是**一篇 1165 行的长文**（13 个编号小节 + 附录），搬进站点时按小节拆成了 14 页，
标题层级整体上提一级（`##` → `#`），并保持原文的编号（正文里的「第 5 节」这类
交叉引用改成了页面链接）。

| 原文章节 | 站点路径 |
| --- | --- |
| 前言 + 为什么 + 目录 | `index.md` |
| 1. 张量与维度 | `01-dims.md` |
| 2. 索引与切片 | `02-indexing.md` |
| 3. 形状变换 | `03-shape.md` |
| 4. 增删维度 | `04-squeeze.md` |
| 5. 广播机制 | `05-broadcasting.md` |
| 6. 矩阵运算 | `06-matrix.md` |
| 7. 拼接与堆叠 | `07-cat-stack.md` |
| 8. 归约操作 | `08-reduction.md` |
| 9. 高级索引 | `09-advanced-index.md` |
| 10. 内存布局 | `10-memory.md` |
| 11. 完整流程 | `11-pipeline.md` |
| 12. 高频报错对照表 | `12-errors.md` |
| 13. 练习题 | `13-exercises.md` |
| 附录：一页速查 | `14-cheatsheet.md` |
| `figs/*.png`（14 张） | `public/figs/tensor-ops/*.png`（改了 ASCII 名） |
| `make_figs.py` | `public/downloads/tensor-ops-make-figs.py` |
| `verify.py` | `public/downloads/tensor-ops-verify.py` |
| `张量运算图解手册.html` | `public/downloads/tensor-ops-handbook.html`（重新生成） |

### ⚠️ 原文有个必须记住的坑：LaTeX 被转义展开过

原文 `README.md` 里有 3 个 FF、1 个 CR、2 个 TAB 控制字符，全部落在第 11 节的两个公式里：

| 原文实际存的 | 应该是 | 原因 |
| --- | --- | --- |
| `FF` + `rac` | `\frac` | `\f` 被当成换页符展开 |
| `CR` + `floor` | `\rfloor` | `\r` 被当成回车展开 |
| `TAB` + `ext` | `\text` | `\t` 被当成制表符展开 |

**这份内容是从某个把 `\t`/`\f`/`\r` 当真转义符处理过的中间产物导出的。**
如果以后重新导入，一定要先查控制字符：

```bash
python3 -c "
raw = open('README.md', encoding='utf-8', newline='').read()
print({c: raw.count(c) for c in '\t\f\r\v\b' if c in raw})"
```

注意必须用 `newline=''` 打开 —— 默认的通用换行模式会把 `CR` 转成 `\n`，
让它伪装成一个正常换行，从行号上根本看不出来。

---

## 2. PyTorch 入门学习笔记

来源：`WorkBuddy/2026-10-06-00-32-08/PyTorch入门学习笔记/`

13 个 md 按「起步 / 官方教程 8 章 / 动手与附录」分成 3 个 Part：

| 原始文件 | 站点路径 |
| --- | --- |
| `README.md` | `index.md` |
| `00-环境安装与运行方式.md` | `part1-basics/01-setup.md` |
| `01-先看懂整件事.md` | `part1-basics/02-big-picture.md` |
| `章节/01-张量.md` | `part2-tutorial/01-tensor.md` |
| `章节/02-数据集与数据加载器.md` | `part2-tutorial/02-dataset.md` |
| `章节/03-数据变换.md` | `part2-tutorial/03-transforms.md` |
| `章节/04-构建模型.md` | `part2-tutorial/04-build-model.md` |
| `章节/05-自动微分.md` | `part2-tutorial/05-autograd.md` |
| `章节/06-优化模型参数.md` | `part2-tutorial/06-optimization.md` |
| `章节/07-保存与加载模型.md` | `part2-tutorial/07-save-load.md` |
| `章节/08-快速入门.md` | `part2-tutorial/08-quickstart.md` |
| `练习清单.md` | `part3-practice/01-exercises.md` |
| `速查表.md` | `part3-practice/02-cheatsheet.md` |
| `代码/fashion_mnist.py` | `public/downloads/pytorch-fashion-mnist.py` |
| `代码/exercises.py` | `public/downloads/pytorch-exercises.py` |
| `PyTorch学习手册.html` | `public/downloads/pytorch-handbook.html`（重新生成） |

三个 Part 的概览页（`part*/index.md`）是**新写的**，源里没有。

### 原文的两处缺陷（搬运时修掉了）

1. **死链**：`章节/08-快速入门.md` 里引用了 `代码/mini_image_classifier.py`，
   但这个文件在整个工作区都不存在。链接文字保留、链接去掉。
2. **HTML 标签不配对**：`章节/05-自动微分.md` 的「练习 5」缺 `<details>` 开头，
   却多了一个 `</details>` 收尾（其余 4 题都是配对完整的），
   Vue 编译器会直接报 `Invalid end tag` 让构建失败。搬运时补上了开头。

---

## 3. 深度学习进阶

来源：`WorkBuddy/2026-10-06-00-32-08/深度学习进阶/`

| 原始文件 | 站点路径 |
| --- | --- |
| `README.md` | `index.md` |
| `Part1-机器学习基础/01-机器学习的本质.md` | `part1-ml-basics/01-what-is-ml.md` |
| `Part1-机器学习基础/02-泛化过拟合与偏差方差.md` | `part1-ml-basics/02-generalization.md` |
| `Part1-机器学习基础/03-正则化与容量控制.md` | `part1-ml-basics/03-regularization.md` |
| `Part1-机器学习基础/04-优化器从SGD到AdamW.md` | `part1-ml-basics/04-optimizers.md` |
| `Part2-深度学习原理/05-反向传播的完整推导.md` | `part2-dl-principles/05-backprop.md` |
| `Part2-深度学习原理/06-归一化.md` | `part2-dl-principles/06-normalization.md` |
| `Part2-深度学习原理/07-卷积与感受野.md` | `part2-dl-principles/07-convolution.md` |
| `Part2-深度学习原理/08-残差连接与架构.md` | `part2-dl-principles/08-residual.md` |
| `Part2-深度学习原理/09-初始化与数值稳定.md` | `part2-dl-principles/09-initialization.md` |
| `Part3-Transformer/10-Attention的数学推导.md` | `part3-transformer/10-attention.md` |
| `Part3-Transformer/11-多头注意力与位置编码.md` | `part3-transformer/11-multi-head-rope.md` |
| `Part3-Transformer/12-从Transformer到LLaMA.md` | `part3-transformer/12-transformer-to-llama.md` |
| `Part3-Transformer/13-推理优化KVCache与GQA.md` | `part3-transformer/13-kv-cache-gqa.md` |
| `Part3-Transformer/14-缩放定律与高效注意力.md` | `part3-transformer/14-scaling-laws.md` |
| `Part4-研究方法/15-怎么读一篇论文.md` | `part4-research/15-reading-papers.md` |
| `Part4-研究方法/16-怎么设计实验.md` | `part4-research/16-designing-experiments.md` |
| `公式速查表.md` | `part5-appendix/17-formula-cheatsheet.md` |
| `面试高频问题.md` | `part5-appendix/18-interview-questions.md` |
| `代码/llama_from_scratch.py` | `public/downloads/llama_from_scratch.py` |
| `深度学习进阶手册.html` | `public/downloads/deep-learning-handbook.html`（重新生成） |

正文内容**一字未改**，只做了三件事：

1. 每篇头部加了 frontmatter（`title` 取自一级标题、`description` 取自「核心问题」那行）
2. 内部相对链接改成站点内绝对链接（原文是 `Part1-机器学习基础/01-xxx.md` 这种，在站点里会 404）
3. 原文有几处畸形相对路径（如 `Part2/../Part2-深度学习原理/05-xxx.md`）按文件名兜底修正了

---

## 离线单页手册（三套共用）

`public/downloads/*-handbook.html` 是给离线 / 无网场景用的单文件版：

| 文件 | 体积 | 页数 |
| --- | --- | --- |
| `deep-learning-handbook.html` | 3.3 MB | 24 |
| `pytorch-handbook.html` | 1.2 MB | 16 |
| `tensor-ops-handbook.html` | 2.3 MB | 15（14 张图已内联 base64） |

**正文改动后必须重新生成**，否则它和站点内容会对不上：

```bash
npm run build                      # 先构建站点
node scripts/build-handbook.mjs            # 全部三套
node scripts/build-handbook.mjs pytorch    # 只生成某一套
```

脚本从 `.vitepress/dist/` 里**抽取**已经渲染好的正文，而不是重新渲染一遍 Markdown。
这样公式（KaTeX）、代码高亮（shiki）、行号、表格样式和站点完全一致，
也不会出现两套渲染逻辑各自跑偏。代价是必须先 `npm run build`。

页面清单和侧栏标签是**从 `guides/` 源目录扫出来的**（和站点侧栏读同一份 frontmatter），
所以新增章节不用改脚本。

处理规则：

- 本指南内的链接 → 页内锚点 `#N`
- `/downloads/*.py` → 相对路径（手册就在 `downloads/` 里，点得开）
- 跨指南链接 → 拼上站点地址指回线上（离线时点不开，但不会指向死路径）
- `tensor-ops` 的图 → 内联成 base64（否则单文件带不走）
- 内联 KaTeX 与 Inter 的 woff2 字体 21 个，其余 17 个字重/字符集整个丢掉

> 三份原始 `*手册.html` 都是用 Python-Markdown 单独渲染的，没挂数学插件，
> 公式全是 `$$...$$` 原文 —— 等于坏掉的离线版。所以全部换掉了。

## 依赖

数学公式靠 KaTeX 渲染：

- `@vscode/markdown-it-katex` + `katex`（devDependencies）
- 插件在 `.vitepress/config.mts` 的 `markdown.config` 里注册
- 样式在 `.vitepress/theme/index.ts` 里 `import 'katex/dist/katex.min.css'`

**两者缺一不可**：只装插件不引样式，公式会渲染成没有排版的裸 HTML。

另外 `config.mts` 里有两个和这批内容直接相关的设置：

- `ignoreDeadLinks: [/^\/downloads\//]` —— 否则指向 `.py` 的链接会被判死链，构建直接失败
  （VitePress 的静态资源白名单里没有 `.py`，会拿它当页面去找 `xxx.py.html`）
- `markdown.config` 里的 `strict` —— 正文有 `\text{欠拟合}` 这类写法，
  只忽略 `unicodeTextInMathMode` 这一类警告，其他语法问题照常报

## 搬运脚本

三个 Python 脚本完成了「复制 + 改名 + 补 frontmatter + 重写链接」，
它们是**一次性的**，不在仓库里。重新导入时按上面各节的映射表重写即可。

## 搬运时统一做的排版修正

正文内容保持原样，只修了两类**在页面上能明显看出来的缺陷**：

1. **代码块里注释紧贴代码**：原文有 17 处写成 `x.dtype# torch.int64`、
   `optimizer.step()# 3. 更新`、`bw = 2e12# A100 显存带宽`，
   渲染出来很难看。只在 ``` 代码块内给 `#` 前补一个空格，不碰正文。
   涉及 `pytorch/part2-tutorial/01-tensor.md`、`part3-practice/02-cheatsheet.md`、
   `part2-tutorial/05-autograd.md`，以及 `deep-learning` 的 7 个文件。
2. **HTML 标签不配对 / 死链**：见上面各节的说明。

排查命令（必须用 Python，`grep` 的字符类在这类模式上会漏）：

```bash
python3 -c "
import re, pathlib
for f in sorted(pathlib.Path('guides').rglob('*.md')):
    for i, l in enumerate(f.read_text(encoding='utf-8').split('\n'), 1):
        if re.search(r'[A-Za-z0-9_)\]]#[ \u4e00-\u9fa5]', l):
            print(f'{f}:{i}: {l}')"
```
