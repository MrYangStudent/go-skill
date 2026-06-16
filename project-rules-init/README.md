# project-rules-init

> 项目规则初始化器 — 自动检测项目语言和框架，生成会话启动指引、阶段开发规则和技能匹配清单。

## 功能

每次从零启动一个 AI 辅助编码项目时，自动完成：

1. **语言/框架检测** — 扫描 `go.mod` / `pyproject.toml` / `package.json` 等标识文件
2. **规则文件生成** — 在 `.codebuddy/rules/` 下生成三个 `RULE.mdc`（项目规则 + 阶段流程 + 技能清单）
3. **技能匹配矩阵** — 扫描已安装技能，生成按阶段匹配的推荐清单
4. **规则自检** — 验证生成的文件完整性、占位符替换、技能覆盖率

## 触发方式

在 CodeBuddy 对话中使用以下关键词触发：

- "初始化项目规则"
- "生成项目规则"
- "setup project rules"
- "init rules"
- "项目初始化"
- "新建项目"

## 生成规则目录结构

```
.codebuddy/rules/
├── project-rules/
│   └── RULE.mdc          ← 项目规则（总是加载）
├── phase-rules/
│   └── RULE.mdc          ← 阶段流程（总是加载）
└── skills-manifest/
    └── RULE.mdc          ← 技能清单（智能体请求）
```

## 要求

- **运行环境**: CodeBuddy IDE
- **权限**: 需要读写项目目录和 `~/.codebuddy/skills/` 目录
- **前置条件**: 项目根目录存在语言标识文件（如 `pyproject.toml`）
