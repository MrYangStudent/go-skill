---
name: go-utility-functions
description: >
  Go 通用工具函数封装技能。当用户要求封装常用函数、编写工具库、生成 HTTP 客户端封装、
  签名/加密工具、排序工具、时间格式化工具、泛型切片/Map 转换工具时触发。
  专门用于识别重复逻辑并封装为可复用的类型安全工具函数，遵循 Go 标准库优先原则。
triggers:
  - 封装工具函数
  - 通用函数
  - 工具库
  - HTTP封装
  - 签名工具
  - 加密工具
  - 排序工具
  - 时间格式化
  - 泛型转换
  - 切片工具
  - Map工具
  - 去重
  - 分页
  - retry重试
  - Go工具函数
  - utility functions
  - Go通用函数
---

# Go 通用工具函数封装 (Go Utility Functions)

## 技能定位

Go 工具函数封装专家，善于识别项目中的重复逻辑，将其抽象为类型安全、零外部依赖的可复用函数。遵循标准库优先、泛型优先、接口最小化原则。

## 核心原则

1. **标准库优先** — 仅使用 Go 标准库，不引入第三方依赖
2. **泛型优先** — Go 1.21+ 泛型用于类型安全的通用函数，避免 `interface{}`
3. **接口最小化** — 函数参数接受 `io.Reader` / `fmt.Stringer` 等标准接口
4. **零值可用** — 结构体零值即可安全使用，无需初始化函数

## 封装检查清单

---

### 1. HTTP 客户端封装

**问题**: 每个 HTTP 调用都重复设置超时、Header、错误处理。

**封装方案**:

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

// Client 封装 HTTP 客户端，内置超时和通用 Header。
type Client struct {
    baseURL    string
    headers    map[string]string
    httpClient *http.Client
}

// NewClient 创建 HTTP 客户端，timeout 为整体请求超时。
func NewClient(baseURL string, timeout time.Duration) *Client {
    return &Client{
        baseURL: baseURL,
        headers: make(map[string]string),
        httpClient: &http.Client{
            Timeout: timeout,
        },
    }
}

// SetHeader 设置通用 Header，所有请求都会携带。
func (c *Client) SetHeader(key, value string) *Client {
    c.headers[key] = value
    return c
}

// Response 封装 HTTP 响应，泛型支持任意响应体类型。
type Response[T any] struct {
    StatusCode int
    Headers    http.Header
    Body       T
}

// Get 发送 GET 请求并解码 JSON 响应。
func Get[T any](ctx context.Context, c *Client, path string) (*Response[T], error) {
    req, err := c.newRequest(ctx, http.MethodGet, path, nil)
    if err != nil {
        return nil, fmt.Errorf("create GET request: %w", err)
    }
    return do[T](c, req)
}

// Post 发送 POST 请求，body 会被编码为 JSON。
func Post[T any](ctx context.Context, c *Client, path string, body interface{}) (*Response[T], error) {
    req, err := c.newRequest(ctx, http.MethodPost, path, body)
    if err != nil {
        return nil, fmt.Errorf("create POST request: %w", err)
    }
    return do[T](c, req)
}

// newRequest 创建带通用 Header 的请求。
func (c *Client) newRequest(ctx context.Context, method, path string, body interface{}) (*http.Request, error) {
    var bodyReader io.Reader
    if body != nil {
        data, err := json.Marshal(body)
        if err != nil {
            return nil, fmt.Errorf("marshal body: %w", err)
        }
        bodyReader = bytes.NewReader(data)
    }

    req, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, bodyReader)
    if err != nil {
        return nil, fmt.Errorf("create request: %w", err)
    }

    for k, v := range c.headers {
        req.Header.Set(k, v)
    }
    if body != nil {
        req.Header.Set("Content-Type", "application/json")
    }
    return req, nil
}

// do 执行请求并解码响应。
func do[T any](c *Client, req *http.Request) (*Response[T], error) {
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("execute request: %w", err)
    }
    defer resp.Body.Close()

    var result T
    if resp.StatusCode >= 400 {
        body, _ := io.ReadAll(resp.Body)
        return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
    }

    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, fmt.Errorf("decode response: %w", err)
    }

    return &Response[T]{
        StatusCode: resp.StatusCode,
        Headers:    resp.Header,
        Body:       result,
    }, nil
}
```

**使用示例**:
```go
client := httpx.NewClient("https://api.example.com", 10*time.Second).
    SetHeader("Authorization", "Bearer "+token).
    SetHeader("Accept", "application/json")

resp, err := httpx.Get[User](ctx, client, "/users/123")
```

---

### 2. 签名工具封装

**问题**: API 签名逻辑散落各处，HMAC 签名参数拼接不统一。

**封装方案**:

```go
package signx

import (
    "crypto/hmac"
    "crypto/md5"
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "sort"
    "strings"
)

// Signer 通用签名器。
type Signer struct {
    secretKey []byte
    method    Method
}

// Method 签名算法。
type Method int

const (
    HMACSHA256 Method = iota
    MD5
)

// NewHMACSHA256Signer 创建 HMAC-SHA256 签名器。
func NewHMACSHA256Signer(secretKey string) *Signer {
    return &Signer{secretKey: []byte(secretKey), method: HMACSHA256}
}

