<script setup lang="ts">
import { computed } from 'vue'
import { data as posts } from '../posts.data'

/** 按年份分组 */
const years = computed(() => {
  const map = new Map<string, typeof posts>()
  for (const p of posts) {
    const y = p.date.slice(0, 4)
    if (!map.has(y)) map.set(y, [])
    map.get(y)!.push(p)
  }
  return [...map.entries()]
    .sort((a, b) => Number(b[0]) - Number(a[0]))
    .map(([year, list]) => ({ year, list }))
})
</script>

<template>
  <div class="ar">
    <p class="ar-total">共 {{ posts.length }} 篇</p>
    <section v-for="g in years" :key="g.year" class="ar-year">
      <h3 class="ar-h">{{ g.year }}</h3>
      <ul class="ar-list">
        <li v-for="p in g.list" :key="p.url">
          <time :datetime="p.date">{{ p.date.slice(5).replace('-', '.') }}</time>
          <a :href="p.url">{{ p.title }}</a>
        </li>
      </ul>
    </section>
    <p v-if="!years.length" class="ar-empty">还没有文章。</p>
  </div>
</template>

<style scoped>
.ar {
  margin: 10px 0 40px;
}

.ar-total {
  font-size: 13px;
  color: var(--vp-c-text-3);
  margin: 0 0 6px;
}

.ar-year {
  margin-top: 30px;
}

.ar-h {
  margin: 0 0 10px;
  padding: 0;
  border: none;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.6px;
  color: var(--vp-c-text-1);
  font-variant-numeric: tabular-nums;
}

.ar-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.ar-list li {
  display: flex;
  align-items: baseline;
  gap: 18px;
  padding: 9px 0;
  border-bottom: 1px solid var(--vp-c-divider);
}

.ar-list time {
  flex: 0 0 52px;
  font-size: 13px;
  color: var(--vp-c-text-3);
  font-variant-numeric: tabular-nums;
}

.ar-list a {
  font-size: 14.8px;
  color: var(--vp-c-text-1);
  text-decoration: none;
}

.ar-list a:hover {
  color: var(--vp-c-brand-1);
}

.ar-empty {
  color: var(--vp-c-text-3);
}
</style>
