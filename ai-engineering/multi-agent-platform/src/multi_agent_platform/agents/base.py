"""Base agent class - deep module interface with thin API, rich internals.

Design principles (from doc 6.4):
    - Clean separation: Transport / Policy / Telemetry injected
    - Error types: RateLimit / Retriable / Fatal
    - Testable: mock the LLM and tools to test independently
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import BaseTool

from ..config import LLMConfig
from ..types import AgentRole, AgentStep, Message, ToolCall
from ..observability import telemetry


def create_llm(config: LLMConfig) -> BaseChatModel:
    """Factory: create LLM client based on unified config.

    All providers use the same env vars:
        LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, LLM_BASE_URL
    """
    if config.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        kwargs: dict = {
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if config.api_key:
            kwargs["anthropic_api_key"] = config.api_key
        if config.base_url:
            kwargs["anthropic_api_url"] = config.base_url
        return ChatAnthropic(**kwargs)

    elif config.provider == "ollama":
        from langchain_ollama import ChatOllama
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
        }
        if config.base_url:
            # Strip /v1 suffix if present (Ollama native API doesn't use it)
            base = config.base_url.rstrip("/")
            if base.endswith("/v1"):
                base = base[:-3]
            kwargs["base_url"] = base
        return ChatOllama(**kwargs)

    else:  # openai (default) - also works with any OpenAI-compatible API
        from langchain_openai import ChatOpenAI
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "openai_api_key": config.api_key or "sk-placeholder",
        }
        if config.base_url:
            kwargs["openai_api_base"] = config.base_url
        return ChatOpenAI(**kwargs)


class BaseAgent(ABC):
    """Abstract base agent - all agents inherit from this.

    Interface contract:
        - `role`: identifies the agent
        - `invoke(task, context)`: execute the agent's logic, return result
        - `system_prompt`: the agent's personality/instructions

    Internals handle LLM calls, tool use, telemetry.
    """

    def __init__(
        self,
        role: AgentRole,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
        system_prompt: str = "",
    ) -> None:
        self.role = role
        self.llm = llm
        self.tools = tools or []
        self.system_prompt = system_prompt

        # Bind tools to LLM if supported
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

    @abstractmethod
    def invoke(self, task: str, context: list[Message] | None = None) -> AgentStep:
        """Execute the agent's main logic.

        Args:
            task: The task description or instruction.
            context: Previous conversation messages for context.

        Returns:
            AgentStep with action taken, output, and metadata.
        """
        ...

    def _build_messages(
        self, task: str, context: list[Message] | None = None
    ) -> list[Any]:
        """Build LangChain message list from task and context."""
        messages = []

        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))

        # Add context messages
        if context:
            for msg in context:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

        # Add current task
        messages.append(HumanMessage(content=task))
        return messages

    def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolCall:
        """Execute a tool by name and return the result."""
        start = time.time()
        tool_obj = next((t for t in self.tools if t.name == tool_name), None)

        if tool_obj is None:
            return ToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=f"Error: tool '{tool_name}' not found",
                success=False,
            )

        try:
            result = tool_obj.invoke(arguments)
            duration_ms = (time.time() - start) * 1000
            telemetry.metrics.record_tool_call(tool_name)
            return ToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=str(result),
                success=True,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            return ToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=f"Error: {e}",
                success=False,
                duration_ms=duration_ms,
            )

    def _call_llm(self, messages: list[Any], use_tools: bool = True) -> Any:
        """Call the LLM with messages and exponential backoff retry.

        Retry policy:
            - Max 3 attempts
            - Exponential backoff: 1s, 2s, 4s
            - Only retries on transient errors (connection, rate limit)
            - Fatal errors (auth, invalid request) raise immediately
        """
        import random

        llm = self.llm_with_tools if (use_tools and self.tools) else self.llm
        max_retries = 3
        base_delay = 1.0

        with telemetry.span(
            f"agent.{self.role.value}.llm_call",
            trace_id="",
            agent_role=self.role.value,
        ) as span:
            last_error = None
            for attempt in range(max_retries):
                try:
                    response = llm.invoke(messages)

                    # Track tokens (distinguish input/output)
                    input_tokens = 0
                    output_tokens = 0
                    total_tokens = 0
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        input_tokens = response.usage_metadata.get("input_tokens", 0)
                        output_tokens = response.usage_metadata.get("output_tokens", 0)
                        total_tokens = response.usage_metadata.get("total_tokens", 0) or (input_tokens + output_tokens)

                    telemetry.metrics.record_tokens(total_tokens)
                    telemetry.metrics.record_agent_call(self.role.value)
                    span.event("llm_response", tokens=total_tokens, input_tokens=input_tokens, output_tokens=output_tokens, attempt=attempt + 1)
                    return response

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()

                    # Non-retriable errors: raise immediately
                    if any(kw in error_str for kw in ["auth", "invalid_api_key", "permission", "not_found"]):
                        span.set_error(f"fatal (no retry): {e}")
                        raise

                    # Retriable: connection errors, rate limits, timeouts
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                        span.event("retry", attempt=attempt + 1, delay=round(delay, 2), error=str(e)[:100])
                        time.sleep(delay)
                    else:
                        span.set_error(f"max retries exceeded: {e}")

            raise last_error
