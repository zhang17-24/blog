/**
 * 学习指南目录扫描
 *
 * 侧边栏不是手写的 —— 每次加载配置时扫描 guides/ 目录自动生成。
 * 新增一个技术只要建目录 + 写 index.md，重启 dev 服务器就会出现在左侧导航里。
 *
 * 约定：
 *   guides/<技术>/**index.md**   该技术的概览页，frontmatter 的 title 作为侧栏分组名，
 *                                order 控制分组排序（小的在前）
 *   guides/<技术>/01-xxx.md      章节，按文件名排序（用数字前缀控制顺序），
 *                                frontmatter 的 title 作为侧栏条目标题
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

export interface GuideGroup {
  dir: string
  name: string
  order: number
  chapters: GuideChapter[]
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

export function scanGuides(): GuideGroup[] {
  if (!fs.existsSync(GUIDES_DIR)) return []

  return fs
    .readdirSync(GUIDES_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith('.') && d.name !== 'node_modules')
    .map((d) => {
      const abs = path.join(GUIDES_DIR, d.name)
      const indexFile = path.join(abs, 'index.md')
      const hasIndex = fs.existsSync(indexFile)

      const chapters = fs
        .readdirSync(abs)
        .filter((f) => f.endsWith('.md') && f !== 'index.md')
        .sort()
        .map((f) => ({
          text: readTitle(path.join(abs, f)),
          link: `/guides/${d.name}/${f.replace(/\.md$/, '')}`
        }))

      return {
        dir: d.name,
        name: hasIndex ? readTitle(indexFile) : d.name,
        order: hasIndex ? readOrder(indexFile) : 99,
        chapters
      }
    })
    .sort((a, b) => a.order - b.order || a.dir.localeCompare(b.dir))
}

/** 生成 VitePress 侧边栏配置：每个技术一个可折叠分组 */
export function buildGuideSidebar() {
  return scanGuides().map((g) => ({
    text: g.name,
    // 默认折叠，VitePress 会在进入该技术的页面时自动展开
    collapsed: true,
    items: [
      { text: '指南概览', link: `/guides/${g.dir}/` },
      ...g.chapters
    ]
  }))
}
