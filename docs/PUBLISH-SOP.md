# 博客发布 SOP

> 标准作业程序 · 从写一篇内容到它在线上可访问
>
> 适用对象：本站维护者  
> 触发条件：要发布一篇新文章 / 一个新指南章节 / 一次站点改动  
> 预计耗时：写作之外，发布动作约 3 分钟（其中 CI 跑 1~2 分钟）  
> 最后更新：2026-10-06

---

## 0. 一句话总览

**在本地写 → 本地自查 → 提交推送 → CI 自动构建并同步到服务器 → 线上验收。**

全流程只有「提交推送」这一步会产生对外影响。前面所有步骤都只发生在你自己的电脑上，  
写砸了、写一半、改主意了，都不会被别人看到。

```
阶段一（本地，别人看不到）：写内容 → 本地预览 → 构建验证
阶段二（对外，从这开始）：  提交推送 → CI 自动构建 → 同步到服务器 → 线上验收
```

只有「提交推送」这一步会产生对外影响，前面几步写砸了、写一半、改主意了都无所谓。

---

## 1. 前置准备（一次性，做过就跳过）

### 1.1 本地环境

| 项目   | 要求                      | 检查命令            |
| ---- | ----------------------- | --------------- |
| Node | 18+，推荐 22（仓库有 `.nvmrc`） | `node -v`       |
| 依赖   | 已安装                     | `npm install`   |
| Git  | 已配置 remote              | `git remote -v` |

### 1.2 服务器（一次性）

服务器上只需要一个能托管静态文件的 Caddy，**不需要 Node、不需要构建环境**。  
CI 挂了站点也照常运行。

> 本站实际状态：**已完成部署**，腾讯云 Ubuntu 24.04，  
> 目录 `/opt/blog`，Docker 开机自启已启用，容器 `restart: unless-stopped`。  
> 服务器重启后站点会自动恢复，不需要人工介入。

```bash
# 1. 装 Docker（本站已装好：Docker 29 + Compose v5）
curl -fsSL https://get.docker.com | sh

# 2. 建目录
sudo mkdir -p /opt/blog/dist && sudo chown $USER:$USER /opt/blog

# 3. 上传 Caddyfile 和 docker-compose.yml
scp Caddyfile docker-compose.yml <用户>@<服务器>:/opt/blog/

# 4. 写站点地址配置，然后启动
ssh <用户>@<服务器> 'printf "SITE_ADDRESS=:80\n" > /opt/blog/.env'
ssh <用户>@<服务器> 'cd /opt/blog && docker compose up -d'
```

#### 站点地址：一份配置支持两种模式

`Caddyfile` 里的站点地址来自环境变量 `SITE_ADDRESS`，**改这个变量就能切换模式**：

| 情况 | `SITE_ADDRESS` | 效果 |
| --- | --- | --- |
| 还没域名 | `:80` | 纯 HTTP，用 `http://<服务器IP>` 访问 |
| 有域名了 | `claspmoon.cn` | 自动申请并续期 HTTPS 证书 |
| 主域 + www | `claspmoon.cn, www.claspmoon.cn` | 多域名用**逗号分隔**，两个都签证书 |

不设这个变量会默认用 `:80`，所以忘配也能起来。

#### 域名下来后怎么切到 HTTPS

三步，都在服务器上，**不需要重新构建站点**：

```bash
# 1. 确认域名 A 记录已指向服务器，且解析生效
dig +short claspmoon.cn              # 应返回 <服务器IP>

# 2. 改 .env
ssh <用户>@<服务器> \
  'cd /opt/blog && sed -i "s|^SITE_ADDRESS=.*|SITE_ADDRESS=claspmoon.cn, www.claspmoon.cn|" .env && cat .env'

# 3. 重建容器让新配置生效
ssh <用户>@<服务器> 'cd /opt/blog && docker compose up -d --force-recreate web'
```

然后看证书申请进度：

```bash
ssh <用户>@<服务器> 'cd /opt/blog && docker compose logs -f web'
```

