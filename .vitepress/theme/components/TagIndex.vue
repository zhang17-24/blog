<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { data as posts } from '../posts.data'

/** 所有标签 + 文章数，按文章数倒序 */
const tags = computed(() => {
  const map = new Map<string, number>()
  for (const p of posts) {
    for (const t of p.tags) map.set(t, (map.get(t) ?? 0) + 1)
  }
  return [...map.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
})

const active = ref<string>('')

const filtered = computed(() =>
  active.value ? posts.filter((p) => p.tags.includes(active.value)) : []
)

function pick(name: string) {
  active.value = active.value === name ? '' : name
  if (typeof history !== 'undefined') {
    history.replaceState(null, '', active.value ? `#${active.value}` : '#')
  }
}

onMounted(() => {
  // 支持 /tags#标签名 直接定位
  const h = decodeURIComponent(location.hash.slice(1))
  if (h && tags.value.some((t) => t.name === h)) active.value = h
})
</script>

<template>
  <div class="ti">
    <div class="ti-cloud">
      <button
        v-for="t in tags"
        :key="t.name"
        class="ti-chip"
        :class="{ 'is-on': t.name === active }"
        @click="pick(t.name)"
      >
        {{ t.name }}<span class="ti-n">{{ t.count }}</span>
      </button>
    </div>

    <p v-if="!tags.length" class="ti-empty">还没有标签。</p>

    <div v-if="active" class="ti-result">
      <h3 class="ti-h">{{ active }} · {{ filtered.length }} 篇</h3>
      <ul class="ti-list">
        <li v-for="p in filtered" :key="p.url">
          <a :href="p.url">{{ p.title }}</a>
          <time :datetime="p.date">{{ p.date.replace(/-/g, '.') }}</time>
        </li>
      </ul>
    </div>
    <p v-else-if="tags.length" class="ti-hint">点上面的标签查看对应文章</p>
  </div>
</template>

<style scoped>
.ti {
  margin: 10px 0 40px;
}

.ti-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ti-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 13px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 999px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-2);
  font-size: 13.5px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.18s;
}

.ti-chip:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.ti-chip.is-on {
  background: var(--vp-c-brand-1);
  border-color: var(--vp-c-brand-1);
  color: #fff;
}

.ti-n {
  font-size: 11.5px;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--vp-c-default-soft);
  color: var(--vp-c-text-3);
}

.ti-chip.is-on .ti-n {
  background: rgba(255, 255, 255, 0.24);
  color: #fff;
}

.ti-hint,
.ti-empty {
  margin-top: 22px;
  font-size: 13.5px;
  color: var(--vp-c-text-3);
}

.ti-result {
  margin-top: 30px;
}

.ti-h {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--vp-c-text-1);
  border: none;
  padding: 0;
}

.ti-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.ti-list li {
  display: flex;
  align-items: baseline;
  gap: 14px;
  padding: 10px 0;
  border-bottom: 1px solid var(--vp-c-divider);
}

.ti-list a {
  flex: 1;
  font-size: 14.5px;
  color: var(--vp-c-text-1);
  text-decoration: none;
}

.ti-list a:hover {
  color: var(--vp-c-brand-1);
}

.ti-list time {
  font-size: 12.5px;
  color: var(--vp-c-text-3);
  font-variant-numeric: tabular-nums;
}
</style>
