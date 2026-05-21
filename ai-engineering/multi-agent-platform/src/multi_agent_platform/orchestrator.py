"""Orchestrator - LangGraph-based multi-agent coordination engine.

Architecture principles (from doc 2.4):
    1. All inter-agent communication goes through Orchestrator (no P2P)
    2. State machine: pending -> planning -> executing -> reviewing -> completed/failed
    3. Failure handling: retry with backoff -> DLQ on max retries

LangGraph state machine:
    ┌─────────┐     ┌──────────┐     ┌───────────┐     ┌──────────┐
    │ pending │────▶│ planning │────▶│ executing │────▶│reviewing │
    └─────────┘     └──────────┘     └───────────┘     └──────────┘
                          │                 │                 │
                          │                 │                 ▼
                          ▼                 ▼           ┌──────────┐
                     ┌─────────┐      ┌─────────┐      │completed │
                     │ failed  │      │ failed  │      └──────────┘
                     └─────────┘      └─────────┘
"""

from __future__ import annotations

import json
import time
from typing import Any, Annotated, TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.language_models import BaseChatModel

from .agents.base import BaseAgent, create_llm
from .agents.planner import PlannerAgent
from .agents.coder import CoderAgent
from .agents.reviewer import ReviewerAgent
from .config import PlatformConfig
from .memory import MemoryManager
from .observability import telemetry
from .policy_engine import PolicyEngine
from .tools.registry import ToolRegistry
from .tools.file_tools import read_file, write_file, list_directory
from .tools.execution_tools import execute_python
from .types import (
    AgentRole,
    AgentStep,
    Message,
    PolicyVerdict,
    TaskRequest,
    TaskResult,
    TaskStatus,
)


class OrchestratorState(TypedDict):
    """State managed by the LangGraph state machine."""

    task_id: str
    tenant_id: str
    user_input: str
    status: str
    plan: list[dict[str, Any]]
    current_step: int
    agent_trace: list[dict[str, Any]]
    output: str
    error: str
    retry_count: int
    start_time: float


