---
name: go-concurrency-reviewer
description: >
  Go 语言并发安全审查技能。当用户要求审查代码并发安全、检查 race condition、
  或请求诊断 goroutine 泄漏、channel 安全、panic 防护等问题时触发。
  专门用于发现和修复 Go 代码中的并发缺陷，精通 Go 内存模型和 race detector。
triggers:
  - 并发审查
  - goroutine 泄漏
  - race condition
  - 线程安全
  - 并发安全审查
  - Go并发审查员
---

# Go 并发审查员 (Go Concurrency Reviewer)

## 技能定位

Go 语言并发安全专家，精通 Go 内存模型、race detector 和并发设计模式。检测代码中的并发问题并提供修复建议。

## 依赖包

```go
import (
    "log"
    "runtime/debug"
)
```

## 严重程度定义

| 级别 | 描述 | 示例 |
|------|------|------|
| 🔴 紧急 | 必定导致 panic 或数据损坏 | map 并发读写、goroutine 无 panic 防护 |
| 🟡 警告 | 可能导致数据不一致或泄漏 | goroutine 泄漏、WaitGroup 计数错误 |
| 💡 建议 | 代码可优化 | 使用更高效的同步方式 |

## 审查检查清单

---

### 1. Goroutine Panic 防护（🔴 紧急）⚠️

**问题**: `go func()` 如果内部程序 panic 后无法恢复，会导致整个程序崩溃。

**正确模式**:
```go
// 正确：添加 recover 防护
go func() {
    defer func() {
        if r := recover(); r != nil {
            // 使用 debug.Stack() 获取当前 goroutine 的栈信息
            log.Printf("[PANIC] recovered: %v\n%S", r, debug.Stack())
        }
    }()
    // ... 业务逻辑
}()
```

**⚠️ 注意**：`recover()` 必须**直接**在 `defer` 的匿名函数中调用，封装为独立函数是无效的：

```go
// 错误：封装为独立函数，recover 无法生效
func safeRecover() {
    if r := recover(); r != nil {  // ❌ 无效！recover 只在直接 defer 中有效
        log.Printf(...)
    }
}
defer safeRecover()  // ❌ 无效

// 正确：recover 必须在直接的 defer 匿名函数中
defer func() {
    if r := recover(); r != nil {  // ✅ 有效
        log.Printf("[PANIC] recovered: %v\n%S", r, debug.Stack())
    }
}()
```

**违规模式**:
```go
// 错误：不安全的 goroutine，无 panic 防护
go func() {
    doSomething() // 可能 panic，导致程序崩溃
}()
```

**修复建议**: 必须为所有 `go func()` 添加 `recover()` 逻辑，捕获 panic 并使用 `debug.Stack()` 打印栈信息。

---

### 2. Map 并发读写保护（🔴 紧急）

**检查模式：**
```go
// ✗ 错误示例 - 未保护的 map
type Cache struct {
    data map[string]string
}

// ✗ 并发读写 map
func (c *Cache) Get(key string) string {
    return c.data[key]  // 读 map，无保护
}

func (c *Cache) Set(key, value string) {
    c.data[key] = value  // 写 map，无保护
}

// ✓ 正确示例 - 使用 RWMutex
type SafeCache struct {
    mu   sync.RWMutex
    data map[string]string
}

func (c *SafeCache) Get(key string) string {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.data[key]
}

func (c *SafeCache) Set(key, value string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[key] = value
}

// ✓ 正确示例 - 使用 sync.Map（适用于读多写少）
type ConcurrentCache struct {
    data sync.Map
}

func (c *ConcurrentCache) Get(key string) (value string, ok bool) {
    if v, exists := c.data.Load(key); exists {
        return v.(string), true
    }
    return "", false
}

func (c *ConcurrentCache) Set(key, value string) {
    c.data.Store(key, value)
}
```

**修复建议：**
- 优先使用 `sync.Map`（Go 1.9+）
- 或使用 `RWMutex` 保护普通 map
- 读操作用 `RLock`，写操作用 `Lock`

---

### 3. Goroutine 退出机制（🟡 警告）

