---
name: readme-writer
description: >
  README 文档编写与完整性检查技能。当用户要求编写 README、检查 README 完整性、
  补全 README 缺失内容、或新增项目需要生成 README 时触发。基于 12 项内容块标准
  （标题→摘要→徽章→目录→背景→安装→用法→流程→总结→参考→贡献者→版权）进行审查。
  作者信息首次使用时引导用户输入，保存在技能安装目录下的 user-config.json。
  源码仓库通过 .gitignore 排除该文件，确保分享时不含用户数据。
triggers:
  - 写README
  - 生成README
  - 检查README
  - README完整性
  - 补全README
  - 完善README
  - README规范
  - 生成项目文档
  - write README
  - README checklist
  - 项目README
  - 初始化README
  - 新建README
---

# README Writer — README 文档编写与完整性检查

> 让每个项目都有一份结构完整、信息齐全的 README。

## 核心能力

| 能力 | 说明 |
|------|------|
| **完整性检查** | 对照 12 项内容块清单，逐项检查 README 是否完整 |
| **自动补全** | 根据项目代码自动推断缺失内容并填入 |
| **徽章生成** | 自动构建 shields.io 徽章（License/Stars/Language/Version） |
| **双向语言** | 中英文 README 同步生成和更新 |
| **作者持久化** | 首次引导输入，存入技能目录 `user-config.json`，后续自动引用 |

---

## 12 项 README 内容块清单

按优先级排列，检查时逐项确认：

| # | 内容块 | 必需 | 说明 |
|---|--------|:---:|------|
| 1 | **项目标题** | ✅ | 一级标题，项目名称 |
| 2 | **语言切换** | ✅ | 中英文跳转链接（多语言项目） |
| 3 | **项目摘要** | ✅ | 1-3 句话说明项目是什么、做什么 |
| 4 | **项目徽章** | ⭐ | shields.io 徽章：License、Stars、Language、Version |
| 5 | **目录 (TOC)** | ⭐ | 长 README 必备，建议 markdown-all-in-one 自动生成 |
| 6 | **项目背景** | ⭐ | 为什么创建、解决什么问题 |
| 7 | **安装/环境要求** | ✅ | 如何安装依赖、环境要求（OS/语言版本/硬件） |
| 8 | **使用方法** | ✅ | 快速开始、常用命令、代码示例 |
| 9 | **项目架构/流程** | ⭐ | 架构图、工作流、目录结构说明 |
| 10 | **贡献指南** | ⭐ | 如何参与贡献、代码规范、PR 流程 |
| 11 | **作者/贡献者** | ✅ | GitHub/Gitee 链接、贡献者列表 |
| 12 | **版权声明** | ✅ | License 类型 |

> ✅ = 必须 | ⭐ = 强烈推荐

---

## 工作流程

### Step 1: 加载作者信息

作者信息存储在**技能安装目录下的 `user-config.json`**（与 `SKILL.md` 同级）。

**首次使用**：配置文件不存在 → 询问用户：

> 请提供你的作者信息（只需提供一次）：
> - GitHub 用户名或完整地址
> - Gitee 用户名或完整地址（可选）
> - 展示名称

收集后在技能目录下创建 `user-config.json`：

```json
{
  "github": "https://github.com/<username>",
  "gitee": "https://gitee.com/<username>",
  "author": "<display-name>"
}
```

**后续使用**：直接读取技能目录下的 `user-config.json`，不再询问。

> ⚠️ `user-config.json` 已加入 `.gitignore`，源码仓库不含用户数据。安装技能到本地后首次运行自动创建。

### Step 2: 扫描目标 README

读取目标项目的 README 文件（支持 `README.md` / `README_zh.md`），
对照 12 项清单逐项检查，生成缺失报告：

```
📋 README 完整性检查报告
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1. 项目标题
✅ 2. 语言切换
❌ 3. 项目徽章        ← 缺失
✅ 4. 目录
❌ 5. 作者/贡献者      ← 缺失
...
```

### Step 3: 补全缺失内容

根据缺失项和项目代码自动生成内容：

**徽章模板**：
```markdown
<a href="https://github.com/<user>/<repo>"><img src="https://img.shields.io/github/stars/<user>/<repo>?style=flat-square" alt="Stars"></a>
<a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
```

**作者链接模板**：
```markdown
## 作者

- GitHub: [@username](https://github.com/username)
- Gitee: [@username](https://gitee.com/username)
```

**安装说明模板**：
如果是 skills 仓库，说明 clone 后按 CodeBuddy skill 规范使用即可；
如果是 Go 项目，说明 `go install` / `go build` 步骤；
如果是 Python 项目，说明 `pip install` / `conda` 步骤。

### Step 4: 同步多语言版本

如果存在 `README_zh.md`，同步更新对应内容。
中英文 README 的结构保持一致，内容分别本地化。

### Step 5: 汇报结果

输出最终报告，列出补充了哪些内容。

---

## 文件结构

```
readme-writer/
├── SKILL.md                   # 本文件 — 技能定义
├── .gitignore                 # 排除 user-config.json（源码仓库干净）
├── user-config.json           # 作者信息（安装后首次运行时自动创建，不入 git）
└── references/
    └── checklist.md           # 12 项内容块详细说明（通用参考）
```

## 参考规范

- [README-GUIDE](https://github.com/AiArt-Gao/README-GUIDE) — 学术团队的 README 标准化框架
- [shields.io](https://shields.io/) — 徽章生成服务
- [makeareadme.com](https://www.makeareadme.com/) — README 最佳实践

## 注意事项

1. **用户数据不入 git**：`user-config.json` 由 `.gitignore` 排除，源码仓库安全可分享。安装后首次运行自动创建
2. **作者信息只问一次**：配置文件存在后永久复用，除非用户主动要求修改
3. **不修改已有正确内容**：只补全缺失项，不重写已存在的内容
4. **推断优于询问**：能从项目代码推断的信息（License 类型、语言版本等）直接填入
5. **中英文同步**：修改英文 README 时同时更新中文版对应内容
6. **徽章使用 shields.io**：统一风格，避免多种来源混搭
