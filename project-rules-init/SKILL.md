---
name: project-rules-init
description: 项目初始化时自动检测语言/框架，生成实体地图（ARCHITECTURE.md）、进度追踪（progress.md）、项目规则文件（架构导航、阶段流程、技能匹配矩阵），并执行规则自检。核心解决多阶段开发中 AI 会话重启后的上下文遗忘问题。
version: 1.0.0
triggers:
  - 初始化项目规则
  - 生成项目规则
  - setup project rules
  - init rules
  - 项目初始化
  - 新建项目
---

# project-rules-init

> 项目规则初始化器 — 自动检测项目语言和框架，生成会话启动指引、阶段开发规则和技能匹配清单。
>
> **⚠️ CodeBuddy 规则目录规范**: 所有规则必须放在 `.codebuddy/rules/<规则名>/RULE.mdc`，每条规则一个子目录。

## 概述

每次从零启动一个 AI 辅助编码项目时，项目规则（架构导航、阶段流程、技能选择）都需要从零编写。这些规则中有大量固定内容是通用的，反复手写低效且容易遗漏。

**核心痛点**：多阶段开发中，AI 会话重启后会丢失对已创建文件、已实现功能的记忆。仅靠"进度文件"记录阶段状态不够——必须追踪到**实体级别**（每个模块、文件、函数是什么、做什么）。

本技能建立**实体驱动开发（Entity-Driven Development）**机制：
1. 检测项目语言和框架
2. **生成 ARCHITECTURE.md**：项目实体地图，按阶段定义每个模块/文件/函数的主体和功能
3. **生成 progress.md**：实体级进度追踪，每完成一个实体即更新状态
4. 生成三个规则文件（项目规则 + 阶段流程 + 技能匹配清单），引用实体定义
5. 自动运行规则自检，输出检查报告

## 工作流

### Step 1: 检测项目语言和框架

**检测逻辑**（按优先级）：

| 检测文件 | 判定语言 | 框架推断 |
|----------|----------|----------|
| `go.mod` | Go | 检查 go.sum 中的 gin/echo/fiber → Web 框架 |
| `pyproject.toml` | Python | 检查 [tool.*] 段 → ruff/mypy/pytest + FastAPI/Django |
| `package.json` | Node.js | 检查 devDependencies → React/Vue/Next.js/Nest.js |
| `Cargo.toml` | Rust | 检查 [dependencies] → 框架 |
| 以上均无 | 通用 | 使用通用规则模板 |

**执行步骤**：
1. 在项目根目录扫描上述标识文件
2. 记录第一个匹配的语言（多语言项目选主语言）
3. 输出检测结果：`[LANG_DETECT] 项目语言: {{PROJECT_LANGUAGE}}`

### Step 2: 生成项目实体地图 — ARCHITECTURE.md

**⚠️ ARCHITECTURE.md 是本机制的核心**：它按阶段定义每个模块/文件/函数的主体和功能描述，是防止多阶段遗忘的唯一信息源。每次会话启动必须首先读取此文件。

#### 模板变量定义

| 变量 | 来源 | 示例值 |
|------|------|--------|
| `{{PROJECT_NAME}}` | 目录名/package名 | `ai-video-pipeline` |
| `{{PROJECT_DESC}}` | 用户输入或 README 首段 | `AI 驱动的视频处理流水线` |
| `{{GENERATION_TIME}}` | 当前时间 ISO 8601 | `2026-07-02T10:00:00+08:00` |
| `{{PROJECT_LANGUAGE}}` | Step 1 检测结果 | `Python` |

#### 生成逻辑

1. **检查 `ARCHITECTURE.md` 是否已存在**：
   - 已存在 → 跳过，输出 `[SKIP] ARCHITECTURE.md 已存在，不覆盖`
   - 不存在 → 生成模板，输出 `[GEN] 生成 ARCHITECTURE.md`

2. **生成模板**（⚠️ 只生成骨架，等用户填入实际内容）：

