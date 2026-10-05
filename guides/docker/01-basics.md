---
title: 基础与镜像分层
description: 容器是什么、Dockerfile 怎么写、构建缓存为什么失效。
---

# 基础与镜像分层

## 容器不是轻量虚拟机

| | 虚拟机 | 容器 |
| --- | --- | --- |
| 隔离层 | 硬件虚拟化 | 内核 namespace |
| 启动时间 | 几十秒 | 几百毫秒 |
| 体积 | GB 级 | MB 级 |
| 内核 | 每个 VM 一个 | 共用宿主机 |

容器本质上就是**被隔离起来的普通进程**。所以容器里跑一个常驻的
`systemd` 或 `cron` 通常是设计错误 —— 一个容器只干一件事。

## Dockerfile 的核心：分层与缓存

```dockerfile
FROM node:22-alpine

WORKDIR /app

# 先只拷依赖清单
COPY package.json package-lock.json ./
RUN npm ci

# 再拷源码
COPY . .

RUN npm run build

CMD ["node", "server.js"]
```

为什么要把 `COPY package.json` 和 `COPY . .` 分开？因为**每一条指令生成一层，
某一层的内容没变就复用缓存**。

如果写成 `COPY . .` 再 `RUN npm ci`，那么改任何一行源码都会让依赖缓存失效，
每次构建都要重新装一遍依赖。

::: tip 缓存规则
**变化频率越低的东西，越应该放在前面。** 系统依赖 → 语言依赖 → 源码。
:::

## 多阶段构建：让产物变小

```dockerfile
# 构建阶段：有完整工具链，体积大
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 运行阶段：只拷贝产物，不带工具链
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

最终镜像里**没有 Node、没有源码、没有 node_modules**，体积可能从 1 GB 降到 30 MB。

## 常用命令

```bash
docker build -t myapp:1.0 .          # 构建
docker run -d -p 8080:80 myapp:1.0   # 后台运行并映射端口
docker ps                            # 看运行中的容器
docker logs -f <容器名>               # 跟踪日志
docker exec -it <容器名> sh          # 进容器
docker image prune -a                # 清理无用镜像
```

## 三个必须记住的点

::: warning 容器里的数据会丢
容器删除时，**可写层里的数据一起消失**。需要持久化的东西（数据库、证书、
上传的文件）必须挂卷：

```bash
docker run -v mydata:/var/lib/data myapp
```
:::

::: warning 端口映射不是防火墙
`-p 8080:80` 默认绑定到 `0.0.0.0`，也就是**对所有网卡开放**。
只想本机访问要写 `-p 127.0.0.1:8080:80`。
:::

::: warning `latest` 标签不保证是最新的
`latest` 只是默认标签，不代表任何语义。生产环境永远用**明确的版本号**，
否则某天重建镜像会突然跑起一个新版本。
:::

下一篇：[Compose 编排](/guides/docker/02-compose)。
