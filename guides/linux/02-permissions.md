---
title: 权限与用户
description: rwx 的含义、chmod 数字怎么算、SSH 密钥登录。
---

# 权限与用户

## 权限字符串怎么读

```bash
$ ls -l
-rw-r--r--  1 root root  1024 Oct  6 01:00 config.yml
drwxr-xr-x  2 root root  4096 Oct  6 01:00 sites
```

拆开看第一个字段 `-rw-r--r--`：

```
-    rw-   r--   r--
│    │     │     └── 其他人 (others)
│    │     └──────── 所属组 (group)
│    └────────────── 所有者 (owner)
└─────────────────── 类型：- 文件 / d 目录 / l 链接
```

`r` = 读，`w` = 写，`x` = 执行。

::: warning 目录上的 x 不是「执行」
对**目录**来说：
- `r` = 可以列出目录内容（`ls`）
- `x` = 可以进入目录（`cd`）、可以访问里面的文件
- `w` = 可以在目录里创建/删除文件

只有 `r` 没有 `x` 时，`ls` 能看到文件名但打不开任何一个。
:::

## chmod：两种写法

```bash
# 符号法
chmod u+x script.sh        # 所有者加执行权限
chmod g-w file.txt         # 组去掉写权限
chmod o=r file.txt         # 其他人只读
chmod a+r file.txt         # 所有人可读（a = all）

# 数字法（更常用）
chmod 644 file.txt         # rw-r--r--
chmod 755 script.sh        # rwxr-xr-x
chmod 600 ~/.ssh/id_ed25519
chmod 700 ~/.ssh
```

数字怎么算：**r=4, w=2, x=1，三组相加**。

| 数字 | 权限 | 典型用途 |
| --- | --- | --- |
| `644` | rw-r--r-- | 普通文件 |
| `600` | rw------- | 私钥、配置文件 |
| `755` | rwxr-xr-x | 可执行文件、目录 |
| `700` | rwx------ | `~/.ssh` 目录 |
| `777` | rwxrwxrwx | **几乎总是错的** |

::: danger 永远不要用 777 解决问题
网上「权限不够？`chmod -R 777`」是最糟糕的建议。它让**任何用户**
都能修改甚至替换你的文件。权限不够时应该问「该由哪个用户来读写」，
然后用 `chown` 把所有权给对的人。
:::

## chown：改所有者

```bash
chown user:group file.txt
chown -R www-data:www-data /var/www   # 递归
```

## sudo：提权的正确姿势

```bash
sudo systemctl restart nginx    # 单条命令提权
sudo -i                         # 切换到 root 的交互 shell
sudo -u postgres psql           # 以指定用户执行
```

`sudo` 会记日志（`/var/log/auth.log`），比直接 `su` 到 root 更可审计。

## SSH 密钥登录

```bash
# 1. 生成密钥对（-C 是注释，方便以后认出来）
ssh-keygen -t ed25519 -C "work-laptop"

# 2. 把公钥传到服务器
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server

# 3. 之后就可以免密登录
ssh user@server
```

::: warning 权限不对 SSH 会拒绝使用密钥
```
Permissions 0644 for 'id_ed25519' are too open.
```
修法：
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```
:::

## 加固服务器：关掉密码登录

改 `/etc/ssh/sshd_config`：

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

然后 `sudo systemctl restart sshd`。

::: danger 改之前先确认密钥能登录
**一定要在另一个终端里验证密钥登录成功之后再关密码登录。**
顺序搞反了会把自己锁在服务器外面，只能去控制台救。
:::

## 常用检查

```bash
whoami                       # 当前用户
id                           # 当前用户的 uid/gid 和所属组
groups                       # 所属组列表
sudo -l                      # 当前用户能执行哪些 sudo 命令
ls -la ~/.ssh                # 检查密钥权限
last | head                  # 最近登录记录
```

Linux 指南到这里结束。
