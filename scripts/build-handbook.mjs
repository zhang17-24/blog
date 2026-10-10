/**
 * 生成各套指南的「离线单页手册」
 *
 *   node scripts/build-handbook.mjs            # 全部
 *   node scripts/build-handbook.mjs pytorch    # 只生成某一套
 *
 * 产物：public/downloads/<名字>-handbook.html
 * 单文件，双击即看，不需要网络，也不需要站点在跑。
 *
 * 做法是从 VitePress 的**构建产物**里抽正文，而不是重新渲染一遍 Markdown：
 *   - 公式（KaTeX）、代码高亮（shiki）、表格样式全部和站点一致，不会跑偏
 *   - 不用维护第二套渲染逻辑
 * 代价：必须先 npm run build
 *
 * 目录树直接从 guides/ 源目录扫出来，和站点侧栏用同一份 frontmatter，
 * 所以新增章节不用改这里。
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const BLOG = path.resolve(HERE, '..')
const DIST = path.join(BLOG, '.vitepress/dist')
const SRC = path.join(BLOG, 'guides')
const DOWNLOADS = path.join(BLOG, 'public/downloads')

if (!fs.existsSync(DIST)) {
  console.error(`找不到构建产物：${DIST}\n先跑 npm run build`)
  process.exit(1)
}

// 站点地址（跨指南的链接在离线版里指回线上）
const SITE_URL = (() => {
  const m = fs.readFileSync(path.join(BLOG, '.vitepress/site.ts'), 'utf8')
    .match(/SITE_URL\s*=\s*['"]([^'"]+)['"]/)
  return m ? m[1].replace(/\/$/, '') : ''
})()

/** 每套指南的配置。pages 由 scan() 从源目录自动扫出来。 */
const GUIDES = {
  'deep-learning': {
    out: 'deep-learning-handbook.html',
    title: '深度学习进阶',
    sub: '从原理到研究方法 · 离线手册'
  },
  pytorch: {
    out: 'pytorch-handbook.html',
    title: 'PyTorch 入门学习笔记',
    sub: '从张量到完整训练脚本 · 离线手册'
  },
  'tensor-ops': {
    out: 'tensor-ops-handbook.html',
    title: '张量运算图解',
    sub: '14 张图讲清形状问题 · 离线手册',
    // 图要内联成 base64，否则单文件带不走
    inlineImages: true
  }
}

// ---------------------------------------------------------------- 扫目录

function frontmatter(file) {
  const src = fs.readFileSync(file, 'utf8')
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---/)
  const out = {}
  if (m) {
    for (const line of m[1].split(/\r?\n/)) {
      const kv = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/)
      if (kv) out[kv[1]] = kv[2].trim().replace(/^["']|["']$/g, '')
    }
  }
  return out
}

