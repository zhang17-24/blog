---
title: SQL
description: 从查询语法到索引原理，把数据库真正用对。
order: 8
---

# SQL

SQL 的语法半天就能学完，但「写出来能跑」和「跑得快、结果对」之间
隔着索引、执行计划和一堆反直觉的规则。

## 章节

| # | 章节 | 内容 |
| --- | --- | --- |
| 01 | [基础查询](/guides/sql/01-basics) | SELECT、JOIN、聚合、NULL 陷阱 |
| 02 | [索引与优化](/guides/sql/02-index) | B+ 树、联合索引、EXPLAIN 怎么读 |

## 示例表结构

后面两章都用这套表：

```sql
CREATE TABLE users (
    id         BIGINT PRIMARY KEY,
    name       VARCHAR(64)  NOT NULL,
    email      VARCHAR(128) NOT NULL,
    created_at TIMESTAMP    NOT NULL
);

CREATE TABLE orders (
    id         BIGINT PRIMARY KEY,
    user_id    BIGINT      NOT NULL,
    amount     DECIMAL(10,2) NOT NULL,
    status     VARCHAR(16) NOT NULL,
    created_at TIMESTAMP   NOT NULL
);
```

::: tip 学习建议
**边看边在本地跑。** 装个 SQLite 或起一个 PostgreSQL 容器就行：

```bash
docker run -d --name pg -e POSTGRES_PASSWORD=dev -p 5432:5432 postgres:16-alpine
```
:::
