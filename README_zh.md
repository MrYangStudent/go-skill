# Go 工程技能库 (go-skill)

一套完整的 Go 语言工程实践技能集，覆盖从代码开发、测试、质量审查到文档生成的完整开发生命周期。

## 核心技能

### go-project-rules

**项目治理规则**，确保项目一致性、进度可视化和规范执行。

| 技能 | 名称 | 描述 |
|------|------|------|
| [go-project-rules](./go-project-rules/) | 项目治理规则 | 进度同步、README 联动、提交检查、验证闭环 |
| [go-full-dev-workflow](./go-full-dev-workflow/) | 完整开发工作流 | 整合 14 个技能的全链路开发流程 |

## 完整技能列表

### 开发流程

| 技能 | 名称 | 描述 |
|------|------|------|
| [go-project-rules](./go-project-rules/) | 项目治理规则 | 进度同步、README 联动、提交检查、验证闭环 |
| [go-full-dev-workflow](./go-full-dev-workflow/) | 完整开发工作流 | 需求 → 实现 → 测试 → 审查 → 文档 → 验证 |
| [feature-development-workflow](./feature-development-workflow/) | 新功能开发工作流 | 需求拆解、TDD/BDD 开发、微模块迭代交付 |

### 测试生成

| 技能 | 名称 | 描述 |
|------|------|------|
| [test-generator](./test-generator/) | 测试生成专员 | 单元测试、并发测试、边界测试、Mock 编写 |

### 工具函数封装

| 技能 | 名称 | 描述 |
|------|------|------|
| [go-utility-functions](./go-utility-functions/) | 通用工具函数 | HTTP 客户端、签名、加密、排序、时间格式化、泛型切片/Map 转换、分页、重试 |

### 代码审查

| 技能 | 名称 | 描述 |
|------|------|------|
| [error-handling-reviewer](./error-handling-reviewer/) | 错误处理审查员 | error 包装检查、panic 防护、参数校验审计 |
| [go-concurrency-reviewer](./go-concurrency-reviewer/) | Go 并发审查员 | race condition 检测、goroutine 泄漏防护、channel 安全 |
| [dependency-reviewer](./dependency-reviewer/) | 依赖管理审查员 | 第三方依赖必要性、安全性、版本锁定审查 |
| [performance-reviewer](./performance-reviewer/) | 性能审查员 | 超时设置、资源关闭、内存分配、sync.Pool |
| [security-reviewer](./security-reviewer/) | 安全审查员 | 敏感信息、SQL 注入、命令注入、依赖漏洞 |
| [database-reviewer](./database-reviewer/) | 数据库审查员 | 连接池、事务处理、查询效率、N+1 检测 |
| [logging-reviewer](./logging-reviewer/) | 日志规范审查员 | 日志级别、脱敏处理、结构化日志、上下文 |
| [context-propagation-reviewer](./context-propagation-reviewer/) | Context 传播审查员 | 链路完整性、超时设置、取消信号、Header 传播 |
| [api-design-reviewer](./api-design-reviewer/) | API 设计审查员 | RESTful 规范、HTTP 语义、命名一致性、版本控制 |

### 文档生成

| 技能 | 名称 | 描述 |
|------|------|------|
| [doc-generator](./doc-generator/) | 文档生成器 | GoDoc 注释、README、AI 友好示例块 |
| [go-api-doc-generator](./go-api-doc-generator/) | API 文档生成器 | OpenAPI 3.0 规范、Postman 集合、curl 命令 |

## 核心特性

- **全链路覆盖**：从需求分析 → 代码实现 → 测试验证 → 质量审查 → 文档沉淀 → 生产部署
- **AI 友好**：所有文档包含 AI-Usage 注释块，支持 Cline/Cursor 等工具学习
- **零外部依赖**：仅使用 Go 标准库，无需引入额外包
- **严格规范**：遵循 Go 官方最佳实践（gofmt、go vet、race detector）
- **模块化设计**：各技能可独立使用，也可组合使用

## go-full-dev-workflow 工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                      阶段零：项目治理                            │
├─────────────────────────────────────────────────────────────────┤
│  go-project-rules                                               │
│  - 对话初始化（读取 README.md、project.md）                      │
│  - 进度同步（project.md 看板管理）                                │
│  - 架构联动（README.md 同步更新）                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      阶段一：准备与文档                           │
├─────────────────────────────────────────────────────────────────┤
│  feature-development-workflow  →  需求澄清、任务拆解             │
│  doc-generator                 →  项目结构、模块文档               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      阶段二：代码实现                             │
├─────────────────────────────────────────────────────────────────┤
│  代码编写 (遵循开发规范)                                         │
│  - GoDoc 注释                                                    │
│  - 错误处理                                                      │
│  - Context 传递                                                  │
│  - 日志记录                                                      │
│  - go-utility-functions 工具封装（识别重复逻辑→封装可复用函数）    │                                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      阶段三：测试生成                             │
├─────────────────────────────────────────────────────────────────┤
│  test-generator                                                 │
│  - 正常路径测试                                                  │
│  - 边界情况测试                                                  │
│  - 错误路径测试                                                  │
│  - 并发安全测试                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      阶段四：质量审查                             │
├─────────────────────────────────────────────────────────────────┤
│  error-handling-reviewer     →  错误处理                         │
│  go-concurrency-reviewer     →  并发安全                         │
│  dependency-reviewer         →  依赖管理                         │
│  performance-reviewer        →  性能表现                         │
│  security-reviewer           →  安全漏洞                         │
│  database-reviewer            →  数据库操作                       │
│  logging-reviewer             →  日志规范                         │
│  context-propagation-reviewer →  Context 链路                    │
│  api-design-reviewer         →  API 设计                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      阶段五：文档生成                             │
├─────────────────────────────────────────────────────────────────┤
│  go-api-doc-generator                                             │
│  - OpenAPI 3.0 规范                                              │
│  - Postman 集合                                                  │
│  - curl 命令示例                                                 │
│  - API 参考文档                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      阶段六：验证与部署                           │
├─────────────────────────────────────────────────────────────────┤
│  go build                   →  编译检查                          │
│  go test -race             →  竞态检测                          │
│  go run                    →  服务启动                           │
│  API 验证                  →  端点测试                          │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 项目初始化

