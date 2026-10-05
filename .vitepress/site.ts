/**
 * 站点级常量：改这里就够了
 */

// 部署后的正式域名（末尾不要带斜杠），影响 RSS、sitemap、og 标签
export const SITE_URL = 'https://blog.example.com'

export const SITE_TITLE = '流沙'
export const SITE_DESC = '写代码，也写生活。'
export const AUTHOR = '你的名字'

/**
 * Giscus 评论（基于 GitHub Discussions，免费、无后端）
 * 开启步骤：
 *   1. 建一个 public 仓库，例如 yourname/blog-comments
 *   2. 在该仓库 Settings → General → Features 勾选 Discussions
 *   3. 安装 giscus App：https://github.com/apps/giscus
 *   4. 打开 https://giscus.app/zh-CN ，填入仓库名，复制生成的 repoId / categoryId
 *   5. 把下面三项填上即可，repo 为空则自动隐藏评论区
 */
export const GISCUS = {
  repo: '',
  repoId: '',
  category: 'Announcements',
  categoryId: ''
}
