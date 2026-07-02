# README 完整性检查清单

> 参考 [README-GUIDE](https://github.com/AiArt-Gao/README-GUIDE) 框架和开源社区最佳实践。

---

## 1. 项目标题

**格式**：一级标题 `# Project Name (short-tag)`

**示例**：
```markdown
# Go Engineering Skills (go-skill)
```

**检查要点**：
- 是否使用一级标题
- 是否包含简短标签/别名
- 名称是否反映项目内容

---

## 2. 语言切换链接

**格式**：标题下方紧跟语言切换

**示例**：
```markdown
[English](./README.md) | [中文](./README_zh.md)
```

**检查要点**：
- 多语言项目必须有
- 链接地址正确
- 放在标题正下方

---

## 3. 项目摘要

**格式**：1-3 句话，项目是什么 + 核心价值

**示例**：
```markdown
A comprehensive engineering skill set covering the complete development
lifecycle from code development, testing, quality review to documentation
generation.
```

**检查要点**：
- 简洁（<100 字）
- 覆盖项目核心用途
- 放在标题和徽章之间

---

## 4. 项目徽章 (Badges)

**格式**：shields.io 静态/动态徽章，markdown 或 HTML

**常用徽章模板**：
```markdown
![License](https://img.shields.io/badge/license-MIT-blue)
![Go Version](https://img.shields.io/badge/Go-1.21+-00ADD8?logo=go)
![Stars](https://img.shields.io/github/stars/<user>/<repo>?style=flat-square)
```

**按项目类型推荐**：
| 项目类型 | 推荐徽章 |
|----------|----------|
| GitHub 仓库 | Stars, License, Language, Last Commit |
| Go 项目 | Go Version, Go Report Card |
| Python 项目 | Python Version, PyPI Version |
| Skills 仓库 | License, Skills Count |
| npm 包 | npm Version, Downloads |

**检查要点**：
- 徽章可点且链接正确
- 颜色统一（参考 shields.io 色系）
- 不超过 6 个（避免杂乱）

---

## 5. 目录 (Table of Contents)

**格式**：Markdown 自动生成或手动维护

**生成方式**：
- VSCode: 安装 `markdown-all-in-one` 插件 → `Ctrl+Shift+P` → `Create Table of Contents`
- 手动: `- [章节名](#锚点)`

**检查要点**：
- README > 200 行必须有
- 锚点与标题匹配
- 层级不超过 3 级

---

## 6. 项目背景

**内容**：
- 为什么创建这个项目
- 解决了什么问题
- 与现有方案的区别

**检查要点**：
- 说明"为什么"而非仅"是什么"
- 适合目标受众理解

---

## 7. 安装 / 环境要求

**内容**：
```
## 安装

### 环境要求
- Go 1.21+
- ...

### 安装步骤
```bash
git clone https://github.com/user/repo.git
cd repo
go build ./...
```
```

**检查要点**：
- 列出语言/运行时版本要求
- 列出系统依赖
- 提供可复制粘贴的安装命令
- 如果无需安装（如 skills 仓库），明确说明

---

## 8. 使用方法

**内容**：
- 快速开始（最小可用示例）
- 常用命令
- 配置说明

**检查要点**：
- 快速开始放在最前面
- 代码块标注语言
- 包含预期输出示例

---

## 9. 项目架构 / 工作流

**格式**：ASCII 图、Mermaid 图、或目录树

**示例**：
```
project/
├── cmd/          # 入口
├── internal/     # 内部逻辑
└── pkg/          # 可导出包
```

**检查要点**：
- 帮助新用户快速理解项目结构
- 工作流图清晰展示各阶段

---

## 10. 贡献指南

**内容**：
- 如何提交 Issue/PR
- 代码规范
- Commit 格式（如 Conventional Commits）
- 开发环境搭建

**检查要点**：
- 至少包含 PR 基本流程
- 代码规范明确可执行

---

## 11. 作者 / 贡献者

**格式**：
```markdown
## 作者

- GitHub: [@username](https://github.com/username)
- Gitee: [@username](https://gitee.com/username)
- Email: xxx@example.com (可选)
```

**检查要点**：
- GitHub 链接可点击
- 如果有 Gitee 镜像也加上
- 多人项目列出主要贡献者

---

## 12. 版权声明

**格式**：
```markdown
## License

[MIT](./LICENSE) © 2024 Author Name
```

**检查要点**：
- License 类型明确
- LICENSE 文件存在且链接正确
- 年份和作者信息正确

---

## 快速检查命令

在检查 README 时，按此顺序逐项打钩：

```
□ 1. 项目标题        — 一级标题 + 简短标签
□ 2. 语言切换        — 中英文跳转链接
□ 3. 项目摘要        — 1-3 句话，标题下方
□ 4. 项目徽章        — shields.io 3-6 个
□ 5. 目录            — TOC 自动生成
□ 6. 项目背景        — 为什么 + 解决什么
□ 7. 安装要求        — 环境 + 安装命令
□ 8. 使用方法        — 快速开始 + 命令
□ 9. 项目架构        — 目录树或工作流图
□ 10. 贡献指南      — PR 流程 + 代码规范
□ 11. 作者信息      — GitHub/Gitee 链接
□ 12. 版权声明      — License 类型 + 链接
```
