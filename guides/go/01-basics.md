---
title: 基础语法与工具链
description: 变量声明、错误处理惯例，以及 go 命令家族怎么用。
---

# 基础语法与工具链

## 极简的语法

Go 的语法少得反常。变量声明有两种写法：

```go
var name string = "流沙"   // 显式类型，可省略类型
age := 28                  // 短声明，只在函数内可用，类型自动推断
```

`:=` 是 Go 里最常用的声明方式，但它**只能在函数体内用**。包级别的变量必须写 `var`。

没有 `while`，只有 `for`：

```go
for i := 0; i < 10; i++ { }   // 经典三段式
for i < 10 { }                // 只留条件，等价于 while
for { }                       // 死循环
for i, v := range items { }   // 遍历切片 / map / channel
```

## 错误处理：显式且啰嗦

Go 没有异常，错误就是普通返回值。这是它最被吐槽、也最被坚持的一点：

```go
f, err := os.Open("config.yml")
if err != nil {
    return fmt.Errorf("打开配置失败: %w", err)
}
defer f.Close()
```

两个约定值得记住：

- **`%w` 而不是 `%v`** —— `%w` 会把原始错误包进去，上层可以用 `errors.Is` / `errors.As` 判断
- **`defer` 在函数返回时执行** —— 紧跟在资源获取之后写 `defer`，别攒到最后

::: tip 为什么不用 try/catch
异常机制的问题在于「错误在哪一层被处理」是不确定的。Go 强制你在每一个调用点做决定：
要么处理，要么往上抛。代价是代码变长，收益是控制流永远清晰。
:::

## 工具链：go 命令家族

Go 把格式化、测试、依赖管理全塞进了一个命令里，这是它工程体验最好的部分。

```bash
go mod init github.com/you/project   # 初始化模块，生成 go.mod
go mod tidy                          # 补齐缺失依赖、删掉没用的
go run main.go                       # 直接跑，不产生文件
go build -o app .                    # 编译成单个二进制
go test ./...                        # 跑全部测试
gofmt -w .                           # 格式化（也可以用 go fmt ./...）
go vet ./...                         # 静态检查，抓常见错误
```

`gofmt` 没有配置项 —— 这是刻意的。所有 Go 代码长一个样，代码评审不用吵风格。

## 交叉编译：一行命令换平台

```bash
GOOS=linux GOARCH=amd64 go build -o app-linux .
GOOS=darwin GOARCH=arm64 go build -o app-mac .
```

不需要装交叉编译工具链，也不依赖目标机器上有 Go。产物是静态二进制，
扔到服务器上直接跑 —— 这是 Go 部署体验碾压 Python / Node 的地方。

## 小结

- `:=` 短声明只在函数内可用；包级别用 `var`
- 错误是返回值，用 `%w` 包装、`errors.Is` 判断
- `defer` 紧跟资源获取写
- `go mod tidy` 是依赖管理的唯一入口
- 交叉编译不需要额外工具链

下一篇讲真正让 Go 区别于其他语言的部分：[goroutine 与 channel](/guides/go/02-concurrency)。
