# Multi-Agent Platform

一个最小但完备的多 Agent 平台框架。基于 LangChain 构建，支持通过注册 Agents + Tools + Workflow 快速搭建任意多 Agent 应用。

## 架构

```
                                   ┌──────────────────────┐
                                   │   Observability      │
                                   │  (trace/metrics/log) │
                                   └──────────┬───────────┘
                                              │
   User ──▶ Gateway ──▶ Orchestrator ────▶ Agent Pool
                            │                 │
                            │          ┌──────┼──────┐
            ┌───────────────┤          ▼      ▼      ▼
            ▼               ▼       Agent A  Agent B  Agent C
      Policy Engine    Memory/RAG   (triage) (coder)  (custom)
      (fail-closed)   (short+long)        │
                                          ▼
                                     Tool Layer
                                    (DB/API/sandbox)
```

Orchestrator 支持两种编排模式：

| 模式 | 触发条件 | 行为 |
|------|---------|------|
| **默认（ReAct）** | `run(request)` | GenericAgent 自主循环：思考→行动→观察→判断 |
| **自定义（YAML）** | `run(request, workflow_name="...")` | 按 YAML 定义的条件路由执行 |

框架提供**机制**，应用提供**策略**：

| 框架（src/） | 应用（examples/） |
|--------------|-------------------|
| AgentRegistry -- 注册任意 Agent | 定义 Agent prompts |
| ToolRegistry -- 注册任意 Tool | 定义 domain tools |
| Orchestrator -- 双模式编排（ReAct + YAML workflow） | 定义 workflow YAML |
| PolicyEngine -- 安全围栏 | - |
| Observability -- trace/metrics/log | - |
| Memory -- 短期 + RAG | - |

## 快速开始

```bash
cd ai-engineering/multi-agent-platform
pip install -r requirements.txt
```

配置 LLM（统一 4 个环境变量）：

```bash
export LLM_PROVIDER="ollama"                    # openai | anthropic | ollama
export LLM_MODEL="qwen2.5:7b"                  # 模型名
export LLM_API_KEY="sk-..."                     # API key（ollama 本地可不设）
export LLM_BASE_URL="http://localhost:11434/v1" # API 端点
```

运行示例：

```bash
# 默认 ReAct 模式：LLM 自主决定每步行动
python examples/01_basic_example.py

# 复杂任务：Orchestrator 自主完成代码编写
python examples/02_multi_agent_workflow.py

# 自定义 Workflow 模式：Triage → Order/Refund/FAQ（展示如何构建应用）
python examples/03_customer_service.py
```

## 如何构建你自己的应用

参考 `examples/03_customer_service.py`，只需 4 步：

```python
from multi_agent_platform.config import PlatformConfig, LLMConfig
from multi_agent_platform.agents.base import create_llm
from multi_agent_platform.agent_registry import AgentRegistry
from multi_agent_platform.tools.registry import ToolRegistry
from multi_agent_platform.orchestrator import Orchestrator

# 1. 定义你的 tools
@tool
def my_tool(query: str) -> str:
    """你的业务工具"""
    return do_something(query)

# 2. 注册 tools + agents
tool_reg = ToolRegistry()
tool_reg.register(my_tool, roles=["my_agent"])

llm = create_llm(LLMConfig())
agent_reg = AgentRegistry(llm, tool_reg)
agent_reg.register(role="my_agent", system_prompt="...", tool_names=["my_tool"])

# 3. 创建 Orchestrator 并加载 workflow
orchestrator = Orchestrator(PlatformConfig(), agent_registry=agent_reg)
orchestrator.load_workflow_yaml("""
name: my_app
entry_step: start
steps:
  - name: start
    agent: my_agent
    is_terminal: true
""")

# 4. 运行
result = orchestrator.run(TaskRequest(tenant_id="x", user_input="..."), workflow_name="my_app")
```

或直接使用默认 ReAct 模式（无需 YAML）：

