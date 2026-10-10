/**
 * 生成「深度学习进阶」离线单页手册
 *
 *   node guides/deep-learning/build-handbook.mjs
 *
 * 产物：public/downloads/deep-learning-handbook.html（单文件，双击即看，无需网络）
 *
 * 做法是从 VitePress 的**构建产物**里抽正文，而不是重新渲染一遍 Markdown。
 * 好处：
 *   - 公式（KaTeX）、代码高亮（shiki）、表格样式全部和站点一致，不会跑偏
 *   - 不用维护第二套渲染逻辑
 * 代价：必须先 npm run build
 *
 * 原版的 深度学习进阶手册.html 是用 Python-Markdown 单独渲染的，没有数学插件，
 * 320 个公式全是 `$$...$$` 原文。这里改掉。
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const BLOG = path.resolve(HERE, '../..')
const DIST = path.join(BLOG, '.vitepress/dist')
const OUT = path.join(BLOG, 'public/downloads/deep-learning-handbook.html')

if (!fs.existsSync(DIST)) {
  console.error(`找不到构建产物：${DIST}\n先跑 npm run build`)
  process.exit(1)
}

// 离线版的页面顺序（分组名非空时在侧栏插一条分隔标题）
const PAGES = [
  ['index.html', '总览与学习路线', ''],

  ['part1-ml-basics/index.html', 'Part 1 · 机器学习基础', 'Part 1 · 机器学习基础'],
  ['part1-ml-basics/01-what-is-ml.html', '01 机器学习的本质', ''],
  ['part1-ml-basics/02-generalization.html', '02 泛化与偏差方差', ''],
  ['part1-ml-basics/03-regularization.html', '03 正则化与容量控制', ''],
  ['part1-ml-basics/04-optimizers.html', '04 优化器 SGD→AdamW', ''],

  ['part2-dl-principles/index.html', 'Part 2 · 深度学习原理', 'Part 2 · 深度学习原理'],
  ['part2-dl-principles/05-backprop.html', '05 反向传播推导', ''],
  ['part2-dl-principles/06-normalization.html', '06 BatchNorm → RMSNorm', ''],
  ['part2-dl-principles/07-convolution.html', '07 卷积与感受野', ''],
  ['part2-dl-principles/08-residual.html', '08 残差连接与架构', ''],
  ['part2-dl-principles/09-initialization.html', '09 初始化与数值稳定', ''],

  ['part3-transformer/index.html', 'Part 3 · Transformer 与现代 LLM', 'Part 3 · Transformer 与现代 LLM'],
  ['part3-transformer/10-attention.html', '10 Attention 推导', ''],
  ['part3-transformer/11-multi-head-rope.html', '11 多头与 RoPE', ''],
  ['part3-transformer/12-transformer-to-llama.html', '12 从 Transformer 到 LLaMA', ''],
  ['part3-transformer/13-kv-cache-gqa.html', '13 KV Cache 与 GQA', ''],
  ['part3-transformer/14-scaling-laws.html', '14 缩放定律与 FlashAttention', ''],

  ['part4-research/index.html', 'Part 4 · 研究方法论', 'Part 4 · 研究方法论'],
  ['part4-research/15-reading-papers.html', '15 怎么读论文', ''],
  ['part4-research/16-designing-experiments.html', '16 怎么设计实验', ''],

  ['part5-appendix/index.html', 'Part 5 · 附录', 'Part 5 · 附录'],
  ['part5-appendix/17-formula-cheatsheet.html', '17 公式速查表', ''],
  ['part5-appendix/18-interview-questions.html', '18 面试高频问题', '']
].map(([rel, label, group]) => ({
  file: path.join(DIST, 'guides/deep-learning', rel),
  label,
  group,
  // 站点 URL，用于把正文里的站内链接改写成页内锚点。
  // cleanUrls 已开启，所以链接里没有 .html；目录页以 / 结尾。
  url:
    '/guides/deep-learning/' +
    rel.replace(/index\.html$/, '').replace(/\.html$/, '')
}))

const URL2IDX = new Map(PAGES.map((p, i) => [p.url, i]))

// ---------------------------------------------------------------- 正文抽取

/** 从 start 位置的 <div 开始，按标签配对找到它的闭合位置 */
function sliceBalancedDiv(html, start) {
  const re = /<div\b|<\/div>/g
  re.lastIndex = start
  let depth = 0
  let m
  while ((m = re.exec(html))) {
    if (m[0] === '<div') depth++
    else if (--depth === 0) return html.slice(start, m.index + '</div>'.length)
  }
  throw new Error('div 未闭合')
}