```markdown
# {{PROJECT_NAME}} — 项目架构

> 最后更新: {{GENERATION_TIME}}
> 语言: {{PROJECT_LANGUAGE}}
> 概述: {{PROJECT_DESC}}

---

## 📋 实体定义规范

本项目按以下格式定义每个实体。**所有条目均为占位，需在对应阶段开发时填入实际内容**。

| 字段 | 说明 |
|------|------|
| **文件/模块** | 实体在项目中的路径（如 `src/auth/handler.go`） |
| **主体** | 实体的类型和名称（如 `LoginHandler` 函数、`UserService` 类） |
| **所属阶段** | 该实体在哪个 Phase 创建（Phase 0 ~ Phase 4） |
| **功能描述** | 该实体解决什么问题，核心输入/输出是什么 |
| **依赖** | 该实体依赖的其他实体（列表） |
| **状态** | ⬜ 待开发 / 🔄 开发中 / ✅ 已完成 |

---

## Phase 0: 环境与基础设施

> 目标: 项目骨架、配置管理、依赖安装、基础工具

### 实体清单

| 文件/模块 | 主体 | 功能描述 | 依赖 | 状态 |
|-----------|------|----------|------|------|
| _待填入_ | _待填入_ | _待填入_ | - | ⬜ |

### 阶段小结

- **产出**: [待填入]
- **关键决策**: [待填入]

---

## Phase 1: 核心业务开发

> 目标: 核心业务逻辑、API 定义、数据模型

### 实体清单

| 文件/模块 | 主体 | 功能描述 | 依赖 | 状态 |
|-----------|------|----------|------|------|
| _待填入_ | _待填入_ | _待填入_ | _待填入_ | ⬜ |

### 阶段小结

- **产出**: [待填入]
- **关键决策**: [待填入]

---

## Phase 2: 测试与质量保障

> 目标: 单元测试、集成测试、测试覆盖率

### 实体清单

| 文件/模块 | 主体 | 功能描述 | 依赖 | 状态 |
|-----------|------|----------|------|------|
| _待填入_ | _待填入_ | _待填入_ | _待填入_ | ⬜ |

### 阶段小结

- **产出**: [待填入]
- **关键决策**: [待填入]

---

## Phase 3: 审查、优化与文档

> 目标: 代码审查、性能优化、技术文档

### 实体清单

| 文件/模块 | 主体 | 功能描述 | 依赖 | 状态 |
|-----------|------|----------|------|------|
| _待填入_ | _待填入_ | _待填入_ | _待填入_ | ⬜ |

### 阶段小结

- **产出**: [待填入]
- **关键决策**: [待填入]

---

## Phase 4: 部署与收尾

> 目标: CI/CD、部署配置、最终验收

### 实体清单

| 文件/模块 | 主体 | 功能描述 | 依赖 | 状态 |
|-----------|------|----------|------|------|
| _待填入_ | _待填入_ | _待填入_ | _待填入_ | ⬜ |

### 阶段小结

- **产出**: [待填入]
- **关键决策**: [待填入]

---

## 🔗 跨阶段依赖图

```
Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4
 [基础设施]   [核心业务]   [测试]     [审查/文档]  [部署]
     │            │          │           │           │
     └── 配置文件、工具函数 → 被所有后续阶段依赖
```

---

> ⚠️ **维护规则**: 
> 1. 每次完成一个实体开发后，**立即**更新对应阶段表格：填入实体信息并将状态改为 ✅
> 2. 每次会话开始时，**首先**读取本文件以恢复对项目的完整认知
> 3. 如果实体被废弃或重构，用 `~~删除线~~` 标记并注明原因
```

### Step 3: 生成实体进度追踪 — progress.md

**⚠️ progress.md 是 ARCHITECTURE.md 的姊妹文件**：专注追踪**当前进度和阻塞项**，不重复实体定义（实体定义只在 ARCHITECTURE.md 中维护）。

