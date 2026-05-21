"""Shared type definitions for the multi-agent platform."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(str, Enum):
    """Built-in agent roles. Custom roles use string identifiers directly."""

    PLANNER = "planner"
    CODER = "coder"
    REVIEWER = "reviewer"
    # Enterprise scenario roles
    TRIAGE = "triage"
    CUSTOM = "custom"


class PolicyVerdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class Message(BaseModel):
    """A message exchanged between components."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskRequest(BaseModel):
    """Incoming task request from user via Gateway."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_input: str
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskResult(BaseModel):
    """Result of a completed task."""

    task_id: str
    status: TaskStatus
    output: str = ""
    artifacts: dict[str, Any] = Field(default_factory=dict)
    agent_trace: list[AgentStep] = Field(default_factory=list)
    total_tokens: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None


class AgentStep(BaseModel):
    """A single step in an agent's execution trace."""

    agent_role: str  # Now accepts any string (not just AgentRole enum)
    action: str  # "plan" | "execute_tool" | "respond" | "delegate" | "triage"
    input_summary: str
    output_summary: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tokens_used: int = 0
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolCall(BaseModel):
    """Record of a tool invocation."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: str = ""
    success: bool = True
    duration_ms: float = 0.0


class PolicyCheckResult(BaseModel):
    """Result from the Policy Engine."""

    verdict: PolicyVerdict
    reason: str = ""
    checked_at: datetime = Field(default_factory=datetime.utcnow)


# Rebuild models that have forward references
TaskResult.model_rebuild()
AgentStep.model_rebuild()
