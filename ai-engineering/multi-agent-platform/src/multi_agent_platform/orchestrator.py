"""Orchestrator - framework-level coordination engine.

Execution modes:
    1. Default adaptive mode: chooses between a capability pipeline and ReAct.
       - Capability pipeline: planner -> specialists when the registry supports it.
       - ReAct fallback: a generic executor with shared tools.
    2. Custom workflow mode: YAML-defined conditional routing for app-specific flows.

Architecture:
    User → Gateway → Orchestrator → Agent Pool
                        │                │
            ┌───────────┤          ┌─────┼─────┐
            ▼           ▼          ▼     ▼     ▼
      PolicyEngine  Memory/RAG  AgentA AgentB AgentC
                                       │
                                       ▼
                                  Tool Layer
"""

from __future__ import annotations

import re
import time
from typing import Any

from .agent_registry import AgentRegistry, GenericAgent
from .agents.base import create_llm
from .agents.planner import PlannerAgent
from .agents.coder import CoderAgent
from .agents.reviewer import ReviewerAgent
from .config import PlatformConfig
from .memory import MemoryManager
from .observability import telemetry
from .policy_engine import PolicyEngine
from .tools.file_tools import set_workspace
from .tools.registry import ToolRegistry
from .tools.file_tools import read_file, write_file, list_directory
from .tools.execution_tools import execute_python
from .types import (
    AgentStep,
    Message,
    PolicyVerdict,
    TaskRequest,
    TaskResult,
    TaskStatus,
    ToolCall,
)
from .workflow_engine import WorkflowDefinition, WorkflowStep


# --- Default mode system prompt ---

DEFAULT_ORCHESTRATOR_PROMPT = """You are an autonomous task executor.
Given a user request, think step by step and use the available tools to accomplish it.
When the task is complete, provide a final summary answer without calling any tools.

Guidelines:
- Break complex tasks into smaller steps and execute them one by one.
- After each tool call, observe the result and decide the next action.
- If a tool call fails, try an alternative approach.
- When you have enough information to answer, respond directly without tool calls.

Think carefully before each action. Observe results and adjust your approach."""


