---
title: Trait 与泛型
description: 抽象能力、关联类型，以及静态分发与动态分发怎么选。
---

# Trait 与泛型

Trait 是 Rust 的抽象单位。它比接口多一点东西，也比接口麻烦一点。

## 基础：定义一个 trait

```rust
trait Summary {
    fn summarize(&self) -> String;
}

struct Article { title: String, body: String }

impl Summary for Article {
    fn summarize(&self) -> String {
        format!("{}：{}…", self.title, &self.body[..20])
    }
}
```

## 默认实现

trait 可以带默认方法，实现者只需覆盖想改的部分：

```rust
trait Summary {
    fn title(&self) -> String;

    // 默认实现可以调用同一 trait 里的其他方法
    fn summarize(&self) -> String {
        format!("{}（暂无摘要）", self.title())
    }
}
```

## Trait 作为参数：两种等价写法

```rust
// 语法糖
fn notify(item: &impl Summary) { }

// 完整写法，也叫 trait bound
fn notify<T: Summary>(item: &T) { }
```

多个约束用 `+` 连接：

```rust
fn notify<T: Summary + Clone>(item: &T) { }

// 约束多了用 where 更清晰
fn process<T, U>(a: &T, b: &U) -> String
where
    T: Summary + Clone,
    U: Summary,
{
    format!("{} {}", a.summarize(), b.summarize())
}
```

## 关联类型 vs 泛型参数

这是最容易混淆的一处：

```rust
// 泛型参数：一个类型可以对多个 T 分别实现
trait From<T> {
    fn from(value: T) -> Self;
}
// 所以 String 可以 From<&str>、From<i32>……

// 关联类型：一个类型只能实现一次
trait Iterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;
}
```

**判断标准**：如果同一类型需要多个实现，用泛型参数；如果只能有一个实现，用关联类型。

## 静态分发 vs 动态分发

```rust
// 静态分发：编译期单态化，为每个具体类型生成一份代码
fn print_all<T: Summary>(items: &[T]) { }

// 动态分发：运行期查虚表，体积更小但有一次间接调用
fn print_all(items: &[Box<dyn Summary>]) { }
```

| | 静态分发 `impl T` / `<T: Trait>` | 动态分发 `dyn Trait` |
| --- | --- | --- |
| 性能 | 好，可内联 | 一次虚表跳转 |
| 二进制体积 | 大（单态化膨胀） | 小 |
| 能否混装不同类型 | 不能 | 能 |
| 对象安全要求 | 无 | 方法不能有泛型参数、不能返回 `Self` |

::: tip 怎么选
**默认用泛型（静态分发）**，只有在需要「一个容器里装多种类型」时才用 `dyn`。
`Vec<Box<dyn Summary>>` 就是典型的动态分发场景。
:::

## 常见标准 trait 速查

| Trait | 作用 | 派生宏 |
| --- | --- | --- |
| `Debug` | `{:?}` 格式化 | `#[derive(Debug)]` |
| `Clone` | 显式复制 | `#[derive(Clone)]` |
| `Copy` | 隐式复制（栈上小类型） | `#[derive(Copy)]` |
| `PartialEq` / `Eq` | `==` 比较 | `#[derive(PartialEq, Eq)]` |
| `Default` | 默认值 | `#[derive(Default)]` |
| `From` / `Into` | 类型转换 | 手写 |
| `Display` | `{}` 格式化 | 手写 |

`Display` 不能派生，必须手写 —— 因为「给人看的格式」没有唯一正确答案。

到这里 Rust 基础三篇就结束了。想继续深入可以看 `Result` 错误处理、并发和宏。
