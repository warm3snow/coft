"""File system tools - read, write, and list operations.

Security: All operations are confined to the workspace directory.
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_core.tools import tool

from ..observability import telemetry

# Default workspace - overridden by config
_WORKSPACE = "/tmp/agent_workspace"


def set_workspace(path: str) -> None:
    """Set the workspace directory for file tools."""
    global _WORKSPACE
    _WORKSPACE = path
    os.makedirs(path, exist_ok=True)


def _safe_path(relative_path: str) -> Path:
    """Resolve a path safely within the workspace (prevent path traversal)."""
    workspace = Path(_WORKSPACE).resolve()
    target = (workspace / relative_path).resolve()
    if not str(target).startswith(str(workspace)):
        raise ValueError(f"Path traversal attempt blocked: {relative_path}")
    return target


@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file from the workspace.

    Args:
        file_path: Relative path within the workspace directory.

    Returns:
        File contents as a string, or an error message.
    """
    try:
        target = _safe_path(file_path)
        if not target.exists():
            return f"Error: file not found: {file_path}"
        if not target.is_file():
            return f"Error: not a file: {file_path}"
        content = target.read_text(encoding="utf-8")
        telemetry.metrics.record_tool_call("read_file")
        return content
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file in the workspace.

    Args:
        file_path: Relative path within the workspace directory.
        content: The content to write to the file.

    Returns:
        Success message or error description.
    """
    try:
        target = _safe_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        telemetry.metrics.record_tool_call("write_file")
        return f"Successfully wrote {len(content)} bytes to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def list_directory(dir_path: str = ".") -> str:
    """List files and directories in the workspace.

    Args:
        dir_path: Relative path within the workspace (default: root).

    Returns:
        Formatted directory listing.
    """
    try:
        target = _safe_path(dir_path)
        if not target.exists():
            return f"Error: directory not found: {dir_path}"
        if not target.is_dir():
            return f"Error: not a directory: {dir_path}"

        entries = []
        for entry in sorted(target.iterdir()):
            prefix = "📁 " if entry.is_dir() else "📄 "
            size = entry.stat().st_size if entry.is_file() else 0
            entries.append(f"{prefix}{entry.name} ({size} bytes)")

        telemetry.metrics.record_tool_call("list_directory")
        return "\n".join(entries) if entries else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {e}"