#### 生成逻辑

1. **检查 `progress.md` 是否已存在**：
   - 已存在 → 跳过，输出 `[SKIP] progress.md 已存在，不覆盖`
   - 不存在 → 生成模板，输出 `[GEN] 生成 progress.md`

2. **生成模板**：

```markdown
# {{PROJECT_NAME}} — 开发进度

> 最后更新: {{GENERATION_TIME}}
> 关联: 实体定义见 [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 当前状态总览

| 阶段 | 实体总数 | 已完成 | 进行中 | 待开始 | 阻塞 | 进度 |
|------|----------|--------|--------|--------|------|------|
| Phase 0 | - | 0 | 0 | - | 0 | 0% |
| Phase 1 | - | 0 | 0 | - | 0 | 0% |
| Phase 2 | - | 0 | 0 | - | 0 | 0% |
| Phase 3 | - | 0 | 0 | - | 0 | 0% |
| Phase 4 | - | 0 | 0 | - | 0 | 0% |
| **总计** | - | **0** | **0** | - | **0** | **0%** |

---

## 当前阶段: Phase 0 — 环境与基础设施

> 🎯 当前目标: [待填入]

### 本轮会话目标

- [ ] [待填入]

### 本轮已完成

_暂无_

---

## 变更日志

| 日期 | 阶段 | 实体 | 变更类型 | 说明 |
|------|------|------|----------|------|
| {{GENERATION_TIME}} | - | - | 初始化 | 创建进度文件 |

---

## 阻塞项

_暂无_

> ⚠️ **更新时机**: 
> 1. **开始开发一个实体时**: 在 ARCHITECTURE.md 中将状态改为 🔄，在此处记录
> 2. **完成一个实体时**: 在 ARCHITECTURE.md 中将状态改为 ✅，在此处记录变更日志
> 3. **遇到阻塞时**: 在此处登记阻塞项
> 4. **会话结束时**: 更新"本轮已完成"和"下一轮目标"
```

### Step 4: 生成规则文件

> **注意**: 此处的规则文件模板依赖 Step 2-3 生成的 ARCHITECTURE.md 和 progress.md。

**⚠️ 必须使用 CodeBuddy 规范的规则目录结构**：

```
.codebuddy/rules/
├── project-rules/
│   └── RULE.mdc          ← 项目规则（总是加载）
├── phase-rules/
│   └── RULE.mdc          ← 阶段流程（总是加载）
└── skills-manifest/
    └── RULE.mdc          ← 技能清单（智能体请求）
```

**RULE.mdc 格式**：每个文件以 YAML frontmatter 开头，正文为 Markdown 内容。

```yaml
---
description: 规则描述（供 Agent 判断相关性）
alwaysApply: true          # true=总是加载, false=智能体请求/手动
enabled: true
updatedAt: 2026-06-16T00:00:00.000Z
provider: project-rules-init
---
```

**模板变量占位符**：

| 变量 | 来源 | 示例值 |
|------|------|--------|
| `{{PROJECT_NAME}}` | pyproject.toml `[project].name` 或 package.json `name` 或目录名 | `ai-video-pipeline` |
| `{{PROJECT_LANGUAGE}}` | Step 1 检测结果 | `Python` |
| `{{ARCHITECTURE_FILE}}` | 扫描根目录匹配 `ARCHITECTURE*.md` | `ARCHITECTURE.md` |
| `{{PROGRESS_FILE}}` | 固定值 | `progress.md` |
| `{{PLAN_FILE}}` | 扫描根目录匹配 `PLAN*.md` | `PLAN.md` |
| `{{DEPENDENCY_FILE}}` | 按语言 | `pyproject.toml` / `go.mod` / `package.json` |
| `{{SKILLS_PATH}}` | 默认 `~/.codebuddy/skills/` | 可覆盖 |
| `{{GENERATION_TIME}}` | 当前时间 ISO 8601 | `2026-06-16T14:00:00+08:00` |