// NewMD5Signer 创建 MD5 签名器（仅用于兼容旧接口，新系统应使用 HMAC-SHA256）。
func NewMD5Signer() *Signer {
    return &Signer{method: MD5}
}

// Sign 对参数按 key 字典序排序后拼接签名。
// 拼接格式: key1=value1&key2=value2... + &key=secretKey
func (s *Signer) Sign(params map[string]string) (string, error) {
    sorted := SortKeys(params)
    var buf strings.Builder
    for i, k := range sorted {
        if i > 0 {
            buf.WriteByte('&')
        }
        buf.WriteString(k)
        buf.WriteByte('=')
        buf.WriteString(params[k])
    }

    switch s.method {
    case HMACSHA256:
        mac := hmac.New(sha256.New, s.secretKey)
        mac.Write([]byte(buf.String()))
        return hex.EncodeToString(mac.Sum(nil)), nil
    case MD5:
        h := md5.Sum([]byte(buf.String() + "&key=" + string(s.secretKey)))
        return hex.EncodeToString(h[:]), nil
    default:
        return "", fmt.Errorf("unsupported sign method: %d", s.method)
    }
}

// Verify 验证签名是否匹配。
func (s *Signer) Verify(params map[string]string, signature string) (bool, error) {
    expected, err := s.Sign(params)
    if err != nil {
        return false, fmt.Errorf("compute signature: %w", err)
    }
    return hmac.Equal([]byte(expected), []byte(signature)), nil
}

// SortKeys 返回按字典序排序的 key 列表。
func SortKeys(params map[string]string) []string {
    keys := make([]string, 0, len(params))
    for k := range params {
        keys = append(keys, k)
    }
    sort.Strings(keys)
    return keys
}
```

**使用示例**:
```go
signer := signx.NewHMACSHA256Signer("my-secret-key")
sig, err := signer.Sign(map[string]string{
    "amount": "100",
    "orderId": "12345",
    "timestamp": "1700000000",
})

ok, err := signer.Verify(params, receivedSig)
```

---

### 3. 加密/哈希工具封装

**问题**: AES 加密、SHA 哈希等操作步骤冗长且容易出错。

**封装方案**:

```go
package cryptox

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "io"
)

// SHA256 计算字符串的 SHA-256 哈希值，返回十六进制编码。
func SHA256(data string) string {
    h := sha256.Sum256([]byte(data))
    return hex.EncodeToString(h[:])
}

// AESEncrypt 使用 AES-GCM 加密明文，key 必须为 16/24/32 字节。
func AESEncrypt(key, plaintext []byte) ([]byte, error) {
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, fmt.Errorf("create cipher: %w", err)
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, fmt.Errorf("create GCM: %w", err)
    }

    nonce := make([]byte, gcm.NonceSize())
    if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
        return nil, fmt.Errorf("generate nonce: %w", err)
    }

    // nonce 拼在密文前面，解密时先取出
    return gcm.Seal(nonce, nonce, plaintext, nil), nil
}

// AESDecrypt 使用 AES-GCM 解密密文。
func AESDecrypt(key, ciphertext []byte) ([]byte, error) {
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, fmt.Errorf("create cipher: %w", err)
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, fmt.Errorf("create GCM: %w", err)
    }

    nonceSize := gcm.NonceSize()
    if len(ciphertext) < nonceSize {
        return nil, fmt.Errorf("ciphertext too short")
    }

    nonce, ciphertext := ciphertext[:nonceSize], ciphertext[nonceSize:]
    return gcm.Open(nil, nonce, ciphertext, nil)
}
```

---

### 4. 排序工具封装

**问题**: 对结构体切片按不同字段排序需要重复实现 `sort.Interface`。

**封装方案**:

```go
package slicex

import "sort"

// By 对切片按指定字段排序，less 函数定义排序规则。
func By[T any](slice []T, less func(a, b T) bool) {
    sort.Slice(slice, func(i, j int) bool {
        return less(slice[i], slice[j])
    })
}

// ByStable 稳定排序，相等元素保持原始顺序。
func ByStable[T any](slice []T, less func(a, b T) bool) {
    sort.SliceStable(slice, func(i, j int) bool {
        return less(slice[i], slice[j])
    })
}

// SortByField 对结构体切片按可比较字段排序。
func SortByField[T any, F cmp.Ordered](slice []T, field func(T) F) {
    sort.Slice(slice, func(i, j int) bool {
        return field(slice[i]) < field(slice[j])
    })
}
```

**使用示例**:
```go
// 按年龄排序
slicex.By(users, func(a, b User) bool { return a.Age < b.Age })

// 按名称稳定排序
slicex.ByStable(users, func(a, b User) bool { return a.Name < b.Name })

// 按字段排序（Go 1.21+ cmp.Ordered）
slicex.SortByField(users, func(u User) string { return u.Name })
```

---

### 5. 时间格式化工具封装

**问题**: Go 的时间格式化使用 `"2006-01-02 15:04:05"` 硬编码字符串，容易写错且不统一。

**封装方案**:

```go
package timex

import "time"

