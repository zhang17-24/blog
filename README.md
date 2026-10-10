# 流沙 · 个人博客

基于 VitePress 1.6 的极简个人博客。纯静态、零后端、自带本地全文搜索（中文分词已配好）。

## 快速开始

```bash
npm install
npm run dev
```

打开 `http://localhost:5173/` 就能看到站点。改任何 `.md` 文件都是**毫秒级热更新**，不用刷新。

```bash
npm run build     # 构建到 .vitepress/dist
npm run preview   # 本地预览构建产物（和线上一致）
```

> 环境要求：Node 18+（推荐 22，仓库里有 `.nvmrc`）。

## 日常流程：从写到发布

> 📋 完整版见 **[docs/PUBLISH-SOP.md](docs/PUBLISH-SOP.md)** —— 含前置准备、
> 发布前检查清单、异常处理（构建失败 / 部署失败 / 紧急回滚）。
>
> 🌐 域名与 HTTPS 见 **[docs/DOMAIN-SETUP.md](docs/DOMAIN-SETUP.md)** —— 备案资格体检、
> 从「IP + HTTP」切到「域名 + HTTPS」的完整步骤。当前域名 `claspmoon.cn` 待备案。

四步，前三步都在本地，最后一步自动完成。

```bash
# 1. 开本地服务器（写完保存就热更新，不用刷新浏览器）
npm run dev

# 2. 写内容
#    文章   → posts/我的新文章.md
#    指南   → guides/<技术>/03-新章节.md

# 3. 本地确认无误后构建一次（会检查死链，有错会直接失败）
npm run build

# 4. 提交推送，剩下的交给 CI
git add -A
git commit -m "新增：xxx"
git push
```

`git push` 之后 GitHub Actions 会自动构建并把产物 rsync 到你的服务器，
**不需要在服务器上做任何事**。进度在仓库的 Actions 页面看。

::: tip 什么时候可以不用 build
`npm run dev` 已经能看到效果，但 `build` 会额外做两件 dev 不做的事：
**检查站内死链**、**生成 RSS 和 sitemap**。所以推送前跑一次更稳。
:::

### 只想先写不想发

`dev` 服务器开着，写多少都只在自己电脑上。GitHub 上不 push 就没人看得到。

### 想先在服务器上试，不影响正式站

用 `npm run preview`（本地预览构建产物，和线上完全一致），或者
按下面「方式 C」在服务器上另起一个端口先试。

## 目录结构

```
.
├─ index.md                    ← 首页（文章列表 + 分页）
├─ archive.md                  ← 归档页（按年分组）
├─ tags.md                     ← 标签页（点标签筛选）
├─ about.md                    ← 关于页
├─ posts/                      ← 文章：写在这里就会被自动收录
├─ guides/                     ← 学习指南：左侧目录树 + 右侧内容
│  ├─ index.md                 ← 指南总览（自动生成技术卡片）
│  ├─ rust/
│  │  ├─ index.md              ← 该技术的概览页
│  │  ├─ 01-ownership.md
│  │  ├─ 02-lifetimes.md
│  │  └─ 03-traits.md
│  ├─ python/  docker/  git/  sql/  linux/ ...
├─ public/                     ← 静态资源，原样拷到根目录
├─ docs/                       ← 内部文档，不参与构建
│  ├─ PUBLISH-SOP.md           ← 发布流程标准作业程序
│  └─ DOMAIN-SETUP.md          ← 域名备案与 HTTPS 切换指南
├─ .vitepress/
│  ├─ config.mts               ← 站点配置：导航、侧栏、搜索
│  ├─ site.ts                  ← 站点信息：域名、标题、评论配置
│  ├─ guides.ts                ← 扫描 guides/ 自动生成侧边栏
│  └─ theme/
│     ├─ index.ts              ← 主题入口（必须有）
│     ├─ posts.data.ts         ← 文章列表数据加载器
│     ├─ guides.data.ts        ← 指南总览数据加载器
│     ├─ build-hooks.ts        ← 构建结束时生成 RSS
│     ├─ style.css             ← 全局样式覆盖
│     └─ components/
│        ├─ PostList.vue       ← 文章列表 + 分页
│        ├─ TagIndex.vue       ← 标签云
│        ├─ ArchiveList.vue    ← 归档列表
│        ├─ GuideIndex.vue     ← 指南总览卡片
│        └─ Comment.vue        ← Giscus 评论区
├─ Dockerfile                  ← 多阶段构建：Node 构建 → Caddy 托管
├─ Caddyfile                   ← 自动 HTTPS 配置
├─ docker-compose.yml          ← 服务器上一键起站
└─ deploy/                     ← 部署脚本与 Nginx 备选配置
```