**检查模式：**
```go
// ✗ 错误示例 - goroutine 泄漏
func process() {
    go func() {
        for {
            data := <-ch
            // 处理数据，但没有退出条件
        }
    }()
}

// ✓ 正确示例 - 使用 context.Context
func fetchAll(ctx context.Context, urls []string) []string {
    results := make([]string, len(urls))
    var wg sync.WaitGroup
    
    for i, url := range urls {
        wg.Add(1)
        go func(idx int, u string) {
            defer func() {
                wg.Done()
                if r := recover(); r != nil {
                    log.Printf("[PANIC] fetchAll worker recovered: %v\n%S", r, debug.Stack())
                }
            }()
            select {
            case <-ctx.Done():
                return
            default:
                results[idx] = fetch(u)
            }
        }(i, url)
    }
    
    wg.Wait()
    return results
}

// ✓ 正确示例 - 使用 done channel
func fetchAll(done <-chan struct{}, urls []string) []string {
    results := make([]string, len(urls))
    var wg sync.WaitGroup
    
    for i, url := range urls {
        wg.Add(1)
        go func(idx int, u string) {
            defer func() {
                wg.Done()
                if r := recover(); r != nil {
                    log.Printf("[PANIC] fetchAll worker recovered: %v\n%S", r, debug.Stack())
                }
            }()
            select {
            case <-done:
                return
            default:
                results[idx] = fetch(u)
            }
        }(i, url)
    }
    
    wg.Wait()
    return results
}
```

**修复建议：**
- 每个启动的 goroutine 必须有明确的退出条件
- 优先使用 `context.Context` 管理生命周期
- 使用 `sync.WaitGroup` 等待 goroutine 完成
- 使用 `errgroup` 简化并发错误处理
- **所有 goroutine 必须添加 panic 防护**

---

### 4. Mutex 使用正确性（🟡 警告）

**检查模式：**
```go
// ✗ 错误示例 - Lock 后未 Unlock
func (s *Service) Update(data string) {
    s.mu.Lock()
    s.data = data
    // 忘记 Unlock
}

// ✗ 错误示例 - defer 位置错误
func (s *Service) Update(data string) {
    s.mu.Lock()
    defer s.mu.Unlock()  // 正确
    
    s.data = data
    s.mu.Unlock()  // 重复 Unlock
}

// ✓ 正确示例
func (s *Service) Update(data string) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.data = data
}

// ✓ 正确示例 - 写多读少场景
func (s *Service) Get() string {
    s.mu.RLock()
    defer s.mu.RUnlock()
    return s.data
}
```

**修复建议：**
- 始终使用 `defer` 确保 Unlock 执行
- 避免在锁内执行阻塞操作
- 读写分离使用 `RWMutex`
- 注意锁的粒度，避免死锁

---

### 5. WaitGroup 计数精确性（🟡 警告）

**检查模式：**
```go
// ✗ 错误示例 - Add 在 goroutine 内
for _, item := range items {
    go func(it Item) {
        wg.Add(1)  // ✗ Add 应该在 goroutine 外
        defer func() {
            wg.Done()
            if r := recover(); r != nil {
                log.Printf("[PANIC] worker recovered: %v\n%S", r, debug.Stack())
            }
        }()
        process(it)
    }(item)
}

// ✗ 错误示例 - Add 和 Done 不匹配
var wg sync.WaitGroup
for _, item := range items {
    wg.Add(1)
    go func(it Item) {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("[PANIC] worker recovered: %v\n%S", r, debug.Stack())
            }
        }()
        if condition {
            return  // ✗ 提前返回，未调用 Done
        }
        process(it)
        wg.Done()
    }(item)
}

// ✓ 正确示例
var wg sync.WaitGroup
for _, item := range items {
    wg.Add(1)
    go func(it Item) {
        defer func() {
            wg.Done()
            if r := recover(); r != nil {
                log.Printf("[PANIC] worker recovered: %v\n%S", r, debug.Stack())
            }
        }()
        process(it)
    }(item)
}
wg.Wait()

// ✓ 正确示例 - 使用 errgroup
g, ctx := errgroup.WithContext(context.Background())
for _, url := range urls {
    url := url  // 捕获为局部变量
    g.Go(func() error {
        return fetch(url)
    })
}
if err := g.Wait(); err != nil {
    // 处理错误
}
```

**修复建议：**
- `wg.Add(1)` 必须在 goroutine **启动前**调用
- `defer wg.Done()` 确保每个分支都执行
- 或使用 `wg.Add(len(items))` 预先计数
- 推荐使用 `golang.org/x/sync/errgroup` 管理并发任务
- **所有 goroutine 必须添加 panic 防护**

---

### 6. Channel 关闭安全性（🟡 警告）

