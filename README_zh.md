# 工程技能库 (Skill Hub)

[English](./README.md) | [中文](./README_zh.md)

覆盖 Go 语言工程实践、通用开发工具和项目管理的一站式技能集。包含代码开发、测试、质量审查、文档生成、项目初始化和趋势监控等 24 个技能。

## 核心技能

### go-project-rules / project-rules-init

**项目治理规则与初始化**，建立实体驱动开发机制，确保项目一致性、进度可视化和规范执行。

| 技能 | 名称 | 描述 |
|------|------|------|
| [go-project-rules](./go-project-rules/) | 项目治理规则 | 进度同步、README 联动、提交检查、验证闭环 |
| [go-full-dev-workflow](./go-full-dev-workflow/) | 完整开发工作流 | 整合 14 个专项技能的端到端开发流程 |
| [project-rules-init](./project-rules-init/) | 项目规则初始化器 | 实体地图 (ARCHITECTURE.md)、进度追踪 (progress.md)、规则自检 |

### context-compressor / github-trend-monitor

**上下文压缩与趋势监控**，智能压缩对话上下文和跟踪 GitHub 技术趋势。

| 技能 | 名称 | 描述 |
|------|------|------|
| [context-compressor](./context-compressor/) | 上下文压缩 | 内容类型感知压缩、三级热/冷存储、会话统计 |
| [github-trend-monitor](./github-trend-monitor/) | GitHub 趋势监控 | 趋势抓取、AI 简报生成、邮件推送、激增检测 |

### prompt-master

**提示词大师**，基于吴恩达课程的结构化提示词工程。

| 技能 | 名称 | 描述 |
|------|------|------|
| [prompt-master](./prompt-master/) | 提示词大师 | 对话式提示词构建、优化与模板 |

## 完整技能列表

### 开发流程

| 技能 | 名称 | 描述 |
|------|------|------|
| [go-project-rules](./go-project-rules/) | 项目治理规则 | 进度同步、README 联动、提交检查、验证闭环 |
| [go-full-dev-workflow](./go-full-dev-workflow/) | 完整开发工作流 | 需求 → 实现 → 测试 → 审查 → 文档 → 验证 |
| [go-incremental-dev](./go-incremental-dev/) | 增量开发工作流 | 从需求到实现的增量迭代、上下文保护、已实现功能清单 |
| [feature-development-workflow](./feature-development-workflow/) | 新功能开发工作流 | 需求拆解、TDD/BDD 开发、微模块迭代交付 |

### 测试生成

| 技能 | 名称 | 描述 |
|------|------|------|
| [go-test-generator](./go-test-generator/) | 测试生成专员 | 单元测试、并发测试、边界测试、Mock 编写 |

### 工具函数封装

| 技能 | 名称 | 描述 |
|------|------|------|
| [go-utility-functions](./go-utility-functions/) | 通用工具函数 | HTTP 客户端、签名、加密、排序、时间格式化、泛型切片/Map 转换、分页、重试 |
| [go-minimal-code](./go-minimal-code/) | 代码极简器 | YAGNI 原则执行、过度设计检测、标准库优先 |

### 代码审查

| 技能 | 名称 | 描述 |
|------|------|------|
| [go-error-handling-reviewer](./go-error-handling-reviewer/) | 错误处理审查员 | error 包装检查、panic 防护、参数校验审计 |
| [go-concurrency-reviewer](./go-concurrency-reviewer/) | Go 并发审查员 | race condition 检测、goroutine 泄漏防护、channel 安全 |
| [go-dependency-reviewer](./go-dependency-reviewer/) | 依赖管理审查员 | 第三方依赖必要性、安全性、版本锁定审查 |
| [go-performance-reviewer](./go-performance-reviewer/) | 性能审查员 | 超时设置、资源关闭、内存分配、sync.Pool |
| [go-security-reviewer](./go-security-reviewer/) | 安全审查员 | 敏感信息、SQL 注入、命令注入、依赖漏洞 |
| [go-database-reviewer](./go-database-reviewer/) | 数据库审查员 | 连接池、事务处理、查询效率、N+1 检测 |
| [go-logging-reviewer](./go-logging-reviewer/) | 日志规范审查员 | 日志级别、脱敏处理、结构化日志、上下文 |
| [go-context-propagation-reviewer](./go-context-propagation-reviewer/) | Context 传播审查员 | 链路完整性、超时设置、取消信号、Header 传播 |
| [go-api-design-reviewer](./go-api-design-reviewer/) | API 设计审查员 | RESTful 规范、HTTP 语义、命名一致性、版本控制 |

### 文档生成

| 技能 | 名称 | 描述 |
|------|------|------|
| [go-doc-generator](./go-doc-generator/) | 文档生成器 | GoDoc 注释、README、AI 友好示例块 |
| [go-api-doc-generator](./go-api-doc-generator/) | API 文档生成器 | OpenAPI 3.0 规范、Postman 集合、curl 命令 |

### 项目管理与工具

