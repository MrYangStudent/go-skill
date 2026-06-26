# Go Minimal Code 实战案例库

## 概述

收集 Go Minimal Code 的实际应用案例，展示如何识别和消除过度工程。

---

## 案例 1: 日期选择器

### 需求
前端页面需要一个日期选择器。

### ❌ 过度工程实现

```go
// 安装了 flatpickr 库
import "github.com/chmln/hanami"

// 创建了包装组件
type DatePicker struct {
    ID       string
    MinDate  string
    MaxDate  string
    Format   string
    Locale   string
}

func (d *DatePicker) Render() string {
    return fmt.Sprintf(`
        <div id="%s">
            <input type="text" readonly />
        </div>
        <script>
            flatpickr("#%s", {
                minDate: "%s",
                maxDate: "%s",
                dateFormat: "%s"
            });
        </script>
    `, d.ID, d.ID, d.MinDate, d.MaxDate, d.Format)
}

// 创建了样式文件
// static/css/datepicker.css (50 行)

// 创建了配置结构体
type DatePickerConfig struct {
    Theme    string
    Timezone string
}

// 总计: ~150 行代码 + 外部依赖 + CSS 文件
```

### ✅ Go Minimal Code 实现

```html
<!-- 浏览器内置，零依赖 -->
<input type="date">
```

### 结果
- 代码量: 150 行 → **1 行** (-99%)
- 依赖: 3 个 → **0 个** (-100%)
- 文件大小: ~2KB → **0 字节**
- 功能: 完全满足需求

### Go Minimal Code 阶梯应用
1. ✅ 浏览器有原生 `<input type="date">`

---

## 案例 2: CSV 解析

### 需求
解析用户上传的 CSV 文件。

### ❌ 过度工程实现

```go
// 引入了第三方 CSV 库
import "github.com/klauspost/compress/gz"

// 创建了 CSV 解析器接口
type CSVParser interface {
    Parse(reader io.Reader) ([]map[string]string, error)
    Validate(headers []string) error
    Transform(records []map[string]string) ([]map[string]string, error)
}

// 创建了具体实现
type StandardCSVParser struct {
    delimiter rune
    hasHeader bool
}

func (p *StandardCSVParser) Parse(reader io.Reader) ([]map[string]string, error) {
    csvReader := csv.NewReader(reader)
    csvReader.Comma = p.delimiter
    // ... 50 行解析逻辑
}

// 创建了转换器
type CSVTransformer struct {
    mappings map[string]string
}

func (t *CSVTransformer) Transform(records []map[string]string) []map[string]string {
    // ... 30 行转换逻辑
}

// 创建了验证器
type CSVValidator struct {
    requiredFields []string
}

func (v *CSVValidator) Validate(headers []string) error {
    // ... 20 行验证逻辑
}

// 总计: ~150 行 + 外部依赖
```

### ✅ Go Minimal Code 实现

```go
package config

import (
    "encoding/csv"
    "fmt"
    "io"
)

// ParseCSV 解析 CSV 文件
func ParseCSV(r io.Reader) ([]map[string]string, error) {
    reader := csv.NewReader(r)
    records, err := reader.ReadAll()
    if err != nil {
        return nil, fmt.Errorf("parse CSV: %w", err)
    }
    
    if len(records) == 0 {
        return nil, fmt.Errorf("empty CSV")
    }
    
    headers := records[0]
    var result []map[string]string
    
    for _, row := range records[1:] {
        record := make(map[string]string)
        for i, header := range headers {
            if i < len(row) {
                record[header] = row[i]
            }
        }
        result = append(result, record)
    }
    
    return result, nil
}
```

### 结果
- 代码量: 150 行 → **30 行** (-80%)
- 依赖: 1 个 → **0 个** (-100%)
- 复杂度: 4 个类型 → **1 个函数**

### Go Minimal Code 阶梯应用
1. ✅ 标准库 `encoding/csv` 能做
2. ❌ 不需要接口（只有一个实现）

---

## 案例 3: HTTP 客户端封装

### 需求
封装 HTTP 请求，添加重试和超时。

### ❌ 过度工程实现