看到 `certificate obtained successfully` 就成了。**首次申请需要几秒到几十秒。**

::: warning 切 HTTPS 前必须确认的两件事
1. **域名已完成 ICP 备案**（国内服务器，未备案的域名走 80/443 会被拦截）
2. 443 端口放通 —— 本站已实测放通（`curl` 返回 `Connection refused` 而非超时，
   说明安全组没拦，只是当时无服务监听），**不需要改安全组**
:::

最后别忘了把 `.vitepress/site.ts` 里的 `SITE_URL` 改成 `https://claspmoon.cn` 并重新部署，
否则 RSS / sitemap 里的链接还指向 IP。

> **本站状态：已完成**（2026-10-10）。`claspmoon.cn` + `www.claspmoon.cn` 均已签好
> Let's Encrypt 证书，HTTP 自动 308 跳 HTTPS。
>
> ⚠️ 切换后**访问服务器 IP 会打不开**（308 跳到只有域名证书的 HTTPS），这是正常现象。
> 想验证服务本身是否正常，用 `curl -sI -H "Host: claspmoon.cn" http://127.0.0.1/`。
>
> 备案要求、证书排障、换域名做法见 **[`docs/DOMAIN-SETUP.md`](./DOMAIN-SETUP.md)**。

#### 服务器 SSH 加固（建议每台新机器都做）

默认的 Ubuntu 云主机开着密码登录，会被持续暴力破解（本站实测 7 天收到 8554 次尝试）。
关掉密码登录即可根治：

```bash
# 备份
sudo cp -a /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%Y%m%d-%H%M%S)

# 写一个 00- 开头的 drop-in（sshd 对同一参数取「第一个出现的值」，
# 所以它优先于 cloud-init 生成的 50-cloud-init.conf，机器重启也不会被覆盖）
sudo tee /etc/ssh/sshd_config.d/00-hardening.conf > /dev/null <<'CONF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
PubkeyAuthentication yes
CONF
sudo chmod 600 /etc/ssh/sshd_config.d/00-hardening.conf

# 校验语法后重载
sudo sshd -t && sudo systemctl reload ssh

# 确认生效
sudo sshd -T | grep -iE '^(passwordauthentication|permitrootlogin)'
```

> **务必先确认密钥登录可用再动手**。改完后验证：
>
> ```bash
> ssh -o BatchMode=yes <用户>@<服务器> 'echo ok'                    # 应该成功
> ssh -o BatchMode=yes -o PubkeyAuthentication=no -o PreferredAuthentications=password \
>     <用户>@<服务器> 'echo 不该成功'                                # 应该被拒绝
> ```
>
> 别忘了 CI 用的部署密钥也要能连（`ssh -i ~/.ssh/blog_deploy ...`）。

### 1.3 GitHub Secrets（一次性）

> **本站状态：已配置完成**，4 个 Secret 都已写入 `zhang17-24/blog`。  
> 部署专用密钥在本地 `~/.ssh/blog_deploy`，公钥已加入服务器的 authorized_keys。  
> 下面这段是记录当初怎么做的，**不需要重做**。

生成部署专用密钥 —— **不要复用你平时的私钥**：

```bash
# 本站实际执行过的命令（SSH 用户不是 root）
ssh-keygen -t ed25519 -f ~/.ssh/blog_deploy -N "" -C "github-actions-blog-deploy"
ssh-copy-id -i ~/.ssh/blog_deploy.pub <用户>@<服务器>
```

打开 GitHub 仓库 → **Settings → Secrets and variables → Actions**，添加：

| Secret 名 | 说明 | 本站实际值 |
| --- | --- | --- |
| `DEPLOY_HOST` | 服务器 IP 或域名 | 已配置 |
| `DEPLOY_USER` | SSH 用户名 | 已配置 |
| `DEPLOY_PATH` | 静态文件目录 | `/opt/blog/dist/` |
| `DEPLOY_SSH_KEY` | `~/.ssh/blog_deploy` **私钥全文** | 已配置 |
| `DEPLOY_PORT` | SSH 端口，默认 22 | 未设置（用默认 22） |