```python
orchestrator = Orchestrator()
result = orchestrator.run(TaskRequest(tenant_id="x", user_input="帮我写一个素数检查函数"))
```

## 项目结构

```
src/multi_agent_platform/          # 框架层
├── config.py                      # 统一配置（LLM_PROVIDER/MODEL/API_KEY/BASE_URL）
├── types.py                       # 类型定义
├── agent_registry.py              # Agent 动态注册 + GenericAgent（ReAct）
├── orchestrator.py                # 双模式编排器（ReAct 默认 + YAML workflow）
├── workflow_engine.py             # Workflow 数据定义（WorkflowStep/Definition）
├── policy_engine.py               # 安全围栏（正则 + 反绕过 + fail-closed）
├── memory.py                      # 短期记忆 + FAISS RAG
├── gateway.py                     # FastAPI HTTP 入口
├── observability.py               # trace(FIFO) + Prometheus + 日志
├── eval.py                        # 评测框架
├── agents/
│   ├── base.py                    # Agent 基类（指数退避 + token 统计）
│   ├── structured_triage.py       # StructuredTriageAgent（with_structured_output）
│   ├── planner.py                 # 内置：任务分解
│   ├── coder.py                   # 内置：代码生成（ReAct + reflection）
│   └── reviewer.py                # 内置：代码审查
└── tools/
    ├── registry.py                # Tool 注册表（按 role 分发）
    ├── file_tools.py              # 内置：文件操作
    └── execution_tools.py         # 内置：Python 沙盒

examples/                          # 应用层（展示如何使用框架）
├── 01_basic_example.py            # 最简用法（ReAct 默认模式）
├── 02_multi_agent_workflow.py     # 复杂任务（ReAct 自主完成）
└── 03_customer_service.py         # 客服场景（YAML workflow 模式）
```

## 设计原则

1. **框架 vs 应用分离** -- 框架提供注册/编排/安全/观测，应用定义 agents/tools/workflow
2. **单 Agent 优先** -- 能用 single agent + tools 解决的不上多 Agent
3. **Agent 不直接互调** -- 所有协作经过 Orchestrator
4. **默认 ReAct 自主执行** -- LLM 动态决策每步行动，无固定 pipeline
5. **Policy Engine fail-closed** -- 安全检查同步阻塞，出错即拒绝
6. **Structured Output 路由** -- Triage 用 Pydantic schema 约束，路由零歧义

## 架构决策

| 决策点 | 当前实现 | 后续演进方向 |
|--------|----------|-------------|
| 编排模式 | 双模式：ReAct 默认 + YAML 自定义 | + 层级编排 |
| LLM 调用 | 指数退避重试（3 次） | + 多模型 fallback + 熔断器 |
| Token 统计 | 区分 input/output tokens | + 精确计费 |
| Agent 执行 | ReAct loop（思考→行动→观察） | + 并行工具调用 |
| Injection 检测 | 正则 + Base64/Unicode/Leetspeak 解码 | + ML 分类器 |
| 日志格式 | LOG_FORMAT=console\|json | + ELK 采集 |
| Trace 存储 | 内存 FIFO 1000 条 | + OpenTelemetry |
| Metrics | Prometheus Counter/Histogram | + Grafana |
| 向量检索 | FAISS 内存 | + pgvector |
| 路由 | structured output 三层降级 | + 强制 schema only |
| 代码沙盒 | subprocess + 黑名单 | + Docker 容器 |

## HTTP API

```bash
python -c "from multi_agent_platform.gateway import run_server; run_server()"
```

| 端点 | 说明 |
|------|------|
| `POST /chat` | 提交任务（支持 `workflow` 字段指定 YAML 模式） |
| `GET /metrics` | JSON 指标 |
| `GET /metrics/prometheus` | Prometheus 格式 |
| `GET /trace/{task_id}` | 执行 trace |
| `GET /health` | 健康检查 |

## 技术栈

LangChain + FastAPI + FAISS + Pydantic v2 + PyYAML + structlog + prometheus-client

## License

Apache 2.0
