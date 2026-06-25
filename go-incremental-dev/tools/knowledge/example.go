package main

import (
	"fmt"
	"time"
)

// exampleContent 返回带有当前日期的 5 条示例知识条目.
func exampleContent() string {
	today := time.Now().Format("2006-01-02")

	return fmt.Sprintf(`<!-- id: entry-example-01 -->
## [slice, util] MustGet - 安全取值

**标签**: slice, util, generic
**来源**: pkg/slicex/must.go
**更新**: %s
**用途**: 从切片中安全获取指定索引元素，越界时返回零值而非 panic

`+"```"+`go
func MustGet[T any](s []T, i int) (T, bool) {
    if i < 0 || i >= len(s) {
        var zero T
        return zero, false
    }
    return s[i], true
}
`+"```"+`

---

<!-- id: entry-example-02 -->
## [retry, http] DoWithRetry - HTTP 请求重试

**标签**: retry, http, resilience
**来源**: pkg/httpx/retry.go
**更新**: %s
**用途**: 对 HTTP 请求进行指数退避重试，支持可重试错误判断

`+"```"+`go
func DoWithRetry(ctx context.Context, client *http.Client, req *http.Request, maxAttempts int, baseWait time.Duration) (*http.Response, error) {
    for attempt := 1; attempt <= maxAttempts; attempt++ {
        resp, err := client.Do(req.Clone(ctx))
        if err == nil && resp.StatusCode < 500 {
            return resp, nil
        }
        if attempt < maxAttempts {
            select {
            case <-ctx.Done():
                return nil, ctx.Err()
            case <-time.After(baseWait * time.Duration(attempt)):
            }
        }
    }
    return nil, fmt.Errorf("retry exhausted after %%d attempts", maxAttempts)
}
`+"```"+`

---

<!-- id: entry-example-03 -->
## [cache, concurrent] SafeCache - 并发安全缓存

**标签**: cache, concurrent, generic
**来源**: pkg/cachex/cache.go
**更新**: %s
**用途**: 泛型并发安全缓存，支持 TTL 过期

`+"```"+`go
type SafeCache[K comparable, V any] struct {
    mu    sync.RWMutex
    items map[K]struct {
        value  V
        expiry time.Time
    }
    ttl time.Duration
}
`+"```"+`

---

<!-- id: entry-example-04 -->
## [page, query] Paginate - 通用分页

**标签**: page, query, pagination
**来源**: pkg/pagex/page.go
**更新**: %s
**用途**: 数据库分页查询参数封装

`+"```"+`go
type Params struct {
    Page     int
    PageSize int
}

func (p Params) Offset() int {
    if p.Page < 1 {
        p.Page = 1
    }
    return (p.Page - 1) * p.PageSize
}
`+"```"+`

---

<!-- id: entry-example-05 -->
## [ctx, timeout] WithTimeout - Context 超时封装

**标签**: ctx, timeout, middleware
**来源**: pkg/ctxx/timeout.go
**更新**: %s
**用途**: 为数据库和 HTTP 调用添加默认超时 Context

`+"```"+`go
func WithDefaultTimeout(ctx context.Context) (context.Context, context.CancelFunc) {
    if ctx == nil {
        ctx = context.Background()
    }
    return context.WithTimeout(ctx, 30*time.Second)
}
`+"```"+`

---
`, today, today, today, today, today)
}