#### 规则 1: `.codebuddy/rules/project-rules/RULE.mdc`（总是加载）

**YAML frontmatter**：`alwaysApply: true`

**内容模板**：

```markdown
# {{PROJECT_NAME}} — 项目规则

## 会话启动检查清单

> ⚠️ **目标**: 在 3 分钟内恢复对项目的完整认知，避免因会话重启导致的上下文遗忘。

1. **读取实体地图** — 阅读 {{ARCHITECTURE_FILE}}
   - 了解项目有哪些阶段、每个阶段有哪些实体
   - 查看每个实体的功能描述和依赖关系
   - 确认跨阶段依赖图理解正确
2. **读取进度追踪** — 阅读 {{PROGRESS_FILE}}
   - 确认当前在哪个阶段
   - 查看哪些实体已完成（✅）、哪些进行中（🔄）
   - 检查是否有阻塞项
3. **读取阶段流程** — 阅读 .codebuddy/rules/phase-rules/RULE.mdc
   - 确认当前阶段的入口/出口标准
   - 确认工具链命令
4. **确认技能清单** — 查看 .codebuddy/rules/skills-manifest/RULE.mdc（智能体请求时自动加载）
   - 确认当前阶段可用的审查/生成技能
5. **确认上下文后开始工作**

## 会话结束检查清单

> ⚠️ **目标**: 确保下一轮会话能无缝衔接，不丢失任何进度。

1. **更新实体状态** — 在 {{ARCHITECTURE_FILE}} 中：
   - 新创建的实体 → 填入主体、功能描述、依赖，状态标为 ✅
   - 修改过的实体 → 更新功能描述
   - 废弃的实体 → 用 `~~删除线~~` 标记
2. **更新进度追踪** — 在 {{PROGRESS_FILE}} 中：
   - 更新阶段状态总览（实体统计数据）
   - 填写变更日志（日期、阶段、实体、变更类型、说明）
   - 记录本轮已完成项
   - 如有阻塞，登记阻塞项
3. **阶段小结** — 如果当前阶段结束时：
   - 在 {{ARCHITECTURE_FILE}} 的阶段小结中记录产出和关键决策
   - 在 {{PROGRESS_FILE}} 中更新"当前阶段"指向下一阶段

## 编码规范
[按 {{PROJECT_LANGUAGE}} 输出对应规范]

## 提交规范
Conventional Commits

## 禁止事项
[通用禁止项 + 特定语言禁止项]
```

#### 规则 2: `.codebuddy/rules/phase-rules/RULE.mdc`（总是加载）

**YAML frontmatter**：`alwaysApply: true`

**内容模板**：