// 常用时间格式常量，避免到处硬编码 "2006-01-02 15:04:05"。
const (
    DateTimeSec   = "2006-01-02 15:04:05"
    DateTimeMilli = "2006-01-02 15:04:05.000"
    DateOnly      = "2006-01-02"
    TimeOnly      = "15:04:05"
    ISO8601       = "2006-01-02T15:04:05Z07:00"
    RFC3339Milli  = "2006-01-02T15:04:05.000Z07:00"
)

// FormatDateTime 格式化为 "2006-01-02 15:04:05"。
func FormatDateTime(t time.Time) string {
    return t.Format(DateTimeSec)
}

// FormatDate 格式化为 "2006-01-02"。
func FormatDate(t time.Time) string {
    return t.Format(DateOnly)
}

// ParseDateTime 解析 "2006-01-02 15:04:05" 格式。
func ParseDateTime(s string) (time.Time, error) {
    return time.ParseInLocation(DateTimeSec, s, time.Local)
}

// ParseDate 解析 "2006-01-02" 格式。
func ParseDate(s string) (time.Time, error) {
    return time.ParseInLocation(DateOnly, s, time.Local)
}

// StartOfDay 返回当天的 00:00:00。
func StartOfDay(t time.Time) time.Time {
    y, m, d := t.Date()
    return time.Date(y, m, d, 0, 0, 0, 0, t.Location())
}

// EndOfDay 返回当天的 23:59:59.999。
func EndOfDay(t time.Time) time.Time {
    y, m, d := t.Date()
    return time.Date(y, m, d, 23, 59, 59, 999999999, t.Location())
}

// StartOfWeek 返回当周周一的 00:00:00。
func StartOfWeek(t time.Time) time.Time {
    t = StartOfDay(t)
    weekday := int(t.Weekday())
    if weekday == 0 {
        weekday = 7 // 周日归到上一周
    }
    return t.AddDate(0, 0, -(weekday - 1))
}

// StartOfMonth 返回当月第一天的 00:00:00。
func StartOfMonth(t time.Time) time.Time {
    y, m, _ := t.Date()
    return time.Date(y, m, 1, 0, 0, 0, 0, t.Location())
}

// EndOfMonth 返回当月最后一天的 23:59:59.999。
func EndOfMonth(t time.Time) time.Time {
    return StartOfMonth(t).AddDate(0, 1, 0).Add(-time.Nanosecond)
}

// TimestampMilli 返回毫秒级时间戳。
func TimestampMilli(t time.Time) int64 {
    return t.UnixMilli()
}

// FromTimestampMilli 从毫秒级时间戳创建 time.Time。
func FromTimestampMilli(ms int64) time.Time {
    return time.UnixMilli(ms)
}
```

---

### 6. 泛型切片/Map 转换工具

**问题**: Map/Filter/Unique/GroupBy 等函数式操作在业务代码中反复手写循环。

**封装方案**:

```go
package slicex

import "cmp"

// Map 将切片每个元素通过 fn 转换为新类型，返回新切片。
func Map[T any, R any](slice []T, fn func(T) R) []R {
    result := make([]R, len(slice))
    for i, v := range slice {
        result[i] = fn(v)
    }
    return result
}

// Filter 过滤切片，保留 fn 返回 true 的元素。
func Filter[T any](slice []T, fn func(T) bool) []T {
    result := make([]T, 0, len(slice))
    for _, v := range slice {
        if fn(v) {
            result = append(result, v)
        }
    }
    return result
}

// Unique 对可比较类型切片去重，保持原始顺序。
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

// UniqueBy 按键值去重，保持原始顺序。
func UniqueBy[T any, K comparable](slice []T, keyFn func(T) K) []T {
    seen := make(map[K]struct{}, len(slice))
    result := make([]T, 0, len(slice))
    for _, v := range slice {
        k := keyFn(v)
        if _, ok := seen[k]; !ok {
            seen[k] = struct{}{}
            result = append(result, v)
        }
    }
    return result
}

// GroupBy 按键值分组。
func GroupBy[T any, K comparable](slice []T, keyFn func(T) K) map[K][]T {
    result := make(map[K][]T)
    for _, v := range slice {
        k := keyFn(v)
        result[k] = append(result[k], v)
    }
    return result
}

// Chunk 将切片分割为指定大小的子切片。
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

// Contains 判断切片是否包含指定元素。
func Contains[T comparable](slice []T, target T) bool {
    for _, v := range slice {
        if v == target {
            return true
        }
    }
    return false
}

// ContainsBy 按条件判断切片是否包含匹配元素。
func ContainsBy[T any](slice []T, fn func(T) bool) bool {
    for _, v := range slice {
        if fn(v) {
            return true
        }
    }
    return false
}

// Find 查找第一个匹配元素，返回元素和是否找到。
func Find[T any](slice []T, fn func(T) bool) (T, bool) {
    for _, v := range slice {
        if fn(v) {
            return v, true
        }
    }
    var zero T
    return zero, false
}

// Flatten 展平二维切片为一维。
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

// Reverse 反转切片（原地修改）。
func Reverse[T any](slice []T) {
    for i, j := 0, len(slice)-1; i < j; i, j = i+1, j-1 {
        slice[i], slice[j] = slice[j], slice[i]
    }
}

