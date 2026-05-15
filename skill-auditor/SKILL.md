---
name: skill-auditor
description: >
  Skill 项目合规性审核工具。检查和验证 Skill 项目是否符合 Claude CodeBuddy Skill 开发规范，
  包括 SKILL.md 格式、manifest.json 结构、文件完整性、脚本规范、资源组织等。
  Use when user wants to audit, review, validate, or check if a skill follows the proper format
  and structure guidelines.
triggers:
  - 审核skill
  - 检查skill
  - skill合规
  - skill规范
  - skill格式
  - skill检查
  - 验证skill
  - skill审查
  - audit skill
  - review skill
  - validate skill
  - check skill format
  - skill structure
---

# Skill Auditor - Skill 合规性审核工具

> 自动检查 Skill 项目是否符合 Claude CodeBuddy 开发规范

## 概述

本技能提供 Skill 项目合规性自动审核功能，基于 Claude Skills 开发完全指南的标准。

## Skill 三层结构规范

每个 Skill 必须遵循三层结构：

```
my-skill/
├── SKILL.md          # 📋 SOP（标准作业程序）- 专家的行动剧本
├── scripts/          # 🔧 工具（Tools）- 确定性的可靠函数
│   └── processor.py
└── reference/        # 📚 资源（Resources）- API 文档、配置文件
    └── guide.md
```

