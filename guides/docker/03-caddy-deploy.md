---
title: 用 Caddy 部署站点
description: 两行配置换自动 HTTPS，以及静态站点最容易踩的 404。
---

# 用 Caddy 部署站点

## 为什么是 Caddy 而不是 Nginx

Nginx 很强，但配 HTTPS 要额外装 certbot、写续期定时任务、还得记得 reload。
Caddy 把这三件事合成了一件：**写个域名，它自己去申请证书、自己去续、自己重载**。

对个人站点来说，这就是全部的理由。

## Caddyfile

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

## 三个容易踩的点

::: warning try_files 不能省
静态站点生成器（VitePress / Hugo / Astro）开了 clean URLs 之后，
URL `/posts/hello` 对应的实际文件是 `posts/hello.html`。

少了这行，**直接访问文章页会 404**（从首页点进去却是好的，因为那是客户端路由）。
:::

::: warning 80 端口要空着
Caddy 申请证书时需要通过 80 端口做 HTTP 校验。被别的服务占了会一直卡在申请阶段。
:::

::: tip 缓存策略
- 带 hash 的静态资源（`/assets/app.abc123.js`）→ 缓存一年，`immutable`
- HTML → 不缓存，`max-age=0, must-revalidate`

文件名变了内容才变，所以资源文件可以放心长缓存；HTML 是入口，必须每次都校验。
:::

## docker-compose

```yaml
services:
  web:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"      # HTTP/3
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./dist:/srv/blog:ro
      - caddy_data:/data
      - caddy_config:/config

volumes:
  caddy_data:
  caddy_config:
```

::: danger caddy_data 卷千万不能删
**证书就存在这个卷里。** 丢了会重新申请，而 Let's Encrypt 有频率限制，
短时间内反复申请会被限流，最长可能等一周。
:::

## 验证部署

```bash
docker compose up -d
docker compose logs -f web
```

看到 `certificate obtained successfully` 就说明证书签下来了。

然后逐项确认：

```bash
curl -I https://blog.example.com/                    # 200 且是 https
curl -I https://blog.example.com/posts/hello         # 文章页不是 404
curl -I https://blog.example.com/assets/app.abc.js   # 有 immutable 缓存头
curl -s https://blog.example.com/feed.xml | head -5  # RSS 正常
```

## 反向代理：把请求转给别的服务

Caddy 做反代比 Nginx 简单很多：

```txt
api.example.com {
    reverse_proxy app:3000
}

# 或者按路径分流
example.com {
    reverse_proxy /api/* app:3000
    file_server
    root * /srv/blog
}
```

`reverse_proxy` 会自动处理 `X-Forwarded-For`、WebSocket 升级和健康检查。

## 部署方式的选择

| 方式 | 服务器需要什么 | 适合 |
| --- | --- | --- |
| 本地构建 + rsync | 只有 Caddy | 个人站点，推荐 |
| 服务器上 Docker 构建 | Docker + 源码 | 不想传构建产物 |
| GitHub Actions + rsync | 只有 Caddy | 推送即部署，最省心 |
| Coolify / Dokploy | Docker + 面板 | 不想碰命令行 |

Docker 指南到这里结束。
