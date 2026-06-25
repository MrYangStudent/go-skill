# 知识库初始化参考文件

> 此文件展示知识条目标准格式，可作为项目知识库的初始模板。
> 使用方式：将内容复制到 `project-knowledge/common-utils.md` 后手动调整，
> 或运行 `knowledge init --example` 自动生成。

<!-- id: entry-ref-01 -->
## [slice, util] MustGet - 安全取值（泛型）

**标签**: slice, util, generic
**来源**: pkg/slicex/must.go
**更新**: 2026-06-25
**用途**: 从切片中安全获取指定索引元素，越界时返回零值而非 panic

```go
// MustGet 从切片中安全获取第 i 个元素.
// 越界时返回零值和 false.
func MustGet[T any](s []T, i int) (T, bool) {
    if i < 0 || i >= len(s) {
        var zero T
        return zero, false
    }
    return s[i], true
}
```

---

<!-- id: entry-ref-02 -->
## [retry, http] DoWithRetry - HTTP 请求重试

**标签**: retry, http, resilience
**来源**: pkg/httpx/retry.go
**更新**: 2026-06-24
**用途**: 对 HTTP 请求进行指数退避重试，支持可重试错误判断

```go
// RetryConfig 重试配置.
type RetryConfig struct {
    MaxAttempts int
    BaseWait    time.Duration
    MaxWait     time.Duration
}

// DoWithRetry 执行带重试的 HTTP 请求.
func DoWithRetry(ctx context.Context, client *http.Client, req *http.Request, cfg RetryConfig) (*http.Response, error) {
    var resp *http.Response
    var err error
    for attempt := 1; attempt <= cfg.MaxAttempts; attempt++ {
        resp, err = client.Do(req.Clone(ctx))
        if err == nil && resp.StatusCode < 500 {
            return resp, nil
        }
        if attempt < cfg.MaxAttempts {
            wait := min(cfg.BaseWait*(1<<(attempt-1)), cfg.MaxWait)
            select {
            case <-ctx.Done():
                return nil, ctx.Err()
            case <-time.After(wait):
            }
        }
    }
    return resp, fmt.Errorf("retry exhausted: %w", err)
}
```

---

<!-- id: entry-ref-03 -->
## [cache, concurrent] SafeCache - 并发安全缓存

**标签**: cache, concurrent, generic
**来源**: pkg/cachex/cache.go
**更新**: 2026-06-23
**用途**: 泛型并发安全缓存，支持 TTL 过期和懒加载

```go
// SafeCache 泛型并发安全缓存.
type SafeCache[K comparable, V any] struct {
    mu    sync.RWMutex
    items map[K]cacheItem[V]
    ttl   time.Duration
}

type cacheItem[V any] struct {
    value  V
    expiry time.Time
}

func NewSafeCache[K comparable, V any](ttl time.Duration) *SafeCache[K, V] {
    return &SafeCache[K, V]{
        items: make(map[K]cacheItem[V]),
        ttl:   ttl,
    }
}

func (c *SafeCache[K, V]) Get(key K) (V, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    item, ok := c.items[key]
    if !ok || time.Now().After(item.expiry) {
        var zero V
        return zero, false
    }
    return item.value, true
}

func (c *SafeCache[K, V]) Set(key K, val V) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = cacheItem[V]{
        value:  val,
        expiry: time.Now().Add(c.ttl),
    }
}
```

---

<!-- id: entry-ref-04 -->
## [page, query] Paginate - 通用分页查询

**标签**: page, query, database
**来源**: pkg/pagex/page.go
**更新**: 2026-06-22
**用途**: 数据库分页查询参数封装，自动计算 offset 和总页数

```go
// Params 分页参数.
type Params struct {
    Page     int
    PageSize int
}

// Result 分页结果.
type Result[T any] struct {
    Items      []T
    Total      int64
    Page       int
    PageSize   int
    TotalPages int
}

func (p Params) Offset() int {
    if p.Page < 1 {
        p.Page = 1
    }
    return (p.Page - 1) * p.PageSize
}

func NewResult[T any](items []T, total int64, params Params) Result[T] {
    totalPages := int(total) / params.PageSize
    if int(total)%params.PageSize != 0 {
        totalPages++
    }
    return Result[T]{
        Items:      items,
        Total:      total,
        Page:       params.Page,
        PageSize:   params.PageSize,
        TotalPages: totalPages,
    }
}
```

---

<!-- id: entry-ref-05 -->
## [ctx, timeout] WithTimeout - Context 超时封装

**标签**: ctx, timeout, middleware
**来源**: pkg/ctxx/timeout.go
**更新**: 2026-06-21
**用途**: 为数据库和 HTTP 调用添加默认超时 Context 的快捷方法

```go
// WithDefaultTimeout 返回带有默认超时的 Context.
func WithDefaultTimeout(ctx context.Context) (context.Context, context.CancelFunc) {
    if ctx == nil {
        ctx = context.Background()
    }
    return context.WithTimeout(ctx, 30*time.Second)
}

// WithTimeout 返回带有指定超时的 Context.
func WithTimeout(ctx context.Context, d time.Duration) (context.Context, context.CancelFunc) {
    if ctx == nil {
        ctx = context.Background()
    }
    return context.WithTimeout(ctx, d)
}
```