```go
// 创建了 HTTP 客户端接口
type HTTPClient interface {
    Do(req *http.Request) (*http.Response, error)
    Get(url string) (response *http.Response, err error)
    Post(url string, body io.Reader) (*http.Response, error)
}

// 创建了包装器
type RetryClient struct {
    client     HTTPClient
    maxRetries int
    baseDelay  time.Duration
}

// 创建了重试策略接口
type RetryStrategy interface {
    ShouldRetry(resp *http.Response) bool
    Backoff(attempt int) time.Duration
}

// 创建了指数退避实现
type ExponentialBackoff struct {
    base time.Duration
    max  time.Duration
}

// 创建了中间件链
type Middleware func(http.Handler) http.Handler

func Chain(middlewares ...Middleware) Middleware {
    return func(next http.Handler) http.Handler {
        for i := len(middlewares) - 1; i >= 0; i-- {
            next = middlewares[i](next)
        }
        return next
    }
}

// 创建了日志中间件
type LoggingMiddleware struct {
    logger Logger
}

// 创建了认证中间件
type AuthMiddleware struct {
    token string
}

// 创建了配置结构体
type ClientConfig struct {
    Timeout       time.Duration
    MaxRetries    int
    BaseDelay     time.Duration
    MaxDelay      time.Duration
    EnableLogging bool
    EnableAuth    bool
}

// 总计: ~300 行 + 高度抽象
```

### ✅ Go Minimal Code 实现

```go
package httpclient

import (
    "fmt"
    "net/http"
    "time"
)

// Client 带重试的 HTTP 客户端
type Client struct {
    http.Client
    maxRetries int
}

// New 创建客户端
func New(maxRetries int) *Client {
    return &Client{
        Client: http.Client{
            Timeout: 30 * time.Second,
        },
        maxRetries: maxRetries,
    }
}

// Get 带重试的 GET 请求
func (c *Client) Get(url string) ([]byte, error) {
    var lastErr error
    
    for attempt := 0; attempt <= c.maxRetries; attempt++ {
        resp, err := c.Client.Get(url)
        if err != nil {
            lastErr = err
            if attempt < c.maxRetries {
                time.Sleep(time.Duration(attempt+1) * time.Second)
                continue
            }
            return nil, fmt.Errorf("get %s: %w", url, err)
        }
        defer resp.Body.Close()
        
        body := make([]byte, 1024)
        n, _ := resp.Body.Read(body)
        return body[:n], nil
    }
    
    return nil, fmt.Errorf("failed after %d retries: %w", c.maxRetries, lastErr)
}
```

### 结果
- 代码量: 300 行 → **40 行** (-87%)
- 类型数: 8 个 → **2 个** (-75%)
- 接口数: 4 个 → **0 个** (-100%)

### Go Minimal Code 阶梯应用
1. ✅ `net/http` 标准库
2. ❌ 不需要接口（只有一个实现）
3. ❌ 不需要中间件链（还没用到）
4. ✅ 最小可用实现

---

## 案例 4: 配置管理

### 需求
管理应用配置（数据库连接、API Key 等）。

### ❌ 过度工程实现

```go
// 创建了配置接口
type ConfigProvider interface {
    Get(key string) string
    GetInt(key string) int
    GetBool(key string) bool
    Load() error
    Validate() error
}

// 创建了文件配置提供者
type FileConfig struct {
    filepath string
    data     map[string]interface{}
}

// 创建了环境变量配置提供者
type EnvConfig struct {
    prefix string
}

// 创建了远程配置提供者
type RemoteConfig struct {
    endpoint string
    client   *http.Client
}

// 创建了配置合并器
type ConfigMerger struct {
    providers []ConfigProvider
}

// 创建了配置验证器
type ConfigValidator struct {
    rules map[string]ValidationRule
}

// 创建了配置 watcher（自动重载）
type ConfigWatcher struct {
    provider ConfigProvider
    onChange func()
}

// 总计: ~400 行 + 高度抽象
```

### ✅ Go Minimal Code 实现

```go
package config

import (
    "fmt"
    "os"
)

// Config 应用配置
type Config struct {
    DBHost     string
    DBPort     int
    DBUser     string
    DBPass     string
    APIKey     string
    Port       int
}

// Load 从环境变量加载配置
func Load() (*Config, error) {
    dbPort := getenvInt("DB_PORT", 5432)
    port := getenvInt("PORT", 8080)
    
    cfg := &Config{
        DBHost:   getenv("DB_HOST", "localhost"),
        DBPort:   dbPort,
        DBUser:   getenv("DB_USER", "postgres"),
        DBPass:   getenv("DB_PASS", ""),
        APIKey:   getenv("API_KEY", ""),
        Port:     port,
    }
    
    if cfg.DBPass == "" {
        return nil, fmt.Errorf("DB_PASS is required")
    }
    
    return cfg, nil
}

func getenv(key, defaultVal string) string {
    if val := os.Getenv(key); val != "" {
        return val
    }
    return defaultVal
}

func getenvInt(key string, defaultVal int) int {
    val := os.Getenv(key)
    if val == "" {
        return defaultVal
    }
    
    var result int
    fmt.Sscanf(val, "%d", &result)
    return result
}
```

