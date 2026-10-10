# 深度学习进阶 · 维护说明

> 内部文档，放在 `docs/` 下（`srcExclude` 已排除整个 `docs/`），不参与站点构建。
>
> 注意：**不要**把它放回 `guides/deep-learning/`。`guides.data.ts` 里的
> `createContentLoader('guides/**/*.md')` 会扫到同目录下所有 .md，
> 放在那边会被当成一章算进「共 N 篇」的计数里。

## 来源与文件映射

内容来自 `WorkBuddy/2026-10-06-00-32-08/深度学习进阶/`。
原始文件名是中文，搬进站点时改成了 ASCII slug —— 因为站点里其他指南和博客文章
（`01-basics.md`、`caddy-vs-nginx.md`）全部用 ASCII，保持一致，URL 和 RSS 也干净。

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
| `深度学习进阶手册.html` | `public/downloads/deep-learning-handbook.html` |

正文内容**一字未改**，只做了三件事：

1. 每篇头部加了 frontmatter（`title` 取自一级标题、`description` 取自「核心问题」那行）
2. 内部相对链接改成站点内绝对链接（原文是 `Part1-机器学习基础/01-xxx.md` 这种，
   在站点里会 404）
3. 原文有几处畸形相对路径（如 `Part2/../Part2-深度学习原理/05-xxx.md`）按文件名兜底修正了

## 结构

```
guides/deep-learning/
├── index.md                  指南入口（原 README）
├── part1-ml-basics/          Part 1，章节 01-04
├── part2-dl-principles/      Part 2，章节 05-09
├── part3-transformer/        Part 3，章节 10-14
├── part4-research/           Part 4，章节 15-16
├── part5-appendix/           Part 5，章节 17-18
└── build-handbook.mjs        重新生成离线单页版
```

每个 Part 目录下的 `index.md` 是该部分的概览页，侧边栏里显示为可折叠子分组，
点分组标题就进这个页面。

## 离线单页版怎么重新生成

`public/downloads/deep-learning-handbook.html`（约 3.3 MB）是给离线/无网场景用的单文件版。

**正文改动后必须重新生成**，否则它和站点内容会对不上：

```bash
npm run build                              # 先构建站点
node guides/deep-learning/build-handbook.mjs
```

脚本从 `.vitepress/dist/` 里**抽取**已经渲染好的正文，而不是重新渲染一遍 Markdown。
这样公式（KaTeX）、代码高亮（shiki）、行号、表格样式和站点完全一致，
也不会出现两套渲染逻辑各自跑偏。代价是必须先 `npm run build`。

> 最初的 `深度学习进阶手册.html` 是用 Python-Markdown 单独渲染的，没挂数学插件，
> 320 个公式全是 `$$...$$` 原文 —— 等于一份坏掉的离线版。所以换掉了。

脚本会内联 KaTeX 和 Inter 的 woff2 字体（21 个），其余 17 个字重/字符集整个丢掉。
体积主要来自 KaTeX 的 HTML 输出（每个字形都是嵌套 span），这是它固有的开销。

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

## 命名为什么是英文

原始文件名是中文（`Part1-机器学习基础/01-机器学习的本质.md`），
站点里统一改成了 ASCII slug（`part1-ml-basics/01-what-is-ml.md`），
因为其他指南和博客文章全部用 ASCII，保持一致，URL 和 RSS/sitemap 也干净。

正文里的一级标题（`# 1 · 机器学习的本质是什么`）保持中文不变，读者看到的还是中文。