> 私钥全文用 `cat ~/.ssh/blog_deploy` 拿到，含 `-----BEGIN` 到 `-----END` 全部行。
>
> 配置密钥这一步用命令行做也行 —— GitHub 要求用仓库公钥做 libsodium sealed box 加密，
> Python 里 `PyNaCl` 的 `SealedBox` 可以直接干这件事。

### 1.4 改站点信息（首次发布前必须做）

打开 `.vitepress/site.ts`：

```ts
export const SITE_URL = 'https://claspmoon.cn'   // ← 换成你的域名
export const SITE_TITLE = '流沙'
export const SITE_DESC = '写代码，也写生活。'
```

`SITE_URL` 会影响 RSS、sitemap 和 og 标签，**不改成真实域名，RSS 订阅者拿到的链接是错的**。

> 本站当前使用 `https://claspmoon.cn`，HTTPS 与证书自动续期均已就绪。

---

## 2. 标准发布流程

### Step 1 · 开本地环境

```bash
cd blog
npm run dev
```

打开 `http://localhost:5173/`。改任何 `.md` 文件都是**毫秒级热更新**，不用刷新浏览器。

> 服务一直开着就行，可以写一整天。

### Step 2 · 写内容

#### 情况 A：写一篇博客文章

在 `posts/` 下新建 `.md`：

```md
---
title: 文章标题
date: 2026-10-06
tags: [随笔, 工具]
description: 一句话摘要，会显示在列表里。不写则自动截取正文前 110 字。
---

正文从这里开始。
```

**判据：只有同时写了 `title` 和 `date` 的文件才会进文章列表。**  
所以 `posts/` 下可以放心放草稿、素材、说明页，只要不写 `date` 就不会被收录。

#### 情况 B：写一个指南章节

已有技术方向 → 直接在对应目录下加文件，**文件名前缀数字**控制顺序：

```
guides/rust/04-macros.md
```

新技术方向 → 建目录 + 概览页：

```bash
mkdir guides/k8s
```

`guides/k8s/index.md`：

```md
---
title: Kubernetes
description: 从 Pod 到 Service，把编排这件事理清楚。
order: 8
---

# Kubernetes

这里是这个方向的学习路径说明。
```

然后写章节 `guides/k8s/01-pods.md`：

```md
---
title: Pod 与容器
description: 最小的调度单位。
---

# Pod 与容器
```

**保存即可，不用重启** —— 左侧目录树会自动刷新（`watch-guides-sidebar` 插件负责）。

#### 情况 C：放图片

图片统一放 `public/` 下，用**绝对路径**引用：

```bash
cp ~/Desktop/diagram.png public/images/diagram.png
```

```md
![架构图](/images/diagram.png)
```

`public/` 下的文件会被原样拷到站点根目录，所以 `/images/diagram.png` 就是最终 URL。

> **不要**用相对路径引用图片，也不要放 `posts/` 旁边 —— 构建后路径会错。

#### 情况 D：只想先存草稿

两种做法，任选：

- **不写 `date`** —— 文件留在 `posts/` 里，不写日期就不会进列表
- **放到 `drafts/` 目录** —— 然后加进 `.vitepress/config.mts` 的 `srcExclude`

### Step 3 · 本地自查

对照下面的**发布前检查清单**逐项过一遍。这是全流程里最容易被跳过、也最容易出问题的一步。

### Step 4 · 构建验证

```bash
npm run build
```

**必须看到 `build complete`，不能有报错。**

`build` 会做两件 dev 不做的事：

1. **检查站内死链** —— 链接写错会直接构建失败并列出文件名
2. **生成 RSS 和 sitemap** —— 只在构建时产出

想更接近线上效果，可以：

```bash
npm run preview     # http://localhost:4173，跑的是构建产物
```

> `preview` 是静态文件服务，**改了代码重新 build 之后必须重启它**，否则看的是旧产物。

### Step 5 · 提交

