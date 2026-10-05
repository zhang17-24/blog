---
title: 异步编程
description: asyncio 的正确用法、GIL 的真相，以及什么时候不该用异步。
---

# 异步编程

异步是 Python 里被误解最多的特性。先记住一句话：

**异步解决的是「等待」的问题，不是「计算」的问题。**

## 同步 vs 异步：什么时候有用

```python
# 同步：三个请求串行，总耗时 = 1 + 1 + 1 = 3 秒
def fetch_all_sync(urls):
    return [requests.get(u) for u in urls]

# 异步：三个请求并发，总耗时 ≈ 1 秒
async def fetch_all(urls):
    async with aiohttp.ClientSession() as s:
        return await asyncio.gather(*[s.get(u) for u in urls])
```

关键在「等网络」的时间被重叠了。如果任务是纯计算（比如算素数），
异步**一点用都没有**，甚至更慢。

## 基本语法

```python
import asyncio

async def fetch(name: str, delay: float) -> str:
    await asyncio.sleep(delay)        # 模拟 IO 等待
    return f"{name} 完成"

async def main():
    # 并发执行，总耗时 = 最慢的那个
    results = await asyncio.gather(
        fetch("A", 1.0),
        fetch("B", 0.5),
    )
    print(results)

asyncio.run(main())
```

::: warning 三个最常见的错误
1. **忘记 `await`** —— 协程对象被创建了但从未执行，还会收到 RuntimeWarning
2. **在协程里调用同步阻塞函数** —— `time.sleep(1)` 会卡死整个事件循环，要用 `asyncio.sleep(1)`
3. **`asyncio.run()` 嵌套调用** —— 一个线程只能有一个事件循环，嵌套会报错
:::

## 并发执行的三种方式

| 方法 | 行为 | 用在 |
| --- | --- | --- |
| `asyncio.gather(*aws)` | 全部并发，等全部完成 | 结果都要，一个失败全失败 |
| `asyncio.gather(*aws, return_exceptions=True)` | 同上，但异常当结果返回 | 允许部分失败 |
| `asyncio.as_completed(aws)` | 谁先完成先拿到 | 流式处理结果 |
| `asyncio.wait_for(aw, timeout)` | 超时抛 `TimeoutError` | 需要超时保护 |
| `asyncio.TaskGroup()` | 3.11+，结构化并发，异常自动传播 | 新代码推荐 |

```python
# Python 3.11+ 推荐写法
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(fetch("A", 1.0))
    t2 = tg.create_task(fetch("B", 0.5))
# 出了这个块，两个任务都已完成；任一失败会取消其余并抛 ExceptionGroup
```

## 限流：别一次发一万个请求

```python
sem = asyncio.Semaphore(10)     # 最多 10 个并发

async def limited(url):
    async with sem:
        return await fetch(url)

await asyncio.gather(*[limited(u) for u in urls])
```

## GIL 的真相

很多人以为「Python 有 GIL，所以多线程没用」。准确的说法是：

- GIL 保证同一时刻只有一个线程执行 **Python 字节码**
- 但**阻塞的 IO 调用会释放 GIL**，所以多线程做网络/文件 IO 是有效的
- **CPU 密集**任务确实被 GIL 卡住，该用 `multiprocessing` 或 C 扩展

| 任务类型 | 该用什么 |
| --- | --- |
| 网络请求、文件读写（IO 密集） | `asyncio`，或线程池 |
| 数学计算、图像处理（CPU 密集） | `multiprocessing`，或 numpy / C 扩展 |
| 混合型 | 进程池 + 每个进程内跑 asyncio |

## 该不该上异步

::: tip 判断标准
**只有当你的程序瓶颈在「等待外部 IO」且并发量较大时，异步才值得。**

- 写个每天跑一次的脚本 → 同步代码，可读性更重要
- Web 服务要扛几千并发连接 → 异步（FastAPI / aiohttp）
- 数据处理管道，CPU 是瓶颈 → 多进程，不是异步
:::

异步的代价是整个调用链都必须是异步的。一个同步的阻塞函数混进去，
整个事件循环就被拖住了。**在项目早期就决定，别中途改。**

Python 指南到这里结束。
