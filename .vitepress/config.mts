import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitepress'
import katexModule from '@vscode/markdown-it-katex'
import { genFeed } from './theme/build-hooks'
import { buildGuideSidebar } from './guides'
import { SITE_URL, SITE_TITLE, SITE_DESC } from './site'

/**
 * markdown-it-katex 是 CJS 包（exports.default = 插件函数）。
 * config.mts 走 esbuild 编译，import 默认导入拿到的可能是命名空间对象
 * 而不是函数本身，直接 md.use() 会报 "plugin.apply is not a function"。
 * 这里两种形态都兜住。
 */
const katexPlugin: any = (katexModule as any)?.default ?? katexModule

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
    lineNumbers: true,

    /**
     * 数学公式（KaTeX）
     *
     * 指南里的公式很多（深度学习那套有 300+ 块级、1000+ 行内），
     * VitePress 默认不认 $...$，会原样输出，所以必须挂这个插件。
     *
     * 选 KaTeX 不选 MathJax：构建时渲染，公式量上千，KaTeX 快一个数量级。
     * 样式（katex.min.css）在 theme/index.ts 里引，字体随构建产物一起打包。
     *
     * strict：正文里有 \text{欠拟合} 这类写法（公式里嵌中文），
     * KaTeX 默认会为每个中文字符打一条 unicodeTextInMathMode 警告，
     * 一次构建刷几十行。只忽略这一类，其他语法问题照常报警。
     */
    config: (md) => {
      md.use(katexPlugin, {
        strict: (errorCode: string) =>
          errorCode === 'unicodeTextInMathMode' ? 'ignore' : 'warn'
      })
    }
  },

  // README 是给人和 GitHub 看的，不要当成页面渲染；
  // deploy/ 是部署配置，docs/ 是内部文档（如发布 SOP），都不参与构建
  srcExclude: ['**/README.md', 'deploy/**', 'docs/**'],

  /**
   * /downloads/ 下放的是可下载的静态文件（源码、手册等），不是页面。
   *
   * 为什么要忽略：VitePress 判断链接是否「死链」时，会先看扩展名在不在
   * 它的静态资源白名单里（zip/pdf/txt/csv/json/svg…）。`.py` 不在名单里，
   * 于是被当成页面去校验，去找 public/downloads/xxx.py.html —— 当然找不到，
   * 构建直接报 dead link 失败。`.html` 因为会走「补 .html 再找」的分支而侥幸通过。
   *
   * 链接本身没问题：cleanUrls 已开启，渲染出来的 href 就是 /downloads/xxx.py。
   * 所以这里只是让死链检查放行这个目录，新增 .py / .ipynb / .sh 等文件都不用再改配置。
   */
  ignoreDeadLinks: [/^\/downloads\//],

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
    plugins: [watchGuides()],

    build: {
      /**
       * 本地搜索索引是一个整体 chunk，页面越多越大（三套指南全量收进去后约 800 KB）。
       * 它是**懒加载**的 —— 用户点开搜索框才会请求，不影响首屏。
       * 所以这里把阈值调高，避免每次构建都刷一条无意义的告警。
       */
      chunkSizeWarningLimit: 1200
    }
  }
})
