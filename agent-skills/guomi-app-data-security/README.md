# guomi-app-data-security

这是一个文档型 Skill，用于定义代码仓库“应用和数据安全”方向的密评式审阅标准。

## 文件说明

- `SKILL.md`：Skill 入口说明
- `standards.md`：评测标准与判定规则
- `output-template.md`：Findings 和报告模板
- `examples.md`：示例提示词、示例 Findings、常见误用

## 设计原则

- Skill 只定义标准，不实现执行器。
- Skill 只约束审阅时应该做什么、不应该做什么。
- Skill 要求结论必须有证据支撑。
- Skill 允许人工复核，不鼓励强行定性。

## 预期使用方式

读取目标仓库后，按本 Skill 的标准完成审阅和报告输出。
