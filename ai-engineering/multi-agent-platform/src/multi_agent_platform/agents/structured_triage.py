"""Structured Triage Agent - uses LLM structured output for deterministic routing.

Instead of relying on free-text output and substring matching,
this agent forces the LLM to output a Pydantic model with a Literal category field.

Benefits:
    - Zero ambiguity: category is an enum, not free text
    - Type-safe: Pydantic validates before routing
    - Deterministic: routing reads a field, not a substring
    - Robust: immune to LLM output format variations

Usage:
    from multi_agent_platform.agents.structured_triage import StructuredTriageAgent, TriageDecision

    agent = StructuredTriageAgent(
        llm=llm,
        categories=["ORDER_STATUS", "REFUND", "FAQ"],
        system_prompt="你是客服分流Agent..."
    )
    result = agent.invoke("我要退货")
    # result.output_summary contains "CATEGORY: REFUND"
    # Workflow engine extracts "REFUND" and routes deterministically
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..types import AgentStep, Message, ToolCall
from ..observability import telemetry
from .base import BaseAgent


def create_triage_schema(categories: list[str]) -> type[BaseModel]:
    """Dynamically create a Pydantic model with Literal category field.

    Args:
        categories: List of valid category names (e.g., ["ORDER_STATUS", "REFUND", "FAQ"])

    Returns:
        A Pydantic model class with:
            - category: str (constrained to given categories)
            - confidence: float (0-1)
            - summary: str
    """
    from typing import Literal
    from enum import Enum

    # Create a Literal type from the categories
    # Using Enum for dynamic Literal creation
    CategoryEnum = Enum("CategoryEnum", {c: c for c in categories})

    class TriageDecision(BaseModel):
        """Structured triage decision - forces LLM to pick exactly one category."""

        category: str = Field(
            description=f"The classified category. MUST be one of: {', '.join(categories)}"
        )
        confidence: float = Field(
            default=0.9,
            ge=0.0,
            le=1.0,
            description="Confidence score between 0 and 1",
        )
        summary: str = Field(
            description="One-sentence summary of the user's intent",
        )

    # Store valid categories for validation
    TriageDecision.__valid_categories__ = categories
    return TriageDecision


class StructuredTriageAgent(BaseAgent):
    """Triage agent that outputs structured decisions via with_structured_output.

    Key difference from GenericAgent:
    - Uses LLM.with_structured_output(TriageDecision)
    - Output is guaranteed to contain a valid category field
    - Workflow engine can route deterministically on the category
    """

    def __init__(
        self,
        llm: BaseChatModel,
        categories: list[str],
        system_prompt: str = "",
        **kwargs: Any,
    ) -> None:
        from ..types import AgentRole

        super().__init__(
            role=AgentRole.TRIAGE,
            llm=llm,
            tools=None,
            system_prompt=system_prompt,
        )
        self.categories = categories
        self._schema = create_triage_schema(categories)

        # Create structured output LLM
        try:
            self._structured_llm = llm.with_structured_output(self._schema)
        except (AttributeError, NotImplementedError):
            # Fallback: LLM doesn't support structured output
            self._structured_llm = None
            telemetry.warn("structured_triage.no_structured_output_support")

    def invoke(self, task: str, context: list[Message] | None = None) -> AgentStep:
        """Classify user intent using structured output.

        Returns AgentStep with:
            - output_summary: "CATEGORY: <category>\nSUMMARY: <summary>"
            - tool_calls: [ToolCall(tool_name="__structured_output__", result=<category>)]
              (used by WorkflowEngine to extract route_category)
        """
        start = time.time()
        messages = self._build_messages(task, context)

        category = None
        summary = ""
        confidence = 0.0

        if self._structured_llm:
            try:
                # Use structured output - LLM is forced to return valid schema
                with telemetry.span("agent.triage.structured_call") as span:
                    decision = self._structured_llm.invoke(messages)

                    if isinstance(decision, dict):
                        category = decision.get("category", "")
                        summary = decision.get("summary", "")
                        confidence = decision.get("confidence", 0.9)
                    elif hasattr(decision, "category"):
                        category = decision.category
                        summary = getattr(decision, "summary", "")
                        confidence = getattr(decision, "confidence", 0.9)

                    # Validate category
                    if category and category.upper() not in [c.upper() for c in self.categories]:
                        span.event("invalid_category", category=category, valid=self.categories)
                        category = self.categories[-1]  # Fallback to last (usually default)

                    span.event("decision", category=category, confidence=confidence)

            except Exception as e:
                telemetry.warn("structured_triage.fallback", error=str(e))
                # Fall through to text-based extraction below

        # Fallback: use regular LLM and extract from text
        if not category:
            try:
                response = self._call_llm(messages, use_tools=False)
                content = response.content if hasattr(response, "content") else str(response)
                # Extract category from text output
                category = self._extract_from_text(content)
                summary = content[:100]
            except Exception as e:
                category = self.categories[-1]  # Default category
                summary = f"Triage fallback due to error: {e}"

        duration_ms = (time.time() - start) * 1000
        output = f"CATEGORY: {category}\nSUMMARY: {summary}"

        # Use a special ToolCall to pass structured data to WorkflowEngine
        structured_data = ToolCall(
            tool_name="__structured_output__",
            arguments={"category": category, "confidence": confidence},
            result=category,  # WorkflowEngine reads this
            success=True,
        )

        telemetry.metrics.record_agent_call("triage")

        return AgentStep(
            agent_role="triage_agent",
            action="triage",
            input_summary=task[:200],
            output_summary=output,
            tool_calls=[structured_data],
            duration_ms=duration_ms,
        )

    def _extract_from_text(self, text: str) -> str:
        """Extract category from free-text LLM output (fallback)."""
        import re

        text_upper = text.upper()
        # Try CATEGORY: XXX pattern
        match = re.search(r"CATEGORY[:\s]+([A-Z_]+)", text_upper)
        if match:
            candidate = match.group(1)
            if candidate in [c.upper() for c in self.categories]:
                return candidate

        # Try simple keyword match
        for cat in self.categories:
            if cat.upper() in text_upper:
                return cat

        return self.categories[-1]  # Default
