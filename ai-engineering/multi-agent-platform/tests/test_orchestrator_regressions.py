from __future__ import annotations

import json
from pathlib import Path

from multi_agent_platform.config import PlatformConfig
from multi_agent_platform.orchestrator import Orchestrator
from multi_agent_platform.tools.file_tools import read_file
from multi_agent_platform.types import AgentStep, TaskRequest
from multi_agent_platform.observability import telemetry


class FakeAgent:
    def __init__(self, role: str, output: str, tools=None, tokens: int = 0):
        self.role = role
        self.output = output
        self.tools = tools or []
        self.tokens = tokens

    def invoke(self, task: str, context=None) -> AgentStep:
        if self.tokens:
            telemetry.metrics.record_tokens(self.tokens, model="test-model")
        return AgentStep(
            agent_role=self.role,
            action="respond",
            input_summary=task[:200],
            output_summary=self.output,
            tokens_used=self.tokens,
        )


class FakeRegistry:
    def __init__(self, agents: dict[str, FakeAgent]):
        self._agents = agents

    def has(self, role: str) -> bool:
        return role in self._agents

    def get(self, role: str):
        if role not in self._agents:
            raise ValueError(role)
        return self._agents[role]


class NamedTool:
    def __init__(self, name: str):
        self.name = name


def _build_orchestrator(monkeypatch, tmp_path: Path, registry: FakeRegistry) -> Orchestrator:
    monkeypatch.setattr("multi_agent_platform.orchestrator.create_llm", lambda config: object())
    config = PlatformConfig(workspace_dir=str(tmp_path))
    return Orchestrator(config=config, agent_registry=registry)


def test_default_mode_uses_capability_pipeline(monkeypatch, tmp_path):
    plan = {
        "analysis": "Implement and review the requested code.",
        "steps": [
            {"step_id": 1, "description": "Write code", "agent": "coder", "input": "Create module", "depends_on": []},
            {"step_id": 2, "description": "Review code", "agent": "reviewer", "input": "Review module", "depends_on": [1]},
        ],
        "success_criteria": "Code is implemented and reviewed.",
    }
    registry = FakeRegistry(
        {
            "planner": FakeAgent("planner", json.dumps(plan), tokens=3),
            "coder": FakeAgent("coder", "implemented task_queue.py", tokens=5),
            "reviewer": FakeAgent("reviewer", "approved with no findings", tokens=7),
        }
    )
    orchestrator = _build_orchestrator(monkeypatch, tmp_path, registry)

    result = orchestrator.run(TaskRequest(tenant_id="tenant-a", user_input="Write a Python module for a task queue"))

    assert result.status.value == "completed"
    assert [str(step.agent_role) for step in result.agent_trace] == ["planner", "coder", "reviewer"]
    assert result.total_tokens == 15
    assert "[coder] implemented task_queue.py" in result.output
    assert "[reviewer] approved with no findings" in result.output


def test_default_mode_falls_back_to_react_without_pipeline_agents(monkeypatch, tmp_path):
    registry = FakeRegistry({})
    orchestrator = _build_orchestrator(monkeypatch, tmp_path, registry)

    monkeypatch.setattr(orchestrator, "_run_default_capability_pipeline", lambda request: None)

    class FakeReActAgent:
        def __init__(self, role, llm, tools, system_prompt):
            self.role = role
            self.llm = llm
            self.tools = tools
            self.system_prompt = system_prompt

        def _build_messages(self, task, context):
            return [task]

        def _call_llm(self, messages, use_tools=True):
            class Response:
                content = "react answer"
                tool_calls = []

            return Response()

        def _execute_tool(self, tool_name, arguments):
            raise AssertionError("should not call tools")

    monkeypatch.setattr("multi_agent_platform.orchestrator.GenericAgent", FakeReActAgent)

    result = orchestrator.run(TaskRequest(tenant_id="tenant-a", user_input="Summarize this ticket"))

    assert result.status.value == "completed"
    assert result.output == "react answer"
    assert [step.action for step in result.agent_trace] == ["final_answer"]


def test_total_tokens_are_scoped_per_request(monkeypatch, tmp_path):
    plan = {
        "analysis": "Implement and review the requested code.",
        "steps": [
            {"step_id": 1, "description": "Write code", "agent": "coder", "input": "Create module", "depends_on": []},
            {"step_id": 2, "description": "Review code", "agent": "reviewer", "input": "Review module", "depends_on": [1]},
        ],
        "success_criteria": "Code is implemented and reviewed.",
    }
    registry = FakeRegistry(
        {
            "planner": FakeAgent("planner", json.dumps(plan), tokens=2),
            "coder": FakeAgent("coder", "implemented", tokens=4),
            "reviewer": FakeAgent("reviewer", "reviewed", tokens=6),
        }
    )
    orchestrator = _build_orchestrator(monkeypatch, tmp_path, registry)

    first = orchestrator.run(TaskRequest(tenant_id="tenant-a", user_input="Write a Python function"))
    second = orchestrator.run(TaskRequest(tenant_id="tenant-a", user_input="Write another Python function"))

    assert first.total_tokens == 12
    assert second.total_tokens == 12
    assert telemetry.metrics.total_requests == 2


def test_workspace_dir_is_applied_to_file_tools(monkeypatch, tmp_path):
    orchestrator = _build_orchestrator(monkeypatch, tmp_path, FakeRegistry({}))
    assert orchestrator.config.workspace_dir == str(tmp_path)

    file_path = tmp_path / "note.txt"
    file_path.write_text("workspace-ok", encoding="utf-8")

    result = read_file.invoke({"file_path": "note.txt"})

    assert result == "workspace-ok"


def test_tool_access_denial_fails_closed(monkeypatch, tmp_path):
    plan = {
        "analysis": "Implement and review the requested code.",
        "steps": [
            {"step_id": 1, "description": "Write code", "agent": "coder", "input": "Create module", "depends_on": []},
        ],
        "success_criteria": "Code is implemented.",
    }
    registry = FakeRegistry(
        {
            "planner": FakeAgent("planner", json.dumps(plan)),
            "coder": FakeAgent("coder", "implemented", tools=[NamedTool("forbidden_tool")]),
            "reviewer": FakeAgent("reviewer", "reviewed"),
        }
    )
    orchestrator = _build_orchestrator(monkeypatch, tmp_path, registry)
    orchestrator.policy.register_tenant("locked-tenant", {"read_file"})

    result = orchestrator.run(TaskRequest(tenant_id="locked-tenant", user_input="Write a Python function"))

    assert result.status.value == "failed"
    assert "not authorized" in (result.error or "")


def test_output_policy_denial_fails_closed(monkeypatch, tmp_path):
    plan = {
        "analysis": "Implement and review the requested code.",
        "steps": [
            {"step_id": 1, "description": "Write code", "agent": "coder", "input": "Create module", "depends_on": []},
        ],
        "success_criteria": "Code is implemented.",
    }
    registry = FakeRegistry(
        {
            "planner": FakeAgent("planner", json.dumps(plan)),
            "coder": FakeAgent("coder", "Customer SSN: 123-45-6789"),
            "reviewer": FakeAgent("reviewer", "reviewed"),
        }
    )
    orchestrator = _build_orchestrator(monkeypatch, tmp_path, registry)

    result = orchestrator.run(TaskRequest(tenant_id="tenant-a", user_input="Write a Python function"))

    assert result.status.value == "failed"
    assert "PII" in (result.error or "")
