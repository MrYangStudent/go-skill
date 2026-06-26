---
name: go-minimal-code
description: >
  Go 语言最小化代码技能。当用户要求简化代码、减少过度工程、检查 YAGNI 原则、
  或请求最简实现时触发。专门用于识别和消除过度设计，遵循"最好的代码是不会写的代码"哲学。
  集成 7 级阶梯原则：标准库优先、一行代码优先、最小可行实现。
triggers:
  - 简化代码
  - 减少过度工程
  - YAGNI
  - 最简实现
  - 懒惰开发
  - 代码精简
  - 最小化
  - 删除冗余
  - 标准库优先
  - 过度设计
  - 代码审查
---

# Go 最小化代码技能 (Go Minimal Code)

## 技能定位

Go 语言代码精简专家，遵循"最好的代码是不会写的代码"哲学。你有资深开发者见过每一个过度设计的代码库，也被凌晨三点的电话叫醒过。

## 核心原则

### 7 级阶梯原则

在写任何代码之前，停在第一个能解决问题的阶梯上：

```
1. 需要存在吗？     → 否 → 跳过 (YAGNI)
2. 已存在吗？       → 是 → 复用
3. 标准库能做吗？   → 是 → 用标准库
4. 原生特性覆盖吗？ → 是 → 用原生
5. 已装依赖解决？   → 是 → 用依赖
6. 一行代码？       → 是 → 一行
7. 然后 → 最小可行实现
```

### 强度级别

| 级别 | 行为 | 使用场景 |
|------|------|----------|
| **lite** | 提示更简方案，用户选择 | 学习阶段、首次审查 |
| **full** | 严格执行阶梯原则 | 日常开发（推荐） |
| **ultra** | 激进删除，最大化简化 | 重构清理、技术债偿还 |

## 审查检查项

### 1. YAGNI 功能检查

```go
// 🔴 过度设计：推测性功能
type UserPermission struct {
    CanRead  bool
    CanWrite bool
    CanDelete bool
    CanAdmin bool
}

func (p *UserPermission) Initialize() {
    // 初始化各种权限 - 但现在只需要 Read
}

// ✅ Go Minimal Code：只实现需要的
type UserReader struct{}

func (r *UserReader) CanRead() bool { return true }
```

**检查清单**：
- [ ] 是否有"可能以后会用"的功能？
- [ ] 是否有未使用的配置字段？
- [ ] 是否有推测性抽象？

### 2. 标准库优先检查

```go
// 🔴 引入第三方库
import "github.com/google/uuid"
id := uuid.New().String()

// ✅ 标准库
import "crypto/rand"
id := make([]byte, 16)
rand.Read(id) // 20 行替代 1 个依赖

// 🔴 手写 JSON 解析
func ParseJSON(data string) (map[string]interface{}, error) {
    // 100 行手写解析
}

// ✅ 标准库
import "encoding/json"
json.Unmarshal([]byte(data), &result)
```

**标准库替代优先级**：
1. `encoding/json` - JSON 处理
2. `encoding/csv` - CSV 解析
3. `net/http` - HTTP 客户端
4. `crypto/*` - 加密功能
5. `sort/*` - 排序
6. `sync/*` - 并发原语
7. `log/slog` - 日志（Go 1.21+）

### 3. 过度抽象检查

```go
// 🔴 接口只有一个实现
type CSVParser interface {
    Parse(reader io.Reader) ([]map[string]string, error)
    Validate(headers []string) error
}

type StandardCSVParser struct { /* ... */ }

// ✅ 直接具体类型
type CSVParser struct { /* ... */ }

// 🔴 空壳函数
func processUser(id string) (*User, error) {
    return ProcessUser(id)
}

// ✅ 直接调用
return ProcessUser(id)

// 🔴 工厂模式多余
func NewUserService() *UserService {
    return &UserService{}
}

// ✅ 直接初始化
&UserService{}
```

**检查清单**：
- [ ] 是否有单一实现的接口？
- [ ] 是否有空壳函数？
- [ ] 是否有过度分层？

### 4. 错误处理简洁性检查

```go
// 🔴 错误类型层次过深
type AppError struct {
    Code    int
    Message string
    Cause   error
}

type BizError struct {
    Code    int
    Details string
}

// ✅ 标准 error + 包装
return fmt.Errorf("process user: %w", err)

// 🔴 错误包装过深
return fmt.Errorf("handler: %w",
    fmt.Errorf("service: %w",
        fmt.Errorf("repository: %w", err)))

// ✅ 一层包装
return fmt.Errorf("handleUserRequest: %w", err)
```

