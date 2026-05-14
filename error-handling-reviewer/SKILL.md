---
name: error-handling-reviewer
description: >
  Go 语言错误处理审查技能。当用户要求审查代码错误处理、检查 error 使用、
  或请求诊断 panic/忽略错误等问题时触发。专门用于发现和修复 Go 代码中
  的错误处理缺陷，遵循"错误是值"哲学。
triggers:
  - 错误处理审查
  - 检查 error
  - 审查代码
  - 错误处理审查员
  - 检查 panic
  - 检查错误包装
---

# 错误处理审查员 (Error Handling Reviewer)

## 技能定位

Go 语言错误处理专家，遵循 "errors are values" 哲学。检测代码中的错误处理问题并提供修复建议。

## 审查检查项

### 1. 被忽略的 error（使用 `_`）

**检查模式：**
```go
// ✗ 错误示例
result, _ := riskyFunction()           // 忽略 error
data, err := json.Unmarshal(input, &v); _ = err  // 明确用 _ 忽略

// ✓ 正确示例
result, err := riskyFunction()
if err != nil {
    return err  // 或处理错误
}
```

**修复建议：**
- 如果确实不需要处理，使用 `_ = err` 并添加注释说明原因
- 否则，使用 `if err != nil { return/handle }` 模式
- 对于可预见的非错误情况，使用 `errors.Is` 或 `errors.As` 检查

### 2. panic 作为错误处理

**检查模式：**
```go
// ✗ 错误示例
if value == nil {
    panic("value should not be nil")
}

func process() {
    if err != nil {
        panic(err)  // 用 panic 处理业务错误
    }
}

// ✓ 正确示例
if value == nil {
    return ErrNilValue  // 或 return fmt.Errorf("...")
}

func process() error {
    if err != nil {
        return fmt.Errorf("process failed: %w", err)
    }
}
```

**例外情况：**
- 真正的不可恢复状态（如 main 启动失败、配置文件严重错误）
- 初始化时的致命错误
- 不使用 panic 处理业务逻辑错误

### 3. 错误包装（%w）

**检查模式：**
```go
// ✗ 错误示例
return errors.New("operation failed")           // 完全丢失底层错误
return fmt.Errorf("failed: " + err.Error())     // 丢失错误链，无法 errors.Is/As
return fmt.Errorf("failed: %v", err)           // 虽然能用 %v，但丢失类型信息

// ✓ 正确示例
return fmt.Errorf("process data: %w", err)      // 保留错误链
return fmt.Errorf("parse config %s: %w", path, err)  // 添加上下文

// ✓ 使用 errors.Wrap（第三方，但常用）
return errors.Wrap(err, "failed to parse")
```

**修复建议：**
- 始终使用 `%w` 包装错误
- 在错误消息中提供上下文（如函数名、操作描述）
- 避免重复包装同一错误

### 4. 错误上下文信息

**检查模式：**
```go
// ✗ 缺少上下文
return err
return errors.New("error")

// ✓ 提供足够上下文
return fmt.Errorf("validateUser: %w", err)
return fmt.Errorf("db.Query: %w", err)

// ✓ 记录错误时包含上下文
log.Printf("handler: failed to process request: %v", err)
logger.Error("authenticate user", "error", err)
```

**修复建议：**
- 每个错误传播点都添加上下文
- 错误消息应该能回答：哪里、什么、为什么
- 使用结构化日志记录错误

### 5. 参数校验

**检查模式：**
```go
// ✗ 未校验参数
func FindUser(id string) (*User, error) {
    user, err := db.Find(id)  // id 为空时会怎样？
    // ...
}

// ✓ 参数校验
func FindUser(id string) (*User, error) {
    if id == "" {
        return nil, ErrInvalidID
    }
    user, err := db.Find(id)
    if err != nil {
        return nil, fmt.Errorf("FindUser %s: %w", id, err)
    }
    // ...
}
```

## 工作流程

1. **扫描代码**
   - 搜索 `:= ` 或 `= ` 赋值语句中的 `_`
   - 搜索 `panic(` 调用
   - 搜索 `fmt.Errorf` 和 `errors.New`
   - 搜索 `log.` 和 `logger.` 调用

2. **分析每个问题**
   - 确定问题类型
   - 评估严重程度（Error/Warning/Suggestion）
   - 检查是否有误报（如刻意忽略的可预期错误）

3. **生成报告**
   ```
   ## 错误处理审查报告
   
   ### 🔴 Error（必须修复）
   - 文件: xxx.go:123
     问题: 使用 `_` 忽略 error
     代码: `_, err := fn()`
     建议: 添加错误处理或使用 `_ = err` 并注释说明
   
   ### 🟡 Warning（建议修复）
   - 文件: xxx.go:456
     问题: 错误未包装
     代码: `return err`
     建议: `return fmt.Errorf("context: %w", err)`
   
   ### 💡 Suggestion（可选改进）
   - 文件: xxx.go:789
     问题: 缺少参数校验
     代码: `func f(id string)`
     建议: 在函数开头添加 `if id == "" { return ErrInvalidID }`
   ```

## 严重程度定义

| 级别 | 描述 | 示例 |
|------|------|------|
| 🔴 Error | 必须修复 | panic 处理业务错误、`_` 忽略关键错误 |
| 🟡 Warning | 建议修复 | 错误未包装、缺少日志 |
| 💡 Suggestion | 可选改进 | 缺少参数校验、日志格式可优化 |

## 常见模式库

### 正确示例

```go
// 1. 标准错误处理
if err != nil {
    return fmt.Errorf("operation: %w", err)
}

// 2. 带上下文的包装
return fmt.Errorf("ParseJSON payload=%s: %w", string(payload), err)

// 3. 哨兵错误定义
var (
    ErrNotFound   = errors.New("resource not found")
    ErrInvalidID  = errors.New("invalid id")
)

// 4. 使用 errors.Is/As
if errors.Is(err, os.ErrNotExist) { ... }
if errors.As(err, &mysqlErr) { ... }

// 5. 结构化日志
logger.Error("operation failed",
    "operation", "db.query",
    "error", err,
    "duration", elapsed,
)
```

### 错误示例

```go
// 1. 忽略错误
data, _ := json.Marshal(v)  // ✗

// 2. panic 代替错误
if v == nil {
    panic("nil value")  // ✗
}

// 3. 丢失错误链
return errors.New("failed")  // ✗
return fmt.Errorf("failed: " + err.Error())  // ✗

// 4. 空错误消息
return err  // ✗
return errors.New("")  // ✗
```
