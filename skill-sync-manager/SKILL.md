---
name: skill-sync-manager
description: >
  Automatically enable/disable CodeBuddy skills based on the current project's
  programming language. Uses .codebuddy/project-language to detect language (python/go),
  then applies prefix-matching rules to toggle skills. Integrates via SessionStart hook
  so skills are always correct when switching projects.
triggers:
  - 同步技能
  - 按语言切换技能
  - sync skills by language
  - auto enable skills
  - 技能管理
---

# Skill Sync Manager — 按项目语言自动管理技能

## 目的

自动根据项目语言启用/禁用对应的 CodeBuddy Skills，减少 token 消耗。

在 Python 项目中自动禁用 17 个 Go 审查/测试技能，在 Go 项目中自动禁用 19 个 Python 技能。
每次会话启动时自动执行，每个不相关技能节省约 **200 tokens**。

### 核心能力

| 能力 | 说明 |
|------|------|
| **语言检测** | `.codebuddy/project-language` + 文件检测 (go.mod / pyproject.toml) |
| **前缀匹配** | `python-*` / `go-*` 前缀规则自动覆盖所有语言专用技能 |
| **YAML Frontmatter** | 通过 `disable: true` 控制 SKILL.md 启用状态 |
| **双向操作** | sync = 当前语言启用/其他禁用；enable-all = 全部启用（跨项目场景） |
| **Hook 集成** | SessionStart Hook 自动同步，无需手动运行 |
| **安全保护** | 始终启用的通用技能（context-compressor, wiki-knowledge-base 等）不受影响 |

## 何时使用

1. **项目切换时** — 从 Python 项目切到 Go 项目，自动调整技能集
2. **新项目初始化** — 新项目放入 `.codebuddy/project-language` 后自动感知
3. **手动切换** — 运行 `py sync_skills.py status` 查看状态，`sync` 手动同步

## 工作原理

```
SessionStart Hook
    │
    ▼
sync_skills.py sync --quiet
    │
    ├─ 检测项目语言 (python / go / unknown)
    │
    ├─ 遍历 ~/.codebuddy/skills/*
    │     ├─ python-* + ALWAYS_ENABLED → 保持启用
    │     ├─ go-*                    → 添加 disable: true
    │     └─ 通用技能                 → 跳过
    │
    └─ 输出: [skills-sync] lang=python | 禁用 17 | ~3400t saved
```

### 语言映射

| 项目语言 | 检测方式 | 启用前缀 | 禁用前缀 |
|----------|---------|---------|---------|
| `python` | `pyproject.toml` / `requirements.txt` | `python-*` | `go-*` |
| `go` | `go.mod` | `go-*` | `python-*` |
| `unknown` | 回退检测 | 全部启用 | 无 |

### 始终启用的通用技能

```
context-compressor   — 上下文压缩
project-rules-init   — 项目规则初始化
wiki-knowledge-base  — Wiki 知识库
prompt-master        — 提示词大师
skill-auditor        — 技能审查器
自己.skill           — 数字分身
```

## 操作流程

### Step 1: 安装

```bash
cd ~/.codebuddy/skills/skill-sync-manager
python scripts/install.py
```

自动在 `~/.codebuddy/settings.json` 注册 SessionStart Hook。

### Step 2: 配置项目语言

在项目根目录创建 `.codebuddy/project-language`，内容为 `python` 或 `go`。

或依赖自动检测：有 `go.mod` 则 go，有 `pyproject.toml` 则 python。

### Step 3: 会话启动自动执行

每次启动新会话时，SessionStart Hook 自动运行 `sync --quiet`，静默同步。

### Step 4: 手动管理

```bash
# 查看当前技能状态
py sync_skills.py status

# 手动同步（verbose 模式）
py sync_skills.py sync

# 预览变更
py sync_skills.py sync --dry-run

# 启用全部技能（跨项目场景）
py sync_skills.py enable-all
```

## 文件结构

```
.codebuddy/skills/skill-sync-manager/
├── SKILL.md                    # 本文件 — 技能定义
├── manifest.json               # 技能元数据
├── cache/                      # 状态缓存目录
└── scripts/
    ├── sync_skills.py          # 核心同步逻辑
    └── install.py              # 多平台安装器
```

## 多平台部署

### CodeBuddy (默认)
```bash
python install.py --codebuddy
```
注册到 `~/.codebuddy/settings.json` → SessionStart Hook

### Claude Code
```bash
python install.py --claude
```
注册到 `~/.claude/settings.json` → SessionStart Hook

### OpenAI Codex
```bash
python install.py --codex
```
注册到 `~/.codex/hooks.json` → SessionStart Hook

### 跨平台安装
```bash
python install.py --all      # 全部平台
python install.py            # 自动检测
```

## 安装脚本选项

| 选项 | 说明 |
|------|------|
| `--codebuddy` | 仅安装 CodeBuddy |
| `--claude` | 仅安装 Claude Code |
| `--codex` | 仅安装 OpenAI Codex |
| `--all` | 安装所有平台 |
| `--dry-run` | 预览不写入 |
| `--uninstall` | 移除 Hook 配置 |
| `--validate` | 验证技能完整性 |

## 注意事项

1. **YAML Frontmatter 安全**：仅操作 `disable` 字段，不修改其他 frontmatter 内容
2. **无 Frontmatter 技能**：自动创建 `---\ndisable: true\n---\n` 包裹
3. **启用时恢复原格式**：若 frontmatter 仅含 `disable`，完整移除包裹
4. **Windows GBK 兼容**：内置 `sys.stdout` 编码处理
5. **静默模式**：Hook 调用时仅在有变更时输出一行摘要
6. **幂等操作**：重复 sync 不会重复修改文件
