# story-ac-author

把自然语言需求转换为敏捷 User Story 与可测试可验收 AC 的 skill。

## Read Order

1. `SKILL.md`
2. `standards.md`
3. `output-template.md`
4. `examples.md`

## 文件说明

- `SKILL.md`：Skill 入口说明，硬约束与必做顺序
- `standards.md`：5 维度澄清规则、AC 4 项硬性检查、Epic 拆分判定、禁止写法
- `output-template.md`：Story、AC、Epic 索引的 Markdown 模板
- `examples.md`：好例 / 坏例 / 典型对话片段 / 反模式

## 使用要点

- 先读 `SKILL.md` 的硬约束和执行顺序。
- 5 维度未全部澄清前不得生成 Story。
- 每条 AC 落盘前必须通过 4 项硬性检查。
- 检测到 Epic 信号时必须先与用户确认拆分方案。
- 任务要求生成文档时，必须实际写入文件，不得只在对话里输出文本。

## 设计原则

- Skill 只定义标准，不实现执行器或解析器。
- Skill 要求所有 Story 必须附澄清证据（澄清记录表）。
- Skill 要求每条 AC 必须可独立验证。
- Skill 拒绝模糊词（"正确地"/"合适的"/"尽快"等）。
- Skill 在落盘前必须过 Output Gate；不过则修正再过，直到全部通过。
