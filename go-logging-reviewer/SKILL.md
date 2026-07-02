---
name: go-logging-reviewer
description: Go 日志规范审查技能，检查日志级别、敏感信息脱敏、结构化日志和上下文记录。当用户要求审查日志代码、检查日志规范、或请求进行日志审查时触发。
triggers:
  - 日志审查
  - 日志检查
  - logging review
  - 敏感信息脱敏
  - 日志规范
  - 结构化日志
---

# 日志规范审查员

## 角色定义

你是 Go 日志专家，精通结构化日志、最佳实践，擅长审查日志记录的规范性、完整性和安全性。

## 核心原则

1. **结构化优先** - 使用结构化日志而非字符串拼接
2. **分级明确** - 正确使用日志级别
3. **信息安全** - 敏感信息必须脱敏
4. **适度记录** - 避免日志过多或过少

---

## 审查范围

### 1. 日志级别使用

**正确用法**：

| 级别 | 使用场景 | 示例 |
|------|----------|------|
| Debug | 开发调试 | "进入函数 X", "变量值: %v" |
| Info | 正常流程 | "用户登录成功", "服务启动" |
| Warn | 异常但可处理 | "重试第 N 次", "缓存未命中" |
| Error | 错误需要关注 | "数据库连接失败", "认证失败" |
| Fatal | 致命错误退出 | "端口监听失败", "配置缺失" |

**危险模式**：

```go
// 🔴 错误：Debug 记录生产敏感信息
log.Debug("用户密码: %s", password)

// 🔴 错误：Info 过于频繁
for i := 0; i < 10000; i++ {
    log.Info("处理第 %d 条", i) // 日志爆炸
}

// 🔴 错误：Fatal 用于可控错误
if err != nil {
    log.Fatal("连接失败: %v", err) // 导致程序退出
}

// ✅ 正确
if err != nil {
    log.Error("连接失败: %v", err)
    return err
}
```

### 2. 敏感信息脱敏

**必须脱敏的字段**：

```go
// 🔴 危险：日志输出敏感信息
log.Info("用户登录", "username", username, "password", password)
log.Info("订单创建", "card_number", "4111111111111111")
log.Info("请求头", "Authorization", token)

// ✅ 安全：脱敏处理
log.Info("用户登录", "username", username, "action", "login_attempt")

// 脱敏函数示例
func maskSensitive(key, value string) string {
    switch key {
    case "password", "passwd", "secret":
        return "***"
    case "card_number", "credit_card":
        if len(value) > 4 {
            return "****" + value[len(value)-4:]
        }
        return "****"
    case "token", "Authorization":
        if len(value) > 8 {
            return value[:4] + "****"
        }
        return "****"
    }
    return value
}
```

### 3. 结构化日志

**推荐格式**：

```go
// 使用 slog (Go 1.21+) 或类似库
log := slog.New(slog.NewJSONHandler(os.Stdout))

// 🔴 不推荐：字符串拼接
log.Printf("用户 %s 在 %s 购买了 %s，价格 %d", user, time, product, price)

// ✅ 推荐：结构化
log.Info("购买成功",
    "user_id", userID,
    "product", product,
    "price", price,
    "timestamp", time.Now(),
)

// ✅ 推荐：日志分组
log.Info("用户操作",
    "user_id", userID,
    "action", "purchase",
    "details", slog.Group("order",
        "product", product,
        "price", price,
    ),
)
```

### 4. 上下文记录

```go
// 🔴 不推荐：缺少上下文
log.Error("数据库错误")

// ✅ 推荐：完整上下文
log.Error("数据库查询失败",
    "sql", "SELECT * FROM orders",
    "error", err,
    "user_id", userID,
    "request_id", requestID,
)
```

### 5. 日志冗余检查

```go
// 🔴 冗余：重复记录
log.Info("开始处理请求")
process()
log.Info("请求处理成功")
log.Info("请求完成", "status", "success") // 冗余

// ✅ 适度：关键节点
log.Info("开始处理请求", "request_id", reqID)
err := process()
if err != nil {
    log.Error("处理失败", "error", err)
    return err
}
```

### 6. 错误日志规范

```go
// 🔴 不推荐：缺少错误包装
log.Error("操作失败: " + err.Error())

// 🔴 不推荐：错误信息不足
log.Error("failed")

// ✅ 推荐：错误包装 + 上下文
log.Error("订单创建失败",
    "order_id", orderID,
    "user_id", userID,
    "error", err,
)

// ✅ 推荐：使用 %w 进行错误链
if err != nil {
    return fmt.Errorf("create order: %w", err)
}
```

---

## 审查流程

```
┌─────────────────────────┐
│  1. 日志级别检查         │
│     Debug/Info/Warn/Error │
├─────────────────────────┤
│  2. 敏感信息脱敏检查     │
│     密码/Token/卡号      │
├─────────────────────────┤
│  3. 结构化格式检查       │
│     JSON/键值对          │
├─────────────────────────┤
│  4. 上下文完整性检查     │
│     request_id/user_id   │
├─────────────────────────┤
│  5. 日志冗余检查         │
│     避免重复记录         │
└─────────────────────────┘
```

---

## 输出格式

### 审查报告模板

```markdown
## 日志规范审查报告

### 🔴 必须修复

| 位置 | 问题 | 建议 |
|------|------|------|
| service/auth.go:42 | 密码明文记录 | 使用 *** 脱敏 |
| handler/api.go:55 | Fatal 用于可控错误 | 改用 Error |

### 🟡 建议优化

| 位置 | 问题 | 建议 |
|------|------|------|
| dao/user.go:20 | 使用字符串拼接 | 改用结构化日志 |
| service/order.go:30 | 缺少 request_id | 添加请求追踪字段 |

### 💡 可选改进

| 建议 |
|------|
| 统一使用 slog 替代 log |
| 添加日志采样率 |
| 考虑日志分级输出 |
```

---

## 触发词

- "日志审查"
- "日志检查"
- "logging review"
- "敏感信息脱敏"
- "日志规范"
- "结构化日志"