```markdown
# {{PROJECT_NAME}} — 阶段开发规则

> ⚠️ **开发前必读**: 每个阶段开始前，必须先在 {{ARCHITECTURE_FILE}} 中查看该阶段的实体清单，确认哪些实体待开发、各自的功能描述是什么。

## 通用开发流程

```
读取实体清单 → 逐实体编码 → 静态检查 → 单元测试 → 代码审查 → 更新实体状态
```

## 阶段详表

### Phase 0: 环境与基础设施

| 项目 | 内容 |
|------|------|
| **目标** | 搭建项目骨架、配置管理、依赖安装、基础工具函数 |
| **实体范围** | 见 {{ARCHITECTURE_FILE}} → Phase 0 实体清单 |
| **入口条件** | 项目语言/框架已确定，开发环境已就绪 |
| **开发流程** | 1. 查看 ARCHITECTURE.md Phase 0 实体清单 → 2. 逐实体编码 → 3. 每完成一个实体，更新 ARCHITECTURE.md 状态为 ✅ → 4. 全部完成后更新 progress.md |
| **出口标准** | 所有 Phase 0 实体状态为 ✅；`{{PROJECT_LANGUAGE}}` 编译/启动成功；lint 通过 |
| **工具命令** | [按 {{PROJECT_LANGUAGE}} 填入对应命令：如 go mod tidy, npm install, pip install -r requirements.txt] |

### Phase 1: 核心业务开发

| 项目 | 内容 |
|------|------|
| **目标** | 实现核心业务逻辑、API 定义、数据模型 |
| **实体范围** | 见 {{ARCHITECTURE_FILE}} → Phase 1 实体清单 |
| **入口条件** | Phase 0 全部实体已完成 |
| **开发流程** | 1. 查看 ARCHITECTURE.md Phase 1 实体清单 → 2. 确认每个实体的功能描述和依赖关系 → 3. 先开发被依赖实体，再开发依赖实体 → 4. 逐实体编码+审查 → 5. 每完成一个实体立即更新状态 |
| **出口标准** | 所有 Phase 1 实体状态为 ✅；核心 API 可调用；{{PROJECT_LANGUAGE}} 编译/启动成功 |
| **工具命令** | [按 {{PROJECT_LANGUAGE}} 填入：如 go build, go vet, python -m pytest, npm run build] |

### Phase 2: 测试与质量保障

| 项目 | 内容 |
|------|------|
| **目标** | 为每个核心实体编写单元测试，确保覆盖率 |
| **实体范围** | 见 {{ARCHITECTURE_FILE}} → Phase 2 实体清单 |
| **入口条件** | Phase 1 全部实体已完成 |
| **开发流程** | 1. 查看 ARCHITECTURE.md Phase 1 实体清单（测试实体对应 Phase 1 业务实体）→ 2. 为每个业务实体编写对应测试文件 → 3. table-driven tests / 参数化测试 → 4. 运行覆盖率检查 |
| **出口标准** | 所有 Phase 2 实体状态为 ✅；测试覆盖率 ≥ 目标值；race/并发检测通过 |
| **工具命令** | [按 {{PROJECT_LANGUAGE}} 填入：如 go test -race -cover, pytest --cov, npm test -- --coverage] |

### Phase 3: 审查、优化与文档

| 项目 | 内容 |
|------|------|
| **目标** | 代码质量审查、性能优化、技术文档生成 |
| **实体范围** | 见 {{ARCHITECTURE_FILE}} → Phase 3 实体清单 |
| **入口条件** | Phase 2 全部实体已完成 |
| **开发流程** | 1. 使用审查技能逐个审查 Phase 0-2 实体 → 2. 修复发现的问题 → 3. 性能分析与优化 → 4. 生成文档 |
| **出口标准** | 所有审查通过（无 critical/warning）；文档已生成；性能指标达标 |
| **工具命令** | [按 {{PROJECT_LANGUAGE}} 填入：如 govulncheck, pprof, benchmark] |

### Phase 4: 部署与收尾

| 项目 | 内容 |
|------|------|
| **目标** | CI/CD 配置、部署、最终验收 |
| **实体范围** | 见 {{ARCHITECTURE_FILE}} → Phase 4 实体清单 |
| **入口条件** | Phase 3 全部审查通过 |
| **开发流程** | 1. 创建 Dockerfile / CI 配置 → 2. 部署至测试环境 → 3. 验收测试 → 4. 最终 README 更新 |
| **出口标准** | 部署成功；所有验收测试通过；CI 流水线绿灯 |
| **工具命令** | [按 {{PROJECT_LANGUAGE}} 填入：如 docker build, docker-compose up] |

## {{PROJECT_LANGUAGE}} 工具链速查

| 命令 | 用途 | 阶段 |
|------|------|------|
| [按语言填入对应命令] | [用途] | [阶段] |

---

## 🔑 实体遗忘防护规则

> 以下规则确保多阶段开发中不会遗忘已创建的实体：

1. **每个实体必须注册在 ARCHITECTURE.md 中**：创建新模块/文件/函数时，必须在对应阶段的实体清单中添加一行
2. **每天首次会话必须先读 ARCHITECTURE.md**：在开始任何编码前恢复实体认知
3. **修改实体时必须先查 ARCHITECTURE.md**：确认该实体的功能描述、依赖关系，避免破坏已有功能
4. **删除实体时必须标记而非删除行**：用 `~~删除线~~` + 原因标注，保留历史记录
```