## 写一篇新文章

在 `posts/` 下新建 `.md` 文件，写上 frontmatter 即可：

```md
---
title: 文章标题
date: 2026-10-06
tags: [随笔, 工具]
description: 一句话摘要，会显示在列表里。不写的话会自动截取正文前 110 字。
---

正文从这里开始。
```

**只有同时写了 `title` 和 `date` 的文件才会出现在文章列表里。** 这样你可以放心在
`posts/` 下放草稿或说明页。

阅读时长会根据正文字数自动计算（中文按 350 字/分钟）。

## Markdown 增强写法

除了标准 Markdown，还有几个高频用法：

**提示块**（`tip` / `warning` / `danger` / `info` / `details`）：

```md
::: tip 小技巧
这里是提示内容。
:::

::: warning 注意
这里是警告。
:::
```

**代码块**（带行号、可高亮指定行）：

````md
```ts{2}
const a = 1
const b = 2   // 这一行会高亮
```
````

**代码组**（多语言切换的标签页）：

````md
::: code-group

```bash [npm]
npm install
```

```bash [pnpm]
pnpm install
```

:::
````

**站内链接**（`cleanUrls` 已开启，**不要写 `.html`**）：

```md
[去看 Rust 所有权](/guides/rust/01-ownership)
```

写错路径 `npm run build` 会直接报错并列出文件，这是好事，别关掉死链检查。

**其他**：`<Badge text="新" />` 徽章、`<details>` 折叠、`<kbd>` 按键样式、
直接在 md 里写 Vue 组件（比如 `<PostList :per-page="6" />`）。

## 改站点信息

打开 `.vitepress/site.ts`：

```ts
export const SITE_URL = 'https://blog.example.com'  // 换成你的域名
export const SITE_TITLE = '流沙'
export const SITE_DESC = '写代码，也写生活。'
```

`SITE_URL` 会影响 RSS、sitemap 和 og 标签，**部署前一定要改**。

导航、侧边栏、搜索、页脚在 `.vitepress/config.mts` 里。

## 改配色

`.vitepress/theme/style.css` 开头就是：

```css
:root {
  --vp-c-brand-1: #2f6fed;   /* 主色，换掉这一行就能全站换肤 */
  --vp-layout-max-width: 1400px;
}
```

深色模式的颜色在下面的 `.dark { ... }` 里。

## 开启评论

用 Giscus（基于 GitHub Discussions，免费、无后端）：

1. 建一个 public 仓库，比如 `yourname/blog-comments`
2. 该仓库 Settings → General → Features 勾选 **Discussions**
3. 安装 giscus App：https://github.com/apps/giscus
4. 打开 https://giscus.app/zh-CN ，填入仓库名，复制生成的 `repoId` 和 `categoryId`
5. 填进 `.vitepress/site.ts` 的 `GISCUS`

`repo` 为空时评论区自动隐藏，不会报错。

## 学习指南（左侧目录树 + 右侧内容）

`guides/` 下每个子目录是一个**技术方向**，左侧目录树就是按这个结构自动生成的。

```
guides/
├─ index.md          ← 指南总览，卡片自动从各技术目录生成
├─ rust/
│  ├─ index.md       ← 该技术概览，frontmatter 的 title 作为侧栏分组名
│  ├─ 01-ownership.md
│  ├─ 02-lifetimes.md
│  └─ 03-traits.md
└─ python/ ...
```