### 结果
- 代码量: 400 行 → **45 行** (-89%)
- 类型数: 7 个 → **2 个** (-71%)
- 接口数: 1 个 → **0 个** (-100%)

### Go Minimal Code 阶梯应用
1. ✅ `os.Getenv` 标准库
2. ❌ 不需要接口（单一实现）
3. ❌ 不需要远程配置（还没需要）
4. ❌ 不需要自动重载（还没需要）

---

## 案例 5: 日志系统

### 需求
添加应用日志功能。

### ❌ 过度工程实现

```go
// 引入了 zap 日志库
import "go.uber.org/zap"

// 创建了日志级别枚举
type LogLevel int

const (
    DEBUG LogLevel = iota
    INFO
    WARN
    ERROR
    FATAL
)

// 创建了日志接口
type Logger interface {
    Debug(msg string, fields ...Field)
    Info(msg string, fields ...Field)
    Warn(msg string, fields ...Field)
    Error(msg string, fields ...Field)
    Fatal(msg string, fields ...Field)
}

// 创建了结构化日志字段
type Field struct {
    Key   string
    Value interface{}
}

// 创建了日志处理器接口
type Handler interface {
    Handle(entry *LogEntry) error
}

// 创建了文件处理器
type FileHandler struct {
    writer io.Writer
}

// 创建了控制台处理器
type ConsoleHandler struct {
    writer io.Writer
}

// 创建了远程处理器（发送到日志服务）
type RemoteHandler struct {
    endpoint string
    client   *http.Client
}

// 创建了日志路由器
type LogRouter struct {
    handlers []Handler
}

// 创建了日志中间件
func LoggingMiddleware(next http.Handler) http.Handler {
    // ... 30 行
}

// 总计: ~500 行 + 外部依赖
```

### ✅ Go Minimal Code 实现

```go
package logger

import (
    "log"
    "log/slog"
    "os"
)

var (
    Debug = slog.Debug
    Info  = slog.Info
    Warn  = slog.Warn
    Error = slog.Error
)

func Init() {
    logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
        Level: slog.LevelDebug,
    }))
    slog.SetDefault(logger)
}
```

### 结果
- 代码量: 500 行 → **15 行** (-97%)
- 依赖: 1 个 → **0 个** (-100%)
- 复杂度: 极高 → **极低**

### Go Minimal Code 阶梯应用
1. ✅ Go 1.21+ 内置 `log/slog` 标准库
2. ❌ 不需要自定义日志级别
3. ❌ 不需要处理器抽象
4. ❌ 不需要中间件（用标准库就行）

---

## 案例总结

### 常见过度工程模式

| 模式 | 红旗信号 | Go Minimal Code 建议 |
|------|----------|---------------------|
| 接口过早 | 接口只有一个实现 | 内联为具体类型 |
| 抽象过度 | 3 层以上的包装 | 直接调用底层 |
| 推测性功能 | "可能以后用到" | 删除，需要时再加 |
| 第三方依赖 | 手写了标准库已有的功能 | 用标准库 |
| 配置膨胀 | 配置结构体有 20 个字段 | 只保留用到的 |
| 中间件链 | 5 个中间件串联 | 合并或移除 |

### 收益统计

| 案例 | 原始行数 | Go Minimal Code 行数 | 减少比例 |
|------|----------|---------------------|----------|
| 日期选择器 | 150 | 1 | -99% |
| CSV 解析 | 150 | 30 | -80% |
| HTTP 客户端 | 300 | 40 | -87% |
| 配置管理 | 400 | 45 | -89% |
| 日志系统 | 500 | 15 | -97% |
| **平均** | **300** | **26** | **-91%** |

### 关键原则

1. **标准库优先** - 90% 的情况标准库够用
2. **延迟抽象** - 重复 3 次以上再封装
3. **删除优先** - 能删的绝不添加
4. **平庸优于巧妙** - 巧妙的代码凌晨三点会找你
5. **一行胜过五十行** - 但不是为了少而少，是为了必要而少

---

**使用方式**: 在审查代码时，参考本案例库识别类似模式，应用 Go Minimal Code 阶梯选择最简方案。
