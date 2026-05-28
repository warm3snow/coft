# 示例

## 0. 使用规则

- 先读 `standards.md`。
- 再按 `output-template.md` 组织文档。
- `AGENTS.md` 默认生成，但保持短索引。

## 1. 示例指令

```text
按 ai-codebase-docs 对当前仓库做文档化整理，生成用于约束 AI coding 的核心文档。

要求：
1. 必须生成 `AGENTS.md`、架构文档、接口文档、数据库文档、部署文档。
2. 文档内容只基于你实际查看过的仓库文件。
3. `AGENTS.md` 要短，只包含阅读顺序、文档索引和少量核心规则。
4. 每类文档都要提炼出 AI 改代码前必须知道的边界信息。
5. 不确定内容统一写入 `docs/ai/open-questions.md`。
```

## 2. 最小合格输出

```text
Created:
- AGENTS.md
- docs/ai/architecture.md
- docs/ai/api.md
- docs/ai/database.md
- docs/ai/deployment.md

Optional:
- docs/ai/open-questions.md
```

## 3. AGENTS.md 片段示例

```markdown
# AGENTS

## Start Here
1. Read `docs/ai/architecture.md`.
2. Read `docs/ai/api.md` before changing handlers or payloads.
3. Read `docs/ai/database.md` before changing models or migrations.
4. Read `docs/ai/deployment.md` before changing config or manifests.
5. Check `docs/ai/open-questions.md` if present.

## Document Index
- `docs/ai/architecture.md`: system shape and module boundaries.
- `docs/ai/api.md`: interface contracts and change impact.
- `docs/ai/database.md`: storage, schema, migrations.
- `docs/ai/deployment.md`: deployment units and runtime config.
```

## 4. 核心文档片段示例

```markdown
# Architecture
- `cmd/api/`: service entrypoint
- `internal/order/`: order domain logic
- `internal/payment/`: payment integration

# API
- `POST /api/v1/orders`: handler in `internal/http/order_handler.go`

# Database
- `orders`: defined by `migrations/202605010001_create_orders.sql`

# Deployment
- `api`: built from `Dockerfile.api`, deployed by `helm/api/`
```

## 5. 禁止写法示例

- 误用：把 `AGENTS.md` 写成一大段系统介绍。
  正确：只保留阅读顺序、文档索引和少量硬规则。

- 误用：写“系统采用微服务架构”。
  正确：只有在仓库中看到多个独立服务入口、部署单元或 workspace 组织后，才保守描述为多服务结构。

- 误用：写“接口统一使用 JWT 鉴权”。
  正确：只有在路由、中间件或文档证据中看到鉴权链路，才写入接口文档。

- 误用：写“系统通过 GitHub Actions 自动部署生产”。
  正确：只有在 CI 工作流和部署脚本中明确看到发布步骤，才写成已观察流程；否则进入 `open-questions`。
