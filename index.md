---
sidebar: false
aside: false
lastUpdated: false
title: 首页
description: 写代码，也写生活。
---

<div class="home-hero">
  <h1>流沙</h1>
  <p>写代码，也写生活。这里记录一些不太成熟的想法，和那些值得被写下来的瞬间。</p>
  <div class="links">
    <a href="/about">关于我</a>
    <a href="/archive">全部文章</a>
    <a href="/tags">标签</a>
    <a href="/feed.xml">RSS 订阅</a>
  </div>
</div>

<div class="home-sec">
  <h2>最新文章</h2>
  <a class="more" href="/archive">全部 →</a>
</div>

<PostList :per-page="6" />

<div class="home-sec">
  <h2>技术笔记</h2>
  <a class="more" href="/notes/">全部 →</a>
</div>

<div class="note-links">

- [Rust 所有权](/notes/rust/ownership) — 借用检查器不是敌人，它只是比我更早地发现了问题
- [Rust 生命周期](/notes/rust/lifetimes) — 标注不是为了取悦编译器，而是为了把意图说清楚
- [Docker 与 Caddy](/notes/selfhost/docker-caddy) — 两台命令换一个自动 HTTPS 的站点

</div>