### 新增一个技术方向

1. 建目录：`mkdir guides/k8s`
2. 写概览页 `guides/k8s/index.md`：

   ```md
   ---
   title: Kubernetes
   description: 从 Pod 到 Service，把编排这件事理清楚。
   order: 7
   ---

   # Kubernetes

   这里是这个方向的学习路径说明。
   ```

3. 写章节，**文件名加数字前缀**控制顺序：

   ```md
   ---
   title: Pod 与容器
   description: 最小的调度单位。
   ---

   # Pod 与容器
   ```

4. 保存 —— **不用重启**，`npm run dev` 会自动重载并刷新左侧目录。

**不需要改任何配置文件** —— 侧边栏由 `.vitepress/guides.ts` 扫描目录生成，
指南总览页的卡片由 `.vitepress/theme/guides.data.ts` 聚合生成。

> 为什么能自动刷新：侧边栏是「配置加载时」算出来的，而 VitePress 只在配置及其依赖
> 变化时才重新加载。`config.mts` 里注册了一个 `watch-guides-sidebar` 插件，
> 监听 `guides/` 下的 md 增删后轻碰 `guides.ts` 的 mtime，触发 VitePress 走完整的
> 配置重载流程。只影响 dev，构建不受影响。

| frontmatter 字段 | 作用 | 必填 |
| --- | --- | --- |
| `title` | 侧栏显示的名字 | 是（不写会退回文件名或一级标题） |
| `description` | 概览页的简介、总览卡片的描述 | 否 |
| `order` | 技术分组的排序（小的在前），只写在 `index.md` 里 | 否（默认 99） |

::: tip 章节排序
章节按**文件名**排序，所以用 `01-`、`02-` 这样的前缀控制顺序。
不想显示数字的话，前缀只影响排序，侧栏显示的是 frontmatter 里的 `title`。
:::

### 为什么侧边栏是折叠的

每个技术分组默认折叠，避免技术多了之后侧栏太长。
**进入某个技术的页面时，VitePress 会自动展开它所在的分组。**

## 部署

### 方式 A：GitHub Actions + rsync（推荐）

服务器上**只需要一个能托静态文件的 Caddy**，不需要 Node，也不需要构建环境。
CI 挂了站点也照常运行。

**服务器准备**（一次性）：

```bash
# 1. 装 Docker
curl -fsSL https://get.docker.com | sh

# 2. 建目录
mkdir -p /opt/blog/dist

# 3. 把 Caddyfile 和 docker-compose.yml 传上去
scp Caddyfile docker-compose.yml root@你的服务器:/opt/blog/

# 4. 改 Caddyfile 里的域名，然后启动
ssh root@你的服务器 'cd /opt/blog && docker compose up -d'
```

**配置自动部署**：

1. 生成一对部署专用密钥（**不要用你平时的私钥**）：

   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/blog_deploy -C "github-actions"
   ssh-copy-id -i ~/.ssh/blog_deploy.pub root@你的服务器
   ```

2. 打开 GitHub 仓库 → Settings → Secrets and variables → Actions，添加：

   | Secret 名 | 值 |
   | --- | --- |
   | `DEPLOY_HOST` | 你的服务器 IP 或域名 |
   | `DEPLOY_USER` | `root`（或你有写权限的用户） |
   | `DEPLOY_PORT` | `22`（非标准端口才需要填） |
   | `DEPLOY_PATH` | `/opt/blog/dist/` |
   | `DEPLOY_SSH_KEY` | `~/.ssh/blog_deploy` 的**私钥全文**（`cat ~/.ssh/blog_deploy`） |

3. 推送代码，Actions 会自动构建并同步：

   ```bash
   git push origin main
   ```

之后每次 `git push` 到 `main` 分支，大约 30 秒后线上就更新了。

> `DEPLOY_PATH` 要和 `docker-compose.yml` 里挂载的 `./dist` 对应，注意结尾的斜杠 ——
> rsync 加不加斜杠行为不同，写 `/opt/blog/dist/` 表示「同步目录内容」。

### 方式 B：本地构建 + 手动同步

不想配 CI 的话，用现成的脚本：

```bash
cp deploy/deploy.env.example deploy/deploy.env
vim deploy/deploy.env          # 填服务器信息
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

