# 代码审查规范

## 审查清单概览

| 审查类型 | 关注点 |
|----------|--------|
| 错误处理 | error 忽略、panic、错误包装 |
| 并发安全 | race condition、goroutine 泄漏 |
| 安全漏洞 | 注入、敏感信息、路径遍历 |
| 性能 | 超时、内存分配、资源关闭 |
| 日志 | 级别、脱敏、结构化 |
| API 设计 | RESTful、状态码、响应结构 |
| Context | 链路完整、超时设置 |

---

## 1. 错误处理审查

### 1.1 被忽略的 error（使用 `_`）

```go
// ✗ 错误示例
result, _ := riskyFunction()

// ✓ 正确示例
result, err := riskyFunction()
if err != nil {
    return err
}
```

### 1.2 panic 作为错误处理

```go
// ✗ 错误示例
if value == nil {
    panic("value should not be nil")
}

// ✓ 正确示例
if value == nil {
    return nil, ErrNilValue
}
```

### 1.3 错误包装（%w）

```go
// ✗ 错误示例
return errors.New("operation failed")

// ✓ 正确示例
return fmt.Errorf("process data: %w", err)
```

### 1.4 参数校验

```go
// ✓ 参数校验
func FindUser(id string) (*User, error) {
    if id == "" {
        return nil, ErrInvalidID
    }
    // ...
}
```

---

## 2. 并发安全审查

### 2.1 Goroutine Panic 防护（🔴 紧急）

```go
// import "runtime/debug"
import "runtime/debug"

// ✓ 正确：添加 recover 防护
go func() {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("[PANIC] recovered: %v\n%s", r, debug.Stack())
        }
    }()
    // ... 业务逻辑
}()
```

### 2.2 Map 并发读写保护

```go
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
```

### 2.3 Goroutine 退出机制

```go
// ✓ 正确示例 - 使用 context.Context
func fetchAll(ctx context.Context, urls []string) []string {
    var wg sync.WaitGroup
    for i, url := range urls {
        wg.Add(1)
        go func(idx int, u string) {
            defer func() {
                if r := recover(); r != nil {
                    log.Printf("[PANIC] recovered: %v\n%s", r, debug.Stack())
                }
                wg.Done()
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
```

### 2.4 WaitGroup 计数精确性

```go
// ✓ 正确示例
for _, item := range items {
    wg.Add(1)
    go func(it Item) {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("[PANIC] recovered: %v\n%s", r, debug.Stack())
            }
            wg.Done()
        }()
        process(it)
    }(item)
}
wg.Wait()
```

### 2.5 闭包捕获循环变量

```go
// ✓ 正确示例 - 作为参数传递
for _, s := range data {
    go func(s string) {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("[PANIC] recovered: %v\n%s", r, debug.Stack())
            }
        }()
        fmt.Println(s)
    }(s)
}
```

---

## 3. 安全审查

### 3.1 敏感信息泄露

```go
// 🔴 危险：敏感信息硬编码
apiKey := "sk-xxxx-xxxx-xxxx"

// ✅ 推荐：环境变量或配置
apiKey := os.Getenv("API_KEY")
```

### 3.2 SQL 注入

```go
// 🔴 危险：字符串拼接
query := "SELECT * FROM users WHERE name = '" + name + "'"

// ✅ 安全：参数化查询
query := "SELECT * FROM users WHERE name = ?"
db.Query(query, name)
```

### 3.3 命令注入

```go
// 🔴 危险：shell 注入
exec.Command("sh", "-c", "ls " + userInput)

// ✅ 安全：参数化执行
exec.Command("ls", userInput)
```

### 3.4 路径遍历

```go
// 🔴 危险：用户输入拼接到路径
path := "./uploads/" + filename

// ✅ 安全：路径校验
if !strings.HasPrefix(filepath.Clean(path), "./uploads/") {
    return errors.New("invalid path")
}
```

---

## 4. 性能审查

### 4.1 超时与上下文

```go
// 🔴 危险：无限等待
resp, err := http.Get(url)

// ✅ 安全：设置超时
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
resp, err := client.Do(req.WithContext(ctx))
```

### 4.2 资源关闭

```go
// ✅ 安全：defer 关闭
func good() {
    resp, err := http.Get(url)
    if err != nil {
        return err
    }
    defer resp.Body.Close()
}
```

### 4.3 内存分配优化

```go
// ✅ 推荐：预分配
func process(items []Item) []Result {
    results := make([]Result, 0, len(items))
    for _, item := range items {
        results = append(results, Result{...})
    }
    return results
}
```

### 4.4 同步手段

```go
// 🔴 禁止：time.Sleep 作为同步
time.Sleep(time.Second)

// ✅ 推荐：channel 或 sync.WaitGroup
var wg sync.WaitGroup
wg.Add(1)
go func() { defer wg.Done(); doSomething() }()
wg.Wait()
```

---

## 5. 日志规范审查

### 5.1 日志级别使用

| 级别 | 使用场景 | 示例 |
|------|----------|------|
| Debug | 开发调试 | "进入函数 X" |
| Info | 正常流程 | "用户登录成功" |
| Warn | 异常但可处理 | "重试第 N 次" |
| Error | 错误需要关注 | "数据库连接失败" |

### 5.2 敏感信息脱敏

```go
// 🔴 危险：日志输出敏感信息
log.Info("用户登录", "password", password)

// ✅ 安全：脱敏处理
func maskSensitive(key, value string) string {
    switch key {
    case "password", "passwd", "secret":
        return "***"
    case "token", "Authorization":
        if len(value) > 8 {
            return value[:4] + "****"
        }
    }
    return value
}
```

### 5.3 结构化日志

```go
// ✅ 推荐：结构化
log.Info("购买成功",
    "user_id", userID,
    "product", product,
    "price", price,
)
```

---

## 6. API 设计审查

### 6.1 RESTful 规范

| 规则 | 正确示例 | 错误示例 |
|------|----------|----------|
| 使用名词 | GET /users | GET /getUsers |
| 使用复数 | GET /users | GET /user |
| 层级结构 | GET /users/{id}/orders | GET /userOrders?user_id={id} |

### 6.2 HTTP 状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | 成功响应 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 参数错误 |
| 401 | Unauthorized | 未认证 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 服务器错误 |

### 6.3 响应结构

```go
// ✅ 推荐：统一响应结构
type Response struct {
    Code    int         `json:"code"`
    Message string      `json:"message"`
    Data    interface{} `json:"data,omitempty"`
}

// ✅ 推荐：分页响应
type PageResponse struct {
    Items      interface{} `json:"items"`
    Total      int64       `json:"total"`
    Page       int         `json:"page"`
    PageSize   int         `json:"page_size"`
    TotalPages int         `json:"total_pages"`
}
```

---

## 7. Context 传播审查

### 7.1 Context 链路完整性

```go
// ✅ HTTP 请求入口
func handler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    result, err := doBusiness(ctx, param)
    resp, err := callDownstream(ctx, req)
}

// ✅ 数据库操作
func queryDB(ctx context.Context, query string) (*Rows, error) {
    return db.QueryContext(ctx, query)
}
```

### 7.2 危险模式

```go
// 🔴 危险：丢失 Context
go processInBackground(param) // 未传递 Context

// 🔴 危险：使用空 Context
rows := db.QueryContext(context.Background(), query) // 应用层应传 ctx

// 🔴 危险：创建新 Context 而非继承
ctx = context.Background() // 丢失请求 Context
```

### 7.3 超时设置

```go
// ✅ 推荐：从请求继承超时
func handler(r *http.Request) {
    ctx := r.Context()
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
}
```
