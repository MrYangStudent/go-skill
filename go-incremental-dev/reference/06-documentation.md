# 文档生成规范

## 文档生成员

专门为代码生成 AI 友好的技术文档。

---

## GoDoc 风格注释

### 包级文档

```go
// Package mathutil 提供常用的数学运算工具函数。
//
// 目的：
//   - 简化日常数学运算
//   - 提供类型安全的数学函数
//
// 示例：
//
//	result := mathutil.Add(1, 2)
package mathutil
```

### 函数文档

```go
// Add 对两个整数进行加法运算。
//
// 参数：
//   - a: 第一个加数
//   - b: 第二个加数
//
// 返回：两个数的和
//
// 错误：本函数不返回错误
func Add(a, b int) int {
    return a + b
}
```

### 方法文档

```go
// Get 根据键获取缓存值。
//
// 如果键不存在或已过期，返回 (zero value, false)。
// 如果 ttl > 0，缓存将在指定时间后自动失效。
//
// 参数：
//   - key: 缓存键
//
// 返回：
//   - value: 缓存值（如果存在）
//   - ok: 键是否存在且未过期
func (c *Cache[K, V]) Get(key K) (V, bool) {
    // ...
}
```

### 错误文档

```go
// 定义错误变量（按惯例以 Err 开头）
var (
    // ErrNotFound 表示请求的资源不存在
    ErrNotFound = errors.New("not found")
    
    // ErrInvalidInput 表示输入参数无效
    ErrInvalidInput = errors.New("invalid input")
    
    // ErrTimeout 表示操作超时
    ErrTimeout = errors.New("operation timeout")
)
```

---

## AI 使用示例块

```go
// Add 对两个整数进行加法运算。
//
// AI-Usage-Begin
// ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
// ┃  AI 使用示例：调用 Add 函数进行加法运算               ┃
// ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
//
// 场景：计算两个数的和
// 输入：a=10, b=20
// 输出：result=30
//
// 常见调用模式：
//   result := mathutil.Add(10, 20)
//   total := mathutil.Add(x, y) + mathutil.Add(z, w)
//
// 边界情况：
//   - 正数相加：mathutil.Add(1, 2) → 3
//   - 负数相加：mathutil.Add(-1, -2) → -3
//   - 零值：mathutil.Add(0, 5) → 5
//
// AI-Usage-End
func Add(a, b int) int {
    return a + b
}
```

---

## README 模板

```markdown
# 模块名称

简短描述模块的功能和用途。

## 功能特性

- 特性 1
- 特性 2
- 特性 3

## 安装

```bash
go get your/module/path
```

## 快速开始

```go
package main

import (
    "context"
    "fmt"
)

func main() {
    // 示例代码
}
```

## API 参考

### NewXXX

创建一个新的 XXX 实例。

```go
func NewXXX(opts ...Option) *XXX
```

**参数**：
- `opts ...Option`: 可选配置项

**返回**：
- `*XXX`: XXX 实例

### XXX.Do

执行主要操作。

```go
func (x *XXX) Do(ctx context.Context, req *Request) (*Response, error)
```

**参数**：
- `ctx context.Context`: 上下文
- `req *Request`: 请求参数

**返回**：
- `*Response`: 响应
- `error`: 错误

## 配置选项

### WithTimeout

设置超时时间。

```go
func WithTimeout(d time.Duration) Option
```

### WithRetry

设置重试次数。

```go
func WithRetry(n int) Option
```

## 错误处理

| 错误 | 说明 |
|------|------|
| `ErrNotFound` | 资源不存在 |
| `ErrTimeout` | 操作超时 |
| `ErrInvalid` | 输入无效 |

## 示例

更多示例请参考 [examples](./examples/) 目录。
```

---

## CHANGELOG 条目模板

```markdown
## [Unreleased]

### Added
- 新功能描述

### Changed
- 功能变更描述

### Deprecated
- 废弃功能说明

### Fixed
- Bug 修复

### Security
- 安全相关更新
```

---

## 设计决策记录 (ADR)

```markdown
# ADR-001: 使用依赖注入解耦

## 状态
已接受

## 背景
原代码直接依赖具体实现，导致测试困难和模块耦合。

## 决策
使用构造函数注入依赖接口。

## 后果
- 正面：便于单元测试，支持 Mock
- 负面：增加代码复杂度
```