// Min 返回最小值，切片为空时返回零值和 false。
func Min[T cmp.Ordered](slice []T) (T, bool) {
    if len(slice) == 0 {
        var zero T
        return zero, false
    }
    m := slice[0]
    for _, v := range slice[1:] {
        if v < m {
            m = v
        }
    }
    return m, true
}

// Max 返回最大值，切片为空时返回零值和 false。
func Max[T cmp.Ordered](slice []T) (T, bool) {
    if len(slice) == 0 {
        var zero T
        return zero, false
    }
    m := slice[0]
    for _, v := range slice[1:] {
        if v > m {
            m = v
        }
    }
    return m, true
}

// Reduce 将切片归约为单个值。
func Reduce[T any, R any](slice []T, initial R, fn func(R, T) R) R {
    result := initial
    for _, v := range slice {
        result = fn(result, v)
    }
    return result
}
```

---

### 7. Map 工具封装

**问题**: 从 map 中取值、转换 key/value、合并 map 等操作重复编写。

**封装方案**:

```go
package mapx

// Keys 返回 map 的所有 key。
func Keys[K comparable, V any](m map[K]V) []K {
    keys := make([]K, 0, len(m))
    for k := range m {
        keys = append(keys, k)
    }
    return keys
}

// Values 返回 map 的所有 value。
func Values[K comparable, V any](m map[K]V) []V {
    values := make([]V, 0, len(m))
    for _, v := range m {
        values = append(values, v)
    }
    return values
}

// Merge 合并多个 map，后面的覆盖前面的同名 key。
func Merge[K comparable, V any](maps ...map[K]V) map[K]V {
    result := make(map[K]V)
    for _, m := range maps {
        for k, v := range m {
            result[k] = v
        }
    }
    return result
}

// Invert 交换 key 和 value（值必须唯一，否则会丢失）。
func Invert[K comparable, V comparable](m map[K]V) map[V]K {
    result := make(map[V]K, len(m))
    for k, v := range m {
        result[v] = k
    }
    return result
}

// MapKeys 对 map 的 key 进行转换。
func MapKeys[K1 comparable, K2 comparable, V any](m map[K1]V, fn func(K1) K2) map[K2]V {
    result := make(map[K2]V, len(m))
    for k, v := range m {
        result[fn(k)] = v
    }
    return result
}

// MapValues 对 map 的 value 进行转换。
func MapValues[K comparable, V1 any, V2 any](m map[K]V1, fn func(V1) V2) map[K]V2 {
    result := make(map[K]V2, len(m))
    for k, v := range m {
        result[k] = fn(v)
    }
    return result
}

// Filter 过滤 map 中满足条件的键值对。
func Filter[K comparable, V any](m map[K]V, fn func(K, V) bool) map[K]V {
    result := make(map[K]V)
    for k, v := range m {
        if fn(k, v) {
            result[k] = v
        }
    }
    return result
}
```

---

### 8. 分页工具封装

**问题**: 分页参数计算和响应构造在各 API 中重复出现。

**封装方案**:

```go
package pagex

// Params 分页请求参数。
type Params struct {
    Page     int // 当前页码，从 1 开始
    PageSize int // 每页条数
}

// Offset 计算数据库偏移量。
func (p Params) Offset() int {
    if p.Page <= 0 {
        return 0
    }
    return (p.Page - 1) * p.Limit()
}

// Limit 返回安全的每页条数（默认 20，最大 100）。
func (p Params) Limit() int {
    if p.PageSize <= 0 {
        return 20
    }
    if p.PageSize > 100 {
        return 100
    }
    return p.PageSize
}

// Result 分页响应结果。
type Result[T any] struct {
    Items    []T   `json:"items"`
    Total    int64 `json:"total"`
    Page     int   `json:"page"`
    PageSize int   `json:"pageSize"`
    Pages    int   `json:"pages"` // 总页数
}

// NewResult 构造分页结果。
func NewResult[T any](items []T, total int64, p Params) Result[T] {
    limit := p.Limit()
    pages := int(total) / limit
    if int(total)%limit > 0 {
        pages++
    }
    return Result[T]{
        Items:    items,
        Total:    total,
        Page:     p.Page,
        PageSize: limit,
        Pages:    pages,
    }
}
```

**使用示例**:
```go
// handler 中
p := pagex.Params{Page: page, PageSize: size}
users, total := db.FindUsers(p.Offset(), p.Limit())
return pagex.NewResult(users, total, p)
```

---

### 9. Retry 重试工具封装

**问题**: 外部调用失败后的重试逻辑散落各处，退避策略不统一。

**封装方案**:

```go
package retryx

import (
    "context"
    "fmt"
    "math"
    "time"
)

// Config 重试配置。
type Config struct {
    MaxAttempts int           // 最大尝试次数（含首次），默认 3
    InitialWait time.Duration // 首次重试等待时间，默认 1s
    MaxWait     time.Duration // 最大等待时间，默认 30s
    Multiplier  float64       // 退避倍数，默认 2.0
}

// DefaultConfig 返回默认配置。
func DefaultConfig() Config {
    return Config{
        MaxAttempts: 3,
        InitialWait: time.Second,
        MaxWait:     30 * time.Second,
        Multiplier:  2.0,
    }
}

