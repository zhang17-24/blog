---
title: 生命周期
description: 标注语法、三条省略规则，以及什么时候该改用所有权。
---

# 生命周期

生命周期标注不是为了取悦编译器，而是为了把意图说清楚。

## 它在解决什么问题

```rust
fn longest(x: &str, y: &str) -> &str {
    if x.len() > y.len() { x } else { y }
}
```

这段编译不过。编译器不知道返回的引用指向 `x` 还是 `y`，
所以无法判断它会不会比参数活得更久。

加上标注就明确了：

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

读法：**返回值活得不会比 `x` 和 `y` 中较短的那个更久。**

## 三条省略规则

大部分时候不用手写。编译器会依次套用：

1. 每个引用参数各自获得一个生命周期
2. 如果只有一个输入生命周期，它被赋给所有输出
3. 如果有 `&self` 或 `&mut self`，它的生命周期赋给所有输出

所以下面这种写法完全合法，不需要任何标注：

```rust
fn first_word(s: &str) -> &str {
    s.split_whitespace().next().unwrap_or("")
}
```

## 结构体里的引用

```rust
struct Excerpt<'a> {
    part: &'a str,
}
```

含义是：`Excerpt` 实例不能比它引用的 `part` 活得更久。

::: warning 一个经验法则
**如果一个结构体里塞了三个以上的引用，先想想能不能改成持有所有权。**

生命周期的复杂度通常是指数级增长的。改成 `String` 只是多一次分配，
但代码可读性的收益往往更大。
:::

## 常见报错

| 报错 | 通常意味着 |
| --- | --- |
| `missing lifetime specifier` | 编译器无法推断，需要显式标注 |
| `borrowed value does not live long enough` | 被引用的值提前离开了作用域 |
| `returns a value referencing data owned by the current function` | 返回了局部变量的引用 |

最后一个是新手最常遇到的 —— 想返回函数内部创建的东西，
要么返回所有权（`String` 而不是 `&str`），要么把数据作为参数传进来。

## 静态生命周期 `'static`

```rust
let s: &'static str = "编译进二进制里的字面量";
```

`'static` 表示「活得和程序一样久」。字符串字面量是 `'static`，
因为它们被编译进了二进制文件。

但要注意：**`Box<dyn Error + 'static>` 里的 `'static` 不是「永远活着」，
而是「不包含任何短于 `'static` 的借用」。** 这个区别在写错误处理时经常遇到。

下一篇讲 [Trait 与泛型](/guides/rust/03-traits)。