| 技能 | 名称 | 描述 |
|------|------|------|
| [project-rules-init](./project-rules-init/) | 项目规则初始化器 | 语言检测、实体地图生成 (ARCHITECTURE.md)、进度追踪 (progress.md)、规则自检 |
| [skill-auditor](./skill-auditor/) | 技能审核员 | 技能合规性检查、frontmatter 验证、命名规范审计 |
| [skill-sync-manager](./skill-sync-manager/) | 技能同步管理器 | 按项目语言自动启停匹配技能 |

### 通用工具

| 技能 | 名称 | 描述 |
|------|------|------|
| [context-compressor](./context-compressor/) | 上下文压缩 | 智能内容压缩，7 种类型检测、三级热/冷存储、8 个 MCP 工具 |
| [github-trend-monitor](./github-trend-monitor/) | GitHub 趋势监控 | 自动抓取趋势项目、AI 生成简报、邮件推送日报、星标激增检测 |
| [prompt-master](./prompt-master/) | 提示词大师 | 六步结构化框架、头脑风暴、AI 审查、写作工作流 |

## 核心特性

- **全链路覆盖**：从需求分析 → 代码实现 → 测试验证 → 质量审查 → 文档沉淀 → 生产部署
- **实体驱动开发**：ARCHITECTURE.md 记录每个模块/函数的主体和功能描述，防止会话重启后遗忘
- **AI 友好**：所有文档包含 AI-Usage 注释块，支持 Cline/Cursor 等工具学习
- **零外部依赖**：仅使用 Go 标准库，无需引入额外包
- **严格规范**：遵循 Go 官方最佳实践（gofmt、go vet、race detector）
- **模块化设计**：各技能可独立使用，也可组合使用

## go-full-dev-workflow 工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                      阶段零：项目治理                            │
├─────────────────────────────────────────────────────────────────┤
│  project-rules-init (首次) / go-project-rules                     │
│  - 项目初始化：生成实体地图 + 进度追踪 + 规则文件                     │
│  - 对话初始化：读取 ARCHITECTURE.md 和 progress.md 恢复认知          │
│  - 进度同步：progress.md 实体看板管理                               │
│  - 架构联动：README.md 同步更新                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      阶段一：准备与文档                           │
├─────────────────────────────────────────────────────────────────┤
│  feature-development-workflow  →  需求澄清、任务拆解             │
│  go-doc-generator                 →  项目结构、模块文档               │
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
│  go-test-generator                                                 │
│  - 正常路径测试                                                  │
│  - 边界情况测试                                                  │
│  - 错误路径测试                                                  │
│  - 并发安全测试                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      阶段四：质量审查                             │
├─────────────────────────────────────────────────────────────────┤
│  go-error-handling-reviewer     →  错误处理                         │
│  go-concurrency-reviewer     →  并发安全                         │
│  go-dependency-reviewer         →  依赖管理                         │
│  go-performance-reviewer        →  性能表现                         │
│  go-security-reviewer           →  安全漏洞                         │
│  go-database-reviewer            →  数据库操作                       │
│  go-logging-reviewer             →  日志规范                         │
│  go-context-propagation-reviewer →  Context 链路                    │
│  go-api-design-reviewer         →  API 设计                         │
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

首次使用 `project-rules-init` 建立项目治理基础：

```
"初始化项目规则"
"project rules init"
"建立实体地图"
```

自动生成：
- ARCHITECTURE.md — 按阶段定义每个模块/函数的主体和功能
- progress.md — 实体级进度追踪和变更日志
- `.codebuddy/rules/` — 三个 RULE.mdc 规则文件

后续每次会话使用 `go-project-rules` 维持治理规则：

```
"同步进度"
"project rules"
```

### 2. 使用完整工作流

一键执行完整开发流程：

```
"运行开发工作流"
"执行完整流程"
"Go 开发流程"
```

### 3. 分步执行

#### 1. 开发新功能

使用 `feature-development-workflow` 启动新功能开发，或使用 `go-incremental-dev` 进行增量迭代：

```
"开发新功能"
"新功能工作流"
"开始开发"
"增量开发"
```

#### 2. 代码审查

按需执行质量审查：