```bash
git add -A
git status              # ← 确认一遍要提交的文件，别把临时文件带进去
git commit -m "新增：Rust 指南所有权章节"
```

**Commit message 建议格式**（中文冒号，一眼能看懂做了什么）：

```
新增：<做了什么>
修改：<改了什么>
修复：<修了什么>
```

> 检查 `git status` 时如果看到 `*.timestamp-*.mjs`，说明 `.gitignore` 失效了，  
> 那是 VitePress 加载 TS 配置时的临时文件，不该提交。

### Step 6 · 推送并观察 CI

```bash
git push
```

推送后 GitHub Actions 自动触发（workflow 定义在 `.github/workflows/deploy.yml`）：

```
检出代码（fetch-depth: 0）→ 装 Node 22 → npm ci → npm run build
  → 配置 SSH → rsync 同步到服务器 → 完成
```

打开仓库的 **Actions** 页面看进度。绿灯通常 1~2 分钟。

> `concurrency` 已配置为只保留最新一次部署，连续 push 不会排队打架。

### Step 7 · 线上验收

**必须实际打开线上站点确认**，不要只看 CI 绿灯。

```bash
# 1. 首页能打开
curl -s -o /dev/null -w "%{http_code}\n" https://<你的域名>/

# 2. 新文章能访问
curl -s -o /dev/null -w "%{http_code}\n" https://<你的域名>/posts/新文章slug
```

然后浏览器里过一遍：

- [ ] 首页文章列表里有新文章，且排在正确的日期位置
- [ ] 点进去正文完整、代码块有高亮、图片能显示
- [ ] 顶部搜索框搜新文章的关键词能搜到
- [ ] 标签页 / 归档页里有它
- [ ] 手机上也看一眼（侧边栏会收成抽屉）

---

## 3. 发布前检查清单

> 建议复制这一节，逐项打勾。

### 内容

- [ ] **frontmatter 有 `title` 和 `date`**（文章）或 `title`（指南章节）
- [ ] `date` 格式是 `YYYY-MM-DD`，且**是真实日期**（写错会导致排序错乱）
- [ ] `tags` 是数组格式 `[标签1, 标签2]`，不是逗号分隔的字符串
- [ ] 标题没有和已有文章重复（搜索框搜一下）
- [ ] 通读一遍，没有明显错别字和半截句子
- [ ] 没有残留的 `TODO` / `xxx` / 占位内容

### 链接与资源

- [ ] **站内链接不带 `.html`** —— 写 `/guides/rust/01-ownership` 而不是 `.../01-ownership.html`
- [ ] 站内链接指向的页面**真的存在**（构建会检查，但早发现早改）
- [ ] 图片放在 `public/` 下，用 `/images/xxx.png` 绝对路径引用
- [ ] 外链是完整的 `https://` 开头
- [ ] 引用的外部链接**自己能打开**（别贴已经 404 的链接）

### 代码块

- [ ] 每个代码块都标了语言（`bash / `ts / \`\`\`md）
- [ ] **语言标记是 Shiki 内置的** —— `caddy`、`gitignore`、`ini` 不是内置的，  
  会 fallback 成纯文本并刷一屏警告。用 `txt` 或最接近的内置语言代替
- [ ] 长命令没有超出容器宽度（会出横向滚动条）

### 元信息

- [ ] `description` 写了（影响列表摘要、搜索结果、RSS 描述）
- [ ] 文章日期不是未来时间（未来日期会让它一直排在最前）

---

## 4. 异常处理

### 4.1 构建失败：死链

```
(!) Found dead link /guides/rust/04-macros in file posts/xxx.md
1 dead link(s) found.
```

**原因**：站内链接指向了不存在的页面。

**处理**：

1. 检查路径拼写，注意**不要带 `.html`**
2. 确认目标文件真的存在，且不是被 `srcExclude` 排除了
3. 如果是**故意**的占位链接（比如指向还没写的文章），临时在 config 里加  
   `ignoreDeadLinks: true` —— 但**不要长期开着**，死链检查是很有价值的护栏

### 4.2 构建警告：Shiki 语言未加载

```
The language 'gitignore' is not loaded, falling back to 'txt' for syntax highlighting.
```

**不影响构建**，只是没高亮 + 日志很吵。把语言标记换成 `txt` 即可。

### 4.3 CI 失败：rsync 报 Permission denied

**原因**：`DEPLOY_SSH_KEY` 配错了，或者公钥没加到服务器。

**处理**：

```bash
# 本地验证密钥本身能用
ssh -i ~/.ssh/blog_deploy root@<服务器> 'echo ok'

