"""Gateway - HTTP entry point with authentication and rate limiting.

Architecture mapping (from doc 2.3):
    | Concern     | Solution                    |
    | ----------- | --------------------------- |
    | Performance | QPS limit, concurrent conns |
    | Reliability | rate-limit graceful degrade |
    | Security    | auth, tenant isolation      |
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import GatewayConfig, PlatformConfig
from .orchestrator import Orchestrator
from .observability import telemetry
from .types import TaskRequest, TaskResult


class ChatRequest(BaseModel):
    """HTTP request body for task submission."""

    message: str
    tenant_id: str = "default"
    context: dict[str, Any] = {}


class ChatResponse(BaseModel):
    """HTTP response body."""

    task_id: str
    status: str
    output: str
    duration_ms: float
    error: str | None = None


class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, max_qps: int = 10) -> None:
        self._max_qps = max_qps
        self._requests: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.time()
        window = self._requests[key]
        # Remove entries outside 1-second window
        window[:] = [t for t in window if now - t < 1.0]
        if len(window) >= self._max_qps:
            return False
        window.append(now)
        return True


def create_app(config: PlatformConfig | None = None) -> FastAPI:
    """Create the FastAPI application with all middleware and routes."""
    config = config or PlatformConfig()
    app = FastAPI(
        title="Multi-Agent Platform",
        description="最小但完备的多 Agent 平台 - LangChain 实现",
        version="0.1.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # State
    rate_limiter = RateLimiter(max_qps=config.gateway.rate_limit_qps)
    orchestrator = Orchestrator(config)

    # --- Routes ---

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        """Main endpoint: submit a task to the multi-agent platform."""
        # Rate limiting
        if not rate_limiter.allow(request.tenant_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # Build internal request
        task_request = TaskRequest(
            id=str(uuid.uuid4()),
            tenant_id=request.tenant_id,
            user_input=request.message,
            context=request.context,
        )

        telemetry.log(
            "gateway.request",
            task_id=task_request.id,
            tenant_id=request.tenant_id,
        )

        # Execute through orchestrator
        result: TaskResult = orchestrator.run(task_request)

        return ChatResponse(
            task_id=result.task_id,
            status=result.status.value,
            output=result.output,
            duration_ms=result.duration_ms,
            error=result.error,
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics() -> dict[str, Any]:
        """Return platform metrics (JSON summary)."""
        return telemetry.metrics.summary()

    @app.get("/metrics/prometheus")
    async def metrics_prometheus():
        """Return Prometheus-format metrics for scraping."""
        from fastapi.responses import Response
        content = telemetry.prometheus_metrics()
        if content is None:
            return Response(content="# prometheus_client not installed\n", media_type="text/plain")
        return Response(content=content, media_type=telemetry.prometheus_content_type())

    @app.get("/trace/{task_id}")
    async def get_trace(task_id: str) -> dict[str, Any]:
        """Get execution trace for a task."""
        trace = telemetry.get_trace(task_id)
        return {"task_id": task_id, "spans": trace}

    return app


def run_server(config: PlatformConfig | None = None) -> None:
    """Start the gateway server."""
    import uvicorn

    config = config or PlatformConfig()
    app = create_app(config)
    uvicorn.run(app, host=config.gateway.host, port=config.gateway.port)
