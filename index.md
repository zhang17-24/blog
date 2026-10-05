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
  <h2>学习指南</h2>
  <a class="more" href="/guides/">全部 →</a>
</div>

<p class="home-guides-intro">按技术方向整理的学习路径。点进去左侧是目录树，右侧是内容，可以顺着「下一篇」一路读完。</p>

<div class="home-guides">
  <a href="/guides/rust/"><b>Rust</b><span>所有权 · 生命周期 · Trait</span></a>
  <a href="/guides/python/"><b>Python</b><span>基础语法 · 数据结构 · 异步</span></a>
  <a href="/guides/docker/"><b>Docker</b><span>镜像分层 · Compose · Caddy</span></a>
  <a href="/guides/git/"><b>Git</b><span>日常命令 · 分支与合并</span></a>
  <a href="/guides/sql/"><b>SQL</b><span>基础查询 · 索引优化</span></a>
  <a href="/guides/linux/"><b>Linux</b><span>Shell · 权限与用户</span></a>
</div>

<style>
.home-guides-intro {
  margin: 0 0 18px;
  font-size: 14.5px;
  line-height: 1.75;
  color: var(--vp-c-text-2);
}
.home-guides {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
  margin-bottom: 10px;
}
.home-guides a {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 15px 18px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 11px;
  text-decoration: none;
  transition: border-color 0.2s, transform 0.2s;
}
.home-guides a:hover {
  border-color: var(--vp-c-brand-1);
  transform: translateY(-2px);
}
.home-guides b {
  font-size: 15.5px;
  font-weight: 700;
  color: var(--vp-c-text-1);
  letter-spacing: -0.2px;
}
.home-guides a:hover b {
  color: var(--vp-c-brand-1);
}
.home-guides span {
  font-size: 12.5px;
  color: var(--vp-c-text-3);
}
</style>
