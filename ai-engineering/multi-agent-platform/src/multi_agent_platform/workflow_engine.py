"""Workflow definitions and deprecated WorkflowEngine shim.

This module provides:
    - WorkflowStep: A single step in a workflow.
    - WorkflowDefinition: A complete workflow definition (parsed from YAML).
    - WorkflowEngine: **Deprecated** - delegates to Orchestrator.

For new code, use Orchestrator directly:
    orchestrator = Orchestrator(config, agent_registry=registry)
    orchestrator.load_workflow_yaml(yaml_str)
    result = orchestrator.run(request, workflow_name="my_workflow")
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

import yaml

from .agent_registry import AgentRegistry
from .memory import MemoryManager
from .observability import telemetry
from .policy_engine import PolicyEngine
from .types import TaskRequest, TaskResult


@dataclass
class WorkflowStep:
    """A single step in a workflow."""

    name: str
    agent: str  # Agent role name (must be registered in AgentRegistry)
    routes: dict[str, str] = field(default_factory=dict)  # output_key -> next_step
    condition: str = ""  # Python-like expression for conditional execution
    is_terminal: bool = False  # If True, workflow ends after this step
    routing_mode: str = "structured"  # "structured" (Pydantic) | "substring" (legacy)


@dataclass
class WorkflowDefinition:
    """A complete workflow definition."""

    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    entry_step: str = ""  # First step name (defaults to steps[0])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowDefinition":
        """Parse a workflow definition from a dict (e.g., loaded from YAML)."""
        steps = []
        for step_data in data.get("steps", []):
            steps.append(WorkflowStep(
                name=step_data["name"],
                agent=step_data["agent"],
                routes=step_data.get("routes", {}),
                condition=step_data.get("condition", ""),
                is_terminal=step_data.get("is_terminal", False),
                routing_mode=step_data.get("routing_mode", "structured"),
            ))

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
            entry_step=data.get("entry_step", steps[0].name if steps else ""),
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "WorkflowDefinition":
        """Parse from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class WorkflowEngine:
    """Deprecated: Use Orchestrator with workflow_name parameter instead.

    This class is kept for backward compatibility only.
    All logic has been moved to Orchestrator._run_workflow().
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        policy: PolicyEngine | None = None,
        memory: MemoryManager | None = None,
    ) -> None:
        warnings.warn(
            "WorkflowEngine is deprecated. Use Orchestrator(agent_registry=registry) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        from .orchestrator import Orchestrator
        from .config import PlatformConfig

        self._orchestrator = Orchestrator(
            config=PlatformConfig(),
            agent_registry=agent_registry,
        )

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a workflow definition."""
        self._orchestrator.register_workflow(workflow)

    def load_workflow_yaml(self, yaml_str: str) -> WorkflowDefinition:
        """Load and register a workflow from YAML."""
        return self._orchestrator.load_workflow_yaml(yaml_str)

    def list_workflows(self) -> list[str]:
        """List registered workflow names."""
        return self._orchestrator.list_workflows()

    def run(self, workflow_name: str, request: TaskRequest) -> TaskResult:
        """Execute a workflow. Delegates to Orchestrator."""
        return self._orchestrator.run(request, workflow_name=workflow_name)
