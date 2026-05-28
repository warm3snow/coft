# 输出模板

<HARD-GATE>
输出任何文档前，必须满足以下条件：

- 默认文档集已创建或更新。
- 文档中的模块、接口、表或模型、部署单元都来自已查看证据。
- 不确定项已单列，不存在伪装成事实的推断。
- `AGENTS.md` 保持简短，只做索引和入口规则。
</HARD-GATE>

## 0. 文件落盘要求

默认应创建以下文件：

- `AGENTS.md`
- `docs/ai/architecture.md`
- `docs/ai/api.md`
- `docs/ai/database.md`
- `docs/ai/deployment.md`

存在未确认事项时，再创建：

- `docs/ai/open-questions.md`

## 1. AGENTS.md 模板

`AGENTS.md` 默认生成，建议保持为索引页：

```markdown
# AGENTS

## Start Here
1. Read `docs/ai/architecture.md`.
2. Read `docs/ai/api.md` before changing handlers, DTOs, SDKs, or payloads.
3. Read `docs/ai/database.md` before changing models, migrations, queries, or repositories.
4. Read `docs/ai/deployment.md` before changing config, Docker, CI, or manifests.
5. Check `docs/ai/open-questions.md` if present.

## Document Index
- `docs/ai/architecture.md`: system shape, modules, entrypoints, dependencies.
- `docs/ai/api.md`: interface inventory, contracts, auth clues, change impact.
- `docs/ai/database.md`: storage, models, migrations, data risks.
- `docs/ai/deployment.md`: deployment units, runtime config, release clues.

## Rules
- Do not rely on guessed architecture, schema, or deployment behavior.
- If code and docs conflict, prefer code evidence and update docs together.
```

## 2. architecture.md 模板

```markdown
# Architecture

## Scope
- Reviewed paths: `...`
- Note: `This document is based on repository evidence only.`

## System Shape
- Repository type: `single service | monolith | monorepo | multi-service`
- Main runtime units: `...`

## Top-Level Modules
- `...`: `responsibility`
- `...`: `responsibility`

## Entry Points
- `...`: `startup entry / bootstrap / main flow`

## Dependency And Call Flow
- `module-a -> module-b`: `evidence`
- `service-a -> service-b`: `evidence`

## External Integrations
- `...`: `evidence`

## AI Coding Constraints
- Before changing `...`, also inspect `...`.
- Treat `...` as shared or high-risk.
```

## 3. api.md 模板

```markdown
# API

## Scope
- Reviewed paths: `...`
- Note: `This document is based on repository evidence only.`

## Interface Inventory
| Type | Identifier | Purpose | Source |
|---|---|---|---|
| HTTP | `GET /...` | `...` | `...` |

## Interface Details
## `GET /...`
- Type: `HTTP`
- Handler: `...`
- Request source: `...`
- Response source: `...`
- Auth clue: `...`
- Upstream/Downstream: `...`
- Change impact: `...`
```

## 4. database.md 模板

```markdown
# Database

## Scope
- Reviewed paths: `...`
- Note: `This document is based on repository evidence only.`

## Storage Inventory
| Store | Evidence | Related Paths |
|---|---|---|
| `PostgreSQL` | `...` | `...` |

## Schema And Models
## `users`
- Source: `migration | model | sql`
- Key fields: `...`
- Relations: `...`
- Accessed by: `...`
- Change risk: `...`

## Migration And Evolution
- Migration path: `...`
- Schema entry points: `...`
```

## 5. deployment.md 模板

```markdown
# Deployment

## Scope
- Reviewed paths: `...`
- Note: `This document is based on repository evidence only.`

## Deployment Units
- `api`: `evidence`
- `worker`: `evidence`

## Build And Runtime Artifacts
- `Dockerfile`: `...`
- `helm/...`: `...`

## Runtime Configuration
- `ENV_A`: `source / usage`
- `ENV_B`: `source / usage`

## Delivery And Release Clues
- `CI workflow`: `...`
- `deploy script`: `...`

## Operational Dependencies
- `service-a` depends on `db/cache/queue`
```

## 6. open-questions.md 模板

```markdown
# Open Questions

## Q1
- Question: `...`
- Why unresolved: `...`
- How to verify: `...`
- Conservative AI behavior: `...`
```

## 7. 输出禁忌

不得输出：

- 只有长篇总说明，没有实际文档文件
- 把 `AGENTS.md` 写成另一份完整架构文档
- 只有接口路径列表，没有契约来源和实现位置
- 只有数据库类型，没有模型、表或迁移线索
- 只有 Dockerfile 提示，没有部署单元和运行配置
- 把不确定事项埋进正文，假装是既定事实
