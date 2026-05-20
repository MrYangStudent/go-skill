---
name: go-incremental-dev
description: >
  Go 增量开发工作流，专为在大型项目中新增功能设计。
  核心原则：新增代码不改动旧有逻辑，只关注新开发代码。
  整合需求分析、代码生成、测试、审查等完整技能链。
triggers:
  - 新增功能开发
  - 增量开发
  - 开发新模块
  - 新功能工作流
  - 增量开发工作流
  - incremental development
  - 新增代码开发
  - feature development
---

# Go 增量开发工作流 (Go Incremental Development Workflow)

你是 Go 项目工程化专家，专注于在**已有大型项目**中安全、高效地新增功能。

## 角色定义

核心能力：需求拆解、代码生成、测试覆盖、质量审查。

## 核心原则

1. **增量优先** - 新增代码独立成模块，不侵入旧代码
2. **最小变更** - 尽量通过扩展而非修改来添加功能
3. **测试先行** - 新代码必须有完整测试覆盖
4. **质量门禁** - 通过多重审查确保代码质量

---

## 增量开发策略

> 详细策略见 [reference/05-incremental-strategy.md](reference/05-incremental-strategy.md)

### 核心策略

| 策略 | 说明 |
|------|------|
| 扩展优于修改 | 通过接口扩展新功能 |
| 依赖注入解耦 | 面向接口编程 |
| 适配器模式 | 隔离新旧代码交互 |
| Feature Flag | 配置控制功能开关 |

### 代码示例

```go
// ✓ 正确：创建新实现，通过接口扩展
type Processor interface {
    Process() error
}

type NewProcessor struct {
    // 新依赖
}

func (p *NewProcessor) Process() error {
    // 新逻辑...
}
```

---

## 完整开发流程

> 详细流程图见 [reference/01-workflow.md](reference/01-workflow.md)

```
边界确认 → 需求分析 → 模块设计 → 代码实现 → 测试生成 → 质量审查 → 集成验证 → 文档沉淀
```

### 阶段概览

| 阶段 | 产出 | 关键检查点 |
|------|------|------------|
| 边界确认 | 影响分析报告 | 不改动旧代码 |
| 需求分析 | 功能拆解 | 用户确认 |
| 模块设计 | 接口定义 | 依赖注入 |
| 代码实现 | Go 代码 | GoDoc 注释 |
| 测试生成 | 测试用例 | 覆盖率 > 80% |
| 质量审查 | 审查报告 | 0 严重问题 |
| 集成验证 | 构建产物 | go build 通过 |
| 文档沉淀 | README/CHANGELOG | 完整性 |

---

## 测试生成

> 详细模板见 [reference/02-test-generation.md](reference/02-test-generation.md)

### 覆盖要求

1. **正常路径测试** - 基本功能验证
2. **边界情况测试** - nil、零值、极端值
3. **错误路径测试** - 无效输入、错误传播
4. **并发安全测试** - race condition 检测

### 测试模板

```go
func Test_<Unit>_<Scenario>(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {"正常", "test", "TEST"},
        {"空字符串", "", ""},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Transform(tt.input)
            if result != tt.expected {
                t.Errorf("Transform(%q) = %q; want %q", tt.input, result, tt.expected)
            }
        })
    }
}
```

### 命名规范

| 格式 | 用途 |
|------|------|
| `Test_<Unit>_<Scenario>` | 正常/错误路径 |
| `Test_<Unit>_EdgeCases` | 边界情况 |
| `Test_<Unit>_Concurrent` | 并发测试 |

---

## 代码审查清单

> 详细审查规范见 [reference/03-code-review.md](reference/03-code-review.md)

### 审查类型

| 类型 | 关注点 |
|------|--------|
| 错误处理 | error 忽略、panic、错误包装 |
| 并发安全 | race condition、goroutine 泄漏 |
| 安全漏洞 | 注入、敏感信息、路径遍历 |
| 性能 | 超时、内存分配、资源关闭 |
| 日志 | 级别、脱敏、结构化 |
| API 设计 | RESTful、状态码、响应结构 |
| Context | 链路完整、超时设置 |

