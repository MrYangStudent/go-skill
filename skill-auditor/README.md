# Skill Auditor 使用指南

> Skill 项目合规性审核工具 - 基于 Claude Skills 开发完全指南

## 功能介绍

Skill Auditor 用于检查 Skill 项目是否符合 Claude CodeBuddy Skill 开发规范，提供全面的合规性检查。

## 核心检查项

### 1. SKILL.md 必需结构

| 检查项 | 要求 | 状态 |
|--------|------|------|
| YAML Frontmatter | 文件必须以 `---` 开头 | 必须 |
| name | 小写+连字符，最大64字符 | 必须 |
| description | 20-1024字符，第三人称 | 必须 |
| triggers | 至少1个触发词 | 必须 |

### 2. scripts/ 脚本规范

| 规范 | 说明 |
|------|------|
| 文档字符串 | 每个脚本必须有清晰的文档说明 |
| 错误处理 | 完善的 try/except 处理 |
| 输入验证 | 验证必需字段 |
| JSON I/O | 标准输入/输出 JSON 格式 |
| 类型注解 | 使用类型提示 |

**使用场景**：
- ✅ 确定性计算
- ✅ 复杂算法
- ✅ 数据验证
- ❌ 灵活判断（用指令）

### 3. reference/ 资源组织

```
reference/
├── api_docs.md              # API 文档
├── examples.md              # 使用示例
├── troubleshooting.md        # 故障排除
├── templates/               # 模板文件
├── data/                    # 示例数据
└── configs/                # 配置文件
```

### 4. 反模式检测

| 反模式 | 问题 | 修复 |
|--------|------|------|
| overly_verbose | 过度解释基础知识 | 删除冗余说明 |
| time_sensitive | 包含时效性信息 | 使用动态获取 |
| windows_path | Windows 路径格式 | 使用正斜杠 |
| no_examples | 缺少具体示例 | 添加实际用例 |
| skill_too_long | SKILL.md >500行 | 拆分到 reference/ |

## 快速开始

### 审核 Skill 项目

```
用户: 帮我审核 lazy-expense-skill
AI: 开始审核...
    
    [检查] SKILL.md 存在 ✅
    [检查] YAML Frontmatter ✅
    [检查] name 字段: lazy-expense-tracker ✅
    [检查] description ✅ (42 字符)
    [检查] triggers ✅ (9 个触发词)
    [检查] scripts/ ⚠️ (未使用脚本)
    [检查] reference/ ⚠️ (未使用参考资源)
    
    [结果] ✅ 审核通过！5/5 必需项通过
```

## 三层结构规范

```
my-skill/
├── SKILL.md          # 📋 SOP - 固化程序性知识
├── scripts/          # 🔧 工具 - 确定性可靠函数
│   ├── __init__.py
│   └── processor.py
└── reference/        # 📚 资源 - API文档、配置
    ├── api_docs.md
    └── examples.md
```

### 各层职责

| 层级 | 作用 | Token消耗 | 必需 |
|------|------|-----------|------|
| **SKILL.md** | 工作流程和最佳实践 | ~5k | ✅ |
| **scripts/** | 确定性计算处理 | 按需 | ⚪ |
| **reference/** | 详细参考资料 | 按需 | ⚪ |

## 设计模式

### 工作流模式
适用于多步骤、需要验证的任务。

```markdown
## Workflow

### Phase 1: Preparation
- [ ] Validate input
- [ ] Check permissions

### Phase 2: Processing
- [ ] Extract data
- [ ] Transform data

### Phase 3: Validation
- [ ] Run validate.py
- [ ] If fail, retry

**Feedback Loop**: Execute → Validate → Fix → Repeat
```

### 决策树模式
适用于条件分支选择。

```markdown
1. Check format:
   - CSV → process_csv.py
   - JSON → process_json.py
   - Excel → process_excel.py

2. Check size:
   - < 1000 rows → memory
   - > 1000 rows → chunked
```

## 输出格式

```json
{
  "audit_result": "pass",
  "skill_name": "my-skill",
  "checks": [
    {"category": "SKILL.md", "item": "YAML", "status": "pass"},
    {"category": "SKILL.md", "item": "name", "status": "pass"},
    {"category": "scripts", "item": "规范", "status": "skip"}
  ],
  "anti_patterns": [],
  "summary": {
    "total": 8,
    "passed": 8,
    "failed": 0,
    "warnings": 0
  }
}
```

## 常见问题

### Q: 缺少 YAML Frontmatter 怎么办？

在 SKILL.md 开头添加：
```markdown
---
name: my-skill
description: >
  技能描述
triggers:
  - 触发词
---

# 后续内容
```

### Q: name 字段格式要求？

```
✅ my-skill-name (小写+连字符)
❌ MySkill (大写)
❌ my_skill (下划线)
❌ my.skill (点号)
```

### Q: SKILL.md 太长怎么办？

拆分到 reference/ 目录：
- SKILL.md < 500 行
- reference/DETAILED.md (详细文档)

### Q: 什么时候用 scripts？

```
✅ 用 scripts:
- 确定性计算 (ROE = 净利润/股东权益)
- 数据验证 (检查必填字段)
- 文件处理 (CSV解析)

❌ 用指令:
- 灵活判断 ("看起来不错")
- 自然语言生成 (写报告)
```

## 开发流程

```
确定需求 → 设计结构 → 编写SKILL.md → 开发脚本 → 组织资源 → 测试 → 优化 → 部署
```

## 参考资源

- [Claude Skills 开发完全指南](https://github.com/sanshao85/claude-skills-guide)
- [CodeBuddy 文档](https://www.codebuddy.ai/docs)
- [YAML 规范](https://yaml.org/spec/1.2.2/)
- [语义化版本](https://semver.org/lang/zh-CN/)
