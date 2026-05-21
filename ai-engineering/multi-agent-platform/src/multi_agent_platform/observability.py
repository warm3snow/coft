"""Observability layer - structured logging, tracing, and metrics.

Architecture mapping (from doc 2.3):
    | Layer         | Observability concern       |
    | ------------- | --------------------------- |
    | Gateway       | QPS, concurrent connections |
    | Orchestrator  | scheduling latency          |
    | Policy Engine | sync latency <= 50ms        |
    | Memory / RAG  | recall latency              |
    | Tool Layer    | single tool SLA             |
    | Observability | trace completeness, audit   |
"""

from __future__ import annotations

import time
import json
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator

try:
    import structlog
    import os

    _log_format = os.getenv("LOG_FORMAT", "console")  # "console" | "json"

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer() if _log_format != "json" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    _HAS_STRUCTLOG = True
except ImportError:
    _HAS_STRUCTLOG = False

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST

    _prom_requests = Counter("platform_requests_total", "Total requests processed", ["tenant_id", "status"])
    _prom_tokens = Counter("platform_tokens_total", "Total LLM tokens consumed", ["model"])
    _prom_agent_calls = Counter("platform_agent_calls_total", "Agent invocations", ["agent_role"])
    _prom_tool_calls = Counter("platform_tool_calls_total", "Tool invocations", ["tool_name"])
    _prom_errors = Counter("platform_errors_total", "Total errors")
    _prom_policy_denials = Counter("platform_policy_denials_total", "Policy denials")
    _prom_request_duration = Histogram(
        "platform_request_duration_ms", "Request duration in milliseconds",
        buckets=[50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000],
    )
    _prom_active_requests = Gauge("platform_active_requests", "Currently processing requests")
    _HAS_PROMETHEUS = True
except ImportError:
    _HAS_PROMETHEUS = False


@dataclass
class Span:
    """A single span in a trace - records one operation."""

    name: str
    trace_id: str
    span_id: str = ""
    parent_span_id: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    attrs: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # "ok" | "error"

    @property
    def duration_ms(self) -> float:
        if self.end_time == 0.0:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def event(self, name: str, **kwargs: Any) -> None:
        self.events.append({"name": name, "time": time.time(), **kwargs})

    def set_error(self, error: str) -> None:
        self.status = "error"
        self.attrs["error"] = error

    def finish(self) -> None:
        self.end_time = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "duration_ms": self.duration_ms,
            "attrs": self.attrs,
            "events": self.events,
            "status": self.status,
        }


@dataclass
class Metrics:
    """Lightweight metrics collector for the platform."""

    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    agent_invocations: dict[str, int] = field(default_factory=dict)
    tool_invocations: dict[str, int] = field(default_factory=dict)
    error_count: int = 0
    policy_denials: int = 0

    def record_tokens(self, tokens: int, model: str = "unknown") -> None:
        self.total_tokens += tokens
        # Rough cost estimation
        cost_per_1k = {"gpt-4o": 0.005, "claude-sonnet-4-20250514": 0.003}.get(model, 0.01)
        self.total_cost_usd += (tokens / 1000) * cost_per_1k
        if _HAS_PROMETHEUS:
            _prom_tokens.labels(model=model).inc(tokens)

    def record_agent_call(self, agent_role: str) -> None:
        self.agent_invocations[agent_role] = self.agent_invocations.get(agent_role, 0) + 1
        if _HAS_PROMETHEUS:
            _prom_agent_calls.labels(agent_role=agent_role).inc()

    def record_tool_call(self, tool_name: str) -> None:
        self.tool_invocations[tool_name] = self.tool_invocations.get(tool_name, 0) + 1
        if _HAS_PROMETHEUS:
            _prom_tool_calls.labels(tool_name=tool_name).inc()

    def record_error(self) -> None:
        self.error_count += 1
        if _HAS_PROMETHEUS:
            _prom_errors.inc()

    def record_policy_denial(self) -> None:
        self.policy_denials += 1
        if _HAS_PROMETHEUS:
            _prom_policy_denials.inc()

    def record_request(self, tenant_id: str = "", status: str = "completed", duration_ms: float = 0) -> None:
        """Record a completed request with Prometheus metrics."""
        self.total_requests += 1
        if _HAS_PROMETHEUS:
            _prom_requests.labels(tenant_id=tenant_id, status=status).inc()
            _prom_request_duration.observe(duration_ms)

    def summary(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "agent_invocations": self.agent_invocations,
            "tool_invocations": self.tool_invocations,
            "error_count": self.error_count,
            "policy_denials": self.policy_denials,
        }


class Telemetry:
    """Unified telemetry: logging + tracing + metrics.

    Features:
        - FIFO trace eviction (max_traces=1000) to prevent OOM
        - Prometheus metrics integration (optional)
        - reset() for clean test isolation
    """

    MAX_TRACES = 1000  # FIFO eviction threshold

    def __init__(self) -> None:
        if _HAS_STRUCTLOG:
            self.logger = structlog.get_logger()
        else:
            import logging
            logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
            self.logger = logging.getLogger("multi_agent_platform")
        self.metrics = Metrics()
        self._traces: OrderedDict[str, list[Span]] = OrderedDict()

    def reset(self) -> None:
        """Reset all metrics and traces. Use between tests for clean isolation."""
        self.metrics = Metrics()
        self._traces.clear()

    @contextmanager
    def span(
        self, name: str, trace_id: str = "", **attrs: Any
    ) -> Generator[Span, None, None]:
        """Context manager that creates and auto-finishes a span."""
        import uuid

        span = Span(
            name=name,
            trace_id=trace_id or str(uuid.uuid4()),
            span_id=str(uuid.uuid4())[:8],
            attrs=attrs,
        )

        # Store span in trace with FIFO eviction
        if span.trace_id not in self._traces:
            self._traces[span.trace_id] = []
            # Evict oldest traces if over limit
            while len(self._traces) > self.MAX_TRACES:
                self._traces.popitem(last=False)
        self._traces[span.trace_id].append(span)

        self.logger.info(f"span.start: {name}", extra={"span_name": name, "trace_id": span.trace_id})
        try:
            yield span
        except Exception as e:
            span.set_error(str(e))
            self.metrics.record_error()
            self.logger.error(f"span.error: {name} - {e}")
            raise
        finally:
            span.finish()
            self.logger.info(
                f"span.end: {name} duration={span.duration_ms:.2f}ms status={span.status}"
            )

    def get_trace(self, trace_id: str) -> list[dict[str, Any]]:
        """Get all spans for a trace as dicts."""
        return [s.to_dict() for s in self._traces.get(trace_id, [])]

    def log(self, event: str, **kwargs: Any) -> None:
        self.logger.info(f"{event} {kwargs}" if kwargs else event)

    def warn(self, event: str, **kwargs: Any) -> None:
        self.logger.warning(f"{event} {kwargs}" if kwargs else event)

    def error(self, event: str, **kwargs: Any) -> None:
        self.logger.error(f"{event} {kwargs}" if kwargs else event)

    @staticmethod
    def prometheus_metrics() -> bytes | None:
        """Generate Prometheus-format metrics output. Returns None if prometheus_client not installed."""
        if _HAS_PROMETHEUS:
            return generate_latest()
        return None

    @staticmethod
    def prometheus_content_type() -> str:
        """Content-Type header for Prometheus metrics endpoint."""
        if _HAS_PROMETHEUS:
            return CONTENT_TYPE_LATEST
        return "text/plain"


# Global singleton
telemetry = Telemetry()
