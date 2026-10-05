---
title: Shell 基础
description: 管道、重定向，以及 grep / sed / awk 的实用用法。
---

# Shell 基础

## 管道与重定向

```bash
# 管道：把前一个命令的输出作为后一个命令的输入
cat access.log | grep "500" | wc -l

# 重定向
command > file       # 覆盖写入
command >> file      # 追加
command 2> err.log   # 只重定向错误输出
command &> all.log   # 标准输出 + 错误都写入
command > /dev/null  # 丢弃输出
```

::: tip 最常用的组合
```bash
# 既看输出又存文件
command 2>&1 | tee output.log

# 后台运行且不因断开 SSH 而终止
nohup command > out.log 2>&1 &
```
:::

## 文本处理三剑客

### grep：查找

```bash
grep -rn "TODO" src/          # 递归 + 显示行号
grep -i "error" app.log       # 忽略大小写
grep -v "debug" app.log       # 反向匹配（排除）
grep -c "GET" access.log      # 只输出匹配行数
grep -A 3 -B 1 "Exception" app.log   # 带前后文
```

### sed：替换

```bash
sed -i 's/old/new/g' file.txt            # 原地替换所有匹配
sed -i 's/old/new/g' *.md                # 批量改多个文件
sed -n '10,20p' file.txt                 # 只打印 10-20 行
sed '/^#/d' file.txt                     # 删掉所有注释行
```

::: warning macOS 的 sed 和 Linux 不一样
macOS 是 BSD sed，`-i` 必须跟一个参数：
```bash
sed -i '' 's/old/new/g' file.txt      # macOS
sed -i 's/old/new/g' file.txt         # Linux
```
跨平台脚本里建议用 `perl -pi -e 's/old/new/g' file.txt`，行为一致。
:::

### awk：按列处理

```bash
awk '{print $1}' file.txt                # 打印第一列
awk -F: '{print $1}' /etc/passwd         # 指定分隔符
awk '$3 > 100 {print $1, $3}' data.txt   # 条件过滤
awk '{sum += $1} END {print sum}' nums   # 求和
```

`$0` 是整行，`$1` 是第一列，`NR` 是行号，`NF` 是列数。

## 文件查找

```bash
find . -name "*.log" -mtime +7           # 7 天前修改的日志
find . -type f -size +100M               # 大于 100MB 的文件
find . -name "*.tmp" -delete             # 找到并删除
find . -type f -exec grep -l "TODO" {} + # 对每个文件执行命令
```

`locate` 比 `find` 快得多（走索引数据库），但索引需要 `updatedb` 更新。

## 查看文件内容

| 命令 | 用途 |
| --- | --- |
| `cat file` | 全部输出 |
| `less file` | 分页查看（`/` 搜索、`q` 退出） |
| `head -n 20 file` | 前 20 行 |
| `tail -n 20 file` | 后 20 行 |
| `tail -f file` | 实时跟踪 ← 看日志必备 |
| `wc -l file` | 统计行数 |

## 磁盘与进程

```bash
df -h                          # 磁盘使用情况（人类可读单位）
du -sh * | sort -rh | head     # 当前目录下最大的几个
free -h                        # 内存
top / htop                     # 进程（htop 更好看，需要装）
ps aux | grep nginx            # 找特定进程
lsof -i :8080                  # 谁占用了 8080 端口 ← 非常常用
kill -9 <PID>                  # 强杀进程
```

## 一个实用的组合

排查「磁盘满了」的完整流程：

```bash
df -h                                   # 1. 哪个分区满了
du -sh /* 2>/dev/null | sort -rh | head # 2. 哪个目录大
du -sh /var/* | sort -rh | head         # 3. 逐层深入
find /var/log -name "*.log" -size +500M # 4. 找到大日志文件
truncate -s 0 /var/log/big.log          # 5. 清空（比 rm 好，不会让进程继续写入已删除文件）
```

::: tip 为什么用 truncate 而不是 rm
如果某个进程正持有这个文件句柄，`rm` 之后磁盘空间**不会释放**，
直到进程重启。`truncate -s 0` 直接把内容清空，空间立刻回收。
:::

下一篇：[权限与用户](/guides/linux/02-permissions)。
