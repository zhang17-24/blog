# ---------- 构建阶段 ----------
# 注意：VitePress 2.0 起要求 Node >= 22，1.x 用 20 也可以，
# 这里统一用 22 避免以后升级踩坑
FROM node:22-alpine AS build

WORKDIR /app

# 先只拷依赖清单，利用 Docker 层缓存：代码改了不会重装依赖
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# lastUpdated 依赖 git 历史；如果构建时没有 .git 目录，
# VitePress 会跳过「最后更新于」而不报错，可以接受
RUN npm run build

# ---------- 运行阶段 ----------
# 服务器上只需要一个能托静态文件的 Caddy，不需要 Node 运行时
FROM caddy:2-alpine

COPY --from=build /app/.vitepress/dist /srv/blog
COPY Caddyfile /etc/caddy/Caddyfile

EXPOSE 80 443