function extractDoc(html, file) {
  const marker = html.indexOf('class="vp-doc ')
  if (marker < 0) throw new Error(`没找到 vp-doc：${file}`)
  const start = html.lastIndexOf('<div', marker)
  return sliceBalancedDiv(html, start)
}

function clean(html) {
  return (
    html
      // 标题旁的 ¶ 锚点链接
      .replace(/<a class="header-anchor"[^>]*>[\s\S]*?<\/a>/g, '')
      // 代码块上的「复制」按钮 —— 离线版没有 VitePress 的 JS，点了没反应
      .replace(/<button[^>]*class="copy"[^>]*><\/button>/g, '')
      // 构建时注入的 scoped 属性
      .replace(/\s+data-v-[0-9a-f]+(="")?/g, '')
      // VitePress 客户端渲染留下的注释占位
      .replace(/<!--\[-->|<!--\]-->|<!---->/g, '')
  )
}

function rewriteLinks(html) {
  return html.replace(/href="([^"]+)"/g, (whole, href) => {
    // 站内指南链接 -> 页内锚点
    if (href.startsWith('/guides/deep-learning')) {
      const base = href.split('#')[0]
      const idx = URL2IDX.get(base)
      return idx === undefined ? whole : `href="#${idx}"`
    }
    // 下载文件 -> 与手册同目录，用相对路径
    if (href.startsWith('/downloads/')) {
      return `href="${href.slice('/downloads/'.length)}"`
    }
    return whole
  })
}

// ---------------------------------------------------------------- 样式

const cssFile = fs
  .readdirSync(path.join(DIST, 'assets'))
  .find((f) => f.startsWith('style.') && f.endsWith('.css'))
if (!cssFile) throw new Error('没找到打包后的 CSS')

/** 只内联真正用得到的字体，其余 @font-face 整个丢掉（浏览器回落到系统字体） */
function inlineFonts(css) {
  const KEEP = /^KaTeX_|^inter-(roman|italic)-latin\./
  let inlined = 0
  let dropped = 0
  const out = css.replace(/@font-face\s*\{[^}]*\}/g, (block) => {
    const m = block.match(/url\(["']?\/assets\/([^"')]+\.woff2)["']?\)/)
    if (!m || !KEEP.test(m[1])) {
      dropped++
      return ''
    }
    const fontPath = path.join(DIST, 'assets', m[1])
    if (!fs.existsSync(fontPath)) {
      dropped++
      return ''
    }
    inlined++
    const b64 = fs.readFileSync(fontPath).toString('base64')
    // 只留 woff2，砍掉 woff / ttf 回退（现代浏览器都支持 woff2）。
    // 注意 [^;}]+ 而不是 [^;]+ —— src 常常是块里最后一个属性，后面直接跟 }，
    // 没有分号，只匹配分号会漏掉。
    return block.replace(
      /src:[^;}]+/,
      `src:url(data:font/woff2;base64,${b64}) format("woff2")`
    )
  })
  console.log(`  字体：内联 ${inlined} 个，丢弃 ${dropped} 个（用不到的字重/字符集）`)
  return out
}

const siteCss = inlineFonts(fs.readFileSync(path.join(DIST, 'assets', cssFile), 'utf8'))