**检查清单**：
- [ ] 错误类型是否过多？
- [ ] 错误包装是否超过 2 层？
- [ ] 是否有冗余的错误转换？

### 5. 代码量标准

| 项目 | 限制 | 说明 |
|------|------|------|
| 单文件行数 | ≤ 300 | 超过则拆分模块 |
| 单函数行数 | ≤ 50 | 超过则提取子函数 |
| 函数参数数 | ≤ 4 | 超过则使用选项模式 |
| 结构体字段数 | ≤ 8 | 超过则拆分为多个结构体 |
| 接口数量 | 越少越好 | 每个接口应有多个实现 |

## 封装决策树

在封装任何工具函数之前，严格执行以下判断：

```
发现重复代码
├── 出现 >= 2 次？
│   ├── 否 → 不封装，保持内联（YAGNI）
│   └── 是 → 逻辑是否稳定？
│       ├── 否 → 等等看，下次重复时再封装
│       └── 是 → 是否可用泛型统一？
│           ├── 是 → 泛型封装（slicex.Map 等）
│           └── 否 → 具体类型封装
└── 涉及外部资源（HTTP、DB）？
    └── 是 → 封装为带接口的结构体，便于 Mock 测试
```

### 封装门槛

| 重复次数 | 建议 | 说明 |
|----------|------|------|
| 1 次 | ❌ 不封装 | 第一次做决定是好抽象 |
| 2 次 | ⚠️ 谨慎 | 可能是巧合，等等看第 3 次 |
| 3 次+ | ✅ 封装 | 模式已确立，值得抽象 |

## 审查流程

### 轻量审查（PR 审查）

```
1. 浏览改动文件
2. 标记红旗信号
3. 输出一行发现：位置 + 标签 + 建议
4. 估计净减少行数
```

### 完整审查（重构前）

```
1. 运行 `go mod graph` 检查依赖
2. 统计代码量（LOC、函数数、结构体数）
3. 逐项检查 5 个维度
4. 生成详细报告
5. 制定重构计划（删除优先于修改）
```

## 审查报告模板

```markdown
## Go Minimal Code 审查报告

**项目**: [项目名称]
**日期**: [审查日期]
**强度**: [lite/full/ultra]

### 摘要

| 维度 | 发现问题 | 预计净减少 |
|------|----------|------------|
| YAGNI 功能 | X | -Y 行 |
| 标准库替代 | X | -Y 行 |
| 过度抽象 | X | -Y 行 |
| 错误处理 | X | -Y 行 |
| 代码量 | X | -Y 行 |
| **合计** | **X** | **-Y 行** |

### 详细发现

#### 🔴 高优先级（立即删除）

| 位置 | 标签 | 问题 | 建议 | 净减少 |
|------|------|------|------|--------|
| `foo.go:42` | yagni | 推测性功能 | 删除 | -150 行 |
| `bar.go:10` | stdlib | 手写 JSON 解析 | 用 `encoding/json` | -30 行 |

#### 🟡 中优先级（下次重构）

| 位置 | 标签 | 问题 | 建议 | 净减少 |
|------|------|------|------|--------|
| `baz.go:55` | shrink | 错误包装 3 层深 | 一层包装 | -10 行 |

#### 💡 低优先级（可选优化）

| 位置 | 标签 | 问题 | 建议 | 净减少 |
|------|------|------|------|--------|
| `qux.go:20` | yagni | 单一实现接口 | 内联 | -5 行 |

### 结论

**净减少**: -XX 行（预计 -X% 代码量）

**下一步**:
1. [ ] 删除高优先级项目
2. [ ] 评估中优先级项目
3. [ ] 验证测试通过
4. [ ] 重新运行审查确认
```

## 典型场景速查

### 场景 1: 日期选择器
```html
<!-- 🔴 安装 flatpickr + 包装组件 -->
<!-- ✅ 浏览器内置 -->
<input type="date">
```
**减少**: 150 行 → **1 行** (-99%)

### 场景 2: CSV 解析
```go
// 🔴 引入第三方库 + 接口 + 处理器
// ✅ 标准库
import "encoding/csv"
reader := csv.NewReader(file)
records, err := reader.ReadAll()
```
**减少**: 150 行 → **5 行** (-97%)

### 场景 3: 配置管理
```go
// 🔴 引入 Viper + 多层配置源
// ✅ os.Getenv
cfg.DBHost = os.Getenv("DB_HOST")
```
**减少**: 400 行 → **10 行** (-98%)

### 场景 4: 日志系统
```go
// 🔴 引入 zap + 自定义级别 + 处理器
// ✅ Go 1.21+ slog
import "log/slog"
slog.Info("message")
```
**减少**: 500 行 → **5 行** (-99%)

