# 工具函数封装规范

## 核心原则

1. **标准库优先** - 仅使用 Go 标准库，不引入第三方依赖
2. **泛型优先** - Go 1.21+ 泛型用于类型安全的通用函数
3. **接口最小化** - 函数参数接受 `io.Reader` / `fmt.Stringer` 等标准接口
4. **零值可用** - 结构体零值即可安全使用

---

## HTTP 客户端封装

```go
package httpx

import (
    "bytes"
    "context"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

type Client struct {
    baseURL    string
    headers    map[string]string
    httpClient *http.Client
}

func NewClient(baseURL string, timeout time.Duration) *Client {
    return &Client{
        baseURL: baseURL,
        headers: make(map[string]string),
        httpClient: &http.Client{Timeout: timeout},
    }
}

type Response[T any] struct {
    StatusCode int
    Headers    http.Header
    Body       T
}

func Get[T any](ctx context.Context, c *Client, path string) (*Response[T], error) {
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+path, nil)
    if err != nil {
        return nil, fmt.Errorf("create GET request: %w", err)
    }
    for k, v := range c.headers {
        req.Header.Set(k, v)
    }
    
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("execute request: %w", err)
    }
    defer resp.Body.Close()

    var result T
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, fmt.Errorf("decode response: %w", err)
    }
    return &Response[T]{StatusCode: resp.StatusCode, Headers: resp.Header, Body: result}, nil
}

func Post[T any](ctx context.Context, c *Client, path string, body any) (*Response[T], error) {
    jsonBody, err := json.Marshal(body)
    if err != nil {
        return nil, fmt.Errorf("marshal request body: %w", err)
    }
    
    req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+path, bytes.NewReader(jsonBody))
    if err != nil {
        return nil, fmt.Errorf("create POST request: %w", err)
    }
    req.Header.Set("Content-Type", "application/json")
    for k, v := range c.headers {
        req.Header.Set(k, v)
    }
    
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("execute request: %w", err)
    }
    defer resp.Body.Close()

    var result T
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil && err != io.EOF {
        return nil, fmt.Errorf("decode response: %w", err)
    }
    return &Response[T]{StatusCode: resp.StatusCode, Headers: resp.Header, Body: result}, nil
}
```

---

## 切片工具

```go
package slicex

import "cmp"

// Map 将切片每个元素通过 fn 转换为新类型
func Map[T any, R any](slice []T, fn func(T) R) []R {
    result := make([]R, len(slice))
    for i, v := range slice {
        result[i] = fn(v)
    }
    return result
}

// Filter 过滤切片
func Filter[T any](slice []T, fn func(T) bool) []T {
    result := make([]T, 0, len(slice))
    for _, v := range slice {
        if fn(v) {
            result = append(result, v)
        }
    }
    return result
}

// Unique 对可比较类型切片去重
func Unique[T comparable](slice []T) []T {
    seen := make(map[T]struct{}, len(slice))
    result := make([]T, 0, len(slice))
    for _, v := range slice {
        if _, ok := seen[v]; !ok {
            seen[v] = struct{}{}
            result = append(result, v)
        }
    }
    return result
}

// GroupBy 按键值分组
func GroupBy[T any, K comparable](slice []T, keyFn func(T) K) map[K][]T {
    result := make(map[K][]T)
    for _, v := range slice {
        k := keyFn(v)
        result[k] = append(result[k], v)
    }
    return result
}

// Chunk 将切片分割为指定大小的子切片
func Chunk[T any](slice []T, size int) [][]T {
    if size <= 0 {
        return nil
    }
    result := make([][]T, 0, (len(slice)+size-1)/size)
    for i := 0; i < len(slice); i += size {
        end := i + size
        if end > len(slice) {
            end = len(slice)
        }
        result = append(result, slice[i:end])
    }
    return result
}

// Sort 对可排序类型切片排序
func Sort[T cmp.Ordered](slice []T) []T {
    result := make([]T, len(slice))
    copy(result, slice)
    for i := 1; i < len(result); i++ {
        for j := i; j > 0 && result[j] < result[j-1]; j-- {
            result[j], result[j-1] = result[j-1], result[j]
        }
    }
    return result
}

// Flatten 将嵌套切片展平
func Flatten[T any](slices [][]T) []T {
    total := 0
    for _, s := range slices {
        total += len(s)
    }
    result := make([]T, 0, total)
    for _, s := range slices {
        result = append(result, s...)
    }
    return result
}
```

---

## Map 工具

```go
package mapx

// Keys 返回 map 的所有 key
func Keys[K comparable, V any](m map[K]V) []K {
    keys := make([]K, 0, len(m))
    for k := range m {
        keys = append(keys, k)
    }
    return keys
}

// Values 返回 map 的所有 value
func Values[K comparable, V any](m map[K]V) []V {
    values := make([]V, 0, len(m))
    for _, v := range m {
        values = append(values, v)
    }
    return values
}

// Merge 合并多个 map
func Merge[K comparable, V any](maps ...map[K]V) map[K]V {
    result := make(map[K]V)
    for _, m := range maps {
        for k, v := range m {
            result[k] = v
        }
    }
    return result
}

// FilterKeys 按条件过滤 key
func FilterKeys[K comparable, V any](m map[K]V, fn func(K) bool) map[K]V {
    result := make(map[K]V)
    for k, v := range m {
        if fn(k) {
            result[k] = v
        }
    }
    return result
}
```

---

## 分页工具

