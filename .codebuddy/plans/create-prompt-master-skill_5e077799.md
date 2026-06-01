---
name: create-prompt-master-skill
overview: 基于 datawhalechina/ai-prompting-for-everyone 项目，创建一个"提示词大师"Skill，通过对话式引导逐步生成和优化提示词。
todos:
  - id: create-skill-directory
    content: 创建 prompt-master 技能目录结构的骨架文件（SKILL.md、manifest.json、README.md）
    status: completed
  - id: create-skill-core
    content: 使用 [skill:skill-creator] 参考最佳实践，编写 SKILL.md 核心内容，包括 YAML Frontmatter、六步对话工作流、角色定义和提示词构建逻辑
    status: completed
    dependencies:
      - create-skill-directory
  - id: create-manifest-readme
    content: 使用 [skill:skill-creator] 参考元数据规范，编写 manifest.json 和 README.md
    status: completed
    dependencies:
      - create-skill-directory
  - id: create-reference
    content: 使用 [mcp:sequential-thinking] 系统化推演参考内容结构，创建 reference/prompt-templates.md 模板集和 reference/course-reference.md 课程知识参考
    status: completed
    dependencies:
      - create-skill-core
  - id: audit-skill
    content: 使用 [skill:skill-auditor] 对 prompt-master 技能进行完整的合规性审核并修复问题
    status: completed
    dependencies:
      - create-manifest-readme
      - create-reference
---

## 产品概述

创建一个"提示词大师"技能（Prompt Master），基于吴恩达《AI Prompting for Everyone》课程的精华内容，通过**对话式引导**的方式，帮助用户逐步构建高质量、结构化的提示词。

## 核心功能

- **对话式提示词构建**：通过 AI 引导的交互式对话，一步步收集用户的角色、背景、目的、约束、输出格式和示例等信息，逐步构建完整的提示词
- **结构化框架**：提供固定的六步对话流程：

1. 角色定义 — 确定 AI 扮演的角色定位
2. 背景描述 — 明确任务的上下文信息
3. 目的阐述 — 明确期望达成的具体目标
4. 约束设定 — 定义限制条件、边界和避坑事项
5. 输出格式 — 指定结果呈现方式（表格、列表、JSON 等）
6. 示例引导 — 提供 1-3 个参考示例（可选）

- **提示词优化**：对用户已有的提示词进行分析和优化建议
- **场景模板**：预设写作、编程、数据分析等常见场景的提示词模板
- **知识注入**：融入课程核心知识（角色扮演、思维链、少样本学习、格式控制等技巧）

## 技术方案

### 实现方式

本项目是一个 Claude CodeBuddy Skill 定义项目，不需要编程语言。通过编写结构化 SKILL.md 来定义 AI 助手的技能行为，使 AI 能够按照预设的工作流为用户提供提示词构建服务。

### 技能架构

采用"三层结构"规范，遵循现有技能体系的设计模式：

```
prompt-master/
├── SKILL.md           # [核心] 技能定义 - 对话式提示词构建引擎的工作流程
├── manifest.json      # [元数据] 结构化元数据配置
├── README.md          # [文档] 使用说明和快速入门
└── reference/         # [资源] 参考知识库（避免 SKILL.md 过长）
    ├── prompt-templates.md    # 场景提示词模板集
    └── course-reference.md    # 课程知识要点参考
```

### 核心设计：对话式提示词构建引擎

采用**工作流模式（Workflow Pattern）** 设计，核心流程如下：

```
用户请求 → 六步对话引导 → 结构化信息收集 → 提示词生成 → 用户确认 → 优化迭代
```

各步骤详细设计：

| 步骤 | 对话问题 | 收集信息 | 输出影响 |
| --- | --- | --- | --- |
| 1. 角色定义 | "你希望 AI 扮演什么角色？" | 角色定位 | 决定语气和专业度 |
| 2. 背景描述 | "这个任务在什么场景下进行？" | 上下文信息 | 提供准确语境 |
| 3. 目的阐述 | "你希望达到什么具体目标？" | 目标期望 | 明确产出方向 |
| 4. 约束设定 | "有哪些限制条件或避坑事项？" | 限制条件 | 控制输出范围 |
| 5. 输出格式 | "你希望结果以什么形式呈现？" | 格式要求 | 规范输出结构 |
| 6. 示例引导 | "有没有参考示例或案例？" | 参考样例 | 提供风格参考 |


### 性能与可靠性设计

- **渐进式披露**：SKILL.md 设计为 < 500 行，核心工作流在 SKILL.md 中，详细模板和知识库在 reference/ 目录下按需加载
- **反模式防护**：避免过度解释基础知识，只包含 AI 不知道的提示词工程特有知识
- **错峰处理**：对某一步骤用户无法回答时，提供智能默认值或跳过选项

### 设计模式

采用以下设计模式：

1. **工作流模式** — 六步对话流程，每步有明确的输入验证和输出
2. **决策树模式** — 根据用户需求类型（写作/编程/数据分析等）选择不同的模板和处理路径
3. **验证模式** — 最终生成的提示词经过完整性检查（是否缺角色、缺目标等）

### 知识体系来源

基于 GitHub 项目 datawhalechina/ai-prompting-for-everyone 的三个模块：

- **Module 1（基础概念）**：提示词结构、基本原则、与 AI 交互的入门技巧
- **Module 2（进阶技巧）**：角色扮演、思维链（Chain-of-Thought）、少样本学习（Few-shot）、格式控制等
- **Module 3（实战应用）**：写作、编程、数据分析、资料整理等场景实战

## Agent Extensions

### Skill

- **skill-creator**
- 用途：参考技能创建的最佳实践，确保 prompt-master 技能的结构和内容符合规范
- 预期产出：符合规范的 SKILL.md、manifest.json、README.md 文件
- **skill-auditor**
- 用途：在技能创建完成后，对 prompt-master 技能进行合规性审核
- 预期产出：合规性审核报告，包含 YAML Frontmatter 验证、文件完整性检查等
- **code-explorer**（SubAgent）
- 用途：探索现有技能目录结构、SKILL.md 格式规范、manifest.json 模板（已在研究阶段使用）
- 预期产出：对现有技能规范的完整理解，用于指导新技能的创建

### MCP

- **sequential-thinking**
- 用途：在设计提示词构建引擎的核心工作流时，进行系统化思维推演，确保对话流程的完整性和合理性
- 预期产出：经过充分推演的六步对话框架设计