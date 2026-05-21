"""Tool registry - centralized management for all tools.

Design principle (from doc 7.2 section 3):
    - Limit tools visible to each agent (< 10)
    - Two-layer tools: high-level capabilities -> internal tool expansion
"""

from __future__ import annotations

from typing import Any, Callable

from langchain_core.tools import BaseTool, tool

from ..observability import telemetry


class ToolRegistry:
    """Centralized tool registry with per-agent access control.

    Agents only see tools registered for their role.
    The Orchestrator uses this to enforce "each agent sees only its domain tools."
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._role_mapping: dict[str, set[str]] = {}  # role -> tool_names

    def register(self, tool_instance: BaseTool, roles: list[str] | None = None) -> None:
        """Register a tool, optionally restricting to specific agent roles."""
        self._tools[tool_instance.name] = tool_instance
        if roles:
            for role in roles:
                if role not in self._role_mapping:
                    self._role_mapping[role] = set()
                self._role_mapping[role].add(tool_instance.name)
        telemetry.log("tool.registered", name=tool_instance.name, roles=roles)

    def get_tools_for_role(self, role: str) -> list[BaseTool]:
        """Get all tools available to a specific agent role."""
        allowed_names = self._role_mapping.get(role)
        if allowed_names is None:
            # No restrictions -> return all tools
            return list(self._tools.values())
        return [self._tools[name] for name in allowed_names if name in self._tools]

    def get_tool(self, name: str) -> BaseTool | None:
        """Get a single tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
