"""Planner Agent - decomposes complex tasks into actionable steps.

Role in the architecture:
    - First agent called by Orchestrator
    - Breaks user request into structured sub-tasks
    - Decides which agents should handle each sub-task
    - Does NOT execute tools directly (delegates to Coder/Reviewer)
"""

from __future__ import annotations

import json
import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from ..types import AgentRole, AgentStep, Message
from .base import BaseAgent

_PLANNER_SYSTEM_PROMPT = """You are a Planning Agent in a multi-agent software development platform.

Your role:
1. Analyze the user's request and break it into clear, actionable sub-tasks
2. Determine which specialist agent should handle each sub-task:
   - "coder" for writing/modifying code
   - "reviewer" for reviewing code quality and correctness
3. Output a structured plan

Output format (JSON):
{
    "analysis": "Brief analysis of what the user wants",
    "steps": [
        {
            "step_id": 1,
            "description": "What needs to be done",
            "agent": "coder|reviewer",
            "input": "Specific instruction for the agent",
            "depends_on": []
        }
    ],
    "success_criteria": "How to know the task is complete"
}

Rules:
- Keep plans concise (max 3 steps)
- Each step should be independently executable
- Always include a review step for code changes
- If the task is simple enough for a single step, use just one step
"""


class PlannerAgent(BaseAgent):
    """Decomposes tasks into structured plans for other agents."""

    def __init__(self, llm: BaseChatModel, tools: list[BaseTool] | None = None) -> None:
        super().__init__(
            role=AgentRole.PLANNER,
            llm=llm,
            tools=tools,
            system_prompt=_PLANNER_SYSTEM_PROMPT,
        )

    def invoke(self, task: str, context: list[Message] | None = None) -> AgentStep:
        """Create a plan for the given task."""
        start = time.time()
        messages = self._build_messages(task, context)
        response = self._call_llm(messages, use_tools=False)

        content = response.content if hasattr(response, "content") else str(response)

        # Try to parse as structured plan
        plan = self._parse_plan(content)

        duration_ms = (time.time() - start) * 1000
        return AgentStep(
            agent_role=self.role,
            action="plan",
            input_summary=task[:200],
            output_summary=content[:500],
            tokens_used=getattr(response, "usage_metadata", {}).get("total_tokens", 0)
            if hasattr(response, "usage_metadata") and response.usage_metadata
            else 0,
            duration_ms=duration_ms,
        )

    def _parse_plan(self, content: str) -> dict[str, Any] | None:
        """Attempt to parse LLM output as a structured plan."""
        try:
            # Try to extract JSON from the response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def get_plan_steps(self, task: str, context: list[Message] | None = None) -> list[dict[str, Any]]:
        """Convenience: get just the steps from a plan."""
        messages = self._build_messages(task, context)
        response = self._call_llm(messages, use_tools=False)
        content = response.content if hasattr(response, "content") else str(response)

        plan = self._parse_plan(content)
        if plan and "steps" in plan:
            return plan["steps"]

        # Fallback: single step with the full task
        return [{"step_id": 1, "description": task, "agent": "coder", "input": task, "depends_on": []}]