| 层级 | 作用 | 必需 |
|------|------|------|
| **SKILL.md** | 固化程序性知识 | ✅ 必须 |
| **scripts/** | 封装操作性知识 | ⚪ 可选 |
| **reference/** | 精选知识库 | ⚪ 可选 |

## 渐进式披露机制

| 层级 | 内容 | Token 消耗 |
|------|------|------------|
| **Level 1** | `name` + `description` | ~100 tokens/skill |
| **Level 2** | SKILL.md 主体内容 | ~5k tokens |
| **Level 3** | scripts + reference 文件 | 按需引用 |

## 合规性检查清单

### 1. SKILL.md 必需结构

```markdown
---
name: <skill-name>              # 唯一标识，小写字母和连字符
description: >                 # 描述，AI 触发匹配用
  <描述内容>
triggers:                       # 触发词列表
  - 触发词1
  - 触发词2
---

# Skill 内容...
```

### 2. name 字段规范

| 规则 | 正确 | 错误 |
|------|------|------|
| 小写字母 | ✅ `my-skill` | ❌ `MySkill` |
| 数字允许 | ✅ `pdf-v2` | ❌ |
| 连字符分隔 | ✅ `skill-auditor` | ❌ `skill_auditor` |
| 最大长度 | 64 字符 | |
| 禁止 | XML标签、空格、下划线 | ❌ `<skill>` |

### 3. description 字段规范

| 规则 | 要求 |
|------|------|
| 最大长度 | 1024 字符 |
| 必须包含 | "做什么" + "何时用" |
| 语气 | 第三人称 |
| 触发词 | 包含中英文触发词 |

**好的示例**：
```yaml
description: >
  财务比率计算工具，支持 ROE、ROA、P/E 等指标。
  Use when analyzing company performance or evaluating investments.
```

**坏的示例**：
```yaml
# ❌ 太简短
description: 财务分析工具

# ❌ 第一人称
description: 我可以帮助你分析财务数据

# ❌ 太泛化
description: Helps with finance stuff
```

### 4. scripts/ 脚本开发规范

**使用脚本的场景**：
- ✅ 确定性计算
- ✅ 复杂算法
- ✅ 数据验证
- ✅ 文件处理

**使用指令的场景**：
- ❌ 灵活判断
- ❌ 自然语言生成

**脚本模板**：
```python
#!/usr/bin/env python3
"""
Script Name: <name>.py
Description: 功能描述
"""

import sys
import json
from typing import Dict, Any

def process(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理函数。
    
    Args:
        input_data: 输入数据字典
        
    Returns:
        处理结果字典
        
    Raises:
        ValueError: 参数无效时
    """
    # 验证输入
    required_fields = ['field1', 'field2']
    for field in required_fields:
        if field not in input_data:
            raise ValueError(f"Missing required field: {field}")
    
    # 处理逻辑
    result = {...}
    return result

def main():
    """主入口函数"""
    try:
        input_data = json.loads(sys.stdin.read())
        result = process(input_data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        error_result = {'status': 'error', 'message': str(e)}
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**脚本规范**：
1. 清晰的文档字符串
2. 完善的错误处理
3. 输入验证
4. JSON 输入/输出
5. 类型注解

### 5. reference/ 资源组织规范

```
reference/
├── api_docs.md              # API 文档
├── examples.md              # 使用示例
├── troubleshooting.md       # 故障排除
├── templates/                # 模板文件
│   ├── report_template.xlsx
│   └── contract_template.docx
├── data/                    # 示例数据
│   └── sample_input.json
└── configs/                 # 配置文件
    └── default_config.yaml
```

**使用 Reference 的场景**：
- ✅ API 文档
- ✅ 配置模板
- ✅ 示例数据
- ✅ 详细指南（过长的技术文档）
- ✅ 模板文件

### 6. 文件命名规范

| 文件类型 | 规范 | 示例 |
|----------|------|------|
| Skill 目录 | 小写+连字符 | `skill-auditor` |
| 脚本文件 | 小写+下划线 | `main_processor.py` |
| 参考文档 | 小写+下划线 | `api_reference.md` |

### 7. 设计模式

#### 工作流模式（Workflow Pattern）
适用于多步骤、需要验证的任务。

```markdown
## Document Processing Workflow

### Phase 1: Preparation
- [ ] Validate input file format
- [ ] Check file size and permissions

### Phase 2: Processing
- [ ] Extract text content
- [ ] Parse structured data

### Phase 3: Validation
- [ ] Run `validate_output.py`
- [ ] If validation fails, return to Phase 2

**Feedback Loop**: Execute → Validate → Fix → Repeat
```

#### 决策树模式（Decision Tree Pattern）
适用于根据条件选择不同路径的任务。

```markdown
1. Check input format:
   - If CSV → Use `process_csv.py`
   - If JSON → Use `process_json.py`
   - If Excel → Use `process_excel.py`

2. Check data size:
   - If < 1000 rows → Process in memory
   - If 1000-100K rows → Use chunked processing
```

#### 验证模式（Validation Pattern）
适用于需要确保输出质量的任务。

```markdown
## Output Validation Checklist

### Data Integrity
- [ ] All required fields are present
- [ ] No null values in critical columns
- [ ] Data types are correct

### Calculations
- [ ] Formulas are correct
- [ ] Totals match sum of components
```

## 反模式（Anti-Patterns）检查

### 🔴 反模式 1: 过度解释基础知识

```markdown
# ❌ 不要这样做
Python is a programming language. A function is a reusable block...

# ✅ 应该这样做
Calculate financial ratios using this formula:
ROE = Net Income / Shareholders' Equity
```

### 🔴 反模式 2: 包含时效性信息

```markdown
# ❌ 不要这样做
As of January 2024, the latest version is 2.5.0.
```

### 🔴 反模式 3: 使用 Windows 路径格式

```markdown
# ❌ 不要这样做
reference\\\\templates\\\\report.xlsx

# ✅ 应该这样做
reference/templates/report.xlsx
```

### 🔴 反模式 4: 缺少具体示例

```markdown
# ❌ 不要这样做
This skill can handle various types of financial analysis tasks.

# ✅ 应该这样做
"Calculate ROE for Apple using Q4 2023 data"
```

### 🔴 反模式 5: SKILL.md 过长

```markdown
# ❌ 不要这样做
# SKILL.md (1000+ lines)

# ✅ 应该这样做
# SKILL.md (< 500 lines)
# reference/DETAILED_GUIDE.md
```

## 审核检查项

### 必需项（SKILL.md）

| 检查项 | 说明 | 验证方法 |
|--------|------|----------|
| YAML Frontmatter | 文件必须以 `---` 开头 | 检查文件开头 |
| name 字段 | 小写+连字符，最大64字符 | 正则: `^[a-z][a-z0-9-]*$` |
| description 字段 | 20-1024字符，第三人称 | 长度+语气检查 |
| triggers 字段 | 至少1个触发词 | 数组非空 |

### 推荐项

| 文件 | 说明 | 优先级 |
|------|------|--------|
| manifest.json | 元数据配置 | 推荐 |
| README.md | 使用说明 | 推荐 |
| scripts/ | 可执行脚本 | 按需 |
| reference/ | 参考资源 | 按需 |

### manifest.json 结构（如果存在）

```json
{
  "name": "string (必填，与SKILL.md一致)",
  "version": "string (必填，语义化版本)",
  "description": "string (必填)",
  "triggers": ["array (推荐)"],
  "language": "string (推荐)",
  "commands": ["array (如果适用)"],
  "dependencies": {"object (可选)"}
}
```

## 输出格式

审核完成后输出结构化报告：

```json
{
  "audit_result": "pass|warning|fail",
  "skill_name": "<name>",
  "checks": [
    {
      "category": "SKILL.md",
      "item": "YAML Frontmatter",
      "status": "pass|fail",
      "message": "说明"
    },
    {
      "category": "SKILL.md",
      "item": "name 字段",
      "status": "pass|fail",
      "message": "说明"
    },
    {
      "category": "scripts",
      "item": "脚本规范",
      "status": "pass|warning|skip",
      "message": "说明"
    },
    {
      "category": "reference",
      "item": "资源组织",
      "status": "pass|warning|skip",
      "message": "说明"
    }
  ],
  "anti_patterns": [
    {
      "file": "SKILL.md",
      "line": 45,
      "type": "overly_verbose",
      "suggestion": "简化描述，删除基础知识"
    }
  ],
  "summary": {
    "total": 10,
    "passed": 8,
    "failed": 1,
    "warnings": 1,
    "skipped": 0
  }
}
```

## 审核流程

### Step 1: 检查文件存在性

```bash
ls <skill-dir>/SKILL.md     # 必须存在
ls <skill-dir>/manifest.json # 推荐存在
ls <skill-dir>/README.md     # 推荐存在
ls <skill-dir>/scripts/      # 按需
ls <skill-dir>/reference/    # 按需
```

### Step 2: 验证 YAML Frontmatter

检查 SKILL.md 开头是否为：
```markdown
---
name: xxx
description: xxx
---
```

### Step 3: 检查必需字段

| 字段 | 类型 | 验证 |
|------|------|------|
| name | string | 非空，`^[a-z][a-z0-9-]*$` |
| description | string | 非空，20-1024字符 |
| triggers | array | 非空，至少1个元素 |

### Step 4: 验证 scripts/ 结构（如果存在）

- 检查 `scripts/` 目录结构
- 验证脚本是否有文档字符串
- 检查输入输出格式（JSON）

### Step 5: 验证 reference/ 结构（如果存在）

- 检查目录组织是否规范
- 验证文件名是否使用小写+下划线

### Step 6: 检查反模式

扫描常见反模式并给出修复建议。

## 对话示例

```
用户: 帮我审核一下这个 skill
AI: 请提供 Skill 项目的目录路径，我将进行合规性检查。
    
    [执行] 检查文件结构
    [执行] 验证 YAML Frontmatter
    [执行] 检查必需字段
    [执行] 验证 scripts/ 结构
    [执行] 检查反模式
    [结果] ✅ 审核通过！8/10 项检查通过
    
    警告项:
    - 缺少 manifest.json（推荐添加）
    
    建议优化:
    - SKILL.md 第 45 行过于冗长，考虑拆分为 reference/DETAILED.md
```

```
用户: 检查 skill 格式
AI: 开始审核...
    
    [检查] SKILL.md 存在 ✅
    [检查] YAML Frontmatter ✅
    [检查] name 字段 ✅
    [检查] description ✅ (42 字符)
    [检查] triggers ✅ (9 个触发词)
    [检查] manifest.json ⚠️ (可选文件)
    [检查] scripts/ ⚠️ (未使用脚本)
    [检查] reference/ ⚠️ (未使用参考资源)
    
    [结果] 审核完成：5 passed, 3 warnings
```

## 开发流程参考

```
确定需求 → 设计 Skill 结构 → 编写 SKILL.md → 开发脚本 → 组织资源 → 本地测试 → 多模型测试 → 性能优化 → 部署使用
```

## 参考规范

- Claude Skills 开发完全指南 (GitHub: sanshao85/claude-skills-guide)
- YAML 1.2 规范
- 语义化版本 (semver.org)

## 注意事项

1. **SKILL.md 是核心**: 即使没有 manifest.json，完整的 SKILL.md 也能正常工作
2. **渐进式加载**: 保持 SKILL.md < 500 行，详细内容放入 reference/
3. **简洁为王**: 只包含 Claude 不知道的信息
4. **具体示例**: 用实际用例替代泛化描述
5. **避免时效性**: 不要包含版本号或日期相关的硬编码信息
