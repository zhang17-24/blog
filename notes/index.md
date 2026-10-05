---
title: 技术笔记
---

# 技术笔记

这里放成体系的内容 —— 一个主题下的若干篇，按目录组织，左侧有导航。

和 [文章](/archive) 的区别是：文章是零散的、按时间写的；
笔记是整理过的、会持续更新的。

## Rust

- [所有权](/notes/rust/ownership)
- [生命周期](/notes/rust/lifetimes)

## 自托管

- [Docker 与 Caddy](/notes/selfhost/docker-caddy)

---

::: tip 怎么新增一篇笔记
在 `notes/` 下新建 `.md` 文件，然后在 `.vitepress/config.mts` 的
`themeConfig.sidebar['/notes/']` 里加一条即可。
:::
