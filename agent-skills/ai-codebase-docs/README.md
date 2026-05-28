# ai-codebase-docs

把代码仓库整理成一套约束 AI coding 的核心工程文档。

这个 Skill 参考 `AGENTS.md` 与 Claude Code 一类 agent-first 文档方式，但重点不是写长篇规范，而是沉淀一套基于仓库事实的最小文档集，让 AI 在改代码前先理解系统边界。

默认产物：

- `AGENTS.md`
- `docs/ai/architecture.md`
- `docs/ai/api.md`
- `docs/ai/database.md`
- `docs/ai/deployment.md`
- `docs/ai/open-questions.md`（仅在存在未确认事项时创建）

其中 `AGENTS.md` 默认生成，但只做短索引：告诉 AI 先看什么、去哪找细节、哪些规则不能猜，不重复四类文档正文。

## Read Order

1. `SKILL.md`
2. `standards.md`
3. `output-template.md`
4. `examples.md`

## 文件说明

- `SKILL.md`：Skill 入口、适用场景、硬约束、执行顺序
- `standards.md`：文档集标准、证据规则、`AGENTS.md` 规范
- `output-template.md`：文档模板与落盘要求
- `examples.md`：示例指令、最小合格输出、常见误用

## 设计原则

- Skill 只定义标准，不实现扫描器、解析器或发布工具。
- 文档必须基于仓库事实，不允许脑补系统设计。
- 文档必须覆盖架构、接口、数据库、部署四类边界。
- `AGENTS.md` 默认存在，但必须短、稳、索引化。
- 不确定信息进入 `open-questions`，不要写成事实。
