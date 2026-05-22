"""
Multi-Agent Platform - 最小但完备的多 Agent 平台架构

Architecture:
    User -> Gateway -> Orchestrator -> Agent Pool
                          |                |
              +-----------+          +-----+-----+
              |           |          |     |     |
              v           v        AgentA AgentB AgentC
        Policy Engine  Memory/RAG        |
        (fail-closed) (short+long)       v
                                    Tool Layer

Orchestrator modes:
    - Default (ReAct): LLM autonomously decides each action step
    - Custom (YAML): Conditional routing workflows (triage -> specialists)
"""

__version__ = "0.3.0"
