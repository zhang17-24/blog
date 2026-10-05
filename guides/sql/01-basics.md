---
title: 基础查询
description: SELECT、JOIN、聚合，以及 NULL 带来的那堆坑。
---

# 基础查询

## 逻辑执行顺序

写 SQL 的顺序和数据库**实际执行**的顺序不一样。记住执行顺序能解释大部分困惑：

```
FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

这解释了两件事：

- 为什么 `WHERE` 里不能用 `SELECT` 里定义的别名（那时还没执行到 SELECT）
- 为什么 `ORDER BY` 里可以用别名（SELECT 已经执行完了）

## JOIN 的四种类型

```sql
-- INNER JOIN：两边都有匹配才保留
SELECT u.name, o.amount
FROM users u
INNER JOIN orders o ON o.user_id = u.id;

-- LEFT JOIN：左表全保留，右表没匹配就填 NULL
SELECT u.name, o.amount
FROM users u
LEFT JOIN orders o ON o.user_id = u.id;
-- 没有订单的用户也会出现，amount 为 NULL
```

| 类型 | 保留什么 |
| --- | --- |
| `INNER JOIN` | 只保留两边都匹配的 |
| `LEFT JOIN` | 保留左表全部 |
| `RIGHT JOIN` | 保留右表全部（一般改写成 LEFT JOIN 更好读） |
| `FULL OUTER JOIN` | 两边都保留 |

::: warning LEFT JOIN 后加 WHERE 的陷阱
```sql
-- 错误：这样写等于 INNER JOIN
SELECT u.name, o.amount
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.status = 'paid';     -- NULL != 'paid'，没订单的用户被过滤掉了

-- 正确：条件要放在 ON 里
SELECT u.name, o.amount
FROM users u
LEFT JOIN orders o ON o.user_id = u.id AND o.status = 'paid';
```
:::

## 聚合与 GROUP BY

```sql
SELECT
    user_id,
    COUNT(*)              AS order_count,
    SUM(amount)           AS total,
    AVG(amount)           AS avg_amount,
    MAX(created_at)       AS last_order
FROM orders
WHERE status = 'paid'
GROUP BY user_id
HAVING COUNT(*) >= 3          -- 过滤聚合结果用 HAVING，不是 WHERE
ORDER BY total DESC
LIMIT 20;
```

**`WHERE` 过滤行，`HAVING` 过滤分组。** 这是必须分清的一条。

## NULL：最反直觉的部分

```sql
SELECT * FROM users WHERE email = NULL;      -- 永远返回空！
SELECT * FROM users WHERE email IS NULL;     -- 正确写法
```

NULL 表示「未知」，所以任何和它的比较结果都是「未知」，不是 true。

| 表达式 | 结果 |
| --- | --- |
| `NULL = NULL` | NULL（不是 true） |
| `NULL <> NULL` | NULL |
| `NULL AND false` | false |
| `NULL AND true` | NULL |
| `NULL OR true` | true |
| `COUNT(*)` | 数所有行，**包含 NULL** |
| `COUNT(列)` | 只数非 NULL 的行 |

::: warning 聚合函数会跳过 NULL
```sql
-- 如果 100 条记录里有 20 条 amount 是 NULL
SELECT AVG(amount) FROM orders;   -- 分母是 80，不是 100
```
需要把 NULL 当 0 参与计算时，用 `AVG(COALESCE(amount, 0))`。
:::

## 窗口函数：分组但不折叠

```sql
SELECT
    user_id,
    amount,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn,
    SUM(amount)  OVER (PARTITION BY user_id)                          AS user_total
FROM orders;
```

和 `GROUP BY` 的区别：**窗口函数保留每一行**，只是附加了聚合信息。
`rn = 1` 就是每个用户最近的那笔订单 —— 取「每组最新一条」的标准写法。

## 常见坑速查

| 现象 | 原因 |
| --- | --- |
| `= NULL` 查不到数据 | 应该用 `IS NULL` |
| `LEFT JOIN` 结果变少了 | `WHERE` 条件把 NULL 行过滤掉了，应放 `ON` 里 |
| `AVG` 结果偏高 | 分母不含 NULL 行 |
| `SELECT` 里有非聚合列但没在 `GROUP BY` 里 | 严格模式下报错，宽松模式下取随机值 |
| 字符串比较结果奇怪 | 排序规则（collation）问题，注意大小写敏感性 |

下一篇：[索引与优化](/guides/sql/02-index)。