```go
package pagex

type Params struct {
    Page     int
    PageSize int
}

func (p Params) Offset() int {
    if p.Page <= 0 {
        return 0
    }
    return (p.Page - 1) * p.Limit()
}

func (p Params) Limit() int {
    if p.PageSize <= 0 {
        return 20
    }
    if p.PageSize > 100 {
        return 100
    }
    return p.PageSize
}

type Result[T any] struct {
    Items    []T   `json:"items"`
    Total    int64 `json:"total"`
    Page     int   `json:"page"`
    PageSize int   `json:"pageSize"`
    Pages    int   `json:"pages"`
}

func NewResult[T any](items []T, total int64, p Params) Result[T] {
    limit := p.Limit()
    pages := int(total) / limit
    if int(total)%limit > 0 {
        pages++
    }
    return Result[T]{Items: items, Total: total, Page: p.Page, PageSize: limit, Pages: pages}
}
```

---

## Retry 重试工具

```go
package retryx

import (
    "context"
    "fmt"
    "math"
    "time"
)

type Config struct {
    MaxAttempts int
    InitialWait time.Duration
    MaxWait     time.Duration
    Multiplier  float64
}

func Do(ctx context.Context, cfg Config, fn func() error) error {
    var lastErr error
    wait := cfg.InitialWait

    for attempt := 1; attempt <= cfg.MaxAttempts; attempt++ {
        if err := ctx.Err(); err != nil {
            return fmt.Errorf("context cancelled: %w", err)
        }

        lastErr = fn()
        if lastErr == nil {
            return nil
        }

        if attempt == cfg.MaxAttempts {
            break
        }

        select {
        case <-ctx.Done():
            return fmt.Errorf("context cancelled during retry: %w", ctx.Err())
        case <-time.After(wait):
        }

        wait = time.Duration(math.Min(float64(wait)*cfg.Multiplier, float64(cfg.MaxWait)))
    }

    return fmt.Errorf("after %d attempts, last error: %w", cfg.MaxAttempts, lastErr)
}
```

---

## 并发安全缓存

```go
package cachex

import (
    "sync"
    "time"
)

type item[V any] struct {
    value     V
    expiredAt time.Time
}

type Cache[K comparable, V any] struct {
    mu   sync.RWMutex
    data map[K]item[V]
}

func New[K comparable, V any]() *Cache[K, V] {
    return &Cache[K, V]{data: make(map[K]item[V])}
}

func (c *Cache[K, V]) Set(key K, value V, ttl time.Duration) {
    c.mu.Lock()
    defer c.mu.Unlock()
    var expiredAt time.Time
    if ttl > 0 {
        expiredAt = time.Now().Add(ttl)
    }
    c.data[key] = item[V]{value: value, expiredAt: expiredAt}
}

func (c *Cache[K, V]) Get(key K) (V, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    it, ok := c.data[key]
    if !ok {
        var zero V
        return zero, false
    }
    if !it.expiredAt.IsZero() && time.Now().After(it.expiredAt) {
        var zero V
        return zero, false
    }
    return it.value, true
}

func (c *Cache[K, V]) Delete(key K) {
    c.mu.Lock()
    defer c.mu.Unlock()
    delete(c.data, key)
}

func (c *Cache[K, V]) Clear() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data = make(map[K]item[V])
}
```

---

## 上下文值工具

```go
package ctxx

import "context"

type Key[T any] struct {
    name string
}

func NewKey[T any](name string) Key[T] {
    return Key[T]{name: name}
}

func WithValue[T any](ctx context.Context, key Key[T], value T) context.Context {
    return context.WithValue(ctx, key, value)
}

func Value[T any](ctx context.Context, key Key[T]) (T, bool) {
    v := ctx.Value(key)
    if v == nil {
        var zero T
        return zero, false
    }
    typed, ok := v.(T)
    return typed, ok
}
```

---

## 字符串工具

```go
package strx

import "strings"

// Truncate 截断字符串
func Truncate(s string, maxLen int, suffix string) string {
    if len(s) <= maxLen {
        return s
    }
    if suffix == "" {
        return s[:maxLen]
    }
    if maxLen <= len(suffix) {
        return suffix
    }
    return s[:maxLen-len(suffix)] + suffix
}

// ContainsAny 检查是否包含任意一个子串
func ContainsAny(s string, substrs []string) bool {
    for _, sub := range substrs {
        if strings.Contains(s, sub) {
            return true
        }
    }
    return false
}

// TitleCase 首字母大写
func TitleCase(s string) string {
    if s == "" {
        return s
    }
    return strings.ToUpper(s[:1]) + s[1:]
}
```

---

## 时间工具

```go
package timex

import "time"

// UnixMilli 返回毫秒时间戳
func UnixMilli(t time.Time) int64 {
    return t.UnixMilli()
}

// FromUnixMilli 从毫秒时间戳创建时间
func FromUnixMilli(ms int64) time.Time {
    return time.UnixMilli(ms)
}

// FormatDate 格式化日期
func FormatDate(t time.Time) string {
    return t.Format("2006-01-02")
}

// FormatDateTime 格式化日期时间
func FormatDateTime(t time.Time) string {
    return t.Format("2006-01-02 15:04:05")
}
```

---

## 错误工具

```go
package errx

import "errors"

// Is 判断错误类型
func Is(err, target error) bool {
    return errors.Is(err, target)
}

// As 转换错误类型
func As[T error](err error) (T, bool) {
    var target T
    ok := errors.As(err, &target)
    return target, ok
}

// Join 组合多个错误
func Join(errs ...error) error {
    var valid []error
    for _, e := range errs {
        if e != nil {
            valid = append(valid, e)
        }
    }
    if len(valid) == 0 {
        return nil
    }
    if len(valid) == 1 {
        return valid[0]
    }
    sb := &strings.Builder{}
    for i, e := range valid {
        if i > 0 {
            sb.WriteString("; ")
        }
        sb.WriteString(e.Error())
    }
    return errors.New(sb.String())
}
```
