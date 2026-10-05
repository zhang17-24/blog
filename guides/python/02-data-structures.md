---
title: 数据结构
description: list / dict / set 的时间复杂度，以及该怎么选。
---

# 数据结构

选错容器是 Python 性能问题里最常见的原因。核心只有一张复杂度表。

## 复杂度速查

| 操作 | `list` | `dict` | `set` |
| --- | --- | --- | --- |
| 索引访问 `a[i]` | **O(1)** | — | — |
| 按 key 查找 | O(n) | **O(1)** | **O(1)** |
| `in` 判断 | O(n) | **O(1)** | **O(1)** |
| 尾部追加 | **O(1)** 均摊 | O(1) 均摊 | O(1) 均摊 |
| 头部插入 `insert(0, x)` | O(n) | — | — |
| 中间删除 | O(n) | O(1) | O(1) |
| 有序遍历 | O(n) | O(n) | O(n) |

**记住一条就够**：需要频繁做 `in` 判断时，先想想能不能换成 `set` 或 `dict`。

```python
# 慢：每次 in 都是 O(n)，整体 O(n²)
def has_duplicate_slow(items):
    seen = []
    for x in items:
        if x in seen:
            return True
        seen.append(x)
    return False

# 快：O(n)
def has_duplicate(items):
    return len(set(items)) != len(items)
```

## list：什么时候不该用

`list` 只在**尾部**操作时才高效。下面两种场景该换容器：

```python
# 场景一：频繁头部插入 → 用 deque
from collections import deque
q = deque()
q.appendleft(1)     # O(1)，而 list.insert(0, 1) 是 O(n)
q.popleft()

# 场景二：需要按优先级取 → 用 heapq
import heapq
h = [3, 1, 2]
heapq.heapify(h)
heapq.heappush(h, 0)
heapq.heappop(h)    # 总是取最小值，O(log n)
```

## dict：现代用法

Python 3.7+ 的 `dict` **保证插入顺序**，所以它同时也是一个有序映射。

```python
# 计数：别写 if key in d 那套了
from collections import Counter
words = ["a", "b", "a", "c", "a"]
Counter(words).most_common(2)     # [('a', 3), ('b', 1)]

# 分组
from collections import defaultdict
groups = defaultdict(list)
for name, dept in [("小明", "技术"), ("小红", "产品"), ("小刚", "技术")]:
    groups[dept].append(name)
# {'技术': ['小明', '小刚'], '产品': ['小红']}

# 合并（3.9+）
a = {"x": 1}
b = {"y": 2}
a | b          # {'x': 1, 'y': 2}，右边的覆盖左边
```

## set：去重和集合运算

```python
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

a & b     # {3, 4}      交集
a | b     # {1,2,3,4,5,6}  并集
a - b     # {1, 2}      差集
a ^ b     # {1,2,5,6}   对称差
```

::: warning set 的元素必须可哈希
`list` 和 `dict` 不能放进 `set`。需要放的话转成 `tuple`，
或者用 `frozenset`。
:::

## 什么时候用 namedtuple / dataclass

当 `dict` 的 key 是固定的几个字段时，`dict` 就不合适了 ——
拼错 key 不会报错，IDE 也补全不了。

```python
from dataclasses import dataclass

@dataclass(frozen=True)     # frozen=True 让它可哈希，能放进 set
class Point:
    x: float
    y: float

p = Point(1.0, 2.0)
p.x            # 属性访问，有补全和类型检查
```

## 小结

| 需求 | 该用 |
| --- | --- |
| 有序、按索引访问、尾部增删 | `list` |
| 两端都要增删 | `deque` |
| 按 key 快速查找 | `dict` |
| 去重、集合运算 | `set` |
| 取最小/最大 | `heapq` |
| 计数 | `Counter` |
| 分组 | `defaultdict(list)` |
| 固定字段的结构 | `dataclass` |

下一篇：[异步编程](/guides/python/03-async)。