// Do 执行带指数退避的重试。
// fn 返回 nil 表示成功，返回 error 表示需要重试。
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

        // 指数退避
        wait = time.Duration(math.Min(
            float64(wait)*cfg.Multiplier,
            float64(cfg.MaxWait),
        ))
    }

    return fmt.Errorf("after %d attempts, last error: %w", cfg.MaxAttempts, lastErr)
}
```

**使用示例**:
```go
err := retryx.Do(ctx, retryx.Config{
    MaxAttempts: 5,
    InitialWait: 500 * time.Millisecond,
}, func() error {
    return callExternalAPI()
})
```

---

### 10. 类型转换工具封装

**问题**: `interface{}` / `any` 到具体类型的断言代码冗长且容易 panic。

**封装方案**:

```go
package convx

import (
    "fmt"
    "strconv"
)

// ToInt64 安全地将 any 转换为 int64。
func ToInt64(v any) (int64, error) {
    switch n := v.(type) {
    case int:
        return int64(n), nil
    case int8:
        return int64(n), nil
    case int16:
        return int64(n), nil
    case int32:
        return int64(n), nil
    case int64:
        return n, nil
    case uint:
        return int64(n), nil
    case float64:
        return int64(n), nil
    case string:
        return strconv.ParseInt(n, 10, 64)
    default:
        return 0, fmt.Errorf("cannot convert %T to int64", v)
    }
}

// ToString 安全地将 any 转换为 string。
func ToString(v any) (string, error) {
    switch s := v.(type) {
    case string:
        return s, nil
    case []byte:
        return string(s), nil
    case fmt.Stringer:
        return s.String(), nil
    case int, int8, int16, int32, int64, uint, uint8, uint16, uint32, uint64, float32, float64, bool:
        return fmt.Sprintf("%v", s), nil
    default:
        return "", fmt.Errorf("cannot convert %T to string", v)
    }
}

// ToBool 安全地将 any 转换为 bool。
func ToBool(v any) (bool, error) {
    switch b := v.(type) {
    case bool:
        return b, nil
    case string:
        return strconv.ParseBool(b)
    case int:
        return b != 0, nil
    default:
        return false, fmt.Errorf("cannot convert %T to bool", v)
    }
}
```

---

### 11. 业务错误码封装

**问题**: 各 API 错误响应格式不统一，错误码散落各处，难以国际化。

**封装方案**:

```go
package errx

import (
    "fmt"
    "net/http"
)

// Code 业务错误码类型。
type Code int

// Error 标准化业务错误，包含错误码、HTTP 状态码和原因。
type Error struct {
    Code     Code   `json:"code"`
    Message  string `json:"message"`
    HTTPCode int    `json:"-"`
    cause    error
}

// New 创建业务错误。
func New(code Code, message string, httpCode int) *Error {
    return &Error{Code: code, Message: message, HTTPCode: httpCode}
}

// WithCause 添加原因错误，保留错误链。
func (e *Error) WithCause(cause error) *Error {
    return &Error{
        Code:     e.Code,
        Message:  e.Message,
        HTTPCode: e.HTTPCode,
        cause:    cause,
    }
}

// Error 实现 error 接口。
func (e *Error) Error() string {
    if e.cause != nil {
        return fmt.Sprintf("[%d] %s: %v", e.Code, e.Message, e.cause)
    }
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}

// Unwrap 支持 errors.Is/As。
func (e *Error) Unwrap() error {
    return e.cause
}

// Respond 生成标准化的 HTTP 错误响应。
func (e *Error) Respond(w http.ResponseWriter) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(e.HTTPCode)
    json.NewEncoder(w).Encode(map[string]any{
        "code":    e.Code,
        "message": e.Message,
    })
}

// 常用错误码预定义，项目可扩展。
const (
    ErrInvalidParam Code = 10001
    ErrUnauthorized Code = 10002
    ErrNotFound     Code = 10003
    ErrConflict     Code = 10004
    ErrInternal     Code = 10005
)

// 预定义错误实例。
var (
    ErrInvalidParamE = New(ErrInvalidParam, "参数无效", http.StatusBadRequest)
    ErrUnauthorizedE = New(ErrUnauthorized, "未授权", http.StatusUnauthorized)
    ErrNotFoundE     = New(ErrNotFound, "资源不存在", http.StatusNotFound)
    ErrConflictE     = New(ErrConflict, "资源冲突", http.StatusConflict)
    ErrInternalE     = New(ErrInternal, "内部错误", http.StatusInternalServerError)
)
```

**使用示例**:
```go
// 基本使用
return errx.ErrNotFoundE.WithCause(fmt.Errorf("user %s not found", id))

// 在 handler 中
if err != nil {
    var appErr *errx.Error
    if errors.As(err, &appErr) {
        appErr.Respond(w)
        return
    }
    errx.ErrInternalE.Respond(w)
}
```

---

### 12. 参数验证器封装

**问题**: 参数校验散落在各 handler 中，if-else 堆叠难以维护。

**封装方案**:

```go
package validx

import (
    "fmt"
    "net/mail"
    "regexp"
    "strings"
    "unicode"
)

// Validator 参数验证器，收集所有错误。
type Validator struct {
    errs []error
}

// New 创建验证器。
func New() *Validator {
    return &Validator{}
}

