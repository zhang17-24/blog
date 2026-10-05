---
aside: false
lastUpdated: false
title: 学习指南
description: 按技术方向整理的学习路径，每个方向都从基础概念讲到能上手用。
---

<div class="home-sec">
  <h2>学习指南</h2>
  <a class="more" href="/archive">博客文章 →</a>
</div>

<p class="gi-intro">左侧目录按技术方向分组，点标题可以折叠展开。每个方向都是一条从基础到深入的路径，可以顺着「下一篇」一路读下去。</p>

<GuideIndex />

<div class="home-sec">
  <h2>使用说明</h2>
</div>

- **左侧目录**按技术分组，点分组标题可以折叠/展开，当前所在的章节会自动展开
- **右侧大纲**显示当前页面的章节结构，长文可以直接跳转
- **顶部搜索**按 `Ctrl / ⌘ + K` 打开，支持中文分词，搜「网盘」能找到「云网盘」
- **底部导航**每篇末尾有「上一篇 / 下一篇」，顺着读就是一条学习路径
- **最后更新**每篇底部会显示最后修改时间，方便判断内容是否还新鲜

::: tip 怎么新增一个技术方向
在 `guides/` 下新建一个目录，写一个 `index.md`（`title` 作为分组名，`order` 控制排序），
再把章节文件按 `01-xxx.md`、`02-xxx.md` 命名放进去。重启 `npm run dev`，
左侧目录会自动出现新的分组 —— 侧边栏是扫描目录生成的，不需要手写配置。
:::

<style>
.gi-intro {
  margin: 0 0 22px;
  font-size: 14.5px;
  line-height: 1.75;
  color: var(--vp-c-text-2);
}
</style>