使用 `go-project-rules` 进行项目初始化：

```
"初始化项目"
"同步进度"
"project rules"
```

首次使用自动加载项目治理规则：
- 读取 README.md 了解项目架构
- 读取 project.md 了解当前进度
- 确认下一步工作

### 2. 使用完整工作流

一键执行完整开发流程：

```
"运行开发工作流"
"执行完整流程"
"Go 开发流程"
```

### 3. 分步执行

#### 1. 开发新功能

使用 `feature-development-workflow` 启动新功能开发流程：

```
"开发新功能"
"新功能工作流"
"开始开发"
```

#### 2. 代码审查

按需执行质量审查：

```bash
# 错误处理审查
error-handling-reviewer

# 并发安全审查
go-concurrency-reviewer

# 性能审查
performance-reviewer

# 安全审查
security-reviewer

# 依赖审查
dependency-reviewer

# 数据库审查
database-reviewer

# 日志审查
logging-reviewer

# Context 审查
context-propagation-reviewer

# API 设计审查
api-design-reviewer
```

#### 3. 测试生成

为代码生成完整测试套件：

```
"生成测试"
"写单元测试"
```

#### 4. 文档生成

生成 API 文档和代码注释：

```
"生成 API 文档"
"生成 README"
```

## 技能详解

### 核心工作流

#### go-project-rules

项目治理规则，确保项目一致性：

- **规则 1**：对话启动强制初始化（读取 README.md、project.md）
- **规则 2**：项目进度强制同步（project.md 看板）
- **规则 3**：架构变更与 README 联动
- **规则 4**：提交前 README 一致性检查
- **规则 5**：阶段完成后的全流程工作流
- **规则 6**：API 修改的即时验证闭环
- **规则 7**：项目扩展约束
- **规则 8**：AI 行为自检

#### go-full-dev-workflow

整合 13 个专项技能的全链路开发流程：

- 阶段零：项目治理（go-project-rules）
- 阶段一：准备与文档（feature-development-workflow, doc-generator）
- 阶段二：代码实现（遵循开发规范）
- 阶段三：测试生成（test-generator）
- 阶段四：质量审查（9 个审查技能）
- 阶段五：文档生成（go-api-doc-generator）
- 阶段六：验证与部署（编译、测试、启动、验证）

### feature-development-workflow

新功能开发工作流，遵循 TDD/BDD 模式：

- 需求澄清与问题定义
- 任务拆解为可验证的微模块
- 设计阶段输出模板
- 集成与验证（go vet、go test -race、go build）

### test-generator

测试生成专员，生成高质量、可维护的测试套件：

- 正常路径测试
- 边界情况测试（nil、零值、极端值）
- 错误路径测试
- 并发安全测试（兼容 `go test -race`）
- Mock 对象编写

### 代码审查技能

| 技能 | 审查范围 |
|------|----------|
| error-handling-reviewer | error 检查、panic 防护、参数校验 |
| go-concurrency-reviewer | race condition、goroutine 泄漏、channel 安全 |
| dependency-reviewer | 必要性、标准库替代、版本锁定、漏洞扫描 |
| performance-reviewer | 超时、资源关闭、内存分配、sync.Pool |
| security-reviewer | 敏感信息、注入防护、认证授权、漏洞扫描 |
| database-reviewer | 连接池、事务、N+1 查询、索引 |
| logging-reviewer | 日志级别、脱敏、结构化、上下文 |
| context-propagation-reviewer | 链路完整性、超时、取消信号、Header 传播 |
| api-design-reviewer | RESTful、状态码、命名一致性、版本控制 |

### 文档生成技能

#### doc-generator

文档生成器，生成 AI 友好的技术文档：

- GoDoc 风格注释
- README 章节结构
- AI-Usage 注释块（供工具学习）
- 使用示例与边界情况说明

#### go-api-doc-generator

API 文档生成器，从 Go HTTP handler 生成完整文档：

- OpenAPI 3.0 规范（YAML/JSON）
- Postman Collection v2.1
- curl 命令示例
- 支持 gorilla/mux、chi、Gin、net/http

## 代码规范

本项目遵循以下 Go 编码规范：

- 所有代码使用 `gofmt` 格式化
- 导入分组顺序：标准库 → 第三方库 → 本地包
- 最大行长度：120 字符
- 包名小写，无下划线
- 错误变量以 `Err` 开头
- 测试文件以 `_test.go` 后缀

## 质量检查

```bash
# 格式化检查
gofmt -l .

# 静态分析
go vet ./...

# 竞态检测
go test -race ./...

# 测试覆盖率
go test -cover ./...

# 漏洞扫描
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

## 适用场景

- 新项目初始化与架构设计
- 复杂业务逻辑开发
- 代码质量审计与重构
- API 文档自动化生成
- 团队编码规范统一

## License

MIT