// NotBlank 校验字符串非空。
func (v *Validator) NotBlank(field, value string) *Validator {
    if strings.TrimSpace(value) == "" {
        v.errs = append(v.errs, fmt.Errorf("%s 不能为空", field))
    }
    return v
}

// MinLen 校验最小长度。
func (v *Validator) MinLen(field, value string, min int) *Validator {
    if len([]rune(value)) < min {
        v.errs = append(v.errs, fmt.Errorf("%s 长度不能小于 %d", field, min))
    }
    return v
}

// MaxLen 校验最大长度。
func (v *Validator) MaxLen(field, value string, max int) *Validator {
    if len([]rune(value)) > max {
        v.errs = append(v.errs, fmt.Errorf("%s 长度不能超过 %d", field, max))
    }
    return v
}

// InRange 校验整数范围。
func (v *Validator) InRange(field string, value, min, max int) *Validator {
    if value < min || value > max {
        v.errs = append(v.errs, fmt.Errorf("%s 必须在 %d~%d 之间", field, min, max))
    }
    return v
}

// Email 校验邮箱格式。
func (v *Validator) Email(field, value string) *Validator {
    if _, err := mail.ParseAddress(value); err != nil {
        v.errs = append(v.errs, fmt.Errorf("%s 邮箱格式无效", field))
    }
    return v
}

// Mobile 校验手机号（中国大陆）。
func (v *Validator) Mobile(field, value string) *Validator {
    matched, _ := regexp.MatchString(`^1[3-9]\d{9}$`, value)
    if !matched {
        v.errs = append(v.errs, fmt.Errorf("%s 手机号格式无效", field))
    }
    return v
}

// Alphanumeric 校验仅含字母和数字。
func (v *Validator) Alphanumeric(field, value string) *Validator {
    for _, r := range value {
        if !unicode.IsLetter(r) && !unicode.IsDigit(r) {
            v.errs = append(v.errs, fmt.Errorf("%s 只能包含字母和数字", field))
            break
        }
    }
    return v
}

// Custom 自定义校验规则。
func (v *Validator) Custom(field string, ok bool, msg string) *Validator {
    if !ok {
        v.errs = append(v.errs, fmt.Errorf("%s %s", field, msg))
    }
    return v
}

// Valid 返回验证结果，nil 表示全部通过。
func (v *Validator) Valid() error {
    if len(v.errs) == 0 {
        return nil
    }
    return fmt.Errorf("参数校验失败: %v", v.errs)
}
```

**使用示例**:
```go
err := validx.New().
    NotBlank("用户名", req.Username).
    MinLen("密码", req.Password, 8).
    Email("邮箱", req.Email).
    Mobile("手机号", req.Mobile).
    Custom("年龄", req.Age >= 18, "必须年满18岁").
    Valid()
if err != nil {
    return err
}
```

---

### 13. ID 生成器封装

**问题**: UUID 生成、雪花 ID 等分散实现，ID 格式不统一。

**封装方案**:

```go
package idx

import (
    "crypto/rand"
    "fmt"
    "sync"
    "sync/atomic"
    "time"
)

// UUID 生成 v4 随机 UUID，仅使用标准库。
func UUID() string {
    var buf [16]byte
    if _, err := rand.Read(buf[:]); err != nil {
        // crypto/rand.Read 极少失败，这里做 fallback
        panic(fmt.Sprintf("crypto/rand.Read: %v", err))
    }
    buf[6] = (buf[6] & 0x0f) | 0x40 // version 4
    buf[8] = (buf[8] & 0x3f) | 0x80 // variant 10
    return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x",
        buf[0:4], buf[4:6], buf[6:8], buf[8:10], buf[10:16])
}

// UUIDNoDash 生成无连字符的 UUID。
func UUIDNoDash() string {
    return strings.ReplaceAll(UUID(), "-", "")
}

// Snowflake 雪花 ID 生成器。
type Snowflake struct {
    mu        sync.Mutex
    epoch     int64 // 起始时间戳（毫秒）
    nodeID    int64 // 节点 ID（0~1023）
    sequence  int64 // 序列号
    lastStamp int64 // 上次时间戳
}

// NewSnowflake 创建雪花 ID 生成器。
// epoch 为自定义纪元（毫秒），nodeID 为节点编号（0~1023）。
func NewSnowflake(epoch time.Time, nodeID int64) *Snowflake {
    return &Snowflake{
        epoch:  epoch.UnixMilli(),
        nodeID: nodeID & 0x3FF, // 10 位
    }
}

// Next 生成下一个雪花 ID。
func (s *Snowflake) Next() int64 {
    s.mu.Lock()
    defer s.mu.Unlock()

    now := time.Now().UnixMilli() - s.epoch
    if now == s.lastStamp {
        s.sequence = (s.sequence + 1) & 0xFFF // 12 位
        if s.sequence == 0 {
            for now <= s.lastStamp {
                now = time.Now().UnixMilli() - s.epoch
            }
        }
    } else {
        s.sequence = 0
    }
    s.lastStamp = now

    return (now << 22) | (s.nodeID << 12) | s.sequence
}

