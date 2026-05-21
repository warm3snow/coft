"""
Multi-Agent Platform - 最小但完备的多 Agent 平台架构

Architecture:
    User -> Gateway -> Orchestrator/Workflow -> Agents Pool
                          |                       |
                          |                       ├── Planner / Triage
              +-----------+                       ├── Coder / Order / Refund
              |           |                       └── Reviewer / FAQ
              v           v                              |
        Policy Engine  Memory/RAG                        v
        (safety guard) (short+long)                 Tool Layer

Supports:
    - Dynamic agent registration (AgentRegistry)
    - YAML-defined workflows with conditional routing (WorkflowEngine)
    - Enterprise scenarios (customer service, code gen, etc.)
"""

__version__ = "0.2.0"