**检查模式：**
```go
// ✗ 错误示例 - 发送数据到已关闭 channel
ch := make(chan int, 10)
go func() {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("[PANIC] channel worker recovered: %v\n%S", r, debug.Stack())
        }
    }()
    for i := 0; i < 20; i++ {
        if i > 10 {
            close(ch)  // 关闭 channel
            return
        }
        ch <- i  // 可能 panic
    }
}()

// ✓ 正确示例 - 只由发送方关闭 channel
ch := make(chan Task, 100)
go func() {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("[PANIC] channel worker recovered: %v\n%S", r, debug.Stack())
        }
    }()
    for task := range ch {  // range 自动检测 channel 关闭
        process(task)
    }
}()

// ✓ 正确示例 - 使用 done channel 通知退出
done := make(chan struct{})
go func() {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("[PANIC] channel worker recovered: %v\n%S", r, debug.Stack())
        }
    }()
    for {
        select {
        case <-done:
            return
        case task := <-ch:
            process(task)
        }
    }
}()

// ✓ 正确示例 - 使用 sync.Once 关闭 channel
type SafeChan struct {
    ch   chan int
    once sync.Once
}

func (s *SafeChan) Close() {
    s.once.Do(func() {
        close(s.ch)
    })
}
```

**修复建议：**
- 遵循 "channel 由发送方关闭" 原则
- 使用 `range` 遍历 channel 自动处理关闭
- 使用 `sync.Once` 确保只关闭一次
- 使用 `done channel` 控制退出
- **所有 goroutine 必须添加 panic 防护**

---

### 7. 闭包捕获循环变量（🟡 警告）

**检查模式：**
```go
// ✗ 错误示例 - 闭包捕获循环变量
data := []string{"a", "b", "c"}
for _, s := range data {
    go func() {
        fmt.Println(s)  // 所有 goroutine 共享同一个 s
    }()
}

// ✓ 正确示例 - 作为参数传递
data := []string{"a", "b", "c"}
for _, s := range data {
    go func(s string) {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("[PANIC] loop worker recovered: %v\n%S", r, debug.Stack())
            }
        }()
        fmt.Println(s)  // 每个 goroutine 有独立的 s
    }(s)
}

// ✓ 正确示例 - 创建局部变量
data := []string{"a", "b", "c"}
for _, s := range data {
    s := s  // 重新声明，创建新变量
    go func() {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("[PANIC] loop worker recovered: %v\n%S", r, debug.Stack())
            }
        }()
        fmt.Println(s)  // 正确
    }()
}
```

**修复建议：**
- 在 for 循环内使用 `s := s` 创建局部副本
- 或将循环变量作为函数参数传递
- 这是 Go 新手最常见的并发 bug

---

## 工作流程

1. **扫描代码**
   - 搜索 `go func()` goroutine 启动
   - 搜索 `sync.Map`、`sync.Mutex`、`sync.RWMutex`
   - 搜索 `sync.WaitGroup`
   - 搜索 `chan` 和 `close(`
   - 搜索 `for ... range`

2. **分析每个问题**
   - 确定并发模型
   - 评估 race condition 风险
   - 检查资源泄漏可能性

3. **生成报告**
   ```
   ## Go 并发安全审查报告
   
   ### 🔴 紧急（必须修复）
   - 文件: xxx.go:123
     问题: goroutine 缺少 panic 防护
     代码: `go func() { ... }()`
     风险: panic 导致程序崩溃
     修复: 添加 defer recover() 并使用 debug.Stack() 打印栈
   
   ### 🟡 警告（建议修复）
   - 文件: xxx.go:456
     问题: goroutine 缺少退出机制
     代码: `go func() { for { ... } }()`
     风险: goroutine 泄漏
     修复: 使用 context 或 done channel
   ```

---

## 快速修复命令

```bash
# 运行竞态检测
go test -race ./...

# 检查死锁
go build -race . && timeout 60 ./your-binary

# 使用 go vet
go vet ./...
```

## 最佳实践

1. **Panic 防护**: 所有 goroutine 必须使用 `defer func() { recover() }()` 封装
2. **SafeGo 封装**: 创建统一的 goroutine 启动函数，自动添加 panic 防护
3. **明确生命周期**: 每个 goroutine 必须有明确的退出机制
4. **避免锁内阻塞**: 互斥锁内不应有 I/O 操作
5. **超时控制**: 所有外部调用必须设置超时
6. **channel 封装**: 不直接暴露 channel，使用函数封装