function titleOf(file) {
  const fm = frontmatter(file)
  if (fm.title) return fm.title
  const h = fs.readFileSync(file, 'utf8').match(/^#\s+(.+)$/m)
  return h ? h[1].trim() : path.basename(file, '.md')
}

/** 扫出与站点侧栏一致的页面顺序 */
function scan(guide) {
  const root = path.join(SRC, guide)
  const dirs = fs.readdirSync(root, { withFileTypes: true })
  const parts = dirs
    .filter((e) => e.isDirectory() && !e.name.startsWith('.'))
    .map((e) => e.name)
    .sort()
  const chapters = dirs
    .filter((e) => e.isFile() && e.name.endsWith('.md') && !/^(index|readme)\.md$/i.test(e.name))
    .map((e) => e.name)
    .sort()

  const pages = [{ rel: 'index.html', label: '总览与学习路线', group: '' }]
  for (const f of chapters) {
    pages.push({
      rel: f.replace(/\.md$/, '.html'),
      label: titleOf(path.join(root, f)),
      group: ''
    })
  }
  for (const d of parts) {
    const pd = path.join(root, d)
    if (!fs.existsSync(path.join(pd, 'index.md'))) continue
    const name = titleOf(path.join(pd, 'index.md'))
    pages.push({ rel: `${d}/index.html`, label: name, group: name })
    const inner = fs
      .readdirSync(pd)
      .filter((f) => f.endsWith('.md') && !/^(index|readme)\.md$/i.test(f))
      .sort()
    for (const f of inner) {
      pages.push({
        rel: `${d}/${f.replace(/\.md$/, '.html')}`,
        label: titleOf(path.join(pd, f)),
        group: ''
      })
    }
  }
  // cleanUrls 已开启，链接里没有 .html；目录页以 / 结尾
  //
  // 注意不能简单 replace(/index\.html$/,'') —— 章节名也可能以 index 结尾
  // （比如 09-advanced-index.html），那样会被误截成 09-advanced-。
  const toUrl = (rel) => {
    if (rel === 'index.html') return ''
    if (rel.endsWith('/index.html')) return rel.slice(0, -'index.html'.length)
    return rel.replace(/\.html$/, '')
  }
  return pages.map((p) => ({
    ...p,
    file: path.join(DIST, 'guides', guide, p.rel),
    url: `/guides/${guide}/${toUrl(p.rel)}`
  }))
}

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

const IMG_MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp' }

function rewriteLinks(html, guide, url2idx, inlineImages) {
  let n = 0
  html = html.replace(/href="([^"]+)"/g, (whole, href) => {
    // 本指南内 -> 页内锚点
    if (href.startsWith(`/guides/${guide}`)) {
      const idx = url2idx.get(href.split('#')[0])
      return idx === undefined ? whole : `href="#${idx}"`
    }
    // 下载文件 -> 与手册同目录，用相对路径
    if (href.startsWith('/downloads/')) {
      return `href="${href.slice('/downloads/'.length)}"`
    }
    // 别的指南 / 其他站内页 -> 指回线上站点（离线时点不开，但不会指向死路径）
    if (href.startsWith('/') && SITE_URL) {
      return `href="${SITE_URL}${href}"`
    }
    return whole
  })

  if (inlineImages) {
    html = html.replace(/src="(\/figs\/[^"]+)"/g, (whole, src) => {
      const file = path.join(BLOG, 'public', src.replace(/^\//, ''))
      const mime = IMG_MIME[path.extname(file).toLowerCase()]
      if (!mime || !fs.existsSync(file)) return whole
      n++
      return `src="data:${mime};base64,${fs.readFileSync(file).toString('base64')}"`
    })
  }
  return { html, inlined: n }
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
.hb-page img{max-width:100%;height:auto}
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

function build(guide) {
  const cfg = GUIDES[guide]
  const pages = scan(guide)
  const url2idx = new Map(pages.map((p, i) => [p.url, i]))

  let inlinedImgs = 0
  const docs = pages.map((p) => {
    if (!fs.existsSync(p.file)) throw new Error(`缺少构建产物：${p.file}`)
    const raw = clean(extractDoc(fs.readFileSync(p.file, 'utf8'), p.file))
    const { html, inlined } = rewriteLinks(raw, guide, url2idx, cfg.inlineImages)
    inlinedImgs += inlined
    return { label: p.label, group: p.group, html }
  })

  const navHtml = docs
    .map((p, i) => {
      const sep = p.group ? `<div class="hb-sep">${p.group}</div>` : ''
      return `${sep}<a class="hb-item" href="#${i}" data-i="${i}">${p.label}</a>`
    })
    .join('\n')

  const bodyHtml = docs
    .map((p, i) => `<div class="hb-page" id="hb-p${i}"><div class="vp-doc">${p.html}</div></div>`)
    .join('\n')

  const out = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${cfg.title} · 离线手册</title>
<style>${siteCss}</style>
<style>${LAYOUT_CSS}</style>
</head>
<body>
<aside id="hb-side">
  <div class="hb-brand">${cfg.title}<small>${cfg.sub}</small></div>
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

  fs.mkdirSync(DOWNLOADS, { recursive: true })
  const outFile = path.join(DOWNLOADS, cfg.out)
  fs.writeFileSync(outFile, out)
  const extra = cfg.inlineImages ? `，内联 ${inlinedImgs} 张图` : ''
  console.log(
    `生成：public/downloads/${cfg.out}  ` +
    `(${(out.length / 1024 / 1024).toFixed(2)} MB, ${docs.length} 页${extra})`
  )
}

const want = process.argv.slice(2)
const targets = want.length ? want : Object.keys(GUIDES)
for (const g of targets) {
  if (!GUIDES[g]) {
    console.error(`未知指南：${g}（可选：${Object.keys(GUIDES).join(' / ')}）`)
    process.exit(1)
  }
  console.log(`\n=== ${g} ===`)
  build(g)
}
