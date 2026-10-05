import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import PostList from './components/PostList.vue'
import TagIndex from './components/TagIndex.vue'
import ArchiveList from './components/ArchiveList.vue'
import Comment from './components/Comment.vue'
import './style.css'

/**
 * 主题入口
 *
 * 注意：只要你创建了 .vitepress/theme/ 目录，就必须有这个文件，
 * 否则 VitePress 启动会报找不到 @theme/index。
 */
export default {
  extends: DefaultTheme,

  Layout() {
    return h(DefaultTheme.Layout, null, {
      // 文章底部挂评论区（组件内部会判断只在 /posts/ 下显示）
      'doc-after': () => h(Comment)
    })
  },

  enhanceApp({ app }) {
    // 全局注册，这样 .md 里可以直接写 <PostList /> 而不用 import
    app.component('PostList', PostList)
    app.component('TagIndex', TagIndex)
    app.component('ArchiveList', ArchiveList)
  }
}
