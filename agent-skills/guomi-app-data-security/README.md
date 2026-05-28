# guomi-app-data-security

代码仓库“应用和数据安全”方向的密评式审阅标准。

## Read Order

1. `SKILL.md`
2. `standards.md`
3. `output-template.md`
4. `examples.md`

## 文件说明

- `SKILL.md`：Skill 入口说明
- `standards.md`：评测标准与判定规则
- `output-template.md`：Findings 和报告模板
- `examples.md`：示例提示词、示例 Findings、常见误用

## 使用要点

- 先看 `SKILL.md` 的硬约束和执行顺序。
- 再看 `standards.md` 的判定口径。
- 输出前按 `output-template.md` 自查。
- 输出风格拿不准时，用 `examples.md` 对照。

## 设计原则

- Skill 只定义标准，不实现执行器。
- Skill 只约束审阅时应该做什么、不应该做什么。
- Skill 要求结论必须有证据支撑。
- Skill 允许人工复核，不鼓励强行定性。