const LAYOUT_CSS = `
#hb-side{position:fixed;inset:0 auto 0 0;width:276px;overflow-y:auto;padding:20px 0 48px;
  background:var(--vp-c-bg-alt);border-right:1px solid var(--vp-c-divider);z-index:20}
#hb-side::-webkit-scrollbar{width:6px}
#hb-side::-webkit-scrollbar-thumb{background:var(--vp-c-divider);border-radius:3px}
.hb-brand{padding:0 20px 16px;font-size:16px;font-weight:700;color:var(--vp-c-text-1)}
.hb-brand small{display:block;margin-top:2px;font-size:11.5px;font-weight:400;color:var(--vp-c-text-3)}
.hb-sep{margin:16px 20px 6px;font-size:11px;font-weight:700;letter-spacing:.06em;
  color:var(--vp-c-text-3);text-transform:uppercase}
.hb-item{display:block;padding:6px 20px;font-size:13.8px;line-height:1.5;text-decoration:none;
  color:var(--vp-c-text-2);border-left:2px solid transparent}
.hb-item:hover{background:var(--vp-c-default-soft);color:var(--vp-c-text-1)}
.hb-item.on{background:var(--vp-c-brand-soft);color:var(--vp-c-brand-1);
  border-left-color:var(--vp-c-brand-1);font-weight:600}
#hb-main{margin-left:276px;padding:0 0 120px}
.hb-page{display:none;max-width:860px;margin:0 auto;padding:40px 40px 0}
.hb-page.on{display:block}
#hb-bar{position:fixed;top:0;right:0;left:276px;z-index:15;display:flex;
  justify-content:flex-end;gap:8px;padding:9px 22px;background:var(--vp-c-bg);
  border-bottom:1px solid var(--vp-c-divider)}
.hb-btn{border:1px solid var(--vp-c-divider);background:var(--vp-c-bg);color:var(--vp-c-text-2);
  border-radius:6px;padding:4px 11px;font-size:12.5px;cursor:pointer;font-family:inherit}
.hb-btn:hover{background:var(--vp-c-bg-alt);color:var(--vp-c-text-1)}
#hb-menu{display:none}
.hb-page .vp-doc{padding-top:14px}
@media (max-width:900px){
  #hb-side{transform:translateX(-100%);transition:.2s}
  #hb-side.open{transform:none}
  #hb-main{margin-left:0}
  #hb-bar{left:0}
  #hb-menu{display:inline-block}
  .hb-page{padding:24px 18px 0}
}
`

// ---------------------------------------------------------------- 组装

const pages = PAGES.map((p) => {
  if (!fs.existsSync(p.file)) throw new Error(`缺少构建产物：${p.file}`)
  const html = rewriteLinks(clean(extractDoc(fs.readFileSync(p.file, 'utf8'), p.file)))
  return { label: p.label, group: p.group, html }
})

const navHtml = pages
  .map((p, i) => {
    const sep = p.group ? `<div class="hb-sep">${p.group}</div>` : ''
    return `${sep}<a class="hb-item" href="#${i}" data-i="${i}">${p.label}</a>`
  })
  .join('\n')

const bodyHtml = pages
  .map((p, i) => `<div class="hb-page" id="hb-p${i}"><div class="vp-doc">${p.html}</div></div>`)
  .join('\n')

const out = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>深度学习进阶 · 离线手册</title>
<style>${siteCss}</style>
<style>${LAYOUT_CSS}</style>
</head>
<body>
<aside id="hb-side">
  <div class="hb-brand">深度学习进阶<small>从原理到研究方法 · 离线手册</small></div>
  ${navHtml}
</aside>
<div id="hb-bar">
  <button class="hb-btn" id="hb-menu">☰ 目录</button>
  <button class="hb-btn" onclick="scrollTo({top:0,behavior:'smooth'})">↑ 顶部</button>
</div>
<main id="hb-main">
${bodyHtml}
</main>
<script>
var pages = document.querySelectorAll('.hb-page')
var items = document.querySelectorAll('.hb-item')
function route() {
  var i = parseInt(location.hash.slice(1))
  if (isNaN(i) || i >= pages.length) i = 0
  pages.forEach(function (el, j) { el.classList.toggle('on', j === i) })
  items.forEach(function (el, j) { el.classList.toggle('on', j === i) })
  scrollTo(0, 0)
  document.getElementById('hb-side').classList.remove('open')
}
addEventListener('hashchange', route)
document.getElementById('hb-menu').onclick = function () {
  document.getElementById('hb-side').classList.toggle('open')
}
route()
</script>
</body>
</html>
`

fs.mkdirSync(path.dirname(OUT), { recursive: true })
fs.writeFileSync(OUT, out)
console.log(`生成：${path.relative(BLOG, OUT)}  (${(out.length / 1024 / 1024).toFixed(2)} MB, ${pages.length} 页)`)
