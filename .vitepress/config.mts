import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitepress'
import { genFeed } from './theme/build-hooks'
import { buildGuideSidebar } from './guides'
import { SITE_URL, SITE_TITLE, SITE_DESC } from './site'

/**
 * 中文本地搜索分词器
 * MiniSearch 默认按空格切词，中文会被当成一整个长串，
 * 导致搜「网盘」找不到「云网盘」。用浏览器原生的 Intl.Segmenter 按词切分。
 */
function cjkTokenize(text: string): string[] {
  if (typeof Intl !== 'undefined' && 'Segmenter' in Intl) {
    const seg = new Intl.Segmenter('zh', { granularity: 'word' })
    return Array.from(seg.segment(text))
      .filter((s) => s.isWordLike)
      .map((s) => s.segment)
  }
  // 兜底：按单字切分
  return text.split('')
}

/**
 * 侧边栏是在「配置加载时」扫描目录算出来的，
 * 而 VitePress 只在 config 文件及其依赖变化时才重新加载配置
 * （见 vitepress/dist/node 里的 handleHotUpdate：
 *   `if (file === configPath || configDeps.includes(file))`）。
 *
 * 单纯调 server.restart() 只重启 Vite，不会重跑 buildGuideSidebar()，
 * 侧边栏还是旧的。正确做法是让 VitePress 自己走配置重载流程 ——
 * 本文件 import 了 guides.ts，所以 guides.ts 属于 configDeps，
 * 更新它的 mtime 就能触发完整重载。
 *
 * 效果：dev 模式下新增/删除指南目录或章节，侧边栏自动刷新。
 * 只影响 dev（apply: 'serve'），构建流程不受影响。
 */
function watchGuides() {
  const guidesModule = fileURLToPath(new URL('./guides.ts', import.meta.url))
  return {
    name: 'watch-guides-sidebar',
    apply: 'serve' as const,
    configureServer(server: any) {
      let timer: ReturnType<typeof setTimeout> | null = null
      const onChange = (file: string) => {
        const f = file.split(path.sep).join('/')
        if (!f.endsWith('.md')) return
        if (!f.includes('/guides/')) return
        if (timer) clearTimeout(timer)
        // 防抖：编辑器保存 / 批量创建会连着触发好几次
        timer = setTimeout(() => {
          const now = new Date()
          try {
            fs.utimesSync(guidesModule, now, now)
          } catch {
            /* 忽略：碰不到文件就让用户手动重启 */
          }
        }, 300)
      }
      server.watcher.on('add', onChange)
      server.watcher.on('unlink', onChange)
    }
  }
}

export default defineConfig({
  title: SITE_TITLE,
  description: SITE_DESC,
  lang: 'zh-CN',

  // 去掉 URL 里的 .html，/posts/hello 而不是 /posts/hello.html
  cleanUrls: true,

  // 显示「最后更新于」。依赖 git 提交时间，CI 里必须 fetch-depth: 0
  lastUpdated: true,

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
    ['link', { rel: 'alternate', type: 'application/rss+xml', title: SITE_TITLE, href: '/feed.xml' }],
    ['meta', { name: 'theme-color', content: '#2f6fed' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: SITE_TITLE }],
    ['meta', { property: 'og:description', content: SITE_DESC }]
  ],

  // 内置 sitemap 生成
  sitemap: { hostname: SITE_URL },

  markdown: {
    lineNumbers: true
  },

  // README 是给人和 GitHub 看的，不要当成页面渲染；
  // deploy/ 下是部署配置，也不参与构建
  srcExclude: ['**/README.md', 'deploy/**'],

  themeConfig: {
    logo: '/logo.svg',
    siteTitle: SITE_TITLE,

    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guides/', activeMatch: '/guides/' },
      { text: '归档', link: '/archive' },
      { text: '标签', link: '/tags' },
      { text: '关于', link: '/about' }
    ],

    /**
     * 侧边栏是自动生成的 —— 扫描 guides/ 下的每个技术目录，
     * 每个技术变成一个可折叠分组，组内是该技术的章节。
     * 新增技术：建目录 + 写 index.md + 加章节文件即可，不用改这里。
     * （dev 模式下由下面的 watchGuides 插件自动重启刷新）
     */
    sidebar: {
      '/guides/': buildGuideSidebar()
    },

    outline: { level: [2, 3], label: '本页目录' },

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            displayDetails: '显示详情',
            resetButtonTitle: '清空',
            backButtonTitle: '返回',
            noResultsText: '没有找到结果',
            footer: {
              selectText: '选择',
              selectKeyAriaLabel: '回车',
              navigateText: '切换',
              navigateUpKeyAriaLabel: '上箭头',
              navigateDownKeyAriaLabel: '下箭头',
              closeText: '关闭',
              closeKeyAriaLabel: 'Esc'
            }
          }
        },
        miniSearch: {
          options: {
            tokenize: cjkTokenize
          },
          searchOptions: {
            fuzzy: 0.2,
            prefix: true,
            boost: { title: 4, text: 2, titles: 1 }
          }
        }
      }
    },

    socialLinks: [{ icon: 'github', link: 'https://github.com/yourname' }],

    docFooter: { prev: '上一篇', next: '下一篇' },
    lastUpdated: { text: '最后更新于' },
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色',
    darkModeSwitchTitle: '切换到深色',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    externalLinkIcon: true,

    footer: {
      message: '内容采用 CC BY-NC-SA 4.0 许可协议',
      copyright: `© ${new Date().getFullYear()} ${SITE_TITLE}`
    },

    notFound: {
      title: '页面走丢了',
      quote: '这里什么都没有，要不回首页看看？',
      linkText: '回到首页'
    }
  },

  // 构建结束：生成 RSS
  buildEnd: async (siteConfig) => {
    await genFeed(siteConfig)
  },

  vite: {
    plugins: [watchGuides()]
  }
})