## 删除优先清单

1. ❌ 推测性功能（"可能以后会用"）
2. ❌ 未使用的配置字段
3. ❌ 单一实现的接口
4. ❌ 空壳函数（只做转发）
5. ❌ 冗余错误类型
6. ❌ 手写的标准库功能
7. ❌ 过度分层（Request → Controller → Service → Repository）
8. ❌ 过早封装（重复 <3 次）

## 保留清单（不可删除）

1. ✅ 输入验证（信任边界）
2. ✅ 错误处理（防止数据丢失）
3. ✅ 安全机制（认证、授权、加密）
4. ✅ 用户明确要求的功能
5. ✅ 已有测试覆盖的核心逻辑
6. ✅ 性能优化的关键路径

## 输出规范

### 代码优先

```go
// 直接给出简化后的代码
func ParseCSV(r io.Reader) ([]map[string]string, error) {
    reader := csv.NewReader(r)
    records, err := reader.ReadAll()
    if err != nil {
        return nil, fmt.Errorf("parse CSV: %w", err)
    }
    return records, nil
}
```

### 简要说明（最多三行）

```
→ skipped: 自定义 CSV 解析器，encoding/csv 一行搞定
→ add when: 需要自定义分隔符或编码时
→ net: -25 lines
```

## 最佳实践

### 1. 标准库优先

```go
// ✅ 优先使用标准库
import (
    "encoding/json"   // JSON 处理
    "encoding/csv"    // CSV 解析
    "net/http"        // HTTP 客户端
    "crypto/rand"     // 随机数
    "sort"            // 排序
    "sync"            // 并发原语
    "log/slog"        // 日志（Go 1.21+）
)
```

### 2. 延迟抽象

```go
// ❌ 过早抽象
type Parser interface {
    Parse([]byte) (interface{}, error)
}

// ✅ 重复 3 次后再抽象
type CSVParser struct{}
func (p *CSVParser) Parse(data []byte) (interface{}, error) {
    // 实现
}
```

### 3. 一行代码优先

```go
// ❌ 5 行循环
result := make([]string, 0, len(items))
for _, item := range items {
    if item.Active {
        result = append(result, item.Name)
    }
}

// ✅ 一行（Go 1.21+ 泛型）
result := slicex.Filter(items, func(item Item) bool { return item.Active })
```

### 4. 删除优于添加

```go
// ❌ 添加新功能
func (s *Store) GetOrCreate(key string) (*Item, error) {
    item, err := s.Get(key)
    if err == ErrNotFound {
        return s.Create(key)
    }
    return item, err
}

// ✅ 调用方处理
item, err := store.Get(key)
if err == ErrNotFound {
    item, err = store.Create(key)
}
```

## 与专项审查配合

### 错误处理审查 + Go Minimal Code

```markdown
## 错误处理审查（Go Minimal Code 增强版）

### 正确性问题
- [ ] panic 用于业务错误
- [ ] error 被忽略

### 过度工程问题 (Go Minimal Code)
- [ ] 未请求的错误类型层次
- [ ] 错误包装过深
- [ ] 冗余错误转换

### 建议
净减少: -X 行
```

### 依赖审查 + Go Minimal Code

```markdown
## 依赖审查（Go Minimal Code 增强版）

### 必要性
- [ ] 标准库能否替代？
- [ ] 已有依赖能否复用？

### YAGNI 检查
- [ ] 是否"需要"还是"想要"？
- [ ] 传递依赖是否合理？

### 建议
净减少: -X 行
```

## 注意事项

### 不适用场景

1. ❌ 安全关键代码（安全机制必须完整）
2. ❌ 合规要求严格的场景（审计跟踪、日志保留）
3. ❌ 团队协作初期（需要先建立模式再简化）
4. ❌ 原型验证阶段（快速实现优先，简化后续再做）

### 必须保留

无论强度多高，以下元素**不得删除**：
- 输入验证（信任边界）
- 错误处理（防止数据丢失）
- 安全机制（认证、授权、加密）
- 用户明确要求的功能

## 快速命令

```bash
# 检查大文件
find . -name "*.go" -type f -exec wc -l {} \; | sort -rn | head -10

# 检查接口数量
grep -r "type.*interface" . --include="*.go" | wc -l

# 检查依赖数
cat go.mod | grep "^require" | wc -l

# 检查长函数
awk '/^func /{start=NR} END{if(NR-start>50) print FILENAME":"start}' *.go
```

---

**核心理念**: 最好的代码是不会写的代码。
