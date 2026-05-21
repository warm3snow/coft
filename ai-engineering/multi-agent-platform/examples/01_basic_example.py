"""Example 01: Basic usage of the multi-agent platform.

Demonstrates:
    - Creating an Orchestrator
    - Submitting a simple task
    - Viewing the result and trace
"""

import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from multi_agent_platform.config import PlatformConfig, LLMConfig
from multi_agent_platform.orchestrator import Orchestrator
from multi_agent_platform.types import TaskRequest
from multi_agent_platform.observability import telemetry


def main():
    """Run a basic task through the multi-agent platform."""

    # Configure (uses env vars: LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, LLM_BASE_URL)
    config = PlatformConfig()

    # Create orchestrator
    orchestrator = Orchestrator(config)

    # Submit a task
    request = TaskRequest(
        tenant_id="demo-tenant",
        user_input="Write a Python function that checks if a number is prime. "
        "Include type hints and a docstring.",
    )

    print(f"🚀 Submitting task: {request.id}")
    print(f"   Input: {request.user_input}")
    print("-" * 60)

    # Execute
    result = orchestrator.run(request)

    # Display results
    print(f"\n📋 Result:")
    print(f"   Status: {result.status.value}")
    print(f"   Duration: {result.duration_ms:.0f}ms")
    print(f"   Tokens used: {result.total_tokens}")
    print(f"\n📝 Output:")
    print(result.output)

    if result.error:
        print(f"\n❌ Error: {result.error}")

    # Show trace
    print(f"\n🔍 Agent Trace ({len(result.agent_trace)} steps):")
    for i, step in enumerate(result.agent_trace):
        print(f"   [{i+1}] {step.agent_role} -> {step.action} ({step.duration_ms:.0f}ms)")
        if step.tool_calls:
            for tc in step.tool_calls:
                status = "✓" if tc.success else "✗"
                print(f"       {status} {tc.tool_name}({tc.duration_ms:.0f}ms)")

    # Show metrics
    print(f"\n📊 Platform Metrics:")
    metrics = telemetry.metrics.summary()
    for k, v in metrics.items():
        print(f"   {k}: {v}")


if __name__ == "__main__":
    main()
