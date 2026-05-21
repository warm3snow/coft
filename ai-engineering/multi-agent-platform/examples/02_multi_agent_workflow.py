"""Example 02: Multi-agent workflow - Planner -> Coder -> Reviewer.

Demonstrates:
    - Full pipeline: plan decomposition, code generation, code review
    - Agent collaboration through Orchestrator
    - Observability (trace, metrics)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from multi_agent_platform.config import PlatformConfig, LLMConfig
from multi_agent_platform.orchestrator import Orchestrator
from multi_agent_platform.types import TaskRequest
from multi_agent_platform.observability import telemetry


def main():
    """Run a multi-step task that requires planner + coder + reviewer."""

    config = PlatformConfig()

    orchestrator = Orchestrator(config)

    # A more complex task that benefits from planning
    request = TaskRequest(
        tenant_id="demo-tenant",
        user_input="""Create a simple Python module for a task queue with the following:
1. A Task class with id, title, status (pending/running/done), and created_at
2. A TaskQueue class that can:
   - add_task(title) -> Task
   - get_next() -> Task (FIFO, only pending tasks)
   - complete(task_id) -> bool
   - list_tasks(status_filter=None) -> list[Task]
3. Write it to 'task_queue.py'
4. Write a simple test that demonstrates it works""",
    )

    print("=" * 60)
    print("Multi-Agent Workflow Demo")
    print("=" * 60)
    print(f"\nTask: {request.user_input[:100]}...")
    print(f"Task ID: {request.id}")
    print("-" * 60)

    # Execute
    result = orchestrator.run(request)

    # Results
    print(f"\n{'='*60}")
    print(f"RESULT: {result.status.value}")
    print(f"{'='*60}")
    print(f"Duration: {result.duration_ms:.0f}ms")
    print(f"Total tokens: {result.total_tokens}")

    print(f"\n--- Output ---")
    print(result.output[:2000])

    # Detailed trace
    print(f"\n--- Agent Trace ---")
    for i, step in enumerate(result.agent_trace):
        print(f"\n  Step {i+1}: {step.agent_role}")
        print(f"    Action: {step.action}")
        print(f"    Duration: {step.duration_ms:.0f}ms")
        print(f"    Output: {step.output_summary[:100]}...")
        if step.tool_calls:
            print(f"    Tools used:")
            for tc in step.tool_calls:
                print(f"      - {tc.tool_name}: {'OK' if tc.success else 'FAILED'}")

    # Metrics
    print(f"\n--- Metrics ---")
    for k, v in telemetry.metrics.summary().items():
        if v:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
