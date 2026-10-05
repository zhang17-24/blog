import fs from 'node:fs'
import path from 'node:path'
import { createContentLoader, type SiteConfig } from 'vitepress'
import { SITE_URL, SITE_TITLE, SITE_DESC } from '../site'

function esc(s: string) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * 在 buildEnd 钩子里生成 /feed.xml
 * 这里用的是 createContentLoader 的 render: true，能拿到整页 HTML，
 * 但数据只在 Node 端使用，不会进客户端 bundle。
 */
export async function genFeed(siteConfig: SiteConfig) {
  const posts = await createContentLoader('posts/*.md', {
    render: true,
    transform(raw) {
      return raw
        .filter((p) => p.frontmatter.date && p.frontmatter.title)
        .map((p) => ({
          title: String(p.frontmatter.title),
          url: p.url,
          date: new Date(p.frontmatter.date),
          desc: String(p.frontmatter.description ?? ''),
          html: p.html ?? ''
        }))
        .sort((a, b) => +b.date - +a.date)
    }
  }).load()

  const abs = (u: string) => SITE_URL.replace(/\/$/, '') + u

  const items = posts
    .map(
      (p) => `    <item>
      <title>${esc(p.title)}</title>
      <link>${esc(abs(p.url))}</link>
      <guid isPermaLink="true">${esc(abs(p.url))}</guid>
      <pubDate>${p.date.toUTCString()}</pubDate>
      <description>${esc(p.desc)}</description>
      <content:encoded><![CDATA[${p.html}]]></content:encoded>
    </item>`
    )
    .join('\n')

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>${esc(SITE_TITLE)}</title>
    <link>${esc(SITE_URL)}</link>
    <description>${esc(SITE_DESC)}</description>
    <language>zh-CN</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <generator>VitePress</generator>
${items}
  </channel>
</rss>
`

  fs.writeFileSync(path.join(siteConfig.outDir, 'feed.xml'), xml, 'utf-8')
  console.log(`  ✓ feed.xml 已生成（${posts.length} 篇文章）`)
}