// ShortID 生成 8 字符短 ID，基于时间戳+随机数。
func ShortID() string {
    var buf [4]byte
    if _, err := rand.Read(buf[:]); err != nil {
        panic(fmt.Sprintf("crypto/rand.Read: %v", err))
    }
    ts := time.Now().UnixMilli() & 0xFFFFFFFF
    return fmt.Sprintf("%08x%08x", ts, buf)
}
```

**使用示例**:
```go
// UUID
id := idx.UUID() // "550e8400-e29b-41d4-a716-446655440000"

// 雪花 ID
sf := idx.NewSnowflake(time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC), 1)
sid := sf.Next() // 1789234567890123456

// 短 ID
short := idx.ShortID() // "18f3a2bc7d9e1f0a"
```

---

### 14. 并发安全缓存封装

**问题**: 带过期时间的内存缓存需要重复实现，map + mutex + timer 管理繁琐。

**封装方案**:

```go
package cachex

import (
    "sync"
    "time"
)

// item 缓存项。
type item[V any] struct {
    value     V
    expiredAt time.Time
}

// Cache 泛型并发安全缓存，支持过期时间。
type Cache[K comparable, V any] struct {
    mu    sync.RWMutex
    data  map[K]item[V]
}

// New 创建缓存。
func New[K comparable, V any]() *Cache[K, V] {
    c := &Cache[K, V]{
        data: make(map[K]item[V]),
    }
    return c
}

// Set 存入缓存，ttl 为存活时间，0 表示永不过期。
func (c *Cache[K, V]) Set(key K, value V, ttl time.Duration) {
    c.mu.Lock()
    defer c.mu.Unlock()
    var expiredAt time.Time
    if ttl > 0 {
        expiredAt = time.Now().Add(ttl)
    }
    c.data[key] = item[V]{value: value, expiredAt: expiredAt}
}

// Get 取出缓存，第二个返回值表示是否存在且未过期。
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

// Delete 删除缓存项。
func (c *Cache[K, V]) Delete(key K) {
    c.mu.Lock()
    defer c.mu.Unlock()
    delete(c.data, key)
}

// Clean 清理所有过期项。
func (c *Cache[K, V]) Clean() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    now := time.Now()
    cleaned := 0
    for k, v := range c.data {
        if !v.expiredAt.IsZero() && now.After(v.expiredAt) {
            delete(c.data, k)
            cleaned++
        }
    }
    return cleaned
}

// Len 返回缓存项数量（含可能已过期但未清理的项）。
func (c *Cache[K, V]) Len() int {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return len(c.data)
}
```

**使用示例**:
```go
cache := cachex.New[string, User]()
cache.Set("user:123", user, 5*time.Minute)

if u, ok := cache.Get("user:123"); ok {
    fmt.Println(u.Name)
}
```

---

### 15. 上下文值工具封装

**问题**: `context.WithValue` 使用裸字符串/数字作为 key，易冲突且不类型安全。

**封装方案**:

```go
package ctxx

import "context"

// Key 类型安全的 context key，避免 string key 冲突。
// 不同包定义的 Key 类型天然隔离，即使名字相同也不会冲突。
type Key[T any] struct {
    name string
}

// NewKey 创建类型安全的 context key。
func NewKey[T any](name string) Key[T] {
    return Key[T]{name: name}
}

// WithValue 向 context 中存入类型安全的值。
func WithValue[T any](ctx context.Context, key Key[T], value T) context.Context {
    return context.WithValue(ctx, key, value)
}

// Value 从 context 中取出类型安全的值，第二个返回值表示是否存在。
func Value[T any](ctx context.Context, key Key[T]) (T, bool) {
    v := ctx.Value(key)
    if v == nil {
        var zero T
        return zero, false
    }
    typed, ok := v.(T)
    return typed, ok
}

// MustValue 从 context 中取出值，不存在则 panic（仅用于中间件已确保注入的场景）。
func MustValue[T any](ctx context.Context, key Key[T]) T {
    v, ok := Value(ctx, key)
    if !ok {
        panic("ctxx: required value not found in context")
    }
    return v
}
```

**使用示例**:
```go
// 定义 key（包级别，类型安全）
var requestIDKey = ctxx.NewKey[string]("request-id")
var userIDKey = ctxx.NewKey[int64]("user-id")

// 中间件注入
ctx = ctxx.WithValue(ctx, requestIDKey, "abc-123")
ctx = ctxx.WithValue(ctx, userIDKey, 42)

// 业务代码取值
reqID, ok := ctxx.Value(ctx, requestIDKey)  // string, bool
uid := ctxx.MustValue(ctx, userIDKey)        // int64
```

---

### 16. 文件操作工具封装

**问题**: 读写 JSON/YAML 文件、安全创建目录等操作重复编写，且容易忘记关闭文件和检查错误。

**封装方案**:

```go
package filex

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
)

// ReadJSON 从 JSON 文件读取并解码到 v。
func ReadJSON(path string, v any) error {
    data, err := os.ReadFile(path)
    if err != nil {
        return fmt.Errorf("read file %s: %w", path, err)
    }
    if err := json.Unmarshal(data, v); err != nil {
        return fmt.Errorf("unmarshal %s: %w", path, err)
    }
    return nil
}

