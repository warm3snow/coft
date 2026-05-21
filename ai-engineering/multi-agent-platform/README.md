# Multi-Agent Platform

一个最小但完备的多 Agent 平台框架。基于 LangChain / LangGraph 构建，支持通过注册 Agents + Tools + Workflow 快速搭建任意多 Agent 应用。

## 架构

```
User ──▶ Gateway ──▶ WorkflowEngine ──▶ Agent Pool
               │            │                │
               │            │          ┌─────┼─────┐
               ▼            ▼          ▼     ▼     ▼
         Policy Engine   Memory    Agent A  Agent B  Agent C
         (fail-closed)   (FAISS)   (tools)  (tools)  (tools)
                                       │
                                       ▼
                                  Tool Layer
                                       │
                              ┌────────┼────────┐
                              ▼        ▼        ▼
                          Observability (trace + Prometheus + log)
```

框架提供**机制**，应用提供**策略**：

| 框架（src/） | 应用（examples/） |
|--------------|-------------------|
| AgentRegistry -- 注册任意 Agent | 定义 Agent prompts |
| ToolRegistry -- 注册任意 Tool | 定义 domain tools |
| WorkflowEngine -- YAML 条件路由 | 定义 workflow YAML |
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
# 单任务流
python examples/01_basic_example.py

# 代码场景：Planner → Coder(ReAct) → Reviewer
python examples/02_multi_agent_workflow.py

# 客服应用：Triage → Order/Refund/FAQ（展示如何构建应用）
python examples/03_customer_service.py
```

## 如何构建你自己的应用

参考 `examples/03_customer_service.py`，只需 4 步：

```python
from multi_agent_platform.agents.base import create_llm
from multi_agent_platform.agent_registry import AgentRegistry
from multi_agent_platform.tools.registry import ToolRegistry
from multi_agent_platform.workflow_engine import WorkflowEngine

# 1. 定义你的 tools
@tool
def my_tool(query: str) -> str:
    """你的业务工具"""
    return do_something(query)

# 2. 注册 tools + agents
tool_reg = ToolRegistry()
tool_reg.register(my_tool, roles=["my_agent"])

agent_reg = AgentRegistry(create_llm(LLMConfig()), tool_reg)
agent_reg.register(role="my_agent", system_prompt="...", tool_names=["my_tool"])

# 3. 定义 workflow
engine = WorkflowEngine(agent_reg)
engine.load_workflow_yaml("""
name: my_app
entry_step: start
steps:
  - name: start
    agent: my_agent
    is_terminal: true
""")

# 4. 运行
result = engine.run("my_app", TaskRequest(tenant_id="x", user_input="..."))
```

## 项目结构

```
src/multi_agent_platform/          # 框架层
├── config.py                      # 统一配置（LLM_PROVIDER/MODEL/API_KEY/BASE_URL）
├── types.py                       # 类型定义
├── agent_registry.py              # Agent 动态注册
├── workflow_engine.py             # YAML 工作流引擎（structured output 路由）
├── orchestrator.py                # LangGraph 状态机（内置 plan→exec→review）
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
├── 01_basic_example.py            # 最简用法
├── 02_multi_agent_workflow.py     # 代码生成场景
└── 03_customer_service.py         # 客服场景（自定义 agents + tools + workflow）
```

## 设计原则

1. **框架 vs 应用分离** -- 框架提供注册/路由/安全/观测，应用定义 agents/tools/workflow
2. **单 Agent 优先** -- 能用 single agent + tools 解决的不上多 Agent
3. **Agent 不直接互调** -- 所有协作经过 WorkflowEngine
4. **Policy Engine fail-closed** -- 安全检查同步阻塞，出错即拒绝
5. **Structured Output 路由** -- Triage 用 Pydantic schema 约束，路由零歧义
6. **Planning 在编排层** -- Agent 内部只做执行策略，不做全局规划

## 架构决策

| 决策点 | 当前实现 | 后续演进方向 |
|--------|----------|-------------|
| LLM 调用 | 指数退避重试（3 次） | + 多模型 fallback + 熔断器 |
| Token 统计 | 区分 input/output tokens | + 精确计费 |
| Agent 反思 | Coder 工具失败时 1 轮 reflection | + 通用 quality gate |
| Injection 检测 | 正则 + Base64/Unicode/Leetspeak 解码 | + ML 分类器 |
| 日志格式 | LOG_FORMAT=console\|json | + ELK 采集 |
| Trace 存储 | 内存 FIFO 1000 条 | + OpenTelemetry |
| Metrics | Prometheus Counter/Histogram | + Grafana |
| 向量检索 | FAISS 内存 | + pgvector |
| 工作流 | 内存状态机 | + LangGraph Checkpoint |
| 路由 | structured output 三层降级 | + 强制 schema only |
| 代码沙盒 | subprocess + 黑名单 | + Docker 容器 |

## HTTP API

```bash
python -c "from src.multi_agent_platform.gateway import run_server; run_server()"
```

| 端点 | 说明 |
|------|------|
| `POST /chat` | 提交任务 |
| `GET /metrics` | JSON 指标 |
| `GET /metrics/prometheus` | Prometheus 格式 |
| `GET /trace/{task_id}` | 执行 trace |
| `GET /health` | 健康检查 |

## 技术栈

LangChain + LangGraph + FastAPI + FAISS + Pydantic v2 + PyYAML + structlog + prometheus-client

## License

Apache 2.0
