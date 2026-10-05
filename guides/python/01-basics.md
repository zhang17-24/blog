---
title: 基础语法
description: 类型系统、可变与不可变、作用域规则，以及几个经典陷阱。
---

# 基础语法

## 类型是动态的，但别乱来

```python
x = 1          # int
x = "hello"    # 现在变成 str 了，合法但不推荐
```

现代 Python 项目建议都加类型标注：

```python
def greet(name: str, times: int = 1) -> str:
    return f"你好，{name}！" * times
```

标注**不会**在运行时强制检查，但配合 `mypy` 或 `pyright` 能在写代码时抓出大量错误。

## 可变 vs 不可变：最重要的分界线

| 不可变 | 可变 |
| --- | --- |
| `int` `float` `str` `tuple` `frozenset` | `list` `dict` `set` `bytearray` |

这个区别带来两个经典陷阱。

### 陷阱一：默认参数

```python
# 错误写法
def add_item(item, target=[]):
    target.append(item)
    return target

add_item(1)   # [1]
add_item(2)   # [1, 2]  ← 不是 [2]！
```

默认参数**只在函数定义时求值一次**，所以那个空列表被所有调用共享了。

```python
# 正确写法
def add_item(item, target=None):
    if target is None:
        target = []
    target.append(item)
    return target
```

### 陷阱二：浅拷贝

```python
a = [[1, 2], [3, 4]]
b = a.copy()        # 浅拷贝，内层还是同一个对象
b[0].append(99)
print(a)            # [[1, 2, 99], [3, 4]]  ← a 也被改了

import copy
c = copy.deepcopy(a)   # 深拷贝才安全
```

## 作用域：LEGB 规则

变量查找顺序是 **L**ocal → **E**nclosing → **G**lobal → **B**uilt-in。

```python
count = 0

def increment():
    global count      # 不加这句，下面那行会创建局部变量并报 UnboundLocalError
    count += 1
```

::: warning 闭包的延迟绑定
```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])   # [2, 2, 2]，不是 [0, 1, 2]
```
闭包捕获的是**变量本身**，不是当时的值。修法是加默认参数固化：
```python
funcs = [lambda i=i: i for i in range(3)]   # [0, 1, 2]
```
:::

## 字符串格式化

```python
name, score = "小明", 92.5

f"{name} 考了 {score:.1f} 分"        # 推荐，Python 3.6+
"{} 考了 {:.1f} 分".format(name, score)
"%s 考了 %.1f 分" % (name, score)     # 老写法，新代码别用
```

## 常见坑速查

| 现象 | 原因 |
| --- | --- |
| 默认参数在多次调用间「记住了」值 | 默认参数只求值一次 |
| 改了 `b` 结果 `a` 也变了 | 浅拷贝，内层对象共享 |
| `UnboundLocalError` | 函数内赋值被当成局部变量，需要 `global` / `nonlocal` |
| `is` 比较整数偶尔「正确」 | 小整数缓存（-5~256），永远用 `==` 比较值 |
| 循环里删列表元素漏掉几个 | 迭代时索引在移动，改用列表推导或倒序删 |

下一篇：[数据结构](/guides/python/02-data-structures)。