// WriteJSON 将 v 编码为 JSON 并写入文件，自动创建目录。
func WriteJSON(path string, v any, perm os.FileMode) error {
    if err := ensureDir(path); err != nil {
        return err
    }
    data, err := json.MarshalIndent(v, "", "  ")
    if err != nil {
        return fmt.Errorf("marshal for %s: %w", path, err)
    }
    if err := os.WriteFile(path, data, perm); err != nil {
        return fmt.Errorf("write file %s: %w", path, err)
    }
    return nil
}

// ReadFile 读取文件全部内容。
func ReadFile(path string) ([]byte, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("read file %s: %w", path, err)
    }
    return data, nil
}

// WriteFile 写入文件，自动创建目录。
func WriteFile(path string, data []byte, perm os.FileMode) error {
    if err := ensureDir(path); err != nil {
        return err
    }
    if err := os.WriteFile(path, data, perm); err != nil {
        return fmt.Errorf("write file %s: %w", path, err)
    }
    return nil
}

// Exists 判断文件或目录是否存在。
func Exists(path string) bool {
    _, err := os.Stat(path)
    return err == nil
}

// Touch 创建空文件，如已存在则更新修改时间。
func Touch(path string) error {
    if err := ensureDir(path); err != nil {
        return err
    }
    f, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        return fmt.Errorf("touch %s: %w", path, err)
    }
    return f.Close()
}

// ensureDir 确保文件所在目录存在。
func ensureDir(path string) error {
    dir := filepath.Dir(path)
    if dir != "" && dir != "." {
        if err := os.MkdirAll(dir, 0755); err != nil {
            return fmt.Errorf("create directory %s: %w", dir, err)
        }
    }
    return nil
}
```

**使用示例**:
```go
// 读取配置
var cfg Config
if err := filex.ReadJSON("config.json", &cfg); err != nil {
    return err
}

// 写入数据
if err := filex.WriteJSON("output/result.json", data, 0644); err != nil {
    return err
}

// 检查文件存在
if !filex.Exists("data/cache.json") {
    // 首次初始化
}
```

1. **识别重复逻辑**
   - 搜索项目中相同模式的代码片段
   - 统计重复出现次数 >= 2 的模式
   - 评估封装收益（减少代码量、提升一致性、降低出错率）

2. **选择封装方案**
   - 优先使用 Go 1.21+ 泛型（`cmp.Ordered`、类型约束）
   - 参数接受标准接口（`io.Reader`、`context.Context`）
   - 返回 error 而非 panic
   - 零值可用设计

3. **实现封装**
   - 仅使用标准库，零外部依赖
   - 完整的 godoc 注释
   - 为每个公开函数编写 table-driven 测试

4. **验证封装**
   - 运行 `go vet ./...`
   - 运行 `go test -race ./...`
   - 确认原有代码可正确替换为新封装

---

## 快速参考：封装决策树

```
发现重复代码
  ├── 出现 >= 2 次？
  │   ├── 否 → 不封装，保持内联
  │   └── 是 → 逻辑是否稳定？
  │       ├── 否 → 考虑配置化而非封装
  │       └── 是 → 是否可用泛型统一？
  │           ├── 是 → 泛型封装（slicex.Map 等）
  │           └── 否 → 具体类型封装（signx.Signer 等）
  └── 涉及外部资源（HTTP、DB）？
      └── 是 → 封装为带接口的结构体，便于 Mock 测试
```

---

## 命名约定

| 包名 | 职责 | 示例 |
|------|------|------|
| `httpx` | HTTP 客户端封装 | `httpx.Get[T]()`, `httpx.Post[T]()` |
| `signx` | 签名工具 | `signx.NewHMACSHA256Signer()`, `signer.Sign()` |
| `cryptox` | 加密/哈希 | `cryptox.SHA256()`, `cryptox.AESEncrypt()` |
| `slicex` | 切片操作 | `slicex.Map()`, `slicex.Filter()`, `slicex.Unique()` |
| `mapx` | Map 操作 | `mapx.Keys()`, `mapx.Merge()`, `mapx.GroupBy()` |
| `timex` | 时间工具 | `timex.FormatDateTime()`, `timex.StartOfDay()` |
| `pagex` | 分页工具 | `pagex.NewResult[T]()` |
| `retryx` | 重试工具 | `retryx.Do()` |
| `convx` | 类型转换 | `convx.ToInt64()`, `convx.ToString()` |
| `strx` | 字符串工具 | 详见 reference/strings_util.md |
| `jsonx` | JSON 工具 | 详见 reference/json_util.md |
| `errx` | 业务错误码 | `errx.New()`, `errx.WithCause()`, `errx.FromHTTP()` |
| `validx` | 参数验证器 | `validx.NotBlank()`, `validx.InRange()`, `validx.Email()` |
| `idx` | ID 生成器 | `idx.UUID()`, `idx.SnowflakeID()`, `idx.ShortID()` |
| `cachex` | 并发安全缓存 | `cachex.New()`, `cachex.Get()`, `cachex.Set()` |
| `ctxx` | 上下文值工具 | `ctxx.WithValue()`, `ctxx.Value()` |
| `filex` | 文件操作工具 | `filex.ReadJSON()`, `filex.WriteJSON()`, `filex.Touch()` |
