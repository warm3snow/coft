"""Agent Registry - dynamic agent registration and factory.

Replaces the hardcoded enum-based agent system with a pluggable registry.
Agents can be registered at runtime with custom system prompts and tool filters.

Usage:
    registry = AgentRegistry(llm)
    registry.register("order_agent", system_prompt="...", tools=["query_order", "track_logistics"])
    agent = registry.get("order_agent")
    result = agent.invoke("查订单 12345")
"""

from __future__ import annotations

from typing import Any, Callable, Type

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .agents.base import BaseAgent
from .observability import telemetry


class GenericAgent(BaseAgent):
    """A generic agent that can be configured with any system prompt and tools.

    This is used by the registry when no custom agent class is provided.
    """

    def __init__(
        self,
        role: str,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
        system_prompt: str = "",
    ) -> None:
        from .types import AgentRole
        # Use CUSTOM enum for non-standard roles
        try:
            agent_role = AgentRole(role)
        except ValueError:
            agent_role = AgentRole.CUSTOM

        super().__init__(
            role=agent_role,
            llm=llm,
            tools=tools,
            system_prompt=system_prompt,
        )
        self._role_name = role  # Keep the string name

    def invoke(self, task: str, context=None):
        """Execute with ReAct loop (tool use) or direct response."""
        import time
        from langchain_core.messages import ToolMessage
        from .types import AgentStep, ToolCall, Message

        start = time.time()
        messages = self._build_messages(task, context)
        tool_calls_made: list[ToolCall] = []

        # ReAct loop if tools available
        max_iterations = 5
        response = None
        for _ in range(max_iterations):
            response = self._call_llm(messages, use_tools=bool(self.tools))

            if hasattr(response, "tool_calls") and response.tool_calls:
                messages.append(response)
                for tc in response.tool_calls:
                    tool_result = self._execute_tool(tc["name"], tc["args"])
                    tool_calls_made.append(tool_result)
                    messages.append(ToolMessage(content=tool_result.result, tool_call_id=tc["id"]))
            else:
                break

        content = response.content if (response and hasattr(response, "content")) else ""
        duration_ms = (time.time() - start) * 1000

        return AgentStep(
            agent_role=self._role_name,
            action="execute_tool" if tool_calls_made else "respond",
            input_summary=task[:200],
            output_summary=content[:500],
            tool_calls=tool_calls_made,
            tokens_used=getattr(response, "usage_metadata", {}).get("total_tokens", 0)
            if hasattr(response, "usage_metadata") and response.usage_metadata
            else 0,
            duration_ms=duration_ms,
        )


class AgentRegistration:
    """Metadata for a registered agent."""

    def __init__(
        self,
        role: str,
        system_prompt: str,
        tool_names: list[str] | None = None,
        agent_class: Type[BaseAgent] | None = None,
        description: str = "",
    ) -> None:
        self.role = role
        self.system_prompt = system_prompt
        self.tool_names = tool_names  # None means "all tools"
        self.agent_class = agent_class
        self.description = description


class AgentRegistry:
    """Dynamic agent registry - register/instantiate agents at runtime.

    Separates agent definition from agent instantiation:
    - Register: define role + prompt + tool access
    - Get: instantiate with LLM and resolved tools
    """

    def __init__(self, llm: BaseChatModel, tool_registry=None) -> None:
        self._llm = llm
        self._tool_registry = tool_registry
        self._registrations: dict[str, AgentRegistration] = {}
        self._instances: dict[str, BaseAgent] = {}  # Cache

    def register(
        self,
        role: str,
        system_prompt: str,
        tool_names: list[str] | None = None,
        agent_class: Type[BaseAgent] | None = None,
        description: str = "",
    ) -> None:
        """Register an agent role with its configuration."""
        self._registrations[role] = AgentRegistration(
            role=role,
            system_prompt=system_prompt,
            tool_names=tool_names,
            agent_class=agent_class,
            description=description,
        )
        # Invalidate cached instance
        self._instances.pop(role, None)
        telemetry.log("agent_registry.registered", role=role, description=description)

    def get(self, role: str) -> BaseAgent:
        """Get or create an agent instance by role name."""
        if role in self._instances:
            return self._instances[role]

        reg = self._registrations.get(role)
        if reg is None:
            raise ValueError(f"Agent role '{role}' not registered. Available: {list(self._registrations.keys())}")

        # Resolve tools
        tools = self._resolve_tools(reg.tool_names)

        # Instantiate
        if reg.agent_class:
            agent = reg.agent_class(llm=self._llm, tools=tools)
        else:
            agent = GenericAgent(
                role=role,
                llm=self._llm,
                tools=tools,
                system_prompt=reg.system_prompt,
            )

        self._instances[role] = agent
        return agent

    def _resolve_tools(self, tool_names: list[str] | None) -> list[BaseTool]:
        """Resolve tool names to tool instances."""
        if self._tool_registry is None:
            return []
        if tool_names is None:
            return self._tool_registry.get_tools_for_role("*")
        return [
            t for name in tool_names
            if (t := self._tool_registry.get_tool(name)) is not None
        ]

    def list_agents(self) -> list[dict[str, str]]:
        """List all registered agent roles."""
        return [
            {"role": r.role, "description": r.description}
            for r in self._registrations.values()
        ]

    def has(self, role: str) -> bool:
        """Check if a role is registered."""
        return role in self._registrations