#### 规则 3: `.codebuddy/rules/skills-manifest/RULE.mdc`（智能体请求）

**YAML frontmatter**：`alwaysApply: false`（Agent 根据 description 判断相关性后自动加载）

**内容模板**：

```markdown
# {{PROJECT_NAME}} — 技能匹配清单

## 技能匹配矩阵
| 阶段 | 推荐技能 | 用途 | 状态 |

## 覆盖统计
| 阶段 | 推荐技能数 | 覆盖状态 |

## 不适用技能
| 技能 | 不适用原因 |
```

### Step 5: 技能发现与匹配矩阵

**扫描逻辑**：
1. 扫描 `{{SKILLS_PATH}}` 目录（默认 `~/.codebuddy/skills/`）
2. 列出所有已安装的技能（读取每个子目录的 `SKILL.md` frontmatter）
3. 按技能名称前缀分类：`python-*` / `go-*` / 通用技能
4. 根据 `{{PROJECT_LANGUAGE}}` 匹配：
   - 语言匹配的技能 → ✅ 推荐
   - 通用技能 → ✅ 推荐（标注阶段）
   - 语言不匹配的技能 → ❌ 不适用（标注原因）

**匹配规则**：

| 技能前缀/名称 | 适用阶段 | 适用条件 |
|---------------|----------|----------|
| `*-dependency-reviewer` | Phase 0, Phase 4 | 语言匹配 |
| `*-config-reviewer` | Phase 0 | 语言匹配 |
| `*-error-handling-reviewer` | Phase 1 | 语言匹配 |
| `*-api-design-reviewer` | Phase 1 | 语言匹配 |
| `*-typing-reviewer` | Phase 1 | 语言匹配 |
| `*-concurrency-reviewer` | Phase 1, Phase 2 | 语言匹配 |
| `*-logging-reviewer` | Phase 1 | 语言匹配 |
| `*-test-generator` | Phase 2 | 语言匹配 |
| `*-security-reviewer` | Phase 3 | 语言匹配 |
| `*-performance-reviewer` | Phase 3 | 语言匹配 |
| `*-refactor-reviewer` | Phase 3 | 语言匹配 |
| `*-architecture-reviewer` | Phase 3 | 语言匹配 |
| `*-doc-generator` | Phase 3 | 语言匹配或通用 |
| `*-api-doc-generator` | Phase 3 | 语言匹配 |
| `*-ci-cd-workflow` | Phase 4 | 语言匹配 |
| `*-project-rules` | 全阶段 | 语言匹配或通用 |
| `*-full-dev-workflow` | 全阶段 | 语言匹配 |
| `*-feature-development-workflow` | 全阶段 | 语言匹配 |
| `context-compressor` | 全阶段 | 通用 |
| `prompt-master` | 全阶段 | 通用 |
| `skill-auditor` | Phase 4 | 通用 |

### Step 6: 规则自检

生成所有文件后，自动执行以下检查：

| # | 检查项 | 检查内容 | 通过条件 |
|---|--------|----------|----------|
| 1 | 架构文件 | `{{ARCHITECTURE_FILE}}` 是否存在 | 文件存在；不存在则按 Step 2 模板生成 |
| 2 | 进度文件 | `{{PROGRESS_FILE}}` 是否存在 | 文件存在；不存在则按 Step 3 模板生成 |
| 3 | 计划文件 | `{{PLAN_FILE}}` 是否存在 | 文件存在 |
| 4 | 规则目录 | `.codebuddy/rules/` 下是否有 3 个 RULE.mdc | 3 个子目录各含 RULE.mdc |
| 5 | 阶段定义 | `phase-rules/RULE.mdc` 每个 Phase 有入口/出口标准 | 5 个 Phase 各有 entry + exit + 实体范围 |
| 6 | 实体可追溯 | `ARCHITECTURE.md` 是否包含实体清单表格 | 每个 Phase 有实体清单表头 |
| 7 | 技能覆盖 | 所有阶段是否至少有一个匹配技能 | 覆盖率 ≥ 80% |
| 8 | 占位符 | 所有 RULE.mdc 中的 `{{VAR}}` 是否已替换 | 无未填充的占位符 |

