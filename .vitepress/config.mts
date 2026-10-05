import { defineConfig } from 'vitepress'
import { genFeed } from './theme/build-hooks'
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
      { text: '笔记', link: '/notes/', activeMatch: '/notes/' },
      { text: '归档', link: '/archive' },
      { text: '标签', link: '/tags' },
      { text: '关于', link: '/about' }
    ],

    // 只给「笔记」区域配侧边栏；博客区（/posts/）保持无侧栏的干净阅读
    sidebar: {
      '/notes/': [
        {
          text: 'Rust 笔记',
          collapsed: false,
          items: [
            { text: '所有权', link: '/notes/rust/ownership' },
            { text: '生命周期', link: '/notes/rust/lifetimes' }
          ]
        },
        {
          text: '自托管',
          collapsed: false,
          items: [{ text: 'Docker 与 Caddy', link: '/notes/selfhost/docker-caddy' }]
        }
      ]
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
  }
})
