"""Configuration management for the multi-agent platform."""

from typing import Optional

from pydantic import BaseModel, Field

try:
    from pydantic_settings import BaseSettings
except ImportError:  # pragma: no cover - fallback for minimal test environments
    BaseSettings = BaseModel


class LLMConfig(BaseSettings):
    """LLM provider configuration - unified interface for all providers.

    Environment variables:
        LLM_PROVIDER   - "openai" | "anthropic" | "ollama" (default: "openai")
        LLM_MODEL      - Model name (e.g. "gpt-4o", "qwen2.5:7b", "claude-sonnet-4-20250514")
        LLM_API_KEY    - API key (not needed for local Ollama)
        LLM_BASE_URL   - API endpoint (e.g. "http://localhost:11434/v1")
        LLM_TEMPERATURE - Temperature (default: 0.0)
        LLM_MAX_TOKENS  - Max tokens (default: 4096)
    """

    provider: str = Field(default="openai", description="openai | anthropic | ollama")
    model: str = Field(default="gpt-4o", description="Model name")
    api_key: Optional[str] = Field(default=None, description="API key")
    base_url: Optional[str] = Field(default=None, description="API base URL")
    temperature: float = 0.0
    max_tokens: int = 4096

    model_config = {"env_prefix": "LLM_", "extra": "ignore"}


class GatewayConfig(BaseSettings):
    """Gateway / HTTP server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    rate_limit_qps: int = 10
    auth_enabled: bool = True

    model_config = {"env_prefix": "GATEWAY_", "extra": "ignore"}


class MemoryConfig(BaseSettings):
    """Memory and RAG configuration."""

    faiss_index_path: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    max_short_term_messages: int = 20
    similarity_top_k: int = 5

    model_config = {"env_prefix": "MEMORY_", "extra": "ignore"}


class PolicyConfig(BaseSettings):
    """Policy engine configuration."""

    enabled: bool = True
    max_input_length: int = 10000
    blocked_patterns_file: Optional[str] = None
    fail_closed: bool = True  # MUST be True in production

    model_config = {"env_prefix": "POLICY_", "extra": "ignore"}


class PlatformConfig(BaseSettings):
    """Top-level platform configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    max_retries: int = 3
    orchestrator_timeout_seconds: int = 300
    workspace_dir: str = "/tmp/agent_workspace"

    model_config = {"env_prefix": "PLATFORM_", "extra": "ignore"}