**输出格式**：

```
═══ 规则自检报告 ═══
✅ 架构文件: ARCHITECTURE.md 存在（含 5 个阶段实体清单）
✅ 进度文件: progress.md 存在
✅ 计划文件: PLAN.md 存在
✅ 规则目录: .codebuddy/rules/ 下 3 个 RULE.mdc 已生成
✅ 阶段定义: 5 个阶段均有入口/出口标准 + 实体范围
✅ 实体可追溯: 5/5 阶段有实体清单表头
✅ 技能覆盖: 21/25 技能已匹配 (覆盖 5/5 阶段)
✅ 占位符: 全部已替换为实际值

总结: 8/8 全部通过
```

## 配置参数

用户可通过以下方式覆盖默认行为：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--skills-path` | `~/.codebuddy/skills/` | 技能扫描路径 |
| `--output-dir` | `.codebuddy/rules/` | 规则文件输出目录（CodeBuddy 规范位置） |
| `--arch-file` | 自动检测 | 指定架构文件路径 |
| `--progress-file` | `progress.md` | 指定进度文件路径 |
| `--language` | 自动检测 | 强制指定项目语言 |
| `--dry-run` | `false` | 仅输出检测结果，不生成文件 |

## 建议

### 建议 1: 将「技能发现」做成显式步骤而非隐式逻辑

当前实现已将技能扫描作为独立的 Step 3。建议进一步增强：不仅按语言前缀匹配，还应解析 `SKILL.md` 的 `description` 字段进行语义匹配。例如某个名为 `my-deploy-tool` 的自定义技能，其 description 中包含 "deploy""CI/CD"，应自动归类到 Phase 4。

**理由**: 用户可能自行编写或安装非标准命名的技能，纯前缀匹配会遗漏这些技能。

**预期收益**: 技能发现覆盖率从 ~80% 提升至 ~95%，减少用户手动补充。

### 建议 2: 规则文件按阶段拆分，而非单一大文件

当前已将规则拆分为 `project-rules/RULE.mdc` / `phase-rules/RULE.mdc` / `skills-manifest/RULE.mdc` 三个文件。建议进一步将 `phase-rules/RULE.mdc` 中的每个 Phase 拆分为独立规则文件（`.codebuddy/rules/phase-0/` ~ `.codebuddy/rules/phase-4/`），由 AI 按当前进度自动加载对应阶段文件。

**理由**: 当项目进行到 Phase 3 时，AI 不需要一次性加载 Phase 0-4 全部内容，按需加载可节省大量 token。

**预期收益**: 大项目中每次会话的规则 token 减少 60-70%，且规则文件更聚焦、维护更方便。

### 建议 3: 加入「规则自检」机制

当前已实现 Step 6 规则自检。建议在此基础上加入**周期性自检**：每次会话开始时，AI 自动验证规则文件引用路径是否仍然有效（是否存在新的架构文件、进度文件是否过时），并在进度文件的阻塞项中报告发现的偏差。

**理由**: 项目在开发过程中文件结构可能变化（如 `ARCHITECTURE.md` 重命名为 `docs/ARCHITECTURE.md`），但规则文件可能未及时更新引用路径，导致 AI 读取失败。

**预期收益**: 消除"规则文件过期导致 AI 无法找到关键文档"的隐性 bug，将文件路径失效的发现时间从"AI 报错时"提前到"会话开始时"。
