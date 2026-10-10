import { createContentLoader } from 'vitepress'

export interface GuideChapter {
  text: string
  link: string
  desc: string
}

export interface GuideGroup {
  dir: string
  name: string
  desc: string
  order: number
  chapters: GuideChapter[]
}

declare const data: GuideGroup[]
export { data }

/**
 * 学习指南总览页的数据
 * 按技术目录聚合，用于渲染卡片。新增技术目录后这里自动生效。
 */
export default createContentLoader('guides/**/*.md', {
  transform(raw): GuideGroup[] {
    const map = new Map<string, GuideGroup>()
    const ensure = (dir: string) => {
      if (!map.has(dir)) {
        map.set(dir, { dir, name: dir, desc: '', order: 99, chapters: [] })
      }
      return map.get(dir)!
    }

    for (const p of raw) {
      const m = p.url.match(/^\/guides\/([^/]+)(\/.*)?$/)
      if (!m) continue
      const dir = m[1]
      const rest = m[2] ?? ''
      const fm = p.frontmatter as Record<string, unknown>
      const g = ensure(dir)

      if (rest === '' || rest === '/') {
        // 该技术的 index.md
        g.name = String(fm.title ?? dir)
        g.desc = String(fm.description ?? '')
        g.order = Number(fm.order ?? 99)
      } else if (rest.endsWith('/')) {
        // 二级分组（Part）的 index.md —— 不进卡片列表，
        // 卡片只列真正能读的章节，Part 层级交给左侧目录树表达
      } else {
        g.chapters.push({
          text: String(fm.title ?? p.url),
          link: p.url,
          desc: String(fm.description ?? '')
        })
      }
    }

    for (const g of map.values()) {
      g.chapters.sort((a, b) => a.link.localeCompare(b.link))
    }
    return [...map.values()].sort((a, b) => a.order - b.order || a.dir.localeCompare(b.dir))
  }
})
