# Docker 与 Caddy

两行命令换一个自动 HTTPS 的站点。

## 最小可用的 compose 文件

```yaml
services:
  web:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"   # HTTP/3
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./dist:/srv/blog:ro
      - caddy_data:/data
      - caddy_config:/config

volumes:
  caddy_data:
  caddy_config:
```

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

## 三个必须记住的点

::: warning 数据卷一定要持久化
`caddy_data` 里存着证书。丢了会重新申请，而 Let's Encrypt 有频率限制，
短时间内反复申请会被限流，最长可能等一周。
:::

::: warning try_files 不能省
静态站点生成器通常输出的是 `posts/hello.html`，但 URL 是 `/posts/hello`。
少了这行，直接访问文章页会 404。
:::

::: tip 80 端口要空着
申请证书时 Caddy 需要通过 80 端口做 HTTP 校验。如果被别的服务占了，
会一直卡在申请阶段。
:::

## 常用命令

```bash
docker compose up -d          # 启动
docker compose logs -f web    # 看日志，证书申请进度在这里
docker compose restart web    # 改完 Caddyfile 后重载
docker compose down           # 停止（数据卷保留）
```
