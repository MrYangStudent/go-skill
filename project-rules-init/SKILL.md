---
name: project-rules-init
description: 项目初始化时自动检测语言/框架，生成项目规则文件（架构导航、阶段流程、技能匹配矩阵），并执行规则自检
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

本技能自动化这个过程：
1. 检测项目语言和框架
2. 生成三个规则文件（项目规则 + 阶段流程 + 技能匹配清单）
3. 自动运行规则自检，输出检查报告

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

### Step 2: 生成规则文件

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
1. 阅读 {{ARCHITECTURE_FILE}}
2. 阅读 {{PROGRESS_FILE}}
3. 阅读 .codebuddy/rules/phase-rules/RULE.mdc
4. 查看 .codebuddy/rules/skills-manifest/RULE.mdc（智能体请求时自动加载）
5. 确认上下文后开始工作

## 编码规范
[按 {{PROJECT_LANGUAGE}} 输出对应规范]

## 提交规范
Conventional Commits

## 禁止事项
[通用禁止项 + 特定语言禁止项]

## 会话结束时
更新 progress.md
```

#### 规则 2: `.codebuddy/rules/phase-rules/RULE.mdc`（总是加载）

**YAML frontmatter**：`alwaysApply: true`

**内容模板**：

```markdown
# {{PROJECT_NAME}} — 阶段开发规则

## 通用开发流程
编码 → 静态检查 → 单元测试 → 代码审查

## 阶段概览
| Phase 0 | 环境准备 | ... |
| Phase 1 | 核心开发 | ... |
| Phase 2 | 测试 | ... |
| Phase 3 | 审查与文档 | ... |
| Phase 4 | 部署与收尾 | ... |

[每个阶段的入口条件、开发流程（含 {{PROJECT_LANGUAGE}} 的工具命令）、出口标准]

## {{PROJECT_LANGUAGE}} 工具链速查
[按语言的 table]
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

### Step 3: 技能发现与匹配矩阵

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

### Step 4: 规则自检

生成所有文件后，自动执行以下检查：

| 检查项 | 检查内容 | 通过条件 |
|--------|----------|----------|
| 架构文件 | `{{ARCHITECTURE_FILE}}` 是否存在 | 文件存在 |
| 进度文件 | `{{PROGRESS_FILE}}` 是否存在 | 文件存在；不存在则创建空模板 → ⚠️ |
| 计划文件 | `{{PLAN_FILE}}` 是否存在 | 文件存在 |
| 规则目录 | `.codebuddy/rules/` 下是否有 3 个 RULE.mdc | 3 个子目录各含 RULE.mdc |
| 阶段定义 | `phase-rules/RULE.mdc` 是否包含入口/出口标准 | 每个 Phase 有 entry + exit |
| 技能覆盖 | 所有阶段是否至少有一个匹配技能 | 覆盖率 ≥ 80% |
| 占位符 | 所有 RULE.mdc 中的 `{{VAR}}` 是否已替换 | 无未填充的占位符 |

**输出格式**：

```
═══ 规则自检报告 ═══
✅ 架构文件: ARCHITECTURE.md 存在
✅ 进度文件: progress.md 存在
✅ 计划文件: PLAN.md 存在
✅ 规则目录: .codebuddy/rules/ 下 3 个 RULE.mdc 已生成
✅ 阶段定义: 5 个阶段均有入口/出口标准
✅ 技能覆盖: 21/25 技能已匹配 (覆盖 5/5 阶段)
✅ 占位符: 全部已替换为实际值

总结: 7/7 全部通过
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

当前已将规则拆分为 `project-rules.md` / `phase-rules.md` / `skills-manifest.md` 三个文件。建议进一步将 `phase-rules/RULE.mdc` 中的每个 Phase 拆分为独立规则文件（`.codebuddy/rules/phase-0/` ~ `.codebuddy/rules/phase-4/`），由 AI 按当前进度自动加载对应阶段文件。

**理由**: 当项目进行到 Phase 3 时，AI 不需要一次性加载 Phase 0-4 全部内容，按需加载可节省大量 token。

**预期收益**: 大项目中每次会话的规则 token 减少 60-70%，且规则文件更聚焦、维护更方便。

### 建议 3: 加入「规则自检」机制

当前已实现 Step 4 规则自检。建议在此基础上加入**周期性自检**：每次会话开始时，AI 自动验证规则文件引用路径是否仍然有效（是否存在新的架构文件、进度文件是否过时），并在进度文件的阻塞项中报告发现的偏差。

**理由**: 项目在开发过程中文件结构可能变化（如 `ARCHITECTURE.md` 重命名为 `docs/ARCHITECTURE.md`），但规则文件可能未及时更新引用路径，导致 AI 读取失败。

**预期收益**: 消除"规则文件过期导致 AI 无法找到关键文档"的隐性 bug，将文件路径失效的发现时间从"AI 报错时"提前到"会话开始时"。
