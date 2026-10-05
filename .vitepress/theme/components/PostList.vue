<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { data as posts } from '../posts.data'

const props = withDefaults(
  defineProps<{
    /** 每页显示多少篇 */
    perPage?: number
    /** 只显示最新的 N 篇（传 0 表示不限） */
    limit?: number
    /** 是否显示分页器 */
    pager?: boolean
  }>(),
  { perPage: 8, limit: 0, pager: true }
)

const page = ref(1)

const source = computed(() => (props.limit > 0 ? posts.slice(0, props.limit) : posts))
const totalPages = computed(() => Math.max(1, Math.ceil(source.value.length / props.perPage)))
const shown = computed(() =>
  source.value.slice((page.value - 1) * props.perPage, page.value * props.perPage)
)
const pageList = computed(() => Array.from({ length: totalPages.value }, (_, i) => i + 1))

watch(totalPages, () => {
  if (page.value > totalPages.value) page.value = 1
})

function go(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  if (typeof window !== 'undefined') {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function formatDate(d: string) {
  return d.replace(/-/g, '.')
}
</script>

<template>
  <div class="pl-wrap">
    <ul class="pl-list">
      <li v-for="post in shown" :key="post.url" class="pl-item">
        <a class="pl-title" :href="post.url">{{ post.title }}</a>
        <div class="pl-meta">
          <time :datetime="post.date">{{ formatDate(post.date) }}</time>
          <span class="pl-sep">·</span>
          <span>{{ post.minutes }} 分钟</span>
          <template v-if="post.tags.length">
            <span class="pl-sep">·</span>
            <span class="pl-tags">
              <a v-for="t in post.tags" :key="t" :href="`/tags#${t}`" class="pl-tag">{{ t }}</a>
            </span>
          </template>
        </div>
        <p v-if="post.excerpt" class="pl-excerpt">{{ post.excerpt }}</p>
      </li>
    </ul>

    <p v-if="!shown.length" class="pl-empty">还没有文章，去 posts/ 目录新建一个 .md 文件试试。</p>

    <nav v-if="props.pager && totalPages > 1" class="pl-pager">
      <button class="pl-btn" :disabled="page === 1" @click="go(page - 1)">上一页</button>
      <button
        v-for="p in pageList"
        :key="p"
        class="pl-btn pl-num"
        :class="{ 'is-on': p === page }"
        @click="go(p)"
      >
        {{ p }}
      </button>
      <button class="pl-btn" :disabled="page === totalPages" @click="go(page + 1)">下一页</button>
    </nav>
  </div>
</template>

<style scoped>
.pl-wrap {
  margin: 8px 0 40px;
}

.pl-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.pl-item {
  padding: 22px 0;
  border-bottom: 1px solid var(--vp-c-divider);
}

.pl-item:first-child {
  padding-top: 8px;
}

.pl-title {
  display: block;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.5;
  letter-spacing: -0.3px;
  color: var(--vp-c-text-1);
  text-decoration: none;
  transition: color 0.2s;
}

.pl-title:hover {
  color: var(--vp-c-brand-1);
}

.pl-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 9px;
  font-size: 13px;
  color: var(--vp-c-text-3);
}

.pl-sep {
  color: var(--vp-c-divider);
}

.pl-tags {
  display: inline-flex;
  gap: 6px;
}

.pl-tag {
  padding: 1px 8px;
  border-radius: 5px;
  background: var(--vp-c-default-soft);
  color: var(--vp-c-text-2);
  font-size: 12px;
  text-decoration: none;
  transition: all 0.2s;
}

.pl-tag:hover {
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
}

.pl-excerpt {
  margin: 10px 0 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--vp-c-text-2);
}

.pl-empty {
  padding: 40px 0;
  text-align: center;
  color: var(--vp-c-text-3);
}

.pl-pager {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-top: 34px;
}

.pl-btn {
  min-width: 36px;
  padding: 6px 12px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-2);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.18s;
}

.pl-btn:hover:not(:disabled) {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.pl-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pl-num.is-on {
  background: var(--vp-c-brand-1);
  border-color: var(--vp-c-brand-1);
  color: #fff;
}
</style>