```bash
# 错误处理审查
go-error-handling-reviewer

# 并发安全审查
go-concurrency-reviewer

# 性能审查
go-performance-reviewer

# 安全审查
go-security-reviewer

# 依赖审查
go-dependency-reviewer

# 数据库审查
go-database-reviewer

# 日志审查
go-logging-reviewer

# Context 审查
go-context-propagation-reviewer

# API 设计审查
go-api-design-reviewer
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

- **规则 1**：对话启动强制初始化（读取 ARCHITECTURE.md、progress.md）
- **规则 2**：项目进度强制同步（progress.md 实体看板）
- **规则 3**：架构变更与 README 联动
- **规则 4**：提交前 README 一致性检查
- **规则 5**：阶段完成后的全流程工作流
- **规则 6**：API 修改的即时验证闭环
- **规则 7**：项目扩展约束
- **规则 8**：AI 行为自检

#### go-full-dev-workflow

整合 14 个专项技能的端到端开发流程，按阶段串联：

- 阶段零：项目治理（go-project-rules）
- 阶段一：准备与文档（feature-development-workflow, go-doc-generator）
- 阶段二：代码实现（遵循开发规范）
- 阶段三：测试生成（go-test-generator）
- 阶段四：质量审查（9 个审查技能）
- 阶段五：文档生成（go-api-doc-generator）
- 阶段六：验证与部署（编译、测试、启动、验证）

#### go-incremental-dev

增量开发工作流，适配大型项目的渐进式开发：

- 上下文保护：防止会话重启后遗忘已实现功能
- 功能清单追踪：记录每个已实现模块的接口和功能
- 回退安全：每步可回退到上一个可运行状态
- 变更摘要：每阶段输出变更摘要

#### feature-development-workflow

新功能开发工作流，遵循 TDD/BDD 模式：

- 需求澄清与问题定义
- 任务拆解为可验证的微模块
- 设计阶段输出模板
- 集成与验证（go vet、go test -race、go build）

### go-test-generator

测试生成专员，生成高质量、可维护的测试套件：

- 正常路径测试
- 边界情况测试（nil、零值、极端值）
- 错误路径测试
- 并发安全测试（兼容 `go test -race`）
- Mock 对象编写

### go-minimal-code

代码极简器，强制执行 YAGNI 原则：

- 过度设计检测：识别不必要的抽象层和接口
- 标准库优先：能用标准库就不引入第三方依赖
- 惰性初始化：按需加载而非预加载
- 死代码清理：识别未使用的导出和函数

### 代码审查技能

| 技能 | 审查范围 |
|------|----------|
| go-error-handling-reviewer | error 检查、panic 防护、参数校验 |
| go-concurrency-reviewer | race condition、goroutine 泄漏、channel 安全 |
| go-dependency-reviewer | 必要性、标准库替代、版本锁定、漏洞扫描 |
| go-performance-reviewer | 超时、资源关闭、内存分配、sync.Pool |
| go-security-reviewer | 敏感信息、注入防护、认证授权、漏洞扫描 |
| go-database-reviewer | 连接池、事务、N+1 查询、索引 |
| go-logging-reviewer | 日志级别、脱敏、结构化、上下文 |
| go-context-propagation-reviewer | 链路完整性、超时、取消信号、Header 传播 |
| go-api-design-reviewer | RESTful、状态码、命名一致性、版本控制 |

### 文档生成技能

#### go-doc-generator

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

### 项目管理与工具

#### project-rules-init

项目规则初始化器，建立实体驱动开发机制：

- 语言/框架自动检测（Go/Python/Node.js）
- 生成 ARCHITECTURE.md 实体地图（按阶段定义每个模块的主体和功能描述）
- 生成 progress.md 进度追踪（实体级状态、变更日志、阻塞项）
- 在 `.codebuddy/rules/` 下生成三个 RULE.mdc（项目规则 + 阶段流程 + 技能清单）
- 规则自检（8 项检查：架构文件、进度文件、阶段定义、实体可追溯、技能覆盖等）
- **核心目标**：解决多阶段开发中 AI 会话重启后的上下文遗忘问题

#### prompt-master

提示词大师，基于吴恩达 AI Prompting for Everyone 课程：

- 六步结构化框架：角色→背景→目的→约束→输出格式→示例
- 头脑风暴、AI 审查、写作工作流
- 迎合性（Sycophancy）认知与应对
- 图像生成 Prompt 优化

#### github-trend-monitor

GitHub Trending 趋势监控：

- 自动抓取 GitHub Trending 趋势项目
- AI 生成每日/每周技术简报
- 邮件推送日报和周报
- 星标激增检测与告警
- 技术栈分析可视化仪表盘

#### skill-auditor

技能合规性审核工具：

- 检查 SKILL.md 格式：YAML frontmatter、name/description/triggers 完整性
- 检查 manifest.json 结构一致性
- 检查技能目录命名规范（语言前缀、路径规范）
- 输出审核报告（pass/warning/failed）

#### skill-sync-manager

技能同步管理器：

- 按项目语言自动启用/停用匹配的技能
- 通过 SessionStart hook 集成，确保每次会话技能与语言匹配
- 支持前缀匹配规则（如 go- 前缀匹配 Go 项目）

### 通用工具

#### context-compressor

上下文压缩技能，智能压缩工具输出和对话上下文：

- **7 种内容类型检测**：JSON/代码/lint/日志/搜索/diff/文本，自动识别
- **智能路由压缩**：每种类型专用压缩器，保留关键信息
- **三级存储 (CCR)**：L1 热存储 (Memory 15min) → L2 冷存储 (SQLite 2h) → L3 移除
- **会话统计**：累计 token 节省、按类型统计、三级存储状态、费用预估
- **缓存管理**：热/冷双向提升、淘汰和手动清理
- **8 个 MCP 工具**：压缩、检索、类型检测、统计、存储概览、冷查询、缓存清理、列表

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
