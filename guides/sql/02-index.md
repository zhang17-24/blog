---
title: 索引与优化
description: B+ 树为什么这么设计、联合索引的最左前缀、EXPLAIN 怎么读。
---

# 索引与优化

## 为什么是 B+ 树

数据库索引不用二叉树、不用哈希，而是 B+ 树，原因是**磁盘 IO 次数**。

- 二叉树在 100 万条数据上深度约 20 → 最坏 20 次磁盘读取
- B+ 树一个节点存几百个 key（一页 16 KB）→ 深度只有 3～4 → 3～4 次磁盘读取

而且 B+ 树的叶子节点是**链表**，所以范围查询（`BETWEEN`、`>`、排序）
可以顺着链表扫，不需要回到根节点。

## 索引的类型

| 类型 | 说明 | 适用 |
| --- | --- | --- |
| 主键索引 | 聚簇索引，数据就存在叶子节点上 | 主键 |
| 二级索引 | 叶子节点存主键值，需要回表 | 普通查询条件 |
| 联合索引 | 多个列组成一个索引 | 多条件组合查询 |
| 唯一索引 | 带唯一约束 | 邮箱、用户名 |
| 覆盖索引 | 查询所需字段全在索引里，无需回表 | 高频查询 |

## 联合索引与最左前缀

```sql
CREATE INDEX idx_user_status_time ON orders (user_id, status, created_at);
```

这个索引相当于按 `(user_id, status, created_at)` 排好序的目录。
**能用上索引的条件必须从最左边开始连续匹配**：

| 查询条件 | 能否用上索引 |
| --- | --- |
| `user_id = 1` | ✅ |
| `user_id = 1 AND status = 'paid'` | ✅ |
| `user_id = 1 AND status = 'paid' AND created_at > '2026-01-01'` | ✅ 完全匹配 |
| `status = 'paid'` | ❌ 跳过了最左列 |
| `created_at > '2026-01-01'` | ❌ 跳过了前两列 |
| `user_id = 1 AND created_at > '2026-01-01'` | ⚠️ 只用到 `user_id` |

::: tip 建联合索引的顺序
**等值条件在前，范围条件在后。**
一旦某个列用了范围查询（`>`、`<`、`BETWEEN`），它后面的列就都用不上索引了。
:::

## 索引失效的几种情况

```sql
-- ❌ 列上用了函数
WHERE YEAR(created_at) = 2026
-- ✅ 改写成范围
WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01'

-- ❌ 隐式类型转换（user_id 是 BIGINT，传了字符串）
WHERE user_id = '123'

-- ❌ 前导通配符
WHERE name LIKE '%小明'
-- ✅ 后缀通配符可以用索引
WHERE name LIKE '小明%'

-- ❌ 在索引列上做运算
WHERE amount * 2 > 100
-- ✅ 把运算挪到右边
WHERE amount > 50
```

**核心原则：索引列必须「干净地」出现在比较符号左边。**

## EXPLAIN 怎么读

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE user_id = 1 AND status = 'paid';
```

重点看这几列：

| 列 | 关注什么 |
| --- | --- |
| `type` | 访问类型。`const` > `eq_ref` > `ref` > `range` > **`ALL`（全表扫描，危险）** |
| `key` | 实际用了哪个索引。是 `NULL` 说明没走索引 |
| `rows` | 预估扫描行数，越小越好 |
| `Extra` | `Using index`（覆盖索引，好）／ `Using filesort`（额外排序，可能慢）／ `Using temporary`（用了临时表，通常要优化） |

::: warning EXPLAIN 的 rows 只是估算
优化器的统计信息可能过期。如果估算和实际差很多，先跑 `ANALYZE TABLE` 更新统计信息。
:::

## 优化的正确顺序

1. **先看慢查询日志**，找到真正慢的那几条 —— 别凭感觉优化
2. **`EXPLAIN` 看执行计划**，确认是全表扫描还是索引失效
3. **改 SQL 或加索引**，优先改 SQL（函数、隐式转换这类问题加索引也没用）
4. **还不行再考虑**：覆盖索引、冗余字段、分页优化、读写分离

## 几个具体技巧

```sql
-- 深分页：LIMIT 1000000, 20 会扫描 100 万行
-- 改成用游标（记住上一页最后一个 id）
SELECT * FROM orders WHERE id > 1000000 ORDER BY id LIMIT 20;

-- 用 EXISTS 代替 IN 处理子查询（大表时通常更快）
SELECT * FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);

-- 批量插入用一条语句，别循环
INSERT INTO orders (user_id, amount) VALUES (1, 10), (2, 20), (3, 30);
```

::: danger 索引不是越多越好
每个索引都会**拖慢写入**（INSERT/UPDATE 都要维护索引）并占用磁盘。
一张表的索引通常控制在 5 个以内，优先保证高频查询。
:::

SQL 指南到这里结束。
