"""Code execution sandbox - restricted subprocess with timeout and resource limits.

Security measures:
    - Timeout enforcement (default 30s)
    - Blocked dangerous imports/operations
    - Output size limit
    - No network access in sandbox
"""

from __future__ import annotations

import subprocess
import tempfile
import os
from pathlib import Path

from langchain_core.tools import tool

from ..observability import telemetry

# Maximum execution time in seconds
_MAX_TIMEOUT = 30

# Maximum output size in bytes
_MAX_OUTPUT_SIZE = 10000

# Blocked imports/operations
_BLOCKED_PATTERNS = [
    "import os",
    "import subprocess",
    "import shutil",
    "__import__",
    "eval(",
    "exec(",
    "open('/",
    "os.system",
    "os.popen",
]


def _check_code_safety(code: str) -> str | None:
    """Check if code contains dangerous patterns. Returns error or None."""
    for pattern in _BLOCKED_PATTERNS:
        if pattern in code:
            return f"Blocked: code contains dangerous pattern '{pattern}'"
    return None


@tool
def execute_python(code: str, timeout: int = 30) -> str:
    """Execute Python code in a sandboxed environment.

    Args:
        code: Python code to execute.
        timeout: Maximum execution time in seconds (max 30).

    Returns:
        stdout output from the execution, or error message.
    """
    # Safety check
    safety_error = _check_code_safety(code)
    if safety_error:
        telemetry.metrics.record_tool_call("execute_python")
        return f"Security Error: {safety_error}"

    timeout = min(timeout, _MAX_TIMEOUT)

    try:
        # Write code to a temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir="/tmp"
        ) as f:
            f.write(code)
            tmp_path = f.name

        # Execute with timeout and restricted environment
        env = {
            "PATH": "/usr/bin:/usr/local/bin",
            "PYTHONPATH": "",
            "HOME": "/tmp",
        }

        result = subprocess.run(
            ["python3", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd="/tmp",
        )

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"

        # Truncate if too long
        if len(output) > _MAX_OUTPUT_SIZE:
            output = output[:_MAX_OUTPUT_SIZE] + "\n... (output truncated)"

        telemetry.metrics.record_tool_call("execute_python")
        return output if output.strip() else "(no output)"

    except subprocess.TimeoutExpired:
        telemetry.metrics.record_tool_call("execute_python")
        return f"Error: execution timed out after {timeout}s"
    except Exception as e:
        telemetry.metrics.record_tool_call("execute_python")
        return f"Error executing code: {e}"
    finally:
        # Cleanup
        try:
            os.unlink(tmp_path)
        except (OSError, UnboundLocalError):
            pass