### 方式 C：服务器上构建（Docker）

把整个仓库 clone 到服务器，用 `Dockerfile` 构建。适合不想把构建产物传过去的场景：

```bash
git clone <你的仓库> /opt/blog && cd /opt/blog
docker build -t my-blog .
docker run -d --name blog --restart unless-stopped \
  -p 80:80 -p 443:443 \
  -v caddy_data:/data -v caddy_config:/config \
  my-blog
```

再配合 GitHub webhook 或 `git pull && docker build` 的定时任务，就能实现推送即更新。

### 方式 D：面板部署

如果你已经在用 [Coolify](https://coolify.io/) 或 [Dokploy](https://dokploy.com/)，
直接连上 GitHub 仓库，构建命令填 `npm run build`，输出目录填 `.vitepress/dist`，
面板会自动处理域名和 HTTPS。这是最省心的方式。

### 用 Nginx 而不是 Caddy

`deploy/nginx.conf` 里有现成配置。区别是 Nginx **不会自动申请证书**，
要额外装 certbot 并配续期定时任务。

## 常见问题

**构建时报 `@theme/index` 找不到**
只要创建了 `.vitepress/theme/` 目录，就必须有 `index.ts` 入口。本仓库已经有了。

**文章日期显示成 `Mon Sep 28`**
frontmatter 里的 `date: 2026-09-28` 会被 YAML 解析成 Date 对象。
`posts.data.ts` 里已经处理了，如果你自己改这个文件注意别用 `String(date)`。

**「最后更新于」所有文章都是同一天**
`lastUpdated` 依赖 git 提交时间。CI 里必须用 `fetch-depth: 0`（workflow 里已配）。

**搜索中文搜不到**
MiniSearch 默认按空格分词。`config.mts` 里已经用 `Intl.Segmenter` 配好了中文分词。

**访问文章页 404**
`cleanUrls: true` 之后，`/posts/hello` 对应的是 `posts/hello.html`。
服务器配置里必须有 `try_files {path} {path}.html {path}/index.html /404.html`
（Caddyfile 和 nginx.conf 里都有）。

**构建失败提示死链**
VitePress 会检查站内链接。写错相对路径就会构建失败 —— 这是好事，但第一次遇到会懵。
临时可以在 config 里加 `ignoreDeadLinks: true`，但别长期开着。

**构建时刷屏 `The language 'xxx' is not loaded`**
代码块的语言标记必须是 Shiki 内置的。写 `caddy`、`gitignore`、`ini` 之类没内置的
会 fallback 成 `txt` —— 不影响构建，只是没有高亮，但日志很吵。
处理方式：把语言标记换成最接近的内置语言，或者干脆写 `txt`。

**找不到 `dist/` 目录**
VitePress 的默认输出目录是 **`.vitepress/dist`**，不是项目根的 `dist/`。
`npm run preview` 也是从这个目录起的服务。

## 常用命令

```bash
npm run dev                      # 开发服务器（热更新）
npm run build                    # 生产构建
npm run preview                  # 预览构建产物
./deploy/deploy.sh               # 手动部署
docker compose logs -f web       # 看服务器日志（含证书申请进度）
docker compose restart web       # 改完 Caddyfile 后重载
```

## 技术说明

- 构建产物是纯静态文件，服务器上不需要 Node 运行时
- 页面首屏是预渲染的静态 HTML，加载后再 hydrate 成 SPA，站内跳转不刷新
- 本地搜索索引在构建时生成，分块加载，离线可用
- RSS 和 sitemap 都在构建时生成（`feed.xml` / `sitemap.xml`）
