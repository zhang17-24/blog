/**
 * 学习指南目录扫描
 *
 * 侧边栏不是手写的 —— 每次加载配置时扫描 guides/ 目录自动生成。
 * 新增一个技术只要建目录 + 写 index.md，重启 dev 服务器就会出现在左侧导航里。
 *
 * 支持两种结构，可以混用：
 *
 *   扁平（适合章节少的）：
 *     guides/<技术>/index.md            该技术的概览页
 *     guides/<技术>/01-xxx.md           章节，按文件名排序
 *
 *   两级（适合章节多、要分 Part 的）：
 *     guides/<技术>/index.md            该技术的概览页
 *     guides/<技术>/part1-xxx/index.md  分组页，侧栏显示为可折叠子分组
 *     guides/<技术>/part1-xxx/01-yyy.md 分组内的章节
 *
 * frontmatter 约定：
 *   title  侧栏显示的名字（缺省时退回文件里的第一个 # 标题，再退回文件名）
 *   order  排序，小的在前（只在 index.md 上有意义，缺省 99）
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// config.mts 会被 esbuild 编译到 .vitepress/ 下的临时文件，
// 所以这里用 import.meta.url 定位，而不是 process.cwd()
const HERE = path.dirname(fileURLToPath(import.meta.url))
const GUIDES_DIR = path.resolve(HERE, '../guides')

export interface GuideChapter {
  text: string
  link: string
}

/** 二级分组（Part）。没有子目录的技术这个数组是空的。 */
export interface GuidePart {
  dir: string
  name: string
  order: number
  chapters: GuideChapter[]
}

export interface GuideGroup {
  dir: string
  name: string
  order: number
  /** 直接放在技术目录下的章节 */
  chapters: GuideChapter[]
  /** 子目录分组 */
  parts: GuidePart[]
}

function readFrontmatter(file: string): Record<string, string> {
  try {
    const src = fs.readFileSync(file, 'utf-8')
    const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---/)
    if (!m) return {}
    const out: Record<string, string> = {}
    for (const line of m[1].split(/\r?\n/)) {
      const kv = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/)
      if (kv) out[kv[1]] = kv[2].trim().replace(/^["']|["']$/g, '')
    }
    return out
  } catch {
    return {}
  }
}

/** 优先取 frontmatter.title，其次取第一个一级标题，最后退回文件名 */
function readTitle(file: string): string {
  const fm = readFrontmatter(file)
  if (fm.title) return fm.title
  try {
    const src = fs.readFileSync(file, 'utf-8')
    const h = src.match(/^#\s+(.+)$/m)
    if (h) return h[1].trim()
  } catch {
    /* ignore */
  }
  return path.basename(file, '.md')
}

function readOrder(file: string): number {
  const fm = readFrontmatter(file)
  const n = Number(fm.order)
  return Number.isFinite(n) ? n : 99
}

/**
 * 读一个目录下的章节（*.md），按文件名排序。
 *
 * 排除两类文件：
 *   index.md   目录的概览页，由调用方单独放在分组第一位
 *   README.md  给 GitHub / 维护者看的说明，config.mts 的 srcExclude 已排除它，
 *              VitePress 不会渲染成页面。这里必须一起排除，否则侧边栏会挂上
 *              一个指向不存在页面的死链（点进去 404）。
 */
function readChapters(dirAbs: string, urlBase: string): GuideChapter[] {
  return fs
    .readdirSync(dirAbs, { withFileTypes: true })
    .filter(
      (e) =>
        e.isFile() &&
        e.name.endsWith('.md') &&
        e.name !== 'index.md' &&
        e.name.toLowerCase() !== 'readme.md'
    )
    .map((e) => e.name)
    .sort()
    .map((f) => ({
      text: readTitle(path.join(dirAbs, f)),
      link: `${urlBase}/${f.replace(/\.md$/, '')}`
    }))
}

export function scanGuides(): GuideGroup[] {
  if (!fs.existsSync(GUIDES_DIR)) return []

  return fs
    .readdirSync(GUIDES_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith('.') && d.name !== 'node_modules')
    .map((d) => {
      const abs = path.join(GUIDES_DIR, d.name)
      const indexFile = path.join(abs, 'index.md')
      const hasIndex = fs.existsSync(indexFile)
      const urlBase = `/guides/${d.name}`

      // 子目录 → Part 分组
      const parts: GuidePart[] = fs
        .readdirSync(abs, { withFileTypes: true })
        .filter((e) => e.isDirectory() && !e.name.startsWith('.') && e.name !== 'node_modules')
        .map((e) => {
          const partAbs = path.join(abs, e.name)
          const partIndex = path.join(partAbs, 'index.md')
          const hasPartIndex = fs.existsSync(partIndex)
          return {
            dir: e.name,
            name: hasPartIndex ? readTitle(partIndex) : e.name,
            order: hasPartIndex ? readOrder(partIndex) : 99,
            chapters: readChapters(partAbs, `${urlBase}/${e.name}`)
          }
        })
        // 只保留真有章节的分组，空目录不显示
        .filter((p) => p.chapters.length > 0)
        .sort((a, b) => a.order - b.order || a.dir.localeCompare(b.dir))

      return {
        dir: d.name,
        name: hasIndex ? readTitle(indexFile) : d.name,
        order: hasIndex ? readOrder(indexFile) : 99,
        chapters: readChapters(abs, urlBase),
        parts
      }
    })
    .sort((a, b) => a.order - b.order || a.dir.localeCompare(b.dir))
}

/**
 * 生成 VitePress 侧边栏配置：每个技术一个可折叠分组。
 * 分组下如果有 Part 子目录，再套一层可折叠子分组（标题可点，进该部分的概览页）。
 */
export function buildGuideSidebar() {
  return scanGuides().map((g) => ({
    text: g.name,
    collapsed: true,
    items: [
      { text: '指南概览', link: `/guides/${g.dir}/` },
      ...g.chapters,
      ...g.parts.map((p) => ({
        text: p.name,
        link: `/guides/${g.dir}/${p.dir}/`,
        collapsed: true,
        items: p.chapters
      }))
    ]
  }))
}