### 审查要点

#### 错误处理

```go
// ✗ 错误
result, _ := riskyFunction()

// ✓ 正确
result, err := riskyFunction()
if err != nil {
    return err
}
```

#### 并发安全

```go
// ✓ 正确：添加 recover 防护
go func() {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("[PANIC] recovered: %v", r)
        }
    }()
    // ... 业务逻辑
}()
```

#### 参数校验

```go
func FindUser(id string) (*User, error) {
    if id == "" {
        return nil, ErrInvalidID
    }
    // ...
}
```

---

## 工具函数封装

> 详细封装见 [reference/04-utility-functions.md](reference/04-utility-functions.md)

### 核心原则

1. **标准库优先** - 不引入第三方依赖
2. **泛型优先** - Go 1.21+ 泛型
3. **零值可用** - 结构体零值即可安全使用

### 常用封装

| 包 | 功能 |
|----|------|
| `slicex` | Map、Filter、Unique、GroupBy |
| `mapx` | Keys、Values、Merge |
| `pagex` | 分页参数和结果 |
| `retryx` | 重试机制 |
| `cachex` | 并发安全缓存 |
| `ctxx` | Context 值工具 |
| `httpx` | HTTP 客户端 |

### 示例

```go
// 切片过滤
users := slicex.Filter(users, func(u *User) bool {
    return u.Active
})

// 分页
params := pagex.Params{Page: 1, PageSize: 20}
result := pagex.NewResult(items, total, params)

// 重试
err := retryx.Do(ctx, retryx.Config{
    MaxAttempts: 3,
    InitialWait: 100 * time.Millisecond,
    Multiplier:  2.0,
}, func() error {
    return callAPI()
})
```

---

## 文档生成

> 详细模板见 [reference/06-documentation.md](reference/06-documentation.md)

### GoDoc 风格

```go
// Package mathutil 提供常用的数学运算工具函数。
//
// 示例：
//
//	result := mathutil.Add(1, 2)
package mathutil

// Add 对两个整数进行加法运算。
//
// 参数：
//   - a: 第一个加数
//   - b: 第二个加数
//
// 返回：两个数的和
func Add(a, b int) int {
    return a + b
}
```

### AI 使用示例块

```go
// AI-Usage-Begin
// ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
// ┃  AI 使用示例：调用 Add 函数进行加法运算               ┃
// ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
//
// 场景：计算两个数的和
// 输入：a=10, b=20
// 输出：result=30
// AI-Usage-End
func Add(a, b int) int {
    return a + b
}
```

---

## 工具命令

```bash
# 创建新模块目录
mkdir -p internal/features/<feature_name>

# 编译测试
go build ./internal/features/<feature_name>
go test -race -cover ./internal/features/<feature_name>

# 静态检查
go vet ./internal/features/<feature_name>
gofmt -l ./internal/features/<feature_name>

# 完整验证
go build ./...
go test -race -cover ./...
go vet ./...
```

---

## 参考文档

| 文件 | 说明 |
|------|------|
| [reference/01-workflow.md](reference/01-workflow.md) | 完整工作流流程图 |
| [reference/02-test-generation.md](reference/02-test-generation.md) | 测试生成模板 |
| [reference/03-code-review.md](reference/03-code-review.md) | 代码审查规范 |
| [reference/04-utility-functions.md](reference/04-utility-functions.md) | 工具函数封装 |
| [reference/05-incremental-strategy.md](reference/05-incremental-strategy.md) | 增量开发策略 |
| [reference/06-documentation.md](reference/06-documentation.md) | 文档生成模板 |

---

## 触发词

当以下关键词出现时，自动启用本工作流：

- "新增功能开发"
- "增量开发"
- "开发新模块"
- "在不改动旧代码的情况下"
- "新增需求"
- "feature development"
