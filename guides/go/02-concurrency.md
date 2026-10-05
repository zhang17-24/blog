---
title: goroutine 与 channel
description: 用通信代替共享内存，以及三个最容易踩的坑。
---

# goroutine 与 channel

## goroutine 便宜到可以随便开

一个 goroutine 初始栈只有 **2 KB**，可以动态增长。开十万个也不会把内存吃满。

```go
go doSomething()   // 加个 go 关键字就并发了
```

就这么多。没有线程池、没有 Future、没有 async/await 标记。

但「便宜」不等于「免费」——**goroutine 泄漏是 Go 服务最常见的内存问题**：
一个永远阻塞在 channel 上的 goroutine，既不会退出也不会被回收。

## channel：用通信代替共享内存

Go 的并发格言是：

> 不要通过共享内存来通信，而要通过通信来共享内存。

```go
ch := make(chan int)

go func() {
    ch <- 42          // 发送
}()

v := <-ch             // 接收，会阻塞直到有值
```

channel 分两种：

```go
ch := make(chan int)      // 无缓冲：发送和接收必须同时就绪
ch := make(chan int, 10)  // 有缓冲：缓冲区没满就能发
```

无缓冲 channel 的「必须同时就绪」是一个很强的同步保证 —— 发送方会一直阻塞到接收方拿走。

关闭与遍历：

```go
close(ch)                  // 只能由发送方关闭，且只能关一次

for v := range ch {        // 通道关闭且缓冲耗尽后自动退出循环
    fmt.Println(v)
}
```

::: warning 关闭 channel 的三条铁律
1. **不要从接收方关闭** —— 你不知道还有没有别的发送方
2. **不要重复关闭** —— panic
3. **不要关闭只为省事** —— 很多场景下不关是更好的选择，让 GC 处理

一个实用的判据：**只有当你需要告诉接收方「没有更多数据了」时才关闭。**
:::

## select：多路等待

`select` 让你同时等多个 channel，哪个先来走哪个：

```go
select {
case msg := <-msgCh:
    handle(msg)
case <-time.After(3 * time.Second):
    return errors.New("超时")
case <-ctx.Done():
    return ctx.Err()
}
```

`time.After` + `ctx.Done()` 这两个分支，是 Go 服务里处理超时和取消的标准写法。
**任何会阻塞的操作，都应该有一个退出路径** —— 否则就是前面说的泄漏。

## 三个最容易踩的坑

### 1. 循环变量捕获（Go 1.22 之前）

```go
for _, item := range items {
    go func() {
        fmt.Println(item)   // Go 1.21 及之前：全部打印最后一个元素
    }()
}
```

Go 1.22 起循环变量每次迭代都是新的，这个问题已经修了。但如果你在维护老代码、
或者 `go.mod` 里写的是 `go 1.21`，仍然会遇到。

老代码里的标准解法是显式传参：

```go
for _, item := range items {
    go func(it string) {
        fmt.Println(it)
    }(item)
}
```

### 2. 忘记等待，主函数先退出了

```go
func main() {
    go doWork()        // 主函数不等它，直接退出，doWork 根本没跑完
}
```

用 `sync.WaitGroup`：

```go
var wg sync.WaitGroup
for _, url := range urls {
    wg.Add(1)
    go func(u string) {
        defer wg.Done()
        fetch(u)
    }(url)
}
wg.Wait()
```

`defer wg.Done()` 写在 goroutine 内部第一行，别写在 `wg.Add` 旁边 —— 位置反了会少减一次。

### 3. 以为 map 并发安全

Go 的 map **并发读写会直接 panic**（不是返回错误，是 crash）。

要么加 `sync.Mutex`：

```go
var mu sync.Mutex
mu.Lock()
m[key] = value
mu.Unlock()
```

要么用 `sync.Map`（只在「读多写少、key 集合稳定」时才有优势，别默认用它）。

## 小结

- goroutine 很便宜，但泄漏的 goroutine 不会被回收
- 无缓冲 channel 是同步点，有缓冲 channel 是队列
- 只有发送方能关闭 channel，且只在需要通知「数据结束」时关
- 任何阻塞操作都要有 `ctx.Done()` 或超时作为退出路径
- map 并发读写会 panic，必须加锁

想继续深入的话，`context` 包和 `errgroup` 是下一步最值得花时间的地方。
