# Prompt Master - 提示词大师

> 基于吴恩达《AI Prompting for Everyone》课程精华的对话式提示词构建引擎

## 核心能力

| 能力 | 说明 |
|------|------|
| 🏗️ **对话式构建** | 六步框架引导：角色→背景→目标→约束→格式→示例 |
| 🔍 **诊断优化** | 六维诊断 + 针对性追问 + 输出优化版提示词 + 改动说明 |
| 💡 **头脑风暴** | 多角度发散、迭代聚焦、角色切换、魔鬼代言人 |
| 🔄 **写作工作流** | 先大纲后正文、消除AI腔、禁用表达清单 |
| 🎯 **AI 推理** | 多标准决策分析、方案比较、风险评估 |
| 📋 **AI 评审** | Rubric 六维度评审、先证据再打分、跨模型检查 |
| 🚫 **反迎合** | Sycophancy 识别与应对、中立提问技巧 |
| 🎨 **图像生成** | 结构化 Prompt 构建（主体/场景/风格/细节） |
| 🧩 **应用构建** | Goal/Input/Output 公式生成迷你应用 |
| 📊 **数据分析** | AI 写代码运行分析，非凭感觉回答 |
| 🌐 **信息检索** | 预训练知识 vs 网络搜索 vs 深度研究对比 |

## 触发方式

直接输入以下任一关键词即可激活：

```
提示词 / 写提示词 / 优化prompt / 提示词工程 / prompt engineer
头脑风暴 / 脑暴 / AI评审 / 迎合性 / 反迎合
写作工作流 / 减少AI腔 / AI推理 / 方案比较
诊断提示词 / 提示词诊断 / 帮我改提示词 / prompt review
图像生成提示词 / 构建应用 / 深度研究 / 魔鬼代言人
```

## 使用场景

- **从零构建提示词**：不知道怎么写 → 六步对话引导你逐步完善
- **已有提示词想优化**：粘贴即可 → 自动诊断 + 追问 + 输出优化版
- **需要创意灵感**：头脑风暴模式，多角度产出，迭代聚焦
- **需要客观评价**：用反迎合技巧获得真实分析，而非虚伪赞同
- **内容质量检查**：AI 评审模式，Rubric 逐项打分，提供修改建议
- **图像/应用生成**：结构化 Prompt 构建，更可控的输出效果

## 文件结构

```
prompt-master/
├── SKILL.md                        # 核心技能定义（SOP）
├── manifest.json                   # 元数据配置
├── README.md                       # 本文件
└── reference/
    ├── prompt_templates.md         # 22 个场景模板
    ├── course_reference.md         # 课程知识要点（17 章）
    ├── case_studies.md             # 5 个真实前后对比案例
    ├── advanced_techniques.md      # 进阶技术（ToT/ReAct/链接/元提示/压缩）
    └── scoring_rubric.md           # 提示词质量量化评分体系
```

## 参考来源

- [Datawhale - AI Prompting for Everyone](https://github.com/datawhalechina/ai-prompting-for-everyone)
- 吴恩达《AI Prompting for Everyone》课程 (DeepLearning.AI)

## License

MIT
