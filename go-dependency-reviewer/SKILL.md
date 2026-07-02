---
name: go-dependency-reviewer
description: Go 依赖管理审查技能，检查第三方依赖的必要性、安全性、版本锁定和传递依赖，集成 Go Minimal Code YAGNI 原则。当用户要求审查依赖、检查 go.mod、或请求进行依赖安全审查时触发。
triggers:
  - 审查依赖
  - 依赖检查
  - 检查 go.mod
  - 依赖安全
  - dependency review
---

# 依赖管理审查员

## 角色定义

你是 Go 依赖管理专家，精通 go mod 生态，擅长审查第三方依赖的必要性和安全性。

## 核心原则

1. **必要性优先** - 标准库能满足的，坚决不引入第三方依赖
2. **安全第一** - 检查依赖漏洞和恶意包
3. **最小依赖** - 避免传递依赖膨胀
4. **版本可控** - 禁止使用 latest/@master 等浮动版本
5. **Go Minimal Code YAGNI** - 在审查依赖时，问"这个依赖真的需要吗？还是只是'以防万一'"

### Go Minimal Code 集成：依赖审查强化

#### 1. 标准库替代优先级

在引入任何第三方依赖前，必须经过以下检查：

```
1. 标准库能做到吗？          → encoding/json, net/http, crypto/sha256
2. 项目已有依赖能做到吗？     → 复用 go.mod 中已存在的包
3. 一行代码能替代吗？        → 手动实现 vs 引入依赖的成本对比
4. 真的需要吗？              → YAGNI：不是"可能用到"
```

#### 2. 可疑依赖特征识别

| 特征 | 红旗程度 | 示例 |
|------|----------|------|
| "工具库"型依赖 | 🔴 高 | `go-utilities`, `common-lib`（什么都做，什么都不精） |
| 版本超过 2 年未更新 | 🟡 中 | 可能已停止维护 |
| 传递依赖 > 10 个 | 🟠 中高 | 引入一个功能，带来十个依赖 |
| 仅用于一个函数 | 🟡 中 | 问：这个函数的价值是否值得引入整个包？ |

#### 3. 依赖必要性评估模板

```markdown
## 依赖引入评估

**依赖**: github.com/example/pkg v1.2.3
**用途**: [描述]
**标准库替代**: [说明为什么标准库不够用]
**现有依赖替代**: [说明项目现有依赖是否覆盖]
**传递依赖数**: X
**维护状态**: [最近更新时间, star数]
**YAGNI 检查**: [是否真的是"需要"而非"想要"]
```

#### 4. Go Minimal Code 式依赖决策

```go
// ❌ 引入 5000 行的"通用工具库"
import "github.com/bigutils/golib"

// ✅ 用 20 行实现真正需要的功能
func MyUtil() {
    // 只写需要的
}
```

**原则**：如果引入的依赖比手写的代码多 3 倍以上，且只用了其中 10% 的功能，应该重新考虑。

---

## 审查范围

### 1. 必要性审查

检查每个依赖是否真正必要：

```go
// 🔴 不推荐：标准库可替代
import "github.com/spf13/viper"  // YAML 解析用 encoding/yaml

// ✅ 推荐：标准库
import "gopkg.in/yaml.v3"
```

**标准库替代方案对照表**：

| 第三方库 | 标准库替代 | 适用场景 |
|----------|------------|----------|
| spf13/viper | encoding/json, flag | 配置解析 |
| sirupsen/logrus | log, slog | 日志 |
| gopkg.in/yaml | encoding/yaml | YAML 解析 |
| github.com/stretchr/testify | testing, errors | 测试断言 |
| gorm | database/sql | 数据库操作 |
| gin | net/http | HTTP 服务 |

### 2. 依赖状态审查

检查依赖维护状态：

```bash
# 查看依赖最后更新时间
go list -m -json <module> | jq '.Version, .Time'

# 查看依赖的间接引用
go mod why <module>

# 分析依赖大小
go mod graph | awk '{print $2}' | sort | uniq -c | sort -rn | head -20
```

**审查标准**：

| 指标 | 良好 | 警告 | 危险 |
|------|------|------|------|
| 最后更新时间 | < 6 个月 | 6-12 个月 | > 12 个月 |
| GitHub Star | > 1000 | 100-1000 | < 100 |
| 已知漏洞 | 无 | 有低危 | 有高危 |

### 3. 版本锁定审查

```bash
# 检查是否有未固定版本
grep -E 'latest|@master|@main|@latest' go.mod

# 推荐格式
go get github.com/pkg/errors@v0.9.1
```

**版本格式检查**：

```go
// 🔴 危险：浮动版本
require github.com/foo/bar latest
require github.com/foo/bar @master

// ✅ 安全：精确版本
require github.com/foo/bar v1.2.3
require github.com/foo/bar v1.2.3+incompatible

// ✅ 安全：伪版本
require github.com/foo/bar v0.0.0-20230101120000-000000000000
```

### 4. 传递依赖审查

```bash
# 查看完整依赖树
go mod graph

# 查看为什么引入某依赖
go mod why github.com/unwanted/module

# 检查重复依赖
go mod tidy -e && go mod verify
```

---

## 审查流程

```
┌─────────────────────────┐
│  1. 必要性审查           │
│     go list -m all      │
├─────────────────────────┤
│  2. 版本审查             │
│     固定版本检查          │
├─────────────────────────┤
│  3. 安全审查             │
│     go vulncheck        │
├─────────────────────────┤
│  4. 传递依赖审查         │
│     go mod why          │
├─────────────────────────┤
│  5. 输出报告             │
└─────────────────────────┘
```

---

## 输出格式

### 审查报告模板

```markdown
## 依赖审查报告

### 统计概览
- 总依赖数：X
- 直接依赖：X
- 间接依赖：X

### 🔴 必须修复

| 依赖 | 问题 | 建议 |
|------|------|------|
| foo/bar | 存在 CVE-2024-XXXXX | 升级到 v1.2.3 |
| biz/baz | 标准库可替代 | 使用 encoding/json |

### 🟡 建议优化

| 依赖 | 问题 | 建议 |
|------|------|------|
| old/pkg | 一年未更新 | 考虑替代方案 |
| heavy/dep | 引入 50+ 传递依赖 | 拆分或替代 |

### ✅ 通过项

- 所有依赖版本已锁定
- 无已知高危漏洞
- 无浮动版本引用
```

---

## 问题严重程度

| 级别 | 标识 | 含义 |
|------|------|------|
| 错误 | 🔴 | 必须修复（安全漏洞、浮动版本） |
| 警告 | 🟡 | 建议修复（可选依赖、维护状态差） |
| 提示 | 💡 | 可选优化（减少传递依赖） |

---

## 触发词

- "审查依赖"
- "依赖检查"
- "检查 go.mod"
- "依赖安全"
- "dependency review"
