<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vitepress'
import { GISCUS } from '../../site'

const route = useRoute()
const box = ref<HTMLElement | null>(null)

/** 只在文章页显示，且必须先在 site.ts 里填好 repo */
const enabled = computed(() => !!GISCUS.repo && route.path.startsWith('/posts/'))

function render() {
  const host = box.value
  if (!host) return
  host.innerHTML = ''
  if (!enabled.value) return

  const s = document.createElement('script')
  s.src = 'https://giscus.app/client.js'
  s.async = true
  s.crossOrigin = 'anonymous'
  s.setAttribute('data-repo', GISCUS.repo)
  s.setAttribute('data-repo-id', GISCUS.repoId)
  s.setAttribute('data-category', GISCUS.category)
  s.setAttribute('data-category-id', GISCUS.categoryId)
  s.setAttribute('data-mapping', 'pathname')
  s.setAttribute('data-strict', '1')
  s.setAttribute('data-reactions-enabled', '1')
  s.setAttribute('data-emit-metadata', '0')
  s.setAttribute('data-input-position', 'top')
  s.setAttribute('data-lang', 'zh-CN')
  s.setAttribute('data-loading', 'lazy')
  host.appendChild(s)
}

onMounted(render)

// SPA 站内跳转不会刷新页面，需要手动重新挂载
watch(
  () => route.path,
  async () => {
    await nextTick()
    render()
  }
)
</script>

<template>
  <div v-if="enabled" class="cm">
    <h2 class="cm-h">评论</h2>
    <div ref="box" class="cm-box"></div>
  </div>
  <div v-else-if="route.path.startsWith('/posts/')" class="cm-tip">
    <p>
      想开启评论？在 <code>.vitepress/site.ts</code> 里填上 GISCUS 的
      <code>repo</code> / <code>repoId</code> / <code>categoryId</code> 即可，说明见该文件注释。
    </p>
  </div>
</template>

<style scoped>
.cm {
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid var(--vp-c-divider);
}

.cm-h {
  margin: 0 0 16px;
  padding: 0;
  border: none;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.3px;
}

.cm-tip {
  margin-top: 40px;
  padding: 14px 18px;
  border: 1px dashed var(--vp-c-divider);
  border-radius: 10px;
  font-size: 13px;
  color: var(--vp-c-text-3);
  line-height: 1.7;
}

.cm-tip p {
  margin: 0;
}

.cm-tip code {
  font-size: 12.5px;
}
</style>
