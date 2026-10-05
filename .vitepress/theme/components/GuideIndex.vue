<script setup lang="ts">
import { data as guides } from '../guides.data'

const total = guides.reduce((n, g) => n + g.chapters.length, 0)
</script>

<template>
  <div class="gi">
    <p class="gi-stat">
      共 <b>{{ guides.length }}</b> 个技术方向 · <b>{{ total }}</b> 篇章节
    </p>

    <div class="gi-grid">
      <article v-for="g in guides" :key="g.dir" class="gi-card">
        <header class="gi-head">
          <a class="gi-name" :href="`/guides/${g.dir}/`">{{ g.name }}</a>
          <span class="gi-count">{{ g.chapters.length }} 篇</span>
        </header>
        <p v-if="g.desc" class="gi-desc">{{ g.desc }}</p>
        <ol class="gi-chapters">
          <li v-for="(c, i) in g.chapters.slice(0, 4)" :key="c.link">
            <span class="gi-idx">{{ String(i + 1).padStart(2, '0') }}</span>
            <a :href="c.link">{{ c.text }}</a>
          </li>
        </ol>
        <a v-if="g.chapters.length > 4" class="gi-more" :href="`/guides/${g.dir}/`">
          还有 {{ g.chapters.length - 4 }} 篇 →
        </a>
        <a v-else-if="g.chapters.length" class="gi-more" :href="`/guides/${g.dir}/`">
          进入指南 →
        </a>
      </article>
    </div>

    <p v-if="!guides.length" class="gi-empty">
      还没有指南。在 guides/ 下新建一个目录，写个 index.md 就会出现在这里。
    </p>
  </div>
</template>

<style scoped>
.gi {
  margin: 10px 0 40px;
}

.gi-stat {
  margin: 0 0 20px;
  font-size: 13.5px;
  color: var(--vp-c-text-3);
}

.gi-stat b {
  color: var(--vp-c-text-1);
  font-weight: 600;
}

.gi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.gi-card {
  display: flex;
  flex-direction: column;
  padding: 20px 22px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  background: var(--vp-c-bg-soft);
  transition: border-color 0.2s, transform 0.2s;
}

.gi-card:hover {
  border-color: var(--vp-c-brand-1);
  transform: translateY(-2px);
}

.gi-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.gi-name {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--vp-c-text-1);
  text-decoration: none;
}

.gi-name:hover {
  color: var(--vp-c-brand-1);
}

.gi-count {
  margin-left: auto;
  flex: none;
  padding: 1px 9px;
  border-radius: 999px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  font-size: 11.5px;
  font-weight: 600;
}

.gi-desc {
  margin: 10px 0 0;
  font-size: 13.5px;
  line-height: 1.65;
  color: var(--vp-c-text-2);
}

.gi-chapters {
  list-style: none;
  margin: 16px 0 0;
  padding: 0;
}

.gi-chapters li {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 5px 0;
}

.gi-idx {
  flex: none;
  font-size: 11.5px;
  font-variant-numeric: tabular-nums;
  color: var(--vp-c-text-3);
}

.gi-chapters a {
  font-size: 13.8px;
  color: var(--vp-c-text-2);
  text-decoration: none;
  line-height: 1.5;
}

.gi-chapters a:hover {
  color: var(--vp-c-brand-1);
}

.gi-more {
  margin-top: 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--vp-c-brand-1);
  text-decoration: none;
}

.gi-empty {
  padding: 40px 0;
  color: var(--vp-c-text-3);
}
</style>
