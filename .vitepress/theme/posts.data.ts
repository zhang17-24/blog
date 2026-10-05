import { createContentLoader } from 'vitepress'

export interface Post {
  title: string
  url: string
  /** YYYY-MM-DD，用于展示 */
  date: string
  /** 时间戳，用于排序 */
  ts: number
  tags: string[]
  excerpt: string
  /** 预计阅读分钟数 */
  minutes: number
}

/** 去掉 frontmatter、代码块、图片、链接和标记符号，得到纯文本 */
function plainText(md: string): string {
  return md
    .replace(/^---[\s\S]*?\n---/, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`]*`/g, '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/<[^>]+>/g, '')
    .replace(/[#>*_~|]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * frontmatter 里的 `date: 2026-09-28` 会被 YAML 解析成 Date 对象，
 * 直接 String() 会得到 "Mon Sep 28 2026 ..."。这里统一格式化成 YYYY-MM-DD。
 * 用 UTC 取值，避免时区把日期挪走一天。
 */
function toDate(v: unknown): Date {
  return v instanceof Date ? v : new Date(String(v))
}

function ymd(v: unknown): string {
  const d = toDate(v)
  if (Number.isNaN(+d)) return String(v).slice(0, 10)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())}`
}

function makeExcerpt(md: string, max = 110): string {
  const t = plainText(md)
  return t.length > max ? t.slice(0, max) + '…' : t
}

/** 中文按 350 字/分钟、英文按 200 词/分钟估算 */
function readingMinutes(md: string): number {
  const t = plainText(md)
  const cjk = (t.match(/[\u4e00-\u9fa5]/g) || []).length
  const words = (t.match(/[A-Za-z0-9]+/g) || []).length
  return Math.max(1, Math.round(cjk / 350 + words / 200))
}

/**
 * 文章列表数据加载器
 *
 * 关键点：transform 的返回值才是最终序列化给客户端的内容。
 * 所以这里 includeSrc: true 拿到原文用来算摘要和阅读时长，
 * 但只把精简后的字段返回出去，客户端 bundle 不会变大。
 *
 * 只要 posts/ 下的 md 写了 date 和 title 就会被收录；
 * 没有 date 的文件（比如将来放个说明页）会被自动忽略。
 */
export default createContentLoader('posts/*.md', {
  includeSrc: true,
  transform(raw): Post[] {
    return raw
      .filter((p) => p.frontmatter.date && p.frontmatter.title)
      .map((p) => {
        const src = p.src ?? ''
        const fm = p.frontmatter
        return {
          title: String(fm.title),
          url: p.url,
          date: ymd(fm.date),
          ts: +toDate(fm.date),
          tags: Array.isArray(fm.tags) ? fm.tags.map(String) : [],
          excerpt: fm.description ? String(fm.description) : makeExcerpt(src),
          minutes: readingMinutes(src)
        }
      })
      .sort((a, b) => b.ts - a.ts)
  }
})