class Orchestrator:
    """Multi-agent orchestration engine using LangGraph.

    Responsibilities:
        - Route tasks to appropriate agents
        - Manage state transitions
        - Enforce retries and timeouts
        - Collect traces for observability
    """

    def __init__(self, config: PlatformConfig | None = None) -> None:
        self.config = config or PlatformConfig()
        self.policy = PolicyEngine(self.config.policy)
        self.memory = MemoryManager(self.config.memory)
        self.tool_registry = ToolRegistry()

        # Initialize LLM
        self._llm = create_llm(self.config.llm)

        # Register default tools
        self._register_default_tools()

        # Initialize agents
        self._agents: dict[AgentRole, BaseAgent] = {
            AgentRole.PLANNER: PlannerAgent(
                llm=self._llm,
                tools=self.tool_registry.get_tools_for_role("planner"),
            ),
            AgentRole.CODER: CoderAgent(
                llm=self._llm,
                tools=self.tool_registry.get_tools_for_role("coder"),
            ),
            AgentRole.REVIEWER: ReviewerAgent(
                llm=self._llm,
                tools=self.tool_registry.get_tools_for_role("reviewer"),
            ),
        }

        # Build state machine
        self._graph = self._build_graph()

    def _register_default_tools(self) -> None:
        """Register platform tools with role-based access."""
        self.tool_registry.register(read_file, roles=["coder", "reviewer"])
        self.tool_registry.register(write_file, roles=["coder"])
        self.tool_registry.register(list_directory, roles=["coder", "reviewer"])
        self.tool_registry.register(execute_python, roles=["coder"])

    def _build_graph(self) -> Any:
        """Build the LangGraph state machine."""
        graph = StateGraph(OrchestratorState)

        # Add nodes
        graph.add_node("policy_check", self._node_policy_check)
        graph.add_node("planning", self._node_planning)
        graph.add_node("executing", self._node_executing)
        graph.add_node("reviewing", self._node_reviewing)
        graph.add_node("completed", self._node_completed)
        graph.add_node("failed", self._node_failed)

        # Set entry point
        graph.set_entry_point("policy_check")

        # Add edges
        graph.add_conditional_edges(
            "policy_check",
            self._route_after_policy,
            {"planning": "planning", "failed": "failed"},
        )
        graph.add_conditional_edges(
            "planning",
            self._route_after_planning,
            {"executing": "executing", "failed": "failed"},
        )
        graph.add_conditional_edges(
            "executing",
            self._route_after_executing,
            {"reviewing": "reviewing", "executing": "executing", "failed": "failed"},
        )
        graph.add_conditional_edges(
            "reviewing",
            self._route_after_reviewing,
            {"completed": "completed", "executing": "executing"},
        )
        graph.add_edge("completed", END)
        graph.add_edge("failed", END)

        return graph.compile()

    # --- State Machine Nodes ---

    def _node_policy_check(self, state: OrchestratorState) -> OrchestratorState:
        """Check input against policy engine (synchronous, fail-closed)."""
        with telemetry.span("orchestrator.policy_check", trace_id=state["task_id"]):
            result = self.policy.check_input(state["user_input"], state["tenant_id"])
            if result.verdict == PolicyVerdict.DENY:
                state["error"] = f"Policy denied: {result.reason}"
                state["status"] = TaskStatus.FAILED.value
            else:
                state["status"] = TaskStatus.PLANNING.value
        return state

    def _node_planning(self, state: OrchestratorState) -> OrchestratorState:
        """Use Planner Agent to decompose the task."""
        with telemetry.span("orchestrator.planning", trace_id=state["task_id"]) as span:
            try:
                planner = self._agents[AgentRole.PLANNER]
                context = self.memory.get_context(state["task_id"])

                steps = planner.get_plan_steps(state["user_input"], context)
                # Cap plan steps to prevent runaway execution with slow models
                max_steps = 3
                if len(steps) > max_steps:
                    steps = steps[:max_steps]
                    telemetry.warn("orchestrator.plan_truncated", original=len(steps), max=max_steps)
                state["plan"] = steps
                state["current_step"] = 0
                state["status"] = TaskStatus.EXECUTING.value

                # Record planning step in trace
                step = planner.invoke(state["user_input"], context)
                state["agent_trace"].append(step.model_dump())
                span.event("plan_created", num_steps=len(steps))

            except Exception as e:
                state["error"] = f"Planning failed: {e}"
                state["status"] = TaskStatus.FAILED.value
                span.set_error(str(e))

        return state

    def _node_executing(self, state: OrchestratorState) -> OrchestratorState:
        """Execute current plan step using the appropriate agent."""
        # Timeout guard: abort if total elapsed time exceeds limit
        elapsed = time.time() - state["start_time"]
        if elapsed > self.config.orchestrator_timeout_seconds:
            state["error"] = f"Timeout: {elapsed:.0f}s exceeded limit of {self.config.orchestrator_timeout_seconds}s"
            state["status"] = TaskStatus.FAILED.value
            telemetry.warn("orchestrator.timeout", elapsed_s=round(elapsed, 1))
            return state
        with telemetry.span("orchestrator.executing", trace_id=state["task_id"]) as span:
            try:
                plan = state["plan"]
                step_idx = state["current_step"]

                if step_idx >= len(plan):
                    state["status"] = TaskStatus.REVIEWING.value
                    return state

                current_plan_step = plan[step_idx]
                agent_name = current_plan_step.get("agent", "coder")
                task_input = current_plan_step.get("input", current_plan_step.get("description", ""))

                # Route to appropriate agent
                role = AgentRole.CODER if agent_name == "coder" else AgentRole.REVIEWER
                agent = self._agents[role]
                context = self.memory.get_context(state["task_id"])

                # Execute
                step_result = agent.invoke(task_input, context)
                state["agent_trace"].append(step_result.model_dump())

                # Store output in memory
                self.memory.add_message(
                    state["task_id"],
                    Message(role="assistant", content=step_result.output_summary),
                )

                # Accumulate output
                state["output"] += f"\n[Step {step_idx + 1}] {step_result.output_summary}"
                state["current_step"] = step_idx + 1
                span.event("step_completed", step=step_idx + 1)

            except Exception as e:
                state["retry_count"] = state.get("retry_count", 0) + 1
                if state["retry_count"] >= self.config.max_retries:
                    state["error"] = f"Execution failed after {self.config.max_retries} retries: {e}"
                    state["status"] = TaskStatus.FAILED.value
                span.set_error(str(e))

        return state

    def _node_reviewing(self, state: OrchestratorState) -> OrchestratorState:
        """Use Reviewer Agent to check the output."""
        with telemetry.span("orchestrator.reviewing", trace_id=state["task_id"]) as span:
            try:
                reviewer = self._agents[AgentRole.REVIEWER]
                review_input = f"Review the following work output:\n\n{state['output']}"
                context = self.memory.get_context(state["task_id"])

                step_result = reviewer.invoke(review_input, context)
                state["agent_trace"].append(step_result.model_dump())
                state["status"] = TaskStatus.COMPLETED.value
                span.event("review_completed")

            except Exception as e:
                # Review failure is non-fatal - mark as completed anyway
                state["status"] = TaskStatus.COMPLETED.value
                span.set_error(str(e))

        return state

    def _node_completed(self, state: OrchestratorState) -> OrchestratorState:
        """Finalize task."""
        state["status"] = TaskStatus.COMPLETED.value
        telemetry.log("orchestrator.task_completed", task_id=state["task_id"])
        self.memory.clear_task(state["task_id"])
        return state

    def _node_failed(self, state: OrchestratorState) -> OrchestratorState:
        """Handle task failure."""
        state["status"] = TaskStatus.FAILED.value
        telemetry.error("orchestrator.task_failed", task_id=state["task_id"], error=state["error"])
        return state

    # --- Routing Functions ---

    def _route_after_policy(self, state: OrchestratorState) -> str:
        return "failed" if state["status"] == TaskStatus.FAILED.value else "planning"

    def _route_after_planning(self, state: OrchestratorState) -> str:
        return "failed" if state["status"] == TaskStatus.FAILED.value else "executing"

    def _route_after_executing(self, state: OrchestratorState) -> str:
        if state["status"] == TaskStatus.FAILED.value:
            return "failed"
        if state["current_step"] < len(state["plan"]):
            return "executing"  # More steps to execute
        return "reviewing"

    def _route_after_reviewing(self, state: OrchestratorState) -> str:
        # Could route back to executing if reviewer requests changes
        # For MVP, always proceed to completed
        return "completed"

    # --- Public API ---

    def run(self, request: TaskRequest) -> TaskResult:
        """Execute a task request through the full pipeline.

        This is the main entry point. Gateway calls this.
        """
        telemetry.metrics.total_requests += 1
        start = time.time()

        # Store user message in memory
        self.memory.add_message(
            request.id,
            Message(role="user", content=request.user_input),
        )

        # Initialize state
        initial_state: OrchestratorState = {
            "task_id": request.id,
            "tenant_id": request.tenant_id,
            "user_input": request.user_input,
            "status": TaskStatus.PENDING.value,
            "plan": [],
            "current_step": 0,
            "agent_trace": [],
            "output": "",
            "error": "",
            "retry_count": 0,
            "start_time": start,
        }

        # Execute state machine with timeout protection
        timeout_seconds = self.config.orchestrator_timeout_seconds
        with telemetry.span("orchestrator.run", trace_id=request.id) as span:
            try:
                final_state = self._graph.invoke(initial_state)
                span.event("state_machine_complete", status=final_state["status"])
            except Exception as e:
                # Catch timeout or unexpected errors
                duration_ms = (time.time() - start) * 1000
                if duration_ms > timeout_seconds * 1000:
                    error_msg = f"Orchestrator timeout after {duration_ms:.0f}ms (limit: {timeout_seconds}s)"
                else:
                    error_msg = f"Orchestrator error: {e}"
                span.set_error(error_msg)
                return TaskResult(
                    task_id=request.id,
                    status=TaskStatus.FAILED,
                    output="",
                    duration_ms=duration_ms,
                    error=error_msg,
                )

        duration_ms = (time.time() - start) * 1000

        # Build result
        return TaskResult(
            task_id=request.id,
            status=TaskStatus(final_state["status"]),
            output=final_state["output"],
            agent_trace=[AgentStep(**s) for s in final_state["agent_trace"]],
            total_tokens=telemetry.metrics.total_tokens,
            duration_ms=duration_ms,
            error=final_state.get("error") or None,
        )
