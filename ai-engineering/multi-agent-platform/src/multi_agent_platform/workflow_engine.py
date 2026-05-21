"""Workflow Engine - YAML-defined conditional routing and multi-step workflows.

Supports:
    - Linear pipelines (step1 → step2 → step3)
    - Conditional routing (triage → N specialist branches)
    - Escalation conditions (if amount > X, escalate to human)
    - Fallback / default routes

Workflow definition format (YAML):
    name: "customer_service"
    steps:
      - name: "triage"
        agent: "triage_agent"
        routes:
          ORDER_STATUS: "order_agent"
          REFUND: "refund_agent"
          FAQ: "faq_agent"
          _default: "faq_agent"
      - name: "escalation"
        agent: "human_validator"
        condition: "refund_amount > 500"
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

import yaml

from .agent_registry import AgentRegistry
from .memory import MemoryManager
from .observability import telemetry
from .policy_engine import PolicyEngine
from .types import AgentStep, Message, PolicyVerdict, TaskRequest, TaskResult, TaskStatus


@dataclass
class WorkflowStep:
    """A single step in a workflow."""

    name: str
    agent: str  # Agent role name (must be registered in AgentRegistry)
    routes: dict[str, str] = field(default_factory=dict)  # output_key -> next_agent
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
    """Executes workflow definitions with conditional routing.

    Unlike the default Orchestrator (linear: plan→execute→review),
    this engine supports arbitrary graph-like workflows with branching.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        policy: PolicyEngine | None = None,
        memory: MemoryManager | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.policy = policy or PolicyEngine()
        self.memory = memory or MemoryManager()
        self._workflows: dict[str, WorkflowDefinition] = {}

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a workflow definition."""
        self._workflows[workflow.name] = workflow
        telemetry.log("workflow.registered", name=workflow.name, steps=len(workflow.steps))

    def load_workflow_yaml(self, yaml_str: str) -> WorkflowDefinition:
        """Load and register a workflow from YAML."""
        wf = WorkflowDefinition.from_yaml(yaml_str)
        self.register_workflow(wf)
        return wf

    def list_workflows(self) -> list[str]:
        """List registered workflow names."""
        return list(self._workflows.keys())

    def run(self, workflow_name: str, request: TaskRequest) -> TaskResult:
        """Execute a workflow for a given request.

        Flow:
            1. Policy check
            2. Find entry step
            3. Execute step → get output
            4. Route to next step based on output/conditions
            5. Repeat until terminal or no more routes
        """
        start = time.time()
        workflow = self._workflows.get(workflow_name)
        if workflow is None:
            return TaskResult(
                task_id=request.id,
                status=TaskStatus.FAILED,
                error=f"Workflow '{workflow_name}' not found. Available: {self.list_workflows()}",
            )

        # Policy check
        policy_result = self.policy.check_input(request.user_input, request.tenant_id)
        if policy_result.verdict == PolicyVerdict.DENY:
            return TaskResult(
                task_id=request.id,
                status=TaskStatus.FAILED,
                error=f"Policy denied: {policy_result.reason}",
            )

        # Build step lookup
        step_map = {s.name: s for s in workflow.steps}
        agent_trace: list[AgentStep] = []
        output_parts: list[str] = []
        context_vars: dict[str, Any] = {"user_input": request.user_input}

        # Store initial message
        self.memory.add_message(request.id, Message(role="user", content=request.user_input))

        # Execute workflow
        current_step_name = workflow.entry_step
        max_hops = 10  # Safety: prevent infinite loops

        with telemetry.span("workflow.run", trace_id=request.id, workflow=workflow_name) as span:
            for hop in range(max_hops):
                step = step_map.get(current_step_name)
                if step is None:
                    break

                # Check condition
                if step.condition and not self._eval_condition(step.condition, context_vars):
                    span.event("step_skipped", step=step.name, condition=step.condition)
                    break

                # Execute agent
                try:
                    agent = self.agent_registry.get(step.agent)
                except ValueError as e:
                    agent_trace.append(AgentStep(
                        agent_role=step.agent,
                        action="error",
                        input_summary=request.user_input[:200],
                        output_summary=str(e),
                    ))
                    break

                context = self.memory.get_context(request.id)
                try:
                    step_result = agent.invoke(request.user_input, context)
                except Exception as e:
                    agent_trace.append(AgentStep(
                        agent_role=step.agent,
                        action="error",
                        input_summary=request.user_input[:200],
                        output_summary=f"Agent execution failed: {e}",
                    ))
                    output_parts.append(f"[{step.name}] Error: {e}")
                    # Return partial result as failed
                    duration_ms = (time.time() - start) * 1000
                    self.memory.clear_task(request.id)
                    return TaskResult(
                        task_id=request.id,
                        status=TaskStatus.FAILED,
                        output="\n".join(output_parts),
                        agent_trace=agent_trace,
                        duration_ms=duration_ms,
                        error=f"Agent '{step.agent}' failed at step '{step.name}': {e}",
                    )

                agent_trace.append(step_result)
                output_parts.append(f"[{step.name}] {step_result.output_summary}")

                # Store in memory
                self.memory.add_message(
                    request.id,
                    Message(role="assistant", content=step_result.output_summary, metadata={"step": step.name}),
                )

                # Update context vars
                context_vars["last_output"] = step_result.output_summary
                context_vars["last_agent"] = step.agent

                # Extract structured routing data if available
                # StructuredTriageAgent sets this in metadata via output_summary
                if step.routes and step.routing_mode == "structured":
                    # Check if agent returned structured category in metadata
                    route_cat = None
                    # Try to get from step_result metadata (set by StructuredTriageAgent)
                    if hasattr(step_result, "tool_calls") and step_result.tool_calls:
                        for tc in step_result.tool_calls:
                            if tc.tool_name == "__structured_output__":
                                route_cat = tc.result
                                break
                    # If not in metadata, extract from output text
                    if not route_cat:
                        route_cat = self._extract_category(step_result.output_summary)
                    if route_cat:
                        context_vars["route_category"] = route_cat

                span.event("step_done", step=step.name, agent=step.agent, hop=hop)

                # Terminal step?
                if step.is_terminal:
                    break

                # Route to next step
                next_step = self._route(step, step_result.output_summary, context_vars)
                if next_step is None:
                    break  # No more routing → done
                current_step_name = next_step

        duration_ms = (time.time() - start) * 1000
        self.memory.clear_task(request.id)

        return TaskResult(
            task_id=request.id,
            status=TaskStatus.COMPLETED,
            output="\n".join(output_parts),
            agent_trace=agent_trace,
            duration_ms=duration_ms,
        )

    def _route(self, step: WorkflowStep, output: str, context_vars: dict[str, Any]) -> str | None:
        """Determine next step based on routing rules.

        Supports two modes:
        - "structured": Extract category from structured output field (preferred)
        - "substring": Legacy substring matching (fallback)
        """
        if not step.routes:
            return None

        # Mode 1: Structured output routing (preferred)
        # Looks for "route_category" in context_vars (set by StructuredTriageAgent)
        if step.routing_mode == "structured":
            category = context_vars.get("route_category")
            if category:
                # Exact match against route keys (case-insensitive)
                for key, target in step.routes.items():
                    if key == "_default":
                        continue
                    if key.upper() == category.upper():
                        telemetry.log("workflow.routed", from_step=step.name, key=key, to=target, mode="structured")
                        return target
                # Fall to default
                default = step.routes.get("_default")
                if default:
                    telemetry.log("workflow.routed", from_step=step.name, key="_default", to=default, mode="structured_default")
                    return default

            # Structured mode fallback: try to extract category from output text
            # Pattern: "CATEGORY: XXX" or json {"category": "XXX"}
            extracted = self._extract_category(output)
            if extracted:
                context_vars["route_category"] = extracted
                for key, target in step.routes.items():
                    if key == "_default":
                        continue
                    if key.upper() == extracted.upper():
                        telemetry.log("workflow.routed", from_step=step.name, key=key, to=target, mode="extracted")
                        return target

        # Mode 2: Substring matching (legacy fallback)
        output_upper = output.upper()
        for key, target in step.routes.items():
            if key == "_default":
                continue
            if key.upper() in output_upper:
                telemetry.log("workflow.routed", from_step=step.name, key=key, to=target, mode="substring")
                return target

        # Default route
        default = step.routes.get("_default")
        if default:
            telemetry.log("workflow.routed", from_step=step.name, key="_default", to=default, mode="default")
            return default

        return None

    @staticmethod
    def _extract_category(output: str) -> str | None:
        """Extract category from LLM output text.

        Handles:
        - "CATEGORY: ORDER_STATUS" format
        - JSON: {"category": "ORDER_STATUS"}
        - Bare category on its own line
        """
        import json as _json

        # Try regex: CATEGORY: XXX
        match = re.search(r"(?:CATEGORY|category)[:\s]+([A-Za-z_]+)", output, re.IGNORECASE)
        if match:
            return match.group(1)

        # Try JSON extraction
        try:
            start = output.find("{")
            end = output.rfind("}") + 1
            if start >= 0 and end > start:
                data = _json.loads(output[start:end])
                if "category" in data:
                    return str(data["category"]).upper()
        except (ValueError, _json.JSONDecodeError):
            pass

        return None

    def _eval_condition(self, condition: str, context_vars: dict[str, Any]) -> bool:
        """Evaluate a simple condition expression safely.

        Supports: "var > N", "var < N", "var == value", "var in [a,b,c]"
        """
        try:
            # Simple numeric comparisons
            match = re.match(r"(\w+)\s*(>|<|>=|<=|==|!=)\s*(.+)", condition)
            if match:
                var_name, op, value = match.groups()
                var_val = context_vars.get(var_name)
                if var_val is None:
                    return False

                # Try numeric comparison
                try:
                    num_val = float(value.strip())
                    var_num = float(var_val)
                    ops = {">": lambda a, b: a > b, "<": lambda a, b: a < b,
                           ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
                           "==": lambda a, b: a == b, "!=": lambda a, b: a != b}
                    return ops[op](var_num, num_val)
                except (ValueError, TypeError):
                    # String comparison
                    return str(var_val).strip() == value.strip().strip("'\"")

            return False
        except Exception:
            return False
