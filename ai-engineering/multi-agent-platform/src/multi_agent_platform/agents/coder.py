"""Coder Agent - writes and modifies code using tools.

Role in the architecture:
    - Receives specific coding tasks from Planner via Orchestrator
    - Has access to file tools and execution sandbox
    - Follows structured output: think -> code -> verify
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool

from ..types import AgentRole, AgentStep, Message, ToolCall
from .base import BaseAgent

_CODER_SYSTEM_PROMPT = """You are a Coder Agent in a multi-agent software development platform.

Your role:
1. Write clean, production-quality code based on the given task
2. Use available tools to read existing code, write new code, and verify it works
3. Follow best practices: clear naming, minimal complexity, proper error handling

Available tools:
- read_file: Read a file from the workspace
- write_file: Write content to a file in the workspace
- list_directory: List files in the workspace
- execute_python: Run Python code to verify it works

Process:
1. Understand the task requirements
2. Read existing code if modifying
3. Write/modify the code
4. Execute a quick test if possible
5. Summarize what you did

Rules:
- Keep functions under 50 lines
- No nested logic deeper than 3 levels
- Handle errors explicitly
- Use descriptive variable names (never 'data', 'info', 'manager')
"""


class CoderAgent(BaseAgent):
    """Writes and modifies code using tools."""

    def __init__(self, llm: BaseChatModel, tools: list[BaseTool] | None = None) -> None:
        super().__init__(
            role=AgentRole.CODER,
            llm=llm,
            tools=tools or [],
            system_prompt=_CODER_SYSTEM_PROMPT,
        )

    def invoke(self, task: str, context: list[Message] | None = None) -> AgentStep:
        """Execute a coding task with tool use."""
        start = time.time()
        messages = self._build_messages(task, context)
        tool_calls_made: list[ToolCall] = []

        # ReAct loop: LLM decides -> use tool -> observe -> repeat
        # Limited to 3 iterations to prevent runaway loops with slow models
        max_iterations = 3
        for _ in range(max_iterations):
            response = self._call_llm(messages, use_tools=True)

            # Check if LLM wants to use tools
            if hasattr(response, "tool_calls") and response.tool_calls:
                messages.append(response)

                for tc in response.tool_calls:
                    tool_result = self._execute_tool(tc["name"], tc["args"])
                    tool_calls_made.append(tool_result)

                    # Add tool result back to conversation
                    messages.append(
                        ToolMessage(content=tool_result.result, tool_call_id=tc["id"])
                    )
            else:
                # LLM is done (no more tool calls)
                break

        content = response.content if hasattr(response, "content") else str(response)

        # Reflection: 1 round of self-check (only if tools were used)
        if tool_calls_made and any(not tc.success for tc in tool_calls_made):
            content = self._reflect(messages, content, tool_calls_made)

        duration_ms = (time.time() - start) * 1000

        return AgentStep(
            agent_role=self.role,
            action="execute_tool",
            input_summary=task[:200],
            output_summary=content[:500],
            tool_calls=tool_calls_made,
            tokens_used=getattr(response, "usage_metadata", {}).get("total_tokens", 0)
            if hasattr(response, "usage_metadata") and response.usage_metadata
            else 0,
            duration_ms=duration_ms,
        )

    def _reflect(self, messages: list, current_output: str, tool_calls: list) -> str:
        """One round of self-reflection when tool calls failed.

        Asks the LLM to identify what went wrong and provide a corrected response.
        Max 1 round (from doc 7.2 section 5: "反思最多 1 轮，超过就升级到人").
        """
        from langchain_core.messages import HumanMessage
        from ..types import ToolCall as TC

        failed_tools = [tc for tc in tool_calls if not tc.success]
        errors = "\n".join(f"- {tc.tool_name}: {tc.result}" for tc in failed_tools)

        reflection_prompt = (
            f"Some tool calls failed:\n{errors}\n\n"
            f"Your previous output was:\n{current_output[:300]}\n\n"
            f"Please provide a corrected response accounting for these failures. "
            f"If you cannot proceed, explain what's needed."
        )
        messages.append(HumanMessage(content=reflection_prompt))

        try:
            response = self._call_llm(messages, use_tools=False)
            return response.content if hasattr(response, "content") else current_output
        except Exception:
            return current_output  # Reflection failure is non-fatal
