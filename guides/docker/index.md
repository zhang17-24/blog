---
title: Docker
description: 从镜像分层到 compose 编排，再到用 Caddy 把站点跑起来。
order: 6
---

# Docker

Docker 的概念不多，但每个概念都会在实际使用中咬你一口：
镜像分层、卷的持久化、端口映射、构建缓存……

这个指南按「先跑起来，再理解原理」的顺序组织。

## 章节

| # | 章节 | 内容 |
| --- | --- | --- |
| 01 | [基础与镜像分层](/guides/docker/01-basics) | 容器 vs 虚拟机、Dockerfile、缓存 |
| 02 | [Compose 编排](/guides/docker/02-compose) | 多容器、卷、网络、健康检查 |
| 03 | [用 Caddy 部署站点](/guides/docker/03-caddy-deploy) | 自动 HTTPS、反代、缓存策略 |

## 安装

```bash
# Linux 服务器
curl -fsSL https://get.docker.com | sh

# macOS / Windows
# 装 Docker Desktop，或者用 colima（更轻）
brew install colima && colima start
```

::: tip 先理解一件事
**容器不是轻量虚拟机。** 容器只是被 Linux 命名空间（namespace）隔离起来的进程，
和宿主机共用同一个内核。这就是它启动只要几百毫秒的原因。
:::