class Orchestrator:
    """Framework-level multi-agent orchestrator.

    Default mode (no workflow) is adaptive rather than hardcoded to a single flow:
    - If the registry exposes planner plus specialist roles, Orchestrator can run
      a capability-driven pipeline.
    - Otherwise, it falls back to a generic ReAct executor over the shared toolset.

    Custom mode (with workflow) runs application-defined YAML routing.

    Usage:
        # Default mode - autonomous ReAct
        orchestrator = Orchestrator()
        result = orchestrator.run(request)

        # Custom mode - YAML workflow
        orchestrator = Orchestrator(agent_registry=my_registry)
        orchestrator.load_workflow_yaml(yaml_str)
        result = orchestrator.run(request, workflow_name="customer_service")
    """

    def __init__(
        self,
        config: PlatformConfig | None = None,
        agent_registry: AgentRegistry | None = None,
    ) -> None:
        self.config = config or PlatformConfig()
        self.policy = PolicyEngine(self.config.policy)
        self.memory = MemoryManager(self.config.memory)
        self.tool_registry = ToolRegistry()
        set_workspace(self.config.workspace_dir)

        # Initialize LLM
        self._llm = create_llm(self.config.llm)

        # Register default tools
        self._register_default_tools()

        # Agent registry (shared by both modes)
        self._agent_registry = agent_registry or self._create_default_registry()

        # Workflow storage (custom mode)
        self._workflows: dict[str, WorkflowDefinition] = {}

    @property
    def agent_registry(self) -> AgentRegistry:
        """Expose registry for external agent registration."""
        return self._agent_registry

    def _register_default_tools(self) -> None:
        """Register platform tools with role-based access."""
        self.tool_registry.register(read_file, roles=["coder", "reviewer", "orchestrator"])
        self.tool_registry.register(write_file, roles=["coder", "orchestrator"])
        self.tool_registry.register(list_directory, roles=["coder", "reviewer", "orchestrator"])
        self.tool_registry.register(execute_python, roles=["coder", "orchestrator"])

    def _create_default_registry(self) -> AgentRegistry:
        """Create registry pre-loaded with built-in reusable agent capabilities."""
        registry = AgentRegistry(self._llm, self.tool_registry)
        registry.register(
            "planner",
            system_prompt="You are a planning agent. Break tasks into clear, actionable steps.",
            agent_class=PlannerAgent,
            description="Task decomposition",
        )
        registry.register(
            "coder",
            system_prompt="You are a coding agent. Write clean, correct code.",
            tool_names=["read_file", "write_file", "list_directory", "execute_python"],
            agent_class=CoderAgent,
            description="Code generation with ReAct",
        )
        registry.register(
            "reviewer",
            system_prompt="You are a code reviewer. Check for correctness and quality.",
            tool_names=["read_file", "list_directory"],
            agent_class=ReviewerAgent,
            description="Code review",
        )
        return registry

    # --- Workflow Management (absorbed from WorkflowEngine) ---

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a workflow definition for custom mode."""
        self._workflows[workflow.name] = workflow
        telemetry.log("workflow.registered", name=workflow.name, steps=len(workflow.steps))

    def load_workflow_yaml(self, yaml_str: str) -> WorkflowDefinition:
        """Load and register a workflow from YAML string."""
        wf = WorkflowDefinition.from_yaml(yaml_str)
        self.register_workflow(wf)
        return wf

    def list_workflows(self) -> list[str]:
        """List registered workflow names."""
        return list(self._workflows.keys())

    # --- Public API ---

    def run(self, request: TaskRequest, workflow_name: str | None = None) -> TaskResult:
        """Execute a task request.

        Args:
            request: The task to execute.
            workflow_name: If provided, use YAML workflow mode.
                          If None, use default ReAct mode.

        Returns:
            TaskResult with status, output, agent trace, and metrics.
        """
        start = time.time()
        baseline_tokens = telemetry.metrics.total_tokens

        # Policy check (fail-closed, synchronous)
        with telemetry.span("orchestrator.policy_check", trace_id=request.id):
            policy_result = self.policy.check_input(request.user_input, request.tenant_id)
            if policy_result.verdict == PolicyVerdict.DENY:
                duration_ms = (time.time() - start) * 1000
                result = TaskResult(
                    task_id=request.id,
                    status=TaskStatus.FAILED,
                    output="",
                    duration_ms=duration_ms,
                    error=f"Policy denied: {policy_result.reason}",
                )
                return self._finalize_result(request, result, start, baseline_tokens)

        # Store user message in memory
        self.memory.add_message(
            request.id,
            Message(role="user", content=request.user_input),
        )

        # Dispatch to appropriate mode
        if workflow_name:
            result = self._run_workflow(request, workflow_name, start)
        else:
            result = self._run_default(request, start)

        return self._finalize_result(request, result, start, baseline_tokens)

    # --- Default Mode: Adaptive Execution ---

    def _run_default(self, request: TaskRequest, start: float) -> TaskResult:
        """Execute using the default adaptive strategy.

        The framework first checks whether the registered agent set can support
        a planner-led capability pipeline for the current request. If not, it
        falls back to a generic ReAct executor over shared tools.
        """
        if self._should_use_capability_pipeline(request):
            try:
                pipeline_result = self._run_default_capability_pipeline(request)
                if pipeline_result is not None:
                    return pipeline_result
            except Exception as e:
                return TaskResult(
                    task_id=request.id,
                    status=TaskStatus.FAILED,
                    output="",
                    duration_ms=(time.time() - start) * 1000,
                    error=f"Capability pipeline failed: {e}",
                )

        max_iterations = 10
        timeout_seconds = self.config.orchestrator_timeout_seconds

        with telemetry.span("orchestrator.react_loop", trace_id=request.id) as span:
            try:
                # Get all tools for orchestrator role
                all_tools = self.tool_registry.get_tools_for_role("orchestrator")
                self._enforce_tool_access(request.tenant_id, all_tools)

                # Create orchestrator agent with all tools
                agent = GenericAgent(
                    role="orchestrator",
                    llm=self._llm,
                    tools=all_tools,
                    system_prompt=DEFAULT_ORCHESTRATOR_PROMPT,
                )

                # Override default max_iterations (GenericAgent uses 5)
                context = self.memory.get_context(request.id)

                # Execute ReAct loop with timeout protection
                # We call agent.invoke which does the ReAct internally.
                # For more iterations, we do the loop ourselves.
                from langchain_core.messages import ToolMessage as LCToolMessage

                messages = agent._build_messages(request.user_input, context)
                agent_trace: list[AgentStep] = []
                tool_calls_made: list[ToolCall] = []
                final_output = ""

                for iteration in range(max_iterations):
                    # Timeout check
                    elapsed = time.time() - start
                    if elapsed > timeout_seconds:
                        span.set_error(f"Timeout after {elapsed:.0f}s")
                        duration_ms = elapsed * 1000
                        self.memory.clear_task(request.id)
                        return TaskResult(
                            task_id=request.id,
                            status=TaskStatus.FAILED,
                            output=final_output,
                            agent_trace=agent_trace,
                            duration_ms=duration_ms,
                            error=f"Timeout: {elapsed:.0f}s exceeded limit of {timeout_seconds}s",
                        )

                    # Call LLM
                    response = agent._call_llm(messages, use_tools=bool(all_tools))

                    # Check for tool calls
                    if hasattr(response, "tool_calls") and response.tool_calls:
                        messages.append(response)
                        iteration_tools: list[ToolCall] = []

                        for tc in response.tool_calls:
                            tool_result = agent._execute_tool(tc["name"], tc["args"])
                            iteration_tools.append(tool_result)
                            tool_calls_made.append(tool_result)
                            messages.append(LCToolMessage(
                                content=tool_result.result,
                                tool_call_id=tc["id"],
                            ))

                        # Record step in trace
                        agent_trace.append(AgentStep(
                            agent_role="orchestrator",
                            action="tool_call",
                            input_summary=f"Iteration {iteration + 1}",
                            output_summary="; ".join(
                                f"{t.tool_name}→{'ok' if t.success else 'err'}"
                                for t in iteration_tools
                            ),
                            tool_calls=iteration_tools,
                        ))

                        span.event("react_iteration", iteration=iteration + 1, tools_called=len(iteration_tools))
                    else:
                        # No tool calls → final answer
                        final_output = response.content if hasattr(response, "content") else ""
                        self._enforce_output_policy(final_output)
                        agent_trace.append(AgentStep(
                            agent_role="orchestrator",
                            action="final_answer",
                            input_summary=request.user_input[:200],
                            output_summary=final_output[:500],
                        ))
                        span.event("react_complete", iterations=iteration + 1)
                        break
                else:
                    # Max iterations reached without final answer
                    final_output = response.content if (response and hasattr(response, "content")) else ""
                    if not final_output:
                        final_output = "[Max iterations reached]"

            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                span.set_error(str(e))
                self.memory.clear_task(request.id)
                return TaskResult(
                    task_id=request.id,
                    status=TaskStatus.FAILED,
                    output="",
                    agent_trace=agent_trace if 'agent_trace' in dir() else [],
                    duration_ms=duration_ms,
                    error=f"Orchestrator error: {e}",
                )

        return TaskResult(
            task_id=request.id,
            status=TaskStatus.COMPLETED,
            output=final_output,
            agent_trace=agent_trace,
            duration_ms=(time.time() - start) * 1000,
        )

    def _run_default_capability_pipeline(self, request: TaskRequest) -> TaskResult | None:
        """Run planner-led specialist execution when the registry supports it."""
        if not self._agent_registry.has("planner"):
            return None

        context = self.memory.get_context(request.id)
        try:
            plan_step = self._execute_agent_with_policy(request, "planner", request.user_input, context)
        except Exception:
            return None

        agent_trace: list[AgentStep] = [plan_step]

        plan_data = self._extract_plan_from_step(plan_step)
        if not plan_data or not plan_data.get("steps"):
            return None

        output_parts: list[str] = []
        last_output = ""

        for planned_step in plan_data["steps"]:
            agent_name = str(planned_step.get("agent", "coder"))
            if not self._agent_registry.has(agent_name):
                return None

            step_input = str(planned_step.get("input") or request.user_input)
            if last_output:
                step_input = f"{step_input}\n\nPrevious step output:\n{last_output}"

            step_result = self._execute_agent_with_policy(
                request,
                agent_name,
                step_input,
                self.memory.get_context(request.id),
            )
            agent_trace.append(step_result)
            output_parts.append(f"[{agent_name}] {step_result.output_summary}")
            last_output = step_result.output_summary

            self.memory.add_message(
                request.id,
                Message(role="assistant", content=step_result.output_summary, metadata={"step": agent_name}),
            )

        final_output = last_output or "\n".join(output_parts)
        if output_parts and final_output != "\n".join(output_parts):
            output_parts.append(f"[final] {final_output}")

        return TaskResult(
            task_id=request.id,
            status=TaskStatus.COMPLETED,
            output="\n".join(output_parts) if output_parts else final_output,
            agent_trace=agent_trace,
        )

    # --- Custom Mode: YAML Workflow ---

    def _run_workflow(self, request: TaskRequest, workflow_name: str, start: float) -> TaskResult:
        """Execute using YAML-defined workflow with conditional routing.

        Flow:
            1. Find workflow by name
            2. Find entry step
            3. Execute step → get output
            4. Route to next step based on output/conditions
            5. Repeat until terminal or no more routes
        """
        workflow = self._workflows.get(workflow_name)
        if workflow is None:
            duration_ms = (time.time() - start) * 1000
            return TaskResult(
                task_id=request.id,
                status=TaskStatus.FAILED,
                output="",
                duration_ms=duration_ms,
                error=f"Workflow '{workflow_name}' not found. Available: {self.list_workflows()}",
            )

        # Build step lookup
        step_map = {s.name: s for s in workflow.steps}
        agent_trace: list[AgentStep] = []
        output_parts: list[str] = []
        context_vars: dict[str, Any] = {"user_input": request.user_input}

        # Execute workflow
        current_step_name = workflow.entry_step
        max_hops = 10  # Safety: prevent infinite loops

        with telemetry.span("orchestrator.workflow", trace_id=request.id, workflow=workflow_name) as span:
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
                    agent = self._agent_registry.get(step.agent)
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
                    step_result = self._execute_agent_with_policy(
                        request,
                        step.agent,
                        request.user_input,
                        context,
                    )
                except Exception as e:
                    agent_trace.append(AgentStep(
                        agent_role=step.agent,
                        action="error",
                        input_summary=request.user_input[:200],
                        output_summary=f"Agent execution failed: {e}",
                    ))
                    output_parts.append(f"[{step.name}] Error: {e}")
                    duration_ms = (time.time() - start) * 1000
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
                if step.routes and step.routing_mode == "structured":
                    route_cat = None
                    if hasattr(step_result, "tool_calls") and step_result.tool_calls:
                        for tc in step_result.tool_calls:
                            if tc.tool_name == "__structured_output__":
                                route_cat = tc.result
                                break
                    if not route_cat:
                        route_cat = self._extract_category(step_result.output_summary)
                    if route_cat:
                        context_vars["route_category"] = route_cat

                span.event("step_done", step=step.name, agent=step.agent, hop=hop)

                # Terminal step?
                if step.is_terminal:
                    break

                # Route to next step
                next_step = self._route_workflow_step(step, step_result.output_summary, context_vars)
                if next_step is None:
                    break
                current_step_name = next_step

        return TaskResult(
            task_id=request.id,
            status=TaskStatus.COMPLETED,
            output="\n".join(output_parts),
            agent_trace=agent_trace,
            duration_ms=(time.time() - start) * 1000,
        )

    @staticmethod
    def _extract_plan_from_step(step: AgentStep) -> dict[str, Any] | None:
        """Extract structured plan JSON from a planner step."""
        output = step.output_summary or ""
        start_idx = output.find("{")
        end_idx = output.rfind("}") + 1
        if start_idx < 0 or end_idx <= start_idx:
            return None

        import json as _json

        try:
            return _json.loads(output[start_idx:end_idx])
        except (ValueError, _json.JSONDecodeError):
            return None

    def _should_use_capability_pipeline(self, request: TaskRequest) -> bool:
        """Decide whether the default path should use planner-led delegation."""
        if not all(self._agent_registry.has(role) for role in ("planner", "coder", "reviewer")):
            return False

        text = request.user_input.lower()
        keywords = (
            "write",
            "implement",
            "create",
            "modify",
            "refactor",
            "test",
            "code",
            "python",
            "module",
            "function",
        )
        return any(keyword in text for keyword in keywords)

    def _execute_agent_with_policy(
        self,
        request: TaskRequest,
        agent_name: str,
        task_input: str,
        context: list[Message] | None = None,
    ) -> AgentStep:
        """Run a registered agent with per-tool and output policy checks."""
        agent = self._agent_registry.get(agent_name)
        self._enforce_tool_access(request.tenant_id, agent.tools)
        step_result = agent.invoke(task_input, context)
        self._enforce_output_policy(step_result.output_summary)
        return step_result

    def _enforce_tool_access(self, tenant_id: str, tools: list[Any]) -> None:
        """Fail closed if tenant is not allowed to use a tool."""
        for tool in tools:
            verdict = self.policy.check_tool_access(tenant_id, tool.name)
            if verdict.verdict == PolicyVerdict.DENY:
                raise PermissionError(verdict.reason)

    def _enforce_output_policy(self, output: str) -> None:
        """Fail closed if agent output violates output policy."""
        verdict = self.policy.check_output(output)
        if verdict.verdict == PolicyVerdict.DENY:
            raise ValueError(verdict.reason)

    def _finalize_result(
        self,
        request: TaskRequest,
        result: TaskResult,
        start: float,
        baseline_tokens: int,
    ) -> TaskResult:
        """Apply consistent request-level accounting and cleanup."""
        final_duration = result.duration_ms or ((time.time() - start) * 1000)
        request_tokens = max(0, telemetry.metrics.total_tokens - baseline_tokens)
        telemetry.metrics.record_request(
            tenant_id=request.tenant_id,
            status=result.status.value,
            duration_ms=final_duration,
        )
        self.memory.clear_task(request.id)
        return result.model_copy(update={"duration_ms": final_duration, "total_tokens": request_tokens})

    # --- Workflow Routing Helpers ---

    def _route_workflow_step(
        self, step: WorkflowStep, output: str, context_vars: dict[str, Any]
    ) -> str | None:
        """Determine next step based on routing rules.

        Modes:
        - "structured": Extract category from structured output (preferred)
        - "substring": Legacy substring matching (fallback)
        """
        if not step.routes:
            return None

        # Mode 1: Structured output routing
        if step.routing_mode == "structured":
            category = context_vars.get("route_category")
            if category:
                for key, target in step.routes.items():
                    if key == "_default":
                        continue
                    if key.upper() == category.upper():
                        telemetry.log("workflow.routed", from_step=step.name, key=key, to=target, mode="structured")
                        return target
                default = step.routes.get("_default")
                if default:
                    telemetry.log("workflow.routed", from_step=step.name, key="_default", to=default, mode="structured_default")
                    return default

            # Fallback: extract category from output text
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
        """
        import json as _json

        # Try regex: CATEGORY: XXX
        match = re.search(r"(?:CATEGORY|category)[:\s]+([A-Za-z_]+)", output, re.IGNORECASE)
        if match:
            return match.group(1)

        # Try JSON extraction
        try:
            start_idx = output.find("{")
            end_idx = output.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                data = _json.loads(output[start_idx:end_idx])
                if "category" in data:
                    return str(data["category"]).upper()
        except (ValueError, _json.JSONDecodeError):
            pass

        return None

    def _eval_condition(self, condition: str, context_vars: dict[str, Any]) -> bool:
        """Evaluate a simple condition expression safely.

        Supports: "var > N", "var < N", "var == value"
        """
        try:
            match = re.match(r"(\w+)\s*(>|<|>=|<=|==|!=)\s*(.+)", condition)
            if match:
                var_name, op, value = match.groups()
                var_val = context_vars.get(var_name)
                if var_val is None:
                    return False

                try:
                    num_val = float(value.strip())
                    var_num = float(var_val)
                    ops = {
                        ">": lambda a, b: a > b, "<": lambda a, b: a < b,
                        ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
                        "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
                    }
                    return ops[op](var_num, num_val)
                except (ValueError, TypeError):
                    return str(var_val).strip() == value.strip().strip("'\"")

            return False
        except Exception:
            return False