# 不能用 → 重新拷贝公钥
ssh-copy-id -i ~/.ssh/blog_deploy.pub root@<服务器>

# 能用但 CI 失败 → 检查 Secret 里私钥全文是否完整（含首尾的 ----- 行）
```

### 4.4 CI 失败：主机密钥验证失败

**原因**：workflow 里的 `ssh-keyscan` 没抓到，或服务器换了主机密钥。

**处理**：在 workflow 的「配置 SSH」步骤里临时加 `-o StrictHostKeyChecking=no`  
（仅排障用，长期开着有中间人风险）。

### 4.5 部署成功但线上是旧内容

**原因**：浏览器缓存，或 CDN 缓存。

**处理**：

1. 强制刷新：`Cmd + Shift + R`
2. 用 curl 直接看服务端返回的内容确认是不是真的没更新：
   ```bash
   curl -s https://<域名>/ | grep "新文章标题"
   ```
3. 如果服务端确实没更新 → 去服务器上看文件时间戳：
   ```bash
   ssh root@<服务器> 'ls -la /opt/blog/dist/ | head'
   ```

### 4.6 站点打不开 / 证书没签下来

**原因**：Caddy 申请 Let's Encrypt 证书失败。常见于域名没解析到服务器、  
或 80 端口没放通。

**处理**：

```bash
ssh root@<服务器> 'cd /opt/blog && docker compose logs -f web'
```

日志里会写明证书申请卡在哪一步。检查：

- 域名 A 记录是否指向服务器 IP（`dig <域名> +short`）
- 服务器 80 / 443 端口是否放通（云厂商安全组 + 本机防火墙）
- Caddyfile 里的域名拼写是否正确

### 4.7 页面 404（其他页面正常）

**原因**：`cleanUrls: true` 时 `/posts/hello` 对应 `posts/hello.html`，  
服务器必须有 `try_files` 兜底。

**处理**：确认 Caddyfile 里有这一行：

```
try_files {path} {path}.html {path}/index.html /404.html
```

少了它，所有不带 `.html` 的路径都会 404。

### 4.8 紧急回滚

**内容写错了要立刻撤下**：

```bash
git revert <出问题的commit>
git push
```

CI 会自动把回滚后的版本部署上去，1~2 分钟后线上恢复。

> **不要用 `git reset --hard` + `git push --force`** —— 会改写历史，  
> 而且 CI 可能因为 concurrency 取消而处于不确定状态。`revert` 更安全。

**整个站点挂了**：去服务器把静态目录换成上一版备份，或直接 `docker compose down`  
先止损，再排查。

---

## 5. 附录

### 5.1 frontmatter 字段速查

**文章（`posts/*.md`）**

| 字段            | 作用                | 必填               |
| ------------- | ----------------- | ---------------- |
| `title`       | 文章标题              | **是**            |
| `date`        | 发布日期，`YYYY-MM-DD` | **是**（不写就不进列表）   |
| `tags`        | 标签数组，`[随笔, 工具]`   | 否                |
| `description` | 列表摘要、RSS 描述       | 否（自动截取正文前 110 字） |

**指南概览页（`guides/<技术>/index.md`）**

| 字段            | 作用         | 必填       |
| ------------- | ---------- | -------- |
| `title`       | 左侧目录树里的分组名 | **是**    |
| `description` | 总览卡片的简介    | 否        |
| `order`       | 分组排序（小的在前） | 否（默认 99） |

**指南章节（`guides/<技术>/NN-xxx.md`）**

| 字段            | 作用         | 必填    |
| ------------- | ---------- | ----- |
| `title`       | 左侧目录树里的章节名 | **是** |
| `description` | 章节简介       | 否     |

> 章节顺序由**文件名前缀**决定（`01-`、`02-`），前缀只影响排序，  
> 侧栏显示的是 `title`。

### 5.2 命令速查

```bash
npm run dev        # 本地开发服务器，http://localhost:5173，热更新
npm run build      # 生产构建 → .vitepress/dist（会查死链、生成 RSS）
npm run preview    # 本地预览构建产物，http://localhost:4173

git add -A && git commit -m "新增：xxx" && git push    # 发布

./deploy/deploy.sh                  # 手动部署（不走 CI，本地构建后 rsync）
```

**服务器侧命令**（本站目录 `/opt/blog`，连接信息见 `deploy/deploy.env`）：

```bash
ssh <用户>@<服务器> 'cd /opt/blog && docker compose ps'            # 看容器状态
ssh <用户>@<服务器> 'cd /opt/blog && docker compose logs -f web'   # 看日志（含证书申请）
ssh <用户>@<服务器> 'cd /opt/blog && docker compose up -d --force-recreate web'  # 改完配置生效
ssh <用户>@<服务器> 'df -h /'                                      # 看磁盘
```

### 5.3 目录约定

```
blog/
├─ index.md                 首页（文章列表 + 分页）
├─ posts/                   博客文章 —— 写这里就会被自动收录
├─ guides/                  学习指南 —— 左侧目录树自动生成
│  ├─ index.md              指南总览（卡片自动生成）
│  └─ <技术>/
│     ├─ index.md           该技术概览（title 作分组名，order 控排序）
│     └─ NN-xxx.md          章节（NN 控顺序）
├─ public/                  静态资源，原样拷到站点根目录（图片放这）
├─ docs/                    内部文档（本文件）—— 不参与构建
├─ .vitepress/
│  ├─ config.mts            站点配置：导航、侧栏、搜索
│  ├─ site.ts               站点信息：域名、标题、评论配置
│  ├─ guides.ts             扫描 guides/ 生成侧边栏
│  └─ theme/                主题、组件、样式
├─ Dockerfile / Caddyfile / docker-compose.yml    服务器部署配置
└─ deploy/                  手动部署脚本
```

### 5.4 发布节奏建议

- **当天写、当天发**：写完立刻走流程，3 分钟就上线，别攒着
- **系列文章**：同一主题的拆成多篇时，建议**一次 push 一起发**，  
  避免读者点进去发现「下一篇」是空的
- **大改动**（改配色、改导航、加功能）：先在 `npm run preview` 里过一遍，  
  再推。这类改动影响面比单篇文章大得多

### 5.5 什么情况**不要**走这个流程

- **只改错别字**：可以直接在 GitHub 网页上编辑文件并提交，CI 一样会跑
- **改服务器配置**（`Caddyfile` / `.env`）：这是服务器侧的事，不经过 CI。  
  改完 `scp` 上去，再 `docker compose up -d --force-recreate web` 让配置生效
- **改 CI 配置本身**（`.github/workflows/`）：推送后 CI 会用它自己跑一遍，  
  如果写错了 CI 会失败，站点保持上一版不变（不会挂）

---

## 附：流程图（纯文本版，方便贴到别处）

```
[1] npm run dev
     ↓
[2] 写 posts/xxx.md 或 guides/<技术>/NN-xxx.md
     ↓
[3] 对照检查清单自查
     ↓
[4] npm run build  ← 必须通过（查死链 + 生成 RSS）
     ↓
[5] git add -A && git commit -m "新增：xxx"
     ↓
[6] git push  ──────→ GitHub Actions
                          ↓
                     npm ci && npm run build
                          ↓
                     rsync → 服务器 /opt/blog/dist/
                          ↓
                     Caddy 直接托管，无需重启
     ↓
[7] 线上验收：curl 状态码 + 浏览器逐项确认
```
