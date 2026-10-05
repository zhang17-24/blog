---
title: 用 Docker + Caddy 部署一个只属于自己的博客
date: 2026-09-28
tags: [DevOps, 教程]
description: 从一台干净的 VPS 开始，把域名、HTTPS、自动部署串起来，全程不超过 30 分钟。
---

从一台干净的 VPS 开始，把域名、HTTPS、自动部署串起来，全程不超过 30 分钟。

## 为什么是 Caddy 而不是 Nginx

Nginx 很强，但配 HTTPS 要额外装 certbot、写续期定时任务、还得记得 `nginx -s reload`。
Caddy 把这三件事合成了一件：**写个域名，它自己去申请证书、自己去续、自己重载**。

对一个个人博客来说，这就是全部的理由。

## 第一步：域名解析

在你的域名商后台加一条 A 记录：

| 类型 | 主机记录 | 记录值 |
| --- | --- | --- |
| A | blog | 你的服务器 IP |

等几分钟让解析生效，用 `dig blog.example.com +short` 确认能查到 IP。

## 第二步：Caddyfile

```txt
blog.example.com {
    root * /srv/blog
    encode zstd gzip

    try_files {path} {path}.html {path}/index.html /404.html
    file_server

    @assets path /assets/*
    header @assets Cache-Control "public, max-age=31536000, immutable"
}
```

几个容易踩的点：

- `try_files` 那行是必须的。VitePress 开了 `cleanUrls` 之后，`/posts/hello` 实际对应的是
  `posts/hello.html`，不加这行访问文章页会 404。
- 带 hash 的静态资源（`/assets/xxx.abc123.js`）可以放心设一年缓存，因为文件名变了内容才变。
- `encode zstd gzip` 能让 HTML 传输体积再小一截。

## 第三步：docker-compose

```yaml
services:
  web:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./dist:/srv/blog:ro
      - caddy_data:/data
      - caddy_config:/config

volumes:
  caddy_data:
  caddy_config:
```

`caddy_data` 这个卷**一定要持久化**，证书就存在里面。丢了的话重启后会重新申请，
Let's Encrypt 有频率限制，短时间内反复申请会被限流。

## 第四步：验证

```bash
docker compose up -d
docker compose logs -f web
```

看到类似 `certificate obtained successfully` 就说明证书签下来了。

> 如果一直卡在申请证书，先检查 80 端口有没有被占用 —— Caddy 申请证书要用 80 端口做 HTTP 校验。

## 自动化部署

手动 `rsync` 传文件能跑通之后，就该交给 CI 了。我的做法是：

1. 本地写完 `git push`
2. GitHub Actions 自动构建
3. `rsync` 把 `dist/` 同步到服务器

服务器上只跑 Caddy，不需要 Node，也不需要构建环境。这样即使 CI 挂了，
站点本身也完全不受影响。
