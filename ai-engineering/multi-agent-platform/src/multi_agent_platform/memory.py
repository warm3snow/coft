"""Memory system - short-term (conversation) + long-term (FAISS vector store).

Architecture mapping (from doc 2.3):
    | Concern        | Solution                              |
    | -------------- | ------------------------------------- |
    | Performance    | recall latency < 200ms                |
    | Reliability    | read-after-write consistency          |
    | Security       | PII masking, row-level tenant access  |
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

from .config import MemoryConfig
from .types import Message
from .observability import telemetry


class MemoryEntry(BaseModel):
    """A single entry in long-term memory."""

    content: str
    metadata: dict[str, Any] = {}
    tenant_id: str = ""


class ShortTermMemory:
    """Conversation-scoped memory - keeps recent messages in a sliding window."""

    def __init__(self, max_messages: int = 20) -> None:
        self._max = max_messages
        self._store: dict[str, list[Message]] = {}  # task_id -> messages

    def add(self, task_id: str, message: Message) -> None:
        if task_id not in self._store:
            self._store[task_id] = []
        self._store[task_id].append(message)
        # Sliding window
        if len(self._store[task_id]) > self._max:
            self._store[task_id] = self._store[task_id][-self._max :]

    def get(self, task_id: str) -> list[Message]:
        return self._store.get(task_id, [])

    def clear(self, task_id: str) -> None:
        self._store.pop(task_id, None)


class LongTermMemory:
    """FAISS-backed vector store for semantic retrieval.

    Uses langchain's FAISS integration for simplicity.
    Tenant isolation is enforced at query time via metadata filtering.
    """

    def __init__(self, config: Optional[MemoryConfig] = None) -> None:
        self.config = config or MemoryConfig()
        self._store: Optional[Any] = None  # FAISS vector store (lazy init)
        self._entries: list[MemoryEntry] = []  # Fallback in-memory store

    def _get_embeddings(self) -> Any:
        """Get embedding model - supports both OpenAI and fallback."""
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(model=self.config.embedding_model)
        except Exception:
            # Fallback: use a simple deterministic embedding for testing
            from langchain_community.embeddings import FakeEmbeddings
            return FakeEmbeddings(size=256)

    def _ensure_store(self) -> None:
        """Lazy-initialize the FAISS store."""
        if self._store is not None:
            return
        try:
            from langchain_community.vectorstores import FAISS

            embeddings = self._get_embeddings()
            # Initialize with a dummy doc to create the index
            self._store = FAISS.from_texts(
                ["__init__"],
                embeddings,
                metadatas=[{"tenant_id": "__system__"}],
            )
            telemetry.log("memory.faiss_initialized")
        except ImportError:
            telemetry.warn("memory.faiss_unavailable", fallback="in_memory")
            self._store = None

    def add(self, content: str, tenant_id: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a document to long-term memory."""
        entry = MemoryEntry(content=content, tenant_id=tenant_id, metadata=metadata or {})
        self._entries.append(entry)

        self._ensure_store()
        if self._store is not None:
            meta = {"tenant_id": tenant_id, **(metadata or {})}
            self._store.add_texts([content], metadatas=[meta])
            telemetry.log("memory.added", tenant_id=tenant_id, length=len(content))

    def search(
        self, query: str, tenant_id: str, top_k: Optional[int] = None
    ) -> list[str]:
        """Search long-term memory with tenant isolation."""
        k = top_k or self.config.similarity_top_k

        self._ensure_store()
        if self._store is not None:
            with telemetry.span("memory.search", query_length=len(query)) as span:
                results = self._store.similarity_search(
                    query,
                    k=k,
                    filter={"tenant_id": tenant_id},
                )
                span.event("results_found", count=len(results))
                return [doc.page_content for doc in results if doc.page_content != "__init__"]

        # Fallback: simple substring search
        matches = [
            e.content
            for e in self._entries
            if e.tenant_id == tenant_id and query.lower() in e.content.lower()
        ]
        return matches[:k]


class MemoryManager:
    """Unified memory interface combining short-term and long-term memory."""

    def __init__(self, config: Optional[MemoryConfig] = None) -> None:
        self.config = config or MemoryConfig()
        self.short_term = ShortTermMemory(max_messages=self.config.max_short_term_messages)
        self.long_term = LongTermMemory(config=self.config)

    def add_message(self, task_id: str, message: Message) -> None:
        """Add a message to short-term memory."""
        self.short_term.add(task_id, message)

    def get_context(self, task_id: str) -> list[Message]:
        """Get conversation context for a task."""
        return self.short_term.get(task_id)

    def store_knowledge(self, content: str, tenant_id: str, **metadata: Any) -> None:
        """Store knowledge in long-term memory."""
        self.long_term.add(content, tenant_id, metadata)

    def recall(self, query: str, tenant_id: str, top_k: int = 5) -> list[str]:
        """Retrieve relevant knowledge from long-term memory."""
        return self.long_term.search(query, tenant_id, top_k)

    def clear_task(self, task_id: str) -> None:
        """Clear short-term memory for a completed task."""
        self.short_term.clear(task_id)
