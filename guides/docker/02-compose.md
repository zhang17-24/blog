---
title: Compose 编排
description: 用一个文件描述多容器应用，以及卷、网络和健康检查。
---

# Compose 编排

单容器用 `docker run` 还行，一旦涉及数据库 + 应用 + 反向代理，
命令行参数就会失控。Compose 用一个 YAML 文件描述整个应用。

## 最小可用示例

```yaml
services:
  web:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./dist:/usr/share/nginx/html:ro

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

```bash
docker compose up -d          # 启动
docker compose logs -f web    # 看某个服务日志
docker compose restart web    # 重启单个服务
docker compose down           # 停止并删除容器（卷保留）
docker compose down -v        # 连卷一起删 ← 危险
```

## 卷：三种写法的区别

| 写法 | 类型 | 说明 |
| --- | --- | --- |
| `./dist:/srv:ro` | 绑定挂载 | 把宿主机目录挂进去，**改文件立即生效** |
| `pgdata:/var/lib/...` | 命名卷 | Docker 管理，适合数据库 |
| `/tmp/x:/data` | 绑定挂载（绝对路径） | 同上，只是路径写死 |

- 静态文件、配置用**绑定挂载**，方便直接改
- 数据库、证书用**命名卷**，性能更好也不容易误删
- `:ro` 表示只读，能加就加 —— 避免容器意外写坏宿主机文件

## 网络：服务名就是主机名

同一个 compose 里的服务在**默认网络**中可以直接用服务名互相访问：

```yaml
services:
  app:
    environment:
      # 不用写 IP，直接用服务名 db
      DATABASE_URL: postgres://user:pass@db:5432/mydb
  db:
    image: postgres:16-alpine
```

这个 DNS 解析由 Docker 内嵌的 DNS 提供，是 Compose 最好用的特性之一。

## 环境变量

```yaml
services:
  app:
    environment:
      - NODE_ENV=production
    env_file:
      - .env          # 从文件读，记得加进 .gitignore
```

在 compose 文件里可以用 `${VAR}` 引用宿主机环境变量，
也可以用同目录下的 `.env` 文件自动加载。

::: warning 别把密码提交进 git
`.env` 一定要写进 `.gitignore`。仓库里放一份 `.env.example` 说明需要哪些变量。
:::

## 健康检查与依赖顺序

`depends_on` **只保证启动顺序，不保证服务可用**。数据库进程起来了但还没准备好
接受连接时，应用可能已经连上去然后崩了。

```yaml
services:
  db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  app:
    depends_on:
      db:
        condition: service_healthy      # 等健康检查通过再启动
```

## 生产环境建议

| 配置 | 作用 |
| --- | --- |
| `restart: unless-stopped` | 崩溃或重启后自动拉起 |
| `logging.options.max-size` | 限制日志体积，否则会吃满磁盘 |
| `deploy.resources.limits` | 限制 CPU/内存 |
| 明确镜像版本号 | 避免 `latest` 突然变了 |

```yaml
services:
  web:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

下一篇：[用 Caddy 部署站点](/guides/docker/03-caddy-deploy)。
