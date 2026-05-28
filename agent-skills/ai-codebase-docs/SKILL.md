---
name: ai-codebase-docs
description: Use when a task asks to generate repository-backed architecture, API, database, deployment, and AGENTS.md documents that constrain AI coding
---

# AI Codebase Docs

## Overview

这个 Skill 用来把代码仓库沉淀为一套约束 AI coding 的工程文档。

核心产物默认包含五类文件：

1. `AGENTS.md`
2. `docs/ai/architecture.md`
3. `docs/ai/api.md`
4. `docs/ai/database.md`
5. `docs/ai/deployment.md`

必要时再补：

- `docs/ai/open-questions.md`

这个 Skill 只定义文档标准与行为边界，不实现扫描器、执行器、渲染器或外部模型调用。

<HARD-GATE>
在使用这个 Skill 时，必须遵守以下规则：

- 不得先写文档、后看仓库。
- 不得把 README 简介复述成核心文档。
- 不得记录未从代码、配置、迁移、接口定义、部署清单或 CI 中观察到的事实。
- 不得把推测出的模块关系、接口契约、表结构、发布流程写成确定事实。
- 必须区分 `observed`、`inferred`、`open_question`。
- 如果任务要求“生成文档”，必须实际创建文档文件，不能只在对话中给提纲。
- `AGENTS.md` 默认生成，但必须保持简短，只做索引和阅读顺序，不复制其他文档正文。
- 所有高风险约束都必须有仓库证据来源。
</HARD-GATE>

## When to Use

在以下情况使用：

- 用户要求“把 codebase SOP 化”。
- 用户要求“生成约束 AI coding 的文档”。
- 用户要求补齐架构、接口、数据库、部署文档。
- 需要给 AI 提供稳定的仓库事实入口。

不要用于：

- 面向客户或市场的产品介绍
- 脱离仓库事实的通用工程规范
- 动态探测、线上发布审批、CMDB 替代
- 在 Skill 内实现解析器或自动化执行链

## Required Order

按以下顺序执行，不要跳步：

1. 先看仓库根目录、README、构建文件、包管理文件、CI 配置。
2. 再看主要源码目录，识别服务、模块、入口点和依赖边界。
3. 提取接口来源，例如路由定义、handler、OpenAPI、proto、GraphQL schema。
4. 提取数据库来源，例如 ORM 模型、DDL、迁移、seed、repository/dao。
5. 提取部署来源，例如 Dockerfile、Compose、Kubernetes、Helm、Terraform、发布脚本、CI/CD。
6. 先写四类核心文档，再写 `AGENTS.md` 索引。
7. 不能确认的事项写入 `open-questions`。
8. 交付前检查各文档之间是否互相矛盾。

## Default Deliverables

默认文档集如下：

1. `AGENTS.md`
2. `docs/ai/architecture.md`
3. `docs/ai/api.md`
4. `docs/ai/database.md`
5. `docs/ai/deployment.md`
6. `docs/ai/open-questions.md`（仅在存在未确认事项时创建）

规则：

- 四类核心文档承载系统事实。
- `AGENTS.md` 承载阅读顺序、文档索引和少量硬规则。
- 小仓库可以合并四类文档中的部分内容，但 `AGENTS.md` 仍默认存在。

## Quick Reference

| 场景 | 默认动作 |
|---|---|
| 需要约束 AI 改代码 | 先补齐四类核心文档，再生成 `AGENTS.md` |
| 只有部分仓库可见 | 明确范围，缺失部分进入 `open-questions` |
| 看到了 OpenAPI/proto/路由定义 | 作为接口文档高置信证据 |
| 看到了迁移/DDL/ORM 模型 | 作为数据库文档高置信证据 |
| 看到了 Docker/K8s/CI 发布脚本 | 作为部署文档高置信证据 |
| 只能从命名推测职责 | 保守表达或转入 `open-questions` |

## Review Checklist

在结束前逐项确认：

- [ ] `AGENTS.md` 已创建或更新。
- [ ] 架构文档已创建或更新。
- [ ] 接口文档已创建或更新。
- [ ] 数据库文档已创建或更新。
- [ ] 部署文档已创建或更新。
- [ ] `AGENTS.md` 足够短，只包含索引和核心规则。
- [ ] 文档中的系统关系、接口、表结构、部署流程都来自已观察证据。
- [ ] 不确定内容已进入 `open-questions`。
- [ ] 各文档之间没有冲突。

## Common Failures

- 把 README 里的项目介绍当成架构文档。
- 只列接口路径，不写契约来源和实现位置。
- 只说“使用 MySQL”，却没有模型、迁移或访问层说明。
- 只说“通过 Docker 部署”，却没有部署单元、配置来源和发布线索。
- 把 `AGENTS.md` 写成另一份长篇总说明。
- 对看不到的模块关系、鉴权链路或发布流程强行下结论。

## Supporting Files

- `standards.md`：文档标准与证据规则
- `output-template.md`：文档模板与落盘要求
- `examples.md`：示例指令、示例输出、禁止写法

## Output Gate

在输出任何文档前，确认三件事：

1. 内容是否基于已查看仓库事实。
2. 内容是否能约束 AI 对系统边界的理解。
3. `AGENTS.md` 是否保持为短索引，而不是重复正文。

任一答案为“否”，就不要写成正式文档。
