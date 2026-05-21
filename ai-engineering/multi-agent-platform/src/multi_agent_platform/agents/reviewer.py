"""Reviewer Agent - reviews code quality and correctness.

Role in the architecture:
    - Final quality gate before task completion
    - Checks for code smells, security issues, correctness
    - Can request changes (sends back to Orchestrator for re-execution)

Review criteria (from doc 6.3):
    5-second checks: function length, nesting depth, file size, naming
    30-second checks: mixed IO/compute, error handling consistency
    5-minute checks: module boundary leaks, abstraction confusion, testability
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from ..types import AgentRole, AgentStep, Message
from .base import BaseAgent

_REVIEWER_SYSTEM_PROMPT = """You are a Code Reviewer Agent in a multi-agent software development platform.

Your role:
1. Review code produced by the Coder Agent
2. Check for quality, correctness, and security issues
3. Provide actionable feedback

Review checklist:
**5-second (visual) checks:**
- Function > 50 lines → RED flag
- Nesting > 3 levels → RED flag
- File > 300 lines → YELLOW flag
- Names like 'data', 'info', 'manager', 'helper' → YELLOW flag

**30-second (structural) checks:**
- Function mixes IO + compute + side effects → RED flag
- Error handling mixes try-catch and return None → RED flag
- Comments explain "what" instead of "why" → YELLOW flag
- Magic numbers without names → YELLOW flag

**5-minute (deep) checks:**
- Module boundary leaks (SQL in UserService) → RED flag
- Abstraction level confusion → RED flag
- Poor testability (dependencies can't be mocked) → RED flag

Output format (JSON):
{
    "verdict": "approve|request_changes|reject",
    "score": 0-10,
    "issues": [
        {
            "severity": "red|yellow",
            "category": "naming|complexity|security|correctness|style",
            "description": "What's wrong",
            "suggestion": "How to fix it"
        }
    ],
    "summary": "Overall assessment in 1-2 sentences"
}

Rules:
- Be constructive but firm
- Red flags = must fix before approval
- Yellow flags = should fix, but not blocking
- Score 7+ = approve, 4-6 = request_changes, <4 = reject
"""


class ReviewerAgent(BaseAgent):
    """Reviews code for quality, correctness, and security."""

    def __init__(self, llm: BaseChatModel, tools: list[BaseTool] | None = None) -> None:
        super().__init__(
            role=AgentRole.REVIEWER,
            llm=llm,
            tools=tools or [],
            system_prompt=_REVIEWER_SYSTEM_PROMPT,
        )

    def invoke(self, task: str, context: list[Message] | None = None) -> AgentStep:
        """Review code and provide structured feedback."""
        start = time.time()
        messages = self._build_messages(task, context)

        # Reviewer typically doesn't need tools - just reads code from context
        response = self._call_llm(messages, use_tools=False)
        content = response.content if hasattr(response, "content") else str(response)

        duration_ms = (time.time() - start) * 1000

        return AgentStep(
            agent_role=self.role,
            action="respond",
            input_summary=task[:200],
            output_summary=content[:500],
            tokens_used=getattr(response, "usage_metadata", {}).get("total_tokens", 0)
            if hasattr(response, "usage_metadata") and response.usage_metadata
            else 0,
            duration_ms=duration_ms,
        )
